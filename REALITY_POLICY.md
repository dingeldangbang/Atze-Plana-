# Verbindliche Realitäts- und Nachweispolicy

Gilt für alle Beiträge, Agenten, APIs, UI, Dokumentation und Releases. Ein kleiner realer Umfang hat Vorrang vor einer simulierten Vollplattform. Keine Mocks, Seeds, Demo-Templates, Fake-Provider, fingierten Messwerte oder vorgegebenen Erfolgsergebnisse im Betriebsweg. Ein Fehler darf nie unbemerkt durch Testdaten ersetzt werden.

## Verbindlicher Prozess
Realer Input → realer Prozess → realer Output → ausgeführter Test → belegte Evidence → Triage → dokumentierter Status. Preflight-Triage und Permissions bleiben zusätzlich VOR jeder späteren externen Execution erforderlich. Retrieval, Memory, Template und Device Profile sind weder Wahrheit noch Freigabe noch reale Hardware.

## Testgrenze
- Synthetische Eingaben sind ausschließlich klar gekennzeichnete Inputs automatisierter Tests/CI in getrennten temporären Instanzen. Die Verarbeitung (HTTP, SQLite, FTS, Dateien, Hash) ist real.
- Fehler-Injektion testet reproduzierbar nicht zuverlässig verfügbare Fehlerfälle; sie liegt unter `tests/`, niemals im Runtime-Providerpfad.
- Eine Hardware-/Dienstsimulation wäre nur bei objektiv fehlender Anbindung, dokumentierter Begründung, außerhalb des Betriebswegs und expliziter Aktivierung erlaubt. Es gibt derzeit keinen solchen Runtime-Testprovider.
- `ATZE_MODE=test` kennzeichnet eine Testinstanz, schaltet aber KEINEN Fake-Backend ein. Standard `operational` ist kein Production-Ready-Zertifikat.
- Der mitgelieferte Smoke-Runner darf keine fremde URL, Betriebs-DB, Speicherwurzel oder Betriebstokens übernehmen. Er startet und entfernt seine eigene lokale Testinstanz. Keine manuelle Fixturebefüllung der Produktvorschau.
- Persistente Modusmarker verhindern das bloße Umschalten einer Test-DB/Objektwurzel auf operational. Legacy-Daten ohne Marker sind nicht automatisch als echte Beobachtungen beweisbar; Betreiber müssen Herkunft prüfen.

## Sichtbare Zustände
`BLOCKED` bei fehlender Implementierung, `NOT CONFIGURED` bei vorhandenem aber unkonfiguriertem Adapter, `UNAVAILABLE` bei konfigurierter nicht erreichbarer Ressource. Fehlende Werte bleiben null/unbekannt, nicht 0% oder Beispielsensorik. Bei UI-Ladefehlern keine alten Werte als aktuelle Messung zeigen.

Für Geräte künftig getrennt: REAL DEVICE (tatsächlich erkannt), DEVICE PROFILE (Beschreibung), UNKNOWN DEVICE (nicht zugeordnet), SIMULATED DEVICE (nur expliziter Test). Eine konfigurierte SD-Dateiwurzel ist FILESYSTEM PATH, kein Nachweis einer SD-Karte. Nicht existierende Module erhalten keine funktionslosen Verbindungsbuttons.

## Nachweisachsen pro Integration
Implemented, Configured, Tested, Validated und Production Ready separat dokumentieren. Ein geschriebener Adapter ohne Live-Test bleibt CONDITIONAL/NOT VALIDATED; fehlender Adapter bleibt NOT IMPLEMENTED/BLOCKED. Statusseiten sind keine Adapter. Reale lokale Git/GitHub-Operationen des Entwicklungsagenten sind keine Runtime-GitHub-Integration der Plattform.

## Builds / Tests / APK / Release
PASS nur nach tatsächlicher Ausführung, andernfalls NOT RUN/BLOCKED. Erwartungen sind keine Ist-Ergebnisse. Reports binden Laufzeit, geprüfte Schritte und Fehler; ein fehlgeschlagener neuer Lauf darf keinen alten PASS-Report unverändert hinterlassen.

Ein APK ist erst VERIFIED, wenn echter Build, existierende Datei, Signaturprüfung, Hash und Installationsprüfung nachgewiesen sind. Aktuell: APK NOT VERIFIED, keine Androidintegration. Ein GitHub-Release braucht realen Commit/Push, Remoteprüfung sowie Release-/Artefaktprüfung; grüner PR ist kein Release. Payment nur über realen Provider, optional dessen offiziell dokumentierte Testumgebung; kein lokales „payment succeeded“. Bright Data nur nach tatsächlicher Providerantwort; Cloudressourcen nur mit tatsächlicher Providerverbindung.

Release als fertig bezeichneter Funktionen nur mit Implementation + realem Test + Validation + synchroner Dokumentation. Fehlende Bestandteile blockieren die Freigabe. Kein Produktionsdeploy oder invasive Aktion ohne ausdrückliche Autorisierung.

## Technische und organisatorische Grenzen
Die Policyprüfung ist eine überprüfbare Teilkontrolle, kein semantischer Beweis jedes Codes. Ein autorisierter Mensch kann weiterhin falschen Text einreichen; kein Schlagwortfilter kann Wahrheit beweisen. Review, Provenance, Hostzugriff und kontrollierter Datenimport bleiben nötig. Testdaten werden nicht aus bestehenden DBs gelöscht oder als real umetikettiert. Vorhandene Daten und Geräte werden nicht für diese Prüfung manipuliert.

## Verbindliche Challenge-Regel v0.3
Every Decision Must Survive Challenge. Kein Primärergebnis direkt in Approval/autoritative Memory übernehmen. Aktuelles Result Package → separater Challenge-Prozess → verifizierter Report → Triage → erforderliche Human Approval → explizite Adoption. Keine Test-/UI-/Configoption zum Überspringen. CONDITIONAL/BLOCK stoppt. Bei Staleness neu prüfen, alte Freigaben nicht wiederverwenden. Primärfreitext nicht durch einen begrenzten strukturierten PASS als wahr ausgeben. [Vertrag](docs/02-core/challenge-worker.md).
