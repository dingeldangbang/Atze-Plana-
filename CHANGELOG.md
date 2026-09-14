# Changelog

## Unreleased — Kernverträge, Stop-Provenienz und Testlücken (0.4.0.dev0)

### Added
`stop_state`-Record: jeder Stop-Wechsel schreibt Revision, Rolle, Zeitstempel und Record-ID unveränderlich in derselben Transaktion wie die `control`-Tabelle. `GET`/`POST /api/control/stop` liefern diese Provenienz; ohne passenden Record bleiben die Werte null/0. Neun neue ausführbare Fälle: CH-018..021 (Worker-Transport, Redirect-/Fehlerverweigerung, CLI-Exitcodes, realer Modul-Kindprozess, Dauerpollen), MCP-012 (Policywechsel zwischen Reservierung und Dispatch), PLAN-016/017 (versionsloser PLAN, Binding-Drift), STO-011/012 (nicht konfigurierte Tier/nicht kanonischer Schlüssel, konkurrierender Modusmarker), DOC-005 (Schema-only-Instanz), plus zwei neue Origin-Grenzfälle in AI-007 und sechs neue MCP-002-Fehlerfälle.

### Changed
Alle 16 bisher vertragslosen Kern-Operationen deklarieren `x-role`/`x-side-effects`; `scripts/docs.py` lehnt eine Operation ohne Vertrag jetzt ab, statt Rollen/Effekte zu erraten. MCP-Testpeer spricht HTTP/1.1 und prüft damit das reale Timeout-Nachziehen pro Lesevorgang. SEC-005 prüft Stop-Provenienz statt nur `active`/`reason`.

### Fixed
`GET /health` brach in einer `schema_only`-Instanz mit einem unbehandelten `AttributeError` ab und meldet jetzt 503 mit explizitem Grund. `plan_service.status()` lieferte für eine PLAN-Identität ohne gespeicherte Version einen unbehandelten Fehler statt `BLOCKED`/`NO_PLAN_VERSION_RECORDED`.

### Security
Health behauptet keinen Erfolg ohne echte Datenbankprüfung. Stop-Zustand ist nachvollziehbar, ohne dass fehlende Provenienz erfunden wird. Worker-Transporttests belegen, dass das Servicecredential bei Redirects nicht weitergeleitet wird und ein Serverfehler keinen Report erzeugt. Coverage-Lücken in Gateway/Storage/MCP-Client geschlossen; beide bisher unbeobachteten Gate-Zweige (`MCP_POLICY_CHANGED`, `PLAN_CONTEXT_CHANGED`) sind regressionsgeprüft.

### Breaking Changes
Keine. `Stop` erhält zusätzliche Felder mit Defaults; bestehende Clients lesen weiterhin `active`/`reason`. `stop_state` ist ein additiver Recordkind.

### Migration
Additiv, kein Schemaeingriff: `stop_state` nutzt die vorhandene `records`-Tabelle. Legacy-Bestände ohne solche Records melden `revision=0`/`actor=null`; die `control`-Tabelle bleibt maßgeblich, bestehende Stop-Zustände wirken unverändert.

### Validation
188 lokale Tests PASS, 99 % App-Statement-Coverage (1940 Statements, 1 Lücke: `challenge_worker.py:64` läuft real im Kindprozess und erscheint nicht im Elternzähler), 2 bekannte Warnungen. Realer HTTP-Smoke normal und `-O`: je 43 geprüfte Responses, 4 separate Workerprozesse mit Exitcode 0. Paketbuild, `scripts/docs.py --check`, `scripts/reality_check.py`, `node --check` und `tests/universe_harness.py --execute --scope core` (5 Checks PASS, Verdict PARTIAL) tatsächlich ausgeführt. Browser-E2E, Dependency-Audit, Remote-CI, Modell-/Android-Pipeline und Lasttest in diesem Schnitt NOT RUN. [Addendum](FINAL_VALIDATION_REPORT.md).

## Unreleased — Privacy-first model boundary, partial integration
- Fixed actual SQLite/FastAPI sync dependency thread-handoff error observed in live preview; one connection per unit of work remains, real two-thread commit/rollback regression added.
- Provider-neutral contracts and real OpenAI-compatible text transport through an explicit model data gate. LOCAL/SELF_HOSTED/PRIVATE_ENDPOINT/EXTERNAL_PROVIDER policy categories, empty defaults.
- Reviewer-only metadata/policy/exact-context consent, local-only lock, allowlists, selected same-project/task context, conservative classification and secret-pattern rejection, durable unknown-outcome audit, no automatic fallback/tool execution/adoption.
- Actual isolated HTTP/TLS security tests; NOT a local HF model/agent/MCP validation. Full requested integration remains BLOCKED; see model-gateway contract and validation report.

## 0.3.0 — unreleased / 2026-09-14

### Added
ADR-004, immutable Result Packages und obligatorische Challenge-Jobs. Separater HTTP-Worker mit dritter Credential, fünf deterministischen Prüfarten, projektweiter Evidence-Gegenprüfung und belegten alternativen Kandidaten. Warum?/Herausfordern/Quellen in UI. Versions-/Fingerprint-/Leasegebundene Reports, explizite reviewergebundene Adoption und aktuelle RAG-Decision-Provenance.

