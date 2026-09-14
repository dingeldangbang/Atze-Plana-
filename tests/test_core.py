"""Executable cases: docstrings identify purpose and expected behavior; JUnit records actual outcome."""
import hashlib
import sqlite3
from datetime import datetime
import pytest
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.triage import evaluate
from conftest import seed, task, challenged_result, process_job_api


def test_config_fails_closed(tmp_path):
    """SEC-001: missing or identical credentials prevent startup; no insecure default."""
    with pytest.raises(ValueError):
        Settings(tmp_path / 'db', '', '')
    with pytest.raises(ValueError):
        Settings(tmp_path / 'db', 'x' * 32, 'x' * 32)


def test_public_surface(client):
    """API-001: health and static UI are public; data and specification require credentials."""
    client.headers.clear()
    assert client.get('/health').json()['status'] == 'ok'
    assert 'Evidence Core' in client.get('/').text
    assert client.get('/static/app.js').status_code == 200
    for path in ['/api/projects', '/api/evidence', '/api/tasks', '/api/audit', '/api/control/stop', '/api/openapi.json']:
        assert client.get(path).status_code == 401
    assert client.get('/docs').status_code == 404
    assert "script-src 'self'" in client.get('/').headers['content-security-policy']


def test_role_separation(client, reviewer):
    """SEC-002: reviewers cannot create projects and operators cannot access audit or stop."""
    assert client.post('/api/projects', headers=reviewer, json={'name': 'Denied'}).status_code == 403
    assert client.get('/api/audit').status_code == 403
    assert client.post('/api/control/stop', json={'active': True, 'reason': 'Denied'}).status_code == 403
    assert client.get('/api/projects', headers={'Authorization': 'Bearer invalid'}).status_code == 401


def test_evidence_provenance_and_review(client, reviewer):
    """EVD-001: content hash is real, evidence starts unverified, review is role-bound and immutable."""
    project, evidence = seed(client, reviewer, verified=False)
    assert evidence['state'] == 'unverified'
    assert evidence['sha256'] == hashlib.sha256(b'Synthetic fixture').hexdigest()
    url = f"/api/evidence/{evidence['id']}/review"
    body = {'state': 'verified', 'reason': 'Reviewed fixture'}
    assert client.post(url, json=body).status_code == 403
    assert client.post(url, headers=reviewer, json=body).status_code == 200
    assert client.post(url, headers=reviewer, json=body).status_code == 409
    assert client.get('/api/evidence').json()[0]['review_reason'] == body['reason']


@pytest.mark.parametrize('action', ['read', 'write', 'flash', 'firmware', 'edl_write', 'production_deploy', 'payment'])
def test_approval_policy(client, reviewer, action):
    """TRI-001: Challenge is mandatory; only READ can be eligible without approval, high-impact decisions remain conditional and never execute."""
    project, evidence = seed(client, reviewer)
    key = task(client, project, evidence, action)
    url = f'/api/tasks/{key}'
    assert client.post(url + '/triage').json()['state'] == 'blocked'
    challenged_result(client, key, evidence['id'])
    decision = client.post(url + '/triage').json()
    assert decision['state'] == ('eligible' if action == 'read' else 'approval_required' if action == 'write' else 'blocked')
    assert decision['validation_status'] == ('ACCEPT' if action in {'read', 'write'} else 'CONDITIONAL')
    assert decision['executed'] is False
    assert client.post(url + '/approve', json={'reason': 'Denied'}).status_code == 403
    response = client.post(url + '/approve', headers=reviewer, json={'reason': 'Explicit fixture approval'})
    assert response.status_code == (201 if action == 'write' else 409)
    if action == 'write':
        assert client.post(url + '/triage').json()['state'] == 'approved'
        assert client.post(url + '/approve', headers=reviewer, json={'reason': 'Duplicate'}).status_code == 409
    assert client.post(url + '/execute').status_code == 404


