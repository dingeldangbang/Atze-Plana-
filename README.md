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
| Telemetrie (IoT-Ingest) | IMPLEMENTED / TESTED | [Device-/Sensor-Registry, fail-closed Device-Token, unveränderliche hash-verifizierte Batches](docs/23-telemetry/telemetry.md); kein WS/MQTT/Serial, keine physische ESP32-Validierung |
| Trend-Analyse (Telemetrie) | IMPLEMENTED / TESTED | [Deterministische Query-Checks mit dokumentierten Kriterien](docs/24-trends/trends.md); CALCULATED, kein ML, keine Prognose |
| Resource-Manager | IMPLEMENTED / TESTED | [Versionierte Datei-Registry mit SHA-256, Referenz-Links, Byte-Vergleich](docs/25-resources/resources.md); kein Virenscan, keine Inhaltsinterpretation |
| Agent Builder v1 | IMPLEMENTED / TESTED | [Deklarative Registry, Zuweisungen, Einzel-Runs durch die vollständige Consent-Kette](docs/26-agents/agents.md); keine autonome Tool-Ausführung, kein Orchestrator |
| Monitoring & Anbindungsverwaltung | IMPLEMENTED / TESTED | [Lesende Plattformübersicht, Integrations-Registry mit echten +/−-Routen](docs/27-monitoring/monitoring.md); kein Alerting, konfiguriert ≠ validiert |
| GitHub-CI / Review-PR | siehe aktuellen Bericht | [PR #1](https://github.com/dingeldangbang/Atze-Plana-/pull/1); kein Merge/Release |
| Produktionsbetrieb & Ressourcenrahmen | CONDITIONAL | „2 GB" = RAM der ausführenden Zielhardware (Honeywell CT45P-XON), kein Core-Speicherbudget; „Free Tier" = externe Anbieter-Nutzungsklasse, nie Datenersatz ([Begriffstrennung](docs/18-deployment/free-tier.md)). Kein Lasttest, kein Deployment, Ingress erforderlich |
| Vollplattform-Release | BLOCKED | Module, Hardware- und Produktionsnachweise fehlen |
| Agenten-Orchestrierung, Vollsandbox, Hardware-Repair, 3D, Cloud | PLANNED / NOT IMPLEMENTED | [Modulmatrix](docs/00-overview/roadmap.md) |

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
Separater [lokaler Modell-Integrationslauf](docs/14-testing/local-model-validation.md) mit gepinnten Gewichten/Runtime und ein [nativer Android-Core-Client](android/README.md) mit echter Build-/Emulator-Pipeline. Diese Pipelines sind keine Erfolgsmeldung: [Testbericht](TEST_REPORT.md), [APK-Bericht](APK_RELEASE_REPORT.md), [Finale Validierung](FINAL_VALIDATION_REPORT.md) nennen nur ausgeführte Ergebnisse. Keine Dummy-Verzeichnisse für fehlende Geräte-/Unity-/MCP-/Cloudmodule. Gesamtplattform bleibt bis zur vollständigen Abnahme BLOCKED. Abgleich der vollständigen Master-Konversation (ChatGPT-Link, External Source) mit dem tatsächlichen Repositorysstand: [MASTER_ABGLEICH](MASTER_ABGLEICH.md).

### Tatsächlich geprüfte neue Deliverables
[Lokaler Modell-CI-Nachweis](TEST_REPORT.md): gepinnte Qwen-Inferenz, keine externe Inferenz, nicht-root/Loopback-only. [Android-Debug-APK und SHA256](APK_RELEASE_REPORT.md): echt gebaut/signiert, installiert/gestartet/getestet im SDK-Emulator. Native App ist ein kleiner Read-only-Core-Statusclient, keine volle Device-/Repair-/Agentplattform. Gesamtfreigabe bleibt BLOCKED.

## PLAN-Inkrement
[Context-Lock-Vertrag](docs/21-plan/context-lock.md): genau ein PLAN je Task, unveränderliche Quellenfassungen, Reviewer-Sperre/Widerruf. Neue Challenge-Policy `challenge-2-context` erfordert erneute Gegenprüfung vorhandener Results. Kein universeller Object Workspace/Executor. Aktuelle tatsächlich ausgeführte Gates im [Testbericht](TEST_REPORT.md). Verbindliche [UI-/Interaktions-/Code-/Abhängigkeitsspezifikation](docs/21-plan/plan-ui-interaction-spec.md) ergänzt: jede sichtbare UI-Funktion benötigt einen realen technischen Pfad (Command/Query → Service → Dependency → Audit/Test), keine Fake-Interaktion, keine toten Buttons; Spezifikation ist Vorgabe, kein Implementierungsstand.

## Telemetrie-Inkrement (Modul 1 der bestätigten Umsetzungsreihe)
[Echter Ingest-Vertrag](docs/23-telemetry/telemetry.md): deklarative Device-/Sensor-Registry (Operator, +), HTTP-Ingestion mit getrenntem Device-Fleet-Token (leer = fail-closed 403), unveränderliche kanonische JSON-Batches mit sha256/Größenverifikation beim Lesen (Korruption → 503), Out-of-Range-/Suspect-Flagging gegen deklarierte (nicht kalibrierte) Ranges, reviewerbestätigte Einzel-Deaktivierung (−) ohne Datenlöschung, Stop-Integration. **WS/MQTT/Serial NOT IMPLEMENTED; keine physische ESP32-/Sensormessung validiert (NOT RUN); Werte sind eingereichte Device-Angaben, keine verifizierte physikalische Messung.**

## Bright Data MCP: Discovery + begrenztes tools/call (Modul 4)
[OAuth-Bearer-Handshake, begrenzte MCP-Erkennung und reviewerbestätigtes tools/call](docs/22-mcp/brightdata.md) für genau die zwei allowlisted Kandidaten (search_engine, scrape_as_markdown) implementiert; standardmäßig gesperrt, Einzelfreigabe je Aufruf, Argument-/Result-Grenzen, Argumente nur als Hash gespeichert. **Keine Live-Bright-Data-Abnahme (in dieser Umgebung NOT CONFIGURED — Provider-Hosts blockiert); kein Tool jenseits der Allowlist; Ergebnisse EXTERNAL_SOURCE, nie verifizierte Wahrheit.** Der isolierte TLS-Protokolltest ist Testinfrastruktur, kein Provider-Nachweis.

## Trend-Engine-Inkrement (Modul 2 der bestätigten Umsetzungsreihe)
[Deterministischer Analyse-Vertrag](docs/24-trends/trends.md): fünf dokumentierte statistische Prüfarten (Drift, Level-Shift, Varianzänderung, Out-of-Range-Rate, Suspect-Rate) als reine Query über unveränderliche Telemetrie-Batches; Kriterien-Endpoint macht alle Schwellwerte sichtbar; Not-Stop blockt Lesezugriffe nicht. **CALCULATED aus SUBMITTED Samples — nie MEASURED, keine Prognose (prediction: NONE), kein ML, keine Lifecycle-/Proaktivitätsengine; keine Validierung an realer Hardware (NOT RUN).**

## Resource-Manager-Inkrement (Modul 3 der bestätigten Umsetzungsreihe)
[Vertrag](docs/25-resources/resources.md): Base64-Upload (≤4 MiB, dokumentierte Grenze) mit SHA-256/Tier-Speicherung und Hash-Verifikation beim Lesen (Korruption → 503); append-only Versionierung mit Predecessor-Kette (identischer Content → 409); Referenz-Links auf existierende Tasks/Projekte statt Dateikopien (Unlink append-only mit Historie); Byte-Vergleich mit gemeinsamen Prä-/Suffixbytes; reviewerbestätigte familienweite Deaktivierung (confirm+reason) ohne Datenlöschung; Not-Stop-Integration; vollständige Audit-Kette. **Kein Viren-/Safety-Scan (NOT IMPLEMENTED, Betreiberverantwortung), keine PDF-/CAD-/Metadaten-Interpretation, kein Workflow-Attach, keine Herkunftsverifikation deklarierter Quellen.**

## Agent-Builder-Inkrement (Modul 5 der bestätigten Umsetzungsreihe)
[Vertrag](docs/26-agents/agents.md): Agenten als versionierte, deklarative Arbeitskonfigurationen (registriertes Modell, Zweck ⊆ Capabilities, Tools ⊆ MCP-Allowlist, Instruktion); Referenz-Zuweisungen auf Tasks/Projekte; Runs sind gebundene `ai_request`s — Vorbereitung durch alle prepare-Gates, **Ausführung nur mit Reviewer-Einzelconsent** über die unveränderte execute-Kette (Kontext-Hash, Policy-/Config-Aktualität, Allowlists, Privacy/Remote, Not-Stop, PLAN-Bindung); Replay geschützt; Outputs DRAFT_UNCHALLENGED und werden nie gespeichert oder adoptiert; vollständige Audit-Kette; reviewerbestätigte familienweite Deaktivierung. **Keine autonome Tool-Ausführung (allowed_tools ist deklarativer Rahmen — Tool-Aufrufe bleiben der reviewerbestätigte MCP-Pfad), kein Orchestrator/Scheduler/Sandbox; Transport nur gegen isolierten Loopback-Empfänger nachgewiesen (kein Modell, keine Live-Inferenz validiert).**

## Monitoring-&-Anbindungs-Inkrement (Modul 6 der bestätigten Umsetzungsreihe)
[Vertrag](docs/27-monitoring/monitoring.md): Lesende Plattformübersicht (`GET /api/monitoring/overview`) aggregiert ausschließlich echte gespeicherte Records — Ist-Zahlen je Zustand, Batch-Metadaten-Summen, Speicher-Tiers, Not-Stop-Flag — ohne jede Gesundheits-, Verfügbarkeits- oder Wahrheitsaussage (konfiguriert ≠ validiert). Integrations-Registry (`GET /api/integrations`) listet jede zur Laufzeit verwaltbare Anbindung mit ihren **echten** Add-/Remove-Routen, Rollen und Bestätigungspflicht; UI-Formulare rufen genau diese Routen auf (+ = Operator: Geräte, Sensoren, Ressourcen-Upload ≤4 MiB, Agenten), **− = Reviewer-bestätigte Deaktivierung mit Pflicht-Begründung** — Bestand, Historie und Audit bleiben vollständig erhalten, ein Lösch-Endpunkt existiert nicht; umgebungsgebundene Anbindungen (AI-Provider, Bright-Data-MCP, Telemetrie-Token) sind nur einsehbar. Feature-Gating ohne tote Buttons: Trend-Analyse ohne aktive Sensoren und Agenten-Deklaration ohne registriertes Modell gesperrt; 4 echte Chromium-Checks in CI (Ist-Zahlen im DOM, UI-Registrierung, bestätigte Deaktivierung, Gating). **Kein Metrics-/Alerting-Backend, kein Live-Polling, keine Provider-Erreichbarkeitsprüfung; voller Trend-Durchlauf im Browser entfällt ehrlich (Smoke-Instanz ohne Ingest-Token).**
