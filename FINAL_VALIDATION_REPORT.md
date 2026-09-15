## Android Workspace-Inkrement — 2026-09-15

Tatsächlich lokal ausgeführt (Python 3.11.2, isolierte Testdaten): **187 pytest-Fälle PASS**, App-Coverage **97,81%**, zwei vorhandene FastAPI/Starlette-Deprecation-Warnungen. Darunter 13 neue Fälle für APK-Transportintegrität, Stale-Artefakt-Invaliderung und tatsächlichen Core-/SQLite-Vertrag der nativen Operationen. `docs.py --check`, `reality_check.py`, Python sdist/wheel Build und pip-audit (keine bekannten Schwachstellen) PASS. Isolierter HTTP-Smoke mit separatem Challenge-Prozess: **43 Antworten geprüft, PASS** (`reports/workspace-smoke.json`). Kein Betriebssystem-/Hardware-/Providerbeweis.

Lokaler Android-Buildpreflight tatsächlich ausgeführt: **BLOCKED: Android SDK not configured**; JDK/SDK/ADB/KVM fehlen, offizieller SDK-Download TLS-Verbindungsfehler. Erster neuer Android-CI-Build/Emulatorlauf 34961828041 PASS, Download wegen gekürzter Annotationen abgelehnt; korrigierter Downloadlauf noch ausstehend. Ergebnisse ausschließlich im [aktuellen APK-Bericht](APK_RELEASE_REPORT.md). Alte Nachweise unten gelten nicht für neues Android-Java. Native End-to-End-HTTPS-Mutationen, physisches Gerät, neue Modell-/Browserabnahme in dieser lokalen Ausführung **NOT RUN** (Core-/Browser-CI 34961828096 hingegen tatsächlich PASS). Keine Vollplattformfreigabe.

---

## Bright Data MCP discovery addendum — 2026-09-14

Bounded real Streamable HTTP client/API added: OAuth bearer only, fixed TLS endpoint, initialize/initialized/tools-list plus session cleanup. Existing gateway, explicit reviewer/project/PUBLIC/provider-region permission, Privacy Lock, stop and current PLAN gate precede dispatch. Durable audit before I/O; no source/context/credentials in metadata reports. Only candidate names search_engine/scrape_as_markdown surfaced, **no tools/call or enabled tool permissions**. [Contract, sources, operations and limitations](docs/22-mcp/brightdata.md).

**169 local tests PASS /97.65% app coverage**,2 known warnings; baseline146 before changes.23 new parametrized cases use an actual verified local HTTPS peer with explicitly synthetic MCP responses, not Bright Data live results. Normal/-O HTTP smoke43 responses/four independent workers each; actual package build, docs/OpenAPI (nine fixed env variables), reality gate PASS. Final remote regression runs remain a separate gate and are recorded in PR after execution.

**Live Bright Data: NOT CONFIGURED / NOT VALIDATED.** No credentials supplied, no account registration, proxy changes, live scraping/search, purchases or provider success claimed. OAuth login/refresh, full MCP tools, permission leases and production privacy/sandbox gates still absent. Counterclaims such as “98% success/any webpage/anonymous” not promoted to facts. No deployment or release. This updates capability scope, not full-platform acceptance.

---

## Universe tooling addendum — 2026-09-14

Actual source inventory, agent instruction profile, opt-in multi-stack command harness and push/PR workflow added; [contract and limitations](docs/14-testing/universe.md). No automatic stub replacement, silent fallback, port scanning or deployment. **146 local tests PASS /98.04% app coverage**,2 known warnings; tooling uses8 real isolated Git/file/process tests. Real selected Core harness execution PASS for each command, overall **PARTIAL**, not universal READY. New wheel/sdist hashes and revision/dirty-state/inventory digest in reports/universe-2026-09-14.json; inventory reports contain no source excerpts. Existing application functions unchanged.

