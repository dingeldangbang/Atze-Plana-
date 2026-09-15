"""Agent registry v1: declared configurations, reference assignments, bounded runs through the AI consent chain.

No autonomous tool execution: allowed_tools is a declared bound; every tool call remains the separate
reviewer-gated MCP path. Runs reuse prepare()/execute() with all policy/consent/stop/PLAN gates intact.
"""
from fastapi import Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from app.agent_models import (Agent, AgentAssignment, AgentDeactivateInput, AgentInput, AgentRun,
                              AgentRunInput, AssignmentInput, UnlinkInput)
from app.ai_gateway import GateDenied, fingerprint
from app.ai_models import AIConsent, AIRequest
from app.ai_service import prepare, execute
from app.context import update
from app.store import get, put, listing, audit, identity, now
from app.storage import guard

CONFIG_FIELDS = ('name', 'description', 'model_id', 'purpose', 'instruction', 'allowed_tools')


def register_agent_api(app, actor, operator, reviewer, connection, store, storage, gateway):
    db_dependency = Depends(connection, scope='function')

    def contract(role, effects):
        return {'x-role': role, 'x-side-effects': effects}

    def validate_configuration(db, body):
        model = get(db, 'ai_model', body.model_id)
        if body.purpose not in model['capabilities']:
            raise HTTPException(422, 'Purpose is not within the registered model capabilities')

    def family_records(db, family_id):
        rows = db.execute("SELECT body FROM records WHERE kind='agent' AND json_extract(body,'$.family_id')=? ORDER BY json_extract(body,'$.version')",
                          (family_id,)).fetchall()
        import json
        return [json.loads(row[0]) for row in rows]

    def latest_family_record(db, family_id):
        import json
        row = db.execute("SELECT body FROM records WHERE kind='agent' AND json_extract(body,'$.family_id')=? ORDER BY json_extract(body,'$.version') DESC LIMIT 1",
                         (family_id,)).fetchone()
        return json.loads(row[0])

    def assigned(db, agent_id, task):
        row = db.execute("SELECT 1 FROM records WHERE kind='agent_assignment' AND json_extract(body,'$.agent_id')=? "
                         "AND json_extract(body,'$.state')='active' AND ((json_extract(body,'$.target_kind')='task' "
                         "AND json_extract(body,'$.target_id')=?) OR (json_extract(body,'$.target_kind')='project' "
                         "AND json_extract(body,'$.target_id')=?))", (agent_id, task['id'], task['project_id'])).fetchone()
        return row is not None

    @app.post('/api/agents', response_model=Agent, status_code=201, tags=['agents'],
              openapi_extra=contract('operator', 'Append declared agent configuration + audit; requires registered model; allowed_tools is a declared bound, never autonomous tool authority; stop blocks'))
    def create(body: AgentInput, who=Depends(operator), db=db_dependency):
        guard(db)
        validate_configuration(db, body)
        if db.execute("SELECT 1 FROM records WHERE kind='agent' AND json_extract(body,'$.name')=?", (body.name,)).fetchone():
            raise HTTPException(409, 'Agent name already registered in this workspace')
        value = dict(id=identity(), family_id=None, version=1, predecessor_id=None,
                     **body.model_dump(), state='active', created_by=who, created_at=now(), deactivated_at=None)
        value['family_id'] = value['id']
        put(db, 'agent', value)
        audit(db, who, 'agent.created', value['id'], {'name': body.name, 'model_id': body.model_id,
                                                      'purpose': body.purpose, 'allowed_tools': body.allowed_tools})
        return value

    @app.get('/api/agents', response_model=list[Agent], tags=['agents'],
             openapi_extra=contract('both', 'None; declared registry only, no autonomy or availability claims'))
    def agents(limit: int = Query(50, ge=1, le=500), offset: int = Query(0, ge=0),
               who=Depends(actor), db=db_dependency):
        return listing(db, 'agent', limit, offset)

    @app.get('/api/agents/{agent_id}', response_model=Agent, tags=['agents'],
             openapi_extra=contract('both', 'None; declared registry only'))
    def agent_detail(agent_id: str, who=Depends(actor), db=db_dependency):
        return get(db, 'agent', agent_id)

    @app.get('/api/agents/{agent_id}/versions', response_model=list[Agent], tags=['agents'],
             openapi_extra=contract('both', 'None; immutable configuration history'))
    def agent_versions(agent_id: str, who=Depends(actor), db=db_dependency):
        return family_records(db, get(db, 'agent', agent_id)['family_id'])

    @app.post('/api/agents/{agent_id}/configure', response_model=Agent, status_code=201, tags=['agents'],
              openapi_extra=contract('operator', 'Append new immutable configuration version + audit; identical configuration rejected; deactivated family blocks; stop blocks'))
    def configure(agent_id: str, body: AgentInput, who=Depends(operator), db=db_dependency):
        guard(db)
        current = get(db, 'agent', agent_id)
        latest = latest_family_record(db, current['family_id'])
        if latest['state'] != 'active':
            raise HTTPException(409, 'Agent family is deactivated')
        validate_configuration(db, body)
        if fingerprint({field: body.model_dump()[field] for field in CONFIG_FIELDS}) == \
           fingerprint({field: latest[field] for field in CONFIG_FIELDS}):
            raise HTTPException(409, 'Identical configuration is not a new version')
        if body.name != latest['name'] and db.execute(
                "SELECT 1 FROM records WHERE kind='agent' AND json_extract(body,'$.name')=? AND json_extract(body,'$.family_id')<>?",
                (body.name, latest['family_id'])).fetchone():
            raise HTTPException(409, 'Agent name already registered in this workspace')
        value = dict(id=identity(), family_id=latest['family_id'], version=latest['version'] + 1,
                     predecessor_id=latest['id'], **body.model_dump(), state='active', created_by=who,
                     created_at=now(), deactivated_at=None)
        put(db, 'agent', value)
        audit(db, who, 'agent.versioned', value['id'], {'family_id': value['family_id'], 'version': value['version'],
                                                         'predecessor_id': latest['id']})
        return value

    @app.post('/api/agents/{agent_id}/assignments', response_model=AgentAssignment, status_code=201, tags=['agents'],
              openapi_extra=contract('operator', 'Append reference assignment + audit; no autonomy granted; existing task/project target required; stop blocks'))
    def assign(agent_id: str, body: AssignmentInput, who=Depends(operator), db=db_dependency):
        guard(db)
        agent = get(db, 'agent', agent_id)
        if agent['state'] != 'active':
            raise HTTPException(409, 'Agent is deactivated')
        get(db, body.target_kind, body.target_id)
        if db.execute("SELECT 1 FROM records WHERE kind='agent_assignment' AND json_extract(body,'$.agent_id')=? "
                      "AND json_extract(body,'$.target_kind')=? AND json_extract(body,'$.target_id')=? "
                      "AND json_extract(body,'$.state')='active'",
                      (agent_id, body.target_kind, body.target_id)).fetchone():
            raise HTTPException(409, 'Active assignment to this target already exists')
        value = dict(id=identity(), agent_id=agent_id, target_kind=body.target_kind, target_id=body.target_id,
                     state='active', created_by=who, created_at=now(), unlinked_at=None)
        put(db, 'agent_assignment', value)
        audit(db, who, 'agent.assigned', value['id'], {'agent_id': agent_id, 'target_kind': body.target_kind,
                                                        'target_id': body.target_id})
        return value

    @app.get('/api/agents/{agent_id}/assignments', response_model=list[AgentAssignment], tags=['agents'],
             openapi_extra=contract('both', 'None; reference list including unlinked history'))
    def agent_assignments(agent_id: str, who=Depends(actor), db=db_dependency):
        get(db, 'agent', agent_id)
        import json
        rows = db.execute("SELECT body FROM records WHERE kind='agent_assignment' AND json_extract(body,'$.agent_id')=? ORDER BY seq",
                          (agent_id,)).fetchall()
        return [json.loads(row[0]) for row in rows]

    @app.post('/api/agents/{agent_id}/unlink', response_model=AgentAssignment, tags=['agents'],
              openapi_extra=contract('operator', 'Mark assignment unlinked + audit; reference removed, history retained; stop blocks'))
    def unlink(agent_id: str, body: UnlinkInput, who=Depends(operator), db=db_dependency):
        guard(db)
        get(db, 'agent', agent_id)
        value = get(db, 'agent_assignment', body.assignment_id)
        if value['agent_id'] != agent_id:
            raise HTTPException(404, 'Assignment belongs to another agent')
        if value['state'] != 'active':
            raise HTTPException(409, 'Assignment is already unlinked')
        value.update(state='unlinked', unlinked_at=now())
        update(db, value)
        audit(db, who, 'agent.unlinked', value['id'], {'agent_id': agent_id, 'target_kind': value['target_kind'],
                                                        'target_id': value['target_id']})
        return value

    @app.post('/api/agents/{agent_id}/runs', response_model=AgentRun, status_code=201, tags=['agents'],
              openapi_extra=contract('operator', 'Prepare bounded run through the full AI prepare gates (registered model, capability, classification, context scan, size, PLAN binding); active task/project assignment required; NO network; reviewer consent required before execution'))
    def create_run(agent_id: str, body: AgentRunInput, who=Depends(operator), db=db_dependency):
        agent = get(db, 'agent', agent_id)
        if agent['state'] != 'active':
            raise HTTPException(409, 'Agent is deactivated')
        task = get(db, 'task', body.task_id)
        if not assigned(db, agent_id, task):
            raise HTTPException(409, 'Agent is not assigned to this task or its project')
        prompt = f"AGENT INSTRUCTION:\n{agent['instruction']}\n\nUSER REQUEST:\n{body.prompt}"
        ai_body = AIRequest(task_id=body.task_id, model_id=agent['model_id'], purpose=agent['purpose'],
                            classification=body.classification, prompt=prompt)
        try:
            request_value = prepare(db, ai_body, who, gateway, storage)
        except GateDenied as error:
            # Return (do not raise) so the request-scoped connection commits the denial audit.
            audit(db, who, 'agent.run_denied', identity(), {'agent_id': agent_id, 'reason': str(error)})
            return JSONResponse(status_code=409, content={'detail': str(error), 'state': 'BLOCKED'})
        run = dict(id=identity(), agent_id=agent_id, agent_version=agent['version'], task_id=body.task_id,
                   request_id=request_value['id'], context_hash=request_value['context_hash'],
                   state='AWAITING_CONSENT', attempt_id=None, blocked_reason=None, created_by=who,
                   created_at=now(), outcome_at=None)
        put(db, 'agent_run', run)
        audit(db, who, 'agent.run_prepared', run['id'], {'agent_id': agent_id, 'agent_version': agent['version'],
                                                          'context_hash': run['context_hash']})
        return run

    @app.get('/api/agents/{agent_id}/runs', response_model=list[AgentRun], tags=['agents'],
             openapi_extra=contract('both', 'None; immutable run history with attempt states; outputs are never stored'))
    def agent_runs(agent_id: str, who=Depends(actor), db=db_dependency):
        get(db, 'agent', agent_id)
        import json
        rows = db.execute("SELECT body FROM records WHERE kind='agent_run' AND json_extract(body,'$.agent_id')=? ORDER BY seq",
                          (agent_id,)).fetchall()
        return [json.loads(row[0]) for row in rows]

    @app.post('/api/agents/{agent_id}/runs/{run_id}/consent', tags=['agents'],
              openapi_extra=contract('reviewer', 'Explicit once-per-run execution consent; reuses the full AI execute gates (exact context hash, policy/config currency, allowlists, privacy/remote, stop, PLAN binding); bounded authenticated transport; output DRAFT_UNCHALLENGED, never stored or adopted; no tool execution'))
    def consent_run(agent_id: str, run_id: str, body: AIConsent, who=Depends(reviewer)) -> dict:
        with store.connect() as db:
            run = get(db, 'agent_run', run_id)
            if run['agent_id'] != agent_id:
                raise HTTPException(404, 'Run belongs to another agent')
            if run['state'] != 'AWAITING_CONSENT':
                raise HTTPException(409, 'Run is not awaiting consent')
        result = execute(store, run['request_id'], body, gateway, who, storage)
        attempt = result['attempt']
        with store.connect() as db:
            run.update(state=attempt['state'], attempt_id=attempt['id'], outcome_at=now(),
                       blocked_reason=attempt.get('reason'))
            update(db, run)
            audit(db, who, 'agent.run_outcome', run['id'], {'state': attempt['state'], 'reason': attempt.get('reason'),
                                                             'attempt_id': attempt['id']})
        return {'agent_run': run, 'attempt': attempt, 'output': result['output'], 'allowed_for_action': False}

    @app.post('/api/agents/{agent_id}/deactivate', response_model=Agent, tags=['agents'],
              openapi_extra=contract('reviewer', 'Confirmed family-wide deactivation + audit; retains configuration, assignments and run history; blocks new runs/assignments/versions'))
    def deactivate(agent_id: str, body: AgentDeactivateInput, who=Depends(reviewer), db=db_dependency):
        guard(db)
        value = get(db, 'agent', agent_id)
        if value['state'] != 'active':
            raise HTTPException(409, 'Agent family is already deactivated')
        for record in family_records(db, value['family_id']):
            if record['state'] == 'active':
                record.update(state='deactivated', deactivated_at=now())
                update(db, record)
        audit(db, who, 'agent.deactivated', value['id'],
              {'family_id': value['family_id'], 'reason': body.reason})
        return get(db, 'agent', agent_id)
