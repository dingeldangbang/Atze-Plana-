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
