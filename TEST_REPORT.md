# Test Report — executed master increment

Stand 2026-09-14. **120 pytest-Fälle bestanden**, zwei sichtbare Deprecation-Warnungen, 97,78% Core-Statement-Coverage. Baseline fbf4be9 nach Analyse erneut gebaut/getestet, Änderungen danach ebenfalls geprüft. JUnit enthält tatsächliche Einzelfälle/Zeiten/Fehler; lokale Reports werden nicht als Produktionsdaten versioniert.

## Konkrete Nachweise
| Gate | Ergebnis / Evidence |
|---|---|
| Core unit/API/storage/triage/privacy/regression | 120 PASS; reports/master-tests.log, junit.xml, coverage.xml |
| Dokumentation/OpenAPI | PASS, vier generierte Produkte/acht feste Envvariablen/lokale Dateilinks |
| Python build / dependency audit / pip check / JS syntax / no-fake gate | PASS; keine bekannten Dependencytreffer beim ausgeführten Lauf |
| Real HTTP Challenge/Core smoke | 29 geprüfte Responses +2 separate Worker, normal und python -O PASS |
| Real local HF model | [34790349657](https://github.com/dingeldangbang/Atze-Plana-/actions/runs/34790349657) PASS, Qwen0.5B Q4_K_M + llama.cpp b10948, Hashes geprüft, tatsächliche Ausgabe READY |
| Modell-Netzwerkgrenze | UID1001, LOOPBACK_ONLY_NO_EXTERNAL_ROUTE, keine geerbten Betriebscredentials, children_stopped=true |
| Modell-Requestzeit | Ein konkreter Test0.881s inkl. Requestablauf, keine allgemeine Leistungs-/2GB-Garantie |
| Android SDK compile/typecheck/sign/build | PASS in [34790349728](https://github.com/dingeldangbang/Atze-Plana-/actions/runs/34790349728) |
| Emulator install/start/native instrumentation | PASS; tatsächlich installierte/gestartete App, keine reine statische Codeprüfung |
| Lokale Androidtools | BLOCKED, kein JDK/SDK in Sandbox; CI-Nachweis nicht als lokaler Build ausgegeben |
| Browser E2E/physische Devices/Honeywell/Unity/BrightData/AgentBuilder/MCP/Sandbox escape | NOT RUN / NOT IMPLEMENTED |

Core-CI für Branchstand b791222 separat unter Actions; Modell-/Androidjobs bauen den PR-Merge. Modellmanifest pins revision9217f5db79a29953eb74d5343926648285ec7e67, Gewichtesha25674a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db, Runtime-sha256bcbf6a304f85dd5acceee4afde432d4d183120a32dccad9ca8dcb05687575d40. Originale Ergebnis-Check-Annotationen tatsächlich via GitHub API gelesen: reports/real-model-final-evidence.json und reports/android-verified-evidence.json. ZIP-Download in diese Sandbox scheitert am Blobtransport; Originalartefakte existieren im erfolgreichen CI-Lauf. [APK-Dateien/Hashes](APK_RELEASE_REPORT.md).

## Testgrenzen / Fehlerhistorie
Drei Harness-Unit-Tests prüfen Opt-in, fehlende Artefakte und echte Byte-/Hash-/Symlinkgrenzen, nicht Inferenz. Erst der separate echte Modelllauf erfüllt den einfachen Inferenztest. Der bisherige Transport-Receiptserver wird nicht als Modell ausgegeben. Modelloutput ist unchallenged, autoritative Übernahme weiterhin blockiert.

Android zuerst Timeout, dann echte Diagnose des AVD-Pfadfehlers, korrigiert und erneut ausgeführt. Keine Testentfernung oder fingiertes PASS. App-Instrumentation prüft Empty State, Ablehnung unsicherer Origins/Klartext, Tokenleeren und TLS-Protokollmenge, nicht eine reale API-Session zu einem entfernten Core. SDK-Emulatornachweis ist kein physischer Device-Test.

Volle Master-Abnahme weiterhin BLOCKED; siehe [Master-Matrix](docs/00-overview/master-acceptance.md).
