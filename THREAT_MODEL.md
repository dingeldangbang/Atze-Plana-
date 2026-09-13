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
