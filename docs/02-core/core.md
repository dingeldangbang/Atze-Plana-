# Implementierte Kernverträge

Gemeinsame Dependencies: Python, FastAPI/Pydantic, lokales SQLite. Konfiguration ausschließlich [sieben Umgebungsvariablen](../19-operations/configuration.md). Inputs/Outputs mit exakten Constraints und HTTP-Fehlern: [API](../08-network/APIs.md), [OpenAPI](../../openapi.yaml). Beispiele: [Quickstart](../../QUICKSTART.md), [API-Smoke](../../scripts/smoke.py).

## Projekte
**Purpose:** Arbeit in benannte Kontexte gliedern. **Inputs:** Name/Beschreibung. **Outputs:** ID/UTC-Metadaten. **Permissions:** Operator write, beide read. **Failure Modes:** 401/403/422/503. **Validation/Tests:** API-002, AUD-001. **Security:** Projekt ist keine Tenant-Grenze. **Known Limitations:** kein Update/Delete oder Planeditor; Archive und Kontextsuche sind separate v0.2-Module.

## Tasks
**Purpose:** unveränderliche Aktionsabsicht mit Evidenzbindung. **Inputs:** Projekt, Titel, Action, eindeutige Evidence-IDs, preconditions_met. **Outputs:** Task-ID, Erstellerrolle/-zeit. **Permissions:** Operator create, beide read/triage. **Failure Modes:** 404 fehlende Referenz, 422 fremde/duplizierte Evidenz, 503 Storage. **Validation/Tests:** API-002, TRI-001/002. **Security:** keine frei ausführbaren Commands; Preconditions sind Selbstauskunft. **Known Limitations:** keine Plan-/Task-Ausführung, Scheduler, Mutationen oder Retries.

## Approval
**Purpose:** menschliche Entscheidung getrennt von Erfassung. **Inputs:** Task-ID und Pflichtgrund. **Outputs:** Approval-ID/Reviewer/Zeit. **Permissions:** nur Reviewer. **Failure Modes:** 409 bei blocked, eligible oder bereits approved. **Validation/Tests:** TRI-001, SEC-003. **Security:** Triage in derselben SQLite-Transaktion erneut geprüft, Aufgaben unveränderlich. **Known Limitations:** keine individuellen Identitäten, allgemeine Expiry, Ziel-/Betragsbindung oder tatsächliche Ausführung; ab v0.3 jedoch Result-/Challenge-/Fingerprintbindung und Invalidierung bei Kontextwechsel. Kein ausreichend starker Vertrag für zukünftige Finanz-/Flashaktionen.

## Audit
**Purpose:** erfolgreiche Mutationen und Triage nachvollziehen. **Inputs:** vom Server erzeugte Rolle/Event/Entity/Details. **Outputs:** paginierte Einträge für Reviewer. **Permissions:** keine direkte Schreib-/Lösch-API. **Failure Modes:** SQL-Ausfall rollt Domainmutation zurück. **Validation/Tests:** AUD-001 prüft tatsächlichen Rollback durch absichtlich fehlschlagenden Audit-Trigger. **Security:** keine Secrets im Audit; Inhalte können sensible Gründe enthalten. **Known Limitations:** keine Hashkette, externe Senke, Auth-Fehlerlogs oder Retention.

## Emergency stop
**Purpose:** neue Freigaben und alle Triage-Ergebnisse blockieren. **Inputs:** active + Grund, Reviewer. **Outputs:** persistenter Zustand. **Failure Modes:** 403/422/503. **Validation/Tests:** SEC-003 inklusive Restart und vorhandener Freigabe. **Security:** global, nicht nur UI-Zustand. **Known Limitations:** kein Interrupt externer Prozesse, kein Hardware-Not-Aus; ab v0.3 entwertet jedes Stopereignis die Challenge-/Approvalbindung; Reset stellt keine alte Freigabe wieder her.

Orchestrator, Context Engine, autonome Action Engine und Agent Runtime sind NOT IMPLEMENTED. Die reine Policyfunktion ist die einzige Decision Engine.

## v0.3 — verbindliche Entscheidungserweiterung
Die obigen Kern-Inputs/Records bleiben bestehen. Vor jeder freigabefähigen Taskentscheidung ist nun ein aktueller Challenge-Pass zum neuesten Result Package zwingend. Approval enthält zusätzlich result_id/challenge_id/fingerprint. Alte Approvals ohne diese Bindung sind historisch, nicht gültig. Direktes neues fact/decision-Memory ist gesperrt; Ergebnisadoption wird erneut transaktionell durch Triage geprüft. [Vollständiger Vertrag](challenge-worker.md), [Triage-Regeln](triage.md).

## Privacy-first Modellgrenze (experimenteller Teilschritt)
[Model Gateway](model-gateway.md) ergänzt explizite lokale/Remote-Policy, manuelles Modellregister, ausgewählten Kontext und Reviewer-Freigabe vor echtem Text-HTTP-Transport. Default: Local-only, External DENY, keine Provider. Kein installiertes HF-Modell, keine smolagents-/MCP-/Sandboxintegration und kein universeller OS-Egress-Lock. Diese vollständigen Integrations-/Release-Gates bleiben BLOCKED. Vorhandene Challenge/Triage bleibt unverändert zwingend.
