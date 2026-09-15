"""Load test tool contract: real subprocess run against a real disposable Core with a structured report."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_loadtest_requires_explicit_fixture_opt_in():
    """LOAD-001: without --allow-fixtures the tool blocks instead of writing synthetic success."""
    result = subprocess.run([sys.executable, 'scripts/loadtest.py'], cwd=ROOT, capture_output=True, text=True, timeout=60)
    assert result.returncode != 0
    assert '--allow-fixtures' in (result.stderr + result.stdout)


def test_loadtest_real_run_and_structured_report(tmp_path):
    """LOAD-002: a real bounded run against a disposable Core passes and writes a truthful structured report."""
    report = tmp_path / 'loadtest.json'
    result = subprocess.run([sys.executable, 'scripts/loadtest.py', '--report', str(report),
                             '--workers', '4', '--requests-per-worker', '10', '--allow-fixtures'],
                            cwd=ROOT, capture_output=True, text=True, timeout=180)
    assert result.returncode == 0, result.stderr
    payload = json.loads(report.read_text())
    assert payload['status'] == 'PASS' and payload['kind'].startswith('REAL LOCAL LOAD')
    assert payload['parameters'] == {'workers': 4, 'requests_per_worker': 10, 'assert_p95_ms': None}
    assert payload['results']['requests'] == 40 and payload['results']['errors'] == 0
    assert payload['results']['successful'] == 40
    assert 0 <= payload['results']['p50_ms'] <= payload['results']['p95_ms'] <= payload['results']['p99_ms']
    assert payload['results']['throughput_rps'] > 0
    assert 'no distributed or cloud load claim' in payload['limits']
