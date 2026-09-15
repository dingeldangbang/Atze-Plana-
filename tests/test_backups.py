"""Backup contract tests: reviewer-triggered verified snapshots, durable records, restore-file verification."""
import hashlib
import sqlite3
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.store import Store
from conftest import seed, task


@pytest.fixture
def settings(tmp_path):
    return Settings(tmp_path / 'test.db', 'operator-test-only-' * 3, 'reviewer-test-only-' * 3,
                    mode='test', challenge_token='challenge-test-only-' * 3)


@pytest.fixture
def client(settings):
    with TestClient(create_app(settings)) as client:
        client.headers['Authorization'] = 'Bearer ' + settings.operator_token
        yield client


@pytest.fixture
def reviewer(settings):
    return {'Authorization': 'Bearer ' + settings.reviewer_token}


def backup_request(reason='Explicit isolated backup test'):
    return {'confirm': True, 'reason': reason, 'note': 'Synthetic test backup, no production claim'}


def create_backup(client, reviewer, **overrides):
    response = client.post('/api/operations/backups', headers=reviewer, json={**backup_request(), **overrides})
    assert response.status_code == 201, response.text
    return response.json()


def test_backup_roles_and_confirmation(client, reviewer):
    """BKP-001: backups are reviewer-confirmed only; operator and unconfirmed requests are refused."""
    assert client.post('/api/operations/backups', json=backup_request()).status_code == 403
    assert client.post('/api/operations/backups', headers=reviewer,
                       json={'confirm': False, 'reason': 'unconfirmed attempt'}).status_code == 422
    assert client.post('/api/operations/backups', headers=reviewer,
                       json={'reason': 'missing confirm field'}).status_code == 422


def test_backup_creates_verified_snapshot_record_and_audit(client, reviewer, settings):
    """BKP-002: real snapshot with matching sha256/size, integrity PASS, per-kind counts equal to the live store, durable audit."""
    project, evidence = seed(client, reviewer)
    task_id = task(client, project, evidence)
    assert task_id
    backup = create_backup(client, reviewer)
    path = settings.db_path.parent / backup['path']
    assert path.exists() and backup['scope'] == 'DATABASE_ONLY' and backup['integrity'] == 'ok'
    assert backup['sha256'] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert backup['size_bytes'] == path.stat().st_size and backup['size_bytes'] > 0
    assert oct(path.stat().st_mode & 0o777) == '0o600'
    with Store(settings.db_path, settings.mode).connect() as live:
        live_counts = dict(live.execute('SELECT kind, COUNT(*) FROM records GROUP BY kind').fetchall())
    # a snapshot cannot contain its own backup record/audit written after the file was taken
    live_counts['audit'] -= 1
    del live_counts['backup']
    assert backup['record_counts'] == live_counts and backup['total_records'] == sum(live_counts.values())
    events = [v['event'] for v in client.get('/api/audit', headers=reviewer).json() if v['event'].startswith('operations.')]
    assert events == ['operations.backup_created']
    assert client.get('/api/operations/backups').json()[0]['id'] == backup['id']


def test_backup_allowed_under_emergency_stop(client, reviewer):
    """BKP-003: a read-only snapshot stays allowed while the emergency stop is active (risk-reducing)."""
    assert client.post('/api/control/stop', headers=reviewer, json={'active': True, 'reason': 'Isolated stop'}).status_code == 200
    backup = create_backup(client, reviewer, reason='Explicit backup while stopped for incident response')
    assert backup['integrity'] == 'ok'
    client.post('/api/control/stop', headers=reviewer, json={'active': False, 'reason': 'Isolated reset'})


def test_backup_snapshots_are_distinct_and_restorable(client, reviewer, settings):
    """BKP-004: two backups are distinct files; each backup file opens read-only, passes quick_check and contains the known records (restore-file verification)."""
    project, evidence = seed(client, reviewer)
    first = create_backup(client, reviewer)
    task(client, project, evidence)
    second = create_backup(client, reviewer, reason='Explicit second backup after more work')
    assert first['id'] != second['id'] and first['sha256'] != second['sha256']
    assert second['total_records'] > first['total_records']
    listing = client.get('/api/operations/backups').json()
    assert {listing[0]['id'], listing[1]['id']} == {first['id'], second['id']}
    for backup in (first, second):
        path = settings.db_path.parent / backup['path']
        restored = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)
        try:
            assert restored.execute('PRAGMA quick_check').fetchall() == [('ok',)]
            assert restored.execute("SELECT COUNT(*) FROM records WHERE id=?", (project['id'],)).fetchone()[0] == 1
            assert restored.execute('SELECT COUNT(*) FROM records WHERE kind=?', ('audit',)).fetchone()[0] > 0
        finally:
            restored.close()
    # honesty: the snapshot contains the state at its own creation time, not later writes
    assert first['total_records'] < second['total_records']
