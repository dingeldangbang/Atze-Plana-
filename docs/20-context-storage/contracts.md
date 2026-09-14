# Context-/Storage-Verträge v0.2

Exakte Inputs/Outputs/Constraints/Fehler: [OpenAPI](../../openapi.yaml), [API-Referenz](../08-network/APIs.md). Ausführbares synthetisches Beispiel: [HTTP-Smoke](../../scripts/smoke.py), gestartet wie im [Quickstart](../../QUICKSTART.md). Keine Beispieldaten sind Hardware-/Quellenbeobachtungen.

## Gemeinsame Dependencies / Configuration / Permissions
Python 3.11+, FastAPI/Pydantic, lokales SQLite mit FTS5, POSIX-Dateisystem mit `O_NOFOLLOW`, `O_DIRECTORY`, `fsync`, `statvfs`. [Sieben Umgebungsvariablen](../19-operations/configuration.md); optionale Storage-Root/SD-Root, keine Providercredentials. Operator erfasst Archive/Cache und nicht-autoritative Memory; beide Rollen lesen/suchen; Reviewer darf Relocation, Cache-Cleanup und Reindex. Kein per-project ACL: Projektfilter trennt Suche fachlich, nicht Benutzerberechtigungen. Alle Endpunkte Bearer-authentifiziert.

## Archive / Unified Namespace
**Purpose:** Originaltext langfristig unveränderlich halten, physischen Ort transparent machen.

**Inputs:** Projekt, eindeutiger relativer ASCII-Pfad, UTF-8-Text (1..65.536 Zeichen), Evidence-IDs, placement=auto/local. Pfadsegmente dürfen nicht leer, `.` oder `..` sein. Kein absolutes Verzeichnis, `%`-Encoding oder Backslash. **Outputs:** ID, `/project/{id}/{relative_path}`, Hash, Bytelänge, Ort/Retained Copies/Version. Text inkl. führender/abschließender Whitespaces wird exakt gespeichert und gehasht; anders als normalisierte Evidence-Strings.

**Side Effects:** Blob schreiben, file-/directory-fsync, zurücklesen/vergleichen, danach Archivmetadaten + FTS + Audit in einer SQLite-Transaktion. **Validation/Tests:** STO-001/002/003/004/005/006/010/011/012; STO-011 verweigert einen nicht konfigurierten Tier und jeden nicht kanonischen Objektschlüssel, STO-012 prüft einen konkurrierend erzeugten Modusmarker (validieren statt überschreiben, fremder Modus 503); Duplicate 409, Cross-Project/Schema 422, fehlendes Projekt 404, Storage/Hash 503, Kapazität 507. Stop blockiert Erfassung/Umplatzierung, nicht Lesen.

**Examples:** `POST /api/archive`; `GET /api/archive/{id}/content`; `GET /api/archive/resolve?logical_path=...` liefert jeweils das aktuelle hashgeprüfte Original. Query-Parameter URL-encodieren. `POST /api/archive/{id}/relocate` mit target=local/sd und Reviewer-Grund.

**Known Limitations / Security:** Keine Revision/Overwrite/Delete-API, Binäruploads, Streaming oder CDN. Dateien und FTS im Klartext. Physische Namespaces basieren nur auf UUIDs; Datei-/Root-Symlinks werden nicht verfolgt. Host-Administratoren und Root-Eltern/Mountverwaltung bleiben vertrauenswürdig; dies schützt nicht gegen kompromittierte Hosts. Root darf nicht als fremd beschreibbare Sandbox verwendet werden.

## Speicherwechsel / Failure Recovery
```mermaid
sequenceDiagram
    participant R as Reviewer
    participant A as API/SQLite Transaction
    participant S as Source Tier
    participant T as Target Tier
    R->>A: relocate(id,target,reason)
    A->>A: Stop / Rolle / Kapazität prüfen
    A->>S: Quelle lesen + Hash/Bytelänge prüfen
    A->>T: neue UUID-Kopie schreiben + fsync
    A->>T: zurücklesen und Originalbytes vergleichen
    A->>A: Tier/Key/retained_copies + Audit committen
    A-->>R: unveränderter logischer Pfad / Hash
    Note over S,T: Quelle bleibt erhalten; kein automatisches Delete
```

