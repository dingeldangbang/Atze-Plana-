"""PLAN manifests verify real selected sources; never promote content to truth."""
import hashlib
import json
from fastapi import HTTPException
from app.store import get, put, audit, identity, now, stopped

MAX_CONTEXT_BYTES = 1024 * 1024


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def latest(db, kind, field, key):
    # Field/kind are internal constants only.
    row = db.execute(f"SELECT body FROM records WHERE kind=? AND json_extract(body,'$.{field}')=? ORDER BY seq DESC LIMIT 1", (kind, key)).fetchone()
    return json.loads(row[0]) if row else None


def task_plan(db, task_id):
    return latest(db, 'plan', 'task_id', task_id)


def guard(db):
    if stopped(db)['active']:
        raise HTTPException(409, 'Emergency stop blocks PLAN mutation')


def manifest(db, plan, resources, storage, metadata):
    task = get(db, 'task', plan['task_id'])
    entries, texts, seen, size = [], [], set(), 0
    dependency_cache, dependency_bytes = {}, 0
    for ref in resources:
        key = (ref['kind'], ref['id'])
        if key in seen:
            raise HTTPException(422, 'Duplicate PLAN resource')
        seen.add(key)
        value = get(db, *key)
        if value['project_id'] != plan['project_id']:
            raise HTTPException(422, 'PLAN source belongs to another project')
        if ref['kind'] == 'memory' and value.get('task_id') not in {None, plan['task_id']}:
            raise HTTPException(422, 'PLAN memory belongs to another task')
        if ref['kind'] == 'archive':
            if storage is None:
                raise HTTPException(503, 'PLAN archive verification unavailable')
            raw = storage.checked(value)
            text = raw.decode('utf-8')
        else:
            text = value['content']
            raw = text.encode()
        size += len(raw)
        if size > MAX_CONTEXT_BYTES:
            raise HTTPException(413, 'PLAN content exceeds bounded 1MiB scope')
        content_hash = hashlib.sha256(raw).hexdigest()
        if content_hash != value['sha256']:
            raise HTTPException(503, 'PLAN source integrity mismatch')
        deps = []
        for eid in value.get('evidence_ids', []):
            if eid not in dependency_cache:
                if len(dependency_cache) >= 64:
                    raise HTTPException(413, 'PLAN evidence dependencies exceed bounded scope')
                evidence = get(db, 'evidence', eid)
                if evidence['project_id'] != plan['project_id']:
                    raise HTTPException(422, 'PLAN evidence dependency belongs to another project')
                raw_evidence = evidence['content'].encode()
                dependency_bytes += len(raw_evidence)
                if hashlib.sha256(raw_evidence).hexdigest() != evidence['sha256']:
                    raise HTTPException(503, 'PLAN dependency integrity mismatch')
                dependency_cache[eid] = {'id':eid, 'record_hash':digest(evidence), 'review_state':evidence['state']}
            deps.append(dependency_cache[eid])
        if size + dependency_bytes > MAX_CONTEXT_BYTES:
            raise HTTPException(413, 'PLAN content and dependencies exceed 1MiB scope')
        entries.append(dict(**ref, sha256=content_hash, size_bytes=len(raw), source_version=value.get('version'),
                            record_hash=digest(value), created_at=value['created_at'], dependencies=deps,
                            source_url=value.get('source_url'), logical_path=value.get('logical_path'),
                            review_state=value.get('state'), content_integrity='VERIFIED', truth_status='UNKNOWN'))
        texts.append({'type':ref['kind'], 'id':ref['id'], 'text':text, 'untrusted':True,
                      'sha256':content_hash, 'start_char':0, 'end_char':len(text), 'declared_relationship':ref['relationship']})
    stop = latest(db, 'audit', 'event', 'control.stop_changed')
    value = dict(plan_id=plan['id'], project_id=plan['project_id'], task_id=plan['task_id'], title=metadata['title'], context_type=metadata['context_type'], task_hash=digest(task), resources=entries, total_bytes=size, dependency_bytes=dependency_bytes, stop_revision=stop['id'] if stop else 'initial')
    return value, digest(value), texts


def append_version(db, plan, body, who, storage, previous=None):
    guard(db)
    resources = [r.model_dump() for r in body.resources]
    value, hash_value, _ = manifest(db, plan, resources, storage, body.model_dump())
    version = put(db, 'plan_version', dict(id=identity(), plan_id=plan['id'], version=(previous['version'] + 1) if previous else 1,
                  title=body.title, context_type=body.context_type, resources=resources, created_at=now(), manifest=value, manifest_hash=hash_value))
    audit(db, who, 'plan.version_created', version['id'], {'plan_id':plan['id'], 'manifest_hash':hash_value})
    return version


