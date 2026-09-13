# Troubleshooting / Fehlerdatenbank

| Problem / Symptom | Mögliche Ursachen | Diagnose / Evidence | Behebung | Eskalation |
|---|---|---|---|---|
| Startfehler Token | leer, zu kurz, identisch; .env nicht geladen | Exception ohne Tokenwerte; config prüfen | zwei zufällige Werte, set -a; . ./.env; set +a | Administrator; keine Secrets mitsenden |
| API 401 | falscher/alter Token | Statuscode, Zeitpunkt, Route ohne Header protokollieren | richtigen Rollen-Token laden, nach Rotation neu verbinden | Administrator |
| API 403 | falsche Rolle | Route und Rollenmatrix | keine Rechte umgehen; Reviewer/Operator korrekt zuordnen | Verantwortlicher Reviewer |
| API 422 | ungültige URL/Zeit/Länge/Referenz | detail im Response; Schema vergleichen | Eingabe korrigieren, keine fremden Projekt-IDs | Entwicklung mit anonymisiertem Payload |
| Task blocked | unverified/rejected, niedrige Confidence, fehlende Preconditions oder Stop | reasons aus POST triage, Evidence-IDs | echte Voraussetzungen herstellen / neuen korrekten Datensatz erfassen; niemals Confidence erfinden | Reviewer |
| Approval 409 | blockiert, bereits approved oder READ eligible | aktuelle Triage und Audit | keinen doppelten Approval erzwingen | Reviewer |
| Database unavailable / 503 | Locktimeout, voller Disk, Rechte, beschädigte DB | Disk/Rechte prüfen, Integritätscheck auf Kopie, Zeitpunkt/Route | einen Prozess, lokalen Pfad; Backup/Recovery | Administrator; Daten erhalten |
| Dashboard leer | nicht verbunden, keine Daten, API-Fehler | status-Anzeige und Browser-Netzwerk ohne Tokenexport | mit Token verbinden; Operator legt Projekt an | Entwicklung |
| Dokumentationscheck fehlgeschlagen | generierte Drift, Linkziel fehlt, Environment-Lücke | konkrete Worker-Fehlermeldung | Quelle und Handbuch korrigieren, scripts/docs.py, erneut --check | Reviewer |
| Dependency-Audit fehlgeschlagen | Advisory oder Registry nicht erreichbar | Report und Exitcode unterscheiden | Abhängigkeiten aktualisieren oder Netzwerkfehler klären; nicht skippen | Security-Verantwortlicher |
| Build fehlgeschlagen | Packaging/Registry/Python | vollständiges redigiertes Buildlog | locked Umgebung und Paketdateien prüfen | Entwicklung |

## Noch nicht implementierte Integrationen
ESP32 nicht erkannt, ADB device offline, Fastboot nicht erreichbar, EDL device nicht erkannt, Unity-/Android-Build failed, Bright Data request failed, Worker timeout, WebSocket disconnected und Sandbox failed können **nicht von diesem Kern diagnostiziert oder repariert werden**. Es gibt dafür keinen Adapter, Build oder Worker.

Symptom in einem externen System: Hersteller-/SDK-Logs mit Zustimmung sichern, Hardware-/SDK-Version und autorisierten Kontext erfassen, zuständiges Team eskalieren. Keine Flash-/EDL-/Netzwerkscanbefehle als vermeintliche Reparatur durchführen. Ein passendes Runbook kann erst nach Integration und realem Test entstehen.
