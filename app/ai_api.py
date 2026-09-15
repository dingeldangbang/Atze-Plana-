"""Explicit API controls; no autonomous agent or hidden provider selection."""
from fastapi import Depends, Query
from fastapi.responses import JSONResponse
from app.ai_models import AIPolicy, ModelRegistration, AIRequest, AIConsent
from app.ai_gateway import ExternalDataGateway, GateDenied
from app.ai_service import policy, prepare, execute
from app.store import put, get, listing, audit, identity, now


def register_ai_api(app, settings, actor, operator, reviewer, connection, store, storage=None):
    gateway = ExternalDataGateway(settings.ai_config_path if settings else None,
                                  (settings.operator_token, settings.reviewer_token, settings.challenge_token, settings.brightdata_oauth_token) if settings else ())
    DB = Depends(connection, scope='function')

    def contract(role, effects):
        return {'x-role': role, 'x-side-effects': effects}

    @app.get('/api/ai/status', tags=['ai'], openapi_extra=contract('both', 'Read-only configuration, never live model validation'))
    def status(who=Depends(actor), db=DB) -> dict:
        return {'policy': policy(db), 'providers': [{'id': p.id, 'mode': p.mode, 'region': p.region,
                 'status': 'CONFIGURED_NOT_VALIDATED'} for p in gateway.providers.values()],
                'model_inference': 'NOT_VALIDATED', 'mcp': 'DISCOVERY_AND_BOUNDED_TOOLS_CALL', 'tool_execution': 'REVIEWER_GATED_ALLOWLIST_ONLY',
                'model_discovery': 'NOT_IMPLEMENTED', 'agent_runtime': 'REGISTRY_AND_BOUNDED_SINGLE_RUNS', 'production_ready': False}

    @app.post('/api/ai/policy', tags=['ai'], status_code=201, openapi_extra=contract('reviewer', 'Append policy and audit; invalidates pending requests; no network'))
    def set_policy(body: AIPolicy, who=Depends(reviewer), db=DB) -> dict:
        value = put(db, 'ai_policy', dict(**body.model_dump(), id=identity(), created_at=now()))
        audit(db, who, 'ai.policy_changed', value['id'])
        return value

    @app.post('/api/ai/models', tags=['ai'], status_code=201, openapi_extra=contract('reviewer', 'Immutable reviewed manual metadata; no download/discovery/live revision or license validation'))
    def register_model(body: ModelRegistration, who=Depends(reviewer), db=DB) -> dict:
        gateway.scan(body.model_dump_json())
        gateway.provider(body.provider_id)
        value = put(db, 'ai_model', dict(**body.model_dump(), id=identity(), created_at=now(), approval_state='MANUALLY_REVIEWED', validation='NOT_LIVE_VALIDATED'))
        audit(db, who, 'ai.model_registered', value['id'])
        return value

    @app.get('/api/ai/models', tags=['ai'], openapi_extra=contract('both', 'Read-only manual model registry'))
    def models(limit: int = Query(100, ge=1, le=100), offset: int = Query(0, ge=0), who=Depends(actor), db=DB) -> list[dict]:
        return listing(db, 'ai_model', limit, offset)

    @app.post('/api/ai/requests', tags=['ai'], status_code=201, openapi_extra=contract('operator', 'Prepare bounded same-project/task context; scan and classify; persist local context for reviewer; NO network'))
    def request(body: AIRequest, who=Depends(operator), db=DB) -> dict:
        try:
            return prepare(db, body, who, gateway, storage)
        except GateDenied as error:
            audit(db, who, 'ai.prepare_denied', identity(), {'reason': str(error)})
            return JSONResponse(status_code=409, content={'detail': str(error), 'state': 'BLOCKED'})

    @app.get('/api/ai/requests/{request_id}', tags=['ai'], openapi_extra=contract('both', 'Read exact prepared context for explicit review, not a model answer'))
    def detail(request_id: str, who=Depends(actor), db=DB) -> dict:
        return get(db, 'ai_request', request_id)

    @app.post('/api/ai/requests/{request_id}/run', tags=['ai'], openapi_extra=contract('reviewer', 'Exact context hash + explicit remote consent; recheck policy/stop; authenticated bounded transport through gateway; durable audit; output unchallenged and not stored; NO tools/adoption/fallback'))
    def run(request_id: str, body: AIConsent, who=Depends(reviewer)) -> dict:
        return execute(store, request_id, body, gateway, who, storage)

    @app.get('/api/ai/attempts/{attempt_id}', tags=['ai'], openapi_extra=contract('both', 'Read audit metadata only; pending outcome is unknown, never automatic retry'))
    def attempt(attempt_id: str, who=Depends(actor), db=DB) -> dict:
        return get(db, 'ai_attempt', attempt_id)

    @app.exception_handler(GateDenied)
    async def denied(request, error):
        return JSONResponse(status_code=409, content={'detail': str(error), 'state': 'BLOCKED'})

    return gateway
