import pytest
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app


@pytest.fixture
def settings(tmp_path):
    return Settings(tmp_path / 'test.db', 'operator-test-only-' * 3, 'reviewer-test-only-' * 3, mode='test')


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
        'content': 'Synthetic fixture', 'confidence': confidence}).json()
    if verified:
        assert client.post(f"/api/evidence/{evidence['id']}/review", headers=reviewer,
                           json={'state': 'verified', 'reason': 'Fixture reviewed in test'}).status_code == 200
    return project, evidence


def task(client, project, evidence, action='read', preconditions=True):
    response = client.post('/api/tasks', json={'project_id': project['id'], 'title': 'Test task',
                           'action': action, 'evidence_ids': [evidence['id']], 'preconditions_met': preconditions})
    assert response.status_code == 201, response.text
    return response.json()['id']
