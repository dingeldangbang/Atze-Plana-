# Roadmap und vollständige Modulabgrenzung

Stand 2026-09-13. PLANNED bedeutet Ziel, NOT IMPLEMENTED bedeutet kein ausführbarer Adapter/Workflow. Keine Liefertermine oder Performancezusagen.

| Master-Bereich | Status | Fehlender Nachweis / nächster Schritt |
|---|---|---|
| 00 Overview | IMPLEMENTED | Dokumentierte Grenzen und Begriffe |
| 01 Architecture | IMPLEMENTED Kern | Kein verteiltes System |
| 02 Core | PARTIAL | Projekte/Aufgaben/Evidence/Triage/Approval; kein Orchestrator, Context-/Decision-LLM oder Action-Executor |
| 03 Plan | NOT IMPLEMENTED | Kein Datei-/Quellenmanager, Query-/Workflow-Builder oder Plan-Workspace; nur Projektmetadaten |
| 04 Agents | NOT IMPLEMENTED | Kein Agent Builder, Runtime, Tools, Lifecycle; vor Implementierung Tool→Permission→Task→Triage→Execution-Vertrag und isolierte Negativtests |
| 05 Devices | NOT IMPLEMENTED | USB, WiFi, BLE, Serial, Discovery, Device Bridge fehlen; reale Testgeräte und Adaptermodell nötig |
| 06 Android | NOT IMPLEMENTED | Keine App/SDK/ADB/Fastboot/EDL/Repair-Server/Honeywell CT45p Integration oder Firmwarevalidierung |
| 07 IoT | NOT IMPLEMENTED | ESP32, Sensoren, Telemetrie, Kalibrierung, Echtzeit nicht angeschlossen |
| 08 Network | PARTIAL | Eigene HTTP-API vorhanden; kein Monitoring/Discovery/MQTT/SSH/Incident-Executor |
| 09 Cloud | NOT IMPLEMENTED | Kein Hybrid-/Multi-Cloud-/Edge-/Provider-Adapter, kein Provisioning |
| 10 Web Research | NOT IMPLEMENTED | Bright Data SERP/Scraping/Browser/Crawl/Extraction/PDF/Cache/Rate-Handling fehlen; URLs nur manuelle Referenzen |
| 11 3D | NOT IMPLEMENTED | Keine Unity-Version, Module, Pakete, Szenen, Assets, Avatare, Worlds oder Digital Twins; kein Editor-/Headless-Build |
| 12 Software | PARTIAL | Python-Webkern und statische UI vorhanden; kein Android-/CLI-/Softwareprojekt-Builder |
| 13 Sandbox | NOT IMPLEMENTED | Tests in Temp-DB sind KEINE Sicherheitsisolation; keine Worker, Artefaktverwaltung oder Lifecycle |
| 14 Testing | PARTIAL | Kern-Unit/Integration/API-Smoke; Browser-E2E, Geräte, Agenten, Lasttest fehlen |
| 15 Trends | NOT IMPLEMENTED | Keine Anomalie-, Lifecycle- oder Proaktivitätsengine |
| 16 Evidence | PARTIAL | Manuelle Provenance, Hash, Review; keine Quellenrangfolge, automatische Wahrheit/Aktualität oder Widerspruchserkennung |
| 17 Security | PARTIAL | Rollen, Fail-closed, Stop; keine individuelle Benutzerverwaltung, MFA, manipulationssicherer Audit |
| 18 Deployment | PARTIAL | Lokaler Start, Build, CI; kein tatsächliches Free-Tier-/Produktionsdeployment |
| 19 Operations | PARTIAL | Runbooks/Health/SQLite-Backup; keine automatische Überwachung oder Backups |

## Reihenfolge weiterer Arbeit
1. Identitäts-/Policy-Modell, widerrufbare und ablaufende zielgebundene Freigaben, Migrationen, Request-Limits, Browser-E2E und Recovery-Abnahme.
2. Lokale read-only Device Bridge mit konkretem Gerätevertrag: Identity, Discovery, Capabilities, Connection, Permissions, Datenmodell, Commands, Events, Failure Modes, Validation und Safety. Keine automatischen USB-/Netzwerkscans ohne Freigabe.
3. Isolierte ephemere Worker und Agenten mit deny-by-default Tool-Liste, Ressourcenlimits, Audit und Emergency-Stop-Kopplung.
4. Provider-Recherche nur mit berechtigten Credentials, ToS-/Datenschutzprüfung und Originalquellenbindung; Rate-Limits/Retry/Caching anhand realer Providerantworten testen.
5. Unity/Android/ESP32 jeweils erst nach SDK-/Hardwareentscheidung, Testfixtures und echten Build-/Gerätenachweisen.

## Nicht verfügbare Abläufe
User→Orchestrator→Triage, Task→Agent→Sandbox, Device→Bridge→Telemetry, Bright Data→Evidence, Repair→Approval→Device, Trend→Action sind Zielbilder, keine aktuellen Sequenzen. Nur die tatsächlich implementierten Abläufe werden in den Architekturdiagrammen gezeigt.

## Invasive Aktionen
FLASH/FIRMWARE/EDL WRITE sind nur Enum-Werte zur Triage. Keine Commands, Firmwaredateien, Backup-/Recovery-Garantien oder Herstellerautorisierungen vorhanden. Niemals aus einer heutigen Freigabe ableiten, dass ein Gerät sicher geflasht werden kann. Honeywell-/EDL-Verfahren benötigen herstellerspezifische Freigaben und geprüfte Images; hier ausdrücklich BLOCKED.
