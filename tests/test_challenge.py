"""Synthetic inputs, real challenge rules/HTTP/SQLite; separate process in smoke."""
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import threading
import urllib.error
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.challenge_rules import analyze, equal_value
from app.challenge_worker import run_once, main, NoRedirects
from conftest import seed, task, result_body, challenged_result, process_job_api, observation


def worker_headers(settings):
    return {'Authorization': 'Bearer ' + settings.challenge_token}


def setup_result(client, reviewer, **changes):
    project, evidence = seed(client, reviewer)
    key = task(client, project, evidence)
    body = {**result_body(key, evidence['id']), **changes}
    response = client.post('/api/results', json=body)
    assert response.status_code == 201, response.text
    return project, evidence, key, response.json()


def source(client, reviewer, project, observations, review=True):
    response = client.post('/api/evidence', json={
        'project_id': project['id'], 'claim': 'Explicit synthetic challenge input',
        'source_url': 'https://example.net/test', 'observed_at': '2026-01-01T00:00:00Z',
        'source_type': 'manual', 'provider': 'pytest additional fixture', 'extraction_method': 'manual',
        'content': 'Additional synthetic source', 'confidence': 0.9, 'observations': observations})
    assert response.status_code == 201, response.text
    e = response.json()
    if review:
        client.post(f"/api/evidence/{e['id']}/review", headers=reviewer, json={'state': 'verified', 'reason': 'Test review'})
    return e


def new_challenge(client, result):
    response = client.post(f"/api/results/{result['id']}/challenge", json={'reason': 'Explicit countercheck'})
    assert response.status_code == 201, response.text
    return response.json()


def test_mandatory_challenge_and_explicit_adoption(client, reviewer, settings):
    """CH-001: pending blocks; a real report enables bounded triage; reviewer adoption stores only checked-scope references, not unchecked primary text."""
    p, e, key, result = setup_result(client, reviewer, summary='UNVALIDATED broad conclusion; must not become memory fact')
    assert client.get('/api/results').json() == [result]
    decision = client.post(f'/api/tasks/{key}/triage').json()
    assert decision['validation_status'] == 'BLOCK' and decision['state'] == 'blocked'
    assert client.post(f"/api/results/{result['id']}/adopt", headers=reviewer, json={'reason': 'Too early'}).status_code == 409
    report = process_job_api(client)
    assert report['analysis']['verdict'] == 'PASS'
    assert {f['check'] for f in report['analysis']['findings']} == {'evidence', 'consistency', 'alternative', 'causality', 'action'}
    why = client.get(f"/api/results/{result['id']}/why").json()
    assert why['current'] and why['decision']['validation_status'] == 'ACCEPT'
    assert why['report']['analysis']['alternatives'][0]['subject'] == 'synthetic-alternative'
    assert client.post(f"/api/results/{result['id']}/adopt", json={'reason': 'Not reviewer'}).status_code == 403
    memory = client.post(f"/api/results/{result['id']}/adopt", headers=reviewer, json={'reason': 'Explicit bounded adoption'})
    assert memory.status_code == 201, memory.text
    assert memory.json()['decision_challenge_id'] == report['id']
    assert 'UNVALIDATED broad conclusion' not in memory.json()['content']
    assert client.post(f"/api/results/{result['id']}/adopt", headers=reviewer, json={'reason': 'Duplicate'}).status_code == 409
    assert client.post('/api/memory', json={'project_id': p['id'], 'category': 'decision', 'content': 'Bypass'}).status_code == 409


