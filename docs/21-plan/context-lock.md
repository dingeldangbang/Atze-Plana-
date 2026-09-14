# PLAN — immutable task context, not truth or permission

[ADR-007](../adr/ADR-007-plan-context-lock.md), [OpenAPI](../../openapi.yaml), [test catalogue](../14-testing/test-catalog.md). Added after executed120-test baseline05ea6d5; no existing record migration/deletion, no operational seed data. Browser validation/actual model results are recorded in the root reports, not assumed from implementation.

## Purpose / inputs / outputs
One PLAN per actual task, project derived from task. Each append-only version contains title, one of project/task/object/device/test/research/software/repair, and1–16 references `{kind: evidence|memory|archive, id, relationship: input|reference|supports|contradicts}`. These are declared organizational relations, **not proven support/contradiction or device integrations**. One resource cannot be selected twice. Same project required; task-scoped Memory only for this task. Project-scoped Memory is allowed. Cache is disposable, never selectable. Only existing UTF-8 text archives, not arbitrary filesystem paths/uploads/binary/PDF/CAD.

Manifest: PLAN/project/task identity, context/title, full task hash, resource IDs/type/declared relation, content SHA256/size, full source-record hash, actual source URL or logical path where applicable, source version/time/review state, attached evidence record hashes/review states, unique dependency byte count, stop revision. At most1MiB selected+dependency bytes and64 distinct Evidence dependencies. Source metadata and dependency reviews participate, not just text. Hash canonical UTF-8 JSON with sorted keys/no whitespace. No source-content copy into manifest (titles/URLs/path metadata can themselves be sensitive). Source `content_integrity=VERIFIED` refers only to checked bytes **at version capture**; `truth_status=UNKNOWN`. Manual Evidence review is preserved separately, not promoted into measured truth. Current validity must be read from status, not an old manifest.

Version creation resolves every source or fails atomically; append requires latest `expected_version_id`. No update/delete/rebase endpoint. Reviewer lock requires exact latest `version_id` and matching `manifest_hash`, recomputed against actual sources. New lock supersedes previous lock. Reviewer reason is hashed, not copied into PLAN audit. Revocation appends a separate record and remains possible under stop. Relock is a new explicit reviewer decision and invalidates previous challenge/request bindings. A changed source needs a **new version**, not a silent refresh of old manifest.

## Dependencies / configuration / permissions
FastAPI/Pydantic, generic SQLite records (`BEGIN IMMEDIATE`, sequential connection), Store audit, existing Storage.checked, no new packages/mandatory environment. Existing ATZE storage configuration applies. Same workspace-wide operator/reviewer credentials; this does not add multi-tenant/project-specific ACLs. Operator: create/version; reviewer: lock/revoke; both: authenticated reads. No network calls, provider configuration or hardware rights. Service transactions roll back on source/audit errors. Blobs are read and checked, never rewritten by PLAN.

## API contract
All routes documented with authentication, schemas, side effects in generated [API reference](../08-network/APIs.md); bearer tokens required. JSON extra fields forbidden. No application rate limiter (ingress required); lists default100/max100, offset supported, versions newest first.

| Method/path | Role | Input/output / side effect |
|---|---|---|
| POST /api/plans | operator | task_id + version content →201 PLAN identity, first immutable version+audit |
| GET /api/plans | either | limit/offset → identities only; fetch live status separately |
| GET /api/plans/{id}/versions | either | limit/offset → stored version/manifest history, not current validation |
| POST /api/plans/{id}/versions | operator | expected_version_id + content →201 new version; prior lock stale |
| POST /api/plans/{id}/locks | reviewer | version_id, manifest_hash, reason →201 lock+audit; no task approval |
| POST /api/plan-locks/{id}/revoke | reviewer | reason → appended revocation+audit; no in-flight recall |
| GET /api/plans/{id}/status | either | live CURRENT/UNLOCKED/SUPERSEDED/REVOKED/STALE/BLOCKED, reason, identity/hash, allowed_for_action always false |

Errors:401 authentication,403 role,404 missing resource,409 stop/duplicate PLAN/outdated expected version/hash/duplicate revocation,413 bounded context/dependency scope,422 schema/duplicate/foreign project/task,503 source/storage integrity unavailable. Live status returns200 with BLOCKED/STALE reason when verification fails; this is **not** success permission. SQLite/OSError mapped503; malformed host-edited internal JSON is outside supported API and can fail500, never a successful decision fallback.

## Mandatory downstream checks
Challenge policy **challenge-2-context** deliberately invalidates pre-upgrade reports, even tasks without PLAN; run worker/Core from same source and request a new challenge. No automatic substitute report. Stop every old Core/worker before upgrade; mixed-version/rolling operation against the same DB is unsupported. Old binaries do not enforce PLAN. Rollback only to a compatible implementation or an explicitly quarantined pre-PLAN backup, never silently serve post-PLAN data through old code. Task with PLAN adds live gate to the snapshot/fingerprint. Worker independently emits blocking `PLAN_CONTEXT_NOT_CURRENT` for non-current context. Claim, completion, Why, Triage, approval, adoption and decision-Memory retrieval pass the actual Storage verifier. Archive verifier omitted internally → BLOCKED. No recursive Memory-to-decision truth promotion.

