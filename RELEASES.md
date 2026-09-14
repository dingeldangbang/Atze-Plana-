# Release management

## 0.4.0.dev0 — Privacy-first foundation, RELEASE BLOCKED

Kein vollständiger HF-Agent-Layer. Text-Adapter/Policy/Context/Consent/Audit implementiert und gegen echte isolierte Transport-/TLS-Sockets geprüft; gepinntes HF-Modell tatsächlich in separater CI validiert, aber kein operatives MCP/smolagents/Full-OS-Sandbox-System. Kein universeller Egressbeweis, kein umfassender Secretclassifier oder verschlüsselter Cache. [Vertrag und Gates](docs/02-core/model-gateway.md). Die neue Datenschutzanforderung gilt als Releasebedingung, nicht als behaupteter Ist-Zustand.

## 0.3.0 — Mandatory Challenge, nicht veröffentlicht

[ADR-004](docs/adr/ADR-004-challenge-before-decision.md) gilt: Result → separater Worker → aktueller Report → Triage → Human Approval/Adoption. Pflichtgate ohne Bypass, einschließlich Legacy-/Stale-/Stopfälle. [Challenge-Scope](docs/02-core/challenge-worker.md) begrenzt alle ACCEPT-Aussagen auf eingereichte strukturierte Claims. Kein semantischer Primärtext-/Online-/Kausalitäts-/Executionnachweis. Zusätzliche Produktionsgates: Worker-/Secret-/OS-Isolation, Liveness-/Leasebetrieb, Last-/Retention-/Restoreabnahme und Browser-E2E. Kein Release allein wegen grüner Software-CI.

## 0.2.1 — Realitätsgrenzen, nicht veröffentlicht

[REALITY_POLICY](REALITY_POLICY.md) ist verbindliches Gate: keine Runtime-Mocks/Seeds/Fake-Fallbacks; getrennte Implemented/Configured/Tested/Validated/Production-Ready-Nachweise. Smoke nur in selbst erzeugter Testinstanz. Teststatus und Buildoutputs benötigen reale Lauf-/Artefaktnachweise. PR/CI ist kein GitHub-Release. Historischer Stand0.2.1: APK damals NOT VERIFIED. Aktueller echter Android-Debug-APK-/Emulatornachweis steht in APK_RELEASE_REPORT; Unity-/Firmwareoutputs weiterhin nicht vorhanden. Bestehende offenen Produktions-/Identitäts-/Restore-/Browser-Gates bleiben bestehen.

## 0.2.0 — vorbereiteter Context-/Storage-Schnitt, nicht veröffentlicht

[ADR-003](docs/adr/ADR-003-mobile-context-storage.md) und [Modulverträge](docs/20-context-storage/contracts.md) gelten. Neues Release-Gate: vollständiger konsistenter Multi-Tier-Backup-/Restore-Nachweis vor Produktion. Das SQLite-Backup allein genügt nicht. Mobile/SD-Hardware, MCP, Offline-Sync, Remoteadapter, Binärstreaming und Auto-Rebalancing fehlen. Added/Changed/Fixed/Security/Breaking/Migration im [Changelog](CHANGELOG.md). Aktuelle Gateergebnisse: [Validierungsbericht](FINAL_VALIDATION_REPORT.md).

## 0.1.0 — vorbereiteter Entwicklungsschnitt, nicht veröffentlicht
Added/Changed/Fixed/Security/Breaking Changes/Migration/Validation: [Changelog](CHANGELOG.md).

Release-Gates: reproduzierbarer Build, Unit/Integration/API-Smoke, Dokumentationscheck, Dependency-Audit, grüner GitHub-Workflow, Review, Lizenzentscheidung. Produktionsrelease zusätzlich Browser-E2E, Lasttest, Backup-/Restore-Abnahme, betriebliches Security-Review und ausdrückliche menschliche Freigabe.

Kein Tag oder GitHub-Release wird als vollständig validierte Plattform veröffentlicht. Das aktuelle Paket kann intern geprüft werden. Offene Gates stehen im [Validierungsbericht](FINAL_VALIDATION_REPORT.md).

## Ablauf
Auf der bestehenden Session-Branch committen und pushen; PR zur Review bereitstellen. Nach Owner-Freigabe ist ein separat autorisierter Releaseprozess erforderlich. In dieser Session keine andere Branch erzeugen oder pushen. Kein automatischer Produktionsdeploy.

Rollback: Dienst stoppen, vorheriges freigegebenes Wheel und dazu passendes SQLite-Backup verwenden; Restore zuerst auf separatem Pfad testen. Keine generische Rückwärtskompatibilität für zukünftige Schemata versprechen.

## PLAN upgrade / rollback
Policy `challenge-2-context` verlangt neue Gegenprüfungen. Alle alten Core/Worker stoppen; kein gemischter Versionsbetrieb oder Rückgriff auf alte Binaries mit post-PLAN-Daten. Ältere Software kennt Context Lock nicht. Kein datenbewahrender automatischer Downgrade zugesagt. [Vertrag](docs/21-plan/context-lock.md).
