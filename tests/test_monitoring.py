"""Monitoring and integration registry contract tests: real aggregation of stored records, no invented state."""
import base64
import pytest
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from test_ai_privacy import ai, receiver  # real isolated loopback transport fixtures, not model inference
from test_agents import declare, assign_task, prepare_run, consent  # reuse the proven agent run helpers

TELEMETRY_TOKEN = 'telemetry-device-test-' * 3


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


def sample(sensor_id, value, timestamp):
    return {'sensor_id': sensor_id, 'value': value, 'timestamp': timestamp}


def populated_workspace(client, device_headers):
    """Real records only: project, evidence, task, device, sensors, two batches, resource."""
    project = client.post('/api/projects', json={'name': 'Monitoring fixture project'}).json()
    evidence = client.post('/api/evidence', json={
        'project_id': project['id'], 'claim': 'Synthetic monitoring fixture input, not a hardware observation',
        'source_url': 'https://example.com/monitoring', 'observed_at': '2026-01-01T00:00:00Z',
        'source_type': 'manual', 'provider': 'pytest fixture', 'extraction_method': 'manual',
        'content': 'Synthetic fixture', 'confidence': 0.9,
        'observations': [{'subject': 'fixture-object', 'variant': 'v1', 'revision': 'r1', 'attribute': 'format',
                          'value': 'text', 'unit': 'label', 'conditions': 'synthetic', 'basis': 'manual'}]}).json()
    task_id = client.post('/api/tasks', json={'project_id': project['id'], 'title': 'Monitoring task', 'action': 'read',
                                              'evidence_ids': [evidence['id']], 'preconditions_met': True}).json()['id']
    device = client.post('/api/telemetry/devices', json={'name': 'monitoring-bench', 'description': 'Fixture device'}).json()
    in_range = client.post(f"/api/telemetry/devices/{device['id']}/sensors",
                           json={'name': 'pack-voltage', 'kind': 'voltage', 'unit': 'V',
                                 'declared_range': {'minimum': 30.0, 'maximum': 60.0}}).json()
    plain = client.post(f"/api/telemetry/devices/{device['id']}/sensors",
                        json={'name': 'motor-rpm', 'kind': 'rpm'}).json()
    batch_a = client.post('/api/telemetry/ingest', headers=device_headers, json={
        'samples': [sample(in_range['id'], 48.1, '2026-01-02T03:04:05+00:00'),
                    sample(in_range['id'], 95.0, '2026-01-02T03:04:06+00:00'),
                    sample(plain['id'], 1200, '2026-01-02T03:04:07+00:00')],
        'session': 'bench-run-1', 'conditions': 'fixture bench run'}).json()
    batch_b = client.post('/api/telemetry/ingest', headers=device_headers, json={
        'samples': [sample(in_range['id'], 50.0, '2026-01-02T04:04:05+00:00')],
        'session': 'bench-run-1', 'conditions': 'fixture bench run'}).json()
    resource = client.post('/api/resources', json={
        'name': 'monitoring-config', 'kind': 'configuration', 'source': 'Owner-declared fixture file',
        'description': 'Synthetic monitoring fixture resource',
        'content_base64': base64.b64encode(b'synthetic monitoring bytes').decode()}).json()
    return project, evidence, task_id, device, in_range, plain, batch_a, batch_b, resource


def test_monitoring_overview_counts_real_records_exactly(client, device_headers):
    """MON-001: overview aggregates only real stored records; sums equal the batch metadata of real ingestions."""
    project, evidence, task_id, device, in_range, plain, batch_a, batch_b, resource = populated_workspace(client, device_headers)
    assert project['id'] and evidence['id'] and task_id
    overview = client.get('/api/monitoring/overview').json()
    counts = overview['counts']
    assert counts['projects'] == 1 and counts['evidence'] == 1 and counts['tasks'] == 1 and counts['results'] == 0
    assert counts['telemetry_devices'] == {'active': 1, 'deactivated': 0}
    assert counts['telemetry_sensors'] == {'active': 2, 'deactivated': 0}
    assert counts['telemetry_batches'] == 2
    assert counts['telemetry_samples'] == batch_a['sample_count'] + batch_b['sample_count'] == 4
    assert counts['telemetry_flagged_out_of_range'] == batch_a['flagged_out_of_range'] + batch_b['flagged_out_of_range'] == 1
    assert counts['telemetry_suspect_samples'] == 0
    assert counts['resources'] == {'active': 1, 'deactivated': 0}
    assert counts['resource_versions_stored_bytes'] == resource['size_bytes']
    assert counts['agents'] == {'active': 0, 'deactivated': 0}
    assert counts['agent_runs'] == {'awaiting_consent': 0, 'draft_unchallenged': 0, 'blocked': 0, 'unavailable': 0}
    assert overview['stop_active'] is False
    assert 'no device/provider health' in overview['disclaimer']
    assert overview['integrations']['telemetry_ingest'] == {'configured': True, 'transport': 'HTTPS_ONLY',
                                                            'note': 'WS/MQTT/Serial NOT IMPLEMENTED'}
    assert overview['integrations']['brightdata_mcp']['configured'] is False
    assert overview['integrations']['brightdata_mcp']['validation'] == 'NOT_LIVE_VALIDATED'
    assert overview['storage']['tiers'] and overview['storage']['source_retention'] is True


