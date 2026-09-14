"""Result/challenge state machine. No worker fallback in API request handling."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
import secrets
from fastapi import HTTPException
from app.store import get, put, listing, audit, identity, now, stopped
from app.context import references, update, index_text
from app.plan_service import task_gate
from app.challenge_rules import analyze, POLICY_VERSION, MAX_PROJECT_EVIDENCE, MAX_SNAPSHOT_EVIDENCE_BYTES


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def latest(db, kind, field, key):
    # kind/field only supplied as internal constants, never request values.
    row = db.execute(f"SELECT body FROM records WHERE kind=? AND json_extract(body, '$.{field}')=? ORDER BY seq DESC LIMIT 1", (kind, key)).fetchone()
    return json.loads(row[0]) if row else None


def current_result(db, task_id):
    return latest(db, 'result', 'task_id', task_id)


def snapshot(db, result, storage=None):
    task = get(db, 'task', result['task_id'])
    count, size = db.execute("SELECT COUNT(*),COALESCE(SUM(LENGTH(CAST(body AS BLOB))),0) FROM records WHERE kind='evidence' AND json_extract(body,'$.project_id')=?", (task['project_id'],)).fetchone()
    truncated = count > MAX_PROJECT_EVIDENCE or size > MAX_SNAPSHOT_EVIDENCE_BYTES
    rows = [] if truncated else db.execute("SELECT body FROM records WHERE kind='evidence' AND json_extract(body,'$.project_id')=? ORDER BY seq LIMIT ?", (task['project_id'], MAX_PROJECT_EVIDENCE + 1)).fetchall()
    stop_event = latest(db, 'audit', 'event', 'control.stop_changed')
    value = dict(policy_version=POLICY_VERSION, task=task, result=result,
                 evidence=[json.loads(row[0]) for row in rows], truncated=truncated, project_evidence_count=count, project_evidence_bytes=size,
                 stop_revision=stop_event['id'] if stop_event else 'initial')
    plan = task_gate(db, task['id'], storage)
    if plan is not None:
        value['plan_context'] = plan
    return value, digest(value)


def make_job(db, result, who, reason, storage=None):
    if stopped(db)['active']:
        raise HTTPException(409, 'Emergency stop blocks challenge scheduling')
    value, fingerprint = snapshot(db, result, storage)
    job = dict(id=identity(), result_id=result['id'], state='pending', fingerprint=fingerprint,
               snapshot=value, created_at=now(), reason=reason, lease_hash=None, lease_expires_at=None)
    put(db, 'challenge_job', job)
    audit(db, who, 'challenge.requested', job['id'], {'result_id': result['id'], 'fingerprint': fingerprint, 'reason': reason})
    return job


def submit_result(db, body, who, storage=None):
    task = get(db, 'task', body.task_id)
    for item in body.claims + body.alternatives:
        references(db, task['project_id'], item.evidence_ids)
    result = put(db, 'result', dict(**body.model_dump(), id=identity(), created_at=now(), created_by=who))
    audit(db, who, 'result.submitted', result['id'], {'task_id': body.task_id})
    make_job(db, result, who, 'Mandatory initial challenge', storage)
    return result


def claim_job(db, storage=None):
    if stopped(db)['active']:
        raise HTTPException(409, 'Emergency stop blocks worker claims')
    rows = db.execute("SELECT body FROM records WHERE kind='challenge_job' AND (json_extract(body,'$.state')='pending' OR (json_extract(body,'$.state')='running' AND json_extract(body,'$.lease_expires_at')<=?)) ORDER BY seq LIMIT 100", (now(),)).fetchall()
    for row in rows:
        job = json.loads(row[0])
        result = get(db, 'result', job['result_id'])
        active = current_result(db, result['task_id'])
        newest_job = latest(db, 'challenge_job', 'result_id', result['id'])
        _, fingerprint = snapshot(db, result, storage)
        if active['id'] != result['id'] or newest_job['id'] != job['id'] or fingerprint != job['fingerprint']:
            job['state'] = 'superseded'
            update(db, job)
            audit(db, 'challenge-worker', 'challenge.superseded', job['id'])
            continue
        lease = secrets.token_urlsafe(32)
        job.update(state='running', lease_hash=hashlib.sha256(lease.encode()).hexdigest(),
                   lease_expires_at=(datetime.now(timezone.utc) + timedelta(seconds=60)).isoformat())
        update(db, job)
        audit(db, 'challenge-worker', 'challenge.claimed', job['id'])
        return dict(job_id=job['id'], lease=lease, fingerprint=job['fingerprint'], snapshot=job['snapshot'])
    return None


def complete_job(db, job_id, body, storage=None):
    job = get(db, 'challenge_job', job_id)
    if stopped(db)['active'] or job['state'] != 'running' or not job['lease_expires_at'] or job['lease_expires_at'] <= now():
        raise HTTPException(409, 'Job is not active or lease expired')
    if not secrets.compare_digest(job['lease_hash'], hashlib.sha256(body.lease.encode()).hexdigest()):
        raise HTTPException(409, 'Lease does not match this worker claim')
    result = get(db, 'result', job['result_id'])
    active = current_result(db, result['task_id'])
    _, fresh = snapshot(db, result, storage)
    if active['id'] != result['id'] or latest(db, 'challenge_job', 'result_id', result['id'])['id'] != job_id or body.fingerprint != job['fingerprint'] or fresh != body.fingerprint:
        raise HTTPException(409, 'Result, challenge or evidence changed; request a fresh challenge')
    # Verification is not a fallback: without worker submission nothing is accepted.
    expected = analyze(job['snapshot']).model_dump()
    if body.analysis.model_dump() != expected:
        raise HTTPException(422, 'Report does not match versioned deterministic challenge rules')
    report = put(db, 'challenge_report', dict(id=identity(), job_id=job_id, result_id=result['id'],
                                             fingerprint=fresh, created_at=now(), worker_identity='challenge-worker', analysis=expected))
    job.update(state='completed', lease_hash=None)
    update(db, job)
    audit(db, 'challenge-worker', 'challenge.completed', job_id, {'report_id': report['id'], 'verdict': expected['verdict'], 'fingerprint': fresh})
    return report


def challenge_gate(db, task_id, storage=None):
    result = current_result(db, task_id)
    if not result:
        return dict(status='BLOCK', reasons=['No primary result package; mandatory challenge not run'], result_id=None, challenge_id=None, fingerprint=None)
    _, fresh = snapshot(db, result, storage)
    job = latest(db, 'challenge_job', 'result_id', result['id'])
    report = latest(db, 'challenge_report', 'job_id', job['id']) if job else None
    base = dict(result_id=result['id'], challenge_id=report['id'] if report else None, fingerprint=fresh)
    if not job or job['state'] != 'completed' or not report:
        return dict(**base, status='BLOCK', reasons=['Mandatory challenge pending, expired or superseded; no in-process fallback'])
    if job['fingerprint'] != fresh or report['fingerprint'] != fresh or report['analysis']['policy_version'] != POLICY_VERSION:
        return dict(**base, status='BLOCK', reasons=['Challenge is stale: evidence, result, stop revision or policy changed'])
    analysis = report['analysis']
    status = 'ACCEPT' if analysis['verdict'] == 'PASS' else analysis['verdict']
    reasons = [f['message'] for f in analysis['findings'] if f['severity'] != 'info']
    return dict(**base, status=status, reasons=reasons or ['Challenge passed for submitted structured claims only; no execution or global truth guarantee'])


def decide_task(db, task_id, storage=None):
    from app.triage import evaluate
    task = get(db, 'task', task_id)
    gate = challenge_gate(db, task_id, storage)
    evidence = [get(db, 'evidence', key) for key in task['evidence_ids']]
    row = db.execute("SELECT body FROM records WHERE kind='approval' AND json_extract(body,'$.task_id')=? AND json_extract(body,'$.challenge_id')=? AND json_extract(body,'$.fingerprint')=? ORDER BY seq DESC LIMIT 1", (task_id, gate['challenge_id'], gate['fingerprint'])).fetchone()
    approval_id = json.loads(row[0])['id'] if row else None
    return evaluate(task, evidence, stopped(db)['active'], approval_id, gate)


def adopt_result(db, result_id, who, reason, storage=None):
    result = get(db, 'result', result_id)
    decision = decide_task(db, result['task_id'], storage)
    if decision.result_id != result_id or decision.validation_status != 'ACCEPT' or decision.state not in {'eligible', 'approved'}:
        raise HTTPException(409, 'Current challenge, triage and any required approval must permit adoption')
    previous = latest(db, 'memory', 'decision_challenge_id', decision.challenge_id)
    if previous:
        raise HTTPException(409, 'This challenge result was already adopted')
    task = get(db, 'task', result['task_id'])
    ids = sorted({key for item in result['claims'] for key in item['evidence_ids']})
    content = f"Structured-claims-only decision snapshot for result {result_id}; challenge {decision.challenge_id}; fingerprint {decision.fingerprint}. Primary free text was NOT adopted or semantically validated. No execution authorization."
    value = dict(id=identity(), project_id=task['project_id'], category='decision', content=content,
                 task_id=task['id'], evidence_ids=ids, commit_sha=None, created_at=now(), state='recorded',
                 sha256=hashlib.sha256(content.encode()).hexdigest(), decision_result_id=result_id,
                 decision_challenge_id=decision.challenge_id, decision_fingerprint=decision.fingerprint)
    put(db, 'memory', value)
    index_text(db, task['project_id'], value['id'], value['content'])
    audit(db, who, 'result.adopted', result_id, {'memory_id': value['id'], 'challenge_id': decision.challenge_id, 'reason': reason})
    return value
