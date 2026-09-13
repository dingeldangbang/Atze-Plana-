"""Separate HTTP worker. No DB credentials, primary/reviewer tokens, or fallback data.

Run: python -m app.challenge_worker --url http://127.0.0.1:8000 [--once]
Only ATZE_CHALLENGE_TOKEN is read; finite request timeout and no response secrets logged.
"""
import argparse
import json
import os
import time
from urllib.request import Request, build_opener, ProxyHandler, HTTPRedirectHandler
from urllib.parse import urlsplit
from app.challenge_rules import analyze


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, new_url):
        return None  # never forward the service credential to another origin


def run_once(url, token):
    parsed = urlsplit(url)
    if parsed.scheme not in {'http', 'https'} or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in {'', '/'}:
        raise ValueError('Use an explicit HTTP(S) server origin without credentials/query/fragment')
    if parsed.scheme == 'http' and parsed.hostname not in {'localhost', '127.0.0.1', '::1'}:
        raise ValueError('Remote challenge-worker transport requires HTTPS')
    if len(token) < 32:
        raise ValueError('Separate ATZE_CHALLENGE_TOKEN required')
    opener = build_opener(ProxyHandler({}), NoRedirects())
    def post(path, value=None):
        request = Request(url.rstrip('/') + path, data=json.dumps(value).encode(), method='POST',
                          headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'})
        with opener.open(request, timeout=20) as response:
            return json.load(response)
    job = post('/api/challenge/jobs/claim')
    if job is None:
        return None
    analysis = analyze(job['snapshot'])
    report = post('/api/challenge/jobs/' + job['job_id'] + '/complete',
                  dict(lease=job['lease'], fingerprint=job['fingerprint'], analysis=analysis.model_dump()))
    return {'job_id': job['job_id'], 'report_id': report['id'], 'verdict': report['analysis']['verdict']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', required=True)
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    token = os.getenv('ATZE_CHALLENGE_TOKEN', '')
    while True:
        try:
            result = run_once(args.url, token)
            print(json.dumps(result or {'status': 'NO_PENDING_JOB'}), flush=True)
        except Exception as error:
            # No response payload, lease, environment or credentials in logs.
            print(json.dumps({'status': 'BLOCKED', 'error_type': type(error).__name__}), flush=True)
            if args.once:
                return 1
        if args.once:
            return 0
        time.sleep(2)


if __name__ == '__main__':
    raise SystemExit(main())
