# Security- und Permission-Architektur

| Zugriff | Public | Operator | Reviewer |
|---|---|---|---|
| UI/Static/Health | ja | ja | ja |
| Projekte/Evidence/Aufgaben/Stop lesen; Schema; Triage | nein | ja | ja |
| Projekte/Evidence/Aufgaben anlegen | nein | ja | nein |
| Evidence review, Task approval, Stop ändern, Audit lesen | nein | nein | ja |
| Archive/Memory/Cache erfassen | nein | ja | nein |
| Archive/Cache lesen, Memory/Storage Health, FTS suchen | nein | ja | ja |
| Relocation, Cache-Cleanup, Reindex | nein | nein | ja |
| Execution / Shell / Device / Cloud | nicht implementiert | nicht implementiert | nicht implementiert |

Authentifizierung ist eine fest konfigurierte Rollenidentität, keine Benutzerverwaltung. Zwei verschiedene Tokens sind technisch vorgeschrieben, die tatsächliche personelle Trennung ist organisatorisch sicherzustellen. Kein Projekt-ACL: beide Rollen können alle Projekte lesen.

Fehler: 401 fehlender/falscher Token, 403 Rolle unzulässig. Domainvalidierung prüft vor dem Commit. Fehlgeschlagene Authentifizierung wird bisher nicht auditiert. Kein Approval-Bypass: approve berechnet unter derselben Schreibtransaktion Triage erneut und akzeptiert nur approval_required.

[Threat Model](../../THREAT_MODEL.md), [Human approval und Grenzen](../../SECURITY.md), [Audit/Stop-Vertrag](../02-core/core.md).

## Separate Challenge-Rolle v0.3
ATZE_CHALLENGE_TOKEN ist weder Operator noch Reviewer. Nur claim/complete erlaubt; normale Daten-/Approval-APIs akzeptieren ihn nicht. Result submit: Operator; Why/Quellen/Rechallenge: beide Benutzerrollen; Adopt: Reviewer. Report-Fingerprint/Lease/aktuellste Jobs/Policy werden atomar geprüft, Report wird deterministisch reproduziert. Kein Token konfiguriert/Worker ausgefallen → keine Ersatzprüfung. Primärresultate erhalten niemals durch eigenes Verdict oder geänderten UI-Zustand einen Pass. Ein gemeinsam genutzter Entwicklungs-OS-Account bleibt eine stärkere Vertrauensgrenze; echte OS-/Secretisolation ist vor Produktion separat umzusetzen.
