"""Application factory: importing schemas does not require production secrets."""
import hashlib
import secrets
import sqlite3
from pathlib import Path
from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from app.config import Settings
from app.storage import Storage
from app.context_api import register_context_api
from app.models import (ProjectInput, Project, EvidenceInput, Evidence, Review,
                        TaskInput, Task, Decision, ApprovalInput, Approval, StopInput, Stop, Audit)
from app.store import Store, get, put, listing, audit, stopped, identity, now
from app.challenge_api import register_challenge_api
from app.challenge_service import decide_task

STATIC = Path(__file__).parent / 'static'


def create_app(settings: Settings | None = None, *, schema_only=False):
    if not schema_only:
        settings = settings or Settings.from_env()
    store = None if schema_only else Store(settings.db_path, settings.mode)
    storage = None if schema_only else Storage(settings)
    app = FastAPI(title='Atze Plana Evidence Core', version='0.3.0',
                  description='Single-workspace evidence and approval registry. No action execution.',
                  docs_url=None, redoc_url=None, openapi_url=None)
    bearer = HTTPBearer(auto_error=False)

    def actor(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
        token = credentials.credentials if credentials else ''
        if settings and secrets.compare_digest(token.encode(), settings.operator_token.encode()):
            return 'operator'
        if settings and secrets.compare_digest(token.encode(), settings.reviewer_token.encode()):
            return 'reviewer'
        raise HTTPException(401, 'Valid bearer token required', headers={'WWW-Authenticate': 'Bearer'})

    def operator(who=Depends(actor)):
        if who != 'operator':
            raise HTTPException(403, 'Operator role required')
        return who

    def reviewer(who=Depends(actor)):
        if who != 'reviewer':
            raise HTTPException(403, 'Reviewer role required')
        return who

    def connection():
        with store.connect() as db:
            yield db

    DB = Depends(connection, scope='function')

    @app.middleware('http')
    async def security_headers(request, call_next):
        response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'"
        return response

    @app.exception_handler(sqlite3.OperationalError)
    async def database_error(request, error):
        return JSONResponse(status_code=503, content={'detail': 'Storage unavailable; retry or contact administrator'})

    @app.exception_handler(OSError)
    async def filesystem_error(request, error):
        return JSONResponse(status_code=503, content={'detail': 'Storage unavailable; check configured tier and permissions'})

    @app.get('/health', tags=['system'])
    def health(db=DB) -> dict[str, str]:
        db.execute('SELECT 1')
        return {'status': 'ok', 'version': '0.3.0', 'mode': settings.mode}

    @app.get('/api/runtime', tags=['system'])
    def runtime(who=Depends(actor)) -> dict[str, str]:
        return {'mode': settings.mode, 'data_scope': 'TEST INPUTS — NOT LIVE EVIDENCE' if settings.mode == 'test' else 'OPERATIONAL — NO SEEDED DATA', 'production_readiness': 'NOT VALIDATED', 'challenge_worker': 'CONFIGURED — liveness not asserted' if settings.challenge_token else 'NOT CONFIGURED — decisions blocked'}

    @app.get('/api/openapi.json', tags=['system'])
    def specification(who=Depends(actor)) -> dict:
        return app.openapi()

    @app.post('/api/projects', response_model=Project, status_code=201, tags=['projects'])
    def create_project(body: ProjectInput, who=Depends(operator), db=DB):
        value = put(db, 'project', dict(**body.model_dump(mode='json'), id=identity(), created_at=now()))
        audit(db, who, 'project.created', value['id'])
        return value

    @app.get('/api/projects', response_model=list[Project], tags=['projects'])
    def projects(limit: int = Query(100, ge=1, le=100), offset: int = Query(0, ge=0), who=Depends(actor), db=DB):
        return listing(db, 'project', limit, offset)

    @app.post('/api/evidence', response_model=Evidence, status_code=201, tags=['evidence'])
    def create_evidence(body: EvidenceInput, who=Depends(operator), db=DB):
        get(db, 'project', body.project_id)
        value = dict(**body.model_dump(mode='json'), id=identity(), created_at=now(),
                     sha256=hashlib.sha256(body.content.encode()).hexdigest(), state='unverified', review_reason=None)
        put(db, 'evidence', value)
        audit(db, who, 'evidence.created', value['id'], {'sha256': value['sha256']})
        return value

    @app.get('/api/evidence', response_model=list[Evidence], tags=['evidence'])
    def evidence(limit: int = Query(100, ge=1, le=100), offset: int = Query(0, ge=0), who=Depends(actor), db=DB):
        return listing(db, 'evidence', limit, offset)

    @app.get('/api/evidence/{evidence_id}', response_model=Evidence, tags=['evidence'])
    def evidence_source(evidence_id: str, who=Depends(actor), db=DB):
        return get(db, 'evidence', evidence_id)

    @app.post('/api/evidence/{evidence_id}/review', response_model=Evidence, tags=['evidence'])
    def review(evidence_id: str, body: Review, who=Depends(reviewer), db=DB):
        import json
        value = get(db, 'evidence', evidence_id)
        if value['state'] != 'unverified':
            raise HTTPException(409, 'Review is immutable; create new evidence for corrections')
        value.update(state=body.state, review_reason=body.reason)
        db.execute('UPDATE records SET body=? WHERE id=?', (json.dumps(value), evidence_id))
        audit(db, who, 'evidence.reviewed', evidence_id, body.model_dump())
        return value

    @app.post('/api/tasks', response_model=Task, status_code=201, tags=['tasks'])
    def create_task(body: TaskInput, who=Depends(operator), db=DB):
        get(db, 'project', body.project_id)
        if len(body.evidence_ids) != len(set(body.evidence_ids)):
            raise HTTPException(422, 'Duplicate evidence reference')
        for key in body.evidence_ids:
            if get(db, 'evidence', key)['project_id'] != body.project_id:
                raise HTTPException(422, 'Evidence belongs to another project')
        value = put(db, 'task', dict(**body.model_dump(mode='json'), id=identity(), created_at=now(), created_by=who))
        audit(db, who, 'task.created', value['id'])
        return value

    @app.get('/api/tasks', response_model=list[Task], tags=['tasks'])
    def tasks(limit: int = Query(100, ge=1, le=100), offset: int = Query(0, ge=0), who=Depends(actor), db=DB):
        return listing(db, 'task', limit, offset)

    @app.post('/api/tasks/{task_id}/triage', response_model=Decision, tags=['tasks'])
    def triage(task_id: str, who=Depends(actor), db=DB):
        decision = decide_task(db, task_id)
        audit(db, who, 'task.triaged', task_id, decision.model_dump())
        return decision

    @app.post('/api/tasks/{task_id}/approve', response_model=Approval, status_code=201, tags=['tasks'])
    def approve(task_id: str, body: ApprovalInput, who=Depends(reviewer), db=DB):
        decision = decide_task(db, task_id)
        if decision.state != 'approval_required':
            raise HTTPException(409, 'Task is not awaiting approval; run triage')
        value = put(db, 'approval', dict(id=identity(), task_id=task_id, created_at=now(), actor=who, reason=body.reason, result_id=decision.result_id, challenge_id=decision.challenge_id, fingerprint=decision.fingerprint))
        audit(db, who, 'task.approved', task_id, value)
        return value

    @app.get('/api/control/stop', response_model=Stop, tags=['control'])
    def stop_state(who=Depends(actor), db=DB):
        return stopped(db)

    @app.post('/api/control/stop', response_model=Stop, tags=['control'])
    def set_stop(body: StopInput, who=Depends(reviewer), db=DB):
        db.execute('UPDATE control SET active=?,reason=? WHERE id=1', (body.active, body.reason))
        audit(db, who, 'control.stop_changed', 'global', body.model_dump())
        return body

    @app.get('/api/audit', response_model=list[Audit], tags=['audit'])
    def audit_log(limit: int = Query(100, ge=1, le=100), offset: int = Query(0, ge=0), who=Depends(reviewer), db=DB):
        return listing(db, 'audit', limit, offset)

    register_challenge_api(app, settings, actor, operator, reviewer, connection)
    register_context_api(app, store, storage, actor, operator, reviewer, connection)

    @app.get('/', include_in_schema=False)
    def index():
        return FileResponse(STATIC / 'index.html')

    app.mount('/static', StaticFiles(directory=STATIC), name='static')
    # Shared operational errors are included in the generated contract.
    for route in app.routes:
        if getattr(route, 'path', '').startswith('/api/'):
            route.responses.update({code: {'description': description} for code, description in {
                401: 'Missing or invalid token', 403: 'Role denied', 404: 'Entity not found',
                409: 'State conflict', 410: 'Disposable cache expired', 507: 'Insufficient eligible storage capacity', 422: 'Invalid input', 503: 'Storage unavailable'}.items()})
    return app
