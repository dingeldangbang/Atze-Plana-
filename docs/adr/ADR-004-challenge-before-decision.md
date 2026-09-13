# ADR-004 — Every Decision Must Survive Challenge

## Status
Accepted am 2026-09-14 für den v0.3-Entscheidungskern. Kein Ersatz für menschliche Verantwortung, keine behauptete unabhängige Webrecherche oder domänenübergreifende Wahrheitsprüfung.

## Bestand / Problem
Ausgangspunkt `1094a8b`: Triage bewertet Task-Evidence, Confidence, Preconditions, Stop und Approval. Es gibt noch keine Result Packages, Challenge-Prozesse oder unabhängige Gegenprüfung. Reviewer-Approval und direkte Memory-Fakt-/Decision-Erfassung könnten ein einzelnes Ergebnis ohne Challenge weiterreichen. Ein Stopreset ließ ältere Freigaben wieder gelten. Keine dieser bestehenden Daten wird gelöscht; die Freigaberegeln werden jedoch absichtlich verschärft.

## Decision
- Primärergebnisse werden als unveränderliche Result Packages einer Task erfasst. Ihre Herkunft ist eine Operatorangabe; ein Primary-Agentenruntime wird dadurch nicht behauptet.
- Strukturierte, auf Evidence bezogene Behauptungen/Beobachtungen bilden einen begrenzten maschinenprüfbaren Vertrag. Freitext wird nicht automatisch verstanden. Fehlende Daten bleiben UNKNOWN; kein Parsing erfundener Quellen oder Telemetrie.
- Ein separat gestarteter Challenge-Worker-Prozess hat einen eigenen Token und ausschließlich Job-Claim/-Complete-Rechte, keine Projekt-/Evidence-/Approval-Schreibrechte. Er bekommt einen versionierten Snapshot aus Task, Ergebnis und allen erfassten Projekt-Evidenzen; dadurch kann der Primary nicht nur seine ausgewählten Belege zur Gegenprüfung vorlegen.
- Fünf Prüfarten: Evidence, Consistency, Alternative, Causality und Action. Deterministische Regeln statt zweitem Prompt desselben Agenten. Gegenbefunde referenzieren tatsächliche Datensätze; fehlende Gegenquellen werden nicht erfunden.
- Der Server verifiziert den workergebundenen Snapshot/Lease und reproduziert die deterministische Reportberechnung vor Annahme. Nur der Worker kann einen Report einreichen; Operator/Reviewer können keinen PASS setzen. Keine in-process Ersatzbearbeitung bei Worker-Ausfall.
- Triage akzeptiert ausschließlich einen aktuellen abgeschlossenen Challenge-Pass zum aktuellsten Result Package/Job, passendem Evidence-/Stop-/Policyfingerprint und unveränderten Voraussetzungen. ACCEPT bezeichnet nur geprüfte strukturierte Eingaben, keine globale Wahrheit. CONDITIONAL und BLOCK gestatten keine Übernahme/Freigabe.
- Neue Ergebnisse, neue Challenges, neue/geänderte Projektevidenz und Stop-Ereignisse entwerten vorherige Freigaben. Historische Datensätze bleiben sichtbar. Approval wird an Result/Challenge/Fingerprint gebunden, nicht bloß Task-ID.
- Übernahme als autoritative Decision-Memory nur über einen reviewergebundenen, erneut geprüften Adopt-Pfad. Direkte neue fact/decision-Memory-Schreibwege werden blockiert. Manuelle Inferenzen/History bleiben ausdrücklich recorded/untrusted und keine Challenge-freigegebenen Entscheidungen.
- CRUD-Eingaben, manuelles Evidence-Review und administrative Dateipflege sind Eingabe-/Betriebsoperationen, keine automatisch akzeptierten Agentenergebnisse. Sie ersetzen niemals das neue Task-Entscheidungsgate. Kein externer Executor wird eingeführt.

## Unabhängigkeit / Grenzen
Prozess, Credentials und Prüfalgorithmus sind vom Primary getrennt. API und Worker verwenden denselben versionierten deterministischen Regelcode zur Reproduzierbarkeit; das ist keine organisatorische oder modellbasierte Quellenunabhängigkeit. Aktuell nur lokale eingereichte Evidence, keine Bright-Data-/Such-/Geräte-/LLM-Integration. Distinkte Quellenherkunft kann höchstens als deklarierte, überprüfungsbedürftige Diversität erfasst werden; ohne unabhängigen Nachweis bleiben Hochrisiko-/Kausalitätsaussagen eingeschränkt. Eigene alternative Kandidaten dürfen nur aus vorhandenen strukturierten Beobachtungen stammen.

## Alternatives
Nur eine UI-Schaltfläche ohne Gate: umgehbar. Zweiter Prompt im Primary: keine getrennten Rechte/Prozesse. Stets grüner Checklistenreport: Fake-Validierung und verboten. Automatische Online-Gegenquellen ohne Provider/Herkunftsprüfung: erfundene Integration. Diese Varianten werden verworfen.

## Konsequenzen / Migration
Additive Records für result, challenge_job, challenge_report; optional strukturierte Evidence-Felder. Bestandsdaten bleiben erhalten, aber Tasks ohne aktuellen Challenge-Pass sind BLOCKED. Frühere Approvals gelten nicht mehr automatisch. Neuer separater Worker-Token/Prozess nötig; unkonfiguriert/ausgefallen bedeutet pending/blocked, niemals Fake-Fallback. Package-/API-Version v0.3 mit dokumentierten Breaking Changes. Tests werden auf den echten Challenge-Weg umgestellt, keine Test-Bypässe.

## Validierung
Realer separater Worker über HTTP; deterministische Unit-/API-Tests, Leases/Retry, falsche Rollen, gefälschte Reports, Replay, stale Evidence/Result/Challenge, Widersprüche, Varianten/Einheiten/Bedingungen, fehlende Messung/Alternative, Korrelation, Stop/Reset, Approval-/Adopt-Umgehung und Audit-Transaktionen. Dokumentation und OpenAPI parallel; Browser-/Hardware-/Webprovider-Nachweise bleiben separate Gates.
