# Abgleich: Repository vs. ChatGPT-Masterkonversation („Causal Validation Gateway")

Stand: 2026-09-14. **Quelle:** geteilte ChatGPT-Konversation, abgerufen am 2026-09-14:
<https://chatgpt.com/share/6aa83d86-0530-83eb-9aea-73235df90571> — Einstufung nach eigener Disziplin:
**EXTERNAL_SOURCE** (frei teilbarer Chat-Verlauf eines Drittanbieters, löschbar/flüchtig, keine verifizierte
Autorschaft). Dieser Abgleich ist Dokumentation; er ändert keinen Produkt-/Testcode.

## 1. Methode

- Konversation vollständig gelesen: Vision („Reality First / No Fiction Data"), Orchestrator-/Inventar-/ESP32-/3D-Konzept,
  15 Funktionsvorschläge, Bright-Data-Integration, „Triage als Entscheidungslogik", PLAN-Reiter-Spezifikation,
  3D/Gaming/Avatar-Ebene, 2-GB-Architektur, Unity-Agent, Trend Engine, Network-Operations-Layer,
  **Master-Agent-Aufforderung (~42 Abschnitte)**, Dependency-&-Resource-Manager-Ergänzung,
  Mobile-Project-Server/MCP/RAG/Memory/Storage-Ergänzung, **Auslieferungs- und Fertigstellungsanforderung
  (inkl. signierter APK)**, Release-Checkliste, HuggingFace-/Privacy-Abschnitt, **2-GB-Korrektur**,
  Context-Lock-Deep-Dive, globaler Plan-/Task-Lock, visueller Workflow-Editor.
- Repositorysstand geprüft: Code (`app/`, `android/`), Docs (`docs/`), ADRs, Berichte, CI-Workflows.
- Tatsächlich ausgeführt am 2026-09-14 in dieser Umgebung (Debian 12, Python 3.11.2):
  `python -m pytest -q` → **169 passed**; `python scripts/docs.py --check` → **PASS** (4 Produkte, OpenAPI valid,
  lokale Links valid, 9 Env-Variablen); `python scripts/reality_check.py` → **PASS**.
  CI-Realteile: `validate.yml`, `universe.yml`, `local-model.yml`, `android.yml` (letzter Android-Lauf 34873545249
  am 2026-09-14: success inkl. Emulator-Installation/Instrumentation).
- Statusvokabular wie im Repo üblich: IMPLEMENTED, IMPLEMENTED/TESTED, PARTIAL, NOT IMPLEMENTED, BLOCKED,
  NOT RUN, ABWEICHUNG. Keine Aussage ohne Nachweis; Lücken werden nicht zu Fähigkeiten aufgewertet.

## 2. Kernaussage

Das Repository setzt **bewusst einen begrenzten, lauffähigen Kern** der Master-Anforderung um und stuft alle
nicht umgesetzten Großmodule selbst korrekt als NOT IMPLEMENTED/BLOCKED ein
([README](README.md), [Master-Matrix](docs/00-overview/master-acceptance.md), [Roadmap](docs/00-overview/roadmap.md)).
Die harten Grundregeln der Konversation sind weitgehend identisch übernommen (No Fiction Data, Triage/Challenge vor
Entscheidung, PLAN/Context Lock, Privacy-First-Modellgrenze, echte APK-Auslieferungspipeline). **Keine erfundene
Implementierung gefunden** — die Selbstaussagen stimmen mit Code, Tests und CI-Nachweisen überein.
Relevante **Deltas** bestehen bei: 2-GB-Neuinterpretation (nicht übernommen), 9-stufigem Statusvokabular (nur
teilweise strukturiert), PLAN als API-Vertrag statt visuellem Workflow-Editor, Permission-Lease-Engine,
Auslieferungsformaten (`release/`-Ordner, Release-Checkliste, AAB) und der offenen Lizenzentscheidung.

## 3. Abgleichsmatrix

| # | Anforderung der Konversation | Repo-Status | Nachweis / Grenze |
|---|---|---|---|
| 1 | **NO FICTION DATA / STRICT MODE**: keine erfundenen Werte/Geräte/Tests; UNKNOWN nie automatisch VERIFIED; Statusvokabular VERIFIED/MEASURED/CALCULATED/CONDITIONAL/ESTIMATED/EXTERNAL_SOURCE/CONTRADICTED/UNKNOWN/BLOCKED | **IMPLEMENTED als Politik, PARTIAL als Datenmodell** | [REALITY_POLICY.md](REALITY_POLICY.md) verbindlich; `scripts/reality_check.py` PASS; Kernmodelle nutzen `ACCEPT/CONDITIONAL/BLOCK` + Challenge `PASS/CONDITIONAL/BLOCK` (`app/models.py`, `app/challenge_models.py`); EXTERNAL_SOURCE/CALCULATED/MEASURED-Kennzeichnung als Disziplin in [Master-Matrix](docs/00-overview/master-acceptance.md), nicht als durchgängiges strukturiertes Feld (Delta D2) |
| 2 | **Triage als zentrale Entscheidungslogik**: was/womit/wie, Preflight, Output-Gate (RELEASE/WARN/BLOCK), Decision Records, Decision Graph | **PARTIAL** | Deterministisches Gate `app/triage.py` (evaluate → ACCEPT/CONDITIONAL/BLOCK mit Gründen), verpflichtend vor Freigabe; Decision Records ≈ Audit + gebundene Challenge-Reports; **keine** Options-/Variantengenerierung, kein Planungs-Executor (Delta D3) |
| 3 | **Challenge Worker** (Primärresultat → unabhängige Gegenprüfung → Triage) | **IMPLEMENTED/TESTED — übererfüllt** | [ADR-004](docs/adr/ADR-004-challenge-before-decision.md), [Challenge-Worker](docs/02-core/challenge-worker.md): separater HTTP-Prozess, dritter Token, fünf Checks, Staleness/Adoption-Gates, Policy `challenge-2-context` (`app/challenge_rules.py`); Konversation forderte Challenge primär für Agentenresultate — das Repo macht sie für **jede** freigabefähige Taskentscheidung zwingend |
| 4 | **Approval/Human-in-the-Loop**; PLAN ≠ ACTION; Notstop | **IMPLEMENTED/TESTED (Kern), ÜBERNOMMEN (Leases, 2026-09-15)** | Reviewer-Approval an Result/Challenge/Context gebunden; Freigabe ist keine Ausführung ([README](README.md)); globaler Stop + Invalidierung; Permission-Lease-Engine für MCP tools/call real (Allow Once/Task/Temporary + Expiry ≤24 h + Nutzungslimit + bestätigter Widerruf; [Vertrag](docs/17-security/permission-leases.md)); bewusst auf mcp.tools_call begrenzt |
| 5 | **PLAN als zentraler Arbeitsbereich** (Dateien/Quellen/Bilder/CAD/Messdaten/Software in einem Task-Kontext, Context Bundles, Rollen) | **PARTIAL — Kernvertrag implementiert** | `app/plan_api.py`/[Context-Lock-Vertrag](docs/21-plan/context-lock.md): genau ein PLAN je Task, unveränderliche Versionen, Quellen-Hashes, Beziehungen `input/reference/supports/contradicts`, ≤1 MiB/64 Evidence-Dependencies; **nur** bestehende UTF-8-Textarchive (kein Binary-/PDF-/CAD-/Bild-Upload; bewusste Grenze, Delta D6); kein Executor |
| 6 | **Kontextsystem mit 8 Kontexttypen** (PROJECT/TASK/OBJECT/DEVICE/TEST/RESEARCH/REPAIR/SOFTWARE) | **IMPLEMENTED** | Exakt diese acht `context`-Arten in [Context-Lock-Vertrag](docs/21-plan/context-lock.md) — direkte Entsprechung zu Abschnitt 5 der Master-Aufforderung |
| 7 | **Context Lock (globaler Plan-/Task-Lock)**: Versionen, Reviewer-Sperre/Widerruf, Change-Detection, Konflikt/Expired-Zustände, Unlock/Relock über Approval, Lock+Triage+Challenge-Kopplung, Lock vor Agentenkontext/Ausführung | **IMPLEMENTED/TESTED (Vertragsebene)** | [ADR-007](docs/adr/ADR-007-plan-context-lock.md): optimistische Versionen, Lock erfordert exakte `version_id`+`manifest_hash`, neue Version statt stillem Refresh, Revoke auch unter Stop, Status CURRENT/UNLOCKED/SUPERSEDED/REVOKED/STALE/BLOCKED, AI-Anfragen müssen aktuellen `plan_lock_id` liefern und werden unmittelbar vor Transport erneut geprüft; **kein** visueller Lock-Rahmen/Workflow-Knoten (Delta D4) |
| 8 | **Visueller Workflow-Editor** (Zoom/Canvas/Minimap, Human-Approval-Knoten, Subworkflows, Parallelität, `workflow.json`-Export) | **NOT IMPLEMENTED** | PLAN ist API + Dashboard-Formulare; kein Canvas/Editor/Export (Master-Matrix „kein universeller Workflow-/Query-/Binary-Builder") |
| 9 | **Memory / RAG / Cache / Archive** mit Provenance; RAG ist Retrieval, nicht Wahrheit | **PARTIAL** | Echtes Memory (fact/decision) mit Challenge-Gates, lokale FTS-Suche mit Offsets/Hashes, Archive-Originalblobs, Cache TTL/Cleanup ([Context-/Storage-Architektur](docs/20-context-storage/architecture.md), `app/context.py`, `app/storage.py`); **keine** semantischen Embeddings/externen RAG-Tools (Master-Matrix) |
| 10 | **Tiered Storage** (RAM/SSD/SD/Server/Cloud, Unified Namespace, automatische sichere Verschiebung Copy→Hash→Verify, Storage Health, Offline-Sync, Mobile Project Server) | **PARTIAL** | Local-Tier + optionales SD-Verzeichnis, Copy/Hash/Verify vor Index-Wechsel, `health()`/`usage()`, Cleanup ([ADR-003](docs/adr/ADR-003-mobile-context-storage.md) als Zielarchitektur); kein RAM-/Server-/Cloud-Tier, kein Unified Namespace über Tiers, kein Offline-Sync, keine Mobile-Server-Runtime |
| 11 | **MCP als universelle Tool-Schicht** (GitHub/Files/Device/Telemetry/…) | **PARTIAL (nur Erkennung)** | [Bright-Data-MCP](docs/22-mcp/brightdata.md): Streamable-HTTP-Discovery, OAuth-Bearer, init/list/cleanup; **kein tools/call**, standardmäßig nicht aktiv |
| 12 | **Privacy-first Modellgrenze**: Provider-Abstraktion, EXTERNAL_AI=DENY default, Datenklassifikation, Secret-Scan, **ExternalDataGateway**, TLS 1.2+, lokale Runtimes, Model Registry, kein unverschlüsselter Drittanbietertransfer | **PARTIAL — Transport/Policy implementiert** | `app/ai_gateway.py` mit Klasse **`ExternalDataGateway`** (Klassenname wortgleich aus der Konversation), Modi LOCAL/SELF_HOSTED/PRIVATE_ENDPOINT/EXTERNAL_PROVIDER, leere Defaults/DENY, Local-only-Lock, Allowlists, Secret-Scan, Klassifikations-Upgrades, Reviewer-Consent, TLS-only (nicht-LOCAL), [Model-Gateway-Vertrag](docs/02-core/model-gateway.md); separate echte Modell-CI mit gepinnter Qwen-Inferenz ([TEST_REPORT](TEST_REPORT.md)); **keine** AgentRuntime/smolagents/Toolnutzung/Offloading (BLOCKED) |
| 13 | **Bright Data als Universal Web Evidence Engine** (SERP/Unlocker/Browser/Crawl/PDF/Provenance/Quellenvergleich) | **NOT IMPLEMENTED / NOT CONFIGURED** | Nur MCP-Erkennung (Zeile 11); URLs sind manuelle Evidence-Referenzen; keine Webabfrage (Master-Matrix) |
| 14 | **Android-Projekt-Workflow + APK-Auslieferungspflicht** (echter Build, Signierung, Installationstest, `APK_RELEASE_REPORT.md`, Debug-vs-Release-Trennung, „signierte APK, sofern Release-Key verfügbar") | **IMPLEMENTED/TESTED (Debug-Umfang)** | Nativer read-only HTTPS-Core-Statusclient ([android/README.md](android/README.md)) mit `ExternalDataGateway.java` (TLS 1.2/1.3, kein Cleartext, FLAG_SECURE, Token nur als Authorization); echter SDK-35-Build ohne Gradle (`scripts/build_android.sh`: javac→d8→aapt2→zipalign→apksigner), Emulator-CI mit Installation/Start/Instrumentation (`atze_result=PASS`); **[APK_RELEASE_REPORT.md](APK_RELEASE_REPORT.md) existiert mit dem von der Konversation geforderten Dateinamen**; ephemerer Debugschlüssel statt Release-Key (Konversation erlaubt diesen Fallback ausdrücklich); kein AAB, kein `release/`-Ordner (Delta D7); kein Download-Blobtransport aus Sandbox-Umgebungen (im Bericht ehrlich ausgewiesen) |
| 15 | **Device Bridge (USB/WiFi/BLE/Serial), ADB/Fastboot/EDL, Android Repair Lab, Repair Server, Honeywell CT45P-Gerätadapter** | **NOT IMPLEMENTED** | Master-Matrix/Roadmap 05/06: keine Geräteanbindung; Emulator-ADB ist Testwerkzeug, keine produktive Bridge; physisches Honeywell NOT RUN |
| 16 | **ESP32/IoT/Telemetrie, Motor Test Lab** (TORQUE=UNKNOWN-Regel, Messkampagnen) | **NOT IMPLEMENTED** | Roadmap 07: keine Sensoren/Telemetrie; keine erfundenen Messwerte |
| 17 | **3D-Welt/Unity/Avatare** (clientseitiges Rendering, Unity Agent Worker, ephemere Sandbox) | **NOT IMPLEMENTED** | Roadmap 11: kein Unity/Lizenz/Build; keine Dummy-Verzeichnisse |
| 18 | **Agent Builder / Software-Projekt-Generator / E-Commerce-Beispiel** | **NOT IMPLEMENTED** | Roadmap 04/12; vor Implementierung Tool→Permission→Task→Triage-Vertrag gefordert |
| 19 | **Trend Engine / Proactive Action** (Trendtypen, Context Normalization, Automatisierungsstufen) | **NOT IMPLEMENTED** | Roadmap 15: keine Anomalie-/Lifecycle-Engine |
| 20 | **Network Operations / Cloud / Multi-Cloud / Payment** | **NOT IMPLEMENTED (Kern-API vorhanden)** | Roadmap 08/09: eigene HTTP-API; kein Monitoring/MQTT/SSH/Provider-Adapter |
| 21 | **Dependency & Resource Manager** (Provider-Abstraktion, temporäre Dienste, Resource Leases mit Expiry, Auto-Provisioning, Failover, Kostensteuerung, RESOURCES-Modul) | **NOT IMPLEMENTED** | Kein Resource Manager/Leasing; Worker existieren nur als CI-Jobs (Modell/Android) ohne Lease-Engine; Master-Matrix weist Sandbox-/Worker-Grenzen aus |
| 22 | **Ephemere Worker / 2-GB-Core / Auslagerung** | **PARTIAL (CI-Worker real, keine Runtime-Orchestrierung)** | Separate CI-Jobs (Modell-Worker, Android-Emulator) mit Lifecycle-Cleanup sind real; keine dauerhafte Worker-Flotte/Orchestrierung im Core |
| 23 | **GitHub/CI/CD/Tests/Dokumentation**: Actions (Tests/Build/Validierung), README-Statusdisziplin, FINAL_VALIDATION_REPORT.md, Reproduzierbarkeit, keine Secrets | **IMPLEMENTED/TESTED** | 4 Workflows (`validate`, `universe`, `local-model`, `android`), heute grün; 169 lokale Tests PASS (2026-09-14); [FINAL_VALIDATION_REPORT.md](FINAL_VALIDATION_REPORT.md); README-Statustabelle entspricht Abschnitt „README ABSCHLUSSSTATUS"; `docs.py --check` Drift-Prüfung; Secret-Handling in [SECURITY.md](SECURITY.md) |
| 24 | **Release-Checkliste** (`RELEASE_CHECKLIST.md` mit Statusregeln je Punkt) | **NOT IMPLEMENTED (als Datei)** | Äquivalente Disziplin in [Master-Matrix](docs/00-overview/master-acceptance.md)/[RELEASES.md](RELEASES.md); die aus der Konversation übernehmbare Checklisten-Datei fehlt (Delta D7) |
| 25 | **Repository-Struktur** (Monorepo `apps/packages/agents/workers/bridge/unity/...` **oder begründete Alternative**), LICENSE | **PARTIAL / ENTSCHEIDUNG OFFEN** | Alternative Struktur (`app/`, `android/`, `docs/`, `scripts/`, `tests/`) ist erlaubt und in [PROJECT_BASELINE](PROJECT_BASELINE.md)/Dokumentation begründet; **LICENSE bewusst nicht erfunden** — Eigentümerentscheidung offen (Delta D8) |
| 26 | **Ressourcenregelung (final korrigiert)**: „2 GB" = maximaler RAM der **ausführenden Zielhardware (Honeywell CT45P-XON)**, „Free Tier" = Nutzungs-/Kostenklasse **externer Anbieter**; dynamische lokale/externe Ressourcenwahl; kein Free-Tier-Fallback auf Fake-Daten | **ÜBERNOMMEN (2026-09-15)** | D1 wurde am 2026-09-15 nachgezogen: README, Master-Matrix, Roadmap und [Free-Tier-Planung](docs/18-deployment/free-tier.md) trennen jetzt Zielhardware-RAM, externe Anbieter-Quotas und Core-Betriebsrahmen; historische Berichte (TEST_REPORT/FINAL_VALIDATION_REPORT) bleiben unverändert |

## 4. Deltas im Detail

- **D1 — 2-GB-Korrektur nicht übernommen (wichtig).** Die Konversation definiert zuletzt: 2 GB = Zielhardware-RAM
  (CT45P-XON), Free Tier = Drittanbieter-Quotas. Das Repo behandelt „2 GB" weiterhin als Core-Kapazitätsziel
  (README „Produktionsbetrieb, 2-GB-Kapazität CONDITIONAL"; Master-Matrix „2GB target"). Empfehlung: Begriffe in
  [Roadmap](docs/00-overview/roadmap.md)/[Master-Matrix](docs/00-overview/master-acceptance.md) und README trennen:
  Zielhardware-Ressourcenrahmen vs. Provider-Quotas vs. Core-Betriebsrahmen.
- **D2 — Statusvokabular reduziert.** Geforderte 9 Zustände existieren als Disziplin/Kennzeichnung, aber die
  Kernmodelle strukturieren nur ACCEPT/CONDITIONAL/BLOCK (+ PASS). Ein dokumentiertes Mapping (welches Feld welchen
  Konversationsstatus abbildet) fehlt.
- **D3 — Triage ist Gate, nicht Planungs-Engine.** Keine was/womit/wie-Optionsgenerierung, keine
  Variantenvergleiche, kein automatischer Preflight-Plan. Bewusster Kernausbau; die konversationelle
  Entscheidungs-Engine bleibt Roadmap-Arbeit.
- **D4 — Kein visueller PLAN-Workflow-Editor.** Canvas, Minimap, Human-Approval-Knoten, Subworkflows,
  `workflow.json`-Export fehlen; PLAN ist API-Vertrag + Dashboard-Bedienung.
- **D5 — Keine Permission-Lease-Engine.** Allow once/task/workflow/temporary + Expiry fehlten; vorhanden waren
  gebundene Approvals, Lock-Widerruf und Notstop. **→ Übernommen am 2026-09-15:** Lease-Engine für
  `mcp.tools_call` (Scope Task/Projekt, Tool-Bindung, Expiry ≤24 h, max_uses, Verbrauch bei Reservierung,
  bestätigter Widerruf unter Stop erlaubt, Audit; [Vertrag](docs/17-security/permission-leases.md)) — bewusst
  auf die eine Aktion mit realer Durchsetzung begrenzt, keine Delegation, kein Workflow-Scope.
- **D6 — Universal Context Workspace begrenzt.** Nur bestehende UTF-8-Textarchive als PLAN-Quellen (≤1 MiB,
  ≤64 Dependencies); kein Upload von Binary/PDF/CAD/Bildern (bewusste, dokumentierte Grenze).
- **D7 — Auslieferungsformate.** Kein `release/`-Ordner (`app-release.apk`/`.aab`/`checksums.txt`), keine
  `RELEASE_CHECKLIST.md`, kein AAB, kein Release-Key (Konversation: „sofern Release-Key verfügbar" — nicht
  vorhanden, ephemerer Debugschlüssel ist der ehrliche Fallback). Inhaltlich decken
  [APK_RELEASE_REPORT.md](APK_RELEASE_REPORT.md), [TEST_REPORT.md](TEST_REPORT.md),
  [FINAL_VALIDATION_REPORT.md](FINAL_VALIDATION_REPORT.md) und SHA256SUMS die geforderten Nachweise.
- **D8 — Lizenz offen.** Konversation fordert LICENSE; das Repo erfindet keine Lizenz und wartet die
  Eigentümerentscheidung ab (REALITY-Policy-konform).
- **D9 — Bewusst offen (korrekt ausgewiesen, kein heimliches Delta):** Bright-Data-Ausführung, MCP-tools/call,
  Agent Builder, ESP32/Telemetrie, Motor-Test-Lab, 3D/Unity, Trends, Network-/Cloud-Ops,
  Dependency-/Resource-Manager, Mobile-Server-Runtime, Offline-Sync. Alles in Roadmap/Master-Matrix als
  NOT IMPLEMENTED/PLANNED geführt — die Konversation liefert dafür die Ausbauspezifikation.

## 5. Besondere Übereinstimmungen (direkte Entsprechungen)

1. **Exakt acht Kontexttypen** (PROJECT/TASK/OBJECT/DEVICE/TEST/RESEARCH/SOFTWARE/REPAIR) — wortgleich aus
   Abschnitt 5 der Master-Aufforderung in den PLAN-Vertrag übernommen.
2. **Ressourcenbeziehungen** `input|reference|supports|contradicts` ≈ Konversations-Rollen (INPUT/REFERENCE/EVIDENCE)
   inklusive Widerspruchsbeziehung.
3. **ExternalDataGateway** — Klassenname in `app/ai_gateway.py` **und** `ExternalDataGateway.java` im
   Android-Client, exakt wie im Privacy-Abschnitt der Konversation gefordert (zentrales Gate, kein Umgehen).
4. **APK_RELEASE_REPORT.md** — der geforderte Dateiname existiert 1:1 und enthält die geforderten Nachweise
   (Hashes, Signaturtyp, Installation/Start/Smoke-Ergebnis, Known Limitations).
5. **Challenge vor jeder Entscheidung** — die Konversation skizziert Challenge primär für Agentenresultate;
   das Repo verschärft sie ([ADR-004](docs/adr/ADR-004-challenge-before-decision.md)) zur Pflicht für **jede**
   freigabefähige Taskentscheidung (Übererfüllung).
6. **Default-Deny/Local-only/TLS-only/Secret-Scan/Klassifikation/Consent** im Modell-Gateway entsprechen dem
   HuggingFace-/Privacy-Abschnitt (EXTERNAL_AI=DENY, Prompt/Context Firewall, keine unverschlüsselten Transfers).
7. **Context-Lock-Mechanik** (Versionen, Reviewer-Sperre/Widerruf, SUPERSEDED/STALE statt CHANGED/CONFLICT,
   Recheck vor Transport, Unlock/Relock als neue Reviewer-Entscheidung) deckt den Lock-Deep-Dive der Konversation
   auf Vertragsebene vollständig.
8. **README-Statusdisziplin** (IMPLEMENTED/TESTED/VALIDATED/CONDITIONAL/BLOCKED/PLANNED) entspricht dem
   Abschnitt „GITHUB README ABSCHLUSSSTATUS".
9. **Kein Fake im Betriebsweg**: REALITY_POLICY/AGENTS.md setzen „NO FICTION DATA"/„STRICT MODE" verbindlich um;
   Testmodus aktiviert keine Mocks; Nicht-Erreichbarkeit liefert Fehler statt Beispieldaten.

## 6. Empfohlene Nacharbeit (Vorschläge, keine Zusicherungen)

1. **D1 nachziehen:** 2-GB-/Free-Tier-Begriffskorrektur in Roadmap/Master-Matrix/README (Dokumentationsänderung). *Erledigt 2026-09-15.*
2. **RELEASE_CHECKLIST.md** aus der Konversation übernehmen (Arbeitsdokument mit Statusregeln je Punkt). *Erstellt 2026-09-15 aus den realen Repo-Disziplinen ([RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md)).*
3. **Statusvokabular-Mapping** dokumentieren (Konversationsstatus ↔ Modellfelder). *Erstellt 2026-09-15 ([Statusvokabular-Mapping](docs/00-overview/status-vocabulary.md)).*
4. **Auslieferungsformat entscheiden:** `release/`-Ordner, AAB, stabile Produktionssignatur — benötigt
   Eigentümerentscheidungen (Signatur-Key ist bewusst kein Agentenrecht).
5. **Lizenzentscheidung** des Repository-Eigentümers einholen.

## 7. Fazit

Der Repository-Kern ist ein **ehrlicher, getesteter Teil der Master-Anforderung**: Evidenz-/Challenge-/Triage-/
Approval-/Stop-/Audit-Kern, PLAN mit Context Lock (mit den exakt übernommenen Kontexttypen), Memory/Archive/Cache
mit lokaler Suche und echtem Storage-Tier, Privacy-first-Modellgrenze mit `ExternalDataGateway`, nativer
Android-Client mit realer SDK-/Emulator-Pipeline und berichteter APK-Auslieferung, dazu disziplinierte CI und
Dokumentation. Die Konversation liefert darüber hinaus die vollständige Ausbauspezifikation (Orchestrator, Agenten,
Geräte, Telemetrie, 3D, Web-Recherche, Ressourcen-Manager), die im Repo durchgängig als NOT IMPLEMENTED/PLANNED
ausgewiesen ist — ohne Platzhalterverzeichnisse oder erfundene Erfolgsmeldungen. Wesentliche Korrekturempfehlung
ist die Übernahme der 2-GB-/Free-Tier-Neuinterpretation; die übrigen Deltas sind dokumentierte, bewusste Grenzen
des aktuellen Inkrements.
