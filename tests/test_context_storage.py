"""Synthetic text/filesystem tests, not device or SD hardware validation."""
import hashlib
import json
import os
import sqlite3
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.storage import Storage
from app.store import Store
from conftest import seed, task


@pytest.fixture
def tiered(settings, reviewer, tmp_path):
    sd = tmp_path / 'simulated-sd'
    sd.mkdir()
    config = replace(settings, sd_root=sd)
    with TestClient(create_app(config)) as client:
        client.headers['Authorization'] = 'Bearer ' + config.operator_token
        yield client, config, reviewer


def archive(client, project, content='  motor observation\n', **overrides):
    body = {'project_id': project['id'], 'relative_path': 'tests/measurement.txt', 'content': content, **overrides}
    response = client.post('/api/archive', json=body)
    assert response.status_code == 201, response.text
    return response.json()


def query(client, project, word='motor'):
    response = client.post('/api/context/query', json={'project_id': project['id'], 'query': word})
    assert response.status_code == 200, response.text
    return response.json()


def expire(config, key):
    with sqlite3.connect(config.db_path) as db:
        value = json.loads(db.execute('SELECT body FROM records WHERE id=?', (key,)).fetchone()[0])
        value['expires_at'] = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
        db.execute('UPDATE records SET body=? WHERE id=?', (json.dumps(value), key))


def test_archive_original_namespace_and_restart(tiered):
    """STO-001: original UTF-8 whitespace/hash survives storage and restart; duplicate namespace cannot overwrite."""
    client, config, reviewer = tiered
    p, e = seed(client, reviewer)
    original = '  Motor Größe ⚙\n\n'
    a = archive(client, p, original, evidence_ids=[e['id']])
    assert a['logical_path'] == f"/project/{p['id']}/tests/measurement.txt"
    assert a['sha256'] == hashlib.sha256(original.encode()).hexdigest()
    assert a['size_bytes'] == len(original.encode())
    content_url = f"/api/archive/{a['id']}/content"
    assert client.get(content_url).json()['content'] == original
    assert client.get('/api/archive').json()[0] == a
    assert client.post('/api/archive', json={'project_id': p['id'], 'relative_path': 'tests/measurement.txt', 'content': 'overwrite'}).status_code == 409
    with TestClient(create_app(config)) as restarted:
        restarted.headers.update(client.headers)
        assert restarted.get(content_url).json()['content'] == original
        assert query(restarted, p)[0]['sha256'] == a['sha256']


@pytest.mark.parametrize('path', ['/absolute', '../escape', 'a/../b', 'a//b', './file', 'a\\b', 'a/%2e%2e/b', 'a\x00b'])
def test_logical_path_rejection(client, reviewer, path):
    """STO-002: absolute, traversal, empty, encoded or platform-specific path segments are rejected."""
    p, e = seed(client, reviewer)
    response = client.post('/api/archive', json={'project_id': p['id'], 'relative_path': path, 'content': 'test'})
    assert response.status_code == 422


def test_copy_verify_switch_retains_source_and_citations(tiered):
    """STO-003: reviewer relocation preserves original, hash and namespace; retrieval resolves the new location."""
    client, config, reviewer = tiered
    p, e = seed(client, reviewer)
    a = archive(client, p, evidence_ids=[e['id']])
    url = f"/api/archive/{a['id']}/relocate"
    body = {'target': 'sd', 'reason': 'Synthetic tier migration'}
    assert client.post(url, json=body).status_code == 403
    moved = client.post(url, headers=reviewer, json=body)
    assert moved.status_code == 200, moved.text
    b = moved.json()
    assert b['retained_copies'] == [{'tier': a['tier'], 'key': a['key']}]
    assert b['logical_path'] == a['logical_path'] and b['sha256'] == a['sha256']
    resolved = client.get('/api/archive/resolve', params={'logical_path': a['logical_path']}).json()
    assert resolved['object']['tier'] == 'sd' and resolved['content'] == '  motor observation\n'
    assert client.get('/api/archive/resolve', params={'logical_path': '/etc/passwd'}).status_code == 404
    storage = Storage(config)
    assert storage.checked(a) == storage.checked(b)
    hit = query(client, p)[0]
    assert hit['location'] == 'sd' and hit['allowed_for_action'] is False
    assert hit['evidence_state'] == 'verified'
    assert client.post(url, headers=reviewer, json=body).status_code == 409
    audit = client.get('/api/audit', headers=reviewer).json()
    assert audit[-1]['details']['source_retained'] is True


