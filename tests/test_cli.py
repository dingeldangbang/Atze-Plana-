"""CLI contract tests: real subprocess against a real local uvicorn Core; fail-closed, no fallback data."""
import json
import subprocess
import sys
import threading
import time

import pytest
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from conftest import seed, task


@pytest.fixture
def settings(tmp_path):
    return Settings(tmp_path / 'test.db', 'operator-test-only-' * 3, 'reviewer-test-only-' * 3,
                    mode='test', challenge_token='challenge-test-only-' * 3)


@pytest.fixture
def seeded(settings):
    with TestClient(create_app(settings)) as client:
        client.headers['Authorization'] = 'Bearer ' + settings.operator_token
        reviewer = {'Authorization': 'Bearer ' + settings.reviewer_token}
        project, evidence = seed(client, reviewer)
        task(client, project, evidence)
        yield client, reviewer


@pytest.fixture
def core(settings, seeded):
    """Real uvicorn Core on an ephemeral loopback port, same database as the seeded fixture."""
    import uvicorn
    config = uvicorn.Config(create_app(settings), host='127.0.0.1', port=0, log_level='error')
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    for _ in range(200):
        if server.started:
            break
        time.sleep(0.05)
    else:
        pytest.fail('Disposable CLI test Core did not start')
    port = server.servers[0].sockets[0].getsockname()[1]
    yield f'http://127.0.0.1:{port}'
    server.should_exit = True
    thread.join(timeout=5)


def cli(*arguments, env_token=None):
    import os
    environment = dict(os.environ)
    environment.pop('ATZE_TOKEN', None)
    if env_token is not None:
        environment['ATZE_TOKEN'] = env_token
    return subprocess.run([sys.executable, '-m', 'app.cli', *arguments], capture_output=True, text=True,
                          cwd=__import__('pathlib').Path(__file__).resolve().parent.parent, env=environment, timeout=30)


def test_cli_status_unauthenticated(core):
    """CLI-001: the health probe works without a token and reports the real instance mode."""
    result = cli('status', '--base-url', core)
    assert result.returncode == 0, result.stderr
    assert 'mode: test' in result.stdout


def test_cli_lists_real_records(core, seeded, settings):
    """CLI-002: authenticated commands return the real records of the running Core; raw equals the API payload."""
    result = cli('projects', '--base-url', core, '--token', settings.operator_token)
    assert result.returncode == 0, result.stderr
    assert 'Test project' in result.stdout and seeded[0].get('/api/projects').json()[0]['id'] in result.stdout
    raw = cli('monitoring', '--base-url', core, '--token', settings.reviewer_token, '--raw')
    assert raw.returncode == 0, raw.stderr
    payload = json.loads(raw.stdout)
    assert payload['counts']['projects'] == 1 and payload['counts']['tasks'] == 1
    assert payload['stop_active'] is False
    empty = cli('leases', '--base-url', core, '--token', settings.operator_token)
    assert empty.returncode == 0 and '(leer — keine Einträge)' in empty.stdout


def test_cli_fail_closed_without_valid_token_or_core(settings):
    """CLI-003: missing/invalid token and unreachable Core fail with clear errors; never fallback data."""
    missing = cli('projects', '--base-url', 'http://127.0.0.1:9')
    assert missing.returncode == 1 and 'ATZE_TOKEN' in missing.stderr
    invalid = cli('projects', '--base-url', 'http://127.0.0.1:9', '--token', 'invalid-token')
    assert invalid.returncode == 2 and 'unreachable' in invalid.stderr and 'no fallback data' in invalid.stderr


def test_cli_rejects_invalid_token_on_real_core(core):
    """CLI-004: a rejected token is reported, not bypassed."""
    result = cli('evidence', '--base-url', core, '--token', 'completely-invalid-token-value')
    assert result.returncode == 1 and '401' in result.stderr
    assert result.stdout == ''
