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

## v0.2 Context / Storage
| Problem | Symptom / mögliche Ursache | Diagnose / Evidence | Resolution / Eskalation |
|---|---|---|---|
| 507 No available tier | Local >=85%, SD >=90%, Reserve <16 MiB+Objekt oder Tier fehlt | Storage Health; konfigurierte Wurzeln/Mounts | Kapazität sicher bereitstellen; keine Archivlöschung erzwingen; Admin |
| 503 Storage integrity | Blob fehlt, Hash/Größe falsch, Symlink oder nicht regulär | Objekt-ID, erwarteter Hash, Audit; Originalkopien read-only prüfen | Schreibverkehr stoppen, geprüfte Retention-/Backupkopie manuell wiederherstellen; Admin/Security |
| SD nicht verfügbar | Root unkonfiguriert, fehlt, nicht zugreifbar | Health available=false; OS-Mountstatus | keine automatische Mount-/Formataktion; freigegebenen Tier herstellen |
| Cache 410 | Server-Expiry erreicht | expires_at/Status | verlorener Cache ist disposable; Taskinput erneut erzeugen, wichtige Originale vorher archivieren |
| Cache Cleanup teilweise fehlgeschlagen | Tombstone vorhanden, Blob noch da oder schon gelöscht | Cache/Audit und Fehlerzeit | Reviewer denselben begrenzten Cleanup wiederholen; Archive unberührt lassen |
| Suche ohne Treffer | anderes Projekt, Token-AND passt nicht, FTS leer | Query/Projekt/Original prüfen | andere Wörter; Reviewer-Reindex aus intakten Originalen; keine Wahrheit aus leerem Index ableiten |
| Suchtreffer, Original offline | lokaler FTS-Auszug noch da, aktiver Tier fehlt | location/Hash und content-503 | Original erst nach erfolgreicher Hashprüfung verwenden; nicht als live-validiert behandeln |
| fact 409 | keine oder unverified/rejected Evidence | Referenz-Reviewzustände | echte Evidenz prüfen; Hypothese als inference speichern, niemals Status künstlich hochsetzen |
| SQLite FTS5 fehlt | Start scheitert bei CREATE VIRTUAL TABLE | SQLite compile options / Pythonbuild | unterstützten SQLite-/Pythonbuild verwenden; kein stiller Such-Bypass |

## Challenge / Triage v0.3
| Symptom | Ursache / Diagnose | Behebung / Grenze |
|---|---|---|
| Task ohne Ergebnis BLOCK | Mandatory challenge not run | echtes Result Package erfassen; fehlende Primary-Runtime nicht durch Demo ersetzen |
| Worker NOT CONFIGURED | dritter Token fehlt | getrennten Token in API/Worker setzen, API neu starten; keine Operator-Credentials als Ersatz |
| Job bleibt pending | Prozess fehlt/unerreichbar | Workerlog/Netz/TLS prüfen, realen Prozess starten; kein UI-PASS erzeugen |
| Claim/complete 403 | falsche Rolle | separaten Worker-Token verwenden, keine Permission-Eskalation |
| Complete 409 | Lease expired, stale Result/Evidence/Stop oder Replay | gegebenenfalls Lease abwarten/neuer Claim bzw. explizite neue Challenge; alte Freigabe bleibt ungültig |
| Complete 422 | Report weicht von versionierten Regeln ab | API-/Worker-Codeversion angleichen, Inputs/Schema prüfen; Verdict nicht überschreiben |
| CONDITIONAL trotz verified Evidence | Maße/Identität/Bedingungen/Messung/Alternative/Kausalität fehlen | konkreten Findings mit Originalbelegen/Test nachgehen; Reviewer-Approval kann keine Lücke wegklicken |
| BLOCK bei Konflikt | identische deklarierte Identität/Bedingungen, abweichende Werte | Variante/Revision/Originalquelle klären, nicht bevorzugten Wert auswählen |
| Scope-/Finding-Limit BLOCK | vollständige Prüfung überschreitet Bounds | Projekt/Ergebnis fachlich sinnvoll aufteilen und vollständig neu prüfen; kein Teil-PASS |
| fact/decision Memory 409 | direkter Übernahmeweg gesperrt | aktuelles Result→Challenge→Triage→ggf. Approval→Reviewer Adopt; nur Inferenz manuell untrusted erfassen |
