# Changelog

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
