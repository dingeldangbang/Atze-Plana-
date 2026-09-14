#!/usr/bin/env python3
"""Read-only source inventory and explicit, verified source backups; no external IO."""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import stat

EXTENSIONS = {'.py', '.js', '.jsx', '.ts', '.tsx', '.rs', '.kt', '.kts', '.java', '.c', '.h', '.cpp', '.hpp', '.swift', '.go', '.rb', '.php', '.dart', '.sh', '.html', '.css', '.cs', '.vue', '.svelte'}
MANIFESTS = {'package.json', 'Cargo.toml', 'build.gradle', 'build.gradle.kts', 'settings.gradle', 'go.mod', 'pyproject.toml', 'composer.json', 'Gemfile', 'Podfile', 'pubspec.yaml', 'CMakeLists.txt', 'Makefile', 'AndroidManifest.xml'}
EXCLUDED = {'.git', '.venv', 'node_modules', 'backups', 'reports', 'data', 'build', 'dist', 'target', '.cache', '__pycache__'}


def safe_source(path):
    return not any(p in EXCLUDED for p in path.parts) and not any(
        p.startswith('.env') or any(s in p.lower() for s in ('secret', 'credential', 'private-key')) for p in path.parts
    ) and path.suffix.lower() not in {'.pem', '.key', '.p12', '.jks', '.db', '.bak'}


def repo_root(path):
    return Path(subprocess.check_output(['git', '-C', str(path), 'rev-parse', '--show-toplevel'], text=True).strip())


def files(root):
    tracked = set(subprocess.check_output(['git', '-C', str(root), 'ls-files', '-z']).decode().split('\0'))
    pending = set(subprocess.check_output(['git', '-C', str(root), 'ls-files', '--others', '--exclude-standard', '-z']).decode().split('\0'))
    return [(Path(p), 'tracked' if p in tracked else 'untracked') for p in sorted((tracked | pending) - {''}) if safe_source(Path(p))]


def read_source(root, relative):
    path = root / relative
    if any(p.is_symlink() for p in [path, *path.parents] if p != root and root in p.parents) or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('Symlink or outside-root source refused')
    if path.stat().st_size > 2 * 1024 * 1024:
        raise ValueError('Source exceeds 2MiB audit bound')
    return path.read_bytes()


def findings(text, suffix):
    result = []
    for n, line in enumerate(text.splitlines(), 1):
        match = re.search(r'(?:#|//|/\*|<!--)\s*(TODO|FIXME|MOCK|SHIM|STUB|PLACEHOLDER|HACK)\b', line)
        if match:
            result.append((n, match[1]))
        if suffix != '.py' and re.search(r'\{\s*return\s+(?:false|0|null|\{\})\s*;?\s*\}', line):
            result.append((n, 'EMPTY_RETURN_REVIEW'))
        if re.search(r'(?:assert\s+True\b|assert\s*\(\s*true\s*\)|not implemented)', line, re.I):
            result.append((n, 'REVIEW_LITERAL'))
    if suffix == '.py':
        try:
            tree = ast.parse(text)
        except SyntaxError as error:
            result.append((error.lineno or 0, 'SYNTAX_ERROR'))
        else:
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    body = list(node.body)
                    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
                        body = body[1:]
                    if len(body) == 1 and (isinstance(body[0], ast.Pass) or
                        isinstance(body[0], ast.Return) and (body[0].value is None or
                        isinstance(body[0].value, ast.Constant) and body[0].value.value in (None, 0, False))):
                        result.append((node.lineno, 'STUB_CANDIDATE'))
                    elif len(body) == 1 and isinstance(body[0], ast.Return) and isinstance(body[0].value, (ast.Dict, ast.List)):
                        value = body[0].value
                        if not (value.keys if isinstance(value, ast.Dict) else value.elts):
                            result.append((node.lineno, 'EMPTY_RETURN_REVIEW'))
    return sorted(set(result))