def test_destination_failure_leaves_authoritative_source(tiered, monkeypatch):
    """STO-004: failed destination verification cannot switch the index or destroy the original."""
    client, config, reviewer = tiered
    p, e = seed(client, reviewer)
    a = archive(client, p)
    original_read = Storage.read
    monkeypatch.setattr(Storage, 'read', lambda self, tier, key: b'corrupt' if tier == 'sd' else original_read(self, tier, key))
    response = client.post(f"/api/archive/{a['id']}/relocate", headers=reviewer, json={'target': 'sd', 'reason': 'Fault injection'})
    assert response.status_code == 503
    assert client.get('/api/archive').json()[0] == a
    assert client.get(f"/api/archive/{a['id']}/content").json()['content'] == '  motor observation\n'
    assert query(client, p)[0]['location'] == 'local'


def test_archive_audit_failure_rolls_back_metadata(tiered):
    """STO-005: failed relocation audit rolls back location; unreferenced copies may remain, original remains readable."""
    client, config, reviewer = tiered
    p, e = seed(client, reviewer)
    a = archive(client, p)
    with sqlite3.connect(config.db_path) as db:
        db.execute("CREATE TRIGGER fail_move BEFORE INSERT ON records WHEN NEW.kind='audit' AND json_extract(NEW.body,'$.event')='archive.relocated' BEGIN SELECT RAISE(ABORT, 'test audit failure'); END")
    with pytest.raises(sqlite3.IntegrityError):
        client.post(f"/api/archive/{a['id']}/relocate", headers=reviewer, json={'target': 'sd', 'reason': 'Fault injection'})
    assert client.get('/api/archive').json()[0] == a
    assert Storage(config).checked(a) == b'  motor observation\n'


def test_corruption_and_symlink_are_not_followed(tiered, tmp_path):
    """STO-006: corrupt source blocks reads/migration; object symlink cannot expose arbitrary host files."""
    client, config, reviewer = tiered
    p, e = seed(client, reviewer)
    a = archive(client, p)
    file = config.db_path.parent / 'objects' / (a['key'] + '.blob')
    file.write_bytes(b'corrupt')
    url = f"/api/archive/{a['id']}/content"
    assert client.get(url).status_code == 503
    assert client.post(f"/api/archive/{a['id']}/relocate", headers=reviewer, json={'target': 'sd', 'reason': 'Corrupt source'}).status_code == 503
    other = tmp_path / 'private.txt'
    other.write_text('must not be exposed')
    file.unlink()
    file.symlink_to(other)
    assert client.get(url).status_code == 503
    assert 'must not be exposed' not in client.get(url).text


def test_capacity_policy_and_unavailable_tier(tiered, monkeypatch):
    """STO-007: capacity policy falls back to configured SD, rejects all-full tiers and reports unavailable remote tiers honestly."""
    client, config, reviewer = tiered
    p, e = seed(client, reviewer)
    health = client.get('/api/storage/health').json()
    assert next(t for t in health['tiers'] if t['tier'] == 'local')['total_bytes'] > 0
    for name in ['ram', 'server', 'cloud']:
        tier = next(t for t in health['tiers'] if t['tier'] == name)
        assert tier['available'] is False and tier['used_percent'] is None
    original_usage = Storage.usage
    def usage(self, tier):
        if tier == 'local':
            return {'free_bytes': 1024, 'used_percent': 99, 'total_bytes': 100000, 'used_bytes': 98976}
        return original_usage(self, tier)
    monkeypatch.setattr(Storage, 'usage', usage)
    a = archive(client, p)
    assert a['tier'] == 'sd'
    monkeypatch.setattr(Storage, 'usage', lambda self, tier: {'free_bytes': 1, 'used_percent': 99})
    assert client.post('/api/archive', json={'project_id': p['id'], 'relative_path': 'full.txt', 'content': 'test'}).status_code == 507


