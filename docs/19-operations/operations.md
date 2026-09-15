# Betrieb, Monitoring, Backup, Recovery und Maintenance

## Monitoring
`GET /health` prüft eine SQLite-Transaktion und liefert Status/Version, bei Storage-OperationalError redacted 503. Keine Prometheusmetriken, automatischen Alerts, WebSockets oder externen Checks. Betreiber überwacht Prozess, RSS, CPU, freien Diskplatz, HTTP-Fehler und Backuplauf. Audit über Reviewer-API exportieren/paginieren; keine Tokens in Logsammler übernehmen.

## Backup
**Ab v0.2 ist dieser Befehl nur ein DB-Backup. Original-/Cachewurzeln sind NICHT enthalten; siehe die v0.2-Erweiterung unten.**
SQLite-WAL nicht durch Kopieren allein der Hauptdatei sichern. Die mitgelieferte `scripts/backup.py` nutzt die SQLite-Backup-API und prüft `PRAGMA integrity_check`. Ziel muss neu sein; produktive Snapshots sicher außerhalb Git aufbewahren. Beispiel nach Laden von `.env`:

```sh
python scripts/backup.py "$ATZE_DB_PATH" /sicherer/pfad/atze-snapshot.db
```

Der Zielordner muss existieren und zugriffsgeschützt sein. Kein automatischer Zeitplan, kein Offsite-Upload, keine Verschlüsselung/Retention implementiert. Stopflag ist kein globaler Schreibstopp: Projekte und Evidenz können weiter erfasst werden.

**In-App-Backup-Endpunkt (2026-09-15):** `POST /api/operations/backups` (Reviewer, `confirm`+`reason`) erzeugt einen verifizierten SQLite-Snapshot (exklusive 0600-Datei unter `<DB-Verzeichnis>/backups/`, SQLite-Backup-API, `integrity_check`) mit durablem Backup-Record inkl. SHA-256, Größe und je-Kind-Record-Zählern sowie Audit `operations.backup_created`; `GET /api/operations/backups` (beide Rollen) listet. Der Snapshot enthält den Zustand **vor** seinem eigenen Record/Audit. Unter Not-Stop erlaubt (read-only, risikoreduzierend). Scope bleibt **DATABASE_ONLY** — Objektwurzeln wie oben/v0.2 beschrieben separat sichern; ein Record belegt nur den Snapshot-Zeitpunkt, keinen Offsite-Kopien- oder Restore-Drill. Kein Lösch-Endpunkt.

## Recovery / Rollback
1. Dienst stoppen; aktuelle DB einschließlich WAL-Zustand aufbewahren, nicht überschreiben.
2. Backup mit `sqlite3.connect(...).execute('PRAGMA integrity_check')` oder Backup-Werkzeug prüfen.
3. Backup auf **neuen** lokalen Pfad kopieren, OS-Rechte setzen, `ATZE_DB_PATH` dort setzen.
4. Passende Softwareversion starten. Health, Projekt-/Evidence-/Task-Listen, Audit und Stop kontrollieren.
5. Erst nach menschlicher Abnahme Traffic umschalten. RPO/RTO sind bisher nicht gemessen.

Schema v1 ohne Migrationen; neue Versionen brauchen versionierte Up-/Down-/Restore-Strategien. Paketrollback allein garantiert keine Datenkompatibilität.

## Maintenance
Dependencies regelmäßig auditieren; Lockfile nach Update neu validieren. Tokens rotieren; Diskwachstum durch Originaltexte/Audit beobachten. Keine Lösch-API: Retention oder Datenschutzlöschung benötigt eine reviewed Erweiterung, nicht ad-hoc SQL im Livebetrieb. [Fehlerdatenbank](troubleshooting.md).

## v0.2 — wichtige Backup-/Storage-Erweiterung
**Das obige SQLite-Backup schützt nur die DB, NICHT mehr den vollständigen Datenbestand.** Archive und Cache liegen unter `ATZE_STORAGE_ROOT` bzw. optional `ATZE_SD_ROOT`. Vor Gesamtsicherung alle schreibenden Server-/Maintenanceprozesse stoppen, Datenbank per Backup-API und alle Wurzeln inklusive Retention-Kopien sichern. Erst nach Restore von DB UND Objekten Archive über content/resolve hashprüfen. Vollständige Multi-Tier-Backupautomatisierung und Produktions-Recovery-Abnahme fehlen. Siehe [Migrations-/Recovery-Vertrag](../20-context-storage/architecture.md).

`GET /api/storage/health` liefert echte Dateisystemkapazität und logische Cache-/Archivbytes, keine RAM-/Cloudmessung. Abgelaufener Cache wird nicht automatisch gelöscht: Reviewer ruft `/api/cache/cleanup` mit Grund und begrenzter Batchgröße auf. Keine Archive/Retained Copies per ad-hoc `rm` löschen. `POST /api/context/reindex` baut FTS paginiert aus geprüften Originalen/Memory neu auf; Storage-Ausfall/Korruption stoppt die jeweilige Transaktion. Restore/Manipulation vorhandener Originale niemals durch stilles Rehashen „reparieren“.

## v0.2.1 — Modusmarker bei Backup/Restore
`instance_mode` gehört zur SQLite-Sicherung; `.atze-mode` als versteckte Datei zur jeweiligen Objektwurzel. Bei Dateisicherung/Restore versteckte Dateien mitnehmen. Keine Testdaten durch Löschen/Ändern dieser Marker in Betriebsdaten umetikettieren. Getrennte Wurzeln/DBs je Instanzmodus. Alte unmarkierte Bestände werden beim operational-Start markiert, damit wird ihre Herkunft nicht nachträglich bewiesen. Vor Nutzung Legacy-Herkunft prüfen. Smoke-Tests verwenden keine konfigurierten Betriebsbestände mehr, sondern entfernen ihre eigene temporäre Instanz nach dem Lauf.

## Challenge-Worker v0.3
Worker separat starten/überwachen; `/api/runtime` meldet nur Tokenkonfiguration, nicht Liveness. Prozess kann im Leerlauf NO_PENDING_JOB melden, das ist kein Test-/Challenge-PASS. Bei Abbruch läuft ein Joblease nach 60 Sekunden ab. Neuer Worker darf ihn claimen, veraltete Jobs werden superseded. Neue Evidence/Result/Stopereignisse erfordern explizite Rechallenge; alte Approvals nicht wiederverwenden. API und Worker bei Policyupdates gemeinsam aktualisieren. Kein Report-/Lease-/Tokenoverride zur Fehlerbehebung.

Result/Job/Reports/Audit liegen in derselben SQLite-Sicherung. Quellblobs/Modusmarker weiterhin separat vollständig sichern. Context-Snapshots enthalten Originaltexte: gleicher Schutz/Retentionbedarf wie Evidence. Max. 500 Evidenzen/4 MiB je Snapshot, max. 500 Findings plus Limitbefund; bei Überschreitung BLOCK statt Teilfreigabe. Keine RAM-/Durchsatzgarantie.
