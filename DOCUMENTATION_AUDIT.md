# Documentation Audit — v0.2.1 No-Fake-Grenzen

Stand 2026-09-14. Ausgangspunkt `f4fedc0`; keine bestehende Domainfunktion gelöscht. [Verbindliche Policy](REALITY_POLICY.md) und [vollständiges Realitäts-/Integrationsaudit](docs/17-security/reality-audit.md).

## Coverage
- Policy gilt für Agenten/Beiträge/CI/Runtime/Reports/Release. Synthetische Testeingaben und Fehler-Injektion sind ausdrücklich kein Hardware-/Dienstnachweis.
- Implemented, Configured, Tested, Validated und Production Ready getrennt für vorhandene Komponenten und fehlende Integrationen dokumentiert.
- Konfiguration umfasst jetzt sechs Environmentvariablen, inklusive ATZE_MODE mit DB-/Rootbindung. API-/Statusfelder und Runtime-Endpunkt in tatsächlicher OpenAPI generiert.
- Alle Testdefinitionen im AST-Testkatalog; konkrete parametrische Outcomes ausschließlich aus ausgeführtem JUnit. Keine statische Pass-Tabelle als Ersatz für Testlauf.
- Build/Test/Reality/Smoke/Dependency-Prüfungen in CI. Smoke startet seine eigene temporäre echte Instanz und kann keine Betriebs-URL übernehmen.

## Corrected / Outdated
- README bezeichnet tatsächliche datenleere Arbeitsoberfläche nicht mehr als „ausführbare Demo“.
- Quickstart und CI enthalten keinen veralteten --base-url-Smoke-Aufruf mehr; Betreiber müssen keine Fixture-Instanz mit Betriebstokens vorbereiten.
- Storage-Dokumentation trennt unimplementierte, unkonfigurierte und nicht erreichbare Tiers; fehlende Werte nicht als künstliche Kapazität dargestellt.
- UI-Doku zeigt expliziten Test-/Betriebsmodus und die Behandlung alter Werte bei Ladefehlern.
- Ops-Doku erweitert um Sicherung/Restore versteckter Modusmarker und Legacy-Herkunftsprüfung. DB-only-Backup nicht als Vollbackup ausgegeben.
- Teststrategie ergänzt um ausdrücklich isolierte echte HTTP-Läufe, Reportfehlerzustände und begrenzte Bedeutung des Reality-Gates.
- Der Schema-only-Modus des Dokumentationsgenerators introspektiert Schnittstellen ohne Datenbankstart; er ist kein Fakeprovider und kein angebotener Runtime-Betriebsweg.

## Validation
Vier generierte Produkte bytegenau synchron; formale OpenAPI-Gültigkeit, lokale Dateireferenzen, sechs Environmentvariablen und Test-Docstrings geprüft. `scripts/reality_check.py` prüft definierte Runtime-/Smoke-Grenzen. Tatsächliche Build-/Test-/HTTP-/GitHubresultate im [Validierungsbericht](FINAL_VALIDATION_REPORT.md); keine alten v0.2-Ergebnisse als aktuelle ausgegeben.

## Missing / Known Gaps
Kein vollständiger semantischer Beweis jeder Dokumentations-/Codeaussage, kein externer Link-/Ankercheck oder allgemeiner Commandparser. Keine Browser-E2E-/Hardware-/Provider-/APK-/Unity-/Payment-/Cloud-/Release-Nachweise. Kein automatisierter Multi-Tier-Vollrestore. Modusmarker können Datenwahrheit nicht beweisen; autorisierte Benutzer/Hostadministratoren bleiben Vertrauensgrenzen. Buildpakete sind echte Python-Artefakte, keine behaupteten APKs/Firmwareoutputs.