def test_monitoring_roles_and_authentication(client, reviewer, tmp_path):
    """MON-002: both roles may read overview and integrations; anonymous and invalid access are refused (fail-closed)."""
    assert client.get('/api/monitoring/overview').status_code == 200
    assert client.get('/api/integrations').status_code == 200
    assert client.get('/api/monitoring/overview', headers=reviewer).status_code == 200
    assert client.get('/api/integrations', headers=reviewer).status_code == 200
    assert client.get('/api/monitoring/overview', headers={'Authorization': 'Bearer invalid'}).status_code == 401
    anonymous_settings = Settings(tmp_path / 'anonymous.db', 'operator-test-only-' * 3, 'reviewer-test-only-' * 3, mode='test')
    with TestClient(create_app(anonymous_settings)) as anonymous:
        assert anonymous.get('/api/monitoring/overview').status_code == 401
        assert anonymous.get('/api/integrations').status_code == 401


def test_monitoring_overview_readable_while_stop_active(client, reviewer, device_headers):
    """MON-003: the emergency stop blocks mutations, never the read-only monitoring view; the stop flag is reported."""
    populated_workspace(client, device_headers)
    stop = client.post('/api/control/stop', headers=reviewer, json={'active': True, 'reason': 'Fixture stop for read-only check'})
    assert stop.status_code == 200
    response = client.get('/api/monitoring/overview')
    assert response.status_code == 200
    assert response.json()['stop_active'] is True
    assert client.post('/api/telemetry/devices', json={'name': 'blocked-device', 'description': ''}).status_code == 409


def test_integration_registry_lists_only_real_routes(client, device_headers):
    """MON-004: every manageable entry names an add/remove route that matches a really registered endpoint."""
    project, evidence, task_id, device, in_range, plain, batch_a, batch_b, resource = populated_workspace(client, device_headers)
    registry = client.get('/api/integrations').json()
    manageable = registry['manageable']
    assert {entry['binding'] for entry in manageable} == {'telemetry_device', 'resource'}
    device_entry = next(e for e in manageable if e['binding'] == 'telemetry_device' and e['id'] == device['id'])
    assert device_entry['state'] == 'active'
    assert device_entry['actions']['add'] == {'route': 'POST /api/telemetry/devices', 'role': 'operator'}
    assert {s['id'] for s in device_entry['sensors']} == {in_range['id'], plain['id']}
    registered = [(method, route.path_regex) for route in client.app.routes for method in getattr(route, 'methods', set())]
    checked = 0
    for entry in manageable + [s for e in manageable if e.get('sensors') for s in e['sensors']]:
        for action in entry['actions'].values():
            method, path = action['route'].split(' ')
            assert any(m == method and regex.fullmatch(path) for m, regex in registered), action['route']
            checked += 1
    assert checked >= 4
    assert registry['removal_semantics'].startswith('Reviewer-confirmed deactivation only')
    assert 'no deletion endpoint exists' in registry['removal_semantics']
    assert 'real implemented endpoint' in registry['action_note']


def test_integration_registry_remove_action_only_for_active(client, reviewer, device_headers):
    """MON-005: deactivated bindings lose the remove action; nested sensors keep state and retained data."""
    project, evidence, task_id, device, in_range, plain, batch_a, batch_b, resource = populated_workspace(client, device_headers)
    assert client.post(f"/api/telemetry/sensors/{in_range['id']}/deactivate", headers=reviewer,
                       json={'confirm': True, 'reason': 'Fixture sensor decommission'}).status_code == 200
    registry = client.get('/api/integrations').json()
    device_entry = next(e for e in registry['manageable'] if e['binding'] == 'telemetry_device' and e['id'] == device['id'])
    states = {s['id']: s for s in device_entry['sensors']}
    assert states[in_range['id']]['state'] == 'deactivated'
    assert 'remove' not in states[in_range['id']]['actions']
    assert states[plain['id']]['state'] == 'active' and 'remove' in states[plain['id']]['actions']
    assert len(client.get(f"/api/telemetry/devices/{device['id']}/sensors").json()) == 2  # nothing removed
    overview = client.get('/api/monitoring/overview').json()['counts']
    assert overview['telemetry_sensors'] == {'active': 1, 'deactivated': 1}
    assert overview['telemetry_batches'] == 2 and overview['telemetry_samples'] == 4


