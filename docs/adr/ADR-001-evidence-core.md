# ADR-001 — begrenzter evidence-first Single-Workspace-Kern

## Status
Accepted für v0.1 am 2026-09-13; nicht für die vollständige Zielplattform.

## Context / Problem
Leeres Repository und eine sehr große Zielplattform. Hardware, SDKs und Providerzugänge fehlen. Behauptete Vollständigkeit wäre unbelegbar; mehrere persistente Dienste wären für ein 2-GB-Ziel unnötig.

## Decision
FastAPI/Pydantic, ein Prozess, lokales SQLite mit generischen typisierten JSON-Datensätzen. Evidenz und deterministische Triage vor jeder gespeicherten Freigabe, Operator/Reviewer getrennt. Keine externen Aktionen, kein Agent/Worker. Clientseitige statische Oberfläche. Originaltext/Hash und manuelles Review statt fingierter Quellenvalidierung.

## Alternatives
Postgres/Redis/Queue/Microservices: spätere Skalierung, aktuell unnötiger Betriebsaufwand. Nur Dokumentation: nicht lauffähig. Universalexecutor: unkontrollierbares Risiko ohne Isolation. Vollständiges relationales Schema: bessere DB-Constraints, mehr frühe Migrationen; hier API-Referenzvalidierung mit dokumentierter Grenze.

## Consequences
Reproduzierbarer kleiner Kern, geringe Dienstdichte, nachvollziehbare Tests. Begrenzter Durchsatz, keine Tenants/Benutzeridentitäten, schwächerer Schutz bei direktem DB-Zugriff. Vor Execution zwingend zielgebundene widerrufbare/ablaufende Approvals, stärkere Identität, Isolation und neue ADRs. 2-GB-Betrieb bleibt ungeprüfte Planung.
