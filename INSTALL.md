# Installation

[Quickstart](QUICKSTART.md) enthält alle ausgeführten Installationsbefehle. `requirements.lock` pinnt Laufzeit- und Entwicklungsabhängigkeiten für die geprüfte Python-Umgebung; es enthält noch keine Artefakt-Hashes oder plattformübergreifende Lock-Metadaten.

## Komponenten
| Komponente | Installation / Zustand |
|---|---|
| Backend / Frontend | Ein FastAPI-Prozess mit statischen Dateien; kein Node-Build |
| Datenbank | SQLite aus Python-Standardbibliothek, lokaler beschreibbarer Pfad; Initialisierung beim Start |
| Object Storage | NOT IMPLEMENTED; Evidenztext bis 20.000 Zeichen in SQLite |
| Local Bridge / Workers | NOT IMPLEMENTED; keine zusätzlichen Dienste starten |
| 3D / Unity / Android | NOT IMPLEMENTED; keine SDK-Version oder Buildfähigkeit behauptet |
| GitHub / CI | Workflow im Repository; keine Zugangsdaten für lokale Tests erforderlich |

## Paket bauen
`python -m build` erzeugt Wheel und sdist unter `dist/`. Deployment muss statische Dateien aus dem Wheel enthalten. `uvicorn app.main:create_app --factory` nutzt die gleiche Factory im Checkout und im installierten Paket. Datenpfad sollte für Dienste absolut sein.

## Datenmodell / Migration
Schema v1 wird per `CREATE TABLE IF NOT EXISTS` erstellt. Keine Upgrade-Migrationen und kein Import bestehender Fremddaten. Bei künftigen Schemaänderungen zuerst versionierte Migrationen und Restore-Test einführen. Mehrere Replikate, Netzlaufwerke und nicht lokales SQLite sind nicht unterstützt.

Konfiguration: [Referenz](docs/19-operations/configuration.md). Produktion: [Gate](PRODUCTION.md).
