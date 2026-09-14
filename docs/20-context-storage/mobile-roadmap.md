# Mobile / MCP / Offline — nächste Ausbaustufen

Diese Seite beschreibt **PLANNED**, nicht aktuelle Fähigkeiten.

## Mobile Project Server
Zielgeräte Linux Mini-PC/Pi/Edge, Android separat erst nach Runtime-/OS-/SDK-Entscheidung. Kein Android-Root, ADB oder SD-Formatierung als Installationsvoraussetzung behaupten. Aktuell läuft nur der Python-Server mit lokalen Daten ohne Cloud. Vor Hardwarefreigabe: FTS5-Verfügbarkeit, `fsync`/Rename-/Mountsemantik, Powerloss, begrenzter Flash, Akku, thermal throttling, Backup, Token-/Geräteschutz testen.

## MCP
Standardkonformen MCP-Server/Host-Adapter wählen, Protokollversion und Transport pinnen. Zuerst read-only Tools `read_project_file` und `search_project_context` auf bestehende Domainservices abbilden, mit Auth-/Schema-/Error-/Capabilities-Tests. Tools/Devices müssen deny-by-default bleiben. Kein generischer Terminalzugriff. Remote Transport erfordert Origin-/Session-/Token-/Rate-Limit-Modell. Das heutige HTTP-API ist ausdrücklich kein MCP-Protokoll.

## Offline Queue / Sync
Queue muss lokale immutable Event-ID, Projekt/Device/Actor, Payload-/Originalhash, kausalen Parent/Revision, Timestamp und Zustände pending/sent/conflict/accepted/rejected haben. Zustellung mindestens einmal plus serverseitige Idempotenz, keine behauptete Exactly-once-Garantie. Konflikt vor Merge explizit erkennen und Triage/Human Approval anwenden; Audit lokal und remote. Keine automatische Überschreibung nach Uhrzeit. Derzeit keine Queue oder Syncfunktion vorhanden.

## Tier 3/4 / Rebalancing
Provideradapter für Server/Cloud mit Auth, Hash/Version, Retry, Retrybudget, Quoten, Datenschutz und Offline-Pinning. Bereitstellung/Migration kann Kosten und Datentransfer auslösen: explizite Policy/Freigabe. Erst Copy→Hash→Verify→Index→Retention; Source Delete nach unabhängigem Haltbarkeitsnachweis, Retentionfrist und Freigabe. Der aktuelle Local→SD-Erstplatzierer nutzt nur Belegung, keine Hot/Cold-/Prioritätsklassifikation und keinen kontinuierlichen Monitor.

## 2-GB-Core
Metadaten und kompakte Indizes lokal halten, große Dateien und Buildworkspaces extern. Aktuell ist FTS eine zusätzliche lokale Textkopie, nicht kostenloser Remoteindex. Insgesamt kein Last-/RAM-Benchmark und keine Unterstützung für das exemplarische 7,2-GB-Unity-Workspace. Streaming, begrenzte Indexbudgets, Indexeviction und remote federated Retrieval müssen zuerst implementiert werden. Kein Core-internes LLM/Embeddingmodell geplant, ohne eigenes Ressourcenbudget.

## Freigabekette
Context ist untrusted Input. Preflight-Triage/Permissions müssen VOR jeder späteren Execution liegen. Ergebnis-Triage NACH Tests kontrolliert, was als Memory/Evidence übernommen werden darf. Kein vom Agenten erzeugter „verified“-Status, keine Permission-Eskalation durch Memory, MCP oder Projektpräferenzen. GitHub-Updates bleiben versionierte reviewed Änderungen; Runtime-Secrets und private Originale werden nicht automatisch committed.
