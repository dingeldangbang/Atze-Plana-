"""Deterministic Documentation Worker: source/schema/test/config/history inventory.

No LLM, no network fetches, no fabricated behavior. --check detects generated drift,
validates OpenAPI, local Markdown file links and environment coverage.
"""
import argparse
import ast
import json
import re
import subprocess
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import yaml
from openapi_spec_validator import validate
from app.main import create_app


def products():
    schema = create_app(schema_only=True).openapi()
    validate(schema)
    result = {'openapi.yaml': yaml.safe_dump(schema, sort_keys=False, allow_unicode=True)}
    lines = ['# API reference (generated)', '',
             'Source: `app/main.py` and Pydantic models. Regenerate: `python scripts/docs.py`.', '',
             '## Shared contract', '',
             '- JSON over HTTP; bearer token for every `/api/` route. Health is public.',
             '- One workspace, two shared role tokens; no per-user identity or tenant isolation.',
             '- No application rate limiter. Production requires a trusted ingress with body/time/rate limits.',
             '- 401 missing/invalid token; 403 wrong role; 404 absent entity; 409 state conflict;',
             '  422 schema/reference validation; 503 unavailable/locked storage. AI run returns explicit BLOCKED/UNAVAILABLE/DRAFT_UNCHALLENGED envelopes; never infer success from HTTP 200.',
             '- Lists: `limit=1..100` (default 100), `offset>=0` (default 0), insertion order.',
             '- Request and response field constraints are in [OpenAPI](../../openapi.yaml).',
             '- Runnable creation example: [Quickstart](../../QUICKSTART.md).', '',
             '| Method | Endpoint | Role | Request schema | Success response | Side effects / evidence requirements |',
             '|---|---|---|---|---|---|']
    for path, methods in schema['paths'].items():
        for method, operation in methods.items():
            if method not in {'get', 'post'}:
                raise ValueError('Document new HTTP method explicitly')
            role = 'both'
            if path == '/health':
                role = 'public'
            elif method == 'post' and path in ['/api/projects', '/api/tasks', '/api/evidence']:
                role = 'operator'
            elif path.endswith(('/review', '/approve')) or path == '/api/audit' or (path == '/api/control/stop' and method == 'post'):
                role = 'reviewer'
            request = operation.get('requestBody', {}).get('content', {}).get('application/json', {}).get('schema', {})
            responses = {k: v for k, v in operation['responses'].items() if k.startswith('2')}
            effect = 'None; read-only'
            if method == 'post':
                if path.endswith('/review'):
                    effect = 'One immutable manual evidence review + audit; reason required'
                elif path.endswith('/approve'):
                    effect = 'Approval bound to current Result/Challenge/fingerprint + audit; current triage must require approval; never executes'
                elif path.endswith('/triage'):
                    effect = 'Decision snapshot in audit; current mandatory Challenge + verified evidence, confidence >=0.8, preconditions, no stop'
                elif path.endswith('/stop'):
                    effect = 'Persist global stop + reason in audit; does not interrupt external processes'
                elif path.endswith('/evidence'):
                    effect = 'Store original text/hash/provenance + audit; existing project required; initially unverified'
                elif path.endswith('/tasks'):
                    effect = 'Immutable task + audit; all evidence references must belong to project'
                else:
                    effect = 'Project + audit; no evidence requirement'
            role = operation.get('x-role', role)
            effect = operation.get('x-side-effects', effect)
            name = request.get('$ref', '').split('/')[-1] or '—'
            response = json.dumps(responses, ensure_ascii=False).replace('|', '\\|')
            lines.append(f'| {method.upper()} | `{path}` | {role} | {name} | `{response}` | {effect} |')
    lines += ['', '## Static surface', '', '`GET /` and `GET /static/{path}` serve the dashboard without authentication.',
              'No embedded workspace data; browser uses same-origin bearer-authenticated API requests.',
              'Bounded JSON UTF-8 archive/cache ingestion is supported; no binary upload, MCP transport, shell, or execute endpoint.', '']
    result['docs/08-network/APIs.md'] = '\n'.join(lines)
    lines = ['# Test catalog (generated)', '',
             'Every test definition is catalogued from its AST; parametrizations produce separate JUnit cases.',
             'Actual results are in `reports/junit.xml` after running pytest, not inferred by this worker.', '',
             '## Shared test procedure', '',
             '- Preconditions: Python 3.11+, locked dependencies; isolated pytest temporary SQLite DB.',
             '- Inputs: synthetic fixtures in [conftest](../../tests/conftest.py), never device observations.',
             '- Actions/expected results: linked test bodies and assertions below are authoritative.',
             '- Execution: `python -m pytest --junitxml=reports/junit.xml`.',
             '- Actual result/status/evidence: JUnit testcase failure/error/skipped and timestamps; CI artifact.',
             '- No test execution is performed by documentation generation itself.', '',
             '| Test ID / purpose / expected result | Executable case |', '|---|---|']
    for path in sorted((ROOT / 'tests').glob('test_*.py')):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith('test_'):
                description = ast.get_docstring(node)
                if not description:
                    raise ValueError(f'Missing test description: {node.name}')
                lines.append(f'| {description.replace(chr(10), " ")} | [{path.name}: {node.name}](../../tests/{path.name}) |')
    result['docs/14-testing/test-catalog.md'] = '\n'.join(lines) + '\n'
    sources = []
    for path in sorted((ROOT / 'app').glob('*.py')):
        tree = ast.parse(path.read_text())
        names = [node.name for node in tree.body if isinstance(node, (ast.ClassDef, ast.FunctionDef))]
        sources.append(f'- `{path.relative_to(ROOT)}`: ' + (', '.join(names) or '(package marker)'))
    env = sorted(set(re.findall(r"os.getenv\('([^']+)'", (ROOT / 'app/config.py').read_text())))
    result['docs/generated-inventory.md'] = '# Source inventory (generated)\n\n' + '\n'.join(sources) + '\n\nEnvironment: ' + ', '.join(f'`{x}`' for x in env) + '\n'
    return result, env


def validate_links():
    errors = []
    files = list(ROOT.glob('*.md')) + list((ROOT / 'docs').rglob('*.md')) + [ROOT / 'reports/README.md']
    for path in files:
        for link in re.findall(r'(?<!!)\[[^\]]*\]\(([^)]+)\)', path.read_text()):
            if '://' in link or link.startswith(('mailto:', '#')):
                continue
            target = link.split('#')[0]
            if target and not (path.parent / target).exists():
                errors.append(f'{path.relative_to(ROOT)}: broken file reference {link}')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--history', action='store_true', help='Print recent local git history as draft input')
    args = parser.parse_args()
    if args.history:
        subprocess.run(['git', 'log', '-10', '--format=%h %s'], cwd=ROOT, check=True)
    generated, env = products()
    errors = []
    for name, content in generated.items():
        path = ROOT / name
        if args.check:
            if not path.exists() or path.read_text() != content:
                errors.append('Outdated generated document: ' + name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
    example_names = sorted(re.findall(r'^(ATZE_\w+)=', (ROOT / '.env.example').read_text(), re.M))
    if env != example_names or env != sorted(yaml.safe_load((ROOT / 'config.example.yaml').read_text())):
        errors.append('Environment/config example coverage mismatch')
    config_doc = (ROOT / 'docs/19-operations/configuration.md').read_text()
    if any(name not in config_doc for name in env):
        errors.append('Missing environment variable documentation')
    errors.extend(validate_links())
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        return 1
    print(f'Documentation OK: {len(generated)} generated products, OpenAPI valid, local file links valid, {len(env)} environment variables covered')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
