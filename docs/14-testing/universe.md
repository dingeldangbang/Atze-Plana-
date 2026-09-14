# Universe — audit et scoped test execution

## Purpose / scope
`.github/agents/universal-engineer.md` is an agent instruction profile, **not** an implemented autonomous agent or a permission grant. `scripts/universe_audit.sh` invokes a standard-library Python inventory; `tests/universe_harness.py` executes supported explicit commands only after `--execute`. These are development tools, not application endpoints, MCP servers or a sandbox.

## Inputs / outputs / dependencies
Python3.11+, Git; test/build tools and dependencies for the selected repository. Audit inspects tracked and non-ignored untracked files, including pending restored work. Source extensions/manifests are explicit in `scripts/universe.py`. No crawling .venv/node_modules/ignored files, backups, runtime data or credential-like paths. Maximum2MiB/file; UTF-8/symlink/size/read errors are visible signals. It writes reports/inventory.md and inventory.json (paths, Git state, hashes, line numbers and signal codes, not source excerpts).

Recognizes multiple root Python/Node/Rust/Go/Gradle stacks and identifies Android and nested manifests. Other platform/nested scopes block execution acceptance until reviewed. It does not confidently infer all frameworks, dead/duplicate code, broken imports or UI coverage. REAL means no detected heuristic, **not** functional validation. TODO/STUB indications are review candidates; exception-handler `pass` is not automatically a stub.

Harness writes reports/universe-YYYY-MM-DD.md/json with fixed command vectors, start/end, status/exit/time and observed new Python wheel/sdist hashes. Existing artifacts do not establish a new build. Raw subprocess stdout/stderr is discarded, since it can contain secrets. Commands execute once per run, with per-command timeouts and process-group cleanup on POSIX. Historical same-day reports are overwritten, initialized BLOCKED before executing. Concurrent harness runs in the same worktree are not supported.

## Commands / configuration / permission
```sh
bash scripts/universe_audit.sh
python tests/universe_harness.py                         # plan only; exits 2, not success
python tests/universe_harness.py --execute --scope core  # actual selected Core execution
python tests/universe_harness.py --execute --scope all   # full detected scope; missing Android contract BLOCKED
python tests/test_universe.py                           # isolated standard-library tooling regression
```

Run with the prepared virtualenv (`.venv/bin/python`) when dependencies are there. No dependency installation, downloads, health-port scans, model/device actions, signing or deployments are triggered by the inventory. Harness tests/builds are arbitrary repository code: review and authorize the repository first and use appropriate external isolation. Removing ATZE-prefixed environment values prevents accidental inheritance by built-in Core fixtures, **not** universal secret erasure or network/filesystem sandboxing. Package managers/build backends can access the network; default environment and host credentials outside this prefix are not isolated.

`--scope core` in this repository selects pytest, real Python build, docs check, reality gate and the self-created isolated HTTP/Challenge smoke. Existing separate browser/model/Android CI remains authoritative for those additional scopes; this harness does not silently claim those gates. Node invokes existing test/build scripts without --if-present, Rust real cargo test/build --locked, Go test/build and root Gradle wrapper test/assemble. Missing command/tool/contract, bad exit, timeout or missing new Python artifact => BLOCKED/exit2. Passed selected commands => PARTIAL/exit0, never universal READY. An exit0 is not proof of meaningful tests or full requirements; agent review remains necessary.

## Backup and edits
No automatic implementation/replacement. Before an approved eligible source edit: `python scripts/universe.py --backup path/to/source.py`. This stores a private SHA256-named immutable copy in backups and verifies bytes; existing corrupt copy, secret-like path, symlink or outside-root path fails. Existing backup names are never overwritten. Backups are ignored and excluded from audit/upload. New files have no fabricated predecessor. Backup is not a whole-project or crash-recovery solution. Host-level concurrent path replacement is outside these application-level checks.

## Failure, tests and validation
UNI-001–007 use explicit isolated synthetic source fixtures and real Git/files/processes: exclusions, untracked scope, no excerpts, AST candidates/syntax, verified backup/corruption/symlink rejection, safe report writing, multi-stack/unknown detection, actual exit/timeout and plan-only no-execution. No simulated operational providers. Test command failures preserve non-PASS report state, never old successful output. Exceptions are reported by type, not raw potentially sensitive messages. No automatic OOM/disconnect/network-down/full-UI test coverage inferred.

`.github/workflows/universe.yml` runs on push/PR with read-only repository permission, pinned existing action revisions, explicit dependency setup and timeout. Uploads only inventory/summary JSON/Markdown, not backups/raw process logs. A checked-in workflow definition is not proof of a completed remote workflow; current execution evidence must be reported separately.

## Executed integration, 2026-09-14
Fresh local dependency installation completed. Seven tooling regression cases PASS; total repository suite **145 PASS /98.04% app coverage**, two known warnings. The tooling itself is not counted in app-only coverage. Actual `--execute --scope core` ran pytest, Python package build, docs consistency, reality gate and isolated HTTP/worker smoke successfully; verdict PARTIAL by design. No hardware/provider/browser/OOM proof derived from this result. Remote Universe workflow execution is a separate gate, not inferred from the YAML.

Workspace recovery: local Git metadata initially pointed at the initial commit although previously delivered source files were present. Remote still held87c6726. Fetched the same session branch, verified ancestor/empty staging, aligned metadata only with `git reset --mixed FETCH_HEAD` and verified SHA256 of all117 eligible working files unchanged. No working-file replacement, force-push or other branch used.