def test_stop_blocks_storage_writes(tiered):
    """STO-008: stop blocks archive/cache creation, relocation and cleanup; existing originals remain readable."""
    client, config, reviewer = tiered
    p, e = seed(client, reviewer)
    key = task(client, p, e)
    a = archive(client, p)
    client.post('/api/control/stop', headers=reviewer, json={'active': True, 'reason': 'Stop storage test'})
    assert client.post('/api/archive', json={'project_id': p['id'], 'relative_path': 'new.txt', 'content': 'test'}).status_code == 409
    assert client.post('/api/cache', json={'task_id': key, 'content': 'test'}).status_code == 409
    assert client.post(f"/api/archive/{a['id']}/relocate", headers=reviewer, json={'target': 'sd', 'reason': 'Denied'}).status_code == 409
    assert client.post('/api/cache/cleanup', headers=reviewer, json={'reason': 'Denied'}).status_code == 409
    assert client.get(f"/api/archive/{a['id']}/content").status_code == 200


def test_cache_expiry_cleanup_and_archive_separation(tiered):
    """CACHE-001: only expired cache is deleted; archive, live cache and memory survive; repeat cleanup is safe."""
    client, config, reviewer = tiered
    p, e = seed(client, reviewer)
    key = task(client, p, e)
    a = archive(client, p)
    cache = client.post('/api/cache', json={'task_id': key, 'content': '  temporary\n', 'ttl_seconds': 60}).json()
    live = client.post('/api/cache', json={'task_id': key, 'content': 'live'}).json()
    assert client.get(f"/api/cache/{cache['id']}/content").json() == '  temporary\n'
    assert query(client, p, 'temporary') == []
    expire(config, cache['id'])
    assert client.get(f"/api/cache/{cache['id']}/content").status_code == 410
    health = client.get('/api/storage/health').json()
    assert health['cache_expired_bytes'] == len('  temporary\n'.encode())
    assert health['cache_active_bytes'] == 4
    assert health['archive_logical_bytes'] == a['size_bytes']
    assert client.post('/api/cache/cleanup', json={'reason': 'Denied'}).status_code == 403
    result = client.post('/api/cache/cleanup', headers=reviewer, json={'reason': 'Expired only'}).json()
    assert result['deleted_ids'] == [cache['id']]
    assert client.post('/api/cache/cleanup', headers=reviewer, json={'reason': 'Retry'}).json()['deleted_ids'] == []
    assert client.get(f"/api/archive/{a['id']}/content").status_code == 200
    assert client.get(f"/api/cache/{live['id']}/content").json() == 'live'


def test_cache_delete_crash_retry(tiered):
    """CACHE-002: failure after physical deletion leaves a committed tombstone and cleanup can retry missing file."""
    client, config, reviewer = tiered
    p, e = seed(client, reviewer)
    key = task(client, p, e)
    c = client.post('/api/cache', json={'task_id': key, 'content': 'disposable'}).json()
    expire(config, c['id'])
    with sqlite3.connect(config.db_path) as db:
        db.execute("CREATE TRIGGER fail_delete BEFORE INSERT ON records WHEN NEW.kind='audit' AND json_extract(NEW.body,'$.event')='cache.deleted' BEGIN SELECT RAISE(ABORT, 'delete crash'); END")
    with pytest.raises(sqlite3.IntegrityError):
        client.post('/api/cache/cleanup', headers=reviewer, json={'reason': 'Fault injection'})
    assert client.get(f"/api/cache/{c['id']}/content").status_code == 410
    with sqlite3.connect(config.db_path) as db:
        db.execute('DROP TRIGGER fail_delete')
    assert client.post('/api/cache/cleanup', headers=reviewer, json={'reason': 'Retry'}).json()['deleted_ids'] == [c['id']]


