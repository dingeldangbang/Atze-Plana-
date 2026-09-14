import pytest
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app


@pytest.fixture
def settings(tmp_path):
    return Settings(tmp_path / 'test.db', 'operator-test-only-' * 3, 'reviewer-test-only-' * 3, mode='test', challenge_token='challenge-test-only-' * 3)


@pytest.fixture
def client(settings):
    with TestClient(create_app(settings)) as client:
        client.headers['Authorization'] = 'Bearer ' + settings.operator_token
        yield client


@pytest.fixture
def reviewer(settings):
    return {'Authorization': 'Bearer ' + settings.reviewer_token}


def seed(client, reviewer, *, confidence=0.9, verified=True):
    project = client.post('/api/projects', json={'name': 'Test project'}).json()
    evidence = client.post('/api/evidence', json={
        'project_id': project['id'], 'claim': 'Synthetic test input, not a hardware observation',
        'source_url': 'https://example.com/test', 'observed_at': '2026-01-01T00:00:00Z',
        'source_type': 'manual', 'provider': 'pytest fixture', 'extraction_method': 'manual',
        'content': 'Synthetic fixture', 'confidence': confidence, 'observations': [observation(), observation('synthetic-alternative')]}).json()
    if verified:
        assert client.post(f"/api/evidence/{evidence['id']}/review", headers=reviewer,
                           json={'state': 'verified', 'reason': 'Fixture reviewed in test'}).status_code == 200
    return project, evidence


def task(client, project, evidence, action='read', preconditions=True):
    response = client.post('/api/tasks', json={'project_id': project['id'], 'title': 'Test task',
                           'action': action, 'evidence_ids': [evidence['id']], 'preconditions_met': preconditions})
    assert response.status_code == 201, response.text
    return response.json()['id']


def observation(subject='synthetic-object', **overrides):
    return {**dict(subject=subject, variant='fixture-v1', revision='fixture-r1', attribute='format', value='text',
                   unit='label', conditions='synthetic fixture only', basis='manual'), **overrides}


def result_body(task_id, evidence_id):
    claim = observation()
    claim.pop('basis')
    return {'task_id': task_id, 'kind': 'plan', 'primary_worker': 'manual synthetic test input',
            'summary': 'Compare submitted fixture properties only; not hardware suitability',
            'claims': [{**claim, 'evidence_ids': [evidence_id], 'requires_measurement': False}],
            'alternatives': [], 'unknowns': [], 'falsification_test': 'Compare original fixture text against declared format'}


def process_job_api(client):
    """Protocol/algorithm test helper; separate OS worker is exercised by HTTP smoke."""
    from app.challenge_rules import analyze
    headers = {'Authorization': 'Bearer ' + 'challenge-test-only-' * 3}
    response = client.post('/api/challenge/jobs/claim', headers=headers)
    assert response.status_code == 200, response.text
    job = response.json()
    if job is None:
        return None
    result = client.post(f"/api/challenge/jobs/{job['job_id']}/complete", headers=headers,
                         json={'lease': job['lease'], 'fingerprint': job['fingerprint'],
                               'analysis': analyze(job['snapshot']).model_dump()})
    assert result.status_code == 201, result.text
    return result.json()


def challenged_result(client, task_id, evidence_id):
    response = client.post('/api/results', json=result_body(task_id, evidence_id))
    assert response.status_code == 201, response.text
    process_job_api(client)
    return response.json()
