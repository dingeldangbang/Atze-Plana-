# API reference (generated)

Source: `app/main.py` and Pydantic models. Regenerate: `python scripts/docs.py`.

## Shared contract

- JSON over HTTP; bearer token for every `/api/` route. Health is public.
- One workspace, two shared role tokens; no per-user identity or tenant isolation.
- No application rate limiter. Production requires a trusted ingress with body/time/rate limits.
- 401 missing/invalid token; 403 wrong role; 404 absent entity; 409 state conflict;
  422 schema/reference validation; 503 unavailable/locked storage. No external provider errors.
- Lists: `limit=1..100` (default 100), `offset>=0` (default 0), insertion order.
- Request and response field constraints are in [OpenAPI](../../openapi.yaml).
- Runnable creation example: [Quickstart](../../QUICKSTART.md).

| Method | Endpoint | Role | Request schema | Success response | Side effects / evidence requirements |
|---|---|---|---|---|---|
| GET | `/health` | public | — | `{"200": {"description": "Successful Response", "content": {"application/json": {"schema": {"additionalProperties": {"type": "string"}, "type": "object", "title": "Response Health Health Get"}}}}}` | None; read-only |
| GET | `/api/runtime` | both | — | `{"200": {"description": "Successful Response", "content": {"application/json": {"schema": {"additionalProperties": {"type": "string"}, "type": "object", "title": "Response Runtime Api Runtime Get"}}}}}` | None; read-only |
| GET | `/api/openapi.json` | both | — | `{"200": {"description": "Successful Response", "content": {"application/json": {"schema": {"additionalProperties": true, "type": "object", "title": "Response Specification Api Openapi Json Get"}}}}}` | None; read-only |
| POST | `/api/projects` | operator | ProjectInput | `{"201": {"description": "Successful Response", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Project"}}}}}` | Project + audit; no evidence requirement |
| GET | `/api/projects` | both | — | `{"200": {"description": "Successful Response", "content": {"application/json": {"schema": {"type": "array", "items": {"$ref": "#/components/schemas/Project"}, "title": "Response Projects Api Projects Get"}}}}}` | None; read-only |
| POST | `/api/evidence` | operator | EvidenceInput | `{"201": {"description": "Successful Response", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Evidence"}}}}}` | Store original text/hash/provenance + audit; existing project required; initially unverified |
| GET | `/api/evidence` | both | — | `{"200": {"description": "Successful Response", "content": {"application/json": {"schema": {"type": "array", "items": {"$ref": "#/components/schemas/Evidence"}, "title": "Response Evidence Api Evidence Get"}}}}}` | None; read-only |
| POST | `/api/evidence/{evidence_id}/review` | reviewer | Review | `{"200": {"description": "Successful Response", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Evidence"}}}}}` | One immutable manual evidence review + audit; reason required |
| POST | `/api/tasks` | operator | TaskInput | `{"201": {"description": "Successful Response", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Task"}}}}}` | Immutable task + audit; all evidence references must belong to project |
| GET | `/api/tasks` | both | — | `{"200": {"description": "Successful Response", "content": {"application/json": {"schema": {"type": "array", "items": {"$ref": "#/components/schemas/Task"}, "title": "Response Tasks Api Tasks Get"}}}}}` | None; read-only |
| POST | `/api/tasks/{task_id}/triage` | both | — | `{"200": {"description": "Successful Response", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Decision"}}}}}` | Decision snapshot in audit; verified evidence, confidence >=0.8, preconditions, no stop |
| POST | `/api/tasks/{task_id}/approve` | reviewer | ApprovalInput | `{"201": {"description": "Successful Response", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Approval"}}}}}` | Approval + audit only; current triage must require approval; never executes |
| GET | `/api/control/stop` | both | — | `{"200": {"description": "Successful Response", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Stop"}}}}}` | None; read-only |
| POST | `/api/control/stop` | reviewer | StopInput | `{"200": {"description": "Successful Response", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Stop"}}}}}` | Persist global stop + reason in audit; does not interrupt external processes |
| GET | `/api/audit` | reviewer | — | `{"200": {"description": "Successful Response", "content": {"application/json": {"schema": {"type": "array", "items": {"$ref": "#/components/schemas/Audit"}, "title": "Response Audit Log Api Audit Get"}}}}}` | None; read-only |
| POST | `/api/archive` | operator | ArchiveInput | `{"201": {"description": "Successful Response", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Archive"}}}}}` | Immutable UTF-8 archive + FTS + audit; existing project and same-project evidence references; stop blocks write |
| GET | `/api/archive` | both | — | `{"200": {"description": "Successful Response", "content": {"application/json": {"schema": {"type": "array", "items": {"$ref": "#/components/schemas/Archive"}, "title": "Response Archives Api Archive Get"}}}}}` | None; metadata only, immutable logical paths |
| GET | `/api/archive/{object_id}/content` | both | — | `{"200": {"description": "Successful Response", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ArchiveContent"}}}}}` | None; current tier read is size/hash verified, unavailable or corrupt returns 503 |
| GET | `/api/archive/resolve` | both | — | `{"200": {"description": "Successful Response", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ArchiveContent"}}}}}` | Resolve stable logical path, then read/hash-check current tier; never interprets path as host filename |
| POST | `/api/archive/{object_id}/relocate` | reviewer | MoveInput | `{"200": {"description": "Successful Response", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Archive"}}}}}` | Copy/fsync/verify before atomic location+audit switch; retains original; explicit reason; stop blocks; 507 capacity failure |
| GET | `/api/storage/health` | both | — | `{"200": {"description": "Successful Response", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/StorageHealth"}}}}}` | None; real configured filesystem usage only, unsupported tiers report null values |
| POST | `/api/cache` | operator | CacheInput | `{"201": {"description": "Successful Response", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/CacheObject"}}}}}` | Task-bound disposable UTF-8 blob + expiry + audit; no FTS or execution; stop blocks write |
| GET | `/api/cache/{object_id}/content` | both | — | `{"200": {"description": "Successful Response", "content": {"application/json": {"schema": {"type": "string", "title": "Response Cache Content Api Cache  Object Id  Content Get"}}}}}` | None; hash verified text, expired returns 410; save as archive explicitly before expiry |
| POST | `/api/cache/cleanup` | reviewer | CleanupInput | `{"200": {"description": "Successful Response", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/CleanupResult"}}}}}` | Commit expired-cache tombstones then delete only expired cache blobs, audit; retry safe; archives never selected; stop blocks |
| POST | `/api/memory` | operator | MemoryInput | `{"201": {"description": "Successful Response", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Memory"}}}}}` | Append-only memory + FTS + audit; fact category requires verified linked evidence; commit SHA is attested not GitHub-validated |
| GET | `/api/memory` | both | — | `{"200": {"description": "Successful Response", "content": {"application/json": {"schema": {"type": "array", "items": {"$ref": "#/components/schemas/Memory"}, "title": "Response Memories Api Memory Get"}}}}}` | None; recorded assertions, not automatic truth validation |
| POST | `/api/context/query` | both | RetrievalQuery | `{"200": {"description": "Successful Response", "content": {"application/json": {"schema": {"items": {"$ref": "#/components/schemas/RetrievalHit"}, "type": "array", "title": "Response Query Api Context Query Post"}}}}}` | Read-only lexical FTS retrieval within project; source/hash/offsets/live evidence; no execution authorization |
| POST | `/api/context/reindex` | reviewer | ReindexInput | `{"200": {"description": "Successful Response", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ReindexResult"}}}}}` | Rebuild one page of derived FTS chunks from hash-verified archive originals or memory; audit; stop blocks; failure rolls back page |

## Static surface

`GET /` and `GET /static/{path}` serve the dashboard without authentication.
No embedded workspace data; browser uses same-origin bearer-authenticated API requests.
Bounded JSON UTF-8 archive/cache ingestion is supported; no binary upload, MCP transport, shell, or execute endpoint.
