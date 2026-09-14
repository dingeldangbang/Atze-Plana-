# Verbindliche Arbeitsregeln für Repository-Agenten

Vor jeder Änderung [REALITY_POLICY.md](REALITY_POLICY.md) lesen und einhalten. Keine Fake-/Demo-/Mock-Implementierung im Produktpfad, kein stiller Providerfallback, keine erfundenen Test-/Build-/GitHub-/Hardwareerfolge. Vorhandene Funktionen zuerst analysieren.

Tests mit synthetischen Inputs/Fehler-Injektion nur außerhalb des Betriebswegs, explizit gekennzeichnet und in temporären Testinstanzen. Niemals die Produktvorschau mit Fixtures befüllen. `ATZE_MODE=test` nutzt echte lokale Komponenten, keine Mocks.

Code, Tests, OpenAPI, Konfiguration und Dokumentation im selben Änderungsschnitt pflegen. `python scripts/docs.py --check`, `python scripts/reality_check.py`, pytest, echter Build und isolierter Smoke müssen tatsächlich laufen. Integrationen getrennt nach Implemented/Configured/Tested/Validated/Production Ready bewerten. Fehlende Adapter BLOCKED, fehlende Konfiguration NOT CONFIGURED; keine Statusseite als Integration ausgeben.

Keine Secrets/Runtime-Daten committen. Kein Merge, Release oder Produktionsdeploy ohne erforderliche Freigabe. Weitere Regeln in CONTRIBUTING.md, DEVELOPMENT.md und SECURITY.md.

## Verbindliche Challenge-Regel v0.3
Every Decision Must Survive Challenge. Kein Primärergebnis direkt in Approval/autoritative Memory übernehmen. Aktuelles Result Package → separater Challenge-Prozess → verifizierter Report → Triage → erforderliche Human Approval → explizite Adoption. Keine Test-/UI-/Configoption zum Überspringen. CONDITIONAL/BLOCK stoppt. Bei Staleness neu prüfen, alte Freigaben nicht wiederverwenden. Primärfreitext nicht durch einen begrenzten strukturierten PASS als wahr ausgeben. [Vertrag](docs/02-core/challenge-worker.md).

## Privacy-first AI boundary
Keine Appdaten unverschlüsselt an Dritte. Neue Model-Egresspfade ausschließlich über ExternalDataGateway und die gebundene Policy-/Reviewer-Prüfung. Standard local-only/external-deny, keine stillen Fallbacks/Redirects, keine Credentials im Kontext, kein Modell-Toolrecht. TLS schützt Transport, nicht Providerverarbeitung. Diese Python-Kontrolle ist KEIN universeller OS-/Netzwerkbeweis; Challenge-Control-Transport ist noch separat, MCP/Agent-Tools fehlen. Host-/Ingress-/Klassifizierungs-/verschlüsselter-Cache-/MCP-/Sandboxgates bleiben release-blockierend. [Begrenzter tatsächlicher Vertrag](docs/02-core/model-gateway.md).
