"""Reviewer-only, once-per-call metadata discovery; no external tool executor."""
from fastapi import Depends
from app.models import Input, Text
from app.store import get, put, audit, identity, now, stopped
from app.context import update
from app.ai_gateway import ExternalDataGateway, GateDenied, fingerprint
from app.ai_service import policy
from app.plan_service import task_gate


class Discover(Input):
    task_id: str
    allow_external_discovery: bool = False
    reason: Text
    plan_lock_id: str | None = None


def gate(db, body, storage):
    task = get(db, 'task', body.task_id)
    current = policy(db)
    if stopped(db)['active']:
        raise GateDenied('EMERGENCY_STOP')
    if not body.allow_external_discovery or current['privacy_lock'] or current['local_only'] or not current['allow_remote']:
        raise GateDenied('MCP_EXTERNAL_DISCOVERY_DENIED')
    if task['action'] != 'read' or not task['preconditions_met'] or task['project_id'] not in current['projects'] or 'PUBLIC' not in current['data_classes'] or 'brightdata-provider-managed' not in current['regions']:
        raise GateDenied('MCP_TASK_PROJECT_CLASS_REGION_DENIED')
    binding = task_gate(db, task['id'], storage)
    if (binding and (binding['state'] != 'CURRENT' or binding['lock_id'] != body.plan_lock_id)) or (not binding and body.plan_lock_id):
        raise GateDenied('MCP_PLAN_CONTEXT_NOT_CURRENT')
    return current['id']


def register_mcp_api(app, settings, actor, reviewer, connection, store, storage):
    gateway = ExternalDataGateway()
    token = settings.brightdata_oauth_token if settings else ''
    DB = Depends(connection, scope='function')

    @app.get('/api/mcp/brightdata/status', tags=['mcp'], openapi_extra={'x-role':'both', 'x-side-effects':'Read-only configuration; no network, OAuth or live validation'})
    def status(who=Depends(actor), db=DB) -> dict:
        return {'provider':'brightdata', 'configured':bool(token), 'authentication':'OAUTH_BEARER_ONLY',
                'validation':'NOT_LIVE_VALIDATED', 'scope':'DISCOVERY_ONLY', 'tool_execution':'NOT_IMPLEMENTED',
                'privacy_lock':policy(db)['privacy_lock'], 'allowed_for_action':False}

    @app.post('/api/mcp/brightdata/discover', tags=['mcp'], openapi_extra={'x-role':'reviewer', 'x-side-effects':'Explicit once-per-call external metadata consent; durable audit before HTTPS MCP handshake/list, no tool invocation; PUBLIC/project/region/Privacy/stop/PLAN gates; 200 envelope may be BLOCKED/UNAVAILABLE'})
    def discover(body: Discover, who=Depends(reviewer)) -> dict:
        result = None
        with store.connect() as db:
            item = dict(id=identity(), task_id=body.task_id, created_at=now(), state='STARTED', reason=None, reason_hash=fingerprint(body.reason))
            try:
                item['policy_id'] = gate(db, body, storage)
                if not token:
                    raise GateDenied('MCP_OAUTH_NOT_CONFIGURED_OR_INVALID')
            except GateDenied as error:
                item.update(state='BLOCKED', reason=str(error))
            put(db, 'mcp_discovery', item)
            audit(db, who, 'mcp.discovery_reserved', item['id'], {'state':item['state'], 'reason':item['reason']})
        if item['state'] != 'BLOCKED':
            with store.connect() as db:
                try:
                    if gate(db, body, storage) != item['policy_id']:
                        raise GateDenied('MCP_POLICY_CHANGED')
                    result = gateway.discover_brightdata(token)
                    item.update(state='DISCOVERED', catalog_sha256=result['catalog_sha256'])
                except GateDenied as error:
                    item.update(state='BLOCKED', reason=str(error))
                except Exception:
                    item.update(state='UNAVAILABLE', reason='MCP_TRANSPORT_OR_RESPONSE_FAILURE')
                update(db, item)
                audit(db, who, 'mcp.discovery_outcome', item['id'], {'state':item['state'], 'reason':item['reason']})
        return {'attempt':item, 'catalog':result, 'allowed_for_action':False}
