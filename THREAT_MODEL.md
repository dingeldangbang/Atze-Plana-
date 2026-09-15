# Threat Model — v0.1

## Assets / Vertrauensgrenzen
Secrets im Prozess/Browser, SQLite mit Originaltexten und Freigaben, Audit, Build-Artefakte. Grenzen: Browser → API, Rollenprüfung → Domain, Domain → lokales Dateisystem, CI → Dependency-Registry/GitHub.

| Angriffsfläche | Bedrohung | Bestehende Kontrolle | Restrisiko / Maßnahme |
|---|---|---|---|
| API/Auth | Tokenraub, Brute Force | lange getrennte Tokens, konstante Vergleiche | TLS/Ingress-Limits nötig; keine MFA |
| Authorization | Selbstfreigabe | feste Rollen, getrennte Tokens | gleicher Mensch kann beide Secrets besitzen |
| Quellen | falsche Claims, Prompt Injection | kein LLM/Executor, manuelles Review | Review/Confidence garantieren keine Wahrheit |
| Browser | XSS / Tokenabfluss | textContent, CSP, Token nur in Memory | kompromittierter Origin/Browser bleibt gefährlich |
| DB | SQL-Injection / Datenverlust | parametrisierte SQL, Transaktionen | Host-Admin kann lesen/manipulieren; Backups nötig |
| Audit | Spurenverfälschung | keine API für Update/Delete | nicht kryptografisch verkettet, keine externe Senke |
| Ressourcen | große Bodies, parallele Writes | begrenzte Felder/Listen, SQLite-Timeout | Request wird vor Feldvalidierung gelesen; Reverse Proxy erforderlich |
| Dependencies/CI | Supply-chain | versionsgepinnt, pip-audit, read-only CI-Berechtigung | keine Hash-Locks, kein unabhängiger Audit |
| Terminal/USB/BLE/Netzgeräte | unkontrollierte Ausführung | NOT IMPLEMENTED | vor Adaptern separates Threat Model |
| Cloud/Webhooks/Agents/Sandbox | Token-/Toolmissbrauch | NOT IMPLEMENTED | keine vorhandene Isolation behaupten |

## Abuse cases und Tests
Falsche Rolle → 403 (SEC-002); fehlender Token → 401 (API-001); unzureichende Evidenz → blocked (TRI-002/003); Stop nach Approval → blocked auch nach Restart (SEC-003); DB-Ausfall → redacted 503 (SEC-004); Audit-Fehler → fachliche Mutation rollback (AUD-001).

## Nicht-Nachweise
Kein Penetrationstest, kein Secret-Scanner-Vollscan der gesamten Git-Historie, keine Hardware-Sicherheitsprüfung, keine Produktionsfreigabe. Dependency-Scan ist nur ein Advisory-Abgleich zum Ausführungszeitpunkt.

## v0.2 Ergänzung
| Fläche | Kontrolle | Restgrenze |
|---|---|---|
| Archive namespace / Traversal | Pfadvalidierung, UUID-physische Dateien, SQL-parametrisierte Auflösung | keine Host-Isolation gegen Admin/Mount-Manipulation |
| Copy/Relocation | hashgeprüfte Quelle, fsync/Readback-Ziel, atomarer DB-/Auditwechsel, Quelle behalten | Orphans/Retained Copies wachsen, keine atomare Cross-FS-Transaktion |
| Cache deletion | nur expired cache, committed tombstone, retry-sicher | Cleanup explizit; temporäre Daten können vorher verloren gehen |
| FTS / Memory Prompt Injection | reine Retrieval-Daten, typed Kategorien, keine Tools, no action permission | Label/Reviewer kann irren, kein semantischer Wahrheitsbeweis |
| Kontextfremde Quellen | same-project Referenzvalidierung, Query-Projektfilter | beide Rollen sehen alle Projekte, keine Tenant-Grenze |
| Datenverlust | unveränderliche Archive, lesende Hashchecks | DB-only Backup nicht mehr vollständig; Gesamtrestore noch kein Produktionsnachweis |

