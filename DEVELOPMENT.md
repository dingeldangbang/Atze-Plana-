# Development

1. [Quickstart](QUICKSTART.md) installieren; nur die Session-Branch bearbeiten.
2. Design und Grenzen vor oder mit dem Code dokumentieren; bedeutende Entscheidung als ADR.
3. Neue Pydantic-Felder und Endpunkte in `app/` implementieren, Rechte und Fehlerfälle testen.
4. Jede `test_*`-Funktion bekommt eine Test-ID und einen erwartetes Verhalten beschreibenden Docstring.
5. `python scripts/docs.py --history` generiert OpenAPI, API-Referenz, Testkatalog und Code-Inventar. Historie ist Entwurfsinput, kein Funktionsnachweis.
6. `python scripts/docs.py --check`, `python -m pytest --cov=app --cov-fail-under=90 --junitxml=reports/junit.xml`, `python -m build`, `pip-audit -r requirements.lock` ausführen.
7. [Dokumentationsaudit](DOCUMENTATION_AUDIT.md) und [Validierungsbericht](FINAL_VALIDATION_REPORT.md) mit echten Ergebnissen aktualisieren.
8. Commit und PR; CI muss dieselben Gates prüfen. Kein Produktionsdeploy in CI.

## Konventionen
- SQL parametrisieren; Zustandsänderung und Audit atomar schreiben.
- Fehlende Funktion als NOT IMPLEMENTED kennzeichnen; keine Fake-Ergebnisse.
- Keine generischen Tool-, Shell- oder Geräte-Executors hinzufügen, ohne Isolation, konkrete Policy und Negativtests.
- Testfixtures sind synthetisch; niemals als echte Geräte-/Quellenevidenz ausgeben.
- Code liegt in `app/`, Tests in `tests/`, Werkzeuge in `scripts/`.

## Bekannte Einschränkungen
Kein Typechecker/Linter-Gate, keine Browserautomatisierung, kein Lasttest. Transitive Bibliotheken können Deprecation-Warnungen ausgeben; diese werden nicht ausgeblendet. Änderungen an generierter API-Referenz gehören in Quelle oder Worker, nicht nur ins Ausgabe-Markdown.
