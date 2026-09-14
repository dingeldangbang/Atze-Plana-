# ADR-003 — Mobile Project Server, Context und Tiered Storage

## Status
Accepted als Zielarchitektur am 2026-09-13. Erster lokaler Implementierungsschnitt v0.2; keine Behauptung einer fertigen mobilen/MCP-/Cloud-Laufzeit. Erweitert ADR-001, ersetzt nicht dessen Evidence-/Permission-Grenzen.

## Bestandsaufnahme vor Änderung
Ausgangspunkt `d52281f`: FastAPI, ein SQLite-Workspace, zwei Rollen, Evidence/Review, Tasks/Triage/Approval/Stop/Audit, statisches Dashboard, generierte OpenAPI und CI. Keine Dateiablage, Memory, Retrieval, Storage-Adapter oder MCP. Bisherige SQLite-Backups enthalten alle damaligen persistenten Daten; nach dieser Erweiterung reicht DB-Backup allein nicht mehr aus. Bestehende APIs und Records bleiben erhalten.

## Context / Problem
Der Core soll Metadaten, Zustände und Entscheidungen halten, große Originaldaten jedoch nicht zwingend in RAM/SQLite. Mobile/offline Verfügbarkeit und transparente Speicherorte sind Ziel. Retrieval darf nie zur Wahrheitsschicht oder Tool-Freigabe werden. Cacheverlust darf weder Memory noch Archive löschen.

## Decision
- GitHub bleibt versionierter technischer Backbone für Code, Konfiguration, Schemas, Tests, ADRs und Agentendefinitionen (später). Private Runtime-Daten/Secrets werden NICHT automatisch nach GitHub synchronisiert.
- Memory: strukturierte, append-only Projektinformationen mit separater Kennzeichnung von Faktbehauptungen und Inferenzen sowie Evidence-/Task-/optional Commit-Referenzen.
- Archive: unveränderliche Originalobjekte, UUID und stabiler logischer Pfad `/project/{project_id}/{relative_path}`. Physische Pfade nie aus Benutzereingaben konstruieren.
- Cache: separate, taskgebundene, ablaufende Objekte; keine RAG-Indexierung, kein Evidence-Ursprung ohne explizite dauerhafte Kopie. Cachebereich ist KEINE Prozess-/Container-Sicherheitsisolation.
- Tier 0 RAM, Tier 1 lokaler Datenträger, Tier 2 SD, Tier 3 Server, Tier 4 Cloud bilden das Zielmodell. Im ersten Schnitt nur lokaler Datenträger und optional vom Betreiber bereitgestelltes SD-Verzeichnis. Kein automatisches Mounten, Formatieren oder Remote-Provisioning.
- Speicherwechsel: Quelle prüfen → neue Kopie schreiben und fsync → Ziel lesen und Hash prüfen → Metadaten/Audit atomar committen → Quelle behalten. Keine automatische Löschung dauerhafter Quellkopien; Crash kann unreferenzierte Kopien hinterlassen, niemals automatisch Originale beseitigen.
- Resource Manager: echte Diskmessungen für konfigurierte lokale Wurzeln, konservative Kapazitätsauswahl. Keine erfundenen RAM/SD/Server/Cloud-Werte. Hintergrund-Rebalancing und Remote-Platzierung bleiben geplant.
- Retrieval: lokaler SQLite-FTS5-Index für begrenzte UTF-8-Texte und Memory, Quell-ID, logischer Ort, Zeit, Version/Hash, Zeichenposition und Live-Evidencezustand je Treffer. Kein LLM, keine semantischen Embeddings, kein Wahrheits-/Kausalitätsbeweis.
- MCP ist die vorgesehene standardisierte Tool-/Context-Schnittstelle; der erste Schnitt stellt die Domainverträge per HTTP bereit. Keine proprietäre REST-Route als MCP ausgeben. Ein echter MCP-Adapter benötigt Protokoll-/Transport-/Auth-Tests vor Freigabe.
- Offline Queue und Sync: zukünftige eigene Eventidentitäten, idempotente Zustellung, Konfliktzustände und explizite Merge-/Triage-Entscheidungen. Lokale Nutzung ohne Cloud ist schon möglich; das ist noch keine synchronisierte Offline Queue.

## Sicherheitsreihenfolge
Plan/Task → Context/Retrieval → Preflight-Triage/Permission/Approval → Ressourcenallokation → isolierte Execution (zukünftig) → Tests → Ergebnis-Triage → Memory/Evidence-Update → optional reviewed GitHub-Änderung. Ergebnis-Triage ersetzt niemals das Preflight-Gate.

Storage-Metadatenpflege ist keine Geräteaktion. Archivwechsel und Cachebereinigung benötigen Reviewer und werden bei aktivem globalem Stop blockiert. Der Operator darf Texte erfassen, aber keine Quellen löschen oder Tierwechsel erzwingen. Keine Flash-/Shell-/Cloud-/Finanz-Ausführung wird hinzugefügt.

## Alternatives
Alles in SQLite: einfache Backups, aber unnötiges Core-Wachstum. Sofortige verteilte Objekt-/Vektordatenbanken: höherer Betriebsbedarf und neue Konsistenz-/Credential-Risiken. Automatisches Move/Delete: könnte bei Crash/SD-Ausfall Daten verlieren. Ungeprüftes Universal-MCP-Terminal: Permission-Bypass-Risiko.

## Consequences / Migrations
Additive Tabellen/Indizes, kein Löschen vorhandener Records. Archive/Cache liegen außerhalb SQLite; Backup/Restore muss Datenbank UND konfigurierte Objektwurzeln zusammen sichern. FTS ist abgeleitet, kein Original. SD ist ein administrativ deklarierter Pfad, kein nachgewiesenes Hardwaregerät. Einzelprozess-/lokales-Dateisystem-Modell bleibt; Android, echte SD-Hotplugfälle, Netzwerkdateisysteme, 2-GB-Last und Cloud brauchen eigene Nachweise.

## Umsetzung / Validierung
1. Typisierte Memory-/Storage-/Retrieval-Verträge und additive Persistenz.
2. Hashgeprüfte Originalablage und Kopiewechsel mit Source Retention, taskgebundener Cache und expliziter Cleanup.
3. Lokales FTS mit Projektfilter und Provenance; Storage Health ohne Beispieldaten.
4. Negativtests: Traversal, falsche Rolle, Cross-Project, Inferenzen, Korruption, Copy-/Auditfehler, fehlender Tier, Kapazität, Restart, Cache/Archive-Trennung.
5. Dokumentations-/API-/Testgeneration, Build, Smoke und GitHub-CI. Nicht implementierte Zielteile zentral kennzeichnen.
