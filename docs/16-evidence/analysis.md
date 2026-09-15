# Evidence-Analyse — Widerspruchskandidaten und Quellenrangfolge (CALCULATED, nie Wahrheit)

Stand 2026-09-15, Baseline 258 ausgeführte Tests PASS vor diesem Inkrement; dieses Inkrement ergänzt 5 Tests (263 PASS). Beide Endpunkte sind **deterministische Queries über gespeicherte Evidence-Records** — Ausgaben sind CALCULATED mit expliziter Methode und Grenze, niemals MEASURED, nie ein Wahrheitsspruch, nie automatisch adoptiert.

## Widerspruchskandidaten
`POST /api/analysis/contradictions` `{project_id}` (beide Rollen, Query ohne Nebenwirkungen/Audit): gruppiert alle deklarierten Observationen des Projekts nach `(subject, attribute)` (Whitespace-stripped, exakter Match); Wertgleichheit = numerisch, wenn beide als Float parsbar, sonst Stringgleichheit **plus** gleiche Einheit. Differierende Werte → `contradiction_candidates` mit allen beteiligten Werten, Evidence-Ids, Review-Zuständen, Zeitpunkten und `scope` (`within_record`/`across_records`); identische Mehrfachnennungen → `corroborated_subject_attributes`. **Kandidaten, kein Urteil:** die Auflösung eines Widerspruchs bleibt menschliche Entscheidung (Review/Challenge); CONTRADICTED im [Statusvokabular](../00-overview/status-vocabulary.md) bedeutet hier stets Kandidat.

## Quellenrangfolge
`GET /api/analysis/source-ranking?project_id=` (beide Rollen): dokumentierte, feste Regelordnung — 1. Review-Zustand (verified > unverified > rejected), 2. deklarierte Confidence (höher zuerst), 3. Beobachtungszeit (neuer zuerst) — mit `rule_trace` je Eintrag. Die Rangfolge ist eine **dokumentiert deterministische Ordnung über deklarierten Feldern**, keine Wahrheits- oder Quellengüte-Aussage; Confidence/Provider sind Owner-Angaben; EXTERNAL_SOURCE-Disziplin bleibt.

## Grenzen / Nicht implementiert
Kein Abgleich mit externen Quellen, keine semantische Ähnlichkeit (nur exakte Gruppierung), keine automatische Konfliktauflösung, keine Zeitfenster-/Gearbeitet-mit-Logik, kein ML. Fehlende subject/attribute-Felder werden nicht gruppiert. Beide Ausgaben entstehen bei jedem Aufruf neu aus unveränderlichen Records (kein Cache, kein Zustand). Roadmap 16 Evidence → PARTIAL erweitert ([Modulmatrix](../00-overview/roadmap.md)).