Bei Schreib-/Verifikations-/Audit-/DBfehler bleibt die bisherige DB-Referenz maßgeblich. Die API wartet durch Function-Scope-Dependencies auf den SQL-Commit, bevor sie Erfolg sendet (TX-001); ein Commitzeitfehler ergibt 503. FS und DB können nicht gemeinsam atomar committen: ein Crash kann partielle oder vollständige unreferenzierte Kopien hinterlassen. Diese werden **nicht automatisch gelöscht**. Ein Reviewer muss sie anhand Original-/Metadaten-/Auditnachweis später behandeln. Kein Release von Quellkopien, keine Crash-/Powerloss-Garantie jeder SD-Hardware und keine automatische Fallback-Lesung von Retained Copies. Bei aktivem Tierausfall gibt es 503; Quelle bleibt für geprüfte manuelle Recovery erhalten.

## Resource Manager / Storage Health
**Purpose:** neue bounded Textobjekte anhand verfügbarer Kapazität platzieren, reale Ressourcen sichtbar machen. **Inputs:** geschätzte tatsächliche UTF-8-Bytelänge und placement. **Outputs:** Tierwahl oder 507; Health meldet total/used/free/used_percent für konfigurierte erreichbare Wurzeln sowie aktive/abgelaufene Cachebytes und logische Archivbytes.

**Policy:** auto versucht Local bei Auslastung <85%, danach SD <90%; jeweils freier Speicher >=Objektgröße+16 MiB Reserve. Explizites local/sd nimmt nur diesen Tier. Werte sind feste konservative Konstanten, keine automatisierte Performanceanalyse. Außenseitige Diskbelegung kann zwischen Check und Write ändern → Writefehler, kein Indexwechsel. Alle bestehenden API-Transaktionen werden per SQLite serialisiert; kein Multi-Host-Allocator.

**Validation:** STO-007/009 prüft echte lokale Messung und injizierte Kapazitätssituationen. Nicht vorhandene RAM-/Server-/Cloud-Adapter haben `available=false`, Messwerte `null`, nicht 0% oder erfundene Werte. **Limitations:** pro konfiguriertem Dateisystem, kein echter SD-Gerätenachweis; zwei Roots auf demselben Datenträger sind keine zwei unabhängigen Kapazitäten. Keine RAM-/CPU-Limitierung, per-project Quoten, Zugriffshäufigkeit, Prioritäten, Offline-Pinning oder Hintergrundmigration. Source Retention spart keinen Platz beim Umplatzieren; automatische Löschung braucht später einen stärkeren Haltbarkeits-/Freigabevertrag.

## Cache
**Purpose:** ersetzbare taskgebundene temporäre Texte vom Archiv und Memory trennen. **Inputs:** existierende Task-ID, Text, TTL 60..86.400 Sekunden (Default 3600). **Outputs:** ID, Task/Projekt, Hash, Tier, expiry, Status. **Validation:** CACHE-001/002, STO-008. Keine Indexierung; TTL hängt an Serverzeit. `GET /api/cache/{id}/content` prüft Hash und Expiry, bei Ablauf 410, bei vorzeitigem Verlust 503.

**Lifecycle:** `POST /api/cache` → GET/Arbeitsnutzung → falls wichtig Text explizit vor Ablauf als Archiv speichern → Reviewer `POST /api/cache/cleanup` mit Grund/limit. Cleanup selektiert nur abgelaufene Cache-Records, committet zuerst expired-Tombstones, löscht dann einzelne Cacheblobs und auditiert deleted. Fehlgeschlagener Delete kann wiederholt werden. Ein Crash nach Delete vor Audit lässt eine abgelaufene Referenz zurück; Retry toleriert fehlenden Blob. Archive/Memory und lebender Cache werden nicht ausgewählt. Kein Backgroundtimer; abgelaufene Daten belegen bis zum expliziten Cleanup weiterhin Platz.