def test_worker_credentials_separate_and_forgery_rejected(client, reviewer, settings):
    """CH-002: operator/reviewer cannot act as worker; worker cannot write primary evidence; forged PASS and replay are rejected."""
    p, e, key, result = setup_result(client, reviewer, unknowns=['Unresolved fixture uncertainty'])
    assert client.post('/api/challenge/jobs/claim').status_code == 403
    assert client.post('/api/challenge/jobs/claim', headers=reviewer).status_code == 403
    headers = worker_headers(settings)
    assert client.get('/api/projects', headers=headers).status_code == 401
    assert client.post('/api/results', headers=reviewer, json=result_body(key, e['id'])).status_code == 403
    job = client.post('/api/challenge/jobs/claim', headers=headers).json()
    analysis = analyze(job['snapshot']).model_dump()
    forged = {**analysis, 'verdict': 'PASS'}
    url = f"/api/challenge/jobs/{job['job_id']}/complete"
    body = {'lease': job['lease'], 'fingerprint': job['fingerprint'], 'analysis': forged}
    assert client.post(url, headers=headers, json=body).status_code == 422
    body['analysis'] = analysis
    assert client.post(url, headers=headers, json={**body, 'lease': 'wrong'}).status_code == 409
    assert client.post(url, headers=headers, json=body).status_code == 201
    assert client.post(url, headers=headers, json=body).status_code == 409
    decision = client.post(f'/api/tasks/{key}/triage').json()
    assert decision['validation_status'] == 'CONDITIONAL' and decision['state'] == 'blocked'


def test_unconfigured_worker_has_no_fallback(settings, reviewer):
    """CH-003: missing service credential leaves pending result blocked; no in-process auto-report or approval path."""
    with TestClient(create_app(replace(settings, challenge_token=''))) as client:
        client.headers['Authorization'] = 'Bearer ' + settings.operator_token
        p, e, key, result = setup_result(client, reviewer)
        assert client.post('/api/challenge/jobs/claim').status_code == 503
        assert client.post(f"/api/results/{result['id']}/challenge", json={'reason': 'No worker'}).status_code == 503
        assert client.post(f'/api/tasks/{key}/triage').json()['state'] == 'blocked'
        assert client.get(f"/api/results/{result['id']}/why").json()['report'] is None


def test_contradiction_not_selected_by_primary_stops_line(client, reviewer):
    """CH-004: independently scanned project evidence contradicting an identical variant/property blocks despite not being selected by primary."""
    p, e, key, result = setup_result(client, reviewer)
    other = source(client, reviewer, p, [observation(value='binary')])
    new_challenge(client, result)
    report = process_job_api(client)
    assert report['analysis']['verdict'] == 'BLOCK'
    conflict = next(f for f in report['analysis']['findings'] if f['code'] == 'CONTRADICTION')
    assert other['id'] in conflict['evidence_ids']
    assert client.post(f"/api/results/{result['id']}/adopt", headers=reviewer, json={'reason': 'Cannot dismiss critical gap'}).status_code == 409


@pytest.mark.parametrize('change,code', [
    ({'variant': 'other-variant'}, 'IDENTITY_OR_SUPPORT_UNKNOWN'),
    ({'revision': 'other-revision'}, 'IDENTITY_OR_SUPPORT_UNKNOWN'),
    ({'unit': 'other-unit'}, 'INCOMPARABLE'),
    ({'conditions': 'other-conditions'}, 'INCOMPARABLE'),
    ({'requires_measurement': True}, 'MEASUREMENT_MISSING'),
    ({'causal': True}, 'CAUSALITY_UNPROVEN')])
def test_specific_unknowns_cannot_pass(client, reviewer, change, code):
    """CH-005: identity, unit/condition, measurement and causality gaps yield concrete CONDITIONAL findings, not rhetorical confirmation."""
    p, e = seed(client, reviewer)
    key = task(client, p, e)
    body = result_body(key, e['id'])
    body['claims'][0].update(change)
    assert client.post('/api/results', json=body).status_code == 201
    report = process_job_api(client)
    assert report['analysis']['verdict'] == 'CONDITIONAL'
    assert any(f['code'] == code and f['next_validation'] for f in report['analysis']['findings'])


