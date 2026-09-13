"""Explicit test-only fixtures and fault injection; no hardware/provider simulation."""
import json
import sqlite3
from dataclasses import replace
from pathlib import Path
import subprocess
import sys
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app.main import create_app
from app.storage import Storage
from app.store import Store
from scripts import smoke
from scripts.reality_check import check


def test_operational_start_has_no_seeded_data(settings):
    """REAL-001: a new operational database/UI has no seeded projects, telemetry, tasks or results; mode is explicit."""
    config = replace(settings, mode='operational')
    with TestClient(create_app(config)) as client:
        client.headers['Authorization'] = 'Bearer ' + config.operator_token
        for path in ['projects', 'evidence', 'tasks', 'archive', 'memory']:
            assert client.get('/api/' + path).json() == []
        client.headers['Authorization'] = 'Bearer ' + config.reviewer_token
        assert client.get('/api/audit').json() == []
        assert client.get('/api/runtime').json()['mode'] == 'operational'
        assert client.get('/health').json()['mode'] == 'operational'
        assert 'Instanzmodus noch nicht geprüft' in client.get('/').text
        client.headers.clear()
        assert client.get('/api/runtime').status_code == 401


def test_test_database_cannot_be_opened_operational(client, settings):
    """REAL-002: persistent test DB marker rejects switching to operational mode without changing/deleting data."""
    assert client.get('/api/runtime').json()['mode'] == 'test'
    with pytest.raises(ValueError, match='mode mismatch'):
        create_app(replace(settings, mode='operational'))
    with sqlite3.connect(settings.db_path) as db:
        assert db.execute('SELECT mode FROM instance_mode').fetchone() == ('test',)


def test_operational_database_cannot_be_used_as_test(settings):
    """REAL-003: an operational database cannot be switched to test mode even if currently empty."""
    create_app(replace(settings, mode='operational'))
    with pytest.raises(ValueError, match='mode mismatch'):
        create_app(settings)


def test_unmarked_existing_database_not_adopted_as_test(settings):
    """REAL-004: legacy nonempty database is refused for test mode rather than silently seeded or relabelled."""
    Store(settings.db_path)
    with sqlite3.connect(settings.db_path) as db:
        db.execute('DROP TABLE instance_mode')
        db.execute("INSERT INTO records(id,kind,body) VALUES('legacy','project','{}')")
    with pytest.raises(ValueError, match='new empty database'):
        Store(settings.db_path, 'test')


def test_storage_root_cannot_cross_modes(settings):
    """REAL-005: blob-root mode marker rejects cross-mode sharing independently of database separation."""
    Storage(settings)
    with pytest.raises(HTTPException, match='mode mismatch'):
        Storage(replace(settings, mode='operational'))
    assert (settings.db_path.parent / 'objects' / '.atze-mode').read_text() == 'test'


def test_unmarked_existing_blobs_not_adopted_as_test(settings):
    """REAL-006: test storage refuses pre-existing unlabelled originals instead of marking them as test data."""
    root = settings.db_path.parent / 'objects'
    root.mkdir()
    (root / 'preexisting.blob').write_bytes(b'legacy original')
    with pytest.raises(HTTPException, match='empty or test-labelled'):
        Storage(settings)
    assert (root / 'preexisting.blob').read_bytes() == b'legacy original'


def test_availability_dimensions_and_real_failure(client, settings, monkeypatch):
    """REAL-007: absent implementation, absent config and actual configured-path outage have distinct statuses and null measurements."""
    tiers = {t['tier']: t for t in client.get('/api/storage/health').json()['tiers']}
    assert tiers['local']['status'] == 'AVAILABLE'
    assert tiers['local']['implemented'] and tiers['local']['configured']
    assert tiers['local']['resource_kind'] == 'FILESYSTEM_PATH'
    assert tiers['sd']['status'] == 'NOT_CONFIGURED' and tiers['sd']['implemented']
    assert not tiers['sd']['configured']
    for name in ['ram', 'server', 'cloud']:
        assert tiers[name]['status'] == 'BLOCKED' and not tiers[name]['implemented']
        assert tiers[name]['used_percent'] is None
    # Remove the actual directory, not substitute measurements.
    root = settings.db_path.parent / 'objects'
    root.rename(root.with_name('offline-objects'))
    tiers = {t['tier']: t for t in client.get('/api/storage/health').json()['tiers']}
    assert tiers['local']['status'] == 'UNAVAILABLE' and tiers['local']['configured']
    assert tiers['local']['free_bytes'] is None


def test_invalid_mode_fails_closed(settings):
    """REAL-008: unknown operating mode is rejected, never interpreted as permission to enable test behavior."""
    with pytest.raises(ValueError, match='ATZE_MODE'):
        replace(settings, mode='demo')


