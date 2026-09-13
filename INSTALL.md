# Installation

[Quickstart](QUICKSTART.md) enthält alle ausgeführten Installationsbefehle. `requirements.lock` pinnt Laufzeit- und Entwicklungsabhängigkeiten für die geprüfte Python-Umgebung; es enthält noch keine Artefakt-Hashes oder plattformübergreifende Lock-Metadaten.

## Komponenten
| Komponente | Installation / Zustand |
|---|---|
| Backend / Frontend | Ein FastAPI-Prozess mit statischen Dateien; kein Node-Build |
| Datenbank | SQLite aus Python-Standardbibliothek, lokaler beschreibbarer Pfad; Initialisierung beim Start |
| Original-/Cacheablage | v0.2: lokale UTF-8-Blobs bis 65.536 Zeichen pro Objekt, optional Betreiber-SD-Verzeichnis; kein Remote Object Store |
| Challenge Worker | separater realer Prüfprozess; python -m app.challenge_worker; eigener Token und HTTP-API |
| Local Bridge / Execution Workers | NOT IMPLEMENTED; Challenge ist kein allgemeiner Executor |
| 3D / Unity / Android | NOT IMPLEMENTED; keine SDK-Version oder Buildfähigkeit behauptet |
| GitHub / CI | Workflow im Repository; keine Zugangsdaten für lokale Tests erforderlich |

## Paket bauen
`python -m build` erzeugt Wheel und sdist unter `dist/`. Deployment muss statische Dateien aus dem Wheel enthalten. `uvicorn app.main:create_app --factory` nutzt die gleiche Factory im Checkout und im installierten Paket. Datenpfad sollte für Dienste absolut sein.

## Datenmodell / Migration
v0.2 ergänzt den v1-Kern additiv um einen Namespace-Index und SQLite-FTS5; bestehende Records bleiben erhalten. FTS5 und POSIX-Dateisystemoperationen sind erforderlich. Keine generelle versionierte Migrationsengine und kein Import bestehender Fremddaten. Bei künftigen Schemaänderungen zuerst versionierte Migrationen und Restore-Test einführen. Mehrere Replikate, Netzlaufwerke und nicht lokales SQLite sind nicht unterstützt.

**Backupänderung v0.2:** SQLite allein enthält nicht mehr die Original-/Cacheblobs. [Storage-/Restore-Grenzen](docs/20-context-storage/architecture.md) beachten.

Konfiguration: [Referenz](docs/19-operations/configuration.md). Produktion: [Gate](PRODUCTION.md).
