# Documentation Audit — 0.4.0.dev0 privacy-first partial integration

ADR-005 vor Implementierung; fehlende lokale Runtime/HF/MCP/Sandbox ausdrücklich erfasst. [Model Gateway](docs/02-core/model-gateway.md) beschreibt Purpose/Inputs/Outputs/Dependencies/Config/Permissions/Failures/Validation/Tests/Security/API-Workflow und Grenzen. Acht feste Umgebungsnamen plus dynamisch benannte ausschließlich providergebundene Secrets; OpenAPI/Inventar/Testkatalog synchron generiert. README, Betrieb, Ressourcen, UI, Policy, Threatmodel, Releasegates und Integrationsmatrix aktualisiert.

Nicht fälschlich behauptet: HF-Liveinferenz aus HTTP-Receipt, semantische Geheimnisfreiheit aus Regex, PrivateLink aus Mode-Label, OS-Isolation aus Python-Gateway, universeller Privacy Lock aus KI-Policyschalter, AgentRuntime aus bloßer Modellanfrage. Alle Modalitäts-Protokolle ausdrücklich Verträge, keine fertigen Provider.

Dokumentationsprüfung lokal PASS (vier generierte Produkte, OpenAPI, lokale Dateilinks, acht Envvariablen); semantische Vollständigkeit/Anker/externe Links nicht umfassend maschinell bewiesen. Ausgeführte Ergebnisse im [aktuellen Validierungsbericht](FINAL_VALIDATION_REPORT.md). Remote-CI für Implementierungsstand a915c659ebf4937b462ce30af9c0c52feb939e99: [34788948064](https://github.com/dingeldangbang/Atze-Plana-/actions/runs/34788948064) vollständig erfolgreich. Zusätzlicher real beobachteter SQLite-Thread-Handoff-Fehler korrigiert und dokumentiert: eigener sequenzieller Connection-Lifecycle mit zwei echten Threads/Commit/Rollback getestet; 117 Gesamttests, 40 parallele Preview-Reads. Korrigierter Code 50c4dfafbf826a0def5cbd9ebd05751244fc9781, [CI 34789132272](https://github.com/dingeldangbang/Atze-Plana-/actions/runs/34789132272) vollständig erfolgreich. Dokumentationsstand ergänzt beobachtete Nachweise, keine neuen Fähigkeiten.

---

## Historisches Dokumentationsaudit v0.3

# Documentation Audit — v0.3 Mandatory Challenge

Stand 2026-09-14. Ausgangspunkt `1094a8b`; keine bestehende Domainfunktion gelöscht. [Verbindliche Policy](REALITY_POLICY.md) und [vollständiges Realitäts-/Integrationsaudit](docs/17-security/reality-audit.md).

## Coverage
- Policy gilt für Agenten/Beiträge/CI/Runtime/Reports/Release. Synthetische Testeingaben und Fehler-Injektion sind ausdrücklich kein Hardware-/Dienstnachweis.
- Implemented, Configured, Tested, Validated und Production Ready getrennt für vorhandene Komponenten und fehlende Integrationen dokumentiert.
- Konfiguration umfasst jetzt sieben Environmentvariablen, inklusive separatem ATZE_CHALLENGE_TOKEN und ATZE_MODE mit DB-/Rootbindung. API-/Statusfelder und Runtime-Endpunkt in tatsächlicher OpenAPI generiert.
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
Vier generierte Produkte bytegenau synchron; formale OpenAPI-Gültigkeit, lokale Dateireferenzen, sieben Environmentvariablen und Test-Docstrings geprüft. `scripts/reality_check.py` prüft definierte Runtime-/Smoke-Grenzen. Tatsächliche Build-/Test-/HTTP-/GitHubresultate im [Validierungsbericht](FINAL_VALIDATION_REPORT.md); keine alten v0.2-Ergebnisse als aktuelle ausgegeben.

## Missing / Known Gaps
Kein vollständiger semantischer Beweis jeder Dokumentations-/Codeaussage, kein externer Link-/Ankercheck oder allgemeiner Commandparser. Keine Browser-E2E-/Hardware-/Provider-/APK-/Unity-/Payment-/Cloud-/Release-Nachweise. Kein automatisierter Multi-Tier-Vollrestore. Modusmarker können Datenwahrheit nicht beweisen; autorisierte Benutzer/Hostadministratoren bleiben Vertrauensgrenzen. Buildpakete sind echte Python-Artefakte, keine behaupteten APKs/Firmwareoutputs.

## Challenge-Abgleich
ADR-004 vor Implementierung; tatsächliche Result-/Worker-/Report-/Adoptverträge, alle fünf Prüfarten, 500-Quellen-/4-MiB-Grenze, Gate-/Stale-/Stop-/Lease-/Approvalmigration und Rollen dokumentiert. API/OpenAPI einschließlich blockierter direkter fact/decision-Erfassung aktualisiert. UI-/RAG-Doku trennt Primärfreitext, strukturierten Report-Scope und dynamische Decisiongültigkeit. Quickstart enthält separaten Worker ohne Primary-/Reviewer-Environment. Kein Same-Host-Prozess als Sandbox oder Source-Recherche ausgegeben. Aktuelle lokale/Remote-Nachweise im [Validierungsbericht](FINAL_VALIDATION_REPORT.md).

## Remote-Nachweis v0.3
Commit `7ef229fda30966d294fa2b038c6b29d97244d023`, [CI 34787960369](https://github.com/dingeldangbang/Atze-Plana-/actions/runs/34787960369) vollständig erfolgreich. Dokumentations-/OpenAPI-Prüfung und reale Test-/Build-/Smoke-Artefakte im Remote-Lauf. Kein Merge/Release/Produktionsdeploy.
