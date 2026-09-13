"""Explicit synthetic INPUTS against a REAL disposable HTTP/SQLite/filesystem instance.

No target URL, reused storage or caller credentials accepted. No simulated provider.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
from tempfile import TemporaryDirectory
import time
import httpx

ROOT = Path(__file__).resolve().parents[1]


def _require(condition, message):
    if not condition:
        raise RuntimeError(message)


def _exercise(client, operator, reviewer, records, *, worker_url, worker_token, worker_records):
    def run_worker():
        worker_env = {k: v for k, v in os.environ.items() if not k.startswith('ATZE_')}
        worker_env['ATZE_CHALLENGE_TOKEN'] = worker_token
        completed = subprocess.run([sys.executable, '-m', 'app.challenge_worker', '--url', worker_url, '--once'],
                                   cwd=ROOT, env=worker_env, capture_output=True, text=True, timeout=30)
        record = {'kind': 'separate real challenge process', 'exit_code': completed.returncode,
                  'stdout': completed.stdout.strip()}
        worker_records.append(record)
        _require(completed.returncode == 0, 'Separate challenge worker failed; no fallback')
        _require(json.loads(completed.stdout)['verdict'] == 'PASS', 'Worker did not produce real PASS')


    def call(method, path, body=None, role='operator', expected=200):
        token = operator if role == 'operator' else reviewer
        response = client.request(method, path, json=body, headers={'Authorization': 'Bearer ' + token})
        records.append({'method': method, 'path': path, 'expected_status': expected, 'actual_status': response.status_code, 'body': response.json()})
        _require(response.status_code == expected, 'Failed: response.status_code == expected')
        return response.json()
    _require(call('GET', '/health')['mode'] == 'test', 'Refusing fixture writes outside test mode')
    _require(call('GET', '/api/runtime')['mode'] == 'test', 'Authenticated test-mode check failed')
    p = call('POST', '/api/projects', {'name': 'Synthetic HTTP smoke fixture', 'description': 'Not a real project observation'}, expected=201)
    observation = dict(subject='synthetic-object', variant='fixture-v1', revision='fixture-r1', attribute='format', value='text', unit='label', conditions='synthetic fixture only', basis='manual')
    e = call('POST', '/api/evidence', {'project_id': p['id'], 'claim': 'Synthetic smoke assertion, not externally validated', 'source_url': 'https://example.com/fixture', 'observed_at': '2026-01-01T00:00:00Z', 'source_type': 'manual', 'provider': 'smoke fixture', 'extraction_method': 'manual', 'content': 'Synthetic test content', 'confidence': 0.9, 'observations': [observation, {**observation, 'subject': 'synthetic-alternative'}]}, expected=201)
    call('POST', f"/api/evidence/{e['id']}/review", {'state': 'verified', 'reason': 'Synthetic test review'}, role='reviewer')
    for action in ['read', 'write']:
        t = call('POST', '/api/tasks', {'project_id': p['id'], 'title': 'Synthetic ' + action, 'action': action, 'evidence_ids': [e['id']], 'preconditions_met': True}, expected=201)
        _require(call('POST', f"/api/tasks/{t['id']}/triage")['state'] == 'blocked', 'Challenge must be mandatory')
        claim = {k: v for k, v in observation.items() if k != 'basis'}
        primary = call('POST', '/api/results', {'task_id': t['id'], 'kind': 'plan', 'summary': 'Compare submitted fixture properties only',
                       'primary_worker': 'explicit smoke input, not an agent runtime',
                       'claims': [{**claim, 'evidence_ids': [e['id']], 'requires_measurement': False}],
                       'alternatives': [], 'unknowns': [], 'falsification_test': 'Inspect synthetic fixture original text'}, expected=201)
        run_worker()
        why = call('GET', f"/api/results/{primary['id']}/why")
        _require(why['current'] and why['report']['analysis']['scope'] == 'submitted_structured_claims_only', 'Current challenge report required')
        d = call('POST', f"/api/tasks/{t['id']}/triage")
        _require(d['state'] == ('eligible' if action == 'read' else 'approval_required'), "Failed: d['state'] == ('eligible' if action == 'read' else 'approval_required')")
        _require(d['executed'] is False, "Failed: d['executed'] is False")
        if action == 'write':
            call('POST', f"/api/tasks/{t['id']}/approve", {'reason': 'Synthetic approval; no execution'}, role='reviewer', expected=201)
            _require(call('POST', f"/api/tasks/{t['id']}/triage")['state'] == 'approved', 'Failed: call(\'POST\', f"/api/tasks/{t[\'id\']}/triage")[\'state\'] == \'approved\'')
    archived = call('POST', '/api/archive', {'project_id': p['id'], 'relative_path': 'smoke/original.txt', 'content': '  synthetic context original\n', 'evidence_ids': [e['id']]}, expected=201)
    original = call('GET', f"/api/archive/{archived['id']}/content")
    _require(original['content'] == '  synthetic context original\n', "Failed: original['content'] == '  synthetic context original\\n'")
    memory = call('POST', '/api/memory', {'project_id': p['id'], 'category': 'inference', 'content': 'synthetic context hypothesis', 'evidence_ids': [e['id']], 'task_id': t['id']}, expected=201)
    hits = call('POST', '/api/context/query', {'project_id': p['id'], 'query': 'synthetic context'})
    _require({h['source_id'] for h in hits} == {archived['id'], memory['id']}, "Failed: {h['source_id'] for h in hits} == {archived['id'], memory['id']}")
    _require(all((not h['allowed_for_action'] for h in hits)), "Failed: all((not h['allowed_for_action'] for h in hits))")
    cache = call('POST', '/api/cache', {'task_id': t['id'], 'content': 'temporary smoke cache'}, expected=201)
    _require(call('GET', f"/api/cache/{cache['id']}/content") == 'temporary smoke cache', 'Failed: call(\'GET\', f"/api/cache/{cache[\'id\']}/content") == \'temporary smoke cache\'')
    health = call('GET', '/api/storage/health')
    _require(next((tier for tier in health['tiers'] if tier['tier'] == 'local'))['available'], "Failed: next((tier for tier in health['tiers'] if tier['tier'] == 'local'))['available']")
    call('POST', '/api/cache/cleanup', {'reason': 'Only expired fixture cache'}, role='reviewer')
    adopted = call('POST', f"/api/results/{primary['id']}/adopt", {'reason': 'Explicit bounded fixture decision'}, role='reviewer', expected=201)
    _require(adopted['decision_result_id'] == primary['id'], 'Adoption must retain challenge provenance')
    call('POST', f"/api/results/{primary['id']}/challenge", {'reason': 'Invalidate prior pass for explicit recheck'}, expected=201)
    _require(call('POST', f"/api/tasks/{t['id']}/triage")['state'] == 'blocked', 'Rechallenge must invalidate old approval')
    call('GET', '/api/audit', role='reviewer')


def run(report_path=Path('reports/smoke.json'), *, allow_fixtures=False):
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = {'timestamp': datetime.now(timezone.utc).isoformat(), 'kind': 'REAL HTTP / SYNTHETIC TEST INPUTS',
              'scope': 'disposable test instance only; no live provider/device validation',
              'status': 'NOT_RUN', 'checks': [], 'worker_processes': []}
    def save():
        report_path.write_text(json.dumps(report, indent=2))
    save()  # invalidate any previous success BEFORE startup or opt-in checks
    if not allow_fixtures:
        report.update(status='BLOCKED', error='Explicit --allow-fixtures required')
        save()
        raise RuntimeError(report['error'])
    report['status'] = 'RUNNING'
    save()
    try:
        with TemporaryDirectory(prefix='atze-test-') as tmp, socket.socket() as listener:
            root = Path(tmp)
            listener.bind(('127.0.0.1', 0))
            listener.listen()
            operator, reviewer, challenge = secrets.token_urlsafe(48), secrets.token_urlsafe(48), secrets.token_urlsafe(48)
            env = {k: v for k, v in os.environ.items() if not k.startswith('ATZE_')}
            env.update(ATZE_MODE='test', ATZE_DB_PATH=str(root / 'core.db'),
                       ATZE_STORAGE_ROOT=str(root / 'objects'), ATZE_SD_ROOT='',
                       ATZE_OPERATOR_TOKEN=operator, ATZE_REVIEWER_TOKEN=reviewer, ATZE_CHALLENGE_TOKEN=challenge)
            address = 'http://127.0.0.1:' + str(listener.getsockname()[1])
            log_path = report_path.with_suffix('.server.log')
            with log_path.open('w') as log:
                server = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'app.main:create_app', '--factory',
                                           '--fd', str(listener.fileno())], cwd=ROOT, env=env,
                                          pass_fds=(listener.fileno(),), stdout=log, stderr=log)
                try:
                    with httpx.Client(base_url=address, timeout=10, trust_env=False) as client:
                        for attempt in range(100):
                            if server.poll() is not None:
                                raise RuntimeError('Disposable server exited before readiness; inspect server log')
                            try:
                                response = client.get('/health', timeout=0.5)
                                if response.status_code == 200:
                                    break
                            except httpx.HTTPError:
                                pass
                            time.sleep(0.05)
                        else:
                            raise RuntimeError('Disposable server did not become ready')
                        _exercise(client, operator, reviewer, report['checks'], worker_url=address, worker_token=challenge, worker_records=report['worker_processes'])
                    report['status'] = 'PASS'
                finally:
                    server.terminate()
                    try:
                        server.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        server.kill()
                        server.wait(timeout=5)
        # Temp data is removed before a successful report is finalized.
    except BaseException as error:
        report.update(status='FAIL', error=f'{type(error).__name__}: {error}')
        raise
    finally:
        report['finished_at'] = datetime.now(timezone.utc).isoformat()
        save()
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--allow-fixtures', action='store_true', help='Explicit synthetic inputs in a new temporary test instance')
    parser.add_argument('--report', default='reports/smoke.json')
    args = parser.parse_args()
    try:
        result = run(args.report, allow_fixtures=args.allow_fixtures)
    except Exception as error:
        print(f'Smoke BLOCKED/FAIL: {error}', file=sys.stderr)
        raise SystemExit(1)
    print(f"Real HTTP smoke PASS: {len(result['checks'])} checked responses; synthetic inputs; {args.report}")
