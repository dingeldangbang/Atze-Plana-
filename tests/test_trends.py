"""Trend engine contract tests: deterministic CALCULATED analysis of real ingested samples, fail-closed reads."""
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app

TELEMETRY_TOKEN = 'telemetry-device-test-' * 3
BASE = datetime(2026, 1, 2, 3, 4, 0, tzinfo=timezone.utc)


@pytest.fixture
def settings(tmp_path):
    return Settings(tmp_path / 'test.db', 'operator-test-only-' * 3, 'reviewer-test-only-' * 3,
                    mode='test', challenge_token='challenge-test-only-' * 3, telemetry_token=TELEMETRY_TOKEN)


@pytest.fixture
def client(settings):
    with TestClient(create_app(settings)) as client:
        client.headers['Authorization'] = 'Bearer ' + settings.operator_token
        yield client


@pytest.fixture
def reviewer(settings):
    return {'Authorization': 'Bearer ' + settings.reviewer_token}


@pytest.fixture
def device_headers():
    return {'Authorization': 'Bearer ' + TELEMETRY_TOKEN}


def ts(minutes):
    return (BASE + timedelta(minutes=minutes)).isoformat()


def register_sensor(client, declared={'minimum': 0.0, 'maximum': 100.0}, name='pack-voltage'):
    device = client.post('/api/telemetry/devices', json={'name': 'Trend bench unit ' + name,
                                                         'description': 'Owner-declared fixture device, no hardware claim'}).json()
    sensor = client.post(f"/api/telemetry/devices/{device['id']}/sensors",
                         json={'name': name, 'kind': 'voltage', 'unit': 'V', 'declared_range': declared,
                               'identification': 'IDENTIFIED', 'note': 'Synthetic fixture sensor'}).json()
    return device, sensor


def ingest(client, sensor_id, values, session='', quality=None, start_minutes=0, step_minutes=1):
    samples = [{'sensor_id': sensor_id, 'value': value,
                'timestamp': ts(start_minutes + index * step_minutes),
                'quality': quality[index] if quality else 'ok'} for index, value in enumerate(values)]
    response = client.post('/api/telemetry/ingest', headers={'Authorization': 'Bearer ' + TELEMETRY_TOKEN},
                           json={'samples': samples, 'session': session, 'conditions': 'Synthetic fixture only'})
    assert response.status_code == 201, response.text
    return response.json()


def analyze(client, sensor_id, session=None, headers=None):
    body = {'sensor_id': sensor_id}
    if session is not None:
        body['session'] = session
    return client.post('/api/telemetry/trends', json=body, headers=headers)


def check_of(report, kind):
    return next(check for check in report['checks'] if check['type'] == kind)


def test_catalog_lists_all_documented_checks(client, device_headers):
    """TRD-001: criteria catalog exposes exactly the five implemented checks with explicit thresholds and limits."""
    response = client.get('/api/telemetry/trends/checks')
    assert response.status_code == 200
    catalog = response.json()
    assert [c['type'] for c in catalog['checks']] == ['drift', 'level_shift', 'variance_change',
                                                      'out_of_range_rate', 'suspect_rate']
    drift = catalog['checks'][0]
    assert drift['criteria']['min_samples'] == 20
    assert catalog['limits'] == {'max_batches': 200, 'max_samples': 200000}
    assert client.get('/api/telemetry/trends/checks', headers=device_headers).status_code == 401


def test_unknown_sensor_rejected(client):
    """TRD-002: analysis of an unknown sensor id fails 404 without computation."""
    assert analyze(client, 'missing-sensor').status_code == 404


def test_empty_history_is_insufficient_evidence(client):
    """TRD-003: sensor without ingested samples yields INSUFFICIENT EVIDENCE for every check, no window."""
    device, sensor = register_sensor(client)
    report = analyze(client, sensor['id']).json()
    assert report['sample_count'] == 0
    assert report['window_start'] is None and report['window_end'] is None
    assert report['verified_types'] == []
    assert report['summary_status'] == 'INSUFFICIENT EVIDENCE'
    assert all(check['status'] == 'INSUFFICIENT EVIDENCE' for check in report['checks'])


