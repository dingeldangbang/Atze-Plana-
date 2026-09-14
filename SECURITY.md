# Security

## Geltung
Dieser Kern besitzt keine externen Ausführungstools. Tokenprüfung, getrennte Operator-/Reviewer-Rollen, Eingabevalidierung, atomare Audit-Einträge und persistenter Triage-Stop sind implementiert. Das ersetzt keinen unabhängigen Security-Audit.

## Meldungen
Keine Secrets, Angriffspayloads gegen Live-Systeme oder private Daten in öffentliche Issues posten. Repository-Eigentümer über einen verfügbaren privaten GitHub-Kanal kontaktieren. Es ist bisher kein dedizierter Security-Kontakt oder SLA festgelegt.

## Schutzmaßnahmen
- Zwei unterschiedliche Bearer-Tokens, mindestens 32 Zeichen; Startup schlägt bei fehlenden Tokens fehl. Zufällige Token empfohlen, nicht Passwörter.
- Keine Rolle aus Request-Feldern; Authentifizierung über konstantzeitlichen Tokenvergleich.
- Reviewer darf keine Primary-Projekte/Evidence/Tasks erfassen; die explizite geprüfte Result-Adoption ist ein separater Reviewer-Pfad; Operator darf weder Evidenz prüfen noch Aufgaben freigeben, Audit lesen oder Stop ändern.
- Kein CORS-Allow-All, kein Cookie-Login, keine Tokenpersistenz im Frontend; CSP und `textContent` statt HTML-Rendering fremder Daten.
- Keine Server-Fetches fremder URLs; dadurch kein implementierter SSRF-Pfad über Quellen. Eine URL ist ein erfasster Verweis, nicht eine geprüfte Quelle.
- SQL-Parameter und Feldlängen; Audit und fachliche Mutation in einer SQLite-Transaktion.
- Jeder Stop-Wechsel schreibt einen unveränderlichen `stop_state`-Record mit aufsteigender Revision, Rolle und Zeitstempel; `/api/control/stop` liefert ihn. Passt kein Record zum aktuellen Control-Zustand, bleiben Revision/Aktor/Zeit null/0 statt erfundener Werte.
- Eine Instanz ohne gebundenen Runtime-Store meldet auf `/health` 503 mit explizitem Grund; kein Erfolg ohne echte Datenbankprüfung.

## Nicht gelöste Risiken
Geteilte Rollen sind keine individuelle Identität; ein Nutzer mit beiden Tokens kann beide Rollen wahrnehmen. Keine MFA, Session-Revoke, per-project ACL, Rate-Limits in der App, Request-Größenbegrenzung, manipulationssichere Auditkette oder Auditierung fehlgeschlagener Logins. DB-Administratoren können Audit- und Stop-Provenienz-Records ändern; beide sind nicht kryptografisch verkettet. Keine automatische Confidence-, Inhalts-, Aktualitäts- oder Gerätevalidierung. Ein Reviewer-Review ist eine menschliche Aussage.

## Human in the loop
READ wird nur mit geprüfter Evidenz, gemeldeter Confidence >=0.8 und bestätigten Voraussetzungen eligible. WRITE, FLASH, FIRMWARE, EDL WRITE, PRODUCTION DEPLOY und PAYMENT erfordern je Aufgabe einen Reviewer-Grund. Keine dieser Aktionen wird ausgeführt. Für spätere finanzielle oder invasive Ausführung ist ein stärkerer, ziel-/betragsgebundener expliziter Freigabevertrag zwingend. Der heutige Approval-Datensatz reicht dafür nicht.

Stop wirkt auf jede neue Triage und Freigabe, nicht auf Netzwerk-, Host- oder Hardwareprozesse. Seit v0.3 bleiben alte Freigaben nach Stop-Deaktivierung ungültig und benötigen neue Challenge/Approval; allgemeine zeitliche Expiry fehlt. Vor Einführung von Executoren muss das korrigiert und getestet werden.

[Threat Model](THREAT_MODEL.md), [Security-Architektur](docs/01-architecture/security-architecture.md).

