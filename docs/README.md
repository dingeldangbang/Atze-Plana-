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
