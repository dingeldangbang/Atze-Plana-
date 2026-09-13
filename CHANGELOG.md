# Changelog

## 0.1.0 — unreleased / 2026-09-13

### Added
Single-Workspace FastAPI/SQLite-Kern; Projekte, Evidenz mit SHA-256 und Herkunft, unveränderliche Aufgaben, manuelle Evidenzprüfung, deterministische Triage, getrennte Freigaberolle, persistenter Stop, Audit, statisches Dashboard. OpenAPI- und Dokumentationsworker, Tests, Build-/Dokumentations-/Security-CI.

### Changed
README vom bloßen Projekttitel zur überprüfbaren Funktions- und Statusübersicht erweitert. Dokumentation entsteht parallel zum Kern und enthält fehlende Module ausdrücklich.

### Fixed
Im ersten Regressionstest gefundene SQLite-WAL-Aktivierung innerhalb einer Transaktion auf Initialisierung außerhalb der Transaktion verlegt.

### Security
Zunächst gefundene verwundbare transitive Starlette-Version aktualisiert; Advisory-Abgleich erneut ausgeführt. Startup ohne sichere getrennte Tokens blockiert. Keine externen Actions oder Shell-Tools.

### Breaking Changes
Keine bestehende Runtime oder Schnittstelle im Ausgangsrepository vorhanden. Neue API ist experimentell.

### Migration
Leeres Repository → frische SQLite-Schema-v1-Datei. Keine Upgrade-Migrationen.

### Validation
Siehe [Final Validation Report](FINAL_VALIDATION_REPORT.md). Keine Hardware- oder Produktionsvalidierung.
