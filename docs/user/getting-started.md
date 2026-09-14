# Benutzerhandbuch

## Getting started / Dashboard
Öffne die Instanz-URL. Du siehst Projektanlage, Sicherheitszustand sowie Listen für Projekte, Evidence und Aufgaben. Vor Anmeldung sind keine Workspace-Daten geladen. Gib einen vom Administrator separat erhaltenen Operator- oder Reviewer-Token ein. Er bleibt nur im Speicher des Tabs; bei Reload erneut anmelden. „Trennen“ leert Token und Anzeige. Die App enthält keine Demo-Messwerte.

## Projekte
Als Operator Name und optional Beschreibung eintragen und speichern. Gespeichert werden UUID, Erfassungszeit und Audit-Ereignis. Kein zusätzliches Approval erforderlich: das ist Metadatenpflege, keine externe WRITE-Aktion. Reviewer kann Projekte sehen, nicht anlegen. Listen zeigen maximal die ersten 100 Einträge; weitere Seiten nur via API.

## Evidence / Context
Oberfläche zeigt Claims, Reviewzustände und gemeldete Confidence. Erfassung und Review derzeit über [API](../08-network/APIs.md). Originaltext, Quellenmetadaten und Hash bleiben in SQLite. Reviewer prüft mit Grund genau einmal. Keine automatische Wahrheitserkennung, kein Binärupload oder Kontexteditor. v0.2 Archivtexte/Memory können über die API erfasst und über die neue Kontextsuche gefunden werden.

## Aufgaben / Triage
Aufgaben werden per API angelegt. „Triage prüfen“ berechnet die aktuellen Blocks/Freigaberegeln und speichert einen Entscheidungssnapshot im Audit. reasons erklären fehlende Voraussetzungen. Kein automatisches Auflösen eines Blocks. Nicht-lesende Aktionen benötigen separate Reviewer-Freigabe per API. Auch approved führt nichts aus.

## Administration / Safety
Reviewer liest Audit und ändert globalen Stop per API. Stop blockiert Triage, nicht Projekterfassung oder externe Geräte. Keine Benutzer-/Rollenverwaltung in der UI. Niemals Secrets oder nicht autorisierte personenbezogene Daten als Evidence speichern.

## Noch nicht verfügbare Benutzerbereiche
Plan, umfassender Datei-/Context-Editor, Devices, Network, Telemetry, 3D World, Agents, Sandbox, Tests als UI-Modul, Repair, Trends sind NOT IMPLEMENTED. Der taskgebundene Textcache ist kein isolierter Sandbox-Executor. Es gibt dafür keine versteckten Menüs, Befehle, Geräte oder gespeicherten Ergebnisse. Testreports entstehen nur über Entwicklungs-/CI-Werkzeuge. [Roadmap](../00-overview/roadmap.md).

## Neu: Speicher und Projektkontext
Nach Anmeldung zeigt „Speicher & Cache“ aktuelle Messwerte nur für erreichbare konfigurierte Wurzeln. Nicht implementierte oder fehlende Tiers bleiben ausdrücklich unbekannt. Archivbytes sind logische Originalgrößen, nicht Gesamtbelegung mit Index/Retained Copies.

Wähle unter „Projektkontext durchsuchen“ ein Projekt und Suchwörter. Treffer stammen aus erfassten Archivtexten/Memory, mit Pfad, Speicherort, Hash, Zeichenposition und Evidence-Zustand. Es wird keine KI-Antwort formuliert. Der Evidence-Zustand ist der Zustand verknüpfter Quellen, kein automatischer Wahrheitsnachweis des Auszugs. Keine Freigabe wird durch Suche erteilt.

Archive und Memory werden zunächst über die dokumentierte API erfasst. Archive sind unveränderlich; gleicher Pfad lässt sich nicht überschreiben. Memory-Inferenzen bleiben Inferenzen. Cache kann nach TTL verloren gehen; wichtige Texte vorher explizit als Archiv sichern. Reviewer steuert Speicherwechsel/Cleanup; ein Wechsel behält die alte Archivkopie. Technische Verträge: [Context/Storage](../20-context-storage/contracts.md).

## v0.2.1 — Betriebs-/Testzustand und fehlende Daten
Nach erfolgreicher Anmeldung erscheint der tatsächliche Modus: TESTINSTANZ (Testeingaben, keine Live-Evidence) oder BETRIEBSINSTANZ (keine Seeds, trotzdem keine Produktionsfreigabe). Vor bestätigter Antwort bleibt der Modus unbekannt. Bei Refreshfehlern werden bisherige Werte verworfen, statt sie als aktuelle Messungen anzuzeigen; keine automatische Beispieldatenbefüllung.

Storage unterscheidet BLOCKED (Adapter fehlt), NOT_CONFIGURED (Dateipfad nicht eingerichtet), UNAVAILABLE (eingerichteter Pfad nicht erreichbar/messbar) und AVAILABLE (reale Dateisystemmessung). „SD“ bleibt eine Pfadklasse, kein erkanntes Gerät. Nicht existierende Sensor-/Cloud-/Repair-/Buildmodule zeigen keine erfundenen Ressourcen oder Ergebnisse und besitzen keine Schein-Verbindungsbuttons.

## Ergebnisse / Warum? / Herausfordern / Quellen
Ab v0.3 sind Taskfreigaben ohne aktuelles Result Package und Challenge-Pass blockiert. Primärpakete werden derzeit über die API erfasst; kein Agent generiert sie automatisch. Die Ergebnisliste zeigt ausdrücklich eingereichte Herkunft und keine ungeprüfte Empfehlung als Fakt.

„Warum?“ liest einen aktuellen Entscheidungssnapshot mit ACCEPT/CONDITIONAL/BLOCK, Jobzustand, fünf Prüfarten, Lücken, konkreten nächsten Validierungen und belegten Gegenkandidaten. Historische Reports werden nicht als aktuelle Freigabe dargestellt. „Quellen“ lädt erfasste Evidence inklusive URL/Hash/Originaltext (bis 30 Referenzen in der UI). „Herausfordern“ verlangt einen Grund und erzeugt einen echten pending Job — der vorige Pass/Approval wird damit entwertet. Ohne laufenden Worker bleibt er ausstehend.

CONDITIONAL/BLOCK heißt keine Übernahme. ACCEPT betrifft ausschließlich die strukturierten Claims, nicht automatisch den Primärfreitext. Reviewer-Adoption erfolgt über die API und speichert einen überprüfbaren Decision-Verweis, nicht die ungeprüfte Zusammenfassung. RAG zeigt auch für Decision-Memory den aktuellen Challenge-Status; bei verändertem Kontext wird er BLOCK. Es findet keine Geräte-/Cloud-/Zahlungs-/Terminalaktion statt.

## KI-Datenschutz
Die neue Anzeige lädt tatsächliche Policy und konfigurierte Provider; keine Beispielmodelle. „KI auf Local-only sperren“ erfordert Reviewer und setzt Default DENY samt leeren Allowlists; macht vorbereitete Anfragen stale. Dies ist nur die KI-Grenze, keine plattformweite Firewall. Metadatenreview, Kontextvorbereitung und expliziter Requestversand sind API-only. Keine UI-Antwort als validierte Agentenentscheidung ausgeben.
