# Roadmap und vollständige Modulabgrenzung

Stand 2026-09-14; Begriffskorrektur (D1) 2026-09-15 übernommen: „2 GB" bezeichnet das RAM der ausführenden Zielhardware (Honeywell CT45P-XON), kein Core-Speicherbudget; „Free Tier" ist eine externe Anbieter-Nutzungs-/Kostenklasse und niemals ein Ersatz für Daten. PLANNED bedeutet Ziel, NOT IMPLEMENTED bedeutet kein ausführbarer Adapter/Workflow. Keine Liefertermine oder Performancezusagen.

| Master-Bereich | Status | Fehlender Nachweis / nächster Schritt |
|---|---|---|
| 00 Overview | IMPLEMENTED | Dokumentierte Grenzen und Begriffe |
| 01 Architecture | IMPLEMENTED Kern | Kein verteiltes System |
| 02 Core | PARTIAL | Result Packages, separater Challenge Worker, Triage/Approval/Adoption plus bisheriger Kern; echte getrennte lokale Modell-CI, kein operativer Orchestrator/Action-Executor |
| 03 Plan | PARTIAL | Task-PLAN-Versionen, echte Archive-/Memory-/Evidence-Referenzen, Context Lock/Widerruf und Gateintegration; versionierte Resource-Registry (Upload mit SHA-256, Referenz-Links auf Task/Projekt, Byte-Vergleich, bestätigte Deaktivierung, [Vertrag](../25-resources/resources.md)); kein universeller Workflow-/Query-/Binary-Builder, kein Virenscan |
| 04 Agents | PARTIAL | Agent Builder v1 real: versionierte deklarative Registry, Referenz-Zuweisungen auf Task/Projekt, gebundene Einzel-Runs durch die vollständige prepare-/Consent-/execute-Kette mit Audit und Default-Deny ([Vertrag](../26-agents/agents.md)); keine autonome Tool-Ausführung, kein Orchestrator/Scheduler/Sandbox/Lifecycle, Outputs nie adoptiert |
| 05 Devices | NOT IMPLEMENTED | USB, WiFi, BLE, Serial, Discovery, Device Bridge fehlen; reale Testgeräte und Adaptermodell nötig |
| 06 Android | PARTIAL | Nativer read-only HTTPS-Statusclient, echtes SDK-/Debug-APK-/Emulatortest-CI; keine physische Honeywell/Repair-/Fastboot-/EDL-/Firmwarevalidierung |
| 07 IoT | PARTIAL | Echte HTTP-Telemetrie-Ingestion: deklarative Device-/Sensor-Registry, fail-closed Device-Token, unveränderliche hash-verifizierte/versionierte Batches, reviewerbestätigte Deaktivierung ([Vertrag](../23-telemetry/telemetry.md)); WS/MQTT/Serial, Kalibrierung, Firmware-Upload, physische ESP32-Validierung fehlen |
| 08 Network | PARTIAL | Eigene HTTP-API vorhanden; kein Monitoring/Discovery/MQTT/SSH/Incident-Executor |
| 09 Cloud | NOT IMPLEMENTED | Kein Hybrid-/Multi-Cloud-/Edge-/Provider-Adapter, kein Provisioning |
| 10 Web Research | PARTIAL | Echtes begrenztes Bright-Data-MCP: Discovery (initialize/tools/list) und reviewerbestätigtes tools/call für genau die zwei allowlisted Kandidaten (search_engine, scrape_as_markdown) mit Argument-/Result-Grenzen ([Vertrag](../22-mcp/brightdata.md)); Live-Provider NOT CONFIGURED; Browser/Crawl/PDF/Cache/Rate-Handling, Zonen, Käufe, Login/Refresh fehlen |
| 11 3D | NOT IMPLEMENTED | Keine Unity-Version, Module, Pakete, Szenen, Assets, Avatare, Worlds oder Digital Twins; kein Editor-/Headless-Build |
| 12 Software | PARTIAL | Python-Webkern, statische UI und echte read-only CLI gegen die dokumentierte API ([Vertrag](../12-software/cli.md)); kein universeller CLI-/Softwareprojekt-Builder, keine Mutationsbefehle |
| 13 Sandbox | PARTIAL Cache / PARTIAL Isolation | Cache TTL/Cleanup, separater Challenge-Prüfprozess und reale Subprozess-Sandbox mit RLimits/Hard-Timeout für die Objekt-Re-Verifikation ([Betriebshandbuch](../19-operations/operations.md)); kein Netzwerk-/Dateisystem-Namespace, kein Seccomp, kein allgemeiner Executor/isolierter Workspace |
| 14 Testing | PARTIAL | Kern-Unit/Integration/API-Smoke; echter PLAN-Browserlauf ergänzt (Resultate in TEST_REPORT), Geräte/Agenten/Lasttest fehlen |
| 15 Trends | PARTIAL | Echte deterministische Trend-Checks über ingestierte Telemetrie (Drift, Level-Shift, Varianzänderung, Out-of-Range-/Suspect-Raten) als Query mit dokumentierten Kriterien und VERIFIED TREND vs. INSUFFICIENT EVIDENCE ([Vertrag](../24-trends/trends.md)); kein ML, keine Prognose, keine Lifecycle-/Proaktivitäts-/allgemeine Anomalieengine |
| 16 Evidence | PARTIAL | Manuelle Provenance, Hash, Review; deterministische Widerspruchskandidaten (within/across records, Wert-/Einheitenvergleich) und dokumentierte Quellenrangfolge als CALCULATED-Queries ([Vertrag](../16-evidence/analysis.md)); keine automatische Wahrheit/Aktualität, keine Konfliktauflösung, kein semantischer Abgleich |
| 17 Security | PARTIAL | Rollen, Fail-closed, Stop; Permission-Lease-Engine für MCP tools/call (Allow Once/Task/Temporary + Expiry ≤24 h + Verbrauchslimit + bestätigter Widerruf, unter Stop widerrufbar; [Vertrag](../17-security/permission-leases.md)); keine individuelle Benutzerverwaltung, MFA, manipulationssicherer Audit |
| 18 Deployment | PARTIAL | Lokaler Start, Build, CI; dokumentierte Free-Tier-Optionen mit exaktem Einrichtungspfad ([Free-Tier-Optionen](../18-deployment/free-tier-options.md)); kein tatsächliches Free-Tier-/Produktionsdeployment |
| 19 Operations | PARTIAL | Runbooks/Health/SQLite-Backup; reale In-App-Plattformübersicht aus gespeicherten Records plus Anbindungs-Registry mit +/−-Verwaltung (Reviewer-bestätigte Deaktivierung, Daten erhalten; [Vertrag](../27-monitoring/monitoring.md)); Reviewer-getriggerter verifizierter In-App-Datenbank-Backup mit durablem Record/Audit ([Betriebshandbuch](../19-operations/operations.md)); keine automatische Überwachung, kein Alerting/Metrics-Backend, keine automatischen/Offsite-Backups, kein Objektwurzel-Backup im Endpunkt |

