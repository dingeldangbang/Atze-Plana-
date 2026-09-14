# Atze Plana

Evidence- und Freigaberegister für einen einzelnen Workspace. **Entwicklungsstand 0.4.0.dev0 ist ein begrenzter, lauffähiger Kern, nicht die vollständige Plattform der Master-Anforderung.** Das Ausgangsrepository enthielt nur einen Titel; siehe [Bestandsaufnahme](PROJECT_BASELINE.md).

## Tatsächlicher Status
| Bereich | Status | Nachweis / Grenze |
|---|---|---|
| Projekte, Evidenz, Aufgaben, obligatorische Challenge/Triage, Freigabe, Stop, Audit | IMPLEMENTED / TESTED | [Tests](docs/14-testing/test-catalog.md) |
| Python-Paket, OpenAPI, Dokumentationskonsistenz | VALIDATED lokal | [Validierungsbericht](FINAL_VALIDATION_REPORT.md) |
| Memory / Archive / Cache / lokale FTS-Suche | IMPLEMENTED / TESTED | [Neue Context-/Storage-Architektur](docs/20-context-storage/architecture.md); kein MCP-/Cloud-/Offline-Sync-Adapter |
| Challenge Worker / Result Packages | IMPLEMENTED / begrenzt | [Eigener Prozess, Token, fünf Checks, Staleness-/Adopt-Gate](docs/02-core/challenge-worker.md); keine unabhängige Online-Recherche |
| Modell-Policy / Text-Gateway | IMPLEMENTED / transportgetestet | Default DENY; separate reale HF-Modell-CI; kein operativer Modellworker, MCP oder Agentensandbox |
| PLAN / Context Lock | IMPLEMENTED / API- und browsergetestet | [Versionen, echte Quellen, Lock/Widerruf, Challenge-/Triage-/AI-Bindung](docs/21-plan/context-lock.md); keine Wahrheit oder Ausführungsrechte |
| Dashboard | IMPLEMENTED | Reale PLAN-Bedienung ergänzt; 7 echte Chromium-PLAN-Prüfungen PASS; Resultate im Testbericht |
| GitHub-CI / Review-PR | siehe aktuellen Bericht | [PR #1](https://github.com/dingeldangbang/Atze-Plana-/pull/1); kein Merge/Release |
| Produktionsbetrieb, 2-GB-Kapazität | CONDITIONAL | Kein Lasttest, kein Deployment, Ingress erforderlich |
| Vollplattform-Release | BLOCKED | Module, Hardware- und Produktionsnachweise fehlen |
| Agenten, Vollsandbox, Hardware-Repair, 3D, Cloud, Bright Data, Trends | PLANNED / NOT IMPLEMENTED | [Modulmatrix](docs/00-overview/roadmap.md) |

## Architektur
Browser → FastAPI → SQLite (Metadaten, Memory, FTS) + externe Original-/Cacheblobs (Local, optional SD-Verzeichnis). [ADR-003](docs/adr/ADR-003-mobile-context-storage.md) definiert Mobile Project Server + MCP/RAG als Zielarchitektur; MCP, Remote-Tiers und Offline-Sync sind noch nicht implementiert. Operator erfasst Daten; Reviewer prüft Evidenz und genehmigt Aufgaben. Ein separater Challenge-Prozess prüft strukturierte Result-Pakete vor jeder freigabefähigen Taskentscheidung. Die Triage akzeptiert nur aktuelle Gegenprüfungen. Primärfreitext wird nicht automatisch als Fakt übernommen. **Freigabe ist keine Ausführung.** Es gibt keine Shell-, Flash-, Cloud- oder Geräteanbindung.

## Quick Start
Python 3.11+, Git und Internet für die Installation:

```sh
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.lock
cp .env.example .env
# Operator-/Reviewer-Token setzen; für Challenge einen DRITTEN separaten Token setzen (je >=32 Zeichen).
set -a; . ./.env; set +a
uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000
```

`http://127.0.0.1:8000` im lokalen Browser öffnen; bei Arena die Port-Vorschau verwenden. API-Token im Dashboard eingeben. Keine Demo-Geräte oder vorausgefüllten Messwerte. Vollständige Anleitung mit API-Beispiel: [QUICKSTART](QUICKSTART.md).

## Entwicklung und Betrieb
- [Installation](INSTALL.md), [Entwicklung](DEVELOPMENT.md), [Produktion](PRODUCTION.md)
- [Dokumentation](docs/README.md), [API/OpenAPI](openapi.yaml), [Benutzerhandbuch](docs/user/getting-started.md)
- [Tests](docs/14-testing/testing-strategy.md), [Security](SECURITY.md), [Threat Model](THREAT_MODEL.md)
- [Beiträge](CONTRIBUTING.md), [Changelog](CHANGELOG.md), [Releaseplan](RELEASES.md)

## Arbeitsoberfläche / Screenshots
Die Oberfläche unter `/` bedient die tatsächlich implementierten APIs und startet ohne Seed-Daten. Sie ist keine Demo-Implementierung. Noch kein versionierter Screenshot und kein öffentliches Deployment. Ihre Grenzen sind im Benutzerhandbuch beschrieben.

## Lizenz
Im Ausgangsrepository wurde keine Lizenz festgelegt. Es wird keine Nutzungs- oder Weiterverbreitungslizenz erfunden. Eine Lizenzentscheidung des Repository-Eigentümers ist vor externer Distribution erforderlich.

## Kein Fake im Betriebsweg
Verbindlich: [REALITY_POLICY](REALITY_POLICY.md), [Integrations-/Realitätsaudit](docs/17-security/reality-audit.md). Implemented, Configured, Tested, Validated und Production Ready werden getrennt ausgewiesen. Testmodus aktiviert keine Mocks; Tests nutzen ausschließlich eigene temporäre Datenbestände und echte lokale Komponenten. Nicht erreichbare Ressourcen liefern Fehler/unknown statt Beispieldaten.

## Every Decision Must Survive Challenge
[ADR-004](docs/adr/ADR-004-challenge-before-decision.md). Ohne konfigurierten und separat laufenden Worker bleiben Tasks blockiert. Worker separat mit nur seinem Service-Token starten: `python -m app.challenge_worker --url http://127.0.0.1:8000`. [Scope, Limits und Betriebsanleitung](docs/02-core/challenge-worker.md). ACCEPT gilt nur für eingereichte strukturierte Claims, nicht für unvalidierte Primärtexte, Geräte-/Kausalitäts-/Produktionsaussagen.

## Privacy-first Modellgrenze (experimenteller Teilschritt)
[Model Gateway](docs/02-core/model-gateway.md) ergänzt explizite lokale/Remote-Policy, manuelles Modellregister, ausgewählten Kontext und Reviewer-Freigabe vor echtem Text-HTTP-Transport. Default: Local-only, External DENY, keine Provider. Kein operativ installiertes HF-Modell (separate gepinnte Modell-CI ist real ausgeführt), keine smolagents-/MCP-/Sandboxintegration und kein universeller OS-Egress-Lock. Diese vollständigen Integrations-/Release-Gates bleiben BLOCKED. Vorhandene Challenge/Triage bleibt unverändert zwingend.

## Master-Anforderung: nächste reale Abnahme
Separater [lokaler Modell-Integrationslauf](docs/14-testing/local-model-validation.md) mit gepinnten Gewichten/Runtime und ein [nativer Android-Core-Client](android/README.md) mit echter Build-/Emulator-Pipeline. Diese Pipelines sind keine Erfolgsmeldung: [Testbericht](TEST_REPORT.md), [APK-Bericht](APK_RELEASE_REPORT.md), [Finale Validierung](FINAL_VALIDATION_REPORT.md) nennen nur ausgeführte Ergebnisse. Keine Dummy-Verzeichnisse für fehlende Geräte-/Unity-/MCP-/Cloudmodule. Gesamtplattform bleibt bis zur vollständigen Abnahme BLOCKED.

### Tatsächlich geprüfte neue Deliverables
[Lokaler Modell-CI-Nachweis](TEST_REPORT.md): gepinnte Qwen-Inferenz, keine externe Inferenz, nicht-root/Loopback-only. [Android-Debug-APK und SHA256](APK_RELEASE_REPORT.md): echt gebaut/signiert, installiert/gestartet/getestet im SDK-Emulator. Native App ist ein kleiner Read-only-Core-Statusclient, keine volle Device-/Repair-/Agentplattform. Gesamtfreigabe bleibt BLOCKED.

## PLAN-Inkrement
[Context-Lock-Vertrag](docs/21-plan/context-lock.md): genau ein PLAN je Task, unveränderliche Quellenfassungen, Reviewer-Sperre/Widerruf. Neue Challenge-Policy `challenge-2-context` erfordert erneute Gegenprüfung vorhandener Results. Kein universeller Object Workspace/Executor. Aktuelle tatsächlich ausgeführte Gates im [Testbericht](TEST_REPORT.md).
