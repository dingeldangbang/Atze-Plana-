"""Synthetic inputs in temporary tests only; no Android/device/provider simulation."""
import base64
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest

from scripts.download_android import assemble


def mirror_fixture():
    # Deliberately not APK bytes: this tests transport integrity, never installation.
    data = b'isolated synthetic transport input; not an APK'
    revision = 'a' * 40
    digest = hashlib.sha256(data).hexdigest()
    run = dict(head_sha=revision, conclusion='success', status='completed', path='.github/workflows/android.yml')
    artifact = dict(file='atze-app-debug.apk', bytes=len(data), sha256=digest)
    evidence = {'source_revision': revision, 'build-status.txt': 'BUILD_PASS; INSTALL_NOT_RUN',
                'validation-status.txt': 'EMULATOR_INSTALL_START_TEST_PASS',
                'instrumentation.txt': 'atze_result=PASS',
                'app-signature.txt': 'Verified using v2 scheme (APK Signature Scheme v2): true',
                'apks': [artifact]}
    encoded = base64.b64encode(data).decode()
    chunks = [dict(**artifact, source_revision=revision, index=i, count=2, base64=part)
              for i, part in enumerate([encoded[:32], encoded[32:]])]
    annotations = [dict(title='ANDROID_ARTIFACT_EVIDENCE', message=json.dumps(evidence))]
    annotations += [dict(title='ANDROID_APK_BYTES', message=json.dumps(chunk)) for chunk in chunks]
    return data, revision, run, annotations


def test_apk_mirror_integrity():
    """APK-TRANSPORT-001: exact successful source and shuffled complete chunks reconstruct original synthetic test bytes."""
    data, revision, run, annotations = mirror_fixture()
    assert assemble(run, list(reversed(annotations)), revision)[0] == data


@pytest.mark.parametrize('damage', ['missing', 'duplicate', 'revision', 'failed', 'hash', 'signature', 'install', 'corruption'])
def test_apk_mirror_fail_closed(damage):
    """APK-TRANSPORT-002: incomplete, mixed, failed or corrupted synthetic CI evidence never produces a deliverable."""
    _, revision, run, annotations = mirror_fixture()
    if damage == 'missing':
        annotations.pop()
    elif damage == 'duplicate':
        annotations.append(copy.deepcopy(annotations[-1]))
    elif damage == 'revision':
        run['head_sha'] = 'b' * 40
    elif damage == 'failed':
        run['conclusion'] = 'failure'
    elif damage in {'signature', 'install'}:
        evidence = json.loads(annotations[0]['message'])
        evidence['app-signature.txt' if damage == 'signature' else 'validation-status.txt'] = 'NOT_RUN'
        annotations[0]['message'] = json.dumps(evidence)
    else:
        chunk = json.loads(annotations[-1]['message'])
        chunk['sha256' if damage == 'hash' else 'base64'] = 'b' * 64 if damage == 'hash' else base64.b64encode(b'corrupt').decode()
        annotations[-1]['message'] = json.dumps(chunk)
    with pytest.raises(ValueError):
        assemble(run, annotations, revision)


def test_android_preflight_invalidates_old_artifacts(tmp_path):
    """APK-BUILD-001: real shell preflight failure removes old synthetic artifacts/PASS but preserves unrelated local files."""
    scripts = tmp_path / 'scripts'
    scripts.mkdir()
    shutil.copyfile('scripts/build_android.sh', scripts / 'build_android.sh')
    output = tmp_path / 'reports/android'
    output.mkdir(parents=True)
    for name in ['atze-app-debug.apk', 'atze-test-debug.apk', 'SHA256SUMS', 'app-signature.txt', 'validation-status.txt']:
        (output / name).write_text('stale synthetic test input, never a real build')
    (output / 'unrelated.txt').write_text('keep')
    env = {k: v for k, v in os.environ.items() if k not in {'ANDROID_HOME', 'ANDROID_SDK_ROOT'}}
    result = subprocess.run(['bash', str(scripts / 'build_android.sh')], env=env, capture_output=True, text=True)
    assert result.returncode != 0
    assert 'SDK not configured' in result.stderr
    assert not list(output.glob('*.apk'))
    assert not (output / 'SHA256SUMS').exists()
    assert (output / 'build-status.txt').read_text().strip() == 'BUILD_BLOCKED_OR_FAILED; INSTALL_NOT_RUN'
    assert (output / 'validation-status.txt').read_text().strip() == 'INSTALL_NOT_RUN'
    assert (output / 'unrelated.txt').read_text() == 'keep'


def test_android_workspace_core_contract(client, reviewer):
    """APK-CORE-001: native payload shapes use real Core/SQLite, paginated records, role rejection and mandatory blocked triage."""
    assert client.get('/api/projects?limit=20&offset=0').json() == []
    body = {'name': 'Synthetic Android contract input', 'description': 'Not an operational project'}
    assert client.post('/api/projects', json=body, headers=reviewer).status_code == 403
    project = client.post('/api/projects', json=body)
    assert project.status_code == 201
    project_id = project.json()['id']
    assert client.get('/api/projects?limit=20&offset=0').json()[0]['id'] == project_id
    assert client.get('/api/projects?limit=20&offset=20').json() == []
    # Same explicit fields/defaults as CoreRequests; no implied evidence or prerequisites.
    for action in ['read', 'write', 'flash', 'firmware', 'edl_write', 'production_deploy', 'payment']:
        body = dict(project_id=project_id, title='Synthetic native task contract', action=action,
                    evidence_ids=[], preconditions_met=False)
        assert client.post('/api/tasks', json=body, headers=reviewer).status_code == 403
        response = client.post('/api/tasks', json=body)
        assert response.status_code == 201
        decision = client.post(f"/api/tasks/{response.json()['id']}/triage")
        assert decision.status_code == 200
        assert decision.json()['state'] == 'blocked'
        assert decision.json()['validation_status'] == 'BLOCK'
        assert decision.json()['executed'] is False
        assert client.post(f"/api/tasks/{response.json()['id']}/approve", json={'reason': 'No bypass'}, headers=reviewer).status_code == 409
    assert len(client.get('/api/tasks?limit=20&offset=0').json()) == 7
    assert client.get('/api/plans?limit=20&offset=0').json() == []
    missing = '00000000-0000-4000-8000-000000000001'
    assert client.get(f'/api/plans/{missing}/status').status_code == 404
    assert client.get('/api/projects', headers={'Authorization': 'Bearer invalid'}).status_code == 401
    events = client.get('/api/audit', headers=reviewer).json()
    assert sum(e['event'] == 'task.created' for e in events) == 7
    assert sum(e['event'] == 'task.triaged' for e in events) == 7
