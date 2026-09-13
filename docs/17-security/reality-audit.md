# Realitätsaudit und Integrationsstatus — v0.2.1

Stand 2026-09-14, Ausgangscommit `f4fedc0`. Verbindliche [Reality Policy](../../REALITY_POLICY.md). Dieser Statusbericht ist **kein Provideradapter**, keine automatische Live-Zertifizierung und kein erfundener Integrationstest.

## Prüfung vor Änderung
- Runtime `app/` nutzte reale SQLite-/FTS-/POSIX-Dateioperationen und keine Mock-/Fake-Provider. Neue Instanzen starteten ohne automatisch angelegte Projekt-/Messdaten.
- Nicht implementierte Geräte/Cloud/MCP/Payment-Module besaßen keine Fake-Verbindungsbuttons oder statischen Erfolgspfade.
- Synthetische Inputs und Fehler-Injektionen lagen in Tests und im separat aufgerufenen HTTP-Smoke. **Lücke:** Smoke akzeptierte eine beliebige Ziel-URL mit Aufrufer-Tokens; reines CLI-Opt-in war keine ausreichende technische Trennung.
- Storage Health verband fehlenden Adapter, fehlende Konfiguration und Ausfall in einer Sammelmeldung. UI konnte nach einem fehlgeschlagenen Refresh alte Messwerte stehen lassen.
- README nannte die echte, datenleere Arbeitsoberfläche missverständlich „Demo“. Das wurde korrigiert; keine Funktion entfernt.

## Technisch verschärft
1. `ATZE_MODE=operational|test`; SQLite-Tabelle `instance_mode` und `.atze-mode` in tatsächlichen Dateiablagen binden den Modus. Cross-Mode-Zugriff wird verweigert. Kein Testmodus aktiviert Mocks: dieselben echten lokalen Komponenten.
2. Smoke nimmt keine Ziel-URL entgegen, startet einen eigenen realen Childprozess auf Loopback mit temporärer DB/Objektwurzel und neuen Tokens. Geerbte ATZE-Konfiguration wird verworfen, HTTP-Proxies deaktiviert. Vor Fixtures prüft er öffentlichen UND authentifizierten Testmodus. Er beendet den Childprozess und entfernt temporäre Daten.
3. Prüfungen im Smoke sind echte Kontrollflüsse, keine mit `python -O` entfernbaren Assertions. Reports starten NOT_RUN/RUNNING und enden abhängig von Ausführung PASS/FAIL; fehlendes Opt-in BLOCKED. Ausführungsfehler überschreiben vorherige PASS-Reports. Syntaxfehler bei CLI-Argumenten starten keinen Test und erzeugen keinen neuen Testnachweis.
4. Storage meldet Implemented/Configured sowie AVAILABLE, NOT_CONFIGURED, UNAVAILABLE oder BLOCKED getrennt. Unerreichbare und nicht messbare Kapazität liefert null-Werte. Automatische Erstplatzierung auf einen anderen tatsächlich verfügbaren lokalen Datenträger ist ein echter Storage-Policyweg, **kein Fake-Fallback**.
5. UI kennzeichnet TESTINSTANZ nach authentifizierter Abfrage, verwirft veraltete Workspacewerte bei Ladefehlern und zeigt keine Ersatzdaten. Nicht implementierte Module bleiben ohne Scheinbedienelemente.
6. CI prüft verbotene Test-/Mock-Imports im Runtimebaum, fehlende Policy und entfernbare Smoke-Assertions/Target-URL. Diese AST-Prüfung ist eng begrenzt, kein allgemeiner semantischer Fake-Detektor.

## Getrennte Nachweisachsen
„lokale Tests“ bezeichnet tatsächlich ausgeführte Softwaretests mit gekennzeichneten Eingaben, niemals Hardware-/Provider-Livevalidierung. Die Konfiguration einer anderen Instanz ist unbekannt.

