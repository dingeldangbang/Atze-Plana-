# Resource-Manager — versionierte Datei-Registry mit Hash, Referenzen und bestätigter Deaktivierung

Stand 2026-09-14, Baseline 200 ausgeführte Tests PASS vor diesem Inkrement; dieses Inkrement ergänzt 16 Tests (216 PASS). Ressourcen existieren ausschließlich durch echten Operator-Upload (Base64, begrenzt); Metadaten (Name, Art, deklarierte Quelle) sind Owner-Angaben, niemals verifizierte Herkunft.

## Zweck / explizite Non-Goals
Workspace-weite Registry für Datei-Ressourcen (file, image, pdf, cad, measurement, dataset, database_result, query, software, configuration, log) mit unveränderlichem, hash-verifiziertem Content, append-only Versionierung, Referenz-Links (keine Kopien) auf Tasks/Projekte, Byte-Vergleich und reviewerbestätigter Deaktivierung ohne Datenlöschung. Backend-Pfad zur [PLAN-UI-Spezifikation](../21-plan/plan-ui-interaction-spec.md), Abschnitt 17–19 (Resource Panel/Upload/Referenz statt Kopie); UI folgt mit Modul 6. **Kein Viren-/Safety-Scan (NOT IMPLEMENTED, Betreiberverantwortung), keine PDF-/CAD-/Metadaten-Parsing (nur Größe/SHA-256/UTF-8-Preview), kein Workflow-Attach (Workflows NOT IMPLEMENTED), keine Promotion zu Evidence (bestehender manueller Evidence-Fluss bleibt), kein Löschen von Content oder Historie, keine Herkunftsverifikation der deklarierten Quelle.**

## API-Vertrag
| Route | Rolle | Wirkung | Fehler |
|---|---|---|---|
| POST /api/resources | operator | Upload: Content-Blob (auto-Tier, O_EXCL/fsync) + Registry-Record v1 + Audit | 422 Base64/Größe/Art, 409 Stop |
| GET /api/resources | both | Registry-Suche (Name-Teilstring case-insensitiv, SHA-256-Präfix ≥8 Zeichen, kind/state-Filter) | 401 |
| GET /api/resources/{id} | both | Metadaten | 404 |
| GET /api/resources/{id}/content | both | Hash-/Größenverifizierter Byte-Download (Raw, Header mit SHA-256/Version) | 503 korrupt |
| GET /api/resources/{id}/preview | both | UTF-8-Textausschnitt (200 Zeichen) oder explizit BINARY | 503 korrupt |
| GET /api/resources/{id}/versions | both | Unveränderliche Versionshistorie der Familie | 404 |
| POST /api/resources/{id}/versions | operator | Neue unveränderliche Version (Predecessor, Note); identischer Content abgelehnt | 409 identisch/deaktiviert/Stop, 422 |
| POST /api/resources/{id}/links | operator | Referenz-Link auf existierenden Task/Projekt (kein Kopieren) | 404 Ziel, 409 doppelt/deaktiviert/Stop |
| GET /api/resources/{id}/links | both | Link-Historie inkl. unlinked | 404 |
| POST /api/resources/{id}/unlink | operator | Link als unlinked markieren (append-only, Historie bleibt) | 404 fremd/unbekannt, 409 erneut |
| GET /api/resources/{id}/compare/{other} | both | Hash-verifizierter Byte-Vergleich (IDENTICAL/DIFFERENT, gemeinsame Prä-/Suffixbytes) | 404, 503 korrupt |
| POST /api/resources/{id}/deactivate | reviewer | Bestätigte familienweite Deaktivierung (confirm+reason), Daten bleiben lesbar | 403 Rolle, 409 erneut/Stop, 422 |

## Daten-/Speicher-Vertrag
Upload: Base64-Content (single-line, validate), dekodiert ≤ **4 MiB** pro Upload (Dokumentierte Grenze für das 2-GB-Ziel; größere Dateien extern teilen). Speicherung über den bestehenden Storage-Tier (`storage.write`, O_EXCL+fsync+Verifikation), sha256 + size_bytes + Tier + UUID-Key im Record. Versionierung: jede Familie (`family_id`) hat Versionen ≥1 mit `predecessor_id`; neue Version mit identischem SHA-256 zum aktuellen Stand → 409 (keine Scheinversion); Deaktivierung wirkt auf die gesamte Familie. Links sind append-only Records mit `state active|unlinked`; erneutes Verlinken desselben Ziels nach Unlink ist erlaubt (neuer Record). Not-Stop blockt alle Mutationen (Upload, Version, Link, Unlink, Deaktivierung), Lese-/Vergleichszugriffe bleiben. Audit: `resource.uploaded/versioned/linked/unlinked/deactivated` (Deaktivierung nur durch Reviewer, mit Begründung).

## Grenzen / Nicht validiert
Kein Viren-/Malware-/Safety-Scan — es gibt keine Scan-Engine, und keine wird simuliert (Betreiberverantwortung, ausdrücklich NOT IMPLEMENTED). Keine Inhaltsinterpretation: Preview prüft nur UTF-8-Dekodierbarkeit; pdf/cad/image bleiben inhaltlich ungeprüft. Kein UI-Workflow-Attach, kein Projekt-Scoping (Registry ist workspace-global; Sichtbarkeit folgt Rollen, nicht Projekten). Herkunftsangabe `source` ist eine deklarierte Owner-Aussage. **Nicht validiert (NOT RUN):** Uploads realer Anwendungen/Benutzer; nur synthetische Testinhalte. Content bleibt nach Deaktivierung vollständig lesbar — es existiert bewusst kein Lösch-Endpunkt ([Roadmap](../00-overview/roadmap.md)); Vault-/Retention-Policies sind Betreiberthemen.
