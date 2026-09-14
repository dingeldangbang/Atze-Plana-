# Überblick, Vision, Ziele und Begriffe

## Produktstand
Ein einzelner Workspace für nachvollziehbare Projekte und Aufgaben. Operatoren erfassen Quellen und Claims; Reviewer prüfen deren Verwendung; Triage klassifiziert mögliche Aktionen. Keine Geräteanbindung oder autonome Orchestrierung. v0.2 ergänzt [Archive, Cache, Memory und lokale Quellen-Suche](../20-context-storage/architecture.md); Mobile Server/MCP/Remote-Sync sind die neue Zielarchitektur, noch keine vollständige Runtime.

## Vision / Ziele
Langfristig eine evidence-first Plattform für Software-, Geräte- und Netzwerkprojekte. Kurzfristig ein reproduzierbarer Kern ohne fiktive Integrationen, mit überprüfbaren Sicherheitsgrenzen und automatischer Dokumentationskonsistenz. Die langfristige Vision ist keine implementierte Fähigkeit.

## Begriffe
- **Evidence:** erfasster Claim mit Originaltext, Quellenmetadaten, SHA-256 und menschlichem Reviewzustand.
- **Confidence:** vom Operator gemeldeter Wert; nicht statistisch kalibriert oder automatisch bewiesen.
- **Triage:** deterministische Bewertung von Voraussetzungen, Evidenz, Risiko, Stop und Approval.
- **Approval:** begründete Reviewer-Freigabe einer unveränderlichen Aufgabe; keine Execution.
- **Audit:** persistente Ereignisdatensätze; keine manipulationssichere externe Logsenke.
- **Workspace:** gesamter Datenbestand einer Instanz; Projekt ist keine Sicherheitsgrenze.

Umfang und Prioritäten: [Roadmap](roadmap.md).
