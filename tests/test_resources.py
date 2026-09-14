"""Resource manager contract tests: real uploads, versions, reference links, confirmed deactivation, no deletion."""
import base64
import hashlib
import pytest
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.resource_models import MAX_CONTENT_BYTES
from conftest import seed, task


@pytest.fixture
def settings(tmp_path):
    return Settings(tmp_path / 'test.db', 'operator-test-only-' * 3, 'reviewer-test-only-' * 3,
                    mode='test', challenge_token='challenge-test-only-' * 3)


@pytest.fixture
def client(settings):
    with TestClient(create_app(settings)) as client:
        client.headers['Authorization'] = 'Bearer ' + settings.operator_token
        yield client


@pytest.fixture
def reviewer(settings):
    return {'Authorization': 'Bearer ' + settings.reviewer_token}


def upload_body(name='bench-config', kind='configuration', content=b'synthetic fixture content v1',
                source='Owner-declared local fixture file', description='Synthetic test resource, not hardware output'):
    return {'name': name, 'kind': kind, 'source': source, 'description': description,
            'content_base64': base64.b64encode(content).decode()}


def upload(client, **overrides):
    response = client.post('/api/resources', json=upload_body(**overrides))
    assert response.status_code == 201, response.text
    return response.json()


def test_upload_roundtrip_with_hash_and_text_preview(client):
    """RES-001: upload persists content blob, returns correct sha256/size/version 1; content readback is byte-identical."""
    content = b'synthetic fixture content v1'
    resource = upload(client, content=content)
    assert resource['version'] == 1 and resource['state'] == 'active'
    assert resource['family_id'] == resource['id'] and resource['predecessor_id'] is None
    assert resource['sha256'] == hashlib.sha256(content).hexdigest()
    assert resource['size_bytes'] == len(content)
    response = client.get(f"/api/resources/{resource['id']}/content")
    assert response.status_code == 200
    assert response.content == content
    assert response.headers['X-Atze-Sha256'] == resource['sha256']
    assert response.headers['X-Atze-Version'] == '1'
    preview = client.get(f"/api/resources/{resource['id']}/preview").json()
    assert preview['encoding'] == 'TEXT' and preview['text_preview'] == 'synthetic fixture content v1'
    assert preview['char_count'] == len(content)
    assert client.get(f"/api/resources/{resource['id']}").json() == resource


def test_binary_upload_preview_marks_binary(client):
    """RES-002: non-UTF-8 content is marked BINARY without interpretation; bytes read back identically."""
    content = bytes(range(256))
    resource = upload(client, name='firmware-chunk', kind='software', content=content)
    preview = client.get(f"/api/resources/{resource['id']}/preview").json()
    assert preview['encoding'] == 'BINARY' and preview['text_preview'] is None and preview['char_count'] is None
    assert preview['size_bytes'] == 256
    assert client.get(f"/api/resources/{resource['id']}/content").content == content


def test_upload_validates_base64_size_and_emptiness(client):
    """RES-003: invalid base64, empty content and content beyond the documented bound are rejected 422."""
    body = upload_body()
    body['content_base64'] = 'not valid base64!!'
    assert client.post('/api/resources', json=body).status_code == 422
    body['content_base64'] = base64.b64encode(b'').decode()
    assert client.post('/api/resources', json=body).status_code == 422
    body['content_base64'] = base64.b64encode(b'x' * (MAX_CONTENT_BYTES + 1)).decode()
    assert client.post('/api/resources', json=body).status_code == 422
    body['kind'] = 'executable'
    body['content_base64'] = base64.b64encode(b'ok').decode()
    assert client.post('/api/resources', json=body).status_code == 422


def test_versioning_appends_immutable_new_versions(client):
    """RES-004: new version appends record with family/predecessor links; identical content is rejected 409."""
    first = upload(client, content=b'content revision one')
    second = client.post(f"/api/resources/{first['id']}/versions",
                         json={'content_base64': base64.b64encode(b'content revision two').decode(),
                               'note': 'Fixture revision'}).json()
    assert second['version'] == 2 and second['family_id'] == first['family_id']
    assert second['predecessor_id'] == first['id'] and second['version_note'] == 'Fixture revision'
    identical = client.post(f"/api/resources/{first['id']}/versions",
                            json={'content_base64': base64.b64encode(b'content revision two').decode()})
    assert identical.status_code == 409
    versions = client.get(f"/api/resources/{first['id']}/versions").json()
    assert [v['version'] for v in versions] == [1, 2]
    assert client.get(f"/api/resources/{second['id']}/content").content == b'content revision two'


