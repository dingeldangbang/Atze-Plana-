# Trend-Engine — deterministische Analyse eingereichter Messreihen

Stand 2026-09-14, Baseline 183 ausgeführte Tests PASS vor diesem Inkrement; dieses Inkrement ergänzt 17 Tests (200 PASS). Trends sind **CALCULATED** aus tatsächlich ingesteten (`SUBMITTED_DEVICE_SAMPLES`), unveränderlichen und hash-verifizierten Telemetrie-Batches — niemals MEASURED, niemals vorhergesagt, niemals als physikalische Wahrheit dargestellt.

## Zweck / explizite Non-Goals
Deterministische statistische Prüfarten (Query im Sinne der Command/Query-Trennung der [PLAN-UI-Spezifikation](../21-plan/plan-ui-interaction-spec.md), Abschnitt 46) über die Messreihen genau eines Sensors, optional eingegrenzt auf eine deklarierte Session. **Kein ML, keine Anomalie-Erkennung jenseits der fünf dokumentierten Checks, keine Prognose/Zukunftsvorhersage (`prediction: NONE`), keine automatischen Aktionen/Alerts, kein Schreibzugriff, kein Audit (deterministisch aus unveränderlichen Batches reproduzierbar), keine Beförderung von Inferenz zu MEASURED.** `VERIFIED TREND` bedeutet ausschließlich: die dokumentierten statistischen Kriterien sind über die eingereichten Samples erfüllt — kein Wahrheits-, Kalibrierungs- oder Gerätegesundheitsbeweis.

## API-Vertrag
| Route | Rolle | Wirkung | Fehler |
|---|---|---|---|
| POST /api/telemetry/trends | both | Deterministischer Analyse-Report (Query, keine Mutation, bei jedem Aufruf neu berechnet) | 404 Sensor, 401 Token, 422 Batch-/Sample-Limit, 503 Blob-Korruption |
| GET /api/telemetry/trends/checks | both | Statischer Katalog der implementierten Prüfarten mit exakten Kriterien und Limits | 401 Token |

Der Report enthält `batch_ids` (gelesene Basis), Zeitfenster, je Prüfart Status/Statistik/Schwellwert/erfüllte-nicht-Kriterien, `verified_types`, `summary_status` sowie die Provenance-Felder `basis=SUBMITTED_DEVICE_SAMPLES`, `result_class=CALCULATED`, `prediction=NONE`. Not-Stop blockt die Analyse nicht (reine Leseoperation); deaktivierte Sensoren bleiben analysierbar (Historie bleibt).

## Prüfarten und Kriterien (alle konstant, im Katalog-Endpoint sichtbar)
| Typ | Statistik | VERIFIED TREND wenn |
|---|---|---|
| drift | Kleinste-Quadrate-Steigung pro Stunde | ≥20 Samples, Fenster ≥600 s, |Gesamtänderung| ≥5 % der Referenzspanne (declared_range, sonst beobachtete Spanne) und ≥2× Residual-Standardabweichung |
| level_shift | Mittelwert(letztes Drittel) − Mittelwert(erstes Drittel) | ≥8 Samples je Drittel, |Shift| ≥5 % der Referenzspanne und ≥2 Standardfehler |
| variance_change | std(letztes Drittel) / std(erstes Drittel) | ≥8 Samples je Drittel, Ratio ≥2 oder ≤0,5 |
| out_of_range_rate | Anteil außerhalb declared_range | declared_range vorhanden (Operator-Aussage, keine Kalibrierung), ≥20 Samples, Rate ≥10 % |
| suspect_rate | Anteil device-deklarierter `quality: suspect` Samples | ≥20 Samples, Rate ≥10 % |

Nicht erfüllte Kriterien werden je Check explizit als `failed_criteria` zurückgegeben (kein verschlucktes NEIN). Referenzspanne ohne declared_range ist die beobachtete Wertespanne; ist sie 0 (konstante Reihe), bleibt der Check INSUFFICIENT EVIDENCE.

## Grenzen / Fehler / Nicht validiert
Arbeitsgrenzen je Query: max. 200 Batches und 200.000 Samples pro Device/Sensor (überschritten → 422 mit Hinweis, keine unbegrenzte Berechnung). Blob-Korruption → 503 fail-closed (Hash-Verifikation über `storage.checked`), kein Teilresultat. Sessions sind Freitext-Labels des Devices; Zeitstempel sind deklarierte Geräteangaben ohne Plausibilitätskorrektur. **Nicht validiert (NOT RUN):** Analyse echter Sensordaten — alle Testreihen sind synthetische Fixtures; keine Validierung an realer Hardware; keine Verteilungsannahmen (nichtparametrische Schwellen, konservativ); keine Lifecycle-/Proaktivitäts-Engine ([Roadmap](../00-overview/roadmap.md), Bereich 15 Trends bleibt für diese Teile NOT IMPLEMENTED). Der Endpoint liest ausschließlich Bestände des Telemetrie-Moduls ([Vertrag](../23-telemetry/telemetry.md)) und erzeugt keine neuen Records.