**Security / Limits:** kein Ausführen von Agentencode/Terminaltools; keine Container-, Netzwerk- oder Prozessisolation. Keine `inputs/workspace/tools`-Verzeichnisstruktur oder Build-Workspace-Allokation. Keine durch Agenten steuerbaren Hostpfade. Eine Cacheallocation ist keine Task-Triage-/Ausführungsfreigabe. Persistieren wichtiger Originale ist nicht automatisch; vor Cleanup von Cache unabhängig sichern.

## Project Memory
**Purpose:** append-only projektbezogene Erinnerungen mit Evidenzbindung. **Inputs:** Kategorie fact/inference/decision/task_history/user_preference/project_state/device_history/test_history/repair_history/trend_history/agent_history; Text, Evidence-IDs, optional Task-ID/Commit-SHA. **Outputs:** recorded, ID, Zeit, Hash. **Validation:** MEM-001/002; Seit v0.3 ist direkte neue fact/decision-Erfassung 409; autoritative Übernahme nur über den aktuellen Result-/Challenge-/Triage-Adopt-Pfad. Ältere Fakten bleiben recorded, nicht automatisch Challenge-akzeptiert. Doppelte/fremde Evidence-/Task-Referenzen 422. Commit nur Formatprüfung, kein GitHub-Netzwerkabruf.

**Safety:** `fact` heißt belegte **eingereichte Faktbehauptung**, nicht automatisch bewiesene Wahrheit; Memory selbst bleibt recorded. Eine inference bleibt inference, auch wenn ihre Quellen verified sind. History-Kategorien aktivieren keinen entsprechenden Geräte-/Agenten-/Repairadapter. User Preferences sind Text, keine zusätzliche Policy oder Permission. Keine automatische Bevorzugung manipulativer Memory-Anweisungen. Metadatenpflege wie Memory-Erfassung wird durch den Triage-Stop nicht global eingefroren; Storage-Mutationen hingegen schon.

## Retrieval / RAG-Vorstufe
**Purpose:** lokale relevante Quelltextbereiche finden, nicht Antworten erfinden. **Inputs:** existierendes Projekt, Query <=256 Zeichen, limit 1..30. Bis zu 16 Worttokens, AND-Verknüpfung, gequotet; keine ungeprüfte FTS-Query-Sprache. **Outputs:** source_id/type, Kategorie, location, logical_path, timestamp, SHA-256/version, start_char/end_char (end exklusiv), Text, Evidence-IDs mit aktuellem Zustand, aggregierter evidence_state und `allowed_for_action=false`.

FTS5 über Archiv-/Memory-Texte, Chunkgröße 1024 Unicodezeichen, Schritt 896 (128 Überlappung), BM25-Reihenfolge mit deterministischem Tiebreaker. Kein Byteoffset, keine PDF-Seite oder Statistik-Confidence. Evidence state: rejected wenn irgendeine Quelle rejected; verified nur bei nichtleerer vollständig verified Quellenliste; sonst unverified. Dies ist der Zustand verknüpfter Evidence, **nicht** die automatische Validierung des gefundenen Texts. Triage muss Evidence der geplanten Task separat prüfen.

**Failure Modes / Tests:** fehlendes Projekt 404, leere Wortquery/limit 422, beschädigter Index→fehlende Source 503; RAG-001/002 und MEM-001. Lokaler FTS enthält Textkopien: bei offline Tier kann ein indizierter Auszug weiterhin gefunden werden, ohne dass das Original erreichbar ist. Suchergebnis-Hash bezeichnet das beim Ingest geprüfte Original; bei Suche wird nicht jede Datei neu gehasht. Vor tatsächlicher Originalverwendung content/resolve aufrufen. Kein Remote-Fallback oder nachträglicher Wahrheitsbeweis.

**Rebuild:** Reviewer `POST /api/context/reindex` mit reason/offset/limit; indexiert eine Seite Archive/Memory neu, Archive werden zuvor gelesen/hashgeprüft. `next_offset` für nächste Seite verwenden, bis indexed_ids leer. Jede Seite atomar und auditiert; Fehler rollt die Seite zurück. Stop blockiert Rebuild. Kein Import alter Evidence, GitHub-Issues, Logs, PDF/CAD/Bilder oder Messgeräte.
