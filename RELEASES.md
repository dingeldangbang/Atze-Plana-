# Release management

## 0.1.0 — vorbereiteter Entwicklungsschnitt, nicht veröffentlicht
Added/Changed/Fixed/Security/Breaking Changes/Migration/Validation: [Changelog](CHANGELOG.md).

Release-Gates: reproduzierbarer Build, Unit/Integration/API-Smoke, Dokumentationscheck, Dependency-Audit, grüner GitHub-Workflow, Review, Lizenzentscheidung. Produktionsrelease zusätzlich Browser-E2E, Lasttest, Backup-/Restore-Abnahme, betriebliches Security-Review und ausdrückliche menschliche Freigabe.

Kein Tag oder GitHub-Release wird als vollständig validierte Plattform veröffentlicht. Das aktuelle Paket kann intern geprüft werden. Offene Gates stehen im [Validierungsbericht](FINAL_VALIDATION_REPORT.md).

## Ablauf
Auf der bestehenden Session-Branch committen und pushen; PR zur Review bereitstellen. Nach Owner-Freigabe ist ein separat autorisierter Releaseprozess erforderlich. In dieser Session keine andere Branch erzeugen oder pushen. Kein automatischer Produktionsdeploy.

Rollback: Dienst stoppen, vorheriges freigegebenes Wheel und dazu passendes SQLite-Backup verwenden; Restore zuerst auf separatem Pfad testen. Keine generische Rückwärtskompatibilität für zukünftige Schemata versprechen.
