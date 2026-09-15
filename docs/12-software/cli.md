# Read-Only-CLI — dokumentierte Abfragen gegen einen laufenden Core

Stand 2026-09-15, Baseline 263 ausgeführte Tests PASS vor diesem Inkrement; dieses Inkrement ergänzt 4 Tests (267 PASS). Die CLI (`python -m app.cli`) ist **rein lesend**: sie spiegelt die dokumentierte API, erfindet keine Felder und führt **keine Mutationen** aus (Roadmap 12: kein universeller Softwareprojekt-Builder).

## Befehle
`status` (ohne Token, `GET /health`) sowie mit Token: `runtime`, `monitoring`, `integrations`, `projects`, `evidence`, `tasks`, `results`, `plans`, `agents`, `resources`, `leases`, `backups`.

```sh
ATZE_BASE_URL=https://core.example ATZE_TOKEN=… python -m app.cli monitoring
python -m app.cli projects --base-url http://127.0.0.1:8000 --token … --raw
```

Optionen: `--base-url` (Standard `ATZE_BASE_URL` oder `http://127.0.0.1:8000`), `--token` (Standard `ATZE_TOKEN`; wird nie ausgegeben), `--raw` (exakte Payload als sortiertes Pretty-JSON). Standardausgabe ist **verlustfrei**: Listen als eine kompakte JSON-Zeile je Eintrag, Objekte als `schlüssel: wert`-Zeilen — keine beschönigende Feldauswahl.

## Fail-Closed-Verhalten
Ohne Token für tokenpflichtige Befehle → Fehler, Exit 1 (keine anonymen Reads). Unerreichbarer Core → Exit 2 mit klarem Fehler, **niemals Ersatzdaten**. 401/403/nicht-200 → Exit 1 mit Status. Exit-Codes: 0 OK, 1 Authentifizierung/Antwort, 2 Verbindung.

## Grenzen / Nicht implementiert
Keine Mutationen (Erstellung/Review/Freigabe bleiben API/UI), kein universeller Projekt-/Geräte-/Agenten-CLI-Builder, kein interaktiver Modus, kein Paging (Standard-Listenlimit der API). Getestet als echter Subprozess gegen einen echten lokalen Uvicorn-Core (CLI-001..004); keine Remote-/TLS-Konfiguration validiert. Roadmap 12 Software → PARTIAL erweitert ([Modulmatrix](../00-overview/roadmap.md)).
