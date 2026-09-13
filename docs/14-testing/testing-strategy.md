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
