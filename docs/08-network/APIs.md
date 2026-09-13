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

## Static surface

`GET /` and `GET /static/{path}` serve the dashboard without authentication.
No embedded workspace data; browser uses same-origin bearer-authenticated API requests.
No Swagger CDN, webhooks, WebSockets, upload, shell, or execute endpoint.