def test_memory_fact_inference_and_live_evidence(tiered):
    """MEM-001: fact creation needs verified evidence; inference remains inference even with verified sources; retrieval is never execution permission."""
    client, config, reviewer = tiered
    p, e = seed(client, reviewer, verified=False)
    base = {'project_id': p['id'], 'category': 'fact', 'content': 'motor tested', 'evidence_ids': [e['id']]}
    assert client.post('/api/memory', json=base).status_code == 409
    assert client.post('/api/memory', json={**base, 'evidence_ids': []}).status_code == 409
    inference = client.post('/api/memory', json={**base, 'category': 'inference'}).json()
    assert inference['state'] == 'recorded'
    assert query(client, p)[0]['evidence_state'] == 'unverified'
    client.post(f"/api/evidence/{e['id']}/review", headers=reviewer, json={'state': 'verified', 'reason': 'Test review'})
    hit = query(client, p)[0]
    assert hit['category'] == 'inference' and hit['evidence_state'] == 'verified' and not hit['allowed_for_action']
    assert client.post('/api/memory', json=base).status_code == 201
    assert len(client.get('/api/memory').json()) == 2
    assert client.post('/api/memory', headers=reviewer, json=base).status_code == 403


def test_retrieval_positions_project_filter_and_query_safety(tiered):
    """RAG-001: lexical retrieval returns real character spans/hashes, isolates projects and treats FTS syntax as words."""
    client, config, reviewer = tiered
    p, e = seed(client, reviewer)
    other = client.post('/api/projects', json={'name': 'Other'}).json()
    original = 'prefix ' * 200 + 'motor unique suffix'
    a = archive(client, p, original)
    hits = query(client, p, 'motor unique')
    assert hits and hits[0]['text'] == original[hits[0]['start_char']:hits[0]['end_char']]
    assert hits[0]['sha256'] == a['sha256'] and hits[0]['source_id'] == a['id']
    assert hits[0]['evidence_state'] == 'unverified'
    assert query(client, other, 'motor unique') == []
    assert query(client, p, '" OR *') == []
    assert client.post('/api/context/query', json={'project_id': p['id'], 'query': '***'}).status_code == 422
    assert client.post('/api/context/query', json={'project_id': p['id'], 'query': 'motor', 'limit': 31}).status_code == 422


def test_cross_project_refs_and_commit_attestation(tiered):
    """MEM-002: foreign/duplicate evidence and task references are rejected; commit is format-checked attestation only."""
    client, config, reviewer = tiered
    p, e = seed(client, reviewer)
    key = task(client, p, e)
    other = client.post('/api/projects', json={'name': 'Other'}).json()
    base = {'project_id': other['id'], 'category': 'inference', 'content': 'motor'}
    assert client.post('/api/memory', json={**base, 'evidence_ids': [e['id']]}).status_code == 422
    assert client.post('/api/memory', json={**base, 'task_id': key}).status_code == 422
    assert client.post('/api/memory', json={**base, 'commit_sha': 'not-a-sha'}).status_code == 422
    assert client.post('/api/memory', json={**base, 'project_id': p['id'], 'evidence_ids': [e['id'], e['id']]}).status_code == 422
    result = client.post('/api/memory', json={**base, 'project_id': p['id'], 'task_id': key, 'commit_sha': 'a'*40})
    assert result.status_code == 201
    assert query(client, p)[0]['commit_sha'] == 'a'*40


def test_missing_sd_and_root_boundaries(settings, tmp_path, reviewer):
    """STO-009: missing SD never gets created, overlapping/symlink roots fail startup, absent tier cannot receive data."""
    with pytest.raises(ValueError):
        Storage(replace(settings, sd_root=settings.db_path.parent / 'objects'))
    with pytest.raises(ValueError):
        Storage(replace(settings, sd_root=settings.db_path.parent / 'objects' / 'nested'))
    alias = tmp_path / 'alias'
    alias.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError):
        Storage(replace(settings, storage_root=alias))
    missing = tmp_path / 'absent-sd'
    config = replace(settings, sd_root=missing)
    with TestClient(create_app(config)) as client:
        client.headers['Authorization'] = 'Bearer ' + config.operator_token
        p, e = seed(client, reviewer)
        a = archive(client, p)
        assert not missing.exists()
        assert client.post(f"/api/archive/{a['id']}/relocate", headers=reviewer, json={'target': 'sd', 'reason': 'Missing tier'}).status_code == 507


