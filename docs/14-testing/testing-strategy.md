# Teststrategie

## Gates
- Unit: reine Triage mit fehlender/abgelehnter Evidenz und Grenzwert.
- Integration: echte temporäre SQLite-Datei über FastAPI TestClient; Rollen, Herkunft, Referenzen, Approval, Stop/Restart und transaktioneller Audit-Rollback.
- API-E2E-Smoke: `scripts/smoke.py` gegen einen separat gestarteten echten HTTP-Prozess; keine Mocks für HTTP/DB. Dies ist **kein Browser-E2E**.
- Dokumentation: generierte Drift, OpenAPI-Validator, lokale Datei-Links, Config-/Environment-Abdeckung, Test-Docstrings und tatsächliche Beispielausführung im Smoke.
- Build: Wheel/sdist; keine Unity-/Android-Builds.
- Security: Negativtests plus `pip-audit`; kein Penetrationstest.

## Reproduktion / Evidence
[Development](../../DEVELOPMENT.md) enthält Befehle. `pytest --junitxml=reports/junit.xml` erfasst einzelne parametrische Testfälle, Ergebnisse, Laufzeiten und Fehler. `--cov=app --cov-report=xml:reports/coverage.xml` misst Python-Zeilenabdeckung, nicht Frontend-/Requirements-Abdeckung. Gates: >=90% Python-Statements; keine Test-Bypässe oder ausgeblendete Failures. CI lädt Reports auch bei Fehlern hoch.

[Testkatalog](test-catalog.md) referenziert für jeden Test ID, Zweck, Preconditions/Fixtures, Aktionen und erwartete Assertions. Tatsächlicher Status ist nur aus einem Laufreport ableitbar; der Generator behauptet keine erfolgreichen Tests.

## Offene Nachweise
Browser-E2E (Login/Logout, UI-Fehler, Rendering, Accessibility), Device-/Agent-/Sandboxtests, Last-/Concurrency-Stresstest, unabhängiger Pentest, Wiederherstellung unter Produktionsbedingungen und plattformübergreifender Build sind NOT IMPLEMENTED bzw. BLOCKED. Temp-DB-Tests sind keine Sandbox-Isolation. Synthetische Daten sind nur Testinputs.

## v0.2 Regressionen
Zusätzliche echte temporäre Dateisystemtests für Originalbytes/Hash, stabile Pfadauflösung nach Relocation, Source Retention, Copy-/Auditfehler, Symlink-/Traversalschutz, Kapazitätsfallback, Stop, Cache-Expiry/Retry, Memory fact/inference, Live-Evidence, Projektfilter, Reindex und additive Migration. Simuliertes SD-Verzeichnis ist keine SD-Hardwarevalidierung. HTTP-Smoke wurde um Archive/Memory/FTS/Cache/Health erweitert. Multi-Tier-Gesamtbackup, mobile Hardware, MCP, Remote-Sync und Browser-E2E sind weiterhin offene Nachweise.

## v0.2.1 — explizite Realitätsschranke
`python scripts/smoke.py --allow-fixtures` startet einen echten HTTP-Childprozess mit eigenen temporären Dateien, Modus test und frischen Tokens. Kein `--base-url` mehr, keine Übernahme von ATZE-Umgebungswerten, kein Mockprovider. Normale pytest-Fixtures wählen test ausdrücklich. Eingaben und reproduzierbare Fehler-Injektion liegen nur im Testwerkzeug, nie im App-Providerpfad. Reports enthalten wirkliche Statuscodes und enden nur nach vollständigem Lauf mit PASS; Opt-out/Fehler ersetzen alte Erfolge durch BLOCKED/FAIL.

REAL-001..015 prüfen Empty Start, Mode-/Legacy-/Root-Grenzen, tatsächlichen Rootausfall, unbekannte Kapazität, explizites Opt-in, ausfallsichere Reportzustände und reale Childprozess-Isolation. `scripts/reality_check.py` prüft zusätzlich enge AST-Grenzen. Keine davon beweist reale SD-/Cloud-/MCP-Hardware, Browserbedienung oder semantische Wahrheit beliebiger Benutzertexte.
