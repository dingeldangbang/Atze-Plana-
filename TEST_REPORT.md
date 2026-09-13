# Test Report — master implementation increment

Stand 2026-09-14, baseline fbf4be9. Baseline executed after inspecting interrupted changes: **120 passed**, two visible deprecation warnings, **97.78%** Core statement coverage; Python wheel/sdist build successful. Three new harness tests verify explicit opt-in, missing artifacts and actual byte/hash/symlink checks. They are NOT model-inference tests.

Evidence: reports/master-baseline.log, reports/coverage.xml, reports/junit.xml, reports/master-build.log. Actual JUnit records individual outcomes/times. No fabricated test table replaces execution.

New integration gates initially NOT RUN: pinned local model inference in isolated CI namespace; actual Android SDK APK build/sign/install/start/instrumentation. Local Android build preflight BLOCKED: no SDK. Direct HF metadata/download TLS connection from sandbox failed, secure document fetch obtained metadata/license only; no weights/inference success inferred.

Existing unit/API/storage/RAG/Memory/Challenge/Triage/permissions/privacy/TLS/socket regressions remain mandatory. Browser E2E, genuine hardware/USB/BLE/ADB repair, Unity, Bright Data, complete Agent Builder/MCP and sandbox escape tests remain NOT RUN/NOT IMPLEMENTED. Final results must reference actually executed CI runs and artifacts.
