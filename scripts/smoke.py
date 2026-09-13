"""Real HTTP workflow. Writes explicitly synthetic fixtures ONLY with opt-in."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import httpx


def run(base_url):
    operator = os.environ['ATZE_OPERATOR_TOKEN']
    reviewer = os.environ['ATZE_REVIEWER_TOKEN']
    records = []
    with httpx.Client(base_url=base_url, timeout=15) as client:
        def call(method, path, body=None, role='operator', expected=200):
            token = operator if role == 'operator' else reviewer
            response = client.request(method, path, json=body, headers={'Authorization': 'Bearer ' + token})
            records.append({'method': method, 'path': path, 'expected_status': expected,
                            'actual_status': response.status_code, 'body': response.json()})
            assert response.status_code == expected, records[-1]
            return response.json()
        call('GET', '/health')
        p = call('POST', '/api/projects', {'name': 'Synthetic HTTP smoke fixture', 'description': 'Not a real project observation'}, expected=201)
        e = call('POST', '/api/evidence', {
            'project_id': p['id'], 'claim': 'Synthetic smoke assertion, not externally validated',
            'source_url': 'https://example.com/fixture', 'observed_at': '2026-01-01T00:00:00Z',
            'source_type': 'manual', 'provider': 'smoke fixture', 'extraction_method': 'manual',
            'content': 'Synthetic test content', 'confidence': 0.9}, expected=201)
        call('POST', f"/api/evidence/{e['id']}/review", {'state': 'verified', 'reason': 'Synthetic test review'}, role='reviewer')
        for action in ['read', 'write']:
            t = call('POST', '/api/tasks', {'project_id': p['id'], 'title': 'Synthetic ' + action,
                     'action': action, 'evidence_ids': [e['id']], 'preconditions_met': True}, expected=201)
            d = call('POST', f"/api/tasks/{t['id']}/triage")
            assert d['state'] == ('eligible' if action == 'read' else 'approval_required')
            assert d['executed'] is False
            if action == 'write':
                call('POST', f"/api/tasks/{t['id']}/approve", {'reason': 'Synthetic approval; no execution'}, role='reviewer', expected=201)
                assert call('POST', f"/api/tasks/{t['id']}/triage")['state'] == 'approved'
        call('GET', '/api/audit', role='reviewer')
    return {'timestamp': datetime.now(timezone.utc).isoformat(), 'kind': 'synthetic HTTP smoke',
            'status': 'passed', 'checks': records}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', required=True)
    parser.add_argument('--allow-fixtures', action='store_true')
    parser.add_argument('--report', default='reports/smoke.json')
    args = parser.parse_args()
    if not args.allow_fixtures:
        parser.error('Refusing to write fixture data without --allow-fixtures; use a test instance')
    result = run(args.base_url)
    path = Path(args.report)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2))
    print(f"HTTP smoke passed: {len(result['checks'])} checked responses; report: {path}")