def inventory(root):
    rows, manifests = [], []
    for path, git_state in files(root):
        if path.name in MANIFESTS:
            manifests.append(str(path))
        if path.suffix not in EXTENSIONS:
            continue
        row = {'path': str(path), 'git': git_state, 'status': 'REAL', 'validation': 'NOT VALIDATED'}
        try:
            raw = read_source(root, path)
            signals = findings(raw.decode('utf-8'), path.suffix)
            row.update(sha256=hashlib.sha256(raw).hexdigest(), signals=signals)
            if signals:
                code = signals[0][1]
                row['status'] = code if code in {'TODO', 'FIXME', 'MOCK', 'STUB', 'PLACEHOLDER'} else 'STUB' if code == 'STUB_CANDIDATE' else 'TODO'
        except (OSError, ValueError, UnicodeError):
            row.update(status='TODO', signals=[(0, 'UNREADABLE_OR_UNSAFE')])
        rows.append(row)
    return {'time': datetime.now(timezone.utc).isoformat(), 'manifests': manifests, 'files': rows}


def write_report(root, name, text):
    directory = root / 'reports'
    if directory.is_symlink():
        raise ValueError('Symlink report directory refused')
    directory.mkdir(exist_ok=True)
    path = directory / name
    if path.is_symlink() or path.parent != directory or '/' in name or '\\' in name:
        raise ValueError('Unsafe report filename')
    # Never follow an existing report symlink. Reports contain no source excerpts/log output.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    with os.fdopen(fd, 'w') as output:
        info = os.fstat(output.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ValueError('Non-regular or hardlinked report refused')
        output.truncate(0)
        output.write(text)
    return path


def audit(root):
    result = inventory(root)
    lines = ['# Universe Inventory', '', result['time'], '',
             'Heuristische Hinweise, keine automatische Reparatur. REAL = kein erkanntes Signal, nicht funktional validiert.',
             'DEAD/DUAL, fehlende Imports, Frameworks, UI-Erreichbarkeit und Spezifikationsabdeckung benötigen gesonderte Analyse.',
             'Ohne Secrets, ignorierte Daten und Quelltextauszüge. Keine Trefferbegrenzung; unsichere/große Dateien werden markiert.',
             '', '## Erkannte Manifestdateien', *['- ' + p for p in result['manifests']], '',
             '## Quelldateien', '| Datei | Git | Status (heuristisch) | Signale (Zeile:Code) | SHA256 |', '|---|---|---|---|---|']
    for row in result['files']:
        name = row['path'].replace('|', '&#124;').replace('\n', ' ').replace('<', '&lt;').replace('>', '&gt;')
        signals = ', '.join(f'{line}:{code}' for line, code in row['signals']) or 'keine'
        lines.append(f"| {name} | {row['git']} | {row['status']} | {signals} | {row.get('sha256', 'UNKNOWN')} |")
    write_report(root, 'inventory.json', json.dumps(result, indent=2) + '\n')
    return write_report(root, 'inventory.md', '\n'.join(lines) + '\n')


def backup(root, relative):
    path = Path(relative)
    if path.is_absolute() or '..' in path.parts or not safe_source(path) or path.suffix not in EXTENSIONS:
        raise ValueError('Only eligible relative source paths may be backed up')
    raw = read_source(root, path)
    sha = hashlib.sha256(raw).hexdigest()
    directory = root / 'backups'
    if directory.is_symlink():
        raise ValueError('Symlink backup directory refused')
    directory.mkdir(mode=0o700, exist_ok=True)
    destination = directory / (sha + '.bak')
    try:
        fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    except FileExistsError:
        if destination.is_symlink() or hashlib.sha256(destination.read_bytes()).hexdigest() != sha:
            raise ValueError('Existing backup failed integrity verification')
    else:
        with os.fdopen(fd, 'wb') as output:
            output.write(raw)
            output.flush()
            os.fsync(output.fileno())
    if hashlib.sha256(destination.read_bytes()).hexdigest() != sha:
        raise ValueError('Backup integrity mismatch')
    return destination


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--backup', help='Explicit relative source; no edits performed')
    args = parser.parse_args()
    root = repo_root(args.root)
    print(backup(root, args.backup) if args.backup else audit(root))