def test_rising_series_verifies_drift(client):
    """TRD-004: 30 monotonically rising samples verify drift with exact slope, CALCULATED provenance, no prediction."""
    device, sensor = register_sensor(client)
    ingest(client, sensor['id'], [10.0 + i for i in range(30)])
    report = analyze(client, sensor['id']).json()
    assert report['sample_count'] == 30
    assert report['summary_status'] == 'VERIFIED TREND'
    assert 'drift' in report['verified_types']
    drift = check_of(report, 'drift')
    assert drift['status'] == 'VERIFIED TREND' and drift['failed_criteria'] == []
    assert abs(drift['value'] - 60.0) < 1e-6  # 1 unit per minute = 60 per hour
    assert report['basis'] == 'SUBMITTED_DEVICE_SAMPLES'
    assert report['result_class'] == 'CALCULATED' and report['prediction'] == 'NONE'


def test_few_samples_are_insufficient_evidence(client):
    """TRD-005: fewer than min_samples yields INSUFFICIENT EVIDENCE with the explicit failed criterion."""
    device, sensor = register_sensor(client)
    ingest(client, sensor['id'], [10.0 + i for i in range(10)])
    report = analyze(client, sensor['id']).json()
    drift = check_of(report, 'drift')
    assert drift['status'] == 'INSUFFICIENT EVIDENCE'
    assert any('sample_count' in criterion for criterion in drift['failed_criteria'])
    assert report['summary_status'] == 'INSUFFICIENT EVIDENCE'


def test_flat_series_verifies_nothing(client):
    """TRD-006: flat alternating series within range verifies no check; noise is not promoted to a trend."""
    device, sensor = register_sensor(client)
    ingest(client, sensor['id'], [50.0 if i % 2 == 0 else 50.2 for i in range(30)])
    report = analyze(client, sensor['id']).json()
    assert report['verified_types'] == []
    assert report['summary_status'] == 'INSUFFICIENT EVIDENCE'
    assert check_of(report, 'drift')['status'] == 'INSUFFICIENT EVIDENCE'
    assert check_of(report, 'level_shift')['status'] == 'INSUFFICIENT EVIDENCE'


def test_step_series_verifies_level_shift(client):
    """TRD-007: step from 10 to 50 across the window verifies level_shift."""
    device, sensor = register_sensor(client)
    ingest(client, sensor['id'], [10.0] * 10 + [30.0] * 10 + [50.0] * 10)
    report = analyze(client, sensor['id']).json()
    shift = check_of(report, 'level_shift')
    assert shift['status'] == 'VERIFIED TREND'
    assert abs(shift['value'] - 40.0) < 1e-9
    assert 'level_shift' in report['verified_types']


def test_dispersion_change_verifies_variance_change_only(client):
    """TRD-008: constant thirds with a volatile last third verify variance_change but not drift."""
    device, sensor = register_sensor(client)
    values = [50.0] * 10 + [49.0, 51.0] * 5 + [20.0, 80.0] * 5
    ingest(client, sensor['id'], values)
    report = analyze(client, sensor['id']).json()
    assert check_of(report, 'variance_change')['status'] == 'VERIFIED TREND'
    assert check_of(report, 'drift')['status'] == 'INSUFFICIENT EVIDENCE'
    assert check_of(report, 'level_shift')['status'] == 'INSUFFICIENT EVIDENCE'
    assert 'variance_change' in report['verified_types']


def test_out_of_declared_range_rate_verifies(client):
    """TRD-009: 20% of samples outside the declared range verify out_of_range_rate."""
    device, sensor = register_sensor(client)
    ingest(client, sensor['id'], [50.0] * 20 + [150.0] * 5)
    report = analyze(client, sensor['id']).json()
    rate = check_of(report, 'out_of_range_rate')
    assert rate['status'] == 'VERIFIED TREND' and abs(rate['value'] - 0.2) < 1e-9
    assert 'out_of_range_rate' in report['verified_types']


def test_device_declared_suspect_rate_verifies(client):
    """TRD-010: 20% device-declared suspect samples verify suspect_rate."""
    device, sensor = register_sensor(client)
    quality = ['suspect'] * 5 + ['ok'] * 20
    ingest(client, sensor['id'], [50.0] * 25, quality=quality)
    report = analyze(client, sensor['id']).json()
    rate = check_of(report, 'suspect_rate')
    assert rate['status'] == 'VERIFIED TREND' and abs(rate['value'] - 0.2) < 1e-9


