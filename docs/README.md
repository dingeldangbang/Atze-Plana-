# Dokumentationsmodul

Die Dokumentation beschreibt den tatsächlich implementierten Kern. Nicht vorhandene Produktbereiche stehen in der [Roadmap/Modulmatrix](00-overview/roadmap.md), nicht in leeren Feature-Handbüchern. Das ist eine Anpassung der vorgeschlagenen 20-Bereiche-Struktur an den realen Code.

## Einstieg
- [Überblick, Ziele und Begriffe](00-overview/project-overview.md)
- [System](01-architecture/system-architecture.md), [Daten](01-architecture/data-architecture.md), [Security](01-architecture/security-architecture.md)
- [Kernverträge](02-core/core.md), [Triage](02-core/triage.md), [Evidence](16-evidence/evidence-model.md)
- [API](08-network/APIs.md), [OpenAPI](../openapi.yaml), [Code-Inventar](generated-inventory.md)
- [Teststrategie](14-testing/testing-strategy.md), [Testkatalog](14-testing/test-catalog.md)
- [2 GB](18-deployment/free-tier.md), [Betrieb](19-operations/operations.md), [Konfiguration](19-operations/configuration.md), [Troubleshooting](19-operations/troubleshooting.md)
- [Benutzer](user/getting-started.md), [Administration](admin/administration.md)
- [ADR 001](adr/ADR-001-evidence-core.md), [ADR 002](adr/ADR-002-documentation-product.md)

## Kontinuierlicher Vertrag
Design/Code/Test/Änderung benötigen im selben PR Dokumentationsänderung oder eine begründete Aussage, warum keine erforderlich ist. `scripts/docs.py` erzeugt Quellinventar, OpenAPI, API-Referenz und Testkatalog. `--check` erkennt Drift, validiert Spezifikation, lokale Dateilinks und Environment-Abdeckung. Menschliche Prüfung ergänzt semantische Korrektheit; automatische Prüfungen beweisen keine Hardwarefähigkeit.

## v0.2 — zentrale Context-/Speicherarchitektur
- [ADR-003](adr/ADR-003-mobile-context-storage.md): Mobile Project Server + MCP/RAG Memory Layer als Zielentscheidung
- [Tatsächliche Architektur und Migration](20-context-storage/architecture.md)
- [Memory/Archive/Cache/Resource/Retrieval-Verträge](20-context-storage/contracts.md)
- [Noch fehlende MCP-, Mobile-, Offline- und Remote-Stufen](20-context-storage/mobile-roadmap.md)

## Verbindliche Realitätsprüfung v0.2.1
[REALITY_POLICY](../REALITY_POLICY.md) gilt für jeden Beitrag. Keine Mock-/Demo-/Fake-Provider oder unbemerkten Fallbacks im Betriebsweg. Tests/Fehler-Injektionen bleiben getrennt; `python scripts/reality_check.py` und `python scripts/smoke.py --allow-fixtures` tatsächlich ausführen. Der Smoke startet ausschließlich seine eigene temporäre Testinstanz. Laufreports beweisen keine Geräte-/Providerintegration. [Getrennte Integrationsnachweise](../docs/17-security/reality-audit.md).

## v0.3 — Every Decision Must Survive Challenge
[ADR-004](adr/ADR-004-challenge-before-decision.md) · [Challenge Worker, fünf Prüfarten, API, Grenzen und Recovery](02-core/challenge-worker.md) · [aktuelle Triage](02-core/triage.md). Primary-Text bleibt unvalidiert; akzeptierte strukturierte Decision-Snapshots benötigen Gegenprüfung und explizite Übernahme. Kein allgemeiner Agent-/Webresearch-/Executor-Anspruch.

## Privacy-first Modellgrenze (experimenteller Teilschritt)
[Model Gateway](02-core/model-gateway.md) ergänzt explizite lokale/Remote-Policy, manuelles Modellregister, ausgewählten Kontext und Reviewer-Freigabe vor echtem Text-HTTP-Transport. Default: Local-only, External DENY, keine Provider. Kein operativ installiertes HF-Modell (separate gepinnte Modell-CI ist real ausgeführt), keine smolagents-/MCP-/Sandboxintegration und kein universeller OS-Egress-Lock. Diese vollständigen Integrations-/Release-Gates bleiben BLOCKED. Vorhandene Challenge/Triage bleibt unverändert zwingend.

