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

## v0.3 — Challenge-Worker-Grenze
| Name | Type | Required | Default | Description | Security sensitivity | Example |
|---|---|---|---|---|---|---|
| ATZE_CHALLENGE_TOKEN | string | für Challenge/Freigabe ja, für Serverstart nein | leer → Worker NOT CONFIGURED | dritter separater Token >=32 Zeichen, verschieden von Operator/Reviewer | secret; nur API und separatem Challenge-Prozess geben | separat per secrets.token_urlsafe(48) erzeugen |

Sieben App-Variablen. Kein Token → keine akzeptierten neuen Taskentscheidungen. Worker separat mit `python -m app.challenge_worker --url http://127.0.0.1:8000` starten, für genau einen echten Job optional `--once`. Remote-Transport benötigt HTTPS. Der Worker liest nur ATZE_CHALLENGE_TOKEN, benötigt keine DB-Pfade/Operator-/Reviewer-Tokens und erhält keine solchen Daten von der API. Keine Weiterleitung des Tokens bei HTTP-Redirects. Fehlender/ausgefallener Worker führt zu pending/blocked, nie internem Ersatz-PASS. Testmodus schaltet keine Sonderregeln frei; Smoke erzeugt seinen eigenen dritten Token/Prozess.

## Privacy-first model boundary — experimental, not full HF integration
| Name | Type | Required | Default | Description | Security sensitivity | Example |
|---|---|---|---|---|---|---|
| ATZE_AI_CONFIG | JSON file path | nein | leer → keine Provider | trusted host config, at startup; providers with id/mode/origin/token_env/region | außerhalb Git; niemals Tokens in JSON; nur administrativ editieren | /srv/atze/private/ai-providers.json |

Acht feste App-Environmentvariablen. Providercredential dynamisch über explizites `token_env` mit Präfix `ATZE_AI_TOKEN_`; mindestens 32 Zeichen, getrennt von Operator/Reviewer/Challenge. Kein Defaulttoken. Fehlende Credential → BLOCKED ohne Socket. Keine URL-/Credentialkonfiguration durch Modellantwort oder Operator-API. System-CA-Trust für TLS; kein `verify=false`. `SSL_CERT_FILE` ist Python/OpenSSL Trust-Konfiguration, keine Option zur Abschaltung von TLS-Prüfung. Hostkonfiguration/Secrets/CA-Rechte separat absichern. JSON-Vertrag und realer API-Ablauf: [Model Gateway](../02-core/model-gateway.md).

## Bright Data discovery only
`ATZE_BRIGHTDATA_OAUTH_TOKEN`: optional OAuth access token, secret environment/secret manager only; default blank (disabled). No login/refresh automation or API-key URL fallback. Never commit a value. Existing Privacy Lock/default deny still applies; [contract](../22-mcp/brightdata.md).
