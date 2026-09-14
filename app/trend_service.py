"""Deterministic trend analysis over real ingested telemetry samples; queries only, no prediction, no truth inference."""
import json
import math
from datetime import datetime, timezone
from fastapi import HTTPException
from app.store import get
from app.telemetry_api import parse_timestamp

CRITERIA = {
    'min_samples': 20,
    'min_window_seconds': 600,
    'min_third_samples': 8,
    'relative_change_threshold': 0.05,
    'signal_to_noise_threshold': 2.0,
    'level_shift_se_factor': 2.0,
    'variance_ratio_threshold': 2.0,
    'rate_threshold': 0.10,
}
LIMITS = {'max_batches': 200, 'max_samples': 200000}


def _mean(values):
    return sum(values) / len(values)


def _std(values):
    if len(values) < 2:
        return 0.0
    m = _mean(values)
    return math.sqrt(sum((v - m) ** 2 for v in values) / (len(values) - 1))


def _round(value):
    return round(value, 9) if isinstance(value, float) else value


def _slope(points):
    """Least-squares slope (value per second) and residual std for sorted [(epoch, value)]."""
    n = len(points)
    if n < 2:
        return 0.0, 0.0
    mx = _mean([p[0] for p in points])
    my = _mean([p[1] for p in points])
    sxx = sum((p[0] - mx) ** 2 for p in points)
    if sxx == 0:
        return 0.0, 0.0
    slope = sum((p[0] - mx) * (p[1] - my) for p in points) / sxx
    intercept = my - slope * mx
    residual_std = 0.0 if n <= 2 else math.sqrt(sum((p[1] - (slope * p[0] + intercept)) ** 2 for p in points) / (n - 2))
    return slope, residual_std


def _reference_span(declared, values):
    if declared:
        return declared['maximum'] - declared['minimum']
    return max(values) - min(values) if len(values) >= 2 else 0.0


def _drift(points, declared):
    n = len(points)
    failed = []
    span = points[-1][0] - points[0][0] if n >= 2 else 0.0
    slope, residual_std = _slope(points)
    total_change = slope * span
    reference = _reference_span(declared, [p[1] for p in points])
    if n < CRITERIA['min_samples']:
        failed.append(f"sample_count >= {CRITERIA['min_samples']}")
    if span < CRITERIA['min_window_seconds']:
        failed.append(f"window >= {CRITERIA['min_window_seconds']} seconds")
    if reference <= 0:
        failed.append('non-zero reference span (declared_range or observed variation)')
    elif abs(total_change) < CRITERIA['relative_change_threshold'] * reference:
        failed.append(f"|total change| >= {CRITERIA['relative_change_threshold']:.0%} of reference span")
    if residual_std > 0 and abs(total_change) < CRITERIA['signal_to_noise_threshold'] * residual_std:
        failed.append(f"signal-to-noise ratio >= {CRITERIA['signal_to_noise_threshold']}")
    signal_to_noise = abs(total_change) / residual_std if residual_std > 0 else None
    return dict(type='drift', status='VERIFIED TREND' if not failed else 'INSUFFICIENT EVIDENCE', sample_count=n,
                statistic='least-squares slope per hour', value=_round(slope * 3600) if n >= 2 else None,
                threshold=f"|slope*window| >= {CRITERIA['relative_change_threshold']:.0%} of reference span and "
                          f">= {CRITERIA['signal_to_noise_threshold']}x residual std",
                failed_criteria=failed,
                details={'total_change': _round(total_change), 'reference_span': _round(reference),
                         'residual_std': _round(residual_std), 'signal_to_noise': _round(signal_to_noise),
                         'window_seconds': _round(span)})