def test_no_alternative_is_not_invented(client, reviewer):
    """CH-006: absent alternative remains a concrete gap; worker emits no fabricated device or counter-source."""
    p = client.post('/api/projects', json={'name': 'Alternative gap fixture'}).json()
    e = source(client, reviewer, p, [observation()])
    key = task(client, p, e)
    client.post('/api/results', json=result_body(key, e['id']))
    report = process_job_api(client)
    assert report['analysis']['alternatives'] == []
    assert any(f['code'] == 'NO_ALTERNATIVE' for f in report['analysis']['findings'])
    assert report['analysis']['verdict'] == 'CONDITIONAL'


def test_stale_evidence_invalidates_reports_approvals_and_adoption(client, reviewer):
    """CH-007: new evidence invalidates a prior approval; a new challenge and human approval are both required before adoption."""
    p, e = seed(client, reviewer)
    key = task(client, p, e, 'write')
    result = challenged_result(client, key, e['id'])
    assert client.post(f'/api/tasks/{key}/approve', headers=reviewer, json={'reason': 'Before new evidence'}).status_code == 201
    source(client, reviewer, p, [observation('additional-fixture')])
    why = client.get(f"/api/results/{result['id']}/why").json()
    assert not why['current'] and why['decision']['state'] == 'blocked'
    assert client.post(f"/api/results/{result['id']}/adopt", headers=reviewer, json={'reason': 'Stale'}).status_code == 409
    new_challenge(client, result)
    process_job_api(client)
    assert client.post(f'/api/tasks/{key}/triage').json()['state'] == 'approval_required'
    assert client.post(f'/api/tasks/{key}/approve', headers=reviewer, json={'reason': 'After new challenge'}).status_code == 201
    assert client.post(f"/api/results/{result['id']}/adopt", headers=reviewer, json={'reason': 'Approved current scope'}).status_code == 201


def test_new_result_and_rechallenge_invalidate_old_pass(client, reviewer):
    """CH-008: newest result and newest challenge must pass; old package/adoption and old job cannot bypass pending work."""
    p, e, key, result = setup_result(client, reviewer)
    process_job_api(client)
    new_challenge(client, result)
    assert client.post(f'/api/tasks/{key}/triage').json()['state'] == 'blocked'
    second = client.post('/api/results', json={**result_body(key, e['id']), 'unknowns': ['new gap']}).json()
    assert client.post(f"/api/results/{result['id']}/challenge", json={'reason': 'Old result'}).status_code == 409
    assert client.post(f"/api/results/{result['id']}/adopt", headers=reviewer, json={'reason': 'Old pass'}).status_code == 409
    report = process_job_api(client)
    assert report['result_id'] == second['id'] and report['analysis']['verdict'] == 'CONDITIONAL'


def test_lease_expiry_reclaim_and_snapshot_race(client, reviewer, settings):
    """CH-009: expired leases are reclaimable, old leases rejected, evidence changes during worker run prevent commit."""
    p, e, key, result = setup_result(client, reviewer)
    headers = worker_headers(settings)
    old = client.post('/api/challenge/jobs/claim', headers=headers).json()
    assert client.post('/api/challenge/jobs/claim', headers=headers).json() is None
    with sqlite3.connect(settings.db_path) as db:
        value = json.loads(db.execute('SELECT body FROM records WHERE id=?', (old['job_id'],)).fetchone()[0])
        value['lease_expires_at'] = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
        db.execute('UPDATE records SET body=? WHERE id=?', (json.dumps(value), old['job_id']))
    body = {'lease': old['lease'], 'fingerprint': old['fingerprint'], 'analysis': analyze(old['snapshot']).model_dump()}
    url = f"/api/challenge/jobs/{old['job_id']}/complete"
    assert client.post(url, headers=headers, json=body).status_code == 409
    new = client.post('/api/challenge/jobs/claim', headers=headers).json()
    assert new['job_id'] == old['job_id'] and new['lease'] != old['lease']
    assert client.post(url, headers=headers, json=body).status_code == 409
    source(client, reviewer, p, [])
    assert client.post(url, headers=headers, json={**body, 'lease': new['lease']}).status_code == 409


