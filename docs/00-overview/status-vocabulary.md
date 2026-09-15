# Statusvokabular-Mapping — Konversationsstatus ↔ tatsächliche Modellfelder

Stand 2026-09-15. Das Repository setzt die neun Konversationszustände als **Disziplin und Kennzeichnung** um, nicht als einzelnes durchgängiges Datenbankfeld (Delta D2 aus [MASTER_ABGLEICH](../../MASTER_ABGLEICH.md)). Dieses Dokument mappt verbindlich, welcher Konversationsstatus durch welches reale Modellfeld abgebildet wird — und wo nur eine Textkennzeichnungspflicht besteht. Keine Aussage ohne Nachweis: ein Feld zu setzen ist nie ein Wahrheitsbeweis.

| Konversationsstatus | Reale Abbildung (Modell/Feld) | Bedeutung und Grenze |
|---|---|---|
| VERIFIED | `evidence.review_state='verified'` (Reviewer-Review); `result` nach Challenge-PASS und Adoption | Bestätigt den **Prozess/Review**, nie die physikalische Wahrheit einer Aussage |
| MEASURED | `telemetry_batch`/`telemetry`-Samples (device-submitted, hash-verifiziert gespeichert) | Vom **Gerät eingereichte** Werte; physikalische Messgenauigkeit/Kalibrierung nie verifiziert |
| CALCULATED | `trend`-Reports (`result_class='CALCULATED'`, `prediction='NONE'`); Monitoring-Summen (`/api/monitoring/overview`); Widerspruchs-/Rangfolge-Ausgaben | Deterministisch aus gespeicherten Records abgeleitet; Eingaben und Einheiten müssen erkennbar bleiben |
| CONDITIONAL | Triage-Entscheidung `CONDITIONAL` (`app/triage.py`, `decision.state`) | Gebundene Zwischenentscheidung mit dokumentierten Gründen; keine Teilausführung |
| ESTIMATED | **Kein strukturiertes Feld.** Kennzeichnungspflicht in Textfeldern (`summary`, `description`, `note`) | Schätzungen müssen im Text als ESTIMATED benannt werden; fehlt die Kennzeichnung, gilt der Zustand als UNKNOWN |
| EXTERNAL_SOURCE | Web-Evidenz (`source_type`/`provider`), MCP-Ergebnisse (Rohresultat nie vollständig gespeichert, nur Metadaten/Exzerpte) | Herkunft extern, unverifiziert; niemals automatisch zu VERIFIED aufwerten |
| CONTRADICTED | Widerspruchskandidaten der Evidenz-Analyse; Challenge-`BLOCK` | Deterministisch gefundene **Kandidaten**; Auflösung bleibt menschliche Entscheidung |
| UNKNOWN | Default für unreviewte Evidenz; `NOT RUN` für Hardware/Messungen | Ehrlicher Ausgangszustand; wird nie automatisch überschrieben |
| BLOCKED | Triage `BLOCK`; Gate-Denials (409 mit `state:'BLOCKED'`); Not-Stop | Aktive Verweigerung mit Grund; kein stiller Ausweichpfad |

## Abbildungsregeln
1. Jeder Statuswechsel entsteht aus einer **realen Operation** (Review, Ingest, Query, Gate) mit Audit-Eintrag — nie aus Textersetzung.
2. `ACCEPT/CONDITIONAL/BLOCK` (Triage) und `PASS/CONDITIONAL/BLOCK` (Challenge) sind die strukturierten Kernentscheidungen; die übrigen Konversationsstatus werden über die Felder oben abgebildet.
3. Fehlt ein strukturiertes Feld (z. B. ESTIMATED), ist die Kennzeichnung **Textpflicht** in der betroffenen Ressource; Prüfer dürfen fehlende Kennzeichnung als UNKNOWN behandeln.
4. Das Mapping ist Teil der Realitätsdisziplin ([REALITY_POLICY](../../REALITY_POLICY.md)): keine Aufwertung, kein Fallback auf Beispieldaten.

Teil der laufenden Inkremente: CONTRADICTED erhält mit der Evidenz-Analyse (Widerspruchserkennung) eine strukturierte Ausgabestelle; ESTIMATED bleibt bewusst Textpflicht, bis ein Eigentümer ein strukturiertes Feld fordert.
