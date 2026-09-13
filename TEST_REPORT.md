# Test Report — master implementation increment

Stand 2026-09-14, baseline fbf4be9. Baseline executed after inspecting interrupted changes: **120 passed**, two visible deprecation warnings, **97.78%** Core statement coverage; Python wheel/sdist build successful. Three new harness tests verify explicit opt-in, missing artifacts and actual byte/hash/symlink checks. They are NOT model-inference tests.

Evidence: reports/master-baseline.log, reports/coverage.xml, reports/junit.xml, reports/master-build.log. Actual JUnit records individual outcomes/times. No fabricated test table replaces execution.

New integration gates initially NOT RUN: pinned local model inference in isolated CI namespace; actual Android SDK APK build/sign/install/start/instrumentation. Local Android build preflight BLOCKED: no SDK. Direct HF metadata/download TLS connection from sandbox failed, secure document fetch obtained metadata/license only; no weights/inference success inferred.

Existing unit/API/storage/RAG/Memory/Challenge/Triage/permissions/privacy/TLS/socket regressions remain mandatory. Browser E2E, genuine hardware/USB/BLE/ADB repair, Unity, Bright Data, complete Agent Builder/MCP and sandbox escape tests remain NOT RUN/NOT IMPLEMENTED. Final results must reference actually executed CI runs and artifacts.

## Tatsächlicher lokaler Modell-CI-Nachweis
[Run34790257577](https://github.com/dingeldangbang/Atze-Plana-/actions/runs/34790257577) PASS. Originale Check-Annotation via authentifizierter GitHub API gelesen: Qwen/Qwen2.5-0.5B-Instruct-GGUF revision9217f5db79a29953eb74d5343926648285ec7e67; Gewichte SHA25674a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db, Runtime SHA256bcbf6a304f85dd5acceee4afde432d4d183120a32dccad9ca8dcb05687575d40. UID1001, LOOPBACK_ONLY_NO_EXTERNAL_ROUTE. Echter Modelloutput `READY`, gemessener einzelner Requestablauf0.906s, children_stopped=true. Kein allgemeiner Geschwindigkeits-/Qualitäts-/Hardware-/Agentnachweis. Download der ZIP-Artefakte in Arena scheitert am Blob-Transport; Check-Annotationen sind zugänglich und wurden tatsächlich gelesen.
