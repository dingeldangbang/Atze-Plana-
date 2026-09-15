"""Read-only CLI against a running Atze Core: documented queries only, no mutations, no secrets echoed.

Usage: python -m app.cli COMMAND [--base-url URL] [--token TOKEN] [--raw]
Credentials come from --token or ATZE_TOKEN; the token is never printed.
"""
import argparse
import json
import os
import sys

import httpx

COMMANDS = {
    'status': ('/health', False),          # unauthenticated health probe
    'runtime': ('/api/runtime', True),
    'monitoring': ('/api/monitoring/overview', True),
    'integrations': ('/api/integrations', True),
    'projects': ('/api/projects', True),
    'evidence': ('/api/evidence', True),
    'tasks': ('/api/tasks', True),
    'results': ('/api/results', True),
    'plans': ('/api/plans', True),
    'agents': ('/api/agents', True),
    'resources': ('/api/resources', True),
    'leases': ('/api/leases', True),
    'backups': ('/api/operations/backups', True),
}


def fail(message: str, code: int) -> int:
    print(f'atze-cli: {message}', file=sys.stderr)
    return code


def render(payload, raw: bool) -> None:
    if raw:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return
    if isinstance(payload, list):
        for item in payload:
            print(json.dumps(item, ensure_ascii=False, sort_keys=True))
        if not payload:
            print('(leer — keine Einträge)')
        return
    for key in sorted(payload):
        value = payload[key]
        printed = json.dumps(value, ensure_ascii=False, sort_keys=True) if isinstance(value, (dict, list)) else value
        print(f'{key}: {printed}')


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog='python -m app.cli', description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('command', choices=sorted(COMMANDS), help='read-only query to run')
    parser.add_argument('--base-url', default=os.getenv('ATZE_BASE_URL', 'http://127.0.0.1:8000'),
                        help='Base URL of the Core (default ATZE_BASE_URL or http://127.0.0.1:8000)')
    parser.add_argument('--token', default=os.getenv('ATZE_TOKEN', ''),
                        help='API token (default ATZE_TOKEN); never echoed')
    parser.add_argument('--raw', action='store_true', help='print the exact response payload as pretty JSON')
    args = parser.parse_args(argv)
    path, needs_token = COMMANDS[args.command]
    headers = {'Authorization': 'Bearer ' + args.token} if needs_token else {}
    if needs_token and not args.token:
        return fail('ATZE_TOKEN or --token is required for this command (fail-closed, no anonymous reads)', 1)
    try:
        response = httpx.get(args.base_url.rstrip('/') + path, headers=headers, timeout=10, trust_env=False)
    except httpx.HTTPError as error:
        return fail(f'Core unreachable at {args.base_url} ({type(error).__name__}); no fallback data', 2)
    if response.status_code == 401:
        return fail('Core rejected the token (401); no fallback data', 1)
    if response.status_code == 403:
        return fail('Token role not sufficient for this command (403)', 1)
    if response.status_code != 200:
        return fail(f'Core answered {response.status_code}; no fallback data', 1)
    render(response.json(), args.raw)
    return 0


if __name__ == '__main__':
    sys.exit(main())
