# Benutzerhandbuch

## Getting started / Dashboard
Öffne die Instanz-URL. Du siehst Projektanlage, Sicherheitszustand sowie Listen für Projekte, Evidence und Aufgaben. Vor Anmeldung sind keine Workspace-Daten geladen. Gib einen vom Administrator separat erhaltenen Operator- oder Reviewer-Token ein. Er bleibt nur im Speicher des Tabs; bei Reload erneut anmelden. „Trennen“ leert Token und Anzeige. Die App enthält keine Demo-Messwerte.

## Projekte
Als Operator Name und optional Beschreibung eintragen und speichern. Gespeichert werden UUID, Erfassungszeit und Audit-Ereignis. Kein zusätzliches Approval erforderlich: das ist Metadatenpflege, keine externe WRITE-Aktion. Reviewer kann Projekte sehen, nicht anlegen. Listen zeigen maximal die ersten 100 Einträge; weitere Seiten nur via API.

## Evidence / Context
Oberfläche zeigt Claims, Reviewzustände und gemeldete Confidence. Erfassung und Review derzeit über [API](../08-network/APIs.md). Originaltext, Quellenmetadaten und Hash bleiben in SQLite. Reviewer prüft mit Grund genau einmal. Keine automatische Wahrheitserkennung, kein Dateiupload, Quellenbrowser oder Kontexteditor.

## Aufgaben / Triage
Aufgaben werden per API angelegt. „Triage prüfen“ berechnet die aktuellen Blocks/Freigaberegeln und speichert einen Entscheidungssnapshot im Audit. reasons erklären fehlende Voraussetzungen. Kein automatisches Auflösen eines Blocks. Nicht-lesende Aktionen benötigen separate Reviewer-Freigabe per API. Auch approved führt nichts aus.

## Administration / Safety
Reviewer liest Audit und ändert globalen Stop per API. Stop blockiert Triage, nicht Projekterfassung oder externe Geräte. Keine Benutzer-/Rollenverwaltung in der UI. Niemals Secrets oder nicht autorisierte personenbezogene Daten als Evidence speichern.

## Noch nicht verfügbare Benutzerbereiche
Plan, Files, umfassender Context, Devices, Network, Telemetry, 3D World, Agents, Sandbox, Tests als UI-Modul, Repair, Trends sind NOT IMPLEMENTED. Es gibt dafür keine versteckten Menüs, Befehle, Geräte oder gespeicherten Ergebnisse. Testreports entstehen nur über Entwicklungs-/CI-Werkzeuge. [Roadmap](../00-overview/roadmap.md).