@pytest.mark.parametrize('confidence,verified,preconditions', [(0.79, True, True), (0.9, False, True), (0.9, True, False)])
def test_blocking_conditions(client, reviewer, confidence, verified, preconditions):
    """TRI-002: low confidence, unverified evidence or absent preconditions block approval."""
    project, evidence = seed(client, reviewer, confidence=confidence, verified=verified)
    key = task(client, project, evidence, 'flash', preconditions)
    decision = client.post(f'/api/tasks/{key}/triage').json()
    assert decision['state'] == 'blocked'
    assert decision['reasons']
    assert client.post(f'/api/tasks/{key}/approve', headers=reviewer, json={'reason': 'Not allowed'}).status_code == 409


def test_emergency_stop_persistent(client, reviewer, settings):
    """SEC-003: persisted stop blocks even approved tasks after application restart."""
    project, evidence = seed(client, reviewer)
    key = task(client, project, evidence, 'write')
    result = challenged_result(client, key, evidence['id'])
    assert client.post(f'/api/tasks/{key}/approve', headers=reviewer, json={'reason': 'Fixture'}).status_code == 201
    assert client.post('/api/control/stop', headers=reviewer, json={'active': True, 'reason': 'Test stop'}).status_code == 200
    with TestClient(create_app(settings)) as restarted:
        decision = restarted.post(f'/api/tasks/{key}/triage', headers=reviewer).json()
        assert decision['state'] == 'blocked'
        assert 'Emergency stop is active' in decision['reasons']
    assert client.post('/api/control/stop', headers=reviewer, json={'active': False, 'reason': 'Resume review'}).status_code == 200
    assert client.post(f'/api/tasks/{key}/triage').json()['state'] == 'blocked'
    assert client.post(f"/api/results/{result['id']}/challenge", json={'reason': 'Recheck after stop reset'}).status_code == 201
    process_job_api(client)
    assert client.post(f'/api/tasks/{key}/triage').json()['state'] == 'approval_required'


def test_input_integrity(client, reviewer):
    """API-002: reject blank names, extra fields, foreign/duplicate/missing references and over-limit lists."""
    for body in [{'name': '   '}, {'name': 'X', 'admin': True}]:
        assert client.post('/api/projects', json=body).status_code == 422
    p, e = seed(client, reviewer)
    other = client.post('/api/projects', json={'name': 'Other'}).json()
    base = {'project_id': other['id'], 'title': 'Invalid', 'action': 'read', 'evidence_ids': [e['id']]}
    assert client.post('/api/tasks', json=base).status_code == 422
    base.update(project_id=p['id'], evidence_ids=[e['id'], e['id']])
    assert client.post('/api/tasks', json=base).status_code == 422
    base['evidence_ids'] = ['missing']
    assert client.post('/api/tasks', json=base).status_code == 404
    assert client.get('/api/projects?limit=101').status_code == 422
    assert client.get('/api/projects?offset=-1').status_code == 422
    assert len(client.get('/api/projects?limit=1&offset=1').json()) == 1


def test_invalid_observation(client, reviewer):
    """EVD-002: future timestamps, non-HTTP URLs and out-of-range confidence are rejected."""
    p, e = seed(client, reviewer)
    body = {k: v for k, v in e.items() if k not in ['id', 'created_at', 'sha256', 'state', 'review_reason']}
    for field, value in [('observed_at', '2999-01-01T00:00:00Z'), ('source_url', 'file:///etc/passwd'), ('confidence', 1.1)]:
        assert client.post('/api/evidence', json={**body, field: value}).status_code == 422


def test_rejected_and_empty_evidence():
    """TRI-003: rejected or absent evidence blocks, including at the confidence threshold."""
    base = {'id': 'unit', 'action': 'read', 'preconditions_met': True, 'evidence_ids': []}
    assert evaluate(base, []).state == 'blocked'
    assert evaluate(base, [{'state': 'rejected', 'confidence': 1}]).state == 'blocked'
    assert evaluate(base, [{'state': 'verified', 'confidence': 0.8}]).state == 'blocked'  # challenge absent


