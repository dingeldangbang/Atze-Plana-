# Changelog

## Unreleased — Resource manager increment (module 3)
- Reale versionierte Resource-Registry (Backend-Pfad zur PLAN-UI-Spezifikation Abschnitt 17–19): Operator-Upload als Base64 (≤4 MiB dokumentierte Grenze) mit SHA-256/Größe/Tier-Speicherung und Hash-Verifikation beim Lesen; append-only Versionierung mit family_id/predecessor_id (identischer Content 409); Referenz-Links auf existierende Tasks/Projekte statt Kopien, Unlink append-only mit Historie; Byte-Vergleich (IDENTICAL/DIFFERENT mit gemeinsamen Prä-/Suffixbytes); Suchfilter (Name-Teilstring, SHA-256-Präfix, kind/state); reviewerbestätigte familienweite Deaktivierung ohne Datenlöschung; Not-Stop blockt Mutationen, nicht Reads; Audit-Kette resource.*. 16 neue Tests (RES-001..016), 216 PASS. Kein Viren-/Safety-Scan und keine Inhaltsinterpretation (NOT IMPLEMENTED); Herkunft deklariert, nicht verifiziert.


## Unreleased — Trend engine increment (module 2)
- Reale Trend-Engine als deterministische Query (CQRS, lesend, ohne Nebenwirkungen/Audit, bei jedem Aufruf aus unveränderlichen Batches neu berechnet): fünf dokumentierte statistische Prüfarten (Drift mit Steigung/SNR, Level-Shift, Varianzänderung, Out-of-Range-Rate, Suspect-Rate) über hash-verifizierte Telemetrie-Batches eines Sensors, optional pro Session; Kriterien-Endpoint mit exakten Schwellen; VERIFIED TREND vs. INSUFFICIENT EVIDENCE mit expliziten failed_criteria; Arbeitsgrenzen 200 Batches/200.000 Samples (422); Blob-Korruption fail-closed 503; Not-Stop blockt Leseanalyse nicht. 17 neue Tests (TRD-001..017), 200 PASS. CALCULATED, nie MEASURED; kein ML, keine Prognose; keine Validierung an realer Hardware (NOT RUN).


## Unreleased — Telemetry increment, PLAN-UI specification, partial integration
- Reales Telemetrie-Modul (Modul 1 der bestätigten Umsetzungsreihe „alles der Reihe nach"): deklarative Device-/Sensor-Registry (Operator), HTTP-Ingestion mit getrenntem Device-Fleet-Token (ATZE_TELEMETRY_TOKEN; leer = fail-closed 403), unveränderliche, versionierte, hash-/größenverifizierte Messbatches über den bestehenden Storage-Tier, Out-of-Range-/Suspect-Flagging, reviewerbestätigte Einzel-Deaktivierung ohne Datenlöschung, Not-Stop-Integration. 14 neue Tests, 183 PASS. WS/MQTT/Serial NOT IMPLEMENTED; keine physische ESP32-Validierung (NOT RUN); Werte sind eingereichte Device-Angaben.
- Verbindliche PLAN-UI-/Interaktions-/Code-/Abhängigkeitsspezifikation (Nutzervorgabe 2026-09-14) aufgenommen: jede sichtbare UI-Funktion benötigt einen realen technischen Pfad (UI → Command/Query → Domain → Dependency → Result → Audit/Test); keine Fake-Interaktion, keine toten Buttons, Action-/Dependency-Registry und Feature-Traceability als Abnahmekriterien künftiger UI-Inkremente. Spezifikation ist SOLL-Zustand, dokumentiert keinen Implementierungsstand.
- Fehlerbehebung: 422-Validierungsantworten serialisieren nicht-endliche Floats (NaN/Infinity) als Strings, statt beim Fehler-Echo einen JSON-Renderfehler (500) zu erzeugen; Schema-Ablehnung bleibt unverändert.

## Unreleased — Privacy-first model boundary, partial integration
- Abgleich der vollständigen ChatGPT-Masterkonversation (Reality First/No Fiction Data, Triage/Challenge, PLAN/Context Lock, APK-Auslieferungspflicht, 2-GB-Korrektur) gegen den tatsächlichen Repositorysstand: [MASTER_ABGLEICH](MASTER_ABGLEICH.md). Am 2026-09-14 tatsächlich ausgeführt: 169 lokale Tests PASS, docs.py --check PASS, reality_check.py PASS. Deltas (u. a. 2-GB-Neuinterpretation, Statusvokabular, Workflow-Editor, Auslieferungsformate) dokumentiert; kein Produkt-/Testcode geändert.
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
