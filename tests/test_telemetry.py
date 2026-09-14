"""Telemetry contract tests: real submitted measurements, declared identities, fail-closed auth."""
import json
import pytest
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app

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


def unconfigured(tmp_path):
    return Settings(tmp_path / 'unconfigured.db', 'operator-test-only-' * 3, 'reviewer-test-only-' * 3, mode='test')


def device_body(name='ESP32 bench unit'):
    return {'name': name, 'description': 'Owner-declared test device fixture, no hardware claim'}


def sensor_body(name='pack-voltage', kind='voltage', unit='V', declared_range=None, identification='IDENTIFIED'):
    return {'name': name, 'kind': kind, 'unit': unit, 'declared_range': declared_range, 'identification': identification,
            'note': 'Owner-declared sensor fixture'}


def sample(sensor_id, value=48.1, timestamp='2026-01-02T03:04:05+00:00', quality='ok'):
    return {'sensor_id': sensor_id, 'value': value, 'timestamp': timestamp, 'quality': quality}


def register_device_with_sensors(client, sensor_specs=(('pack-voltage', 'voltage', 'V', {'minimum': 30.0, 'maximum': 60.0}),), name='ESP32 bench unit'):
    device = client.post('/api/telemetry/devices', json=device_body(name)).json()
    sensors = [client.post(f"/api/telemetry/devices/{device['id']}/sensors", json=sensor_body(*spec)).json()
               for spec in sensor_specs]
    return device, sensors


def test_settings_require_separate_long_telemetry_token():
    """TEL-001: settings reject short or platform-shared telemetry tokens; separate >=32 char credential enforced."""
    with pytest.raises(ValueError):
        Settings('x.db', 'operator-test-only-' * 3, 'reviewer-test-only-' * 3, mode='test',
                 telemetry_token='short')
    with pytest.raises(ValueError):
        Settings('x.db', 'operator-test-only-' * 3, 'reviewer-test-only-' * 3, mode='test',
                 telemetry_token='operator-test-only-' * 3)


def test_ingest_fail_closed_without_configured_token(tmp_path):
    """TEL-002: blank ATZE_TELEMETRY_TOKEN keeps ingest fail-closed (403 not configured, 401 without bearer); registry still works."""
    settings = unconfigured(tmp_path)
    with TestClient(create_app(settings)) as unconfigured_client:
        unconfigured_client.headers['Authorization'] = 'Bearer ' + settings.operator_token
        device, sensors = register_device_with_sensors(unconfigured_client)
        response = unconfigured_client.post('/api/telemetry/ingest', headers={'Authorization': 'Bearer ' + TELEMETRY_TOKEN},
                                            json={'samples': [sample(sensors[0]['id'])]})
        assert response.status_code == 403
        assert 'not configured' in response.json()['detail'].lower()
        unconfigured_client.headers.pop('Authorization')
        assert unconfigured_client.post('/api/telemetry/ingest', json={'samples': [sample(sensors[0]['id'])]}).status_code == 401


def test_ingest_rejects_wrong_or_missing_token(client, device_headers):
    """TEL-003: ingest requires the exact device token; missing/unknown bearer rejected 401, valid token accepted."""
    device, sensors = register_device_with_sensors(client)
    body = {'samples': [sample(sensors[0]['id'])]}
    assert client.post('/api/telemetry/ingest', json=body).status_code == 401
    assert client.post('/api/telemetry/ingest', headers={'Authorization': 'Bearer wrong-token-' * 4},
                       json=body).status_code == 401
    assert client.post('/api/telemetry/ingest', headers=device_headers, json=body).status_code == 201


def test_platform_tokens_are_not_telemetry_tokens(client, reviewer):
    """TEL-004: operator/reviewer platform credentials never authorize telemetry ingest."""
    device, sensors = register_device_with_sensors(client)
    body = {'samples': [sample(sensors[0]['id'])]}
    assert client.post('/api/telemetry/ingest', json=body).status_code == 401
    assert client.post('/api/telemetry/ingest', headers=reviewer, json=body).status_code == 401


