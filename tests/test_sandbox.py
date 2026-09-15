"""Sandbox worker contract tests: real isolated subprocess re-verification with rlimits and hard timeout."""
import base64
import json
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.sandbox import run_isolated
from conftest import seed

ROOT = Path(__file__).resolve().parents[1]


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


def upload(client, content=b'synthetic sandbox verification bytes', name='sandbox-resource'):
    response = client.post('/api/resources', json={'name': name, 'kind': 'file',
                                                   'source': 'Owner-declared fixture file',
                                                   'description': 'Synthetic sandbox fixture',
                                                   'content_base64': base64.b64encode(content).decode()})
    assert response.status_code == 201, response.text
    return response.json()


def verify(client, reviewer, resource_id, reason='Explicit isolated re-verification'):
    response = client.post(f'/api/operations/verify/resource/{resource_id}', headers=reviewer,
                           json={'confirm': True, 'reason': reason})
    assert response.status_code == 201, response.text
    return response.json()


def test_sandbox_reverification_match_and_audit(client, reviewer):
    """SBX-001: an intact object re-verifies byte-exact in a separate process with a durable record and audit."""
    resource = upload(client)
    result = verify(client, reviewer, resource['id'])
    assert result['outcome'] == 'MATCH' and result['job_result']['recomputed_sha256'] == resource['sha256']
    assert result['sandbox']['exit_code'] == 0 and result['sandbox']['timed_out'] is False
    assert result['sandbox']['duration_seconds'] > 0
    assert 'NOT a network/filesystem namespace' in result['sandbox']['isolation']
    events = [v['event'] for v in client.get('/api/audit', headers=reviewer).json() if v['event'].startswith('operations.')]
    assert events == ['operations.resource_verified']


def test_sandbox_reverification_detects_real_corruption(client, reviewer, settings):
    """SBX-002: tampering with the stored object bytes on disk yields MISMATCH (fail-closed detection, no fake PASS)."""
    resource = upload(client, content=b'original bytes that will be tampered with')
    object_path = settings.db_path.parent / 'objects' / (resource['key'] + '.blob')
    assert object_path.exists()
    object_path.write_bytes(b'tampered bytes replacing the original object')
    result = verify(client, reviewer, resource['id'], reason='Explicit corruption detection test')
    assert result['outcome'] == 'MISMATCH' and result['job_result']['recomputed_sha256'] != resource['sha256']


def test_sandbox_reverification_unavailable_object(client, reviewer, settings):
    """SBX-003: a missing object file reports UNAVAILABLE, never a silent PASS."""
    resource = upload(client, content=b'bytes that will disappear')
    object_path = settings.db_path.parent / 'objects' / (resource['key'] + '.blob')
    object_path.unlink()
    result = verify(client, reviewer, resource['id'], reason='Explicit unavailability test')
    assert result['outcome'].startswith('UNAVAILABLE:')


def test_sandbox_roles_stop_and_targets(client, reviewer):
    """SBX-004: verification is reviewer-confirmed; unknown resources 404; the emergency stop blocks execution."""
    resource = upload(client, name='sandbox-roles')
    assert client.post(f"/api/operations/verify/resource/{resource['id']}",
                       json={'confirm': True, 'reason': 'operator attempt'}).status_code == 403
    assert client.post(f"/api/operations/verify/resource/{resource['id']}", headers=reviewer,
                       json={'confirm': False, 'reason': 'unconfirmed'}).status_code == 422
    assert client.post('/api/operations/verify/resource/missing-resource', headers=reviewer,
                       json={'confirm': True, 'reason': 'unknown target'}).status_code == 404
    assert client.post('/api/control/stop', headers=reviewer, json={'active': True, 'reason': 'Isolated stop'}).status_code == 200
    assert client.post(f"/api/operations/verify/resource/{resource['id']}", headers=reviewer,
                       json={'confirm': True, 'reason': 'stopped attempt'}).status_code == 409


def test_sandbox_rlimits_are_real():
    """SBX-005: the memory rlimit kills an over-allocating child; the hard timeout kills a hanging child."""
    memory = run_isolated([sys.executable, '-c', 'data = bytearray(300 * 1024 * 1024)'],
                          timeout_seconds=15, memory_mb=64)
    assert memory['exit_code'] != 0 and memory['timed_out'] is False
    timeout = run_isolated([sys.executable, '-c', 'import time; time.sleep(30)'],
                           timeout_seconds=2, memory_mb=256)
    assert timeout['timed_out'] is True and timeout['duration_seconds'] < 10
    clean = run_isolated([sys.executable, '-c', 'print("bounded child output")'],
                         timeout_seconds=10, memory_mb=256)
    assert clean['exit_code'] == 0 and 'bounded child output' in clean['stdout_tail']