def create_plan(db, body, who, storage):
    guard(db)
    task = get(db, 'task', body.task_id)
    if task_plan(db, body.task_id):
        raise HTTPException(409, 'Task already has PLAN; append a version')
    plan = put(db, 'plan', dict(id=identity(), task_id=body.task_id, project_id=task['project_id'], created_at=now()))
    append_version(db, plan, body, who, storage)
    audit(db, who, 'plan.created', plan['id'], {'task_id':body.task_id})
    return plan


def revise_plan(db, plan_id, body, who, storage):
    plan = get(db, 'plan', plan_id)
    previous = latest(db, 'plan_version', 'plan_id', plan_id)
    if previous['id'] != body.expected_version_id:
        raise HTTPException(409, 'PLAN changed; read latest version first')
    return append_version(db, plan, body, who, storage, previous)


def create_lock(db, plan_id, body, who, storage):
    guard(db)
    plan = get(db, 'plan', plan_id)
    version = latest(db, 'plan_version', 'plan_id', plan_id)
    if version['id'] != body.version_id:
        raise HTTPException(409, 'Only latest PLAN version can be locked')
    _, current, _ = manifest(db, plan, version['resources'], storage, version)
    if current != version['manifest_hash'] or current != body.manifest_hash:
        raise HTTPException(409, 'PLAN sources changed; append reviewed version before locking')
    lock = put(db, 'plan_lock', dict(id=identity(), plan_id=plan_id, version_id=version['id'], manifest_hash=current,
                                  created_at=now(), actor=who, reason_hash=digest(body.reason)))
    audit(db, who, 'plan.context_locked', lock['id'], {'plan_id':plan_id, 'version_id':version['id'], 'manifest_hash':current})
    return lock


def revoke_lock(db, lock_id, body, who):
    lock = get(db, 'plan_lock', lock_id)
    if latest(db, 'plan_revocation', 'lock_id', lock_id):
        raise HTTPException(409, 'PLAN lock already revoked')
    record = put(db, 'plan_revocation', dict(id=identity(), lock_id=lock_id, plan_id=lock['plan_id'], created_at=now(), reason_hash=digest(body.reason)))
    # Revocation remains allowed during emergency stop.
    audit(db, who, 'plan.context_revoked', lock_id, {'revocation_id':record['id']})
    return record


def status(db, plan, storage):
    version = latest(db, 'plan_version', 'plan_id', plan['id'])
    if version is None:
        # Defensive: a PLAN without any recorded version can never bind context.
        return dict(plan_id=plan['id'], version_id=None, lock_id=None, manifest_hash=None,
                    allowed_for_action=False, state='BLOCKED', reason='NO_PLAN_VERSION_RECORDED')
    lock = latest(db, 'plan_lock', 'plan_id', plan['id'])
    base = dict(plan_id=plan['id'], version_id=version['id'], lock_id=lock['id'] if lock else None,
                manifest_hash=version['manifest_hash'], allowed_for_action=False)
    if stopped(db)['active']:
        return dict(**base, state='BLOCKED', reason='EMERGENCY_STOP')
    if not lock:
        return dict(**base, state='UNLOCKED', reason='REVIEWER_CONTEXT_LOCK_REQUIRED')
    if lock['version_id'] != version['id']:
        return dict(**base, state='SUPERSEDED', reason='NEW_PLAN_VERSION')
    if latest(db, 'plan_revocation', 'lock_id', lock['id']):
        return dict(**base, state='REVOKED', reason='REVIEWER_REVOKED_CONTEXT')
    try:
        _, current, _ = manifest(db, plan, version['resources'], storage, version)
    except (HTTPException, OSError, UnicodeError):
        return dict(**base, state='BLOCKED', reason='CONTEXT_SOURCE_UNAVAILABLE_OR_INVALID')
    if current != lock['manifest_hash'] or current != version['manifest_hash']:
        return dict(**base, state='STALE', reason='SOURCE_OR_STOP_REVISION_CHANGED')
    return dict(**base, state='CURRENT', reason='HASH_BOUND_CONTEXT_ONLY_NOT_TRUTH_OR_PERMISSION')


def task_gate(db, task_id, storage=None):
    plan = task_plan(db, task_id)
    return status(db, plan, storage) if plan else None


def locked_context(db, task_id, lock_id, storage):
    plan = task_plan(db, task_id)
    if not plan:
        if lock_id:
            raise HTTPException(409, 'No PLAN for requested task')
        return None
    gate = status(db, plan, storage)
    if not lock_id or gate['state'] != 'CURRENT' or gate['lock_id'] != lock_id:
        raise HTTPException(409, 'Current task PLAN lock required; no omitted/stale/foreign lock')
    version = get(db, 'plan_version', gate['version_id'])
    _, _, texts = manifest(db, plan, version['resources'], storage, version)
    return gate, texts