Initial Universe workflows on7b988d4 actually passed: [PR34798607416](https://github.com/dingeldangbang/Atze-Plana-/actions/runs/34798607416) and [push34798605327](https://github.com/dingeldangbang/Atze-Plana-/actions/runs/34798605327). Follow-up adds FIFO/hardlink safety and revision binding, executed locally; final remote results recorded in PR. Full platform/production remains BLOCKED. Git metadata recovered from the existing remote with working-file hashes preserved; no force push.

---

# Abschlussvalidierung — PLAN / Context Lock

## Abschließender CI-Nachweis69e6676

Der erweiterte Teststand und der Download-Fix sind auf **69e667659d9761e902b430db267163ee393357e0** tatsächlich erneut geprüft: [Core inklusive Browser34794084565](https://github.com/dingeldangbang/Atze-Plana-/actions/runs/34794084565), [zusätzlicher Core-Pushlauf34794082691](https://github.com/dingeldangbang/Atze-Plana-/actions/runs/34794082691), [echte Modell-/PLAN-Inferenz34794084699](https://github.com/dingeldangbang/Atze-Plana-/actions/runs/34794084699) und [Android Build/Emulator34794084629](https://github.com/dingeldangbang/Atze-Plana-/actions/runs/34794084629) **PASS**. Der zuvor gescheiterte Download wird damit nicht umetikettiert; neue echte Ausführung mit unveränderten TLS-/Hash-Gates erfolgreich. Dieser abschließende Nachweiskommentar ändert keine App-/Test-/Workflowfunktion. Nachfolgende reine Bericht-CI-Ergebnisse stehen im [PR](https://github.com/dingeldangbang/Atze-Plana-/pull/1).

Das ausgewählte Download-APK bleibt ausdrücklich das in APK_RELEASE_REPORT beschriebene1a919db-Artefakt; spätere ephemere Signaturen/Hashes werden nicht damit verwechselt. Vollplattform/Produktion weiterhin BLOCKED.

Stand 2026-09-14. **Reales, begrenztes Inkrement umgesetzt und getestet. Gesamtplattform / Produktionsrelease weiterhin BLOCKED.** Kein Merge, Tag, Release oder Produktionsdeploy.

## Implementiert
- Ein taskgebundener PLAN mit unveränderlichen Versionen und1–16 tatsächlichen Evidence-/Memory-/Text-Archivquellen; keine vorgefüllten Quellen oder simulierten Geräte.
- SHA-256-/Metadaten-/Abhängigkeitsmanifest, maximale Byte-/Referenzbudgets, optimistische Versionsprüfung, Reviewer-Lock und append-only Widerruf.
- Veraltete Quellen, Versionen, Locks oder Stop-Revisionen blockieren Challenge/Triage/Freigabe/Adoption und Decision-Memory. AI benötigt den aktuellen Lock, ohne Umgehung durch zusätzliche manuelle Quellen.
- Reale API und Browserbedienung; bekannte Secretmuster und gespeicherte Kontextkorruption werden vor Modelltransport abgewiesen. Kein Tool-/Executorzugriff.
- **CURRENT bestätigt die gebundene Fassung, niemals Wahrheit oder Aktionsberechtigung.** [Vollständiger Vertrag](docs/21-plan/context-lock.md).

## Tatsächlich ausgeführte Gates
| Gate | Ergebnis / konkreter Nachweis |
|---|---|
| Voranalyse/Baseline | 05ea6d5:120 Tests,97.78%, Build/Docs PASS vor Änderungen |
| Abschließende lokale Unit/API/Integration/Security/PLAN-Regressionssuite | **138 PASS,98.04%**,2 bekannte Warnungen,29.09s; `reports/plan-final-tests.log`, JUnit/Coverage |
| Echter HTTP-/Worker-E2E, normal und python -O | **41 Responses +4 separate Worker je Lauf PASS**; darunter PLAN BLOCK und erneute Freigabeprüfung |
| Core CI inkl. Build/Audit/Docs/Browser | [34793544467](https://github.com/dingeldangbang/Atze-Plana-/actions/runs/34793544467) und [34793540906](https://github.com/dingeldangbang/Atze-Plana-/actions/runs/34793540906) PASS auf1a919db; drei zusätzliche lokale Budget/Concurrencyfälle anschließend ergänzt |
| Echter Chromium-Browser | **7 Prüfungen PASS**, Google Chrome152.0.7977.82, beendet und Profil entfernt; kein --no-sandbox |
| Echtes gepinntes lokales Modell mit PLAN | [34793544446](https://github.com/dingeldangbang/Atze-Plana-/actions/runs/34793544446) PASS: tatsächlich geladene Gewichte, Antwort READY auch aus gesperrtem Archivkontext; widerrufene Warteschlangenanfrage BLOCKED |
| Android compile/sign/install/start/instrumentation | [34793544458](https://github.com/dingeldangbang/Atze-Plana-/actions/runs/34793544458) PASS; [aktuelles ausgewähltes APK](APK_RELEASE_REPORT.md) |
| Lokaler Paketbuild / Dependency-Audit / pip check / JS / Shell / Reality Gate | PASS; kein bekannter Treffer im ausgeführten Dependency-Audit; kein hermetischer/bit-identischer Buildanspruch |
| Dokumentation / OpenAPI | PASS; vier generierte Produkte, lokale Dateilinks, acht feste Envvariablen; neue ADR/Verträge/Migration synchron |
| Lokale Vorschau | Alte Core-/Workerprozesse gestoppt, neue gestartet; registrierte PLAN-API200, ausgeliefertes JS per SHA mit aktuellem Code identisch; Worker meldet NO_PENDING_JOB |

Implementierung `8125e85e72ad4639d551e0a81cefcf9084b676b4`, Browser-/Sessionkorrekturen und validierter Code `1a919db830d18d38b59b3e08314d148107bb9d23`; GitHub baut PR-Merge `01fcd2d98f0120bcfb3f499a5d5bb0988451ebae`. Anschließender Dokumentations-/Testcommit ergänzt Nachweise und drei Budget/Concurrencyfälle; dessen eigener CI-Lauf wird zusätzlich im PR dokumentiert. [Review-PR #1](https://github.com/dingeldangbang/Atze-Plana-/pull/1).

## Modell-/Browser-/APK-Grenzen
Qwen0.5B Q4_K_M und llama.cpp b10948 real gehasht/geladen, UID1001 im Namespace ohne externe Route, Prozesse beendet. Das beweist konkrete Textinferenz, keine Modellqualität oder komplette Agentensandbox. Browserdaten ausschließlich synthetisch in eigener Testinstanz, keine Produktfixtures. Anfangs falsche Harness-Loginselektoren/Statusannahme und ENOTEMPTY beim abrupten Browserende: diagnostiziert, korrigiert, echter Wiederholungslauf PASS. Auch veraltete Verbindungsanzeige und Eingabefeld nach Logout korrigiert. Keine Tests entfernt oder Sandbox deaktiviert.

SDK-Emulator ist kein physisches Gerät. Die native App bleibt read-only Statusclient, ohne PLAN-Editor, Honeywell/EDL/Repair oder geprüfte Live-Core-TLS-Session. Kein lokaler APK-Download behauptet: Blobtransport scheitert hier, originale GitHub-Artefakte/Hashes und Check-Annotationen sind geprüft. Debug-Schlüssel ephemer; kein AAB/stabil signiertes Release.

## Kritische offene Gates / nächste Schritte
- Volle Permission-Leases/HITL Once/Task/Workflow/Temporary, Executor-/Filesystem-/Syscall-Sandbox und Escape-Abnahme vor allgemeinen Tools/MCP.
- Universal-PLAN mit PDF/CAD/3D/Device-/Research-/Repair-Engines, Agent Builder, echte Bridge-/ESP32-/Honeywell-/Trend-/Unity-/Cloud-/Bright-Data-Adapter fehlen; keine erfundenen Hardware-/Providerresultate.
- Universelles authentifiziertes TLS-/Egress-Gateway, verschlüsselte Bestandsdaten/Secretcache, individuelles Rollenmodell, unabhängiger Privacy-/Security-Audit, Last-/2GB-/Restore-Abnahme fehlen.
- Byteintegrität ist keine semantische Wahrheit; Originalprosa/Messungen werden nicht durch deterministische Regeln zertifiziert. Quelle exakt wiederhergestellt kann live wieder passen; Widerruf/Stoprevision werden nicht wiederbelebt. Keine Beobachtung unbeobachteter Hoständerungen/in-flight-Rückholung.
- **Upgrade:** alle alten Core/Worker stoppen, Policy challenge-2-context erfordert neue Gegenprüfungen. Kein Mischbetrieb oder stiller Downgrade mit post-PLAN-Daten.

Weitere Arbeit: echte zielgebundene, widerruf-/ablaufbare Permission-Leases und isolierter Executor als nächster kleiner Schnitt. Hardware-/Providerabnahmen benötigen konkrete autorisierte Ressourcen. Kein Full-Platform-Release aus einem grünen Teiltest ableiten.

### Abschlusslauf25b3512 / Download-Grenze
Core-/Browser-CI34793906467 PASS mit erweiterten Tests. Modell-CI34793906490 scheiterte **vor Inferenz** beim Staging öffentlicher gepinnter Dateien; genauer Transportfehler aus hier nicht abrufbaren Bloblogs nicht behauptet. GitHub lehnte direkte Wiederholung ab („workflow file may be broken“), kein Authentifizierungsfehler und kein Beweis eines YAML-Fehlers. Downloadstufe daher um begrenzte native Curl-Transient-Retries und strukturierte Exit-/HTTP-Annotationen ergänzt, mit unveränderten HTTPS-/TLS-/Hashvorgaben. Neuer identischer Inferenztest folgt im CI des Fixcommits; endgültiger Laufstatus wird im PR nachgetragen. Vorheriger realer Inferenznachweis1a919db bleibt getrennt bestehen.

---

## Historische Nachweise früherer Inkremente (nicht aktuelle Abnahme)

# Final Validation Report — real model worker + Android prototype

Stand 2026-09-14. **FUNCTIONAL PROTOTYPE / CONDITIONAL**, vollständige Plattform und Production Release **BLOCKED**. Implementierungsbasis fbf4be9; Android-Pfadkorrektur und geprüfter Branchstand `b7912227f2a021cc3664b27e5984312369b1328e`. Keine erfundenen Dienste, Geräte, Modelloutputs oder APKs. Kein Merge/Release/Produktionsdeploy.

## Gelieferter realer Umfang
- Bestehender Evidence-/Context-/Storage-/Privacy-/Challenge-/Triage-Core bleibt erhalten; 120 Tests/97,78% Coverage und beide echten HTTP-Smokes bestanden.
- Reale lokale Qwen-Inferenz auf separat betriebenem **GitHub-CI-Worker**, gepinnte Modell-/Runtimebytes, unprivilegierter Prozess, Netzwerknamespace nur Loopback, explizit synthetischer Prompt, tatsächlicher Output READY, anschließend Kindprozesse beendet. Keine operative Modellkonfiguration oder vollständige AgentRuntime daraus abgeleitet.
- Nativer **Android-Core-Statusclient** mit realem HTTPS-Transportcode, explizitem Ziel/Token, keinen automatischen Daten/Devices, TLS1.2+/Systemtrust, keinem Redirect-/Klartextfallback. Echte Debug-APKs gebaut/signaturgeprüft, im SDK-Emulator installiert/gestartet und native UI-/Sicherheitsgrenzen geprüft. Keine Repair-/Bridgefähigkeit vorgetäuscht.

## Ausgeführte Gates / Artefakte
[TEST_REPORT](TEST_REPORT.md) nennt konkrete Laufresultate, [APK_RELEASE_REPORT](APK_RELEASE_REPORT.md) die echten Dateien/Signatur-/Installationsgrenzen und SHA256-Werte.

- [Modell-CI 34790349657](https://github.com/dingeldangbang/Atze-Plana-/actions/runs/34790349657): PASS; UID1001, LOOPBACK_ONLY_NO_EXTERNAL_ROUTE, tatsächlicher einzelner Request0.881s, Ausgabe READY, children_stopped=true. Kein allgemeiner Qualitäts-/Performancebeweis.
- [Android-CI 34790349728](https://github.com/dingeldangbang/Atze-Plana-/actions/runs/34790349728): PASS in3m19s; tatsächliche APK-Erzeugung/Signaturprüfung/Installation/Start/Instrumentation.
- [Download der geprüften APKs und Nachweise](https://github.com/dingeldangbang/Atze-Plana-/actions/runs/34790349728/artifacts/10328670450). Branchcommit b791222, PR-Mergecode c9d5f9c31349013fbc7bc0bdeabb3adedce4ca01. Appdatei **atze-app-debug.apk**,16811Bytes,SHA256`b7893a6d8e4da3650b21c75d10796d7db4032410c2a5be65ee7c45af30f03b14`. Test-APK separat, nicht normale Appinstallation.
- Downloads aus Blob-Store in Arena scheitern mit EOF; **keine lokale APK-Kopie behauptet**. Dateien und Prüfsummen wurden im tatsächlichen CI erzeugt; GitHub-Artefaktmetadaten und Original-Check-Annotationen authentifiziert abgerufen. User kann Original über GitHub downloaden; Retention14Tage, kein dauerhafter Release.

## Fehler ehrlich behoben
Direkter HF-TLS-Abruf in Sandbox gescheitert; keine Zertifikatsabschaltung/anderer Provider. Lokaler Androidbuild korrekt BLOCKED (JDK/SDK fehlen). Erster CI-Androidbuild erzeugte APKs, Installationsphase scheiterte; Diagnose zeigte AVD-Home-Konflikt. Gemeinsame explizite Pfade/ini-Prüfung eingeführt und der gesamte Lauf erneut bestanden. Keinen alten Teil-PASS als APK-Abnahme ausgegeben.

## Unverändert blockierte Master-Gates
[Master acceptance matrix](docs/00-overview/master-acceptance.md): vollständiger PLAN-Binary-/CAD-/Device-/Repair-Kontext samt Context Lock, allgemeiner Agent Builder/MCP/Permission-Leases/Tool-Executor/Filesystem-Sandbox, echte USB/WiFi/BLE/ADB/Fastboot/EDL-/Honeywell-/ESP32-/Motor-/Trend-/Unity-/BrightData-/Cloud-/Paymentintegration fehlen oder sind nicht validiert. Kein Messwert/Drehmoment/Cloudgerät erfunden. Android-Emulator-ADB ist Testwerkzeug, keine produktive Device Bridge. Reale Core-TLS-Session aus APK und physische Hardwaretests NOT RUN; AAB nicht gebaut; keine Produktionssignatur. Universeller Egress-/verschlüsselter Secretcache-/2GB-Last-/Security-Audit offen. Deployment und Release bleiben BLOCKED.

Nächste Priorität: begrenzter PLAN-Objekt-/Context-Lock-Vertrag und widerrufbare Permission-Leases vor allgemeiner MCP-/Toolausführung. Reale Geräte/Provider nur mit tatsächlich verfügbaren autorisierten Ressourcen anbinden. [ADR-006](docs/adr/ADR-006-real-worker-and-android-validation.md). Historische Validierungsberichte darunter sind zeitlich markierte frühere Stände, keine aktuellen APK-Buildhashes.

---

## Historische Validierung vor dem erfolgreichen Worker-/Androidlauf

# Master-Inkrement — reale Worker-/Android-Abnahme, noch keine Gesamtfreigabe

Stand 2026-09-14. Basis fbf4be9. Ist-Zustand und unterbrochene Änderungen geprüft; aktuelle Baseline erneut ausgeführt: 120 Tests, 97,78% Core-Coverage, Python-Build, Dokumentation/OpenAPI/No-fake/JS-Syntax PASS. Drei Harness-Tests sind kein realer Modelltest. [Testbericht](TEST_REPORT.md), [APK-Bericht](APK_RELEASE_REPORT.md), [ADR-006](docs/adr/ADR-006-real-worker-and-android-validation.md).

Neue Implementierung: gepinnter tatsächlicher lokaler HF/llama.cpp-Integrationsrunner mit separatem nicht-root Netzwerknamespace; nativer Android-HTTPS-Core-Statusclient plus tatsächliche SDK-/Signatur-/Emulatorpipeline. Lokaler HF-TLS-Abruf scheiterte, keine Zertifikatsabschwächung. Android-Build lokal tatsächlich BLOCKED (SDK/JDK fehlen). CI dieser neuen Integrationen steht zum Zeitpunkt dieser Berichtsfassung noch aus. **Kein Modell-/APK-/Emulator-PASS aus bloßer Workflowdefinition ableiten.**

Unverändert: keine operative externe Inferenz, keine neuen Plattform-Testdaten; alle relevanten Entscheidungen weiterhin Challenge/Triage/Approval-pflichtig. Kein Native-Device-/Honeywell-/Repair-/ESP32-/Unity-/BrightData-/Cloud-/Payment-/MCP-/AgentBuilder-Erfolg behauptet. Universal-Egress-/Filesystem-/Syscall-Sandbox, umfassende Datenschutzabnahme und Gesamtplattformrelease BLOCKED. Keine leeren Modulverzeichnisse als fertige Implementierung angelegt.

Nachfolgend historischer Stand der vorherigen bereits validierten Core-Änderungen. Dessen CI/Buildhashes sind kein Nachweis der neuen Worker-/Androidkandidaten.

---

# Final Validation Report — 0.4.0.dev0 Privacy-first foundation

Stand 2026-09-14; Basis `9413bf5d4608e21cbdbf6894d4033c807b32a8ee`, Branch `arena/01a09c9d-atze-plana`. **Teilimplementierung, vollständige HF-/Agent-/MCP-Abnahme BLOCKED.** Kein Release/Produktionsdeploy. [ADR-005](docs/adr/ADR-005-private-model-gateway.md), [implementierter Vertrag](docs/02-core/model-gateway.md).

## Prüfung vor Implementierung / Konsequenz
Bestehende Netzwerk-/Context-/Rollen-/Challenge-/Build-/CI-Pfade geprüft. Keine Modellruntime/Weights installiert, keine HF-/MCP-/Tool-Sandboxintegration vorhanden. Bestehende Domainfunktionen nicht ersetzt. Keine Modellgewichte/ausführbaren Modellrepositorys heruntergeladen; keine externe Inferenz mit Projektinhalten durchgeführt. Zusatzabhängigkeiten: keine. Neuer Core bleibt modellfrei; inferiert nur über explizit konfigurierte kompatible Textserver. Abstrakte Modalitätsverträge sind KEINE implementierten Modalitätsprovider.

## Tatsächlich implementiert
LOCAL/SELF_HOSTED/PRIVATE_ENDPOINT/EXTERNAL_PROVIDER-Konfiguration; default Local-only/Privacy Lock/External DENY/empty allowlists. Manuell reviewergebundenes Modellregister, begrenzte Same-Project-/Same-Task-Kontextauswahl, konservative Klassifizierung und Secret-Patternblock, exakte Context-Hash-Consent, erneut geprüfte Policy/Stop/Config vor I/O. Reale authentifizierte Text-HTTP/TLS-Anbindung, keine Redirects/Proxies/Fallbacks/Tools. Durable Pending-Outcome-Audit vor I/O, kein automatisches Retry nach unklarem Ausgang. Antwort bleibt DRAFT_UNCHALLENGED, keine direkte Result-/Memory-/Decisionadoption. UI zeigt tatsächlichen KI-Policystatus und bietet reviewergebundenen KI-Local-only-Lock.

## Aktuell ausgeführte lokale Gates
| Gate | Ergebnis | Grenze / Evidence |
|---|---|---|
| Gesamtsuite | **117 passed**, 2 sichtbare Deprecation-Warnungen | `reports/ai-tests.log`, JUnit; 90 bestehende + 27 neue parametrisierte Fälle |
| Statement-Coverage | **97,78%**, 1489 Statements /33 nicht parent-gemessen | Challenge-Kindprozesse nicht in Parent-Coverage; keine Requirements-/Browserabdeckung behauptet |
| Privacy-/Rollen-/Leak-/Context-/Memory-/Replay-/Stop-/Policytests | TESTED | echte APIs/SQLite, abgewiesene Anfragen ohne Transport; AI-001..014 |
| TLS | TESTED begrenzt | echter Loopback-TLS-Handshake: unbekanntes Zertifikat abgewiesen, explizit vertrautes temporäres Testzertifikat akzeptiert; TLSminimum1.2; keine echte PrivateLink-/Remoteproviderabnahme |
| Text-HTTP-Transport | TESTED, **kein Modelltest** | isolierter Receiver berechnet Hash-Transportbeleg, kein Modell/Fakeprovider in Runtime; HTTP-/Redirect-/Tools-/Malformed-/Oversize-Grenzen |
| Bestehender realer HTTP-Smoke | PASS | 29 Responses und zwei separate Challenge-Workerprozesse, auch unter python -O |
| Dependencies/Security | pip check PASS, pip-audit keine bekannten Treffer | keine unabhängige Sicherheitsabnahme/OS-Egressgarantie |
| Docs/OpenAPI/No-fake/JS | PASS | vier generierte Produkte, acht feste Envvariablen, lokale Dateilinks, AST-Gate, node --check |
| Wheel/sdist Build | PASS 0.4.0.dev0 | tatsächlich erzeugt, keine APK/Modellartefakte |
| Installiertes Wheel | PASS begrenzt | zweite locked venv, python -I lädt site-packages; isolierte DB/API/default deny/HTML geprüft |
| Reproduzierbarkeit | CONDITIONAL | zwei Builds mit SOURCE_DATE_EPOCH1789344000: Wheel bytegleich; sdist-Dateien/Inhalte gleich, Archivbytes verschieden |
| Remote-CI dieses Schnitts | PASS | Korrigierter Implementierungsstand 50c4dfafbf826a0def5cbd9ebd05751244fc9781; [Lauf 34789132272](https://github.com/dingeldangbang/Atze-Plana-/actions/runs/34789132272) komplett erfolgreich, inkl. Tests/Build/Docs/Audit/Smokes/JS/Artefaktupload |
| Browser E2E | NOT RUN | Syntax/HTTP sind kein Bedienungsnachweis |
| Gesamte HF-Agent-Integration / Release | **BLOCKED** | lokale HF-Inferenz, AgentRuntime/MCP/OS-Sandbox/full privacy/cost/offload noch nicht umgesetzt/validiert |

Lokaler wiederholter Wheel-SHA256: `09e3184292f3421bc359f905ff838def6e07759081c0d955d03c290362f1b573`. Weitere ignorierte Laufartefakte: `reports/ai-build.log`, `reports/ai-wheel-install.log`, `reports/ai-reproducibility.json`, `reports/dependency-audit.json`, `reports/smoke*.json`. CI erzeugt eigene commitgebundene Artefakte. Erster Gesamtlauf: 110 bestanden/1 Docsfehler wegen noch fehlendem ATZE_AI_CONFIG in YAML-Spiegel; Spiegel ergänzt, Generator und Gesamtsuite danach neu ausgeführt. Kein Test umgangen.

## Nicht als erfüllt ausgegebene Akzeptanzkriterien
- **Local Hugging Face model / autonome Agent Runtime / MCP / Multimodel Challenge:** NOT RUN/NOT IMPLEMENTED. Kein Modelloutput oder MCP-Erfolg erfunden. Bestehender deterministischer separater Challenge-Worker ist kein unabhängiges zweites KI-Modell.
- **RAG/Memory/Context/Challenge/Triage/Audit:** bestehende reale Softwarepfade regressionsgeprüft; Modellkontext nur explizite Evidence/Memory-Auswahl, keine gesamte Datenbank oder automatisch freigegebene externe RAG-Suche.
- **Universal ExternalDataGateway/Full Privacy Lock/No plaintext external transmission:** neue Modellkommunikation gegated, aber keine plattformweite OS-Egressgarantie. Bestehender Challenge-Control-Transport weiterhin separat. Ingress/TLS-Termination/Hostadmins/Plugins/andere künftige Adapter separat absichern. Kein universal erfülltes Security-Audit behauptet.
- **Secrets/Cache:** bekannte Muster und explizite SECRET/CREDENTIAL blockiert; kein umfassender semantischer/Encoded-Secret-Detektor. Legacy Memory/Cache/Core DB nicht verschlüsselt-at-rest; keine globale Secretcachegarantie. Exakte menschliche Kontextprüfung bleibt notwendig.
- **Authenticated/Region/Revision/License/Private Endpoint:** Bearer wird an administrativ konfigurierten Endpoint geschickt, TLS geprüft; regionale Speicherung/Providerverhalten/private Netzwerktopologie/geladene Modellrevision nicht attestiert. Ein Moduslabel ist keine PrivateLink-Bereitstellung.
- **Kosten/Ressourcen/Offloading/2-GB-Core:** keine Kostenberechnung/Provisionierung/GPU-Messung oder Lastgarantie. Core hält keine Gewichte; Inferenzthread hält zeitweise DB-Schreiblock. Sockettimeout ist keine harte Gesamtdeadline. In-flight Daten können durch Policyänderung nicht zurückgeholt werden.

Nächster realer Integrationsschritt: geprüften separaten lokalen Modellworker mit konkreter Runtime, Modelllizenz, gepinnter Revision und Hardwarebudget bereitstellen; reale Inferenz und danach eigenständige Agent-/MCP-/Sandboxpfade jeweils durch eigene Abnahmegates führen. Keine Remote-Inferenz im Produkt automatisch aktivieren.

## Beobachteter Previewfehler und Regression
Beim abschließenden Live-Read nach Neustart trat SQLite ProgrammingError auf: FastAPI kann sync Dependency-Enter/Handler/Exit auf verschiedene Poolthreads verteilen. Bisherige SQLite-Threadbindung war zu streng. Store.connect verwendet weiterhin eine eigene, sequenziell genutzte Verbindung pro Unit-of-Work, jetzt mit erlaubtem Thread-Handoff. DB-THREAD-001 prüft reale getrennte Threads inklusive Commit und Rollback. Kein geteilter globaler Connectionpool oder überlappende Benutzung eingeführt. Erneut ausgeführt: 117 Tests, beide echten Smokes, zwei Builds und installierter-Wheel-Check samt Thread-Handoff. Preview nach Korrektur: 40 echte Read-only-Anfragen mit 8 parallelen Clients erfolgreich, Default DENY/leere Modell-/Resultlisten, keine Testeinträge. reports/ai-preview-read.json. CI der Korrektur tatsächlich geprüft: [34789132272](https://github.com/dingeldangbang/Atze-Plana-/actions/runs/34789132272), komplett erfolgreich in 1m12s. Frühere grüne Läufe allein wurden nicht als Nachweis der Korrektur verwendet.

## Remote-/Preview-Nachweis
Implementierung `7de6893211a87c92bc2af42bae498b1d75efee61`, zusätzliche explizite Sperre bekannter unbeschrifteter Plattform-/Providercredentials in `a915c659ebf4937b462ce30af9c0c52feb939e99`. Lokaler Lauf vor Thread-Handoff-Korrektur 116 Tests; Remote-Lauf 34788948064 für diesen Code vollständig grün (1m16s). Nicht blockierende bekannte Node-20→24-Actionwarnung sichtbar. PR bleibt offen. Dieser nachfolgende Dokumentationscommit ergänzt tatsächliche Nachweise.

Preview auf 0.4.0.dev0 neu gestartet, Health operational/ok. Tatsächlich abgefragte AI-Policy: default-deny, privacy_lock=true, local_only=true, external_ai=false, allow_remote=false; Provider und Modellregister leer. Keine Testmodelle/Prompts/Testprovider in Betriebsdaten; keine externe Inferenz aktiviert. Kein Browser-E2E-/Produktionsnachweis.

---

## Historischer Bericht des vorherigen v0.3-Schnitts (keine aktuellen 0.4-Buildhashes/CI-Ergebnisse)

### v0.3 Mandatory Challenge

Stand 2026-09-14. Repository `dingeldangbang/Atze-Plana-`, feste Branch `arena/01a09c9d-atze-plana`, Basis `1094a8b40349dd258e1e716bd6cdfb3ad94974fc`. [PR #1](https://github.com/dingeldangbang/Atze-Plana-/pull/1). Kein Merge/Tag/GitHub-Release oder Produktionsdeploy. Implementierungscommit `7ef229fda30966d294fa2b038c6b29d97244d023` tatsächlich gepusht. [Remote-CI 34787960369](https://github.com/dingeldangbang/Atze-Plana-/actions/runs/34787960369) vollständig erfolgreich: Installation, Docs, Tests, Build, Dependency-Audit, Reality-Gate, beide HTTP-Smokes, JS-Syntax und Artefaktupload. Frühere v0.2.1-CI wird nicht als v0.3-Nachweis verwendet. Dieser nachfolgende Dokumentationscommit ergänzt den tatsächlich beobachteten Nachweis.

## Tatsächlicher Implementierungsumfang
[ADR-004](docs/adr/ADR-004-challenge-before-decision.md): Primary **API-Eingabe** → unveränderliches Result Package → separater HTTP-Challenge-Worker mit eigenem Token → serververifizierter Report → Triage → erforderliche Human Approval → explizite Reviewer-Adoption. Kein Primär-Agentgenerator/LLM/Executor hinzugefügt.

Fünf reale deterministische Dimensionen: Evidence, Consistency, Alternative, Causality, Action. Projektweite eingereichte Evidence wird nach strukturiertem Identitäts-/Messkontext geprüft, Gegenwerte stoppen. Fehlende Alternative bleibt UNKNOWN; vorhandene begründete Kandidaten stammen aus tatsächlichen eingereichten Datensätzen. Keine erfundene Gegenquelle. Calculation/Kausalität/High-impact eingeschränkt; Action-Ausführung BLOCK. Aktuelle Reports und Approvals an Result/Job/Policy/Evidence/Stop gebunden. Direktes fact/decision-Memory 409; Adoption speichert ausschließlich geprüfte Scope-Provenance, nicht Primärfreitext. Retrieval prüft aktuellen Status neu, nie Aktionsberechtigung.

## Ausgeführte Gates
| Gate | Status | Tatsächlicher Nachweis |
|---|---|---|
| Unit/Integration/Safety | TESTED | 90 pytest-Fälle bestanden, zwei sichtbare Deprecation-Warnungen; keine Testausblendung |
| Coverage | VALIDATED begrenzt | 97,34%, 1203 Statements/32 nicht parent-gemessen; Challenge-Rules/API/Service 100%; separate Worker-Kindprozesse nicht in parent-Coverage |
| Real HTTP | TESTED | 29 geprüfte Responses, zwei echte separate Workerprozesse; explizit temporäre synthetische Testeingaben, keine Produktfixtures |
| Optimized Smoke | TESTED | python -O: ebenfalls 29 Responses und separate Worker; keine entfernbaren assert-Gates im Smoke |
| Triage/Agentgrenze | TESTED begrenzt | Kein ACCEPT/Approval/Adopt ohne aktuellen Report; Manipulation/Replay/Stale/Stop/Lease/Rollen/Snapshotgrenzen getestet. Spezialisierter Worker, kein allgemeiner Agent Builder |
| Build | VALIDATED begrenzt | Wheel und sdist 0.3.0 tatsächlich gebaut |
| Reproduzierbarkeit | CONDITIONAL | Zwei Builds mit SOURCE_DATE_EPOCH=1789344000: Wheel bytegleich; sdist-Dateinamen/Inhalte/hashgleich, tar.gz-Bytes verschieden (Archivmetadaten). Kein vollständig bitreproduzierbares Release behauptet |
| Installiertes Wheel | VALIDATED begrenzt | Zweite venv aus requirements.lock, Wheel installiert, python -I importiert site-packages, leere isolierte Test-DB, Health/HTML/JS/Resultliste/Worker-Claim geprüft |
| Security | CONDITIONAL | Rollen-/Lease-/Hash-/Stop-/Pfad-/Mode-/Auditrollback-Negativtests; pip-audit: keine bekannten Dependencytreffer. Kein unabhängiger Pentest |
| Dependencies/JS | TESTED | pip check ohne Konflikte; node --check app/static/app.js erfolgreich |
| Documentation/OpenAPI | VALIDATED begrenzt | Vier generierte Produkte, formale OpenAPI, lokale Dateilinks, sieben Envvariablen, Test-Docstrings geprüft |
| No-fake Boundary | TESTED begrenzt | scripts/reality_check.py PASS; enges AST-/Smoke-Gate, kein umfassender semantischer Fake-Detektor |
| Browser-E2E | NOT RUN | HTTP/JS-Syntax ersetzt keine Browserinteraktion; keine erfundenen Screenshots/Bedienungstests |
| CI/GitHub | VALIDATED begrenzt | Commit 7ef229f gepusht; Remote-Lauf 34787960369 vollständig erfolgreich, reale CI-Artefakte hochgeladen; PR offen |
| Sandbox/Hardware/Cloud/Release | NOT IMPLEMENTED / BLOCKED | Keine neuen Adapter, reale Execution-Sandbox, Gerätetests oder Produktionsabnahme |

Wheel-SHA256 des lokalen reproduzierten Builds: `eb42a0f39382db19e11f13bf232f4aa557b63f8ad03a4a008ec2f9551287de57`. Artefakte bleiben außerhalb Git. Dateien: `reports/tests.log`, `reports/junit.xml`, `reports/coverage.xml`, `reports/smoke.json`, `reports/smoke-optimized.json`, `reports/dependency-audit.json`, `reports/build.log`, `reports/reproducibility.json`, `reports/wheel-install.log`. CI erzeugt eigene commitgebundene Artefakte.

### Beobachtete Fehler und Korrekturen
Frühe Testmigration hatte alte Direkt-Approval-/Smoke-Annahmen; auf zwingenden echten Challengefluss umgestellt und vollständig neu ausgeführt. Erster installierter-Wheel-Check verwendete falsche Umgebungsnamen für Testpfade; vorhandener Objektwurzel-Modusguard verweigerte cross-mode-Zugriff korrekt. Mit tatsächlichen ATZE_DB_PATH/ATZE_STORAGE_ROOT erneut vollständig isoliert ausgeführt: PASS. Keine Betriebsdaten in Testdaten umetikettiert. sdist-Byteunterschied bleibt ausdrücklich offen.

## Grenzen / offene Gates
- ACCEPT ausschließlich `submitted_structured_claims_only`: exakte endliche Decimal-/normierte Stringvergleiche; keine Einheitenumrechnung, freie Mathematik, Primärtextsemantik oder Kausalitätsbeweise. Metadaten/Measurements/Review sind eingereichte Angaben, nicht tatsächliche Hardwareverifikation.
- Worker separat mit eigener Credential, aber gemeinsamer Rulecode und gleicher Entwicklungs-OS-Nutzer. Keine unabhängige Online-Recherche/organisatorische Herkunft/Host-Sandbox bewiesen. Betriebstokenkonfiguration beweist keine Worker-Liveness.
- Snapshots bis 500 Records/4 MiB, maximal 500 Findings plus BLOCK bei Überlauf. Grenzen sind kein Last-/2-GB-RAM-/globaler Body-/Rate-Limit-Nachweis. Immutable Job-/Reportretention noch ohne GC.
- Geteilte Rollen statt individuelle Identitäten/MFA/Tenant-ACL; keine zeitbasierte Approvalexpiry, kein kryptografisch manipulationssicheres Audit. Stalenessbindung ersetzt diese Produktionsgates nicht.
- Result-Erfassung API-only; kein versteckter Primary-Generator. Why/Challenge/Quellen real implementiert, Browser-E2E bleibt offen.
- Cache/Memory/Archive getrennt; unveränderte Filesystem-/SQLite-Crashlücke, Retention alter Kopien, kein konsistenter automatisierter Gesamtrestore und keine reale SD-Hardwareabnahme.
- MCP, mobile Geräte/Android/APK, Primary LLM, Agent Builder, allgemeine Executor/Sandbox, Remote/Cloud/Bright Data, Payment, Offline-Sync weiterhin NOT IMPLEMENTED/BLOCKED. Git/gh-Entwicklungszugriff ist keine Runtimeintegration.

## Nächste Schritte
Remote-CI/PR prüfen; Browser-E2E, bitreproduzierbare sdist-Metadaten, konsistenten Restore und isolierten Workerbetrieb validieren. Anschließend tatsächliche unabhängige Recherche-/Experimentschnittstellen spezifizieren und mit realen Quellen prüfen — erst dann allgemeinere Agententscheidungen freigeben.

[Dokumentationsaudit](DOCUMENTATION_AUDIT.md) · [Integrationsaudit](docs/17-security/reality-audit.md) · [Challenge-Vertrag](docs/02-core/challenge-worker.md) · [Policy](REALITY_POLICY.md)

## Entwicklungs-Preview (kein Produktionsdeploy)
API auf 0.3.0 neugestartet, Health meldet operational/ok/0.3.0. Runtime meldet OPERATIONAL — NO SEEDED DATA und Production NOT VALIDATED. Separater Worker mit ausschließlich eigener Credential im Kindprozess-Environment gestartet; reale Claim-Aufrufe antworten NO_PENDING_JOB. Tatsächliche Resultliste leer, keine synthetischen Pakete im Betrieb erzeugt. Same-Host-Prozess weiterhin keine OS-Sandbox. Der öffentliche `/openapi.json`-Pfad antwortet absichtlich 404; die aktuelle OpenAPI wird offline generiert, nicht durch einen eingeschalteten Runtime-Dokupfad behauptet.

GitHub meldet eine nicht blockierende Node-20→24-Warnung für gepinnte Actions; Lauf erfolgreich. Browser-E2E und unabhängiges Productionreview bleiben offen.
