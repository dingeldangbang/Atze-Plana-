# Pinned real local model validation

[ADR-006](../adr/ADR-006-real-worker-and-android-validation.md). Core/model APIs already exist; this adds an actual integration harness, not a provider mock.

## Inputs / provenance
`validation/local-model.lock.json` pins official Qwen/Qwen2.5-0.5B-Instruct-GGUF revision9217f5db79a29953eb74d5343926648285ec7e67, Q4_K_M file491400032bytes, advertised LFS SHA256. Apache2 license text inspected at pinned URL. Runtime official llama.cpp b10948 ubuntu-x64 archive with GitHub-advertised digest. Its `execution` field deliberately remains `NOT_RUN_BY_LOCK`; a static lock cannot claim downloaded bytes or inference. Metadata is EXTERNAL_SOURCE; only a successful file check proves bytes match it. No automatic legal/quality/production approval. No weights/library binaries in Git.

## Stages / exact meaning
1. Explicit CI workflow stages public artifacts over verified HTTPS only, no platform input/credential; SHA256+size verified. Failed download => BLOCKED, no substituted model.
2. Validator refuses missing/modified artifacts, no opt-in or root execution. Requires a Linux namespace with exactly loopback and no external route. Namespace setup privileged, actual Core/model/test non-root. Parent egress probe uses documentation address and no payload. Filesystem/syscall isolation is NOT proved by network namespace.
3. Extract verified official archive with safe tar data filter, run actual llama-server with local GGUF, CPU2threads/context1024/parallel1, auth key file0600, no web UI/MCP proxy. No inherited platform/GitHub/HF secrets. Never accepts an arbitrary server URL or model download fallback.
4. Start actual disposable Core HTTP server with fresh keys and test-mode storage. Prove default DENY, register concrete tested metadata, explicit exact-context reviewer consent and local allowlist, then run short synthetic prompt through real model adapter.
5. Actual output must satisfy documented simple instruction (`READY`). Report stores this synthetic actual output and elapsed time, not a general quality score. Must stay DRAFT_UNCHALLENGED; no Result/autoadoption/action, Triage remains blocked.
6. Terminate children and remove temporary DB/keys/extraction. Structured report only; no operational prompts/raw logs/keys uploaded. Crash/invalid response => FAIL, prior PASS overwritten. No ADB/MCP/AgentBuilder success inferred.

## Running
`python scripts/validate_local_model.py --allow-fixtures --model /verified/file.gguf --runtime-archive /verified/runtime.tar.gz` inside a non-root loopback-only namespace. Never run namespace provisioning inside the ordinary application. Standard pytest only tests harness refusal/hash behavior and does not claim model inference. `.github/workflows/local-model.yml` separately performs actual model integration; reports bound to its commit. Direct HF TLS download failed in Arena sandbox, no TLS bypass attempted. The CI run's outcome must be recorded before claiming real inference.

## Known limits
Declared license/revision and fixed artifacts are not a model-security audit. CPU time/hardware refer only to concrete worker, no 2GB-wide guarantee. Loopback port selection has a local allocation race and fails closed if occupied; dedicated ephemeral runner required. Socket15s timeout in Core is not a hard total inference deadline. No persistent local model installation in operational preview, no smolagents/MCP/multimodel challenge, no full Sandbox/permission escalation proof. Model weights remain transient CI artifacts and are not distributed as part of the APK.