## Reihenfolge weiterer Arbeit
1. [Mobile/Context/Storage-Architektur](../20-context-storage/architecture.md) und [MCP-/Offline-/Remote-Roadmap](../20-context-storage/mobile-roadmap.md) weiter umsetzen; Identitäts-/Policy-Modell, widerrufbare und ablaufende zielgebundene Freigaben, Migrationen, Request-Limits, Browser-E2E und Recovery-Abnahme.
2. Lokale read-only Device Bridge mit konkretem Gerätevertrag: Identity, Discovery, Capabilities, Connection, Permissions, Datenmodell, Commands, Events, Failure Modes, Validation und Safety. Keine automatischen USB-/Netzwerkscans ohne Freigabe.
3. Isolierte ephemere Worker und Agenten mit deny-by-default Tool-Liste, Ressourcenlimits, Audit und Emergency-Stop-Kopplung.
4. Provider-Recherche nur mit berechtigten Credentials, ToS-/Datenschutzprüfung und Originalquellenbindung; Rate-Limits/Retry/Caching anhand realer Providerantworten testen.
5. Unity/Android/ESP32 jeweils erst nach SDK-/Hardwareentscheidung, Testfixtures und echten Build-/Gerätenachweisen.

## Nicht verfügbare Abläufe
User→Orchestrator→Triage, Task→Agent→Sandbox, Device→Bridge→Telemetry, Bright Data→Evidence, Repair→Approval→Device, Trend→Action sind Zielbilder, keine aktuellen Sequenzen. Nur die tatsächlich implementierten Abläufe werden in den Architekturdiagrammen gezeigt.

## Invasive Aktionen
FLASH/FIRMWARE/EDL WRITE sind nur Enum-Werte zur Triage. Keine Commands, Firmwaredateien, Backup-/Recovery-Garantien oder Herstellerautorisierungen vorhanden. Niemals aus einer heutigen Freigabe ableiten, dass ein Gerät sicher geflasht werden kann. Honeywell-/EDL-Verfahren benötigen herstellerspezifische Freigaben und geprüfte Images; hier ausdrücklich BLOCKED.