def test_device_registry_requires_operator_and_rejects_duplicates(client, reviewer):
    """TEL-005: device registration is operator-only, workspace-unique names, 409 duplicates, empty registry reads."""
    assert client.get('/api/telemetry/devices').json() == []
    assert client.post('/api/telemetry/devices', headers=reviewer, json=device_body()).status_code == 403
    created = client.post('/api/telemetry/devices', json=device_body())
    assert created.status_code == 201
    assert created.json()['state'] == 'active'
    assert client.post('/api/telemetry/devices', json=device_body()).status_code == 409
    assert len(client.get('/api/telemetry/devices').json()) == 1
    assert client.get(f"/api/telemetry/devices/{created.json()['id']}/sensors").json() == []


def test_sensor_declaration_validates_kind_and_range(client):
    """TEL-006: sensor declaration validates fixed kinds, ordered declared_range, per-device unique names."""
    device = client.post('/api/telemetry/devices', json=device_body()).json()
    assert client.post(f"/api/telemetry/devices/{device['id']}/sensors",
                       json=sensor_body('motor-rpm', 'rpm', 'rpm')).status_code == 201
    assert client.post(f"/api/telemetry/devices/{device['id']}/sensors",
                       json=sensor_body('bad-kind', 'watt', 'W')).status_code == 422
    assert client.post(f"/api/telemetry/devices/{device['id']}/sensors",
                       json=sensor_body('reversed', 'voltage', 'V', {'minimum': 60.0, 'maximum': 30.0})).status_code == 422
    assert client.post(f"/api/telemetry/devices/{device['id']}/sensors",
                       json=sensor_body('equal', 'voltage', 'V', {'minimum': 30.0, 'maximum': 30.0})).status_code == 422
    assert client.post(f"/api/telemetry/devices/{device['id']}/sensors",
                       json=sensor_body('motor-rpm', 'rpm', 'rpm')).status_code == 409
    sensors = client.get(f"/api/telemetry/devices/{device['id']}/sensors").json()
    assert [s['name'] for s in sensors] == ['motor-rpm']


def test_ingest_stores_and_returns_verified_batch(client, device_headers):
    """TEL-007: real ingest persists canonical hash-verified batch blob, counts flags, ordered timestamps, exact sample readback."""
    device, sensors = register_device_with_sensors(client, (
        ('pack-voltage', 'voltage', 'V', {'minimum': 30.0, 'maximum': 60.0}),
        ('motor-temp', 'temperature', '°C', None)))
    body = {'session': 'bench-run-1', 'conditions': 'Owner-recorded indoor bench run',
            'samples': [sample(sensors[0]['id'], value=48.2, timestamp='2026-01-02T03:04:06+00:00'),
                        sample(sensors[0]['id'], value=99.9, timestamp='2026-01-02T03:04:05+00:00'),
                        sample(sensors[0]['id'], value=48.0, timestamp='2026-01-02T03:04:04+00:00', quality='suspect'),
                        sample(sensors[1]['id'], value=41.5, timestamp='2026-01-02T03:04:07+00:00')]}
    batch = client.post('/api/telemetry/ingest', headers=device_headers, json=body)
    assert batch.status_code == 201, batch.text
    value = batch.json()
    assert value['device_id'] == device['id']
    assert value['sample_count'] == 4
    assert value['sensor_ids'] == sorted(s['id'] for s in sensors)
    assert value['flagged_out_of_range'] == 1
    assert value['suspect_samples'] == 1
    assert value['first_timestamp'] == '2026-01-02T03:04:04+00:00'
    assert value['last_timestamp'] == '2026-01-02T03:04:07+00:00'
    assert len(value['sha256']) == 64 and value['size_bytes'] > 0
    read = client.get(f"/api/telemetry/batches/{value['id']}/samples").json()
    assert read['batch'] == value
    assert sorted(read['samples'], key=lambda s: s['timestamp']) == sorted(body['samples'], key=lambda s: s['timestamp'])
    assert client.get(f"/api/telemetry/batches/{value['id']}/samples").status_code == 200
    assert client.get('/api/telemetry/batches').json() == [value]
    assert client.get(f"/api/telemetry/batches?device_id={device['id']}").json() == [value]