## PLAN / Context Lock
[Vertrag, UI/API, Sicherheit, Migration und Grenzen](21-plan/context-lock.md) · [ADR-007](adr/ADR-007-plan-context-lock.md). Gebundene echte Quellen, keine Wahrheit/Toolberechtigung. [Verbindliche UI-/Interaktions-/Code-/Abhängigkeitsspezifikation](21-plan/plan-ui-interaction-spec.md): jede sichtbare UI-Funktion benötigt einen realen technischen Pfad; Spezifikation ist SOLL, nicht Implementierungsstand.

## Telemetrie (IoT)
[Echter Ingest-Vertrag: Device-/Sensor-Registry, fail-closed Device-Token, unveränderliche hash-verifizierte Batches, bestätigte Deaktivierung](23-telemetry/telemetry.md). Kein WS/MQTT/Serial, keine physische ESP32-Validierung, Werte sind eingereicht, nicht verifizierte physikalische Messung.

## Trend-Analyse
[Deterministische Query-Engine über ingestierte Messreihen: fünf dokumentierte Checks (Drift, Level-Shift, Varianzänderung, Out-of-Range-/Suspect-Rate) mit exakten Kriterien, VERIFIED TREND vs. INSUFFICIENT EVIDENCE](24-trends/trends.md). CALCULATED, nie MEASURED; kein ML, keine Prognose.

## Resource-Manager
[Versionierte Datei-Registry: Base64-Upload ≤4 MiB mit SHA-256/Tier-Speicherung, append-only Versionen, Referenz-Links auf Task/Projekt statt Kopien, Byte-Vergleich, reviewerbestätigte Deaktivierung ohne Löschung](25-resources/resources.md). Kein Virenscan (NOT IMPLEMENTED), keine Inhaltsinterpretation.

## Agent Builder v1
[Deklarative Agenten-Registry mit versionierter Konfiguration, Referenz-Zuweisungen und gebundenen Einzel-Runs durch die vollständige AI-Consent-Kette](26-agents/agents.md). Keine autonome Tool-Ausführung; Outputs DRAFT_UNCHALLENGED, nie gespeichert oder adoptiert.

## Evidence-Analyse
[Deterministische Widerspruchskandidaten (within/across records) und dokumentierte Quellenrangfolge als CALCULATED-Queries](16-evidence/analysis.md). Kandidaten, kein Urteil; Rangfolge ist keine Wahrheit; kein semantischer Abgleich, kein ML.

## Permission Leases
[Begrenzte, ablaufende, widerrufbare Vorfreygaben für MCP tools/call](17-security/permission-leases.md): Reviewer gewährt mit Zielbindung, Tool-Bindung, Pflicht-Ablauf und Nutzungslimit; Verbrauch bei Reservierung; Widerruf unter Not-Stop erlaubt; niemals Ersatz technischer Gates.

## Statusvokabular-Mapping
[Verbindliche Zuordnung der neun Konversationszustände (VERIFIED/MEASURED/CALCULATED/CONDITIONAL/ESTIMATED/EXTERNAL_SOURCE/CONTRADICTED/UNKNOWN/BLOCKED) zu realen Modellfeldern und Kennzeichnungspflichten](00-overview/status-vocabulary.md). Keine Aufwertung ohne reale Operation; ESTIMATED bleibt Textpflicht.

## Monitoring & Anbindungsverwaltung
[Lesende Plattformübersicht aus echten gespeicherten Records plus Integrations-Registry mit echten Add-/Remove-Routen](27-monitoring/monitoring.md). − ausschließlich Reviewer-bestätigte Deaktivierung mit Begründung, Daten bleiben erhalten; umgebungsgebundene Anbindungen nur einsehbar; kein Alerting, keine Wahrheitsaussagen.

## Bright Data MCP discovery + begrenztes tools/call
[Enger Vertrag: Authentifizierung, API, Datenschutz, Allowlist-Ausführung und offene Live-Abnahme](22-mcp/brightdata.md). tools/call nur für die zwei allowlisted Kandidaten mit Reviewer-Einzelfreigabe; kein allgemeiner Tool-Executor, keine Live-Provider-Validierung.