def test_links_are_references_to_existing_targets(client, reviewer):
    """RES-005: link attaches resource by reference to an existing task; duplicates 409; unlink keeps history."""
    project, evidence = seed(client, reviewer)
    task_id = task(client, project, evidence)
    resource = upload(client)
    link = client.post(f"/api/resources/{resource['id']}/links", json={'target_kind': 'task', 'target_id': task_id})
    assert link.status_code == 201
    assert link.json()['state'] == 'active'
    assert client.post(f"/api/resources/{resource['id']}/links",
                       json={'target_kind': 'task', 'target_id': task_id}).status_code == 409
    unlinked = client.post(f"/api/resources/{resource['id']}/unlink", json={'link_id': link.json()['id']})
    assert unlinked.status_code == 200 and unlinked.json()['state'] == 'unlinked' and unlinked.json()['unlinked_at']
    assert client.post(f"/api/resources/{resource['id']}/links",
                       json={'target_kind': 'task', 'target_id': task_id}).status_code == 201
    history = client.get(f"/api/resources/{resource['id']}/links").json()
    assert [l['state'] for l in history] == ['unlinked', 'active']


def test_link_targets_must_exist_and_resource_must_be_active(client, reviewer):
    """RES-006: unknown task/project target 404; project link works; deactivated resource blocks links 409."""
    project, evidence = seed(client, reviewer)
    resource = upload(client)
    assert client.post(f"/api/resources/{resource['id']}/links",
                       json={'target_kind': 'task', 'target_id': 'missing'}).status_code == 404
    project_link = client.post(f"/api/resources/{resource['id']}/links",
                               json={'target_kind': 'project', 'target_id': project['id']})
    assert project_link.status_code == 201
    deactivated = client.post(f"/api/resources/{resource['id']}/deactivate", headers=reviewer,
                              json={'confirm': True, 'reason': 'Fixture retirement for link test'})
    assert deactivated.status_code == 200
    assert client.post(f"/api/resources/{resource['id']}/links",
                       json={'target_kind': 'task', 'target_id': 'any'}).status_code == 409


def test_compare_identical_and_different_content(client):
    """RES-007: byte comparison identifies identical content and computes real prefix/suffix for differences."""
    left = upload(client, name='left', content=b'COMMON-PREFIX-alpha')
    right = upload(client, name='right', content=b'COMMON-PREFIX-alpha')
    identical = client.get(f"/api/resources/{left['id']}/compare/{right['id']}").json()
    assert identical['relation'] == 'IDENTICAL'
    assert identical['common_prefix_bytes'] == len(b'COMMON-PREFIX-alpha')
    changed = upload(client, name='changed', content=b'COMMON-PREFIX-beta')
    different = client.get(f"/api/resources/{left['id']}/compare/{changed['id']}").json()
    assert different['relation'] == 'DIFFERENT'
    assert different['common_prefix_bytes'] == len(b'COMMON-PREFIX-')
    assert different['common_suffix_bytes'] == 1  # 'alpha' and 'beta' share the trailing 'a'
    shorter = upload(client, name='shorter', content=b'COMMON-PREFIX-alp')
    trimmed = client.get(f"/api/resources/{left['id']}/compare/{shorter['id']}").json()
    assert trimmed['relation'] == 'DIFFERENT'
    assert trimmed['left_size_bytes'] == 19 and trimmed['right_size_bytes'] == 17  # 'alp' is one byte shorter than 'alpha'