def _level_shift(points, declared):
    n = len(points)
    third = n // 3
    failed = []
    diff = se = 0.0
    if third >= 1:
        first = [p[1] for p in points[:third]]
        last = [p[1] for p in points[-third:]]
        diff = _mean(last) - _mean(first)
        se = math.sqrt(_std(first) ** 2 / third + _std(last) ** 2 / third)
    reference = _reference_span(declared, [p[1] for p in points])
    if third < CRITERIA['min_third_samples']:
        failed.append(f"at least {CRITERIA['min_third_samples']} samples per window third")
    if reference <= 0:
        failed.append('non-zero reference span (declared_range or observed variation)')
    elif abs(diff) < CRITERIA['relative_change_threshold'] * reference:
        failed.append(f"|mean shift| >= {CRITERIA['relative_change_threshold']:.0%} of reference span")
    if abs(diff) < CRITERIA['level_shift_se_factor'] * se:
        failed.append(f"|mean shift| >= {CRITERIA['level_shift_se_factor']} standard errors")
    return dict(type='level_shift', status='VERIFIED TREND' if not failed else 'INSUFFICIENT EVIDENCE', sample_count=n,
                statistic='mean(last third) - mean(first third)', value=_round(diff) if third >= 1 else None,
                threshold=f"|shift| >= {CRITERIA['relative_change_threshold']:.0%} of reference span and "
                          f">= {CRITERIA['level_shift_se_factor']} standard errors",
                failed_criteria=failed,
                details={'standard_error': _round(se), 'third_size': third, 'reference_span': _round(reference)})


def _variance_change(points):
    n = len(points)
    third = n // 3
    failed = []
    std_first = std_last = 0.0
    ratio = 1.0
    if third >= 2:
        std_first = _std([p[1] for p in points[:third]])
        std_last = _std([p[1] for p in points[-third:]])
        ratio = (std_last + 1e-12) / (std_first + 1e-12)
    if third < CRITERIA['min_third_samples']:
        failed.append(f"at least {CRITERIA['min_third_samples']} samples per window third")
    if not (ratio >= CRITERIA['variance_ratio_threshold'] or ratio <= 1 / CRITERIA['variance_ratio_threshold']):
        failed.append(f"std ratio >= {CRITERIA['variance_ratio_threshold']:g} or "
                      f"<= {1 / CRITERIA['variance_ratio_threshold']:g}")
    return dict(type='variance_change', status='VERIFIED TREND' if not failed else 'INSUFFICIENT EVIDENCE', sample_count=n,
                statistic='std(last third) / std(first third)', value=_round(ratio) if third >= 2 else None,
                threshold=f"std ratio >= {CRITERIA['variance_ratio_threshold']:g} or "
                          f"<= {1 / CRITERIA['variance_ratio_threshold']:g}",
                failed_criteria=failed,
                details={'std_first': _round(std_first), 'std_last': _round(std_last), 'third_size': third})


def _out_of_range_rate(points, declared):
    n = len(points)
    failed = []
    if not declared:
        failed.append('declared_range required by operator')
        rate = None
        out = None
    else:
        out = sum(1 for p in points if not (declared['minimum'] <= p[1] <= declared['maximum']))
        rate = out / n if n else 0.0
        if n < CRITERIA['min_samples']:
            failed.append(f"sample_count >= {CRITERIA['min_samples']}")
        if rate < CRITERIA['rate_threshold']:
            failed.append(f"out-of-range rate >= {CRITERIA['rate_threshold']:.0%}")
    return dict(type='out_of_range_rate', status='VERIFIED TREND' if not failed else 'INSUFFICIENT EVIDENCE', sample_count=n,
                statistic='fraction of samples outside declared_range', value=_round(rate) if rate is not None else None,
                threshold=f"rate >= {CRITERIA['rate_threshold']:.0%} with >= {CRITERIA['min_samples']} samples",
                failed_criteria=failed,
                details={'out_of_range_samples': out, 'declared_range': declared})