def test_ingest_input_validation(client, device_headers):
    """TEL-008: ingest rejects empty/oversized/unknown-sensor/non-finite/naive-or-invalid-timestamp/cross-device batches 404/422."""
    other, _ = register_device_with_sensors(client, (('other-voltage', 'voltage', 'V', None),), name='Second bench unit')
    device, sensors = register_device_with_sensors(client, (('pack-voltage', 'voltage', 'V', None),))
    ingest = lambda payload: client.post('/api/telemetry/ingest', headers=device_headers, json=payload)
    assert ingest({'samples': []}).status_code == 422
    assert ingest({'samples': [sample(sensors[0]['id'])] * 1001}).status_code == 422
    assert ingest({'samples': [sample('missing-sensor')]}).status_code == 404
    nan_body = json.dumps({'samples': [sample(sensors[0]['id'])]}).replace('48.1', 'NaN')
    assert client.post('/api/telemetry/ingest', headers={**device_headers, 'Content-Type': 'application/json'},
                       content=nan_body).status_code == 422
    assert ingest({'samples': [sample(sensors[0]['id'], timestamp='2026-01-02T03:04:05')]}).status_code == 422
    assert ingest({'samples': [sample(sensors[0]['id'], timestamp='02.01.2026 03:04')]}).status_code == 422
    assert ingest({'samples': [sample(sensors[0]['id'], quality='broken')]}).status_code == 422
    assert ingest({'samples': [sample(sensors[0]['id'])], 'extra': 1}).status_code == 422
    with_other = client.post(f"/api/telemetry/devices/{other['id']}/sensors", json=sensor_body('other-current', 'current', 'A')).json()
    assert ingest({'samples': [sample(sensors[0]['id']), sample(with_other['id'])]}).status_code == 422


def test_device_deactivation_requires_reviewer_confirmation_and_retains_data(client, device_headers, reviewer):
    """TEL-009: device deactivation needs reviewer confirm+reason, 409 on repeat, blocks ingest/sensors, retains registry."""
    device, sensors = register_device_with_sensors(client)
    assert client.post(f"/api/telemetry/devices/{device['id']}/deactivate", headers=reviewer,
                       json={'confirm': False, 'reason': 'x' * 20}).status_code == 422
    assert client.post(f"/api/telemetry/devices/{device['id']}/deactivate", headers=reviewer,
                       json={'confirm': True, 'reason': ''}).status_code == 422
    assert client.post(f"/api/telemetry/devices/{device['id']}/deactivate",
                       json={'confirm': True, 'reason': 'Fixture retirement without deletion'}).status_code == 403
    deactivated = client.post(f"/api/telemetry/devices/{device['id']}/deactivate", headers=reviewer,
                              json={'confirm': True, 'reason': 'Fixture retirement without deletion'})
    assert deactivated.status_code == 200
    assert deactivated.json()['state'] == 'deactivated'
    assert deactivated.json()['deactivated_at']
    assert client.post(f"/api/telemetry/devices/{device['id']}/deactivate", headers=reviewer,
                       json={'confirm': True, 'reason': 'Second attempt'}).status_code == 409
    assert client.post('/api/telemetry/ingest', headers=device_headers,
                       json={'samples': [sample(sensors[0]['id'])]}).status_code == 409
    assert client.post(f"/api/telemetry/devices/{device['id']}/sensors",
                       json=sensor_body('post-retirement', 'voltage', 'V')).status_code == 409
    assert len(client.get('/api/telemetry/devices').json()) == 1


