# Native Android Core Client — development scope

Real native Java Activity, no WebView, demo data, generated device list or fake backend. Only implemented operation: explicit authenticated **HTTPS GET /api/runtime** against the user's chosen Core. No operational endpoint/token compiled into APK. UI says disconnected until actual response; failures clear status, never show replacement data.

## Security / permissions
Only INTERNET permission. No USB/BLE/ADB/Fastboot/EDL/Serial/Filesystem/Payment privileges or agent tools. `ExternalDataGateway.java` is the only Android outbound path; HTTPS origin only, no userinfo/path/query/fragment, explicit user consent button. Token used only as Authorization for chosen server, not stored/logged/backed up; field cleared after click/destruction, autofill/save disabled. RAM/String erasure cannot be guaranteed. FLAG_SECURE limits screenshots/recents capture. Backup disabled.

System CA + hostname verification retained; socket protocols restricted to TLS1.2/1.3. No trust-all CA, debug cleartext or redirect fallback. 10s per blocking operation and 16KiB response bound, not a hard global deadline. No cookies, browser, search or model inference. The configured Core necessarily receives the auth credential; user must choose their own trusted Core. No per-user backend identities, durable client egress ledger or production mobile-security assessment added. All-platform privacy/sandbox gates remain open.

## Build / dependencies
Official Android SDK platform android-35, build-tools35.0.0, Java javac/jar/keytool and zip. No Gradle/Maven wrapper or external app dependency. `scripts/build_android.sh` genuinely compiles Java→DEX, packages Android manifests, aligns and signs app/test APKs, then verifies signatures and computes SHA256. Local missing SDK/JDK blocks; never writes a success APK placeholder. Artifacts under ignored `reports/android/`.

`ANDROID_HOME=/actual/sdk scripts/build_android.sh` (or ANDROID_SDK_ROOT). Build status and install status are separate. CI `.github/workflows/android.yml` provisions required SDK components using hosted runner's accepted SDK installation, creates a temporary key, starts a real Android emulator, installs both APKs, launches Activity and executes custom instrumentation. No mocked Android runtime. The checked-in workflow is only configured test infrastructure: a current run artifact is required before a debug APK is reported TESTED or VALIDATED. Ephemeral signing key removed; rebuilds have different signatures, so no in-place update guarantee. DO NOT use as production signing identity. No AAB yet. No distribution/release merely because debug build passes.

## Tests / outputs
Instrumentation checks actual Activity launch/empty state, rejection of plaintext/unsafe origins, token clearing, and enabled TLS protocol set. It does NOT prove a real remote Core TLS exchange, sensor/device bridge, Honeywell compatibility, Android repair or physical hardware. Test data are synthetic and never sent over network. UI assertion failure fails instrumentation; CI requires explicit `atze_result=PASS`.

Deliver only actual `atze-app-debug.apk`, `atze-test-debug.apk` (test package, not customer app), SHA256SUMS, apksigner verification, installed package/launch/instrumentation evidence. Consult [APK release report](../APK_RELEASE_REPORT.md) for the outcome of actual runs, not this workflow definition. Production/full-platform release remains BLOCKED.
