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
