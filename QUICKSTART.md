# Quickstart

## Voraussetzungen
Linux/macOS-Shell, Python 3.11 oder neuer, Git. Geprüfte Umgebung: Linux, Python 3.11.2. Windows/PowerShell ist noch nicht validiert. Für pip ist Internet erforderlich.

```sh
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.lock
cp .env.example .env
python -c 'import secrets; print(secrets.token_urlsafe(48)); print(secrets.token_urlsafe(48))'
```

Die beiden erzeugten Werte lokal in `.env` bei `ATZE_OPERATOR_TOKEN` und `ATZE_REVIEWER_TOKEN` eintragen. Nicht in Chat, Git oder Tickets kopieren. `.env` ist ignoriert, aber nicht verschlüsselt.

```sh
chmod 600 .env
set -a; . ./.env; set +a
uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000
```

Dashboard: Port 8000; in Arena den Live-Preview-Link verwenden. Token im Passwortfeld eingeben. Operator kann Projekte anlegen. Reviewer kann Listen lesen; weitergehende Freigaben erfolgen per API.

## API-Beispiel (zweite lokale Shell)

```sh
set -a; . ./.env; set +a
curl --fail http://127.0.0.1:8000/health
curl --fail http://127.0.0.1:8000/api/projects \
  -H "Authorization: Bearer $ATZE_OPERATOR_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"name":"Mein Projekt","description":"Manuell erfasst"}'
curl --fail http://127.0.0.1:8000/api/projects \
  -H "Authorization: Bearer $ATZE_OPERATOR_TOKEN"
```

`127.0.0.1` ist hier nur das Ziel eines lokalen CLI-Befehls, niemals ein Browser-Backend für die Remote-Vorschau. Browsercode verwendet relative URLs.

## Prüfung

```sh
python -m pytest --cov=app --cov-report=term-missing --junitxml=reports/junit.xml
python scripts/docs.py --check
python -m build
pip-audit -r requirements.lock
```

[Kompletter Ablauf als ausführbarer API-Smoke-Test](scripts/smoke.py): `python scripts/smoke.py --allow-fixtures`. Der Runner startet selbst eine temporäre TESTINSTANZ mit eigenen Tokens/Dateien und echten lokalen Komponenten; keine bestehende Instanz wird befüllt.

Stoppen: Ctrl+C. Daten bleiben unter `data/atze.db` erhalten. Fehlende Tokens verhindern den Start; keine unsichere Standardanmeldung.

## Context / Speicher ab v0.2
Ohne Zusatzkonfiguration nutzt der Server `data/objects` neben der Standarddatenbank. `ATZE_STORAGE_ROOT` kann einen anderen lokalen Pfad angeben. `ATZE_SD_ROOT` nur auf ein bereits provisioniertes, vertrauenswürdiges Verzeichnis setzen; der Server erkennt/mountet keine SD-Karte. Keine Remote-Credentials nötig. Die Oberfläche zeigt Storage Health und lokale Quellen-Suche.

`python scripts/smoke.py --allow-fixtures` startet ausschließlich eine **eigene temporäre Testinstanz** und prüft zusätzlich Archive, exakten Text-Readback, Memory-Inferenz, Quellen-Retrieval und Cache. Fremde Ziel-URLs werden nicht akzeptiert, geerbte Betriebsdatenpfade und Tokens nicht verwendet. Es importiert keine echten Motor-/Gerätedaten. [API-/Lifecycle-Verträge](docs/20-context-storage/contracts.md).

`ATZE_MODE` bleibt für die Arbeitsinstanz standardmäßig `operational`. Das ist keine Produktionsfreigabe. Der Smoke setzt seinen eigenen Modus ausdrücklich auf `test`. Datenbank/Dateiwurzeln erhalten dauerhafte Modusmarker; Testbestände dürfen nicht durch einen Moduswechsel produktiv gemacht werden. [Policy und Legacy-Grenzen](REALITY_POLICY.md).