def _suspect_rate(points):
    n = len(points)
    suspect = sum(1 for p in points if p[2] == 'suspect')
    rate = suspect / n if n else 0.0
    failed = []
    if n < CRITERIA['min_samples']:
        failed.append(f"sample_count >= {CRITERIA['min_samples']}")
    if rate < CRITERIA['rate_threshold']:
        failed.append(f"suspect rate >= {CRITERIA['rate_threshold']:.0%}")
    return dict(type='suspect_rate', status='VERIFIED TREND' if not failed else 'INSUFFICIENT EVIDENCE', sample_count=n,
                statistic='fraction of device-declared suspect samples', value=_round(rate),
                threshold=f"rate >= {CRITERIA['rate_threshold']:.0%} with >= {CRITERIA['min_samples']} samples",
                failed_criteria=failed, details={'suspect_samples': suspect})


def analyze_sensor(db, storage, sensor_id, session):
    sensor = get(db, 'telemetry_sensor', sensor_id)
    rows = db.execute("SELECT body FROM records WHERE kind='telemetry_batch' AND json_extract(body,'$.device_id')=? ORDER BY seq",
                      (sensor['device_id'],)).fetchall()
    if len(rows) > LIMITS['max_batches']:
        raise HTTPException(422, f"More than {LIMITS['max_batches']} stored batches for this device; narrow the analysis scope")
    batches = [json.loads(row[0]) for row in rows]
    if session is not None:
        batches = [batch for batch in batches if batch['session'] == session]
    samples = []
    for batch in batches:
        for sample in json.loads(storage.checked(batch)):
            if sample['sensor_id'] == sensor_id:
                samples.append(sample)
        if len(samples) > LIMITS['max_samples']:
            raise HTTPException(422, f"More than {LIMITS['max_samples']} samples for this sensor; narrow the analysis scope")
    points = sorted((parse_timestamp(s['timestamp']).timestamp(), s['value'], s['quality']) for s in samples)
    declared = sensor.get('declared_range')
    checks = [_drift(points, declared), _level_shift(points, declared), _variance_change(points),
              _out_of_range_rate(points, declared), _suspect_rate(points)]
    verified = [check['type'] for check in checks if check['status'] == 'VERIFIED TREND']
    return dict(sensor_id=sensor_id, device_id=sensor['device_id'], session=session, sample_count=len(points),
                window_start=datetime.fromtimestamp(points[0][0], timezone.utc).isoformat() if points else None,
                window_end=datetime.fromtimestamp(points[-1][0], timezone.utc).isoformat() if points else None,
                batch_ids=[batch['id'] for batch in batches], checks=checks, verified_types=verified,
                summary_status='VERIFIED TREND' if verified else 'INSUFFICIENT EVIDENCE',
                basis='SUBMITTED_DEVICE_SAMPLES', result_class='CALCULATED', prediction='NONE')


def catalog():
    return dict(checks=[
        dict(type='drift', statistic='least-squares slope per hour',
             criteria={k: CRITERIA[k] for k in ('min_samples', 'min_window_seconds', 'relative_change_threshold', 'signal_to_noise_threshold')},
             description='Sustained directional change over the analysis window, relative to declared or observed span'),
        dict(type='level_shift', statistic='mean(last third) - mean(first third)',
             criteria={k: CRITERIA[k] for k in ('min_third_samples', 'relative_change_threshold', 'level_shift_se_factor')},
             description='Sustained shift between the first and last third of the analysis window'),
        dict(type='variance_change', statistic='std(last third) / std(first third)',
             criteria={k: CRITERIA[k] for k in ('min_third_samples', 'variance_ratio_threshold')},
             description='Change in dispersion between the first and last third of the analysis window'),
        dict(type='out_of_range_rate', statistic='fraction of samples outside declared_range',
             criteria={k: CRITERIA[k] for k in ('min_samples', 'rate_threshold')},
             description='Rate of samples outside the operator-declared (not calibrated) range'),
        dict(type='suspect_rate', statistic='fraction of device-declared suspect samples',
             criteria={k: CRITERIA[k] for k in ('min_samples', 'rate_threshold')},
             description='Rate of samples the device itself marked suspect'),
    ], limits=LIMITS)
