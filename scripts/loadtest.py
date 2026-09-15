"""Bounded local load test against a REAL disposable Core instance (own process, ephemeral port, temp storage).

Honest scope: evidence about THIS machine and THIS build only — no distributed load, no cloud claims,
no shared thresholds. Report-only by default; --assert-p95-ms turns a documented local bound into a gate.
Explicit --allow-fixtures required (synthetic inputs, test mode only).
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import secrets
import socket
import statistics
import subprocess
import sys
from tempfile import TemporaryDirectory
import threading
import time

import httpx

ROOT = Path(__file__).resolve().parents[1]


def percentile(values, fraction):
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round(fraction * (len(ordered) - 1))))
    return round(ordered[index], 3)


def run(report_path=Path('reports/loadtest.json'), *, workers=8, requests_per_worker=40,
        assert_p95_ms=None, allow_fixtures=False):
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = {'timestamp': datetime.now(timezone.utc).isoformat(),
              'kind': 'REAL LOCAL LOAD / SYNTHETIC TEST INPUTS',
              'scope': 'single disposable local instance on this machine; not a distributed or cloud load proof',
              'status': 'NOT_RUN', 'parameters': {'workers': workers, 'requests_per_worker': requests_per_worker,
                                                  'assert_p95_ms': assert_p95_ms}}
    report_path.write_text(json.dumps(report, indent=2))  # invalidate any previous report first
    if not allow_fixtures:
        report.update(status='BLOCKED', error='Explicit --allow-fixtures required')
        report_path.write_text(json.dumps(report, indent=2))
        raise RuntimeError(report['error'])
    report['status'] = 'RUNNING'
    report_path.write_text(json.dumps(report, indent=2))
    latencies, errors = [], []
    lock = threading.Lock()

    def request_once(client, token, index):
        read_paths = ['/health', '/api/projects', '/api/tasks', '/api/monitoring/overview']
        if index % 10 == 7:  # bounded mutation share: unique-named synthetic projects
            body = {'name': f'synthetic-load-project-{index}', 'description': 'Disposable load test input'}
            return client.post('/api/projects', json=body, headers={'Authorization': 'Bearer ' + token})
        return client.get(read_paths[index % len(read_paths)],
                          headers={'Authorization': 'Bearer ' + token} if index % len(read_paths) else {})

    try:
        with TemporaryDirectory(prefix='atze-load-') as tmp, socket.socket() as listener:
            root = Path(tmp)
            listener.bind(('127.0.0.1', 0))
            listener.listen()
            operator = secrets.token_urlsafe(48)
            env = {k: v for k, v in os.environ.items() if not k.startswith('ATZE_')}
            env.update(ATZE_MODE='test', ATZE_DB_PATH=str(root / 'core.db'), ATZE_STORAGE_ROOT=str(root / 'objects'),
                       ATZE_SD_ROOT='', ATZE_OPERATOR_TOKEN=operator, ATZE_REVIEWER_TOKEN=secrets.token_urlsafe(48))
            address = 'http://127.0.0.1:' + str(listener.getsockname()[1])
            server = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'app.main:create_app', '--factory',
                                       '--fd', str(listener.fileno())], cwd=ROOT, env=env,
                                      pass_fds=(listener.fileno(),), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                with httpx.Client(base_url=address, timeout=10, trust_env=False) as probe:
                    for _ in range(200):
                        if server.poll() is not None:
                            raise RuntimeError('Disposable load test Core exited before readiness')
                        try:
                            if probe.get('/health', timeout=0.5).status_code == 200:
                                break
                        except httpx.HTTPError:
                            pass
                        time.sleep(0.05)
                    else:
                        raise RuntimeError('Disposable load test Core did not become ready')

                def worker(worker_index):
                    with httpx.Client(base_url=address, timeout=10, trust_env=False) as client:
                        for step in range(requests_per_worker):
                            index = worker_index * requests_per_worker + step
                            started = time.perf_counter()
                            try:
                                response = request_once(client, operator, index)
                                ok = response.status_code in (200, 201)
                            except httpx.HTTPError:
                                ok = False
                            elapsed = (time.perf_counter() - started) * 1000
                            with lock:
                                latencies.append(round(elapsed, 3))
                                if not ok:
                                    errors.append(index)

                threads = [threading.Thread(target=worker, args=(index,)) for index in range(workers)]
                started = time.perf_counter()
                for thread in threads:
                    thread.start()
                for thread in threads:
                    thread.join()
                wall = time.perf_counter() - started
            finally:
                server.terminate()
                try:
                    server.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait(timeout=5)
        successful = len(latencies) - len(errors)
        report.update(status='PASS' if not errors else 'FAIL',
                      results={'requests': len(latencies), 'successful': successful, 'errors': len(errors),
                               'error_request_ids': errors[:20],
                               'p50_ms': percentile(latencies, 0.50), 'p95_ms': percentile(latencies, 0.95),
                               'p99_ms': percentile(latencies, 0.99), 'max_ms': percentile(latencies, 1.0),
                               'throughput_rps': round(len(latencies) / wall, 3) if wall else None,
                               'wall_seconds': round(wall, 3)},
                      limits='Latency percentiles are machine- and build-specific; no distributed or cloud load claim; '
                             'SQLite serializes writes; the mutation share is bounded (10% project creations)')
        if assert_p95_ms is not None and report['results']['p95_ms'] is not None:
            if report['results']['p95_ms'] > assert_p95_ms:
                report['status'] = 'FAIL'
                report['error'] = f"p95 {report['results']['p95_ms']} ms exceeded the documented local bound {assert_p95_ms} ms"
        report_path.write_text(json.dumps(report, indent=2))
        if report['status'] != 'PASS':
            raise RuntimeError(report.get('error', 'Load test had failing requests; inspect the structured report'))
        return report
    finally:
        pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--report', type=Path, default=Path('reports/loadtest.json'))
    parser.add_argument('--workers', type=int, default=8)
    parser.add_argument('--requests-per-worker', type=int, default=40)
    parser.add_argument('--assert-p95-ms', type=float, default=None,
                        help='Optional documented local bound; turns p95 into a gate')
    parser.add_argument('--allow-fixtures', action='store_true',
                        help='Explicit synthetic inputs against a new disposable test instance')
    arguments = parser.parse_args()
    result = run(arguments.report, workers=arguments.workers, requests_per_worker=arguments.requests_per_worker,
                 assert_p95_ms=arguments.assert_p95_ms, allow_fixtures=arguments.allow_fixtures)
    print(f"Local load test PASS: {result['results']['requests']} requests, "
          f"p95 {result['results']['p95_ms']} ms, {result['results']['throughput_rps']} rps; {arguments.report}")
