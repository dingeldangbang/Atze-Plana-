# Betrieb mit etwa 2 GB RAM — CONDITIONAL

Begriffskorrektur (2026-09-15): „2 GB" bezeichnet das maximale RAM der **ausführenden Zielhardware (Honeywell CT45P-XON)** — der Rahmen, innerhalb dessen der Core hier geplant wird —, kein Core-Speicherbudget an sich. „Free Tier" ist eine Nutzungs-/Kostenklasse **externer Anbieter**, nie ein Datenersatz oder Fallback auf Beispieldaten. Kein Lasttest auf dem physischen Gerät und kein Free-Tier-Deployment wurden durchgeführt (NOT RUN). Nachfolgend ein **Planungsbudget, keine Messwerte oder Zusage**.

| Komponente | RAM-Planungsreserve |
|---|---:|
| OS, SSH und Basisdienste | 400–600 MiB |
| ein Uvicorn/Python-Prozess | 150–350 MiB |
| SQLite Pagecache / Dateisystemcache | 150–300 MiB |
| TLS-Ingress und Monitoring | 100–200 MiB |
| freie Reserve | Rest bis ca. 2 GiB |

Ein bis zwei vCPU für geringe interaktive Nutzung ansetzen; Durchsatz, gleichzeitige Nutzer und Latenz müssen gemessen werden. SQLite serialisiert hier alle Request-Transaktionen, einschließlich Reads. Große Evidenzlisten (100 Texte à 20.000 Zeichen) erhöhen temporären Speicherverbrauch.

## Empfohlene Konfiguration
Ein Worker, SQLite auf lokaler persistenter SSD, kein Redis/Postgres/Object-Store zusätzlich erforderlich. Kleine Listen mit `limit`, Ingress-Body-/Rate-/Timeout-Limits, Disk-Warnung und Backup-Retention. Kein Reload im Betrieb. `requirements.lock` umfasst Entwicklungswerkzeuge; Builds/Tests nicht parallel zur Produktion auf engem RAM ausführen.

## Ephemere Worker / Scaling / Grenzen
Ephemere Worker sind NOT IMPLEMENTED. Unity, Android-Builds, Browser-Crawling und LLM-Hosting gehören nicht auf diesen 2-GB-Kern. Später ausgelagerte Worker separat budgetieren und isolieren. Keine Multi-Replica-Skalierung mit lokaler SQLite. v0.2 FTS kopiert indizierten Text zusätzlich lokal; externe Blobablage allein garantiert keinen konstanten Core-Speicherbedarf. Automatische Erstplatzierung Local→SD reduziert keinen bereits belegten Speicher; Relocation behält Originalkopien. Taskgebundener dateibasierter Cache implementiert, aber ohne Cleanup-Daemon; Evidenz wächst ohne automatische Retention. Swap ist kein Ersatz für Kapazitätsprüfung; OOM-/Disk-Verhalten vor Freigabe testen.

## v0.3 Zusatzbudget
Zusätzlich zum API-Prozess läuft der separate Challenge-Prozess (stdlib HTTP + Pydantic-Regeln, kein LLM). Das frühere Einprozessbudget ist damit nur historische Basis; zusätzliche Python-/Snapshot-/Report-RAMreserve einplanen und tatsächlich messen. Projekt-Evidence max. 4 MiB/500 Datensätze pro Challenge, größere Scopes BLOCKED. Snapshot- und Auditwachstum, serialisierte SQLite-Transaktionen und wiederholte Challenges begrenzen Durchsatz/Storage. Keine 2-GB-Tauglichkeit oder große autonome Workloads durch diese Limits bewiesen.

## KI-Ressourcen
Core hält keine Modellgewichte und lädt keine Inferenzbibliothek. Große Modelle benötigen einen separat bereitgestellten Worker; RAM/GPU/Modellkapazität wird noch nicht automatisch gemessen oder provisioniert. Gateway-Textgrenzen sind kein 2-GB-Lastnachweis. Socketoperationen können SQLite-Schreibzugriff blockieren; Isolation/harter Deadlinebetrieb vor Produktion abnehmen. Kein automatisches Cloud-Offloading/Fallback.