def test_challenge_stop_and_audit_atomicity(client, reviewer, settings):
    """CH-010: stop blocks schedule/claims/complete; report/audit failure rolls back completion instead of permitting acceptance."""
    p, e, key, result = setup_result(client, reviewer)
    headers = worker_headers(settings)
    job = client.post('/api/challenge/jobs/claim', headers=headers).json()
    body = {'lease': job['lease'], 'fingerprint': job['fingerprint'], 'analysis': analyze(job['snapshot']).model_dump()}
    client.post('/api/control/stop', headers=reviewer, json={'active': True, 'reason': 'Challenge stop'})
    assert client.post('/api/challenge/jobs/claim', headers=headers).status_code == 409
    assert client.post(f"/api/challenge/jobs/{job['job_id']}/complete", headers=headers, json=body).status_code == 409
    assert client.post('/api/results', json=result_body(key, e['id'])).status_code == 409
    client.post('/api/control/stop', headers=reviewer, json={'active': False, 'reason': 'Reset'})
    new_challenge(client, result)
    job = client.post('/api/challenge/jobs/claim', headers=headers).json()
    with sqlite3.connect(settings.db_path) as db:
        db.execute("CREATE TRIGGER fail_challenge BEFORE INSERT ON records WHEN NEW.kind='audit' AND json_extract(NEW.body,'$.event')='challenge.completed' BEGIN SELECT RAISE(ABORT, 'challenge audit fault'); END")
    with pytest.raises(sqlite3.IntegrityError):
        client.post(f"/api/challenge/jobs/{job['job_id']}/complete", headers=headers,
                    json={'lease': job['lease'], 'fingerprint': job['fingerprint'], 'analysis': analyze(job['snapshot']).model_dump()})
    assert client.get(f"/api/results/{result['id']}/why").json()['report'] is None


def test_claim_references_and_service_config(client, reviewer, settings):
    """CH-011: duplicate/foreign references and shared/short worker credentials cannot establish a challenge boundary."""
    p, e = seed(client, reviewer)
    other = client.post('/api/projects', json={'name': 'Other'}).json()
    key = task(client, p, e)
    foreign = source(client, reviewer, other, [])
    body = result_body(key, foreign['id'])
    assert client.post('/api/results', json=body).status_code == 422
    body = result_body(key, e['id'])
    body['claims'][0]['evidence_ids'] *= 2
    assert client.post('/api/results', json=body).status_code == 422
    with pytest.raises(ValueError, match='Challenge'):
        replace(settings, challenge_token=settings.operator_token)
    with pytest.raises(ValueError, match='Challenge'):
        replace(settings, challenge_token='short')


def test_rule_boundaries_and_scope(client, reviewer, settings):
    """CH-012: truncated scope, missing/corrupt/rejected sources and declared unsupported actions/calculations never receive a fake PASS."""
    p, e, key, result = setup_result(client, reviewer)
    job = client.post('/api/challenge/jobs/claim', headers=worker_headers(settings)).json()
    snap = job['snapshot']
    assert analyze({**snap, 'truncated': True}).verdict == 'BLOCK'
    assert analyze({**snap, 'evidence': []}).verdict == 'BLOCK'
    changed = json.loads(json.dumps(snap))
    changed['evidence'][0]['content'] = 'corrupt original'
    assert analyze(changed).verdict == 'BLOCK'
    changed['evidence'][0]['content'] = 'Synthetic fixture'
    changed['evidence'][0]['state'] = 'rejected'
    assert analyze(changed).verdict == 'BLOCK'
    for kind, verdict in [('action', 'BLOCK'), ('calculation', 'CONDITIONAL')]:
        assert analyze({**snap, 'result': {**snap['result'], 'kind': kind}}).verdict == verdict
    assert equal_value('18', '18.0')
    assert not equal_value('12–18', '18')
    assert not equal_value('NaN', '0')