def test_smoke_requires_opt_in_and_invalidates_old_report(tmp_path):
    """REAL-009: absent explicit opt-in overwrites a stale PASS report with BLOCKED without starting tests."""
    report = tmp_path / 'smoke.json'
    report.write_text('{"status":"PASS"}')
    with pytest.raises(RuntimeError, match='allow-fixtures'):
        smoke.run(report)
    assert json.loads(report.read_text())['status'] == 'BLOCKED'


def test_smoke_real_isolated_process_ignores_operational_paths(tmp_path, monkeypatch):
    """REAL-010: real HTTP smoke uses a fresh process/DB/roots/tokens, not inherited operational paths or credentials."""
    sentinel = tmp_path / 'operational.db'
    sentinel.write_bytes(b'unchanged operational sentinel')
    monkeypatch.setenv('ATZE_DB_PATH', str(sentinel))
    monkeypatch.setenv('ATZE_STORAGE_ROOT', str(tmp_path / 'must-not-create'))
    monkeypatch.setenv('ATZE_MODE', 'operational')
    monkeypatch.setenv('ATZE_OPERATOR_TOKEN', 'invalid-inherited-token')
    result = smoke.run(tmp_path / 'real-smoke.json', allow_fixtures=True)
    assert result['status'] == 'PASS' and len(result['checks']) == 20
    assert result['checks'][0]['body']['mode'] == 'test'
    assert sentinel.read_bytes() == b'unchanged operational sentinel'
    assert not (tmp_path / 'must-not-create').exists()


def test_smoke_failure_does_not_leave_pass(tmp_path, monkeypatch):
    """REAL-011: an injected test failure produces FAIL with error, not hardcoded/stale PASS, and stops the real child."""
    def fail(*args):
        raise RuntimeError('deliberate harness failure')
    monkeypatch.setattr(smoke, '_exercise', fail)
    report = tmp_path / 'failed.json'
    report.write_text('{"status":"PASS"}')
    with pytest.raises(RuntimeError, match='deliberate'):
        smoke.run(report, allow_fixtures=True)
    result = json.loads(report.read_text())
    assert result['status'] == 'FAIL' and 'deliberate' in result['error']
    assert result['finished_at']


def test_smoke_rejects_arbitrary_target():
    """REAL-012: CLI no longer accepts a user-supplied target URL for fixture writes."""
    result = subprocess.run([sys.executable, 'scripts/smoke.py', '--base-url', 'https://example.com'], capture_output=True, text=True)
    assert result.returncode != 0 and 'unrecognized arguments' in result.stderr


def test_reality_boundary_guard(tmp_path):
    """REAL-013: runtime mock imports and assert-only test success are rejected by the narrow guardrail."""
    assert check() == []
    (tmp_path / 'app').mkdir()
    (tmp_path / 'scripts').mkdir()
    (tmp_path / 'app/bad.py').write_text('from unittest import mock\n')
    (tmp_path / 'scripts/smoke.py').write_text('assert True\n')
    errors = check(tmp_path)
    assert any('runtime' in e for e in errors)
    assert any('python -O' in e for e in errors)
    assert any('policy' in e for e in errors)


def test_zero_capacity_has_no_invented_percentage(client, monkeypatch):
    """REAL-014: a filesystem capacity probe without total size yields UNAVAILABLE/null, not an invented 100 percent."""
    from types import SimpleNamespace
    import app.storage as storage
    monkeypatch.setattr(storage.os, 'fstatvfs', lambda fd: SimpleNamespace(f_blocks=0, f_frsize=4096, f_bavail=0))
    tier = client.get('/api/storage/health').json()['tiers'][1]
    assert tier['tier'] == 'local' and tier['status'] == 'UNAVAILABLE'
    assert tier['used_percent'] is None


def test_late_unmarked_tier_is_unavailable_until_reviewed_restart(settings, tmp_path):
    """REAL-015: newly appearing unlabelled tier is not initialized by GET; reviewed restart binds its mode explicitly."""
    root = tmp_path / 'later-tier'
    config = replace(settings, sd_root=root)
    with TestClient(create_app(config)) as client:
        client.headers['Authorization'] = 'Bearer ' + config.operator_token
        root.mkdir()
        tier = client.get('/api/storage/health').json()['tiers'][2]
        assert tier['status'] == 'UNAVAILABLE'
        assert not (root / '.atze-mode').exists()
    with TestClient(create_app(config)) as client:
        client.headers['Authorization'] = 'Bearer ' + config.operator_token
        assert client.get('/api/storage/health').json()['tiers'][2]['status'] == 'AVAILABLE'
    assert (root / '.atze-mode').read_text() == 'test'
