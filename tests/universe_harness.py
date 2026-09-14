#!/usr/bin/env python3
"""Explicit bounded command runner, not a sandbox or universal readiness proof."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from universe import audit, files, repo_root, write_report


def detect_stack(root):
    names = {str(p) for p, _ in files(root)}
    stacks = []
    for manifest, stack in [('package.json', 'node'), ('Cargo.toml', 'rust'), ('go.mod', 'go'),
                             ('pyproject.toml', 'python'), ('build.gradle', 'gradle'),
                             ('build.gradle.kts', 'gradle'), ('composer.json', 'php'),
                             ('Gemfile', 'ruby'), ('pubspec.yaml', 'flutter')]:
        if manifest in names:
            stacks.append(stack)
    if any(p.endswith('AndroidManifest.xml') for p in names):
        stacks.append('android')
    nested = sorted(p for p in names if '/' in p and Path(p).name in
                    {'package.json', 'Cargo.toml', 'pyproject.toml', 'go.mod', 'build.gradle', 'build.gradle.kts'})
    return sorted(set(stacks)), nested


def plan(root, scope):
    stacks, nested = detect_stack(root)
    commands, blockers = [], []
    atze = (root / 'scripts/smoke.py').is_file() and (root / 'app/plan_service.py').is_file()
    for stack in stacks:
        if stack == 'python':
            commands.extend([('python tests', [sys.executable, '-m', 'pytest', '-q']),
                             ('python build', [sys.executable, '-m', 'build'])])
            if atze:
                commands.extend([(name, [sys.executable, 'scripts/' + script, *args]) for name, script, args in [
                    ('documentation', 'docs.py', ['--check']), ('reality', 'reality_check.py', []),
                    ('isolated HTTP/worker E2E', 'smoke.py', ['--allow-fixtures'])]])
        elif stack == 'node':
            package = json.loads((root / 'package.json').read_text())
            for action in ['test', 'build']:
                if package.get('scripts', {}).get(action):
                    commands.append(('node ' + action, ['npm', 'run', action]))
                else:
                    blockers.append('node: missing ' + action + ' script')
        elif stack == 'rust':
            commands.extend([('rust tests', ['cargo', 'test', '--locked']), ('rust build', ['cargo', 'build', '--locked'])])
        elif stack == 'go':
            commands.extend([('go tests', ['go', 'test', './...']), ('go build', ['go', 'build', './...'])])
        elif stack == 'gradle':
            commands.extend([('gradle tests', ['./gradlew', 'test']), ('gradle build', ['./gradlew', 'assemble'])])
        else:
            if scope == 'core' and atze and stack == 'android':
                continue
            blockers.append(stack + ': explicit platform/build/test contract and tools required')
    if not stacks:
        blockers.append('Unknown stack: no test/build success inferred')
    if nested:
        blockers.append('Nested manifest build scopes require explicit review: ' + ', '.join(nested))
    return stacks, commands, blockers


def run_command(root, name, argv, timeout):
    result = {'name': name, 'argv': argv, 'status': 'BLOCKED', 'exit_code': None}
    executable = root / argv[0] if '/' in argv[0] and not Path(argv[0]).is_absolute() else argv[0]
    if not shutil.which(str(executable)):
        result['reason'] = 'EXECUTABLE_NOT_AVAILABLE'
        return result
    started = time.monotonic()
    # Keep logs out of reports: commands can print secrets. No inherited ATZE credentials.
    env = {k: v for k, v in os.environ.items() if not k.startswith('ATZE_')}
    process = subprocess.Popen(argv, cwd=root, env=env, stdin=subprocess.DEVNULL,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    try:
        result['exit_code'] = process.wait(timeout=timeout)
        result['status'] = 'PASS' if result['exit_code'] == 0 else 'FAIL'
    except subprocess.TimeoutExpired:
        result.update(status='BLOCKED', reason='TIMEOUT')
    finally:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            pass
        # Also stop descendants if the parent has already exited.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()
    result['seconds'] = round(time.monotonic() - started, 3)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true', help='Authorize execution of repository test/build code')
    parser.add_argument('--scope', choices=['all', 'core'], default='all')
    parser.add_argument('--timeout', type=int, default=300)
    args = parser.parse_args(argv)
    if not 1 <= args.timeout <= 1800:
        parser.error('timeout must be 1..1800 seconds per command')
    root = repo_root(Path.cwd())
    date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    report = {'started_at': datetime.now(timezone.utc).isoformat(), 'scope': args.scope,
              'status': 'BLOCKED', 'checks': [], 'mocks_removed': 0, 'artifacts': [],
              'limitations': ['No automatic repairs, port scans, hardware or deployment',
                              'No complete UI/endpoint/OOM/disconnect/semantic/secret audit',
                              'Runner is not an OS sandbox; repository commands can execute arbitrary code']}
    target = f'universe-{date}.json'
    write_report(root, target, json.dumps(report, indent=2))
    try:
        audit(root)
        stacks, commands, blockers = plan(root, args.scope)
        report.update(stacks=stacks, blockers=blockers, planned=[{'name': n, 'argv': a} for n, a in commands])
        if args.execute:
            # Python wheel/sdist must be produced or modified in this execution, not old leftovers.
            before = {p: p.stat().st_mtime_ns for p in (root / 'dist').glob('*') if p.is_file()}
            for name, command in commands:
                report['checks'].append(run_command(root, name, command, args.timeout))
                write_report(root, target, json.dumps(report, indent=2))
            for p in (root / 'dist').glob('*'):
                if p.is_file() and not p.is_symlink() and p.suffix in {'.whl', '.gz'} and p.stat().st_mtime_ns != before.get(p):
                    report['artifacts'].append({'file': str(p.relative_to(root)), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'bytes': p.stat().st_size})
            if 'python' in stacks and not report['artifacts']:
                report['blockers'].append('No new Python build artifact observed')
            if commands and not report['blockers'] and all(r['status'] == 'PASS' for r in report['checks']):
                report['status'] = 'PARTIAL'  # Selected commands passed, universal acceptance NOT established.
        else:
            report['blockers'].append('Execution not authorized; plan only')
    except Exception as error:
        report['error_type'] = type(error).__name__  # No exception strings/source data in shared report.
        report['status'] = 'BLOCKED'
    finally:
        report['finished_at'] = datetime.now(timezone.utc).isoformat()
        write_report(root, target, json.dumps(report, indent=2) + '\n')
        lines = ['# Universe validation — ' + date, '', 'Conclusion: **' + report['status'] + '**',
                 'Scope: ' + args.scope, 'Mocks removed: 0 (no automatic source edits)', '',
                 '| Check | Status | Actual exit code | Seconds |', '|---|---|---|---|']
        for row in report['checks']:
            lines.append(f"| {row['name']} | {row['status']} | {row['exit_code']} | {row.get('seconds', '—')} |")
        if report.get('error_type'):
            lines += ['', 'Harness error: ' + report['error_type']]
        lines += ['', '## Blockers / limits', *['- ' + b for b in report.get('blockers', []) + report['limitations']],
                  '', 'Exact command vectors and observed artifact SHA256: ' + target]
        write_report(root, f'universe-{date}.md', '\n'.join(lines) + '\n')
    print(f"Universe: {report['status']} — reports/universe-{date}.md")
    return 0 if report['status'] == 'PARTIAL' else 2


if __name__ == '__main__':
    raise SystemExit(main())
