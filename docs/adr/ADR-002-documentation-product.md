# ADR-002 — Dokumentation als geprüftes Produktmodul

## Status
Accepted am 2026-09-13.

## Context / Problem
Die Zielanforderung verlangt automatische Dokumentation und technische Nachweise. Handgepflegte doppelte API-/Test-/Config-Listen driften; LLM-Text kann nicht implementierte Fähigkeiten erfinden.

## Decision
Deterministischer lokaler Documentation Worker introspektiert OpenAPI/Pydantic, Python-AST-Testbeschreibungen, Konfigurationsreferenzen und optional Git-Historie. Outputs versionieren, in CI bytegenau vergleichen und OpenAPI formal validieren. Handbücher, Grenzen, ADRs und tatsächliche Validationreports bleiben reviewed Texte. Fehlende Module zentral kennzeichnen statt über 100 leere Feature-Seiten erzeugen.

## Alternatives
Nur manuelle Dokumentation: driftanfällig. Vollautonomer LLM-Worker: zusätzliche Credentials/Prompt-Injection-Risiken und keine Wahrheitsgarantie. Statisches Docs-Hosting: später möglich, aber kein Ersatz für Konsistenzprüfung.

## Consequences
Schema/API/Test-Katalog automatisch synchron, Quellenbezug prüfbar. Linkprüfung deckt lokale Dateien ab, noch keine externen Ziele oder Markdown-Anker. Semantische Commandprüfung nur für tatsächlich ausgeführte Quickstart-/Smoke-/CI-Pfade, nicht für jedes Codebeispiel. Worker generiert keine erfundenen Test-, Repair- oder Deploymentreports.