| Integration / Funktion | Implemented | Configured | Tested | Validated | Production Ready |
|---|---|---|---|---|---|
| SQLite / FTS / Core APIs | YES | je Instanz lokaler Pfad | lokale echte DB/HTTP-Tests | begrenzter Kern, siehe Laufreport | NO — Betriebs-/Security-Gates |
| Archive / Memory / Cache | YES, begrenzte Texte | je Instanz echte Wurzeln | reale Dateien/Hash/Fehlerfälle | lokal begrenzt | NO — Gesamtbackup/Last/Identity |
| Storage Local | YES | Standardroot oder explizit | reale Dateisystemmessung | Messung nur für aktuelle Instanz | NO — keine allgemeine Hostabnahme |
| Storage SD-Pfad | YES als Dateisystemadapter | optional; sonst NOT_CONFIGURED | zweites temporäres Testverzeichnis | KEIN SD-Hardware-/Hotplugnachweis | NO |
| RAM-/Server-/Cloud-Storage | NO | keine Adapterkonfiguration | NOT RUN | BLOCKED | NO |
| Dashboard | YES, echte API-Daten/Empty States | vorhandene Server-URL | HTTP/Syntax; Browser-E2E NOT RUN | CONDITIONAL | NO |
| Runtime GitHub-Connector | NO | NOT CONFIGURED | NOT RUN | BLOCKED | NO |
| Entwicklungsagent: Git/GitHub | reale git/gh-Werkzeuge genutzt | Repositoryzugriff vorhanden | Commit/Push/PR/CI tatsächlich ausgeführt | nur verlinkte konkrete Operationen | kein Runtimefeature / kein Release |
| USB Discovery | NO | NOT CONFIGURED | NOT RUN | BLOCKED | NO |
| WiFi-Geräte / BLE / Serial | NO | NOT CONFIGURED | NOT RUN | BLOCKED | NO |
| ESP32 / Telemetrie | NO | NOT CONFIGURED | NOT RUN | BLOCKED; keine Live-Messwerte | NO |
| Android / Honeywell | NO | NOT CONFIGURED | NOT RUN | BLOCKED; APK NOT VERIFIED | NO |
| ADB / Fastboot / EDL / Repair | NO | NOT CONFIGURED | NOT RUN | BLOCKED | NO |
| Unity / 3D Build | NO | NOT CONFIGURED | NOT RUN | BLOCKED; kein Buildartefakt | NO |
| Bright Data / externe Recherche | NO | NOT CONFIGURED | NOT RUN | BLOCKED; keine Providerantwort | NO |
| Cloud-Provisioning / Netzwerkprovider | NO | NOT CONFIGURED | NOT RUN | BLOCKED | NO |
| Payment | NO | NOT CONFIGURED | NOT RUN | BLOCKED; kein offizieller Provider-Sandboxtest | NO |
| MCP / Primary Agent Builder / Runtime | NO | NOT CONFIGURED | NOT RUN | BLOCKED; REST ist nicht MCP | NO |
| Isolierter Execution-Sandbox | NO | NOT CONFIGURED | NOT RUN | BLOCKED; Textcache ist keine Isolation | NO |
| Trend Engine / Offline Sync | NO | NOT CONFIGURED | NOT RUN | BLOCKED | NO |

## Test- und Simulationsinventar
- `tests/conftest.py`: expliziter test-Modus, synthetische Projekt-/Quellentexte, echte temporäre SQLite-Dateien.
- `tests/test_context_storage.py`: reale temporäre Dateiwurzeln. Das bisher „simulated SD“ benannte Verzeichnis testet **Dateiablage**, nicht SD-Gerätekommunikation. Reale SD-Hardware fehlt; kein solcher Provider wird in den Betriebsweg injiziert.
- pytest monkeypatch/Fehlertrigger: nur reproduzierbare Fehlersituationen (Korruption/Transaktions-/Disk-/Harnessfehler), kein Runtime-Fallback. Expected Assertions sind Erwartungen; Actual Results stehen im echten JUnit-Lauf.
- `scripts/smoke.py`: synthetische Inputs über echten HTTP-Server; jetzt selbst erzeugte temporäre TESTINSTANZ, kein Ersatzprovider. Nicht ins App-Wheel als Runtime-Tool eingebunden.
- Keine verfügbaren Demo-Apps, Providerstubs, Payment-Simulatoren, fingierten APKs oder Firmwareoutputs im Produktbaum.

## Grenzen / Legacy / Release-Gate
Software kann nicht feststellen, ob beliebiger manuell eingereichter Text wahr ist. Modusmarker sind keine kryptografische Herkunftssignatur und kein Schutz gegen Hostadministratoren, die Marker löschen. Bestehende unmarkierte Daten werden nicht gelöscht oder als „REAL“ zertifiziert; bekannte alte Smoke-Bestände bleiben Testdaten und dürfen nicht in operational importiert werden. Keine automatischen Datenimporte.

Ausgeführte Prüfungen: [Testkatalog](../14-testing/test-catalog.md), [aktueller Validierungsbericht](../../FINAL_VALIDATION_REPORT.md). Eine grüne CI belegt nur ihre tatsächlich ausgeführten Gates, nicht alle Zielintegrationen. Keine Hardware-/Cloud-/APK-/Releaseerfolge aus diesen Softwaretests ableiten. Kein Produktionsrelease ohne die offenen Betriebs-/Security-/Restore-/UI-Gates und explizite Freigabe.

## Erweiterung v0.3 — separat zu bewerten
Die oben genannten fehlenden Primary-Agent-/MCP-/Provider-/Hardwareintegrationen bleiben fehlend. Neu real implementiert ist ein spezialisierter **Challenge-Prüfprozess**, kein allgemeiner Agent Builder oder Execution-Worker.

| Funktion | Implemented | Configured | Tested | Validated | Production Ready |
|---|---|---|---|---|---|
| Result/Challenge/Adopt-Gate | YES, strukturiert begrenzt | API + eigener Servicetoken | echte API-/Regel-/SQLite-Tests | Scope laut Report, siehe aktuellen Validationreport | NO |
| Separater Challenge Worker | YES, eigenes Python-Programm | eigener Prozess erforderlich; Token allein beweist keine Liveness | tatsächlich zwei Prozesse im isolierten HTTP-Smoke | lokale eingereichte Evidenz, keine unabhängige Online-Recherche | NO — OS-/Secret-/Betriebsabnahme |
| Semantische/Online-/Kausalitäts-Gegenprüfung | NO | kein Provider/Experimentvertrag | NOT RUN | BLOCKED/CONDITIONAL | NO |

Kein statisches „Bist du sicher?“ ersetzt Gegenprüfung. Reportresultate stammen aus realen Regeln und Snapshotdaten. Ungeprüfter Primärfreitext wird nicht als Fakt adoptiert. Fehlende Quellen/Alternativen bleiben UNKNOWN, keine Motor-/Sensorbeispiele in der Produktinstanz.
