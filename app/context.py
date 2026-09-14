"""Local context services. No MCP protocol, remote execution, or truth inference."""
import hashlib
import json
import re
from fastapi import HTTPException
from app.store import get, put, audit, identity, now


def update(db, value):
    db.execute('UPDATE records SET body=? WHERE id=?', (json.dumps(value), value['id']))


def references(db, project_id, evidence_ids):
    get(db, 'project', project_id)
    if len(evidence_ids) != len(set(evidence_ids)):
        raise HTTPException(422, 'Duplicate evidence references')
    evidence = [get(db, 'evidence', key) for key in evidence_ids]
    if any(e['project_id'] != project_id for e in evidence):
        raise HTTPException(422, 'Evidence belongs to another project')
    return evidence


def index_text(db, project_id, source_id, text):
    # Character offsets in original text (not bytes), bounded chunks with overlap.
    db.execute('DELETE FROM context_fts WHERE source_id=?', (source_id,))
    for start in range(0, len(text), 896):
        end = min(start + 1024, len(text))
        db.execute('INSERT INTO context_fts VALUES(?,?,?,?,?)', (project_id, source_id, start, end, text[start:end]))
        if end == len(text):
            break


def create_memory(db, body, who):
    evidence = references(db, body.project_id, body.evidence_ids)
    if body.category in {'fact', 'decision'}:
        raise HTTPException(409, 'Authoritative memory requires result/challenge/triage adoption; record an inference instead')
    if body.task_id and get(db, 'task', body.task_id)['project_id'] != body.project_id:
        raise HTTPException(422, 'Task belongs to another project')
    value = dict(**body.model_dump(), id=identity(), created_at=now(), state='recorded',
                 sha256=hashlib.sha256(body.content.encode()).hexdigest())
    put(db, 'memory', value)
    index_text(db, body.project_id, value['id'], body.content)
    audit(db, who, 'memory.created', value['id'], {'category': body.category, 'sha256': value['sha256']})
    return value


def retrieve(db, body, storage=None):
    get(db, 'project', body.project_id)
    terms = re.findall(r'\w+', body.query, re.UNICODE)[:16]
    if not terms:
        raise HTTPException(422, 'Query requires searchable words')
    expression = ' AND '.join('"' + term + '"' for term in terms)
    rows = db.execute('SELECT source_id,start_char,end_char,text FROM context_fts WHERE context_fts MATCH ? AND project_id=? ORDER BY bm25(context_fts),source_id,CAST(start_char AS INTEGER) LIMIT ?',
                      (expression, body.project_id, body.limit)).fetchall()
    hits = []
    for key, start, end, text in rows:
        row = db.execute('SELECT kind,body FROM records WHERE id=?', (key,)).fetchone()
        if row is None:
            raise HTTPException(503, 'Context index references missing source')
        kind, value = row[0], json.loads(row[1])
        evidence = [{'id': e, 'state': get(db, 'evidence', e)['state']} for e in value['evidence_ids']]
        state = 'rejected' if any(e['state'] == 'rejected' for e in evidence) else 'verified' if evidence and all(e['state'] == 'verified' for e in evidence) else 'unverified'
        decision_status = 'BLOCK' if value.get('category') in {'fact', 'decision'} else None
        if value.get('decision_result_id'):
            from app.challenge_service import decide_task
            current = decide_task(db, value['task_id'], storage)
            if current.challenge_id == value['decision_challenge_id'] and current.fingerprint == value['decision_fingerprint']:
                decision_status = current.validation_status
        hits.append(dict(decision_result_id=value.get('decision_result_id'), decision_challenge_id=value.get('decision_challenge_id'), decision_status=decision_status, source_id=key, source_type=kind, category=value.get('category', 'archive'),
                         location=value.get('tier', 'core'), logical_path=value.get('logical_path', f"/project/{value['project_id']}/memory/{key}"),
                         timestamp=value['created_at'], sha256=value['sha256'], start_char=int(start), end_char=int(end),
                         text=text, evidence=evidence, evidence_state=state, commit_sha=value.get('commit_sha'),
                         version=1, allowed_for_action=False))
    return hits
