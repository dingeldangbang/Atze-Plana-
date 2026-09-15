"""Evidence analysis contract tests: deterministic contradiction candidates and source ranking; CALCULATED, never truth."""
import pytest
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from conftest import seed, observation


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


def evidence_body(project_id, observations, claim='Synthetic analysis fixture', confidence=0.9, observed_at='2026-01-01T00:00:00Z'):
    return {'project_id': project_id, 'claim': claim, 'source_url': 'https://example.com/analysis',
            'observed_at': observed_at, 'source_type': 'manual', 'provider': 'pytest fixture',
            'extraction_method': 'manual', 'content': 'Synthetic analysis fixture content', 'confidence': confidence,
            'observations': observations}


def test_contradiction_candidates_across_and_within_records(client, reviewer):
    """EVA-001: differing values for the same (subject, attribute) become CALCULATED candidates, never verdicts."""
    project = client.post('/api/projects', json={'name': 'Analysis fixture project'}).json()
    first = client.post('/api/evidence', json=evidence_body(project['id'], [
        observation(subject='motor-temp', attribute='value', value='41.5', unit='C'),
        observation(subject='motor-temp', attribute='value', value='44.0', unit='C')])).json()
    second = client.post('/api/evidence', json=evidence_body(project['id'], [
        observation(subject='motor-temp', attribute='value', value='44.0', unit='C')])).json()
    client.post(f"/api/evidence/{first['id']}/review", headers=reviewer, json={'state': 'verified', 'reason': 'Fixture review'})
    result = client.post('/api/analysis/contradictions', json={'project_id': project['id']}).json()
    assert result['result_class'] == 'CALCULATED' and result['prediction'] == 'NONE'
    assert result['evidence_count'] == 2 and result['observation_count'] == 3
    candidates = result['contradiction_candidates']
    assert len(candidates) == 1 and candidates[0]['subject'] == 'motor-temp' and candidates[0]['attribute'] == 'value'
    assert candidates[0]['scope'] == 'across_records' and len(candidates[0]['values']) == 3
    states = {value['evidence_id']: value['evidence_state'] for value in candidates[0]['values']}
    assert states[first['id']] == 'verified' and states[second['id']] == 'unverified'
    assert 'candidates for human resolution' in result['limits']


def test_contradiction_within_single_record_flagged(client):
    """EVA-002: conflicting observations inside one evidence record are flagged scope within_record."""
    project = client.post('/api/projects', json={'name': 'Within-record project'}).json()
    client.post('/api/evidence', json=evidence_body(project['id'], [
        observation(subject='cell-1', attribute='voltage', value='3.9', unit='V'),
        observation(subject='cell-1', attribute='voltage', value='4.1', unit='V')]))
    result = client.post('/api/analysis/contradictions', json={'project_id': project['id']}).json()
    assert [candidate['scope'] for candidate in result['contradiction_candidates']] == ['within_record']


def test_corroboration_and_unit_mismatch(client):
    """EVA-003: identical value+unit across records corroborates; a unit difference alone is a conflict."""
    project = client.post('/api/projects', json={'name': 'Corroboration project'}).json()
    client.post('/api/evidence', json=evidence_body(project['id'], [observation(subject='rpm', attribute='idle', value='1200', unit='rpm')]))
    client.post('/api/evidence', json=evidence_body(project['id'], [observation(subject='rpm', attribute='idle', value='1200', unit='rpm')]))
    client.post('/api/evidence', json=evidence_body(project['id'], [observation(subject='rpm', attribute='idle', value='1200', unit='krpm')]))
    result = client.post('/api/analysis/contradictions', json={'project_id': project['id']}).json()
    assert result['contradiction_candidates'] and result['contradiction_candidates'][0]['scope'] == 'across_records'
    assert result['corroborated_subject_attributes'] == []
    clean = client.post('/api/projects', json={'name': 'Clean project'}).json()
    client.post('/api/evidence', json=evidence_body(clean['id'], [observation(subject='rpm', attribute='idle', value='1200', unit='rpm')]))
    client.post('/api/evidence', json=evidence_body(clean['id'], [observation(subject='rpm', attribute='idle', value='1200', unit='rpm')]))
    result = client.post('/api/analysis/contradictions', json={'project_id': clean['id']}).json()
    assert result['contradiction_candidates'] == []
    assert result['corroborated_subject_attributes'][0]['occurrences'] == 2


def test_contradictions_isolated_per_project_and_validated(client, settings):
    """EVA-004: analysis is scoped to one project; unknown projects 404; both roles may query, anonymous 401."""
    project = client.post('/api/projects', json={'name': 'Isolated project'}).json()
    client.post('/api/evidence', json=evidence_body(project['id'], [observation(subject='x', attribute='y', value='1', unit='u')]))
    other = client.post('/api/projects', json={'name': 'Other project'}).json()
    client.post('/api/evidence', json=evidence_body(other['id'], [observation(subject='x', attribute='y', value='2', unit='u')]))
    result = client.post('/api/analysis/contradictions', json={'project_id': project['id']}).json()
    assert result['contradiction_candidates'] == [] and result['evidence_count'] == 1
    assert client.post('/api/analysis/contradictions', json={'project_id': 'missing'}).status_code == 404
    assert client.post('/api/analysis/contradictions', json={'project_id': other['id']}).status_code == 200
    anonymous = TestClient(create_app(Settings(settings.db_path, settings.operator_token, settings.reviewer_token, mode='test')))
    assert anonymous.post('/api/analysis/contradictions', json={'project_id': project['id']}).status_code == 401


def test_source_ranking_deterministic_with_trace(client, reviewer):
    """EVA-005: documented rule order (review state, confidence, recency) with a per-item rule trace; not a truth claim."""
    project = client.post('/api/projects', json={'name': 'Ranking project'}).json()
    rejected = client.post('/api/evidence', json=evidence_body(project['id'], [], claim='rejected claim', confidence=0.99)).json()
    unverified = client.post('/api/evidence', json=evidence_body(project['id'], [], claim='unverified strong',
                                                                 confidence=0.95, observed_at='2026-02-01T00:00:00Z')).json()
    verified = client.post('/api/evidence', json=evidence_body(project['id'], [], claim='verified claim',
                                                               confidence=0.7, observed_at='2026-01-01T00:00:00Z')).json()
    client.post(f"/api/evidence/{verified['id']}/review", headers=reviewer, json={'state': 'verified', 'reason': 'Fixture review'})
    client.post(f"/api/evidence/{rejected['id']}/review", headers=reviewer, json={'state': 'rejected', 'reason': 'Fixture rejection'})
    result = client.get('/api/analysis/source-ranking', params={'project_id': project['id']}).json()
    order = [row['evidence_id'] for row in result['ranking']]
    assert order == [verified['id'], unverified['id'], rejected['id']]
    assert result['ranking'][0]['rule_trace'] == ['review_state=verified', 'confidence=0.7', 'observed_at=2026-01-01T00:00:00Z']
    assert result['rules'][0].startswith('1. review state')
    assert 'not a truth or source-quality guarantee' in result['limits']
    repeat = client.get('/api/analysis/source-ranking', params={'project_id': project['id']}).json()
    assert repeat['ranking'] == result['ranking']  # deterministic, no hidden state
    assert client.get('/api/analysis/source-ranking', params={'project_id': 'missing'}).status_code == 404
