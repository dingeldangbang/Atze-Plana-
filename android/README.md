# Native Android Core Workspace — 0.2-dev

Native Java Activity, no WebView, demo records, embedded Python server or agent. This is a **partial, server-dependent client**, not the complete platform. Full-platform delivery remains BLOCKED. See [current APK evidence](../APK_RELEASE_REPORT.md) and [remaining modules](../docs/00-overview/roadmap.md).

## Actually connected operations

| UI | Existing Core endpoint | Scope |
|---|---|---|
| Authorize visible session | `GET /api/runtime` | Real response required before workspace opens |
| Project directory / selection | `GET /api/projects?limit=20&offset=N` | Workspace-wide pages; choose project for task form |
| Create project | `POST /api/projects` | Operator; name/description; explicit confirmation |
| Task directory | `GET /api/tasks?limit=20&offset=N` | Workspace-wide pages, project and task IDs shown |
| Create task | `POST /api/tasks` | Operator; title/project/action/existing evidence IDs/explicit prerequisites |
| Request triage | `POST /api/tasks/{id}/triage` | Both roles; explicit confirmation, audit entry, **never execution** |
| PLAN directory / current status | `GET /api/plans?limit=20&offset=N`, `GET /api/plans/{id}/status` | Read-only; CURRENT is context binding, not truth/permission |

No new server endpoint or OpenAPI contract. Project/task creation registers primary inputs; it is not authoritative fact/decision adoption. Existing mandatory Result → Challenge → Triage → Reviewer → Adoption gates remain server-side. Missing evidence/Challenge blocks even READ. Action labels including flash/payment are **declarations only**, not device/payment adapters. Reviewer credentials cannot create projects/tasks. The server is authoritative about roles and current state; the client does not invent a role or successful result.

Native evidence entry/review, PLAN editing/locking, Result submission, Challenge operations, reviewer approval/adoption, model configuration, MCP calls, storage management, offline sync and a bundled Core are **not included**. Existing web/API functionality remains available separately; it is not falsely presented as native integration. Device/Repair/Agent/Cloud/Unity/IoT modules are still missing.

## Use

1. Install only `atze-app-debug.apk` on an authorized Android 8+ device (minSdk26). Test APK is not the user app.
2. Independently operate the Python Core and separate Challenge worker according to [Quickstart](../QUICKSTART.md). Use a trusted HTTPS ingress with an Android-trusted certificate. No Core URL, credentials or provider access are embedded in the APK.
3. Enter **your own** Core HTTPS origin, no path/query/userinfo. Enter an Operator or Reviewer token and explicitly authorize this visible session. The chosen Core necessarily receives token and submitted fields.
4. Load projects or create one as Operator; select it, then register a task. Confirm each mutation with its destination and payload. Existing evidence IDs may be entered; none are invented. Triage does not execute anything.
5. Lists are workspace-wide, 20 entries per page, not a selected-project filter. PLAN status requires an existing PLAN created via the Core web/API.
6. Disconnect or background the app to clear session credentials, records, selection and drafts. Re-enter token on return. There is no disk storage or saved instance restoration. A sent request cannot be recalled; after ambiguous network/write failure inspect lists before resubmitting. No automatic retry.

## Security / permissions

Only INTERNET permission. No USB/BLE/ADB/Serial/Filesystem/Payment privileges or generic executor. `ExternalDataGateway.java` is the sole outbound path: HTTPS origin validation, fixed method/route allowlist, system CA and hostname checks, TLS1.2/1.3 only, redirects and response caching disabled. No cookies, fallback, external browser or model inference. Auth tokens are printable non-space ASCII, 32–4096 characters; no log/persistence/backup/autofill. Token input clears after authorization; explicitly consented credential remains in RAM until disconnect/background. In-flight request closures can retain credentials until transport ends. Java String erasure cannot be guaranteed.

FLAG_SECURE covers Activity and mutation confirmation dialogs. Backup disabled. Forms are not saved; text input suggestions disabled where applicable. OS/keyboard compromise and privileged debuggers remain outside this boundary. Development APK is debuggable, **not suitable for production credentials/data**.

Requests bounded to 64KiB, responses to 256KiB with JSON content-type requirement. 10s connect/read timeouts plus a checked 30s response-read deadline, **not a hard total request/writing/cancellation deadline**. Failures clear result views rather than showing old records as current. A failed mutation can have committed on the server; no idempotency guarantee or retry is added. New endpoint families require explicit allowlist changes and tests.

No production mobile-security assessment, per-user backend identity, durable egress ledger, encrypted offline data store or OS-wide privacy proof. Full-platform gates remain open.

## Build / signing / delivery

Official SDK platform android-35, build-tools35.0.0, javac/jar/keytool and zip. No Gradle/Maven/app dependency. `ANDROID_HOME=/actual/sdk scripts/build_android.sh` performs Java→DEX, manifest packaging, zipalign, ephemeral development signing, `apksigner verify`, SHA256 and source hashes. Known old artifacts/PASS records are invalidated **before preflight**; failed builds remove partial APKs. Artifacts remain under ignored `reports/`.

CI `.github/workflows/android.yml` runs build, real SDK emulator installation/launch and instrumentation. Merely defining it is not a success result. Signing key is temporary and removed, never uploaded. Every new build has a different identity; updates over previously signed versions may fail. Do not uninstall/delete existing app data without explicit consent. No stable release signing, AAB, store submission or GitHub release.

Original Actions artifact is the primary download (14-day retention). For clients whose network cannot reach the Actions blob host, the workflow additionally mirrors the **validated non-secret app APK only**, at most 27KB, in bounded check annotations. No signing key, token or user data is mirrored. Retrieve with:

```sh
python scripts/download_android.py --run-id ACTUAL_RUN_ID --revision FULL_SOURCE_SHA
```

Uses configured `gh` authentication and verifies selected successful workflow, exact built revision (for PR merge builds, its source parent is independently checked through the commit API), build/signature/emulator evidence, chunk consistency, byte size and SHA256 against the independent build annotation. Writes `reports/android-download/atze-app-debug.apk` only after those gates pass. This local byte verification is **not** a local apksigner or installation test. Consult the APK report for actual run ID/hash and outcomes.

## Test boundaries

Instrumentation: actual Activity launch, empty state, unauthenticated hidden workspace, token clearing on unsafe authorization and background lifecycle, disconnect, unsafe origin/route/header rejection, project/task payload validation/defaults and TLS protocol set. Synthetic inputs stay inside isolated instrumentation; no synthetic server/device provider.

Python regression: transport integrity/fail-closed retrieval, real shell preflight invalidation, and actual Core/SQLite create/list/pagination/role/audit/blocked-triage contracts. These are separate from native networking. **End-to-end Android↔Core HTTPS exchange and successful native mutation UI interactions are not yet validated.** Physical hardware, Honeywell, repair, live provider access and production readiness are NOT VALIDATED. No claims are inferred merely from test source.
