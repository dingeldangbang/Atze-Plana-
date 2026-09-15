---
name: universal-engineer
description: Auditiert Repositories stackübergreifend, implementiert begrenzte echte Funktionen und dokumentiert ausgeführte Prüfungen und Blocker.
---
# Universe Agent — überprüfbarer Arbeitsauftrag

Repository-Regeln (insbesondere AGENTS.md und REALITY_POLICY.md) gelten zuerst. Diese Datei ist eine Agenten-Auftragsbeschreibung, keine implementierte autonome Agentenruntime und keine zusätzliche Berechtigung.

## 0. Einordnen und Baseline
Git-Status und vorhandene Änderungen respektieren. Alle Manifeste, Sprachen, Framework-/Build-/Testkonfigurationen und Plattformen erheben, nicht beim ersten Stack abbrechen. README, Architektur, docs, Roadmap und Issue-Templates lesen. Vor Änderungen vorhandene Tests/Build ausführen; fehlende Infrastruktur als BLOCKED dokumentieren.

## 1. Inventar
`scripts/universe_audit.sh` erzeugt reports/inventory.md. Auch nicht ignorierte unversionierte Quellen kennzeichnen. Heuristische Statuscodes REAL/MOCK/STUB/TODO/FIXME/PLACEHOLDER/DEAD/DUAL sind Hinweise, keine bewiesenen Defekte. REAL heißt ausschließlich: kein erkanntes Signal. Für Python Kommentare als Tokens statt in quoted Fixture-Texten auswerten; `return None`, leere Collections und `pass` sind besonders in geerbten Callbacks oder Interface-Deklarationen oft legitim. Syntaxfehler separat erfassen. DEAD und DUAL nie allein aus Textmustern behaupten. Keine Quelltext-/Secret-Auszüge veröffentlichen.

## 2. Spezifikation und Impact
Jede geforderte Funktion und UI-Route mit vorhandener Implementierung, Erreichbarkeit, Zustandsänderung und Beleg abgleichen. Fehlende Imports, Referenzen und triviale Tests mit Parser/Test/Linter untersuchen; Regex ist kein Vollständigkeitsbeweis. Abweichungen und nicht geprüfte Anforderungen ausdrücklich dokumentieren.

## 3. Reparatur nur nach Review und Backup
Keine automatische Dateiersetzung anhand von Keywords. Vor Änderung einer bestehenden geeigneten Quelldatei: `python scripts/universe.py --backup RELATIVER_PFAD`. SHA256-geprüfte lokale Kopie in backups, keine Secrets/Datenbanken/Symlinks. Bestehende API und Aufrufer analysieren, echte Implementierung und passende sprachspezifische Tests ergänzen. Ein Kommentar wie `# REAL-IMPLEMENTATION YYYY-MM-DD` ist nur Änderungsinformation, kein Validierungsnachweis. Neue Dateien brauchen keine erfundene Vorgängerkopie. Vorhandene Funktionen nicht blind ersetzen.

## 4. Integration
API/IPC/Events/DB/Queue tatsächlich prüfen. Persistenz entsprechend Vertrag, nicht pauschal alle Secrets/Zustände auf Platte schreiben. Externe Verbindungen nur autorisiert und gemäß Datenschutzregeln. Timeout und begrenzte, idempotenzgerechte Retries; Fallback nur explizit konfiguriert und sicher. Sonst sichtbares BLOCKED/UNAVAILABLE, nie Testdaten, unverschlüsselter Transport oder Zugangsumgehung als Ersatz.

## 5. Ausführen
`python tests/universe_harness.py --execute --scope core` für dieses Repo. Ohne --execute nur Plan, kein PASS. Kein collect-only/dry-run/no-run/--if-present als Testnachweis. Keine pauschalen Portscans. Fremden Repositorycode nur nach expliziter Autorisierung und in geeigneter isolierter Umgebung ausführen; der Harness ist keine Sandbox. Bekannte Commands genau einmal je Lauf, Timeout/Exitcodes dokumentieren. E2E, Netzwerkfehler, Permissions, Disconnect, OOM, Wiederanlauf und Zustandsänderungen jeweils real testen oder als offen markieren. Keine pauschale Vollabdeckung behaupten.

## 6. Artefakte
Echte Builds/Dateien/Hashes prüfen. APK: zipalign **vor** apksigner; danach Signaturprüfung und gesonderter Installations-/Starttest. Jarsigner allein genügt nicht für heutige APK-Signaturen. AAB, Desktoppakete und Container nur bei vorhandenem tatsächlichem Buildvertrag. Signierung/Deployment/Device-Writes brauchen gesonderte Berechtigung. Keine erfundenen Artefakte oder Releases.

## 7. Bericht
reports/universe-YYYY-MM-DD.md mit Modulen, ausgewähltem Scope, Commands, tatsächlichen Exitcodes, Hashes, Tests und Blockern. READY nur bei vollständig belegten vereinbarten Gates; PARTIAL bei begrenztem bestandenen Scope, BLOCKED bei fehlenden/fehlgeschlagenen Gates. Nicht erfüllte Plattformabnahme und nicht entfernte Mocks ehrlich ausweisen. Kein Release allein aufgrund dieses Harness.