def test_sensor_deactivation_blocks_only_that_sensor(client, device_headers, reviewer):
    """TEL-010: sensor deactivation blocks only that sensor for ingest, device and other sensors keep working."""
    device, sensors = register_device_with_sensors(client, (
        ('pack-voltage', 'voltage', 'V', None), ('motor-rpm', 'rpm', 'rpm', None)))
    deactivated = client.post(f"/api/telemetry/sensors/{sensors[0]['id']}/deactivate", headers=reviewer,
                              json={'confirm': True, 'reason': 'Fixture sensor retirement'})
    assert deactivated.status_code == 200
    assert client.post('/api/telemetry/ingest', headers=device_headers,
                       json={'samples': [sample(sensors[0]['id'])]}).status_code == 409
    assert client.post('/api/telemetry/ingest', headers=device_headers,
                       json={'samples': [sample(sensors[1]['id'])]}).status_code == 201
    assert client.post(f"/api/telemetry/sensors/{sensors[0]['id']}/deactivate", headers=reviewer,
                       json={'confirm': True, 'reason': 'Second attempt'}).status_code == 409
    assert len(client.get(f"/api/telemetry/devices/{device['id']}/sensors").json()) == 2


def test_emergency_stop_blocks_telemetry_mutations(client, device_headers, reviewer):
    """TEL-011: emergency stop blocks device/sensor/ingest mutations 409, reads stay available, clearing stop restores ingest."""
    device, sensors = register_device_with_sensors(client)
    stop = client.post('/api/control/stop', headers=reviewer, json={'active': True, 'reason': 'Fixture emergency stop'})
    assert stop.status_code == 200
    assert client.post('/api/telemetry/devices', json=device_body('second')).status_code == 409
    assert client.post(f"/api/telemetry/devices/{device['id']}/sensors",
                       json=sensor_body('extra', 'voltage', 'V')).status_code == 409
    assert client.post('/api/telemetry/ingest', headers=device_headers,
                       json={'samples': [sample(sensors[0]['id'])]}).status_code == 409
    reads = client.get('/api/telemetry/devices')
    assert reads.status_code == 200
    assert client.post('/api/control/stop', headers=reviewer, json={'active': False, 'reason': 'Fixture stop cleared'}).status_code == 200
    assert client.post('/api/telemetry/ingest', headers=device_headers,
                       json={'samples': [sample(sensors[0]['id'])]}).status_code == 201


def test_batches_filter_rejects_unknown_device(client):
    """TEL-011b: batch listing filters by existing device and rejects unknown device filter 404."""
    assert client.get('/api/telemetry/batches?device_id=unknown').status_code == 404
    assert client.get('/api/telemetry/batches').json() == []


def test_corrupt_blob_fails_closed_on_read(client, device_headers, tmp_path):
    """TEL-012: corrupted batch blob fails closed 503 on sample read while metadata and hash remain inspectable."""
    device, sensors = register_device_with_sensors(client)
    batch = client.post('/api/telemetry/ingest', headers=device_headers,
                        json={'samples': [sample(sensors[0]['id'])]}).json()
    blob_path = tmp_path / 'objects' / (batch['key'] + '.blob')
    assert blob_path.exists()
    blob_path.write_bytes(b'corrupted payload bytes')
    response = client.get(f"/api/telemetry/batches/{batch['id']}/samples")
    assert response.status_code == 503
    metadata = client.get('/api/telemetry/batches').json()
    assert metadata[0]['sha256'] == batch['sha256']


def test_audit_records_telemetry_actions(client, device_headers, reviewer):
    """TEL-013: audit trail covers registration, declaration, ingest (device actor) and confirmed deactivation (reviewer actor)."""
    device, sensors = register_device_with_sensors(client)
    client.post('/api/telemetry/ingest', headers=device_headers, json={'samples': [sample(sensors[0]['id'])]})
    client.post(f"/api/telemetry/devices/{device['id']}/deactivate", headers=reviewer,
                json={'confirm': True, 'reason': 'Fixture audit trail check'})
    entries = [e for e in client.get('/api/audit', headers=reviewer).json() if e['event'].startswith('telemetry.')]
    assert [e['event'] for e in entries] == ['telemetry.device_registered', 'telemetry.sensor_declared',
                                             'telemetry.ingested', 'telemetry.device_deactivated']
    assert entries[2]['actor'] == 'telemetry-device'
    assert entries[3]['actor'] == 'reviewer'
