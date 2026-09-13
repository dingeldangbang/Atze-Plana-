# Security

## Geltung
Dieser Kern besitzt keine externen Ausführungstools. Tokenprüfung, getrennte Operator-/Reviewer-Rollen, Eingabevalidierung, atomare Audit-Einträge und persistenter Triage-Stop sind implementiert. Das ersetzt keinen unabhängigen Security-Audit.

## Meldungen
Keine Secrets, Angriffspayloads gegen Live-Systeme oder private Daten in öffentliche Issues posten. Repository-Eigentümer über einen verfügbaren privaten GitHub-Kanal kontaktieren. Es ist bisher kein dedizierter Security-Kontakt oder SLA festgelegt.

## Schutzmaßnahmen
- Zwei unterschiedliche Bearer-Tokens, mindestens 32 Zeichen; Startup schlägt bei fehlenden Tokens fehl. Zufällige Token empfohlen, nicht Passwörter.
- Keine Rolle aus Request-Feldern; Authentifizierung über konstantzeitlichen Tokenvergleich.
- Reviewer darf nicht erfassen; Operator darf weder Evidenz prüfen noch Aufgaben freigeben, Audit lesen oder Stop ändern.
- Kein CORS-Allow-All, kein Cookie-Login, keine Tokenpersistenz im Frontend; CSP und `textContent` statt HTML-Rendering fremder Daten.
- Keine Server-Fetches fremder URLs; dadurch kein implementierter SSRF-Pfad über Quellen. Eine URL ist ein erfasster Verweis, nicht eine geprüfte Quelle.
- SQL-Parameter und Feldlängen; Audit und fachliche Mutation in einer SQLite-Transaktion.

## Nicht gelöste Risiken
Geteilte Rollen sind keine individuelle Identität; ein Nutzer mit beiden Tokens kann beide Rollen wahrnehmen. Keine MFA, Session-Revoke, per-project ACL, Rate-Limits in der App, Request-Größenbegrenzung, manipulationssichere Auditkette oder Auditierung fehlgeschlagener Logins. DB-Administratoren können Auditdaten ändern. Keine automatische Confidence-, Inhalts-, Aktualitäts- oder Gerätevalidierung. Ein Reviewer-Review ist eine menschliche Aussage.

## Human in the loop
READ wird nur mit geprüfter Evidenz, gemeldeter Confidence >=0.8 und bestätigten Voraussetzungen eligible. WRITE, FLASH, FIRMWARE, EDL WRITE, PRODUCTION DEPLOY und PAYMENT erfordern je Aufgabe einen Reviewer-Grund. Keine dieser Aktionen wird ausgeführt. Für spätere finanzielle oder invasive Ausführung ist ein stärkerer, ziel-/betragsgebundener expliziter Freigabevertrag zwingend. Der heutige Approval-Datensatz reicht dafür nicht.

Stop wirkt auf jede neue Triage und Freigabe, nicht auf Netzwerk-, Host- oder Hardwareprozesse. Nach Deaktivierung können bestehende Freigaben wieder approved sein; es gibt keine Revocation/Expiry. Vor Einführung von Executoren muss das korrigiert und getestet werden.

[Threat Model](THREAT_MODEL.md), [Security-Architektur](docs/01-architecture/security-architecture.md).
