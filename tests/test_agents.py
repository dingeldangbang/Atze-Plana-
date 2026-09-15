"""Agent builder v1 contract tests: declared registry, assignments, bounded runs through the full AI consent chain."""
import json
from test_ai_privacy import ai, receiver  # Real isolated loopback transport fixtures, not model inference.


def agent_body(model_id, name='bench-analyst', purpose='analysis', instruction=None, allowed_tools=None):
    return {'name': name, 'description': 'Synthetic fixture agent, no autonomy claim',
            'model_id': model_id, 'purpose': purpose,
            'instruction': instruction or 'Work strictly from the submitted context; never invent measurements or claim tool authority.',
            'allowed_tools': allowed_tools or []}


def declare(client, model_id, **overrides):
    response = client.post('/api/agents', json=agent_body(model_id, **overrides))
    assert response.status_code == 201, response.text
    return response.json()


def assign_task(client, agent, task_id):
    response = client.post(f"/api/agents/{agent['id']}/assignments", json={'target_kind': 'task', 'target_id': task_id})
    assert response.status_code == 201, response.text
    return response.json()


def prepare_run(client, agent, task_id, prompt='Summarize the submitted context without inventing facts.', **overrides):
    response = client.post(f"/api/agents/{agent['id']}/runs", json={'task_id': task_id, 'prompt': prompt, **overrides})
    assert response.status_code == 201, response.text
    return response.json()


def consent(client, reviewer, agent, run, **overrides):
    return client.post(f"/api/agents/{agent['id']}/runs/{run['id']}/consent", headers=reviewer,
                       json={'context_hash': run['context_hash'], 'reason': 'Explicit isolated agent run test', **overrides})


def test_agent_declaration_validation(ai):
    """AGT-001: agent declaration validates unique name, registered model, capability purpose, allowlisted tools, operator role."""
    client, reviewer, body, *_ = ai
    agent = declare(client, body['model_id'])
    assert agent['version'] == 1 and agent['state'] == 'active' and agent['family_id'] == agent['id']
    assert client.post('/api/agents', json=agent_body(body['model_id'])).status_code == 409
    assert client.post('/api/agents', json=agent_body('missing-model', name='other')).status_code == 404
    assert client.post('/api/agents', json=agent_body(body['model_id'], name='planner', purpose='plan')).status_code == 422
    assert client.post('/api/agents', json=agent_body(body['model_id'], name='tooler', allowed_tools=['terminal'])).status_code == 422
    assert client.post('/api/agents', headers=reviewer, json=agent_body(body['model_id'], name='reviewer-agent')).status_code == 403
    assert len(client.get('/api/agents').json()) == 1


def test_agent_configuration_versioning(ai):
    """AGT-002: configure appends immutable versions with predecessor chain; identical configuration rejected 409."""
    client, reviewer, body, *_ = ai
    agent = declare(client, body['model_id'])
    assert client.post(f"/api/agents/{agent['id']}/configure", json=agent_body(body['model_id'])).status_code == 409
    revised = client.post(f"/api/agents/{agent['id']}/configure",
                          json=agent_body(body['model_id'], instruction='Revised fixture instruction; still no autonomy.'))
    assert revised.status_code == 201
    assert revised.json()['version'] == 2 and revised.json()['predecessor_id'] == agent['id']
    assert revised.json()['family_id'] == agent['family_id']
    assert [v['version'] for v in client.get(f"/api/agents/{agent['id']}/versions").json()] == [1, 2]
    assert client.get(f"/api/agents/{agent['id']}").json()['version'] == 1  # record id addresses exactly this version
    assert client.get(f"/api/agents/{revised.json()['id']}").json()['version'] == 2


def test_agent_assignments_are_references(ai):
    """AGT-003: assignments attach agents by reference to existing tasks/projects; duplicates 409; unlink keeps history."""
    client, reviewer, body, *_ = ai
    agent = declare(client, body['model_id'])
    task = next(t for t in client.get('/api/tasks').json() if t['id'] == body['task_id'])
    assert client.post(f"/api/agents/{agent['id']}/assignments",
                       json={'target_kind': 'task', 'target_id': 'missing'}).status_code == 404
    assignment = assign_task(client, agent, body['task_id'])
    assert assignment['state'] == 'active'
    assert client.post(f"/api/agents/{agent['id']}/assignments",
                       json={'target_kind': 'task', 'target_id': body['task_id']}).status_code == 409
    project_assignment = client.post(f"/api/agents/{agent['id']}/assignments",
                                     json={'target_kind': 'project', 'target_id': task['project_id']})
    assert project_assignment.status_code == 201
    unlinked = client.post(f"/api/agents/{agent['id']}/unlink", json={'assignment_id': assignment['id']})
    assert unlinked.status_code == 200 and unlinked.json()['state'] == 'unlinked' and unlinked.json()['unlinked_at']
    assert client.post(f"/api/agents/{agent['id']}/unlink", json={'assignment_id': assignment['id']}).status_code == 409
    states = [a['state'] for a in client.get(f"/api/agents/{agent['id']}/assignments").json()]
    assert states == ['unlinked', 'active']


