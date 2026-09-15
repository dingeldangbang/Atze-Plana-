"""Permission lease contract tests: bounded grants, expiry, exhaustion, revocation, MCP enforcement."""
from dataclasses import replace
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from test_mcp import peer, setup  # real isolated TLS peer + MCP fixture setup, not live Bright Data


def lease_body(task_id, **overrides):
    body = {'action': 'mcp.tools_call', 'scope_kind': 'task', 'scope_id': task_id, 'tool': None,
            'expires_at': (datetime.now(tz=timezone_utc()) + timedelta(hours=1)).isoformat(),
            'max_uses': 1, 'reason': 'Explicit bounded lease grant for isolated tests'}
    body.update(overrides)
    return body


def timezone_utc():
    from datetime import timezone
    return timezone.utc


def grant(client, reviewer, task_id, **overrides):
    response = client.post('/api/leases', headers=reviewer, json=lease_body(task_id, **overrides))
    assert response.status_code == 201, response.text
    return response.json()


def call_body(body, tool='search_engine', **overrides):
    request = {'task_id': body['task_id'], 'tool': tool, 'arguments': {'query': 'synthetic lease test'},
               'allow_external_call': True, 'reason': 'Explicit isolated tool call'}
    request.update(overrides)
    return request


def test_lease_creation_validation_and_roles(client, reviewer):
    """LEA-001: leases are reviewer-granted only; scope must exist; TTL/expiry/tool bounds enforced."""
    body, pol = setup(client, reviewer)
    assert client.post('/api/leases', json=lease_body(body['task_id'])).status_code == 403
    assert client.post('/api/leases', headers=reviewer, json=lease_body('missing-task')).status_code == 404
    past = lease_body(body['task_id'], expires_at=(datetime.now(tz=timezone_utc()) - timedelta(minutes=1)).isoformat())
    assert client.post('/api/leases', headers=reviewer, json=past).status_code == 422
    far = lease_body(body['task_id'], expires_at=(datetime.now(tz=timezone_utc()) + timedelta(hours=25)).isoformat())
    assert client.post('/api/leases', headers=reviewer, json=far).status_code == 422
    assert client.post('/api/leases', headers=reviewer, json=lease_body(body['task_id'], tool='terminal')).status_code == 422
    assert client.post('/api/leases', headers=reviewer, json=lease_body(body['task_id'], max_uses=0)).status_code == 422
    lease = grant(client, reviewer, body['task_id'])
    assert lease['state'] == 'active' and lease['effective_state'] == 'active'
    assert lease['uses_count'] == 0 and lease['uses_remaining'] == 1
    assert client.get('/api/leases', headers=reviewer).json()[0]['id'] == lease['id']
    assert client.get(f"/api/leases/{lease['id']}").json()['effective_state'] == 'active'


def test_lease_operator_requires_active_lease(client, reviewer):
    """LEA-002: operator tool calls without a lease stay 403 (default deny preserved)."""
    body, pol = setup(client, reviewer)
    assert client.post('/api/mcp/brightdata/call', json=call_body(body)).status_code == 403


def test_lease_reviewer_consent_path_unchanged(client, reviewer):
    """LEA-003: reviewer still needs the explicit per-call consent flag; a lease does not replace the reviewer consent."""
    body, pol = setup(client, reviewer)
    grant(client, reviewer, body['task_id'])
    denied = client.post('/api/mcp/brightdata/call', headers=reviewer,
                         json=call_body(body, allow_external_call=False)).json()
    assert denied['attempt']['state'] == 'BLOCKED' and denied['attempt']['reason'] == 'MCP_EXTERNAL_CALL_DENIED'


