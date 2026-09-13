"""Bounded model requests: explicit selected context, reviewer consent, no adoption."""
import json
from app.ai_models import AIPolicy
from app.ai_gateway import GateDenied, fingerprint, scan
from app.store import get, put, audit, identity, now, stopped
from app.context import update


def policy(db):
    row = db.execute("SELECT body FROM records WHERE kind='ai_policy' ORDER BY seq DESC LIMIT 1").fetchone()
    return json.loads(row[0]) if row else dict(**AIPolicy().model_dump(), id='default-deny')


def prepare(db, body, who, gateway):
    task = get(db, 'task', body.task_id)
    model = get(db, 'ai_model', body.model_id)
    if body.purpose not in model['capabilities']:
        raise GateDenied('MODEL_CAPABILITY_DENIED')
    if body.classification in {'SECRET', 'CREDENTIAL'}:
        raise GateDenied('SECRET_CLASS_BLOCKED')
    if len(body.evidence_ids) + len(body.memory_ids) > 8:
        raise GateDenied('CONTEXT_COUNT_EXCEEDED')
    scan(body.prompt)
    context = [{'type': 'prompt', 'text': body.prompt}]
    for kind, ids in [('evidence', body.evidence_ids), ('memory', body.memory_ids)]:
        if len(ids) != len(set(ids)):
            raise GateDenied('DUPLICATE_CONTEXT')
        for key in ids:
            source = get(db, kind, key)
            if source['project_id'] != task['project_id']:
                raise GateDenied('CROSS_PROJECT_CONTEXT')
            if kind == 'memory' and source.get('task_id') not in {None, body.task_id}:
                raise GateDenied('CROSS_TASK_MEMORY')
            scan(source['content'])
            context.append({'type': kind, 'id': key, 'text': source['content'], 'untrusted': True})
    text = json.dumps(context, ensure_ascii=False)
    scan(text)
    # Explicit selected context is conservatively confidential, never auto-public.
    classification = 'CONFIDENTIAL' if len(context) > 1 else body.classification
    value = dict(**body.model_dump(), id=identity(), created_at=now(), project_id=task['project_id'],
                 context=text, context_hash=fingerprint(text), effective_classification=classification,
                 state='AWAITING_REVIEW', config_hash=gateway.config_hash, policy_id=policy(db)['id'])
    if len(text) > policy(db)['max_context_chars']:
        raise GateDenied('CONTEXT_SIZE_EXCEEDED')
    put(db, 'ai_request', value)
    audit(db, who, 'ai.request_prepared', value['id'], {'context_hash': value['context_hash'], 'classification': classification})
    return value


def check(db, request, gateway, consent):
    current = policy(db)
    model = get(db, 'ai_model', request['model_id'])
    provider = gateway.provider(model['provider_id'])
    if stopped(db)['active']:
        raise GateDenied('EMERGENCY_STOP')
    if request['state'] != 'AWAITING_REVIEW':
        raise GateDenied('REQUEST_NOT_PENDING')
    if consent.context_hash != request['context_hash']:
        raise GateDenied('CONTEXT_HASH_MISMATCH')
    if request['policy_id'] != current['id'] or request['config_hash'] != gateway.config_hash:
        raise GateDenied('STALE_POLICY_OR_CONFIG')
    task = get(db, 'task', request['task_id'])
    if task['action'] != 'read' or not task['preconditions_met']:
        raise GateDenied('READ_TASK_PRECONDITIONS_REQUIRED')
    required = [(model['provider_id'], current['providers']), (request['model_id'], current['models']),
                (request['project_id'], current['projects']), (request['purpose'], current['tasks']),
                (request['effective_classification'], current['data_classes']), (provider.region, current['regions'])]
    if any(value not in allowed for value, allowed in required):
        raise GateDenied('POLICY_ALLOWLIST_DENIED')
    if provider.mode != 'LOCAL':
        if current['privacy_lock'] or current['local_only'] or not current['allow_remote'] or not consent.allow_remote:
            raise GateDenied('REMOTE_EXPORT_DENIED')
        if provider.mode == 'EXTERNAL_PROVIDER' and not current['external_ai']:
            raise GateDenied('EXTERNAL_AI_DENIED')
    scan(request['context'])
    return current, model


def execute(store, key, consent, gateway, who):
    attempt = dict(id=identity(), request_id=key, created_at=now(), state='PENDING_OUTCOME', output_hash=None, reason=None)
    # Persist audit BEFORE possible I/O. A crash leaves explicit unknown outcome, never retry.
    with store.connect() as db:
        request = get(db, 'ai_request', key)
        try:
            current, model = check(db, request, gateway, consent)
        except GateDenied as error:
            attempt.update(state='BLOCKED', reason=str(error))
        attempt.update(task_id=request['task_id'], provider_id=get(db, 'ai_model', request['model_id'])['provider_id'],
                       model_id=request['model_id'], context_hash=request['context_hash'],
                       classification=request['effective_classification'], policy_id=request['policy_id'], tools=[],
                       permission={'actor': who, 'allow_remote': consent.allow_remote, 'context_hash': consent.context_hash, 'reason_hash': fingerprint(consent.reason)})
        put(db, 'ai_attempt', attempt)
        audit(db, who, 'ai.attempt', attempt['id'], attempt)
        if attempt['state'] == 'BLOCKED':
            return dict(attempt=attempt, output=None, allowed_for_action=False)
        request['state'] = 'RESERVED'
        update(db, request)
    output = None
    with store.connect() as db:
        request = get(db, 'ai_request', key)
        # Recheck policy/stop after reacquiring lock, serialize changes through send.
        request['state'] = 'AWAITING_REVIEW'
        try:
            current, model = check(db, request, gateway, consent)
            output = gateway.model_provider(model['provider_id']).generate(model['model'], request['context'], current['max_output_tokens'])
            attempt.update(state='DRAFT_UNCHALLENGED', output_hash=fingerprint(output))
        except GateDenied as error:
            attempt.update(state='BLOCKED', reason=str(error))
        except Exception:
            # Transport/schema errors never logged with sensitive payload/URL/token.
            attempt.update(state='UNAVAILABLE', reason='TRANSPORT_OR_RESPONSE_FAILURE_NO_FALLBACK')
        request['state'] = 'CONSUMED'
        update(db, request)
        update(db, attempt)
        audit(db, who, 'ai.outcome', attempt['id'], {'state': attempt['state'], 'output_hash': attempt['output_hash'], 'reason': attempt['reason']})
    return dict(attempt=attempt, output=output, allowed_for_action=False)
