"""Monitoring overview and integration registry: read-only aggregation of real state, no invention."""
import json
from fastapi import Depends
from app.store import stopped


def register_monitoring_api(app, settings, actor, operator, reviewer, connection, store, storage, gateway):
    DB = Depends(connection, scope='function')

    def count(db, kind, field=None, value=None):
        if field is None:
            return db.execute('SELECT COUNT(*) FROM records WHERE kind=?', (kind,)).fetchone()[0]
        return db.execute("SELECT COUNT(*) FROM records WHERE kind=? AND json_extract(body,'$.\"' || ? || '\"')=?",
                          (kind, field, value)).fetchone()[0]

    def total(db, kind, field):
        return db.execute("SELECT COALESCE(SUM(json_extract(body,'$.\"' || ? || '\"')),0) FROM records WHERE kind=?",
                          (field, kind)).fetchone()[0]

    def bodies(db, kind):
        return [json.loads(row[0]) for row in
                db.execute('SELECT body FROM records WHERE kind=? ORDER BY seq', (kind,)).fetchall()]

    def state_counts(db, kind, states):
        return {state: count(db, kind, 'state', state) for state in states}

    @app.get('/api/monitoring/overview', tags=['monitoring'],
             openapi_extra={'x-role': 'both', 'x-side-effects': 'None; read-only aggregation of stored records; configured is never validated; no device/provider health or truth claims'})
    def overview(who=Depends(actor), db=DB) -> dict:
        brightdata = bool(settings.brightdata_oauth_token) if settings else False
        telemetry = bool(settings.telemetry_token) if settings else False
        return {
            'stop_active': stopped(db)['active'],
            'counts': {
                'projects': count(db, 'project'), 'tasks': count(db, 'task'),
                'evidence': count(db, 'evidence'), 'results': count(db, 'result'),
                'telemetry_devices': state_counts(db, 'telemetry_device', ['active', 'deactivated']),
                'telemetry_sensors': state_counts(db, 'telemetry_sensor', ['active', 'deactivated']),
                'telemetry_batches': count(db, 'telemetry_batch'),
                'telemetry_samples': total(db, 'telemetry_batch', 'sample_count'),
                'telemetry_flagged_out_of_range': total(db, 'telemetry_batch', 'flagged_out_of_range'),
                'telemetry_suspect_samples': total(db, 'telemetry_batch', 'suspect_samples'),
                'resources': state_counts(db, 'resource', ['active', 'deactivated']),
                'resource_versions_stored_bytes': total(db, 'resource', 'size_bytes'),
                'agents': state_counts(db, 'agent', ['active', 'deactivated']),
                'agent_runs': {'awaiting_consent': count(db, 'agent_run', 'state', 'AWAITING_CONSENT'),
                               'draft_unchallenged': count(db, 'agent_run', 'state', 'DRAFT_UNCHALLENGED'),
                               'blocked': count(db, 'agent_run', 'state', 'BLOCKED'),
                               'unavailable': count(db, 'agent_run', 'state', 'UNAVAILABLE')},
            },
            'integrations': {
                'ai_providers': [{'id': p.id, 'mode': p.mode, 'region': p.region,
                                  'status': 'CONFIGURED_NOT_VALIDATED'} for p in gateway.providers.values()],
                'brightdata_mcp': {'configured': brightdata, 'scope': 'DISCOVERY_AND_BOUNDED_TOOLS_CALL',
                                   'validation': 'NOT_LIVE_VALIDATED'},
                'telemetry_ingest': {'configured': telemetry, 'transport': 'HTTPS_ONLY',
                                     'note': 'WS/MQTT/Serial NOT IMPLEMENTED'},
            },
            'storage': storage.health(db),
            'disclaimer': 'Aggregated stored-record counts only; no device/provider health, availability or truth claims. Configured is not validated.',
        }

    @app.get('/api/integrations', tags=['integrations'],
             openapi_extra={'x-role': 'both', 'x-side-effects': 'None; read-only registry of runtime-manageable bindings with their real management routes and roles; environment-bound integrations are displayed, not runtime-manageable'})
    def integrations(who=Depends(actor), db=DB) -> dict:
        manageable = []
        sensors_by_device = {}
        for sensor in bodies(db, 'telemetry_sensor'):
            sensors_by_device.setdefault(sensor['device_id'], []).append(
                {'binding': 'telemetry_sensor', 'id': sensor['id'], 'name': sensor['name'], 'kind': sensor['kind'],
                 'state': sensor['state'],
                 'actions': ({'remove': {'route': f"POST /api/telemetry/sensors/{sensor['id']}/deactivate",
                                         'role': 'reviewer', 'requires': 'confirm+reason', 'data': 'retained'}}
                             if sensor['state'] == 'active' else {})})
        for device in bodies(db, 'telemetry_device'):
            manageable.append({'binding': 'telemetry_device', 'id': device['id'], 'name': device['name'],
                               'state': device['state'], 'created_at': device['created_at'],
                               'actions': {'add': {'route': 'POST /api/telemetry/devices', 'role': 'operator'},
                                           **({'remove': {'route': f"POST /api/telemetry/devices/{device['id']}/deactivate",
                                                          'role': 'reviewer', 'requires': 'confirm+reason', 'data': 'retained'}}
                                              if device['state'] == 'active' else {})},
                               'sensors': sensors_by_device.get(device['id'], [])})
        for agent in bodies(db, 'agent'):
            manageable.append({'binding': 'agent', 'id': agent['id'], 'name': agent['name'],
                               'purpose': agent['purpose'], 'model_id': agent['model_id'],
                               'state': agent['state'], 'created_at': agent['created_at'],
                               'actions': {'add': {'route': 'POST /api/agents', 'role': 'operator'},
                                           **({'remove': {'route': f"POST /api/agents/{agent['id']}/deactivate",
                                                          'role': 'reviewer', 'requires': 'confirm+reason', 'data': 'retained'}}
                                              if agent['state'] == 'active' else {})}})
        for resource in bodies(db, 'resource'):
            manageable.append({'binding': 'resource', 'id': resource['id'], 'name': resource['name'],
                               'kind': resource['kind'], 'state': resource['state'], 'version': resource['version'],
                               'created_at': resource['created_at'],
                               'actions': {'add': {'route': 'POST /api/resources', 'role': 'operator'},
                                           **({'remove': {'route': f"POST /api/resources/{resource['id']}/deactivate",
                                                          'role': 'reviewer', 'requires': 'confirm+reason', 'data': 'retained'}}
                                              if resource['state'] == 'active' else {})}})
        environment_bound = [
            {'binding': 'ai_provider', 'id': p.id, 'state': 'CONFIGURED_NOT_VALIDATED',
             'management': 'ATZE_AI_CONFIG server environment; runtime add/remove NOT IMPLEMENTED'}
            for p in gateway.providers.values()]
        environment_bound.append(
            {'binding': 'brightdata_mcp',
             'state': 'CONFIGURED' if (settings.brightdata_oauth_token if settings else '') else 'NOT_CONFIGURED',
             'management': 'ATZE_BRIGHTDATA_OAUTH_TOKEN server environment; runtime add/remove NOT IMPLEMENTED'})
        environment_bound.append(
            {'binding': 'telemetry_device_fleet',
             'state': 'CONFIGURED' if (settings.telemetry_token if settings else '') else 'NOT_CONFIGURED',
             'management': 'ATZE_TELEMETRY_TOKEN server environment; runtime add/remove NOT IMPLEMENTED'})
        return {'manageable': manageable, 'environment_bound': environment_bound,
                'removal_semantics': 'Reviewer-confirmed deactivation only; all data and history are retained; no deletion endpoint exists',
                'action_note': 'Every listed route is a real implemented endpoint; unlisted actions do not exist'}
