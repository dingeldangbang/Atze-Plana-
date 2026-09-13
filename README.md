# Atze Plana

Evidence- und Freigaberegister für einen einzelnen Workspace. **Version 0.1.0 ist ein begrenzter, lauffähiger Kern, nicht die vollständige Plattform der Master-Anforderung.** Das Ausgangsrepository enthielt nur einen Titel; siehe [Bestandsaufnahme](PROJECT_BASELINE.md).

## Tatsächlicher Status
| Bereich | Status | Nachweis / Grenze |
|---|---|---|
| Projekte, Evidenz, Aufgaben, Triage, Freigabe, Stop, Audit | IMPLEMENTED / TESTED | [Tests](docs/14-testing/test-catalog.md) |
| Python-Paket, OpenAPI, Dokumentationskonsistenz | VALIDATED lokal | [Validierungsbericht](FINAL_VALIDATION_REPORT.md) |
| Dashboard | IMPLEMENTED | Projektanlage, Listen, Triage; weitere Eingaben via API |
| Produktionsbetrieb, 2-GB-Kapazität | CONDITIONAL | Kein Lasttest, kein Deployment, Ingress erforderlich |
| Vollplattform-Release | BLOCKED | Module, Hardware- und Produktionsnachweise fehlen |
| Agenten, Sandbox, Hardware, 3D, Android, Cloud, Bright Data, Trends | PLANNED / NOT IMPLEMENTED | [Modulmatrix](docs/00-overview/roadmap.md) |

## Architektur
Browser → FastAPI → SQLite. Operator erfasst Daten; Reviewer prüft Evidenz und genehmigt Aufgaben. Deterministische Triage erzeugt begründete Entscheidungen. **Freigabe ist keine Ausführung.** Es gibt keine Shell-, Flash-, Cloud- oder Geräteanbindung.

## Quick Start
Python 3.11+, Git und Internet für die Installation:

```sh
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.lock
cp .env.example .env
# Zwei verschiedene zufällige Tokens in .env eintragen (je >=32 Zeichen).
set -a; . ./.env; set +a
uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000
```

`http://127.0.0.1:8000` im lokalen Browser öffnen; bei Arena die Port-Vorschau verwenden. API-Token im Dashboard eingeben. Keine Demo-Geräte oder vorausgefüllten Messwerte. Vollständige Anleitung mit API-Beispiel: [QUICKSTART](QUICKSTART.md).

## Entwicklung und Betrieb
- [Installation](INSTALL.md), [Entwicklung](DEVELOPMENT.md), [Produktion](PRODUCTION.md)
- [Dokumentation](docs/README.md), [API/OpenAPI](openapi.yaml), [Benutzerhandbuch](docs/user/getting-started.md)
- [Tests](docs/14-testing/testing-strategy.md), [Security](SECURITY.md), [Threat Model](THREAT_MODEL.md)
- [Beiträge](CONTRIBUTING.md), [Changelog](CHANGELOG.md), [Releaseplan](RELEASES.md)

## Demo / Screenshots
Die mitgelieferte Oberfläche unter `/` ist die ausführbare Demo und startet ohne Seed-Daten. Noch kein versionierter Screenshot und kein öffentliches Deployment. Ihre Grenzen sind im Benutzerhandbuch beschrieben.

## Lizenz
Im Ausgangsrepository wurde keine Lizenz festgelegt. Es wird keine Nutzungs- oder Weiterverbreitungslizenz erfunden. Eine Lizenzentscheidung des Repository-Eigentümers ist vor externer Distribution erforderlich.