def test_lease_operator_executes_via_real_peer(settings, reviewer, peer):
    """LEA-004: operator with an active task-scoped lease completes a real TLS-peer tools/call; use consumed + audited."""
    settings = replace(settings, brightdata_oauth_token='synthetic-oauth-access')
    with TestClient(create_app(settings)) as c:
        c.headers['Authorization'] = 'Bearer ' + settings.operator_token
        body, pol = setup(c, reviewer)
        c.post('/api/ai/policy', headers=reviewer, json=pol)
        lease = grant(c, reviewer, body['task_id'])
        result = c.post('/api/mcp/brightdata/call', json=call_body(body)).json()
        assert result['attempt']['state'] == 'COMPLETED' and result['source'] == 'EXTERNAL_SOURCE'
        assert result['attempt']['result_excerpt'].startswith('synthetic external result for search_engine')
        stored = c.get(f"/api/leases/{lease['id']}").json()
        assert stored['uses_count'] == 1 and stored['effective_state'] == 'exhausted'
        assert stored['uses_remaining'] == 0
        events = [v['event'] for v in c.get('/api/audit', headers=reviewer).json() if v['event'].startswith('lease.')]
        assert events == ['lease.created', 'lease.used']
        # exhausted lease no longer authorizes the operator
        assert c.post('/api/mcp/brightdata/call', json=call_body(body)).status_code == 403


def test_lease_multi_use_and_project_scope(settings, reviewer, peer):
    """LEA-005: max_uses bounds the lease; project scope covers tasks of that project, not other projects."""
    settings = replace(settings, brightdata_oauth_token='synthetic-oauth-access')
    with TestClient(create_app(settings)) as c:
        c.headers['Authorization'] = 'Bearer ' + settings.operator_token
        body, pol = setup(c, reviewer)
        c.post('/api/ai/policy', headers=reviewer, json=pol)
        project_id = c.get('/api/projects').json()[0]['id']
        lease = grant(c, reviewer, body['task_id'], scope_kind='project', scope_id=project_id, max_uses=2)
        first = c.post('/api/mcp/brightdata/call', json=call_body(body)).json()
        second = c.post('/api/mcp/brightdata/call', json=call_body(body, tool='scrape_as_markdown',
                                                                   arguments={'url': 'https://example.org/lease'})).json()
        assert first['attempt']['state'] == 'COMPLETED' and second['attempt']['state'] == 'COMPLETED'
        assert c.get(f"/api/leases/{lease['id']}").json()['uses_count'] == 2
        assert c.post('/api/mcp/brightdata/call', json=call_body(body)).status_code == 403
        # a task of a different project is not covered by the project-scoped lease
        other, _ = setup(c, reviewer)
        assert c.post('/api/mcp/brightdata/call', json=call_body(other)).status_code == 403


def test_lease_tool_bound_and_expired(settings, reviewer, peer):
    """LEA-006: a tool-bound lease refuses the other allowlisted tool; expiry is computed, not stored silently."""
    settings = replace(settings, brightdata_oauth_token='synthetic-oauth-access')
    with TestClient(create_app(settings)) as c:
        c.headers['Authorization'] = 'Bearer ' + settings.operator_token
        body, pol = setup(c, reviewer)
        c.post('/api/ai/policy', headers=reviewer, json=pol)
        tool_bound = grant(c, reviewer, body['task_id'], tool='search_engine')
        assert c.post('/api/mcp/brightdata/call', json=call_body(body, tool='scrape_as_markdown')).status_code == 403
        assert c.post(f"/api/leases/{tool_bound['id']}/revoke", headers=reviewer,
                      json={'confirm': True, 'reason': 'Isolated test: free the scope for the aging check'}).status_code == 200
        lease = grant(c, reviewer, body['task_id'], max_uses=5)
        # white-box state aging against the real record store: stored state stays append-only
        from app.store import Store
        from app.context import update
        stored = c.get(f"/api/leases/{lease['id']}").json()
        aged = {key: value for key, value in stored.items() if key not in ('effective_state', 'uses_remaining')}
        aged['expires_at'] = (datetime.now(tz=timezone_utc()) - timedelta(seconds=1)).isoformat()
        with Store(settings.db_path, settings.mode).connect() as db:
            update(db, aged)
        aged_view = c.get(f"/api/leases/{lease['id']}").json()
        assert aged_view['effective_state'] == 'expired' and aged_view['state'] == 'active'  # stored record unchanged
        assert c.post('/api/mcp/brightdata/call', json=call_body(body)).status_code == 403