## v0.2 Context-/Storage-Angriffsfläche
Neue authentifizierte Text-Ingestion (max. 65.536 Zeichen/Objekt), FTS und Dateioperationen. Diese sind Metadaten-/Storagepflege, keine Taskausführung. Relocation/Cleanup/Reindex nur Reviewer; Archive/Cache-Mutationen und Reindex bei Stop blockiert. Fact-Memory benötigt verified Evidence, bleibt aber eine aufgezeichnete Behauptung. Retrieval liefert immer allowed_for_action=false; Prompt-Injection im Text verleiht keine Tools/Rechte.

Neue Roots sind vertrauenswürdig administrierte lokale Dateisysteme, keine fremd beschreibbaren Agenten-Workspaces. UUID-Dateinamen, `O_NOFOLLOW`, Regulärdateiprüfung, Größen-/Hashprüfung, fsync, Source Retention und SQL-Transaktionen schützen API-vermittelte Pfade. Ein kompromittierter OS-Administrator/Root-Elternpfad/Mount kann nicht abgewehrt werden. Filesystem+SQLite haben keinen atomaren gemeinsamen Commit: Orphans möglich, keine automatische Original-GC.

Cache-Cleanup darf ausschließlich abgelaufene Cacheobjekte löschen und committet zuvor Tombstones. Es ist keine Prozessisolation. Multi-Tier-Vollbackup, Remote/MCP-Transportauth, SD-Hotplug/Powerloss, Quoten, Memory-Revocation und echte mobile Hardwarevalidierung bleiben offen. Archive, FTS und Memory liegen unverschlüsselt auf Disk; keine Runtime-Synchronisation privater Daten nach GitHub.

## Verbindliche Realitätsprüfung v0.2.1
[REALITY_POLICY](REALITY_POLICY.md) gilt für jeden Beitrag. Keine Mock-/Demo-/Fake-Provider oder unbemerkten Fallbacks im Betriebsweg. Tests/Fehler-Injektionen bleiben getrennt; `python scripts/reality_check.py` und `python scripts/smoke.py --allow-fixtures` tatsächlich ausführen. Der Smoke startet ausschließlich seine eigene temporäre Testinstanz. Laufreports beweisen keine Geräte-/Providerintegration. [Getrennte Integrationsnachweise](docs/17-security/reality-audit.md).

## Mandatory Challenge v0.3
[Every Decision Must Survive Challenge](docs/02-core/challenge-worker.md). Ohne aktuellen serverseitig verifizierten Workerreport kein Task-ACCEPT, kein Approval und keine autoritative Resultübernahme. Workercredential separat; claim/complete allein erlaubt. Primärpakete/Jobs/Reports unveränderlich bzw. servergebundene Leasezustände; Replay und stale Snapshots blockiert. Kritische Befunde nicht durch Human-Approval überstimmbar. Jeder neue Challenge-/Result-/Evidence-/Stopstand entwertet alte Approvals.

Ein PASS ist ausschließlich der Abschluss begrenzter strukturierter Checks, kein Beweis für Primärfreitext, reale Geräteidentität, unabhängige Quellen oder Kausalität. Adopt speichert nur einen gebundenen Decision-Verweis; direktes fact/decision-Memory blockiert. RAG berechnet die aktuelle Decisiongültigkeit erneut. Gemeinsamer Rulecode und gleicher Entwicklungs-OS-Nutzer sind keine organisatorische/OS-Isolation. Vor Produktion getrennte Nutzer/Secrets/Workersicherheit abnehmen; kein Executor eingeführt.

## Privacy-first AI boundary
Keine Appdaten unverschlüsselt an Dritte. Neue Model-Egresspfade ausschließlich über ExternalDataGateway und die gebundene Policy-/Reviewer-Prüfung. Standard local-only/external-deny, keine stillen Fallbacks/Redirects, keine Credentials im Kontext, kein Modell-Toolrecht. TLS schützt Transport, nicht Providerverarbeitung. Diese Python-Kontrolle ist KEIN universeller OS-/Netzwerkbeweis; Challenge-Control-Transport ist noch separat, MCP/Agent-Tools fehlen. Host-/Ingress-/Klassifizierungs-/verschlüsselter-Cache-/MCP-/Sandboxgates bleiben release-blockierend. [Begrenzter tatsächlicher Vertrag](docs/02-core/model-gateway.md).
