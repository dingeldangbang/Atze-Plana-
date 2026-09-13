import sqlite3
import subprocess
import sys
import pytest
from scripts.backup import backup
from app.config import Settings
from app.main import create_app
from fastapi.testclient import TestClient


def test_backup_restore(client, settings, tmp_path):
    """OPS-001: backup integrity and restored project read work; existing destination is never overwritten."""
    created = client.post('/api/projects', json={'name': 'Backup fixture'}).json()
    destination = tmp_path / 'backup.db'
    assert backup(settings.db_path, destination) == 'ok'
    assert destination.stat().st_mode & 0o777 == 0o600
    with pytest.raises(FileExistsError):
        backup(settings.db_path, destination)
    restored = Settings(destination, settings.operator_token, settings.reviewer_token, mode=settings.mode)
    with TestClient(create_app(restored)) as restored_client:
        response = restored_client.get('/api/projects', headers={'Authorization': 'Bearer ' + settings.operator_token})
        assert response.json()[0]['id'] == created['id']
    with sqlite3.connect(destination) as db:
        assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'


def test_docs_consistent():
    """DOC-002: OpenAPI, generated references, local links and environment coverage pass the worker gate."""
    result = subprocess.run([sys.executable, 'scripts/docs.py', '--check'], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_environment_config(monkeypatch, tmp_path):
    """CFG-001: documented environment names configure startup and persistent path without defaults for secrets."""
    monkeypatch.setenv('ATZE_OPERATOR_TOKEN', 'a' * 40)
    monkeypatch.setenv('ATZE_REVIEWER_TOKEN', 'b' * 40)
    monkeypatch.setenv('ATZE_DB_PATH', str(tmp_path / 'from-env.db'))
    with TestClient(create_app()) as client:
        assert client.get('/health').status_code == 200
        assert client.get('/api/tasks', headers={'Authorization': 'Bearer ' + 'a' * 40}).json() == []


def test_documentation_drift_detection(monkeypatch, tmp_path):
    """DOC-003: changed generated output causes nonzero check status instead of silent acceptance."""
    import scripts.docs as docs
    root = tmp_path
    (root / '.env.example').write_text('')
    (root / 'config.example.yaml').write_text('{}')
    (root / 'docs/19-operations').mkdir(parents=True)
    (root / 'docs/19-operations/configuration.md').write_text('')
    (root / 'reports').mkdir()
    (root / 'reports/README.md').write_text('')
    (root / 'generated.md').write_text('outdated')
    monkeypatch.setattr(docs, 'ROOT', root)
    monkeypatch.setattr(docs, 'products', lambda: ({'generated.md': 'current'}, []))
    monkeypatch.setattr(sys, 'argv', ['docs.py', '--check'])
    assert docs.main() == 1
    (root / 'generated.md').write_text('current')
    assert docs.main() == 0


def test_broken_link_detection(monkeypatch, tmp_path):
    """DOC-004: missing local reference is detected and existing reference is accepted."""
    import scripts.docs as docs
    (tmp_path / 'README.md').write_text('[missing](missing.md)')
    (tmp_path / 'reports').mkdir()
    (tmp_path / 'reports/README.md').write_text('')
    monkeypatch.setattr(docs, 'ROOT', tmp_path)
    assert docs.validate_links() == ['README.md: broken file reference missing.md']
    (tmp_path / 'missing.md').write_text('Now present')
    assert docs.validate_links() == []