def test_search_by_name_kind_state_and_hash_prefix(client):
    """RES-008: registry search matches name substrings case-insensitively, kind/state filters and sha256 prefixes."""
    first = upload(client, name='Bench Configuration A', kind='configuration', content=b'alpha')
    second = upload(client, name='bench log b', kind='log', content=b'beta')
    assert [r['id'] for r in client.get('/api/resources?query=bench').json()] == [first['id'], second['id']]
    assert [r['id'] for r in client.get('/api/resources?query=CONFIGURATION').json()] == [first['id']]
    assert [r['id'] for r in client.get('/api/resources?kind=log').json()] == [second['id']]
    by_hash = client.get(f"/api/resources?query={first['sha256'][:12]}").json()
    assert [r['id'] for r in by_hash] == [first['id']]
    assert client.get('/api/resources?query=zzz-no-match').json() == []


def test_deactivation_requires_reviewer_confirmation_and_retains_data(client, reviewer):
    """RES-009: reviewer confirm+reason deactivates whole family, 409 on repeat, blocks versions; content stays readable."""
    first = upload(client, content=b'v1 content')
    second = client.post(f"/api/resources/{first['id']}/versions",
                         json={'content_base64': base64.b64encode(b'v2 content').decode()}).json()
    assert client.post(f"/api/resources/{first['id']}/deactivate",
                       json={'confirm': True, 'reason': 'wrong role'}).status_code == 403
    assert client.post(f"/api/resources/{first['id']}/deactivate", headers=reviewer,
                       json={'confirm': False, 'reason': 'x' * 20}).status_code == 422
    deactivated = client.post(f"/api/resources/{first['id']}/deactivate", headers=reviewer,
                              json={'confirm': True, 'reason': 'Fixture retirement, data retained'})
    assert deactivated.status_code == 200
    assert client.post(f"/api/resources/{first['id']}/deactivate", headers=reviewer,
                       json={'confirm': True, 'reason': 'second attempt'}).status_code == 409
    versions = client.get(f"/api/resources/{first['id']}/versions").json()
    assert all(v['state'] == 'deactivated' for v in versions)
    assert client.post(f"/api/resources/{second['id']}/versions",
                       json={'content_base64': base64.b64encode(b'v3 content').decode()}).status_code == 409
    assert client.get(f"/api/resources/{first['id']}/content").content == b'v1 content'
    assert client.get(f"/api/resources/{second['id']}/content").content == b'v2 content'
    assert [r['id'] for r in client.get('/api/resources?state=deactivated').json()] == [first['id'], second['id']]


def test_emergency_stop_blocks_mutations_not_reads(client, reviewer):
    """RES-010: emergency stop blocks upload/version/link/deactivation 409; reads and compare stay available."""
    resource = upload(client, content=b'stable fixture content')
    assert client.post('/api/control/stop', headers=reviewer,
                       json={'active': True, 'reason': 'Fixture stop'}).status_code == 200
    assert client.post('/api/resources', json=upload_body(name='blocked')).status_code == 409
    assert client.post(f"/api/resources/{resource['id']}/versions",
                       json={'content_base64': base64.b64encode(b'new').decode()}).status_code == 409
    assert client.post(f"/api/resources/{resource['id']}/links",
                       json={'target_kind': 'project', 'target_id': 'x'}).status_code == 409
    assert client.post(f"/api/resources/{resource['id']}/deactivate", headers=reviewer,
                       json={'confirm': True, 'reason': 'blocked by stop'}).status_code == 409
    assert client.get(f"/api/resources/{resource['id']}/content").content == b'stable fixture content'
    assert client.get(f"/api/resources/{resource['id']}/compare/{resource['id']}").json()['relation'] == 'IDENTICAL'
    assert client.post('/api/control/stop', headers=reviewer,
                       json={'active': False, 'reason': 'Fixture stop cleared'}).status_code == 200


def test_corrupt_blob_fails_closed_on_content_preview_and_compare(client, tmp_path):
    """RES-011: corrupted resource blob fails 503 on content/preview/compare; metadata and hash stay inspectable."""
    resource = upload(client)
    blob_path = tmp_path / 'objects' / (resource['key'] + '.blob')
    assert blob_path.exists()
    blob_path.write_bytes(b'corrupted resource bytes')
    assert client.get(f"/api/resources/{resource['id']}/content").status_code == 503
    assert client.get(f"/api/resources/{resource['id']}/preview").status_code == 503
    other = upload(client, name='other', content=b'other content')
    assert client.get(f"/api/resources/{resource['id']}/compare/{other['id']}").status_code == 503
    assert client.get(f"/api/resources/{resource['id']}").json()['sha256'] == resource['sha256']


