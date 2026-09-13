# Triage / Decision Engine

## Purpose, Inputs, Outputs
`app/triage.py:evaluate` erhält Task, zugehörige Evidence, aktuellen Stop und optional Approval-ID. Ergebnis: task_id, state, risk, reasons, evidence_ids, niedrigste gemeldete confidence, approval_id, executed=false. Keine Tools, keine Netzwerkanfragen und keine LLM-Entscheidung.

## Entscheidungsregeln (in Reihenfolge)
1. Globaler Stop → Blocking reason.
2. preconditions_met=false → Blocking reason.
3. Keine Evidenz → Blocking reason.
4. Mindestens eine Evidenz nicht verified → Blocking reason.
5. Minimum der gemeldeten Confidence <0.8 → Blocking reason.
6. Bei irgendeinem Blocking reason: blocked, auch wenn ein Approval existiert.
7. Sonst READ → eligible; alle anderen Aktionen ohne Approval → approval_required, mit Approval → approved.

Risk: READ low, WRITE medium, alle anderen high. Das ist eine feste grobe Kategorie, keine kontextbezogene Schadensprognose. Policythreshold 0.8 ist im Code festgelegt, nicht konfigurierbar. Abgelehnte/unverified Evidence darf nicht automatisch verwendet werden.

## Nachvollziehbarkeit
Was: Task-ID und unveränderliche Aufgabe. Warum: reasons. Evidenz: IDs → Originaltext/Hash/Review. Voraussetzungen: operator-attestiertes Flag. Risiken: action-basierte Kategorie. Aktion: Enum der Aufgabe. Freigabe: approval_id mit Reviewer-Grund. Ergebnis: state und executed=false. Jede POST-Triage speichert einen Snapshot im Audit. Es gibt keine automatische Benachrichtigung/Eskalationsqueue; der API-Client muss blocked oder approval_required an Menschen weitergeben.

## Dependencies / Configuration / Permissions
Reine Pythonfunktion; API lädt Daten transaktionell aus SQLite. Beide Rollen dürfen Triage starten; nur Reviewer kann approve. Keine direkten Endpunkte zur freien Manipulation eines Decision-Objekts.

## Failure Modes / Validation / Tests / Security
Fehlende Task-ID → 404, unzulässige Eingabe → 422, Storage → 503. TRI-001 testet jede Action, TRI-002 die zentralen Blocks, TRI-003 leere/abgelehnte Evidenz und Grenzwert, SEC-003 den persistenten Stop. Approval endpoint berechnet erneut, um getrennte Precheck/Write-Rennen zu verhindern.

## Examples / Known Limitations
[API-Smoke](../../scripts/smoke.py) zeigt einen synthetischen READ- und WRITE-Ablauf. Keine automatische Faktenprüfung, Evidenzalterung, Widerspruchsanalyse, Device Preconditions, Approval-Expiry/Revocation oder Ausführung. Ein eligible READ ist nicht ausgeführt. Das Flag `preconditions_met` ist kein technischer Gerätecheck.