Selected Memory/archive prose is not semantically certified by deterministic worker. Current challenge remains bounded to submitted structured claims and actual Evidence; PLAN adds integrity/provenance dependency, not an LLM/research/causality validator. A relevant claim still needs proper Evidence, alternatives and risk handling. Missing semantic/hardware verification remains a full-platform release gap.

AI requests for a task with PLAN **must** supply current `plan_lock_id` and no separate evidence_ids/memory_ids. Selected text includes source ID/type/SHA/whole-text character offsets/declared relation, marked untrusted. Existing≤8 resources and model/policy context budgets still apply (PLAN's16 does not increase inference allowance). Any source selection upgrades effective classification to at least CONFIDENTIAL. Full selected text is secret-scanned; no partial extraction/fake fallback. Explicit reviewer inference consent, task read restriction, local/default-deny policy, model allowlists and gateway TLS remain mandatory. Saved context hash is recomputed before consent/transport to detect stored-text corruption. PLAN binding rechecked during preparation and immediately before transport under serialized DB gate; newly added PLAN also blocks previously prepared legacy requests. Output remains DRAFT_UNCHALLENGED; no tools or auto-adoption.

## Example / user workflow
Create genuine project/task/sources through existing APIs; do not treat instructional values as source evidence. In dashboard: connect as operator → select actual task and1–16 real resources → save. Inspect version and hashes. Connect as reviewer → inspect current source bindings → explicitly lock with reason. Then submit relevant Result to separate Challenge, Triage and any required approval. For inference, add returned lock ID to AIRequest and explicitly consent to exact context hash. Source/version change or revoke requires refreshing version/lock/challenge/approval as applicable.

API request shape (variables must come from actual authenticated responses; not executable sample data):
```
POST /api/plans
{task_id: TASK_ID, title: YOUR_TITLE, context_type: "research",
 resources: [{kind: "archive", id: ACTUAL_ARCHIVE_ID, relationship: "reference"}]}
POST /api/plans/PLAN_ID/locks
{version_id: LATEST_VERSION_ID, manifest_hash: RETURNED_SHA256, reason: YOUR_REVIEW_REASON}
```
This schematic uses variable names deliberately; exact valid JSON schemas/examples/error contracts are in OpenAPI. No secret credentials in examples.

UI uses textContent, no innerHTML. Lists show first100 per type; missing selected resources/non-input relationships require API editing rather than silent loss. Refresh/login clears unsaved PLAN draft; logout clears resource/manifest views. Separate session/request counters discard stale asynchronous responses. Lock/revoke buttons hit real reviewer routes, not simulated UI success. Android remains read-only Core status, no native PLAN editor.

## Validation / tests / failure recovery / limitations
PLAN-001–015 cover real files/SQLite/API/HTTP, source/role/scope/hash/byte limits, append/revoke/stop, approval/RAG invalidation, no-I/O AI refusal and secret scan. Test data/faults isolated, not operational fixtures. Real smoke uses41 checked responses and4 separate worker invocations, normal/-O. Optional `python scripts/smoke.py --allow-fixtures --browser --report reports/browser-plan.json` creates its own test Core and invokes installed real Chromium over CDP pipes; no browser dependency fallback or disabled sandbox. Local browser absence is BLOCKED. Actual model pipeline also checks a locked archive and revoked queued request using pinned loaded weights; results only after execution.

On stale: inspect actual source changes, append reviewed version, new reviewer lock, new independent challenge and any approval. On corruption: restore verified original or capture new legitimate source, not edit hash to conceal error. Status is live re-evaluation, not a persistent filesystem-change watcher: exact restored source bytes/metadata can match old version again; explicit revocations and stop revisions never revive. Host changes between checks cannot be observed retroactively. SQLite and filesystem not jointly atomic; in-flight operations cannot be recalled. OS/admin access outside application boundary; no tamper-proof/signed audit, at-rest encryption, universal DLP, full leases/HITL executor, MCP/device/CAD integration or2GB performance validation. These gaps remain BLOCKED, not unlocked by CURRENT.

### Important service-function mapping
All functions inherit the dependencies/configuration/security/failure/validation/limitations above; direct Python calls are not a separately authenticated API.

| Function | Purpose / inputs → outputs | Authority / tests |
|---|---|---|
| manifest | DB+task PLAN+refs+storage+metadata → canonical hashes + untrusted full texts | internal verifier, no grant; PLAN001/004/005/012–014 |
| create_plan / append_version / revise_plan | operator content + expected latest version → immutable identity/version/audit | role enforced at API; guard stop/transaction; PLAN001/002/008/015 |
| create_lock / revoke_lock | reviewer exact manifest/reason → new lock or revocation | no action privilege; PLAN002/003/006/007 |
| status / task_gate | current PLAN/task + storage → live binding state, always no action | read/verify only; PLAN003/005/007 |
| locked_context | actual task + requested lock + storage → current binding and selected source texts | fails closed, not consent; PLAN009–011 |