### Changed
Jede freigabefähige Taskentscheidung benötigt aktuellen Challenge-Pass. Approval an Result/Challenge/Context gebunden. Stopreset, neue Evidence/Result/Challenge entwerten vorherige Freigaben. Smoke prüft echte getrennte Workerprozesse statt eines erfundenen PASS. Existing Tests an das verschärfte Gate angepasst, nicht umgangen.

### Fixed
Bisherige Direktfreigabe ohne Gegenprüfung und direkte neue fact/decision-Memory-Übernahme blockiert. Primärfreitext wird nicht automatisch aus strukturiertem PASS adoptiert. Stale Memory-Passes in Retrieval werden neu geprüft. Scope-/Findinggrenzen führen zu BLOCK statt unvollständigem PASS.

### Security
Operator/Reviewer können keine Workerreports setzen; Worker keine Primär-/Approvalrechte. Replay, Leaseablauf, Snapshot-/Policyänderung und manipulierte Reports abgewiesen. Kein Worker-Fallback/Executor. Keine unabhängige Web-/Quellen-/Kausalitätsprüfung vorgetäuscht; Same-Host-Prozess ist keine Sandbox.

### Breaking Changes
Tasks ohne aktuellen Result-/Challenge-Pass sind BLOCKED, alte Approvals ohne Bindung nicht gültig. Neue direkte fact/decision-Memory-POSTs 409. Dritter Token und separater Worker erforderlich. High-impact-/Action-/Calculation-Gates bewusst eingeschränkt.

### Migration
Additive result/challenge_job/challenge_report Records und optionale strukturierte Evidence-Beobachtungen. Alte Daten bleiben erhalten; keine automatisch erzeugten Ergebnisse/Reports. Neue echte Pakete und Gegenprüfungen erforderlich. API und Worker zusammen auf dieselbe Policyversion aktualisieren.

### Validation
Siehe [aktuellen Bericht](FINAL_VALIDATION_REPORT.md). Nur überprüfte strukturierte lokale Datenverträge, keine freigeschalteten Geräte-/Cloud-/Primary-Agentfähigkeiten.

## 0.2.1 — unreleased / 2026-09-14

### Added
Verbindliche REALITY_POLICY und AGENTS-Regeln; getrenntes Integrations-/Nachweisaudit. ATZE_MODE mit persistenter DB-/Objektrootbindung, authentifizierter Runtime-Modusanzeige, enge CI-Reality-Grenzprüfung und Regressionen gegen Testdatenkontamination.

### Changed
Smoke startet ausschließlich eigene reale temporäre Testinstanz/Dateien/Tokens; keine übergebene Ziel-URL oder geerbten ATZE-Daten. Normale pytest-Fixtures explizit test. Storage-Status trennt Implemented/Configured/Verfügbarkeit. UI kennzeichnet Testmodus und leert alte Werte bei Ladefehlern. README bezeichnet die reale Arbeitsoberfläche nicht mehr als Demo.

### Fixed
Mögliche fehladressierte Fixturewrites im alten Smoke; stale PASS-Dateien bei Ausführungsfehlern; via python -O entfernbare Smoke-Assertions; irreführende Sammel-Verfügbarkeitsmeldung und erfundener 100%-Wert bei nicht messbarer Gesamtkapazität.

### Security
Kein Testprovider/Mock im Betriebsweg. Cross-Mode-DB-/Rootzugriff verweigert; Legacy-Daten nicht als echte Messungen zertifiziert. Modusmarker sind kein Schutz gegen Hostadministratoren. Reale Capacity-Alternative bleibt ein echter Datenträgerzugriff, kein Fakefallback.

### Breaking Changes
`--base-url` im Smoke entfernt. `ATZE_MODE` akzeptiert operational/test; Wechsel bestehender markierter Datenbestände abgelehnt. Neue API-Statusfelder und Healthversion 0.2.1.

### Migration
Additive SQLite instance_mode-Tabelle und `.atze-mode` in konfigurierten erreichbaren Wurzeln. Bestehende unmarkierte Bestände bleiben im operational-Modus möglich, müssen inhaltlich auf Herkunft geprüft werden. Testmodus nimmt keine unmarkierten nonempty Bestände an. Marker mit sichern; keine Daten werden automatisch gelöscht oder importiert.

### Validation
Aktuelle tatsächliche Ergebnisse im [Validierungsbericht](FINAL_VALIDATION_REPORT.md). Keine neuen Hardware-/Provider-/APK-/Releasefähigkeiten behauptet.

## 0.2.0 — unreleased / 2026-09-13

### Added
ADR-003 als zentrale Mobile-/Context-/Storage-Zielarchitektur. Lokale immutable UTF-8-Archive mit Unified Namespace, hashgeprüfte Copy/Verify/Index-Relocation und Source Retention. Append-only Project Memory mit fact/inference-Trennung und Evidence-/Task-/attestierter Commitbindung. Lokale FTS5-Retrieval-Vorstufe mit Provenance und Reindex. Taskgebundener TTL-Cache mit Tombstone-/Retry-Cleanup. Echte Storage Health, konservative Local→SD-Erstplatzierung und UI-Quellen-Suche.

