# Agent Builder v1 — deklarative Agenten-Registry mit begrenzten Einzel-Runs durch die vollständige Consent-Kette

Stand 2026-09-15, Baseline 224 ausgeführte Tests PASS vor diesem Inkrement; dieses Inkrement ergänzt 12 Tests (236 PASS). Agenten sind **deklarierte Arbeitskonfigurationen** — keine autonomen Laufzeiten, keine Tool-Autorität, keine verschleierten Ausführungen.

## Zweck / explizite Non-Goals
Versionierte Registry (Operator deklariert), Referenz-Zuweisungen auf Tasks/Projekte und gebundene Einzel-Runs, die **dieselbe harte Kette wie normale Modellrequests** durchlaufen: `prepare()` (registriertes Modell, Zweck ⊆ Fähigkeiten, Klassifizierung, Secret-Scan, Kontextgrenzen, PLAN-Bindung) → **Reviewer-Einzelconsent** → `execute()` (exakter Kontext-Hash, Policy-/Config-Aktualität, Allowlists, Privacy/Remote, Not-Stop, PLAN-Bindung, begrenzter authentifizierter Transport). **Keine autonome Tool-Ausführung (NOT IMPLEMENTED):** `allowed_tools` ist ein deklarierter Rahmen — jeder Tool-Aufruf bleibt der separate reviewerbestätigte MCP-Pfad ([Vertrag](../22-mcp/brightdata.md)). Keine Pause/Resume-/Scheduler-/Multi-Step-Orchestrierung, kein Memory-RAG-Autonomiebegriff, keine Adoption von Ausgaben (Output bleibt DRAFT_UNCHALLENGED und wird nie gespeichert), kein Agent-zu-Agent-Verkehr.

## API-Vertrag
| Route | Rolle | Wirkung | Fehler |
|---|---|---|---|
| POST /api/agents | operator | Agent deklarieren (v1) + Audit; registriertes Modell + Zweck ⊆ Capabilities + Tools ⊆ MCP-Allowlist erforderlich | 404 Modell, 409 Name, 422, 409 Stop |
| GET /api/agents, /{id}, /{id}/versions | both | Registry/Konfigurationshistorie | 404 |
| POST /api/agents/{id}/configure | operator | Neue unveränderliche Konfigurationsversion (Predecessor-Kette); identische Konfiguration 409 | 409, 422 |
| POST /api/agents/{id}/assignments | operator | Referenz-Zuweisung auf existierenden Task/Projekt (keine Autonomie) | 404 Ziel, 409 doppelt/deaktiviert/Stop |
| GET /{id}/assignments, POST /{id}/unlink | both / operator | Zuweisungshistorie inkl. unlinked; Unlink append-only | 404, 409 |
| POST /api/agents/{id}/runs | operator | Run **vorbereiten** (kein Netz): Agent-Instruktion + Nutzeranfrage als ein begrenzter Kontext durch alle prepare-Gates; erfordert aktive Task-/Projekt-Zuweisung | 404, 409 nicht zugewiesen/deaktiviert, 409 BLOCKED bei Gate-Deny (durable Audit, kein Run-Record) |
| GET /api/agents/{id}/runs | both | Unveränderliche Run-Historie mit Attempt-Zuständen; Outputs werden nie gespeichert | 404 |
| POST /api/agents/{id}/runs/{run_id}/consent | reviewer | **Einmalige Ausführungsfreigabe** durch die vollständige execute-Kette; Ergebnis DRAFT_UNCHALLENGED, Output nur im Response, nie gespeichert/adoptiert | 403, 404, 409 nicht ausstehend |
| POST /api/agents/{id}/deactivate | reviewer | Bestätigte familienweite Deaktivierung (confirm+reason); Bestände bleiben lesbar | 403, 409 erneut/Stop, 422 |

## Ausführungs-/Sicherheitsmodell
Ein Run ist ein `ai_request` mit gebundener Herkunft: Kontext = `AGENT INSTRUCTION:\n{Instruktion}\n\nUSER REQUEST:\n{Anfrage}` (bleibt ≤8000 Zeichen, Klassifizierung standardmäßig CONFIDENTIAL, konservativ). Run-Record referenziert `request_id`, `context_hash`, `agent_version`; Consent verlangt den exakten Hash (`AIConsent`), einmalig — Replay → 409 (REQUEST_NOT_PENDING auf dem zugrundeliegenden Request). Outcomes: `DRAFT_UNCHALLENGED` (Ausgabe erhalten, ungeprüft, nur Hash im Attempt), `BLOCKED` (Gate/Policy/Stop, mit Grund), `UNAVAILABLE` (Transportfehler, kein Fallback). Default-Deny-Policy blockt jeden Transport, bevor ein Socket geöffnet wird. Not-Stop blockt Registry-Mutationen und Consent; Run-Vorbereitung bleibt lokal erlaubt (kein Netz), Ausführung bleibt gesperrt. Audit-Kette: `agent.created/versioned/assigned/unlinked/run_denied/run_prepared/run_outcome/deactivated`.

## Grenzen / Nicht validiert
Agenten deklarieren Metadaten (Beschreibung, Instruktion, Tools) — Owner-Aussagen ohne Verifikation. Keine Live-Modellinferenz validiert: Der echte Transportnachweis in den Tests ist ein isolierter Loopback-Empfänger (Testinfrastruktur, kein Modell — wie im [Model-Gateway-Vertrag](../02-core/model-gateway.md)). Kein Sandbox-/Ressourcen-/Token-Budget je Agent (globale Policy-Grenzen gelten). Kein Workflow-/Multi-Step-/Agentenorchestrator; Agent Builder v1 ist die Registry- und Einzel-Run-Grundlage gemäß [PLAN-UI-Spezifikation](../21-plan/plan-ui-interaction-spec.md) Abschnitt 28, UI folgt mit Modul 6. Roadmap 04 Agents → PARTIAL ([Modulmatrix](../00-overview/roadmap.md)).
