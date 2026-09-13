# Verbindliche Arbeitsregeln für Repository-Agenten

Vor jeder Änderung [REALITY_POLICY.md](REALITY_POLICY.md) lesen und einhalten. Keine Fake-/Demo-/Mock-Implementierung im Produktpfad, kein stiller Providerfallback, keine erfundenen Test-/Build-/GitHub-/Hardwareerfolge. Vorhandene Funktionen zuerst analysieren.

Tests mit synthetischen Inputs/Fehler-Injektion nur außerhalb des Betriebswegs, explizit gekennzeichnet und in temporären Testinstanzen. Niemals die Produktvorschau mit Fixtures befüllen. `ATZE_MODE=test` nutzt echte lokale Komponenten, keine Mocks.

Code, Tests, OpenAPI, Konfiguration und Dokumentation im selben Änderungsschnitt pflegen. `python scripts/docs.py --check`, `python scripts/reality_check.py`, pytest, echter Build und isolierter Smoke müssen tatsächlich laufen. Integrationen getrennt nach Implemented/Configured/Tested/Validated/Production Ready bewerten. Fehlende Adapter BLOCKED, fehlende Konfiguration NOT CONFIGURED; keine Statusseite als Integration ausgeben.

Keine Secrets/Runtime-Daten committen. Kein Merge, Release oder Produktionsdeploy ohne erforderliche Freigabe. Weitere Regeln in CONTRIBUTING.md, DEVELOPMENT.md und SECURITY.md.