def test_worker_transport_constraints(settings):
    """CH-013: worker rejects credential-bearing/remote-plaintext origins, missing credentials and redirects instead of faking a result."""
    for url in ['file:///etc/passwd', 'http://example.com', 'https://user:pass@example.com', 'https://example.com/?token=abc']:
        with pytest.raises(ValueError):
            run_once(url, settings.challenge_token)
    with pytest.raises(ValueError):
        run_once('http://127.0.0.1:8000', '')
    assert NoRedirects().redirect_request(None, None, 302, None, None, 'https://elsewhere.invalid') is None


def test_unreviewed_sources_alternatives_and_unknown_sentinels(client, reviewer, settings):
    """CH-014: unknown values are not promoted by matching strings; alternative rationale alone is not evidence and unreviewed sources remain conditional."""
    p, e, key, result = setup_result(client, reviewer)
    job = client.post('/api/challenge/jobs/claim', headers=worker_headers(settings)).json()
    snap = job['snapshot']
    unreviewed = json.loads(json.dumps(snap))
    unreviewed['evidence'][0]['state'] = 'unverified'
    assert any(f.code == 'UNVALIDATED_SOURCE' for f in analyze(unreviewed).findings)
    unknown = json.loads(json.dumps(snap))
    unknown['result']['claims'][0]['revision'] = 'UNKNOWN'
    unknown['result']['falsification_test'] = '?'
    report = analyze(unknown)
    assert report.verdict == 'CONDITIONAL'
    assert {'UNKNOWN_PARAMETER', 'NO_FALSIFICATION_TEST'} <= {f.code for f in report.findings}
    for subject, verdict in [('synthetic-alternative', 'PASS'), ('nonexistent-profile', 'CONDITIONAL')]:
        alt = {**snap, 'result': {**snap['result'], 'alternatives': [{'subject': subject, 'rationale': 'Submitted exclusion rationale', 'evidence_ids': [e['id']]}]}}
        assert analyze(alt).verdict == verdict
    assert analyze({**snap, 'task': {**snap['task'], 'preconditions_met': False}}).verdict == 'BLOCK'


def test_adopted_memory_retrieval_revalidates_challenge(client, reviewer):
    """CH-015: retrieved decision-memory carries challenge provenance and becomes BLOCK after evidence changes; no stale acceptance in RAG."""
    p, e, key, result = setup_result(client, reviewer)
    process_job_api(client)
    response = client.post(f"/api/results/{result['id']}/adopt", headers=reviewer, json={'reason': 'Reviewed structured scope'})
    assert response.status_code == 201
    body = {'project_id': p['id'], 'query': 'Structured'}
    hit = client.post('/api/context/query', json=body).json()[0]
    assert hit['decision_result_id'] == result['id'] and hit['decision_status'] == 'ACCEPT'
    assert hit['allowed_for_action'] is False
    assert client.get(f"/api/evidence/{e['id']}").json()['sha256'] == e['sha256']
    source(client, reviewer, p, [])
    assert client.post('/api/context/query', json=body).json()[0]['decision_status'] == 'BLOCK'


def test_adoption_audit_failure_rolls_back_memory(client, reviewer, settings):
    """CH-016: accepted challenge does not bypass atomic audit on adoption; audit failure creates no decision-memory or index entry."""
    p, e, key, result = setup_result(client, reviewer)
    process_job_api(client)
    with sqlite3.connect(settings.db_path) as db:
        db.execute("CREATE TRIGGER fail_adopt BEFORE INSERT ON records WHEN NEW.kind='audit' AND json_extract(NEW.body,'$.event')='result.adopted' BEGIN SELECT RAISE(ABORT, 'adoption audit fault'); END")
    with pytest.raises(sqlite3.IntegrityError):
        client.post(f"/api/results/{result['id']}/adopt", headers=reviewer, json={'reason': 'Atomic test'})
    assert client.get('/api/memory').json() == []
    assert client.post('/api/context/query', json={'project_id': p['id'], 'query': 'Structured'}).json() == []