def test_agent_run_requires_active_assignment(ai):
    """AGT-004: run preparation requires an active task or project assignment; prepared run awaits reviewer consent."""
    client, reviewer, body, *_ = ai
    agent = declare(client, body['model_id'])
    denied = client.post(f"/api/agents/{agent['id']}/runs",
                         json={'task_id': body['task_id'], 'prompt': 'Synthetic agent task prompt'})
    assert denied.status_code == 409 and 'not assigned' in denied.json()['detail']
    assert client.get(f"/api/agents/{agent['id']}/runs").json() == []
    assign_task(client, agent, body['task_id'])
    run = prepare_run(client, agent, body['task_id'])
    assert run['state'] == 'AWAITING_CONSENT' and len(run['context_hash']) == 64
    assert run['agent_version'] == 1 and run['request_id']


def test_agent_run_prepare_denial_is_durable(ai):
    """AGT-005: prepare-level denials (secret classification) return 409 BLOCKED with audit and no run record."""
    client, reviewer, body, *_ = ai
    agent = declare(client, body['model_id'])
    assign_task(client, agent, body['task_id'])
    denied = client.post(f"/api/agents/{agent['id']}/runs",
                         json={'task_id': body['task_id'], 'prompt': 'Synthetic prompt', 'classification': 'SECRET'})
    assert denied.status_code == 409
    assert denied.json() == {'detail': 'SECRET_CLASS_BLOCKED', 'state': 'BLOCKED'}
    assert client.get(f"/api/agents/{agent['id']}/runs").json() == []
    events = [e['event'] for e in client.get('/api/audit', headers=reviewer).json()]
    assert 'agent.run_denied' in events


def test_agent_run_default_deny_blocks_before_transport(ai):
    """AGT-006: consent under default-deny policy blocks with durable attempt and zero network traffic."""
    client, reviewer, body, pol, seen, *_ = ai
    agent = declare(client, body['model_id'])
    assign_task(client, agent, body['task_id'])
    run = prepare_run(client, agent, body['task_id'])
    result = consent(client, reviewer, agent, run).json()
    assert result['attempt']['state'] == 'BLOCKED' and result['attempt']['reason'] == 'POLICY_ALLOWLIST_DENIED'
    assert result['output'] is None and result['agent_run']['state'] == 'BLOCKED'
    assert result['agent_run']['blocked_reason'] == 'POLICY_ALLOWLIST_DENIED'
    assert seen == [] and result['allowed_for_action'] is False


def test_agent_run_full_consent_chain_real_transport(ai):
    """AGT-007: full chain prepare→reviewer consent→real loopback transport; instruction and request transmitted; output unchallenged."""
    client, reviewer, body, pol, seen, *_ = ai
    assert client.post('/api/ai/policy', headers=reviewer, json=pol).status_code == 201
    agent = declare(client, body['model_id'], allowed_tools=['search_engine'])
    assign_task(client, agent, body['task_id'])
    run = prepare_run(client, agent, body['task_id'])
    result = consent(client, reviewer, agent, run).json()
    assert result['attempt']['state'] == 'DRAFT_UNCHALLENGED'
    assert result['output'].startswith('transport receipt ')
    assert result['agent_run']['state'] == 'DRAFT_UNCHALLENGED' and result['agent_run']['attempt_id']
    assert result['allowed_for_action'] is False
    assert len(seen) == 1 and seen[0][0] == '/v1/chat/completions'
    transmitted = json.dumps(seen[0][1])
    assert 'AGENT INSTRUCTION' in transmitted and 'USER REQUEST' in transmitted
    runs = client.get(f"/api/agents/{agent['id']}/runs").json()
    assert [r['state'] for r in runs] == ['DRAFT_UNCHALLENGED']
    assert 'transport receipt' not in json.dumps(runs)  # output never stored


def test_agent_consent_hash_and_replay_protection(ai):
    """AGT-008: wrong context hash blocks; a consumed run cannot be consented again."""
    client, reviewer, body, pol, seen, *_ = ai
    client.post('/api/ai/policy', headers=reviewer, json=pol)
    agent = declare(client, body['model_id'])
    assign_task(client, agent, body['task_id'])
    run = prepare_run(client, agent, body['task_id'])
    mismatch = consent(client, reviewer, agent, run, context_hash='a' * 64).json()
    assert mismatch['attempt']['state'] == 'BLOCKED' and mismatch['attempt']['reason'] == 'CONTEXT_HASH_MISMATCH'
    assert mismatch['agent_run']['state'] == 'BLOCKED'
    assert seen == []
    result = consent(client, reviewer, agent, run)
    assert result.status_code == 409 and 'not awaiting consent' in result.json()['detail']
    assert seen == []


