"""HTTP domain API. A future MCP adapter must call the same permission-bound services."""
from datetime import datetime, timezone
from fastapi import Depends, HTTPException, Query
from app.context import create_memory, retrieve, index_text
from app.context_models import (ArchiveInput, Archive, ArchiveContent, MoveInput, MemoryInput, Memory,
                                RetrievalQuery, RetrievalHit, CacheInput, CacheObject, CleanupInput,
                                CleanupResult, StorageHealth, ReindexInput, ReindexResult)
from app.store import get, listing, audit
from app.storage import guard


def register_context_api(app, store, storage, actor, operator, reviewer, connection):
    db_dependency = Depends(connection, scope='function')

    def contract(role, effects):
        return {'x-role': role, 'x-side-effects': effects}

    @app.post('/api/archive', response_model=Archive, status_code=201, tags=['storage'],
              openapi_extra=contract('operator', 'Immutable UTF-8 archive + FTS + audit; existing project and same-project evidence references; stop blocks write'))
    def archive_create(body: ArchiveInput, who=Depends(operator), db=db_dependency):
        return storage.archive(db, body, who)

    @app.get('/api/archive', response_model=list[Archive], tags=['storage'],
             openapi_extra=contract('both', 'None; metadata only, immutable logical paths'))
    def archives(limit: int = Query(100, ge=1, le=100), offset: int = Query(0, ge=0), who=Depends(actor), db=db_dependency):
        return listing(db, 'archive', limit, offset)

    @app.get('/api/archive/{object_id}/content', response_model=ArchiveContent, tags=['storage'],
             openapi_extra=contract('both', 'None; current tier read is size/hash verified, unavailable or corrupt returns 503'))
    def archive_content(object_id: str, who=Depends(actor), db=db_dependency):
        value = get(db, 'archive', object_id)
        return {'object': value, 'content': storage.checked(value).decode()}

    @app.get('/api/archive/resolve', response_model=ArchiveContent, tags=['storage'],
             openapi_extra=contract('both', 'Resolve stable logical path, then read/hash-check current tier; never interprets path as host filename'))
    def resolve(logical_path: str = Query(min_length=1, max_length=512), who=Depends(actor), db=db_dependency):
        import json
        row = db.execute("SELECT body FROM records WHERE kind='archive' AND json_extract(body,'$.logical_path')=?", (logical_path,)).fetchone()
        if row is None:
            raise HTTPException(404, 'Logical archive path not found')
        value = json.loads(row[0])
        return {'object': value, 'content': storage.checked(value).decode()}

    @app.post('/api/archive/{object_id}/relocate', response_model=Archive, tags=['storage'],
              openapi_extra=contract('reviewer', 'Copy/fsync/verify before atomic location+audit switch; retains original; explicit reason; stop blocks; 507 capacity failure'))
    def relocate(object_id: str, body: MoveInput, who=Depends(reviewer), db=db_dependency):
        return storage.move(db, object_id, body, who)

    @app.get('/api/storage/health', response_model=StorageHealth, tags=['storage'],
             openapi_extra=contract('both', 'None; real configured filesystem usage only, unsupported tiers report null values'))
    def health(who=Depends(actor), db=db_dependency):
        return storage.health(db)

    @app.post('/api/cache', response_model=CacheObject, status_code=201, tags=['cache'],
              openapi_extra=contract('operator', 'Task-bound disposable UTF-8 blob + expiry + audit; no FTS or execution; stop blocks write'))
    def cache_create(body: CacheInput, who=Depends(operator), db=db_dependency):
        return storage.cache(db, body, who)

    @app.get('/api/cache/{object_id}/content', response_model=str, tags=['cache'],
             openapi_extra=contract('both', 'None; hash verified text, expired returns 410; save as archive explicitly before expiry'))
    def cache_content(object_id: str, who=Depends(actor), db=db_dependency):
        value = get(db, 'cache', object_id)
        if value['state'] != 'active' or datetime.fromisoformat(value['expires_at']) <= datetime.now(timezone.utc):
            raise HTTPException(410, 'Disposable cache has expired')
        return storage.checked(value).decode()

    @app.post('/api/cache/cleanup', response_model=CleanupResult, tags=['cache'],
              openapi_extra=contract('reviewer', 'Commit expired-cache tombstones then delete only expired cache blobs, audit; retry safe; archives never selected; stop blocks'))
    def cleanup(body: CleanupInput, who=Depends(reviewer)):
        return storage.cleanup(store, body, who)

    @app.post('/api/memory', response_model=Memory, status_code=201, tags=['context'],
              openapi_extra=contract('operator', 'Untrusted non-authoritative memory + FTS + audit; direct fact/decision writes blocked, use challenged result adoption; commit SHA is attested not GitHub-validated'))
    def memory_create(body: MemoryInput, who=Depends(operator), db=db_dependency):
        return create_memory(db, body, who)

    @app.get('/api/memory', response_model=list[Memory], tags=['context'],
             openapi_extra=contract('both', 'None; recorded assertions, not automatic truth validation'))
    def memories(limit: int = Query(100, ge=1, le=100), offset: int = Query(0, ge=0), who=Depends(actor), db=db_dependency):
        return listing(db, 'memory', limit, offset)

    @app.post('/api/context/query', response_model=list[RetrievalHit], tags=['context'],
              openapi_extra=contract('both', 'Read-only lexical FTS retrieval within project; source/hash/offsets/live evidence; no execution authorization'))
    def query(body: RetrievalQuery, who=Depends(actor), db=db_dependency):
        return retrieve(db, body)

    @app.post('/api/context/reindex', response_model=ReindexResult, tags=['context'],
              openapi_extra=contract('reviewer', 'Rebuild one page of derived FTS chunks from hash-verified archive originals or memory; audit; stop blocks; failure rolls back page'))
    def reindex(body: ReindexInput, who=Depends(reviewer), db=db_dependency):
        import json
        guard(db)
        rows = db.execute("SELECT kind,body FROM records WHERE kind IN ('archive','memory') ORDER BY seq LIMIT ? OFFSET ?", (body.limit, body.offset)).fetchall()
        keys = []
        for kind, document in rows:
            value = json.loads(document)
            text = storage.checked(value).decode() if kind == 'archive' else value['content']
            index_text(db, value['project_id'], value['id'], text)
            keys.append(value['id'])
        audit(db, who, 'context.reindexed', 'global', {'source_ids': keys, 'reason': body.reason})
        return {'indexed_ids': keys, 'next_offset': body.offset + len(keys)}