def test_lease_revocation_and_stop(settings, reviewer, peer):
    """LEA-007: confirmed revocation blocks the operator immediately; revoking stays allowed under emergency stop."""
    settings = replace(settings, brightdata_oauth_token='synthetic-oauth-access')
    with TestClient(create_app(settings)) as c:
        c.headers['Authorization'] = 'Bearer ' + settings.operator_token
        body, pol = setup(c, reviewer)
        c.post('/api/ai/policy', headers=reviewer, json=pol)
        lease = grant(c, reviewer, body['task_id'])
        assert c.post(f"/api/leases/{lease['id']}/revoke", json={'confirm': True, 'reason': 'unconfirmed actor'}).status_code == 403
        assert c.post(f"/api/leases/{lease['id']}/revoke", headers=reviewer,
                      json={'confirm': False, 'reason': 'unconfirmed'}).status_code == 422
        c.post('/api/control/stop', headers=reviewer, json={'active': True, 'reason': 'Isolated stop for revocation'})
        revoked = c.post(f"/api/leases/{lease['id']}/revoke", headers=reviewer,
                         json={'confirm': True, 'reason': 'Explicit early revocation decision'})
        assert revoked.status_code == 200 and revoked.json()['state'] == 'revoked'
        assert revoked.json()['effective_state'] == 'revoked'
        assert c.post(f"/api/leases/{lease['id']}/revoke", headers=reviewer,
                      json={'confirm': True, 'reason': 'again'}).status_code == 409
        # granting under stop is blocked
        assert c.post('/api/leases', headers=reviewer, json=lease_body(body['task_id'])).status_code == 409
        c.post('/api/control/stop', headers=reviewer, json={'active': False, 'reason': 'Isolated reset'})
        assert c.post('/api/mcp/brightdata/call', json=call_body(body)).status_code == 403


def test_lease_never_bypasses_technical_gates(settings, reviewer, peer):
    """LEA-008: an active lease does not bypass stop, privacy lock, allowlist or argument bounds."""
    settings = replace(settings, brightdata_oauth_token='synthetic-oauth-access')
    with TestClient(create_app(settings)) as c:
        c.headers['Authorization'] = 'Bearer ' + settings.operator_token
        body, pol = setup(c, reviewer)
        c.post('/api/ai/policy', headers=reviewer, json=pol)
        grant(c, reviewer, body['task_id'], max_uses=10)
        c.post('/api/control/stop', headers=reviewer, json={'active': True, 'reason': 'Isolated stop'})
        assert c.post('/api/mcp/brightdata/call', json=call_body(body)).json()['attempt']['reason'] == 'EMERGENCY_STOP'
        c.post('/api/control/stop', headers=reviewer, json={'active': False, 'reason': 'Isolated reset'})
        c.post('/api/ai/policy', headers=reviewer, json={**pol, 'privacy_lock': True})
        assert c.post('/api/mcp/brightdata/call', json=call_body(body)).json()['attempt']['reason'] == 'MCP_EXTERNAL_CALL_DENIED'
        c.post('/api/ai/policy', headers=reviewer, json=pol)
        assert c.post('/api/mcp/brightdata/call', json=call_body(body, tool='dangerous_unselected')).status_code == 422
        assert c.post('/api/mcp/brightdata/call', json=call_body(body, arguments={'query': 'x' * 5000})).status_code == 422


def test_lease_use_consumed_on_transport_failure(settings, reviewer, peer):
    """LEA-009: a use is consumed at reservation time; a transport failure does not refund the lease."""
    settings = replace(settings, brightdata_oauth_token='synthetic-oauth-access')
    peer[1]['case'] = 'rpc_error'
    with TestClient(create_app(settings)) as c:
        c.headers['Authorization'] = 'Bearer ' + settings.operator_token
        body, pol = setup(c, reviewer)
        c.post('/api/ai/policy', headers=reviewer, json=pol)
        lease = grant(c, reviewer, body['task_id'])
        result = c.post('/api/mcp/brightdata/call', json=call_body(body)).json()
        assert result['attempt']['state'] == 'BLOCKED' and result['attempt']['reason'] == 'MCP_INVALID_RPC_RESPONSE'
        assert c.get(f"/api/leases/{lease['id']}").json()['uses_count'] == 1
        assert c.post('/api/mcp/brightdata/call', json=call_body(body)).status_code == 403