def test_audit_and_transaction(client, reviewer, settings):
    """AUD-001: domain mutation and audit persist together; failed references create neither."""
    p, e = seed(client, reviewer)
    key = task(client, p, e)
    client.post(f'/api/tasks/{key}/triage')
    events = client.get('/api/audit', headers=reviewer).json()
    assert [e['event'] for e in events] == ['project.created', 'evidence.created', 'evidence.reviewed', 'task.created', 'task.triaged']
    assert events[-1]['details']['evidence_ids'] == [e['id']]
    with sqlite3.connect(settings.db_path) as db:
        db.execute("CREATE TRIGGER fail_audit BEFORE INSERT ON records WHEN NEW.kind='audit' BEGIN SELECT RAISE(ABORT, 'test rollback'); END")
    with pytest.raises(sqlite3.IntegrityError):
        client.post('/api/projects', json={'name': 'Must roll back'})
    assert len(client.get('/api/projects').json()) == 1


def test_storage_error_redacted(client, settings):
    """SEC-004: storage failure returns redacted 503, not a SQL or filesystem traceback."""
    with sqlite3.connect(settings.db_path) as db:
        db.execute('DROP TABLE records')
    response = client.get('/api/projects')
    assert response.status_code == 503
    assert response.json() == {'detail': 'Storage unavailable; retry or contact administrator'}


def test_schema(client):
    """DOC-001: authenticated schema reflects supported APIs and bearer authentication."""
    schema = client.get('/api/openapi.json').json()
    assert schema['components']['securitySchemes']['HTTPBearer']['scheme'] == 'bearer'
    assert '/api/tasks/{task_id}/approve' in schema['paths']


def test_stop_read(client, reviewer, settings):
    """SEC-005: both roles inspect the real stop state with recorded revision/actor/time; write stays reviewer-only; an unrecorded legacy change reports unknown provenance instead of invented values."""
    initial = client.get('/api/control/stop').json()
    assert initial == {'active': False, 'reason': 'Initial state', 'revision': 0,
                       'actor': None, 'created_at': None, 'record_id': None}
    first = client.post('/api/control/stop', headers=reviewer, json={'active': True, 'reason': 'Readback test'}).json()
    assert set(first) == {'active', 'reason', 'revision', 'actor', 'created_at', 'record_id'}
    assert first['active'] is True and first['reason'] == 'Readback test'
    assert first['revision'] == 1 and first['actor'] == 'reviewer'
    assert datetime.fromisoformat(first['created_at']).tzinfo is not None
    assert client.get('/api/control/stop').json() == first
    second = client.post('/api/control/stop', headers=reviewer, json={'active': False, 'reason': 'Resume review'}).json()
    assert second['revision'] == 2 and second['record_id'] != first['record_id']
    with sqlite3.connect(settings.db_path) as db:
        db.execute("UPDATE control SET active=1,reason='Legacy change without provenance record'")
    assert client.get('/api/control/stop').json() == {
        'active': True, 'reason': 'Legacy change without provenance record',
        'revision': 0, 'actor': None, 'created_at': None, 'record_id': None}


def test_schema_only_instance_fails_closed(settings):
    """DOC-005: a schema-only instance has no runtime store, so health returns an honest 503 instead of asserting ok or raising an unhandled error, while every data route still refuses access."""
    from app.main import create_app
    with TestClient(create_app(schema_only=True)) as schema_client:
        response = schema_client.get('/health')
        assert response.status_code == 503
        assert response.json() == {'detail': 'Schema-only instance has no runtime store; health is not assertable'}
        for path in ['/api/runtime', '/api/projects', '/api/storage/health', '/api/ai/status', '/api/openapi.json']:
            assert schema_client.get(path).status_code == 401
        claim = schema_client.post('/api/challenge/jobs/claim',
                                   headers={'Authorization': 'Bearer ' + settings.challenge_token})
        assert claim.status_code == 503 and 'NOT CONFIGURED' in claim.json()['detail']
        assert '/api/tasks/{task_id}/approve' in create_app(schema_only=True).openapi()['paths']