def test_device_deactivation_reflected_and_data_retained(client, reviewer, device_headers):
    """MON-006: reviewer-confirmed device deactivation moves the count; records, batches and audit history are retained."""
    project, evidence, task_id, device, in_range, plain, batch_a, batch_b, resource = populated_workspace(client, device_headers)
    assert client.post(f"/api/telemetry/devices/{device['id']}/deactivate",
                       json={'confirm': True, 'reason': 'Fixture device removal'}).status_code == 403
    assert client.post(f"/api/telemetry/devices/{device['id']}/deactivate", headers=reviewer,
                       json={'confirm': False, 'reason': 'unconfirmed attempt'}).status_code == 422
    assert client.post(f"/api/telemetry/devices/{device['id']}/deactivate", headers=reviewer,
                       json={'confirm': True, 'reason': 'Fixture device removal'}).status_code == 200
    counts = client.get('/api/monitoring/overview').json()['counts']
    assert counts['telemetry_devices'] == {'active': 0, 'deactivated': 1}
    assert counts['telemetry_batches'] == 2 and counts['telemetry_samples'] == 4  # history fully retained
    registry = client.get('/api/integrations').json()['manageable']
    device_entry = next(e for e in registry if e['binding'] == 'telemetry_device' and e['id'] == device['id'])
    assert device_entry['state'] == 'deactivated' and 'remove' not in device_entry['actions']
    audit = client.get('/api/audit', headers=reviewer, params={'limit': 100}).json()
    assert any(entry['event'] == 'telemetry.device_deactivated' and entry['entity_id'] == device['id'] for entry in audit)


def test_agent_run_states_counted(ai):
    """MON-007: overview counts agents and agent runs by real state after prepare and a default-deny consent outcome."""
    client, reviewer, body, pol, seen, *_ = ai
    agent = declare(client, body['model_id'])
    assert client.get('/api/monitoring/overview').json()['counts']['agents'] == {'active': 1, 'deactivated': 0}
    assign_task(client, agent, body['task_id'])
    run = prepare_run(client, agent, body['task_id'])
    counts = client.get('/api/monitoring/overview').json()['counts']
    assert counts['agent_runs'] == {'awaiting_consent': 1, 'draft_unchallenged': 0, 'blocked': 0, 'unavailable': 0}
    result = consent(client, reviewer, agent, run).json()
    assert result['agent_run']['state'] == 'BLOCKED' and seen == []
    counts = client.get('/api/monitoring/overview').json()['counts']
    assert counts['agent_runs'] == {'awaiting_consent': 0, 'draft_unchallenged': 0, 'blocked': 1, 'unavailable': 0}
    entry = next(e for e in client.get('/api/integrations').json()['manageable'] if e['binding'] == 'agent')
    assert entry['purpose'] == 'analysis' and entry['model_id'] == body['model_id'] and entry['state'] == 'active'


def test_environment_bound_integrations_display_only(client, settings):
    """MON-008: environment-bound integrations are displayed with server-environment semantics, never runtime-manageable."""
    registry = client.get('/api/integrations').json()
    environment = {entry['binding']: entry for entry in registry['environment_bound']}
    assert set(environment) == {'brightdata_mcp', 'telemetry_device_fleet'}
    assert environment['brightdata_mcp']['state'] == 'NOT_CONFIGURED'
    assert environment['telemetry_device_fleet']['state'] == 'CONFIGURED'
    for entry in registry['environment_bound']:
        assert entry['management'].endswith('runtime add/remove NOT IMPLEMENTED')
        assert 'actions' not in entry
    assert not any('actions' in e for e in registry['environment_bound'])


def test_ai_provider_bindings_follow_gateway_configuration(client):
    """MON-009: configured AI providers appear as environment-bound entries marked configured-not-validated."""
    registry = client.get('/api/integrations').json()
    provider_entries = [e for e in registry['environment_bound'] if e['binding'] == 'ai_provider']
    overview = client.get('/api/monitoring/overview').json()['integrations']['ai_providers']
    assert provider_entries == [{'binding': 'ai_provider', 'id': p['id'], 'state': 'CONFIGURED_NOT_VALIDATED',
                                 'management': 'ATZE_AI_CONFIG server environment; runtime add/remove NOT IMPLEMENTED'}
                                for p in overview]
    assert all('actions' not in entry for entry in provider_entries)
