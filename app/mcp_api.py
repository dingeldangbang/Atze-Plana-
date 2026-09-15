"""Reviewer-only, once-per-call external MCP discovery and bounded allowlisted tools/call."""
import hashlib
import json
from fastapi import Depends, HTTPException
from app.models import Input, Text
from app.store import get, put, audit, identity, now, stopped
from app.context import update
from app.ai_gateway import ExternalDataGateway, GateDenied, fingerprint
from app.ai_service import policy
from app.plan_service import task_gate
from app.mcp_client import CANDIDATES, MAX_ARGUMENT_BYTES
from app.lease_service import consume_lease


class Discover(Input):
    task_id: str
    allow_external_discovery: bool = False
    reason: Text
    plan_lock_id: str | None = None


class Call(Input):
    task_id: str
    tool: str
    arguments: dict
    allow_external_call: bool = False
    reason: Text
    plan_lock_id: str | None = None


def gate(db, body, storage, consent=None, denied_reason='MCP_EXTERNAL_DISCOVERY_DENIED'):
    task = get(db, 'task', body.task_id)
    current = policy(db)
    if stopped(db)['active']:
        raise GateDenied('EMERGENCY_STOP')
    allowed = body.allow_external_discovery if consent is None else consent
    if allowed is not True or current['privacy_lock'] or current['local_only'] or not current['allow_remote']:
        raise GateDenied(denied_reason)
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
                'validation':'NOT_LIVE_VALIDATED', 'scope':'DISCOVERY_AND_BOUNDED_TOOLS_CALL',
                'tool_execution':'TOOLS_CALL_BOUNDED_ALLOWLIST', 'allowlisted_tools':sorted(CANDIDATES),
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

    @app.post('/api/mcp/brightdata/call', tags=['mcp'], openapi_extra={'x-role':'reviewer (per-call consent) or operator (active permission lease consumed per use)', 'x-side-effects':'Explicit external tool execution: reviewer once-per-call consent, or operator use of an active, unexhausted, unexpired lease (consumed at reservation; no refund on transport failure); the lease never bypasses technical gates (allowlist, argument/result bounds, PUBLIC/project/region/Privacy/stop/PLAN); durable audit before bounded tools/call over HTTPS; 200 envelope may be BLOCKED/UNAVAILABLE; results are EXTERNAL_SOURCE, never verified truth, never allowed for action'})
    def call(body: Call, who=Depends(actor)) -> dict:
        # Request-shape security bounds are rejected before any durable attempt or I/O.
        if body.tool not in CANDIDATES:
            raise HTTPException(422, 'Tool is not in the allowlisted candidate set')
        encoded_arguments = json.dumps(body.arguments)
        if len(encoded_arguments.encode()) > MAX_ARGUMENT_BYTES:
            raise HTTPException(422, f'Arguments exceed the {MAX_ARGUMENT_BYTES}-byte bound')
        if token and token in encoded_arguments:
            raise HTTPException(422, 'Arguments must not contain the provider credential')
        result = None
        with store.connect() as db:
            item = dict(id=identity(), task_id=body.task_id, tool=body.tool, created_at=now(), state='STARTED',
                        reason=None, reason_hash=fingerprint(body.reason),
                        arguments_sha256=hashlib.sha256(encoded_arguments.encode()).hexdigest())
            try:
                consent = body.allow_external_call
                if who == 'operator':
                    consume_lease(db, who, 'mcp.tools_call', body.task_id, body.tool)
                    consent = True
                item['policy_id'] = gate(db, body, storage, consent=consent,
                                         denied_reason='MCP_EXTERNAL_CALL_DENIED')
                if not token:
                    raise GateDenied('MCP_OAUTH_NOT_CONFIGURED_OR_INVALID')
            except GateDenied as error:
                item.update(state='BLOCKED', reason=str(error))
            put(db, 'mcp_call', item)
            audit(db, who, 'mcp.call_reserved', item['id'], {'state':item['state'], 'tool':body.tool, 'reason':item['reason']})
        if item['state'] != 'BLOCKED':
            with store.connect() as db:
                try:
                    if gate(db, body, storage, consent=consent,
                            denied_reason='MCP_EXTERNAL_CALL_DENIED') != item['policy_id']:
                        raise GateDenied('MCP_POLICY_CHANGED')
                    result = gateway.call_brightdata(token, body.tool, body.arguments)
                    item.update(state='COMPLETED', tool_is_error=result['is_error'],
                                result_excerpt=result['excerpt'], content_items=result['content_items'],
                                result_sha256=result['result_sha256'], result_size_bytes=result['result_size_bytes'])
                except GateDenied as error:
                    item.update(state='BLOCKED', reason=str(error))
                except Exception:
                    item.update(state='UNAVAILABLE', reason='MCP_TRANSPORT_OR_RESPONSE_FAILURE')
                update(db, item)
                audit(db, who, 'mcp.call_outcome', item['id'], {'state':item['state'], 'tool':body.tool,
                                                                 'reason':item['reason'],
                                                                 'tool_is_error':bool(item.get('tool_is_error'))})
        return {'attempt':item, 'result':result, 'source':'EXTERNAL_SOURCE', 'allowed_for_action':False}
