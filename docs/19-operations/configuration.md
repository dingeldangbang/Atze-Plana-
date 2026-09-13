# Konfigurationsreferenz

Runtime liest ausschließlich Environment. `.env` muss explizit durch die Shell oder den Dienst geladen werden; `config.example.yaml` ist nur eine maschinenlesbare Dokumentationsvorlage, **kein YAML-Loader**. Es gibt keine versteckten Providerkeys; optionale lokale Storage-Wurzeln sind unten dokumentiert.

| Name | Type | Required | Default | Beschreibung | Security sensitivity | Example |
|---|---|---|---|---|---|---|
| ATZE_OPERATOR_TOKEN | string | ja | leer → Startfehler | Bearer für Erfassung/Lesen/Triage, >=32 Zeichen | secret, nie loggen/committen | lokal per secrets.token_urlsafe(48) erzeugen |
| ATZE_REVIEWER_TOKEN | string | ja | leer → Startfehler | Bearer für Review/Approval/Stop/Audit, >=32 und verschieden | secret, separat verteilen | separat zufällig erzeugen |
| ATZE_DB_PATH | path string | nein | data/atze.db | beschreibbare lokale SQLite-Datei | enthält sensible Daten, OS-Rechte nötig | /srv/atze/data/atze.db |

Tokens werden beim Start geladen. Rotation: neue Werte außerhalb Git setzen, Dienst neu starten, alte Tokens müssen dann 401 ergeben. Rollen sind geteilt, nicht individuell. Relative DB-Pfade beziehen sich auf das Arbeitsverzeichnis; Produktion braucht absolute Pfade. Zusätzlich liest v0.2 die zwei unten dokumentierten optionalen Storage-Variablen.

Uvicorn host/port/workers sind CLI-Optionen, keine Appkonfiguration. Getesteter Start: `uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000`. OpenAPI-Erzeugung nutzt `schema_only=True` und startet keine Datenbank, keine geheimnisabhängige Runtime und keinen Server.

## v0.2 — storage roots
| Name | Type | Required | Default | Description | Security sensitivity | Example |
|---|---|---|---|---|---|---|
| ATZE_STORAGE_ROOT | directory path | nein | leer → DB-Elternverzeichnis/objects | lokale Original-/Cacheblobs; wird angelegt | sensible Originaltexte; außerhalb Git; OS-Rechte erforderlich | /srv/atze/objects |
| ATZE_SD_ROOT | directory path | nein | leer → Tier nicht konfiguriert | vorhandenes, administrativ bereitgestelltes Verzeichnis; wird nicht gemountet/angelegt | keine Symlink-/überlappenden Roots; Mount/Backup Betreiberaufgabe | /media/atze-sd/objects |

Fünf App-Variablen ab v0.2. Leere optionale Variablen im Beispiel aktivieren keine SD-Karte. Root-Verzeichnisse dürfen keine Symlinks sein; SD und Local dürfen weder identisch noch verschachtelt sein. Eine Pfadkonfiguration ist keine Hardwareerkennung. Physische Dateinamen werden ausschließlich aus serverseitigen UUIDs erzeugt; logische Pfade sind keine Host-Dateipfade. Root- und Mountverwaltung erfordert einen vertrauenswürdigen OS-Administrator. Vorhandene Mountpunkte, Unterverzeichnisse und Betriebsrechte separat prüfen. Standardablage unter `data/` ist Git-ignoriert; externe Root-Pfade ebenfalls niemals committen.

## v0.2.1 — explizite Testgrenze
| Name | Type | Required | Default | Description | Security sensitivity | Example |
|---|---|---|---|---|---|---|
| ATZE_MODE | enum operational/test | nein | operational | tatsächlicher Instanzmodus, in SQLite und `.atze-mode` je Objektwurzel dauerhaft gebunden | Testbestände nicht in Betrieb umetikettieren; kein Fake-Backend-Schalter | operational |

Sechs App-Variablen ab v0.2.1. `test` benötigt neue leere oder bereits testmarkierte Bestände; Mischbetrieb und Moduswechsel schlagen fehl. Bestehende unmarkierte DBs/Wurzeln dürfen in operational weiterbetrieben werden, ihre historischen Daten sind dadurch NICHT als echte Beobachtungen verifiziert. Ein Betreiber muss Legacy-Herkunft prüfen. Fehlende SD-Wurzeln werden nicht angelegt; bei späterem Zugriff wird der Marker ebenfalls geprüft. Ein neu eingehängter unmarkierter Pfad bleibt bis zum Neustart nach Administratorprüfung UNAVAILABLE; GET-Abfragen erzeugen keine Marker. Marker niemals löschen/ändern, um eine Ablehnung zu umgehen. Betriebsmodus bedeutet nicht Produktionsfreigabe. `/health` und authentifiziertes `/api/runtime` zeigen den tatsächlichen Modus, die UI kennzeichnet TEST ausdrücklich.