def test_out_of_range_requires_declared_range(client):
    """TRD-011: without a declared_range the out_of_range_rate check stays INSUFFICIENT EVIDENCE with explicit reason."""
    device, sensor = register_sensor(client, declared=None)
    ingest(client, sensor['id'], [50.0] * 25)
    report = analyze(client, sensor['id']).json()
    rate = check_of(report, 'out_of_range_rate')
    assert rate['status'] == 'INSUFFICIENT EVIDENCE'
    assert 'declared_range required by operator' in rate['failed_criteria']


def test_session_scoping_filters_basis(client):
    """TRD-012: session filter narrows analysis to that session's batches only; empty session means all."""
    device, sensor = register_sensor(client)
    ingest(client, sensor['id'], [10.0 + i for i in range(30)], session='rising')
    ingest(client, sensor['id'], [50.0] * 30, session='flat', start_minutes=60)
    flat = analyze(client, sensor['id'], session='flat').json()
    assert flat['sample_count'] == 30 and len(flat['batch_ids']) == 1
    assert flat['session'] == 'flat'
    assert check_of(flat, 'drift')['status'] == 'INSUFFICIENT EVIDENCE'
    rising = analyze(client, sensor['id'], session='rising').json()
    assert check_of(rising, 'drift')['status'] == 'VERIFIED TREND'
    everything = analyze(client, sensor['id']).json()
    assert everything['sample_count'] == 60 and everything['session'] is None


def test_corrupt_blob_fails_closed_on_analysis(client, tmp_path):
    """TRD-013: corrupted batch blob makes analysis fail 503; no partial trend is computed."""
    device, sensor = register_sensor(client)
    batch = ingest(client, sensor['id'], [10.0 + i for i in range(30)])
    blob_path = tmp_path / 'objects' / (batch['key'] + '.blob')
    assert blob_path.exists()
    blob_path.write_bytes(b'corrupted analysis input')
    response = analyze(client, sensor['id'])
    assert response.status_code == 503


def test_analysis_is_deterministic(client):
    """TRD-014: identical query over immutable batches returns byte-identical report."""
    device, sensor = register_sensor(client)
    ingest(client, sensor['id'], [10.0 + i * 0.5 for i in range(30)])
    first = analyze(client, sensor['id'])
    second = analyze(client, sensor['id'])
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()


def test_roles_and_stop_do_not_block_read_only_analysis(client, reviewer, device_headers):
    """TRD-015: platform roles required (device token 401); emergency stop does not block read-only trend queries."""
    device, sensor = register_sensor(client)
    ingest(client, sensor['id'], [10.0 + i for i in range(30)])
    assert analyze(client, sensor['id'], headers=device_headers).status_code == 401
    assert analyze(client, sensor['id'], headers=reviewer).status_code == 200
    assert client.post('/api/control/stop', headers=reviewer,
                       json={'active': True, 'reason': 'Fixture stop for read-only check'}).status_code == 200
    assert analyze(client, sensor['id']).status_code == 200
    assert client.post('/api/control/stop', headers=reviewer,
                       json={'active': False, 'reason': 'Fixture stop cleared'}).status_code == 200


def test_batch_limit_fails_explicitly(client):
    """TRD-016: more than max_batches stored batches for one device rejects analysis 422 instead of unbounded work."""
    device, sensor = register_sensor(client)
    for index in range(201):
        ingest(client, sensor['id'], [50.0], session=f'limit-{index}')
    response = analyze(client, sensor['id'])
    assert response.status_code == 422
    assert 'batches' in response.json()['detail']


def test_deactivated_sensor_history_stays_analyzable(client, reviewer):
    """TRD-017: reviewer-confirmed sensor deactivation retains and keeps history analyzable."""
    device, sensor = register_sensor(client)
    ingest(client, sensor['id'], [10.0 + i for i in range(30)])
    deactivated = client.post(f"/api/telemetry/sensors/{sensor['id']}/deactivate", headers=reviewer,
                              json={'confirm': True, 'reason': 'Fixture retirement, history retained'})
    assert deactivated.status_code == 200
    report = analyze(client, sensor['id'])
    assert report.status_code == 200
    assert report.json()['summary_status'] == 'VERIFIED TREND'