def test_additive_upgrade_preserves_v1_data(settings):
    """MIG-001: v0.1 records/control survive additive FTS/namespace schema initialization and repeated startup."""
    with sqlite3.connect(settings.db_path) as db:
        db.execute('CREATE TABLE records (seq INTEGER PRIMARY KEY AUTOINCREMENT,id TEXT UNIQUE NOT NULL,kind TEXT NOT NULL,body TEXT NOT NULL)')
        db.execute('CREATE TABLE control (id INTEGER PRIMARY KEY CHECK(id=1), active INTEGER NOT NULL, reason TEXT NOT NULL)')
        db.execute("INSERT INTO control VALUES(1,1,'Existing stop')")
        db.execute('INSERT INTO records(id,kind,body) VALUES(?,?,?)', ('legacy', 'project', json.dumps({'id': 'legacy', 'name': 'Existing', 'description': '', 'created_at': '2026-01-01T00:00:00Z'})))
    Store(settings.db_path)
    Store(settings.db_path)
    with sqlite3.connect(settings.db_path) as db:
        assert db.execute('SELECT active,reason FROM control').fetchone() == (1, 'Existing stop')
        assert db.execute("SELECT COUNT(*) FROM records WHERE id='legacy'").fetchone()[0] == 1


def test_reindex_from_originals_and_rejected_evidence(tiered):
    """RAG-002: paginated reviewer rebuild restores derived FTS; rejected evidence remains rejected without granting use."""
    client, config, reviewer = tiered
    p, e = seed(client, reviewer, verified=False)
    a = archive(client, p, evidence_ids=[e['id']])
    m = client.post('/api/memory', json={'project_id': p['id'], 'category': 'inference', 'content': 'motor hypothesis', 'evidence_ids': [e['id']]}).json()
    client.post(f"/api/evidence/{e['id']}/review", headers=reviewer, json={'state': 'rejected', 'reason': 'Synthetic rejection'})
    assert all(hit['evidence_state'] == 'rejected' for hit in query(client, p))
    with sqlite3.connect(config.db_path) as db:
        db.execute('DELETE FROM context_fts')
    assert query(client, p) == []
    body = {'reason': 'Restore derived index', 'limit': 1}
    assert client.post('/api/context/reindex', json=body).status_code == 403
    first = client.post('/api/context/reindex', headers=reviewer, json=body).json()
    assert first == {'indexed_ids': [a['id']], 'next_offset': 1}
    second = client.post('/api/context/reindex', headers=reviewer, json={**body, 'offset': 1}).json()
    assert second['indexed_ids'] == [m['id']]
    assert len(query(client, p)) == 2


def test_index_and_nonregular_storage_fail_closed(tiered):
    """STO-010: missing index source, oversized blobs and nonregular objects fail closed rather than return false content."""
    client, config, reviewer = tiered
    p, e = seed(client, reviewer)
    a = archive(client, p)
    file = config.db_path.parent / 'objects' / (a['key'] + '.blob')
    file.write_bytes(b'x' * 262145)
    assert client.get(f"/api/archive/{a['id']}/content").status_code == 503
    file.unlink()
    os.mkfifo(file)
    assert client.get(f"/api/archive/{a['id']}/content").status_code == 503
    with sqlite3.connect(config.db_path) as db:
        db.execute('DELETE FROM records WHERE id=?', (a['id'],))
    assert client.post('/api/context/query', json={'project_id': p['id'], 'query': 'motor'}).status_code == 503


@pytest.mark.parametrize('endpoint', ['/api/projects', '/api/archive'])
def test_transaction_finalization_precedes_success(tiered, monkeypatch, endpoint):
    """TX-001: failure at transaction finalization returns 503, never a success sent before commit; mutation rolls back."""
    from contextlib import contextmanager
    client, config, reviewer = tiered
    p, e = seed(client, reviewer)
    original = Store.connect
    @contextmanager
    def fail_on_exit(self):
        with original(self) as db:
            yield db
            raise sqlite3.OperationalError('Injected commit-time failure')
    monkeypatch.setattr(Store, 'connect', fail_on_exit)
    body = {'name': 'Must roll back'} if endpoint == '/api/projects' else {'project_id': p['id'], 'relative_path': 'rollback.txt', 'content': 'not committed'}
    response = client.post(endpoint, json=body)
    assert response.status_code == 503
    with sqlite3.connect(config.db_path) as db:
        assert db.execute("SELECT COUNT(*) FROM records WHERE kind='project'").fetchone()[0] == 1
        assert db.execute("SELECT COUNT(*) FROM records WHERE kind='archive'").fetchone()[0] == 0