def test_agent_roles_for_prepare_and_consent(ai):
    """AGT-009: operator prepares runs and cannot consent; reviewer consents and cannot declare/prepare."""
    client, reviewer, body, pol, *_ = ai
    client.post('/api/ai/policy', headers=reviewer, json=pol)
    agent = declare(client, body['model_id'])
    assign_task(client, agent, body['task_id'])
    run = prepare_run(client, agent, body['task_id'])
    operator_consent = client.post(f"/api/agents/{agent['id']}/runs/{run['id']}/consent",
                                   json={'context_hash': run['context_hash'], 'reason': 'Operator cannot consent runs'})
    assert operator_consent.status_code == 403
    reviewer_prepare = client.post(f"/api/agents/{agent['id']}/runs", headers=reviewer,
                                   json={'task_id': body['task_id'], 'prompt': 'Reviewer cannot prepare'})
    assert reviewer_prepare.status_code == 403


def test_agent_run_emergency_stop(ai):
    """AGT-010: emergency stop blocks registry mutations and consent execution; reads stay available."""
    client, reviewer, body, pol, seen, *_ = ai
    client.post('/api/ai/policy', headers=reviewer, json=pol)
    agent = declare(client, body['model_id'])
    assign_task(client, agent, body['task_id'])
    run = prepare_run(client, agent, body['task_id'])
    client.post('/api/control/stop', headers=reviewer, json={'active': True, 'reason': 'Isolated agent stop'})
    assert client.post('/api/agents', json=agent_body(body['model_id'], name='blocked-agent')).status_code == 409
    assert client.post(f"/api/agents/{agent['id']}/assignments",
                       json={'target_kind': 'task', 'target_id': body['task_id']}).status_code == 409
    result = consent(client, reviewer, agent, run).json()
    assert result['attempt']['reason'] == 'EMERGENCY_STOP' and result['agent_run']['state'] == 'BLOCKED'
    assert seen == []
    assert client.get(f"/api/agents/{agent['id']}/runs").status_code == 200
    client.post('/api/control/stop', headers=reviewer, json={'active': False, 'reason': 'Isolated reset'})
    assert prepare_run(client, agent, body['task_id'])['state'] == 'AWAITING_CONSENT'


def test_agent_deactivation_reviewer_confirmed_and_retained(ai):
    """AGT-011: reviewer confirm+reason deactivates the family; blocks runs/assignments/versions; history stays readable."""
    client, reviewer, body, *_ = ai
    agent = declare(client, body['model_id'])
    client.post(f"/api/agents/{agent['id']}/configure", json=agent_body(body['model_id'], instruction='Second fixture version.'))
    assign_task(client, agent, body['task_id'])
    run = prepare_run(client, agent, body['task_id'])
    assert client.post(f"/api/agents/{agent['id']}/deactivate",
                       json={'confirm': True, 'reason': 'Operator cannot deactivate agents'}).status_code == 403
    assert client.post(f"/api/agents/{agent['id']}/deactivate", headers=reviewer,
                       json={'confirm': False, 'reason': 'x' * 20}).status_code == 422
    deactivated = client.post(f"/api/agents/{agent['id']}/deactivate", headers=reviewer,
                              json={'confirm': True, 'reason': 'Fixture agent retirement, history retained'})
    assert deactivated.status_code == 200
    assert all(v['state'] == 'deactivated' for v in client.get(f"/api/agents/{agent['id']}/versions").json())
    assert client.post(f"/api/agents/{agent['id']}/deactivate", headers=reviewer,
                       json={'confirm': True, 'reason': 'second attempt'}).status_code == 409
    assert client.post(f"/api/agents/{agent['id']}/runs",
                       json={'task_id': body['task_id'], 'prompt': 'Blocked after retirement'}).status_code == 409
    assert client.post(f"/api/agents/{agent['id']}/assignments",
                       json={'target_kind': 'task', 'target_id': body['task_id']}).status_code == 409
    assert client.post(f"/api/agents/{agent['id']}/configure",
                       json=agent_body(body['model_id'], instruction='Blocked version.')).status_code == 409
    assert [r['id'] for r in client.get(f"/api/agents/{agent['id']}/runs").json()] == [run['id']]


def test_agent_audit_chain(ai):
    """AGT-012: audit covers creation, versioning, assignment, run preparation, outcome and confirmed deactivation."""
    client, reviewer, body, pol, *_ = ai
    client.post('/api/ai/policy', headers=reviewer, json=pol)
    agent = declare(client, body['model_id'])
    client.post(f"/api/agents/{agent['id']}/configure", json=agent_body(body['model_id'], instruction='Second fixture version.'))
    assign_task(client, agent, body['task_id'])
    run = prepare_run(client, agent, body['task_id'])
    consent(client, reviewer, agent, run)
    client.post(f"/api/agents/{agent['id']}/deactivate", headers=reviewer,
                json={'confirm': True, 'reason': 'Fixture lifecycle complete'})
    events = [e['event'] for e in client.get('/api/audit', headers=reviewer).json() if e['event'].startswith('agent.')]
    assert events == ['agent.created', 'agent.versioned', 'agent.assigned', 'agent.run_prepared',
                      'agent.run_outcome', 'agent.deactivated']