def test_scope_limits_block_instead_of_partial_validation(client, reviewer, monkeypatch):
    """CH-017: bounded snapshot and finding limits stop the line instead of silently validating a truncated context."""
    import app.challenge_service as service
    import app.challenge_rules as rules
    p, e, key, result = setup_result(client, reviewer)
    monkeypatch.setattr(service, 'MAX_SNAPSHOT_EVIDENCE_BYTES', 1)
    new_challenge(client, result)
    report = process_job_api(client)
    assert report['analysis']['verdict'] == 'BLOCK'
    assert any(f['code'] == 'SCOPE_LIMIT' for f in report['analysis']['findings'])
    monkeypatch.setattr(rules, 'MAX_FINDINGS', 1)
    limited = rules.analyze({'task': {'action': 'read', 'evidence_ids': [], 'preconditions_met': True},
                             'result': {'claims': [], 'alternatives': [], 'unknowns': [], 'kind': 'plan', 'falsification_test': 'inspect original'}, 'evidence': []})
    assert limited.verdict == 'BLOCK'
    assert limited.findings[-1].code == 'FINDING_LIMIT'


WORKER_TOKEN = 'isolated-worker-transport-credential-0000'
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def worker_peer():
    """Real loopback HTTP peer for the two worker endpoints; payloads are explicitly synthetic, never a challenge verdict source."""
    seen, behavior = [], {'case': 'job', 'job': None}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # Isolated peer logs only; never echo the service credential.

        def do_POST(self):
            length = int(self.headers.get('Content-Length') or 0)
            body = json.loads(self.rfile.read(length)) if length else None
            seen.append((self.path, self.headers.get('Authorization'), body))
            if behavior['case'] == 'redirect':
                self.send_response(302)
                self.send_header('Location', 'http://127.0.0.1:9/never-follow')
                self.send_header('Content-Length', '0')
                self.end_headers()
                return
            payload = {'detail': 'isolated peer failure'} if behavior['case'] == 'error' else (
                behavior['job'] if self.path == '/api/challenge/jobs/claim'
                else {'id': 'synthetic-report-id', 'analysis': {'verdict': 'PASS'}})
            raw = json.dumps(payload).encode()
            self.send_response(500 if behavior['case'] == 'error' else 200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server, seen, behavior
    server.shutdown()
    server.server_close()
    thread.join(timeout=3)


def test_worker_transport_claims_and_completes_real_job(client, reviewer, settings, worker_peer):
    """CH-018: the separate worker code path claims a real API job and submits the deterministic report over actual loopback HTTP with its own credential, never a platform token."""
    server, seen, behavior = worker_peer
    _, evidence, key, result = setup_result(client, reviewer)
    job = client.post('/api/challenge/jobs/claim', headers=worker_headers(settings)).json()
    behavior['job'] = job
    outcome = run_once(f'http://127.0.0.1:{server.server_port}', WORKER_TOKEN)
    assert outcome == {'job_id': job['job_id'], 'report_id': 'synthetic-report-id', 'verdict': 'PASS'}
    assert [entry[0] for entry in seen] == ['/api/challenge/jobs/claim', f"/api/challenge/jobs/{job['job_id']}/complete"]
    assert all(entry[1] == 'Bearer ' + WORKER_TOKEN for entry in seen)
    assert settings.operator_token not in json.dumps(seen) and settings.reviewer_token not in json.dumps(seen)
    completion = seen[1][2]
    assert completion['lease'] == job['lease'] and completion['fingerprint'] == job['fingerprint']
    assert completion['analysis'] == analyze(job['snapshot']).model_dump()
    behavior['job'] = None
    assert run_once(f'http://127.0.0.1:{server.server_port}', WORKER_TOKEN) is None
    assert len(seen) == 3 and seen[2][0] == '/api/challenge/jobs/claim'


def test_worker_transport_refuses_redirect_and_server_error(worker_peer):
    """CH-019: a redirect or failing server yields a transport error instead of a fabricated report, and the service credential is never forwarded to another origin."""
    server, seen, behavior = worker_peer
    url = f'http://127.0.0.1:{server.server_port}'
    behavior['case'] = 'redirect'
    with pytest.raises(urllib.error.HTTPError):
        run_once(url, WORKER_TOKEN)
    assert len(seen) == 1 and seen[0][0] == '/api/challenge/jobs/claim'
    behavior['case'] = 'error'
    with pytest.raises(urllib.error.HTTPError):
        run_once(url, WORKER_TOKEN)
    assert len(seen) == 2 and all(entry[0].startswith('/api/challenge/') for entry in seen)


def test_worker_cli_exit_codes_and_module_entry(client, reviewer, settings, worker_peer, monkeypatch, capsys):
    """CH-020: the documented CLI exits 0 after a real completed job and 1 on transport failure, in process and as an actual separate OS process, reporting BLOCKED without inventing a verdict."""
    server, seen, behavior = worker_peer
    url = f'http://127.0.0.1:{server.server_port}'
    _, evidence, key, result = setup_result(client, reviewer)
    behavior['job'] = client.post('/api/challenge/jobs/claim', headers=worker_headers(settings)).json()
    monkeypatch.setenv('ATZE_CHALLENGE_TOKEN', WORKER_TOKEN)
    monkeypatch.setattr(sys, 'argv', ['app.challenge_worker', '--url', url, '--once'])
    assert main() == 0
    assert json.loads(capsys.readouterr().out)['report_id'] == 'synthetic-report-id'
    behavior['case'] = 'error'
    monkeypatch.setattr(sys, 'argv', ['app.challenge_worker', '--url', url, '--once'])
    assert main() == 1
    assert json.loads(capsys.readouterr().out)['status'] == 'BLOCKED'
    environment = {**os.environ, 'ATZE_CHALLENGE_TOKEN': WORKER_TOKEN, 'PYTHONPATH': str(ROOT)}
    failed = subprocess.run([sys.executable, '-m', 'app.challenge_worker', '--url', url, '--once'],
                            env=environment, cwd=ROOT, capture_output=True, text=True, timeout=60)
    assert failed.returncode == 1 and json.loads(failed.stdout)['status'] == 'BLOCKED'
    new_challenge(client, result)
    behavior['case'] = 'job'
    behavior['job'] = client.post('/api/challenge/jobs/claim', headers=worker_headers(settings)).json()
    succeeded = subprocess.run([sys.executable, '-m', 'app.challenge_worker', '--url', url, '--once'],
                               env=environment, cwd=ROOT, capture_output=True, text=True, timeout=60)
    assert succeeded.returncode == 0
    assert json.loads(succeeded.stdout)['verdict'] == 'PASS' and WORKER_TOKEN not in succeeded.stdout


def test_worker_continuous_poll_until_interrupted(worker_peer, monkeypatch, capsys):
    """CH-021: without --once the worker keeps polling after a failure and invents no verdict in between; the documented interrupt point is the wait between attempts."""
    import app.challenge_worker as worker
    server, seen, behavior = worker_peer
    behavior['case'] = 'error'
    monkeypatch.setenv('ATZE_CHALLENGE_TOKEN', WORKER_TOKEN)
    monkeypatch.setattr(sys, 'argv', ['app.challenge_worker', '--url', f'http://127.0.0.1:{server.server_port}'])

    class Interrupted(Exception):
        pass

    waits = []

    def interrupt(seconds):
        waits.append(seconds)
        raise Interrupted('isolated test interrupt of the poll loop')

    monkeypatch.setattr(worker.time, 'sleep', interrupt)
    with pytest.raises(Interrupted):
        worker.main()
    assert waits == [2]
    assert json.loads(capsys.readouterr().out) == {'status': 'BLOCKED', 'error_type': 'HTTPError'}
    assert len(seen) == 1 and seen[0][0] == '/api/challenge/jobs/claim'