def test_roles_operator_writes_reviewer_deactivates_both_read(client, reviewer):
    """RES-012: operator-only upload/version/link/unlink (reviewer 403); reviewer-only deactivation (operator 403); both read."""
    resource = upload(client)
    assert client.post('/api/resources', json=upload_body(name='reviewer attempt'),
                       headers=reviewer).status_code == 403
    assert client.post(f"/api/resources/{resource['id']}/versions", headers=reviewer,
                       json={'content_base64': base64.b64encode(b'nope').decode()}).status_code == 403
    assert client.post(f"/api/resources/{resource['id']}/links", headers=reviewer,
                       json={'target_kind': 'project', 'target_id': 'x'}).status_code == 403
    assert client.post(f"/api/resources/{resource['id']}/deactivate",
                       json={'confirm': True, 'reason': 'operator cannot deactivate'}).status_code == 403
    assert client.get('/api/resources', headers=reviewer).status_code == 200
    assert client.get(f"/api/resources/{resource['id']}/content", headers=reviewer).status_code == 200


def test_unlink_validates_link_identity_and_state(client, reviewer):
    """RES-013: unlink rejects unknown link 404, foreign-resource link 404 and double unlink 409."""
    project, evidence = seed(client, reviewer)
    first = upload(client, name='first resource')
    second = upload(client, name='second resource')
    link = client.post(f"/api/resources/{first['id']}/links",
                       json={'target_kind': 'project', 'target_id': project['id']}).json()
    assert client.post(f"/api/resources/{first['id']}/unlink", json={'link_id': 'missing'}).status_code == 404
    assert client.post(f"/api/resources/{second['id']}/unlink", json={'link_id': link['id']}).status_code == 404
    assert client.post(f"/api/resources/{first['id']}/unlink", json={'link_id': link['id']}).status_code == 200
    assert client.post(f"/api/resources/{first['id']}/unlink", json={'link_id': link['id']}).status_code == 409


def test_audit_covers_resource_lifecycle(client, reviewer):
    """RES-014: audit trail records upload, versioning, linking, unlinking and confirmed deactivation with actors."""
    project, evidence = seed(client, reviewer)
    resource = upload(client)
    client.post(f"/api/resources/{resource['id']}/versions",
                json={'content_base64': base64.b64encode(b'second revision').decode()})
    link = client.post(f"/api/resources/{resource['id']}/links",
                       json={'target_kind': 'project', 'target_id': project['id']}).json()
    client.post(f"/api/resources/{resource['id']}/unlink", json={'link_id': link['id']})
    client.post(f"/api/resources/{resource['id']}/deactivate", headers=reviewer,
                json={'confirm': True, 'reason': 'Fixture lifecycle complete'})
    entries = [e for e in client.get('/api/audit', headers=reviewer).json() if e['event'].startswith('resource.')]
    assert [e['event'] for e in entries] == ['resource.uploaded', 'resource.versioned', 'resource.linked',
                                             'resource.unlinked', 'resource.deactivated']
    assert all(e['actor'] == 'operator' for e in entries[:-1]) and entries[-1]['actor'] == 'reviewer'


def test_preview_truncates_long_text(client):
    """RES-015: text preview truncates at 200 characters while reporting the true character count."""
    content = ('abcdefghij' * 50).encode()
    resource = upload(client, name='long-text', kind='log', content=content)
    preview = client.get(f"/api/resources/{resource['id']}/preview").json()
    assert preview['encoding'] == 'TEXT'
    assert len(preview['text_preview']) == 200 and preview['char_count'] == 500


def test_hash_is_verifiable_against_returned_metadata(client):
    """RES-016: returned sha256/size match an independent recomputation over the downloaded bytes."""
    content = b'independently verifiable fixture payload'
    resource = upload(client, content=content)
    downloaded = client.get(f"/api/resources/{resource['id']}/content").content
    assert hashlib.sha256(downloaded).hexdigest() == resource['sha256']
    assert len(downloaded) == resource['size_bytes']
