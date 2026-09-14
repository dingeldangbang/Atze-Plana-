"""Narrow CI guardrails, NOT a semantic proof that every implementation is real."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLOCKED_IMPORTS = {'tests', 'pytest', 'unittest.mock', 'faker', 'responses', 'respx'}


def check(root=ROOT):
    errors = []
    for path in (root / 'app').rglob('*.py'):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            names = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ''] if isinstance(node, ast.ImportFrom) else []
            if isinstance(node, ast.ImportFrom) and node.module == 'unittest' and any(a.name == 'mock' for a in node.names):
                names.append('unittest.mock')
            for name in names:
                if any(name == banned or name.startswith(banned + '.') for banned in BLOCKED_IMPORTS):
                    errors.append(f'{path.relative_to(root)}: test/mock dependency in runtime: {name}')
    smoke = (root / 'scripts/smoke.py').read_text()
    if '--base-url' in smoke:
        errors.append('Smoke runner must not accept an arbitrary target URL')
    if any(isinstance(node, ast.Assert) for node in ast.walk(ast.parse(smoke))):
        errors.append('Smoke checks must not disappear with python -O')
    if not (root / 'REALITY_POLICY.md').is_file():
        errors.append('Missing binding reality policy')
    return errors


if __name__ == '__main__':
    errors = check()
    if errors:
        raise SystemExit('\n'.join(errors))
    print('Reality boundary checks PASS: no forbidden runtime imports; no target-URL or assert-only smoke. Semantic/provider review still required.')
