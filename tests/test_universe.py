"""UNI: isolated synthetic source fixtures; real Git/files/processes, never product data."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from universe import audit, backup, findings, inventory, write_report, read_source
spec = importlib.util.spec_from_file_location('universe_harness', ROOT / 'tests/universe_harness.py')
harness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(harness)


class UniverseTests(unittest.TestCase):
    """Real local tooling boundaries; no model/provider simulation."""
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)

    def tearDown(self):
        self.temp.cleanup()

    def test_inventory_exclusions_and_pending_files(self):
        """UNI-001: ignored/secret files excluded, pending source seen, no source excerpt."""
        (self.root / '.gitignore').write_text('ignored/\n')
        (self.root / 'ignored').mkdir()
        (self.root / 'ignored/a.py').write_text('SECRET_MARKER')
        (self.root / '.env.py').write_text('SECRET_MARKER')
        (self.root / 'source.py').write_text('# TODO PRIVATE_MARKER\ndef value():\n    return None\n')
        rows = inventory(self.root)['files']
        self.assertEqual([r['path'] for r in rows], ['.gitignore', 'source.py'])
        self.assertEqual(rows[1]['git'], 'untracked')
        text = audit(self.root).read_text()
        self.assertNotIn('PRIVATE_MARKER', text)
        self.assertNotIn('SECRET_MARKER', text)

    def test_inventory_covers_cross_language_and_contract_sources(self):
        """UNI-010: CJS, workflow/API/build/docs contracts and safe env template are inventoried; real env remains excluded."""
        fixtures = {
            'runner.cjs': "'use strict';\n",
            'workflow.yml': 'name: isolated workflow\n',
            'schema.yaml': 'openapi: 3.1.0\n',
            'contract.json': '{}\n',
            'manifest.xml': '<manifest/>\n',
            'pyproject.toml': '[project]\nname="fixture"\n',
            'requirements.lock': 'example==1.0\n',
            'README.md': '# Isolated contract\n',
            '.env.example': 'ATZE_OPERATOR_TOKEN=\n',
        }
        for name, content in fixtures.items():
            (self.root / name).write_text(content)
        (self.root / '.env').write_text('must-not-inventory')
        rows = {row['path']: row for row in inventory(self.root)['files']}
        self.assertTrue(set(fixtures).issubset(rows))
        self.assertNotIn('.env', rows)
        self.assertTrue(all(rows[name]['status'] == 'REAL' for name in fixtures))
        self.assertEqual(backup(self.root, 'runner.cjs').read_text(), fixtures['runner.cjs'])

    def test_legitimate_pass_and_syntax(self):
        """UNI-002: exception pass not a stub; whole empty function candidate, syntax distinct."""
        self.assertEqual(findings('try:\n    x()\nexcept ValueError:\n    pass\n', '.py'), [])
        self.assertIn((1, 'STUB_CANDIDATE'), findings('def empty():\n    pass\n', '.py'))
        self.assertTrue(any(code == 'SYNTAX_ERROR' for _, code in findings('def (', '.py')))
        self.assertEqual(findings('Use `assert True` only as an example.\n', '.md'), [])
        self.assertIn((1, 'TODO'), findings('# TODO real documentation gap\n', '.md'))

    def test_backup_integrity_and_symlinks(self):
        """UNI-003: actual byte copy, idempotent backup, corrupt backup/symlink rejected."""
        raw = b'def value():\n    return 7\n'
        (self.root / 'source.py').write_bytes(raw)
        saved = backup(self.root, 'source.py')
        self.assertEqual(saved.name, hashlib.sha256(raw).hexdigest() + '.bak')
        self.assertEqual(saved.read_bytes(), raw)
        self.assertEqual(backup(self.root, 'source.py'), saved)
        saved.write_bytes(b'corruption')
        with self.assertRaises(ValueError):
            backup(self.root, 'source.py')
        (self.root / 'link.py').symlink_to(self.root / 'source.py')
        with self.assertRaises(ValueError):
            backup(self.root, 'link.py')
        with self.assertRaises(ValueError):
            backup(self.root, '../source.py')

    def test_report_symlink_refused(self):
        """UNI-004: report writer cannot overwrite symlink target."""
        (self.root / 'reports').mkdir()
        target = self.root / 'valuable.txt'
        target.write_text('retained')
        (self.root / 'reports/a.md').symlink_to(target)
        with self.assertRaises(ValueError):
            write_report(self.root, 'a.md', 'bad')
        self.assertEqual(target.read_text(), 'retained')

    def test_multi_stack_and_unknown(self):
        """UNI-005: multiple stacks, actual commands without collect/dry-run; unknown blocked."""
        self.assertTrue(harness.plan(self.root, 'all')[2])
        (self.root / 'pyproject.toml').write_text('[project]\nname="fixture"')
        (self.root / 'Cargo.toml').write_text('[package]\nname="fixture"')
        stacks, commands, blockers = harness.plan(self.root, 'all')
        self.assertEqual(stacks, ['python', 'rust'])
        self.assertEqual(len(commands), 4)
        self.assertFalse(blockers)
        self.assertNotIn('--no-run', repr(commands))
        self.assertNotIn('--collect-only', repr(commands))

    def test_android_all_scope_uses_explicit_build_contract(self):
        """UNI-011: all-scope Android detection runs the declared build script rather than claiming a platform result."""
        (self.root / 'android/app').mkdir(parents=True)
        (self.root / 'android/app/AndroidManifest.xml').write_text('<manifest/>')
        (self.root / 'scripts').mkdir()
        (self.root / 'scripts/build_android.sh').write_text('exit 0\n')
        stacks, commands, blockers = harness.plan(self.root, 'all')
        self.assertEqual(stacks, ['android'])
        self.assertEqual(commands, [('Android debug build', ['bash', 'scripts/build_android.sh'])])
        self.assertEqual(blockers, [])
        self.assertEqual(harness.run_command(self.root, *commands[0], 2)['status'], 'PASS')

    def test_actual_process_exit_and_timeout(self):
        """UNI-006: real failing/successful/timeout processes, no shell; no stdout leak."""
        ok = harness.run_command(self.root, 'success', [sys.executable, '-c', 'print("SECRET_MARKER")'], 2)
        bad = harness.run_command(self.root, 'failure', [sys.executable, '-c', 'raise SystemExit(7)'], 2)
        slow = harness.run_command(self.root, 'timeout', [sys.executable, '-c', 'import time; time.sleep(10)'], 1)
        self.assertEqual((ok['status'], bad['exit_code'], slow['reason']), ('PASS', 7, 'TIMEOUT'))
        # argv is explicit metadata; subprocess stdout itself is never reported.
        self.assertNotIn('stdout', ok)

    def test_plan_only_fails_closed(self):
        """UNI-007: no --execute means no code runs, saved report BLOCKED, nonzero exit."""
        (self.root / 'package.json').write_text(json.dumps({'scripts': {'test': 'touch MUST_NOT_EXIST', 'build': 'touch MUST_NOT_EXIST'}}))
        result = subprocess.run([sys.executable, str(ROOT / 'tests/universe_harness.py')], cwd=self.root, capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.root / 'MUST_NOT_EXIST').exists())
        report = json.loads(next((self.root / 'reports').glob('universe-*.json')).read_text())
        self.assertEqual(report['checks'], [])
        self.assertEqual(report['status'], 'BLOCKED')

    def test_nonregular_and_hardlinked_output(self):
        """UNI-008: FIFO source cannot hang scanner; hardlinked report cannot truncate data."""
        os.mkfifo(self.root / 'blocked.py')
        with self.assertRaises(ValueError):
            read_source(self.root, Path('blocked.py'))
        (self.root / 'reports').mkdir()
        target = self.root / 'retained.txt'
        target.write_text('untouched')
        os.link(target, self.root / 'reports/hardlink.md')
        with self.assertRaises(ValueError):
            write_report(self.root, 'hardlink.md', 'replacement')
        self.assertEqual(target.read_text(), 'untouched')

    def test_token_aware_markers_and_inherited_hooks(self):
        """UNI-009: Python strings and inherited no-op callbacks stay REAL; actual markers and unimplemented bodies stay visible."""
        callback = 'class Callback(Base):\n    def log_message(self, *args):\n        pass\n'
        self.assertEqual(findings('example = "# TODO fixture text"\n', '.py'), [])
        self.assertEqual(findings(callback, '.py'), [])
        self.assertIn((1, 'TODO'), findings('# TODO real source marker\n', '.py'))
        self.assertIn((1, 'REVIEW_LITERAL'), findings('assert True\n', '.py'))
        self.assertIn((2, 'STUB_CANDIDATE'), findings('def missing():\n    raise NotImplementedError("not implemented")\n', '.py'))

        (self.root / 'callback.py').write_text(callback)
        (self.root / 'marker.py').write_text('# TODO real source marker\n')
        (self.root / 'missing.py').write_text('def missing():\n    raise NotImplementedError("not implemented")\n')
        rows = {row['path']: row for row in inventory(self.root)['files']}
        self.assertEqual(rows['callback.py']['status'], 'REAL')
        self.assertEqual(rows['marker.py']['status'], 'TODO')
        self.assertEqual(rows['missing.py']['status'], 'STUB')


if __name__ == '__main__':
    unittest.main()