Regressionen: STO-001..010, CACHE-001/002, MEM-001/002, RAG-001/002, MIG-001. Tests verwenden temporäre Verzeichnisse als **simulierten** zweiten Tier, keine behauptete SD-Hardware.

## v0.2.1 — Testdatenkontamination / falsche Erfolgsanzeigen
Risiko: beliebig adressierbarer Smoke-Runner könnte Testeingaben in Betriebs-DB schreiben; alte UI-Werte oder PASS-Dateien könnten einen ausgefallenen/neuen Lauf verdecken. Kontrolle: keine fremde Ziel-URL, selbst gestartete temporäre echte Testinstanz, eigenständige Credentials, explizites Opt-in und Modusprobe, dauerhafte DB-/Objektroot-Modusmarker, Reportstatus vor Beginn neu schreiben, Werte nach UI-Refreshfehler verwerfen. Kein Fake-Fallback bei fehlenden Adaptern/Roots oder Nullkapazität. Test-SD bleibt Dateiverzeichnis, kein Device-Profil/Live-Gerät.

Restrisiken: Legacydaten ohne Marker brauchen Herkunftsprüfung; Administratoren können Marker oder Datensätze manipulieren. Ein autorisierter Mensch kann falsche Behauptungen erfassen. Die AST-Prüfung erkennt ausgewählte Testimports, nicht jede denkbare Scheinimplementierung. Kein ausgeführter Browser-E2E in diesem Schnitt.

## v0.3 — ungeprüfte Primärergebnisse / Worker-Manipulation / Stale Approvals
Neue Angriffsflächen: eingereichte strukturierte Claims, Challenge-Jobs/Snapshots, Worker-Servicecredential, Lease-/Complete-Endpunkte, Why-/Adopt-Darstellung. Grenzen: Operator erzeugt kein PASS, Reviewer spielt keinen Worker, Worker erfasst keine Primärquellen/Approvals. Claim-/Complete-Token und Lease getrennt; Kontextfingerprint/neueste Jobs/Policy/Report werden atomar verifiziert. Server erzeugt keinen Ersatzbericht ohne Workeraufruf.

Bedrohungen: falsche Evidence-Metadaten, unterdrückte Gegenquellen, überbreiter Primärtext, Replay, stale Daten nach Freigabe, Reviewer-Umgehung kritischer Lücken, Credentialleck/Redirect, Snapshot-DoS. Kontrollen: projektweit begrenzte Gegenprüfung, exakte strukturierte Befunde, freier Primärtext nicht adoptiert, Context-/Stopinvalidierung, zwingende Gateprüfung vor Approval/Adopt, keine HTTP-Redirects für Servicetoken, keine Remote-Plaintext-Verbindung, 4-MiB-/500-Source-/500-Finding-Bounds mit BLOCK statt Teil-PASS. Kein unabhängiger Source-Provider, semantischer Truth-Check oder Host-Sandbox vorhanden. Der Worker kann unter demselben OS-Nutzer prinzipiell Hostdateien lesen; API-Rechtetrennung ist keine Hostisolation.

CH-001..017 plus echte separate Workerprozesse im HTTP-Smoke prüfen diese begrenzten Softwareverträge. Kein Hardware-/Kausal-/Produktionssicherheitsnachweis daraus ableiten.

## Privacy-first AI boundary
Keine Appdaten unverschlüsselt an Dritte. Neue Model-Egresspfade ausschließlich über ExternalDataGateway und die gebundene Policy-/Reviewer-Prüfung. Standard local-only/external-deny, keine stillen Fallbacks/Redirects, keine Credentials im Kontext, kein Modell-Toolrecht. TLS schützt Transport, nicht Providerverarbeitung. Diese Python-Kontrolle ist KEIN universeller OS-/Netzwerkbeweis; Challenge-Control-Transport ist noch separat, MCP/Agent-Tools fehlen. Host-/Ingress-/Klassifizierungs-/verschlüsselter-Cache-/MCP-/Sandboxgates bleiben release-blockierend. [Begrenzter tatsächlicher Vertrag](docs/02-core/model-gateway.md).
