"""Real PLAN reference/version/lock endpoints. No file upload or device simulation."""
from fastapi import Depends, Query
from app.store import get, listing
from app.plan_models import PlanCreate, PlanRevise, PlanLockInput, PlanRevoke, Plan, PlanVersion, PlanLock, PlanStatus
from app.plan_service import create_plan, revise_plan, create_lock, revoke_lock, status


def register_plan_api(app, storage, actor, operator, reviewer, connection):
    DB = Depends(connection, scope='function')
    def contract(role, effects):
        return {'x-role':role,'x-side-effects':effects}

    @app.post('/api/plans', response_model=Plan, status_code=201, tags=['plan'], openapi_extra=contract('operator','Create one task-bound PLAN + first immutable version + source hash checks + audit; no permissions/truth'))
    def create(body: PlanCreate, who=Depends(operator), db=DB):
        return create_plan(db, body, who, storage)

    @app.get('/api/plans', response_model=list[Plan], tags=['plan'], openapi_extra=contract('both','Read-only PLAN identities; no fake resources'))
    def plans(limit: int=Query(100,ge=1,le=100), offset: int=Query(0,ge=0), who=Depends(actor), db=DB):
        return listing(db,'plan',limit,offset)

    @app.get('/api/plans/{plan_id}/versions', response_model=list[PlanVersion], tags=['plan'], openapi_extra=contract('both','Read immutable stored manifests, not current validation; newest first'))
    def versions(plan_id: str, limit: int=Query(100,ge=1,le=100), offset: int=Query(0,ge=0), who=Depends(actor), db=DB):
        import json
        get(db,'plan',plan_id)
        return [json.loads(row[0]) for row in db.execute("SELECT body FROM records WHERE kind='plan_version' AND json_extract(body,'$.plan_id')=? ORDER BY seq DESC LIMIT ? OFFSET ?",(plan_id,limit,offset))]

    @app.post('/api/plans/{plan_id}/versions', response_model=PlanVersion, status_code=201, tags=['plan'], openapi_extra=contract('operator','Append immutable version with optimistic expected_version_id; invalidate old lock/challenge/approvals; stop blocks'))
    def revise(plan_id: str, body: PlanRevise, who=Depends(operator), db=DB):
        return revise_plan(db,plan_id,body,who,storage)

    @app.post('/api/plans/{plan_id}/locks', response_model=PlanLock, status_code=201, tags=['plan'], openapi_extra=contract('reviewer','Lock current exact manifest after fresh source checks; latest lock supersedes prior consent; no action authority; stop blocks'))
    def lock(plan_id: str, body: PlanLockInput, who=Depends(reviewer), db=DB):
        return create_lock(db,plan_id,body,who,storage)

    @app.post('/api/plan-locks/{lock_id}/revoke', tags=['plan'], openapi_extra=contract('reviewer','Append revocation and audit; immediately blocks new PLAN-bound uses; allowed during stop, cannot recall in-flight data'))
    def revoke(lock_id: str, body: PlanRevoke, who=Depends(reviewer), db=DB) -> dict:
        return revoke_lock(db,lock_id,body,who)

    @app.get('/api/plans/{plan_id}/status', response_model=PlanStatus, tags=['plan'], openapi_extra=contract('both','Live source/file integrity and revision/lock/stop checks; CURRENT means context binding only, never truth/permission'))
    def current(plan_id: str, who=Depends(actor), db=DB):
        return status(db,get(db,'plan',plan_id),storage)
