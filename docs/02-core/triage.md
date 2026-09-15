# Triage / Decision Engine — v0.3

**Kein relevantes Primärergebnis wird ohne Challenge übernommen.** [Vollständiger Challenge-Vertrag](challenge-worker.md).

## Inputs / Outputs / Dependencies
Task, verknüpfte echte Evidence-Records, aktueller Stop, neuestes Result Package, neuester abgeschlossener Challenge-Report, aktueller Fingerprint und daran gebundene Approval. Pythonregeln, FastAPI/SQLite und separater HTTP-Worker. Response: bisherige Task-state/risk/reasons/evidence_ids/confidence/approval_id plus validation_status, result_id, challenge_id, fingerprint, challenge_reasons. executed bleibt false.

## Pflichtregeln
1. Stop aktiv, Preconditions nicht bestätigt, keine Evidence, nicht vollständig verified oder minimale gemeldete Confidence <0.8 blockieren weiterhin.
2. Kein Result / kein abgeschlossener aktueller Challenge-Report / stale Daten oder Policy → BLOCK.
3. Challenge CONDITIONAL → keine Freigabe; Task-state blocked. Challenge BLOCK → BLOCK.
4. Nur Challenge PASS mit bestandenem Basistriage-Gate → ACCEPT für submitted_structured_claims_only.
5. Danach READ eligible, WRITE approval_required bzw. approved mit aktuellem Reviewer-Approval. Hochrisikoaktionen bleiben durch den Challenge Worker eingeschränkt; kind=action hat keinen Executor und ist BLOCKED.
6. Adoption nur ausdrücklich durch Reviewer mit erneut geprüfter aktueller Triage; Primärfreitext nicht automatisch übernommen.

Neue Evidence, neues Result, erneute Challenge und Stopereignisse entwerten alte Approval-Bindungen. Ein Stopreset stellt keine alte Freigabe wieder her. Frühere v0.2-Approvals ohne Challengebindung sind historische Datensätze, keine gültigen Freigaben.

## Nachvollziehbarkeit / Permissions
Was: unveränderliche Task + Result. Warum: Triagegründe und fünf Challenge-Prüfarten. Quellen: Evidence-IDs, Originaltext/SHA, strukturierte Beobachtungen. Voraussetzungen: Operator-Attestierung plus Gegenprüfung. Risiken: read low, write medium, übrige high; keine kontextsensitive Schadensprognose. Freigabe: Result/Report/Fingerprint-gebundenes Reviewer-Approval. Ergebnis: ACCEPT/CONDITIONAL/BLOCK und executed=false. Snapshot in Audit bei POST triage.

## Failure Modes / Tests / Security
401/403 Rollen, 404 fehlende Entität, 409 Zustandskonflikt/abgelehnte Adoption, 422 ungültige Inputs/gefälschter Workerreport, 503 Storage-/Worker-Konfiguration. CH-001..017 und TRI-/SEC-Regressionen prüfen tatsächliche Fail-closed-Gates. Kein API-Schalter zum Überspringen von Challenge, kein Mock bei Worker-Ausfall. Kein Source-/LLM-/Device-Executor.

## Configuration / Examples / Limits
[Sieben Konfigurationsvariablen](../19-operations/configuration.md), [isolierter echter HTTP-Smoke](../../scripts/smoke.py). Preconditions/Confidence bleiben deklarierte Angaben; Challenge ist begrenzte strukturierte Datenprüfung, kein globaler Wahrheits-/Semantik-/Kausalitätsnachweis. Details zu Unabhängigkeit, Scope-Limits und Lease-Recovery im Challenge-Vertrag.