### Changed
Core speichert Metadaten/Memory/Index in SQLite, Original-/Cachetexte zusätzlich in konfigurierten Dateiwurzeln. API-/Dokumentations-/Testkatalog automatisch erweitert. Bestehende v0.1-Funktionen bleiben erhalten; 27 ursprüngliche Tests weiterhin enthalten. MCP, Remote-Tiers, Offline Queue/Sync und mobile Hardware bleiben explizite Zielmodule.

### Fixed
SQL-Dependencies schließen ihre Transaktion jetzt vor der HTTP-Erfolgsantwort ab (`scope=function`); zwei Regressionen prüfen Commitzeitfehler im Core und Archivpfad.

Dokumentationsaussagen zu fehlender Textablage/Context-Suche und DB-only Backup an die neue Implementierung angepasst. Logical path resolution bleibt nach Tierwechsel stabil. Cache-Cleanup behandelt Crash nach Delete vor Audit über vorher persistierte Tombstones und Retry.

### Security
Physische UUID-Namen, `O_NOFOLLOW`, Größen-/Hashprüfung, fsync und Quellkopie-Erhaltung. Relocation/Cleanup/Reindex reviewergebunden; Storage-Mutationen durch Stop blockiert. Retrieval erteilt keine Ausführungserlaubnis und macht Inferenz nicht zu Fakt. Keine Policy-/Executor-/MCP-Umgehung.

### Breaking Changes
POSIX-Dateisystem und SQLite-FTS5 benötigt. DB-only Backup enthält nicht mehr alle Originaldaten. Neue Roots gehören in ein Gesamtsicherungskonzept. Health-Version 0.2.0; bestehende Domain-API unverändert.

### Migration
Additive Namespace-/FTS-Tabelleninitialisierung, vorhandene Records/Control bleiben erhalten. Neue optionale `ATZE_STORAGE_ROOT` / `ATZE_SD_ROOT`. Kein automatischer Import alter Evidence oder externen Projektmaterials. Keine automatische Cloud-/SD-Mount-/Dateilöschaktion.

### Validation
Siehe [aktuellen Bericht](FINAL_VALIDATION_REPORT.md); nur lokale Testverzeichnisse, keine realen SD-/Mobile-/MCP-/Cloud-Nachweise.

## 0.1.0 — unreleased / 2026-09-13

### Added
Single-Workspace FastAPI/SQLite-Kern; Projekte, Evidenz mit SHA-256 und Herkunft, unveränderliche Aufgaben, manuelle Evidenzprüfung, deterministische Triage, getrennte Freigaberolle, persistenter Stop, Audit, statisches Dashboard. OpenAPI- und Dokumentationsworker, Tests, Build-/Dokumentations-/Security-CI.

### Changed
README vom bloßen Projekttitel zur überprüfbaren Funktions- und Statusübersicht erweitert. Dokumentation entsteht parallel zum Kern und enthält fehlende Module ausdrücklich.

### Fixed
Im ersten Regressionstest gefundene SQLite-WAL-Aktivierung innerhalb einer Transaktion auf Initialisierung außerhalb der Transaktion verlegt.

### Security
GitHub Actions auf vollständige, über die GitHub-API aufgelöste Commit-SHAs gepinnt; Repository-Policy blockierte den ersten CI-Start korrekt.

Zunächst gefundene verwundbare transitive Starlette-Version aktualisiert; Advisory-Abgleich erneut ausgeführt. Startup ohne sichere getrennte Tokens blockiert. Keine externen Actions oder Shell-Tools.

### Breaking Changes
Keine bestehende Runtime oder Schnittstelle im Ausgangsrepository vorhanden. Neue API ist experimentell.

### Migration
Leeres Repository → frische SQLite-Schema-v1-Datei. Keine Upgrade-Migrationen.

### Validation
Siehe [Final Validation Report](FINAL_VALIDATION_REPORT.md). Keine Hardware- oder Produktionsvalidierung.

## Master increment — real worker and native Android candidates (unreleased)
- Pinned local-model artifact manifest + actual isolated inference runner/CI, separate from transport-receipt tests. Default operational policy unchanged.
- Native Java Android read-only HTTPS Core client, TLS1.2/1.3-only sockets, no token persistence/cleartext/redirect fallback, no device/repair buttons pretending integration.
- Official SDK build/sign/verify/checksum and emulator installation/start/instrumentation pipeline; local SDK preflight fails explicitly, CI outcomes recorded separately.
- Added APK_RELEASE_REPORT, TEST_REPORT and master acceptance matrix. No overall platform/production release declared.

## 2026-09-14 — bounded PLAN increment (unreleased)
Append-only task contexts, actual source/dependency hashes, reviewer lock/revoke, mandatory Challenge/Triage/AI binding, API/UI and real browser pipeline. Challenge policy migration requires new reports. Saved AI context SHA verified before transport. No full-platform/production release or added device execution. Validation evidence maintained in root reports.
