"""Permission-separated result/Challenge endpoints; no UI-fabricated report route."""
import secrets
from fastapi import Depends, HTTPException, Query
from fastapi.security import HTTPBearer
from app.store import get, listing
from app.challenge_models import ResultInput, Result, ChallengeRequest, JobStatus, WorkItem, Completion, ChallengeReport, Why
from app.context_models import Memory
from app.challenge_service import submit_result, current_result, make_job, latest, claim_job, complete_job, decide_task, adopt_result


def register_challenge_api(app, settings, actor, operator, reviewer, connection):
    DB = Depends(connection, scope='function')
    bearer = HTTPBearer(auto_error=False)

    def worker(credentials=Depends(bearer)):
        if not settings or not settings.challenge_token:
            raise HTTPException(503, 'Challenge worker credential NOT CONFIGURED; decisions remain blocked')
        supplied = credentials.credentials if credentials else ''
        if not secrets.compare_digest(supplied.encode(), settings.challenge_token.encode()):
            raise HTTPException(403, 'Separate challenge-worker credential required')
        return 'challenge-worker'

    def contract(role, effects):
        return {'x-role': role, 'x-side-effects': effects}

    @app.post('/api/results', response_model=Result, status_code=201, tags=['challenge'],
              openapi_extra=contract('operator', 'Immutable primary result + mandatory pending challenge job + audit; NOT acceptance; same-project references; stop blocks'))
    def submit(body: ResultInput, who=Depends(operator), db=DB):
        return submit_result(db, body, who)

    @app.get('/api/results', response_model=list[Result], tags=['challenge'],
             openapi_extra=contract('both', 'Read-only unadopted primary packages, not accepted recommendations'))
    def results(limit: int = Query(100, ge=1, le=100), offset: int = Query(0, ge=0), who=Depends(actor), db=DB):
        return listing(db, 'result', limit, offset)

    @app.post('/api/results/{result_id}/challenge', response_model=JobStatus, status_code=201, tags=['challenge'],
              openapi_extra=contract('both', 'Request new mandatory challenge; invalidates previous report/approval for this result; no worker fallback; 503 without worker config'))
    def challenge(result_id: str, body: ChallengeRequest, who=Depends(actor), db=DB):
        if not settings.challenge_token:
            raise HTTPException(503, 'Challenge worker NOT CONFIGURED')
        result = get(db, 'result', result_id)
        if current_result(db, result['task_id'])['id'] != result_id:
            raise HTTPException(409, 'Only the latest result can be challenged for adoption')
        return {k: v for k, v in make_job(db, result, who, body.reason).items() if k in JobStatus.model_fields}

    @app.get('/api/results/{result_id}/why', response_model=Why, tags=['challenge'],
             openapi_extra=contract('both', 'Read-only current triage, report findings, evidence IDs, alternative candidates and limitations; stale reports explicitly not current'))
    def why(result_id: str, who=Depends(actor), db=DB):
        result = get(db, 'result', result_id)
        decision = decide_task(db, result['task_id'])
        job = latest(db, 'challenge_job', 'result_id', result_id)
        report = latest(db, 'challenge_report', 'job_id', job['id']) if job else None
        return dict(result=result, decision=decision.model_dump(), latest_job={k: v for k, v in job.items() if k in JobStatus.model_fields} if job else None,
                    report=report, current=bool(report and decision.result_id == result_id and report['fingerprint'] == decision.fingerprint and job['state'] == 'completed'))

    @app.post('/api/results/{result_id}/adopt', response_model=Memory, status_code=201, tags=['challenge'],
              openapi_extra=contract('reviewer', 'Explicit adoption into decision-memory only after current Challenge ACCEPT + triage + required task approval; revalidated atomically; no execution'))
    def adopt(result_id: str, body: ChallengeRequest, who=Depends(reviewer), db=DB):
        return adopt_result(db, result_id, who, body.reason)

    @app.post('/api/challenge/jobs/claim', response_model=WorkItem | None, tags=['challenge-worker'],
              openapi_extra=contract('challenge-worker', 'Lease oldest eligible pending/expired job for 60s; supersede stale jobs; return server snapshot; token is NOT an operator/reviewer token'))
    def claim(who=Depends(worker), db=DB):
        return claim_job(db)

    @app.post('/api/challenge/jobs/{job_id}/complete', response_model=ChallengeReport, status_code=201, tags=['challenge-worker'],
              openapi_extra=contract('challenge-worker', 'Verify lease/current snapshot/policy/exact deterministic report, append immutable report and audit; no direct client-set verdict; stale/replay 409; forged output 422'))
    def complete(job_id: str, body: Completion, who=Depends(worker), db=DB):
        return complete_job(db, job_id, body)
