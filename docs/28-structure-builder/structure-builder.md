# Struktur-Builder (AXM v0.1) — versionierte visuelle Modelle, CALCULATED-Generierung ohne Nebenwirkungen

Stand 2026-09-15, Baseline 274 ausgeführte Tests PASS vor diesem Inkrement; dieses Inkrement ergänzt 10 Tests (284 PASS) und 2 echte Browser-Checks (CI). Der Struktur-Builder ist der MVP-Schritt (v0.1) der [AXM-Analyse](axm-analysis.md): **deklarative, versionierte Sitemap-/Komponentenmodelle mit deterministischer Generierung** — kein Code-Generator, kein UI-Renderer, kein Agenten-System.

## Zweck / explizite Non-Goals
Operatoren beschreiben eine Seiten-/Komponentenstruktur als Graph (Knoten + Beziehungen), versionieren ihn append-only und lassen daraus **read-only** eine Routing-Übersicht und ein UI-Platzhalter-Skelett berechnen. **Non-Goals:** keine Code-/Projektgenerierung (keine Datei wird geschrieben, nichts wird ausgeführt), kein React/Build-Step (vanilla JS + SVG), kein Graph-Database-Dienst (JSON-Graph in der bestehenden SQLite-Record-Tabelle; die Analyse selbst nennt „JSON-Graph oder Neo4j (Einfach)" — gewählt wurde der einfachere, repo-konforme Weg), keine A2UI-/Agenten-Integration, kein Versionsvergleichs-UI, keine adaptive Präsentation, keine Unsicherheits-Visualisierung, keine Multi-Agenten (alles roadmap-offen, s. [AXM-Analyse](axm-analysis.md)).

## Datenmodell
- **Knoten (Node):** `local_id` (Muster `^[a-z0-9][a-z0-9_-]{0,63}$`, version-lokal eindeutig), `kind` ∈ page/section/component/action/data, `name` (1–120), `permissions` (Liste, max. 8 Einträge à 64 Zeichen — **deklarierte Metadaten, keine durchgesetzte Autorisierung**), `note`.
- **Beziehungen (Edge):** `source`/`target` (müssen existieren, keine Self-Edges), `kind` ∈ contains/triggers/depends_on.
- **Grenzen:** max. 64 Knoten / 128 Beziehungen pro Version (MVP-Bound).
- **Struktur (Registry-Record):** name, description, `version` (Zeiger auf neueste Version), `state` active/deactivated.
- **Version (append-only Record):** vollständiges Modell (nodes+edges), `version`-Nummer, `predecessor_id`-Kette, `manifest_hash` (SHA-256 über kanonisches JSON), note, Ersteller/Zeitpunkt. Versionen sind unveränderlich; es existiert kein Lösch-Endpunkt.

## Validierungsregeln (vollständig vor jeder Persistierung, nie reparierend)
1. contains nur von page/section-Knoten (Container).
2. Höchstens ein contains-Elternteil pro Knoten; contains-Kanten müssen azyklisch sein (Forest).
3. Seiten-Namen müssen einen nicht-leeren URL-Slug ergeben (`slug()`: Kleinbuchstaben, Umlaute ä/ö/ü/ß → ae/oe/ue/ss, Nicht-Alphanumerisches → einzelnes `-`, gekürzt/stripped).
4. **Genau eine Wurzel-Seite** (belegt den Pfad `/`); weitere Seiten hängen als contains-Kinder (direkt oder über verschachtelte Seiten).
5. Generierte Routen-Pfade müssen einzigartig sein.
6. Beim Anlegen/Versionieren identisch wiederholte Manifeste → 409 (eine neue Version muss das Modell ändern).

## Generierung (CALCULATED, Query)
`generate_routes`: deterministische Routing-Übersicht über die Seiten-Containment-Kette — Pfad = `/slug-Chain`; **Seiten unterhalb einer Sektion routen nicht** (sie erscheinen nur im Skelett der umgebenden Seite). `generate_skeleton`: verschachteltes Platzhalter-Skelett (Wurzeln = Knoten ohne contains-Elternteil; `placeholder: 'EMPTY'`; triggers/depends_on als `relations` am Zielknoten; permissions mitgeschrieben). Die Ausgabe ist **version-gepinnt** (Default: neueste; `?version=` für historische), `result_class: CALCULATED`, `prediction: NONE`, `basis: STRUCTURE_VERSION_MANIFEST`; ein gespeicherter Hash-Widerspruch (`stored_hash ≠ manifest_hash`) lässt die Generierung mit 503 ablehnen. Gleiches Manifest → byte-gleiches Ergebnis, kein versteckter Zustand.

## API-Vertrag
| Route | Rolle | Wirkung | Fehler |
|---|---|---|---|
| POST /api/structures | operator | Struktur-Registry-Eintrag + unveränderliche Version 1 aus dem vollständigen Modell (StructureCreateInput: name/description/nodes/edges/note); vollständige Validierung vor Persistenz; Not-Stop blockiert | 401/403/409 (Stop)/422 |
| GET /api/structures | both | Lesende Liste (limit/offset, max. 100) | 401 |
| GET /api/structures/{id} | both | Lesender Einzelzugriff | 401/404 |
| GET /api/structures/{id}/versions | both | Unveränderliche Versionshistorie (neueste zuerst) mit Manifest-Hashes | 401/404 |
| POST /api/structures/{id}/versions | operator | Neue unveränderliche Vollversion (predecessor-Kette; identischer Manifest-Inhalt → 409; vollständige Validierung; Not-Stop und deaktivierte Struktur blockieren; Registry-`version` zeigt danach auf die neue Version) | 401/403/404/409/422 |
| GET /api/structures/{id}/generate?version= | both | CALCULATED: Routing-Übersicht + UI-Platzhalter-Skelett aus genau einer gespeicherten Version; schreibt keine Datei, führt nichts aus | 401/404/503 (Hash-Widerspruch) |
| POST /api/structures/{id}/deactivate | reviewer | Bestätigte Deaktivierung (`{confirm: true, reason ≥ 8 Zeichen}`); alle Versionen/Historie bleiben erhalten; kein Lösch-Endpunkt; Not-Stop blockiert | 401/403/404/409/422 |

## UI (Sektion „Struktur-Builder (AXM v0.1)")
Gemäß [PLAN-UI-Spezifikation](../21-plan/plan-ui-interaction-spec.md): Struktur-Select + Anlege-Formular (Operator; legt Version 1 mit Wurzel-Seite `root` an), SVG-Canvas mit Auto-Tree-Layout (contains solide, triggers/depends_on gestrichelt mit Pfeil), **Drag&Drop verschiebt ausschließlich die Ansichtsposition** (localStorage `atze-structure-positions-<id>`, pro Browser lokal — nie das Modell), Knoten-Inspektor bei Klick (Name, Typ, Berechtigungen, Notiz, Beziehungen; Ändern/Entfernen als Staging), Knoten-/Beziehungs-Formulare als **lokales Staging** (Statuszeile: „lokal vorbereitet — noch nicht versioniert"), Commit-Formular → `POST versions`, Generieren-Button → Routen + Skelett, Live-Vorschau des lokalen Modells im Canvas. Verbinden/Aktualisieren verwirft nicht committete Entwürfe (gleiche Politik wie der PLAN-Editor). Alle Ausgaben als TextContent (kein Markup-Injection-Pfad); Server validiert beim Commit vollständig erneut — die UI-Prüfung ist Komfort, nicht Sicherheitsgrenze.

## Browser-/Test-Evidenz
`tests/test_structures.py` (STR-001..010): Rollen (anonym 401, Reviewer 403 auf Erstellung/Versionierung/Deaktivierung), vollständige Graph-Validierung (doppelte IDs, unbekannte/Self-Endpunkte, Nicht-Container-Eltern, Zyklen, Doppel-Eltern, Bounds, Slug- und Routen-Kollisionen, zwei Wurzeln), append-only-Versionierung mit unveränderter Historie + 409 bei identischem Manifest, deterministische Generierung (Routen, Skelett, relations, wiederholter Aufruf byte-gleich), Version-Pinning (alte Version behält alte Routen; unbekannte Version 404), bestätigte Deaktivierung mit Daten-/Historie-Erhalt (Operator 403, unbestätigt 422, Wiederholung 409), Not-Stop blockt Mutationen aber nicht Lesezugriff/Generierung, permissions als deklarierte Metadaten (Bounds 422), Slug-Normalisierung (Umlaute/Leerzeichen/Satzzeichen, verschachtelte Pfade), Seiten-unter-Sektion-Semantik. Browser-Gate (Chromium CDP, CI): BROWSER-AXM-01 (Anlage über UI-Formular → echte Struktur Version 1 in der API, Canvas rendert, Generierung deterministisch `/`), BROWSER-AXM-02 (Staging von Knoten mit Markup im Namen + contains-Beziehung → Canvas-Zustand, Inspektor, Commit → Version 2, generierte Route im DOM = API-Ergebnis, kein `<img>`/kein Skript-Pfad, Historie append-only).

## Grenzen / Nicht validiert
Permissions werden gespeichert und reproduziert, aber **nicht durchgesetzt** (keine Autorisierung an der Struktur-API). Generierung erzeugt leere Platzhalter — kein echter UI-Code, keine Komponenten-Bibliothek, kein Routing-Framework. Kein Export in Dateisysteme/Repositories, kein Versions-Diff-UI, kein Kollaborations-/Konfliktmodell (letzter Commit gewinnt, Identitäts-409 schützt vor Leer-Commits). Kein Undo über die Verwerfen-Funktion hinaus (Staging ist clientlokal). Drag&Drop-Positionen sind Browser-lokal und nicht Teil des Modells oder Versionierung. Roadmap 12 Software → PARTIAL erweitert ([Modulmatrix](../00-overview/roadmap.md)); v1.0/v2.0-Schritte der AXM-Analyse bleiben PLANNED, nicht implementiert.
