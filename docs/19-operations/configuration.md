# Konfigurationsreferenz

Runtime liest ausschließlich Environment. `.env` muss explizit durch die Shell oder den Dienst geladen werden; `config.example.yaml` ist nur eine maschinenlesbare Dokumentationsvorlage, **kein YAML-Loader**. Es gibt keine versteckten Providerkeys oder optionalen Integrationen.

| Name | Type | Required | Default | Beschreibung | Security sensitivity | Example |
|---|---|---|---|---|---|---|
| ATZE_OPERATOR_TOKEN | string | ja | leer → Startfehler | Bearer für Erfassung/Lesen/Triage, >=32 Zeichen | secret, nie loggen/committen | lokal per secrets.token_urlsafe(48) erzeugen |
| ATZE_REVIEWER_TOKEN | string | ja | leer → Startfehler | Bearer für Review/Approval/Stop/Audit, >=32 und verschieden | secret, separat verteilen | separat zufällig erzeugen |
| ATZE_DB_PATH | path string | nein | data/atze.db | beschreibbare lokale SQLite-Datei | enthält sensible Daten, OS-Rechte nötig | /srv/atze/data/atze.db |

Tokens werden beim Start geladen. Rotation: neue Werte außerhalb Git setzen, Dienst neu starten, alte Tokens müssen dann 401 ergeben. Rollen sind geteilt, nicht individuell. Relative DB-Pfade beziehen sich auf das Arbeitsverzeichnis; Produktion braucht absolute Pfade. Keine anderen Environment-Variablen werden im Appcode gelesen.

Uvicorn host/port/workers sind CLI-Optionen, keine Appkonfiguration. Getesteter Start: `uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000`. OpenAPI-Erzeugung nutzt `schema_only=True` und startet keine Datenbank, keine geheimnisabhängige Runtime und keinen Server.
