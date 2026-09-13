# Administratorhandbuch

## Users / Roles / Permissions / Policies
Keine Benutzerverwaltung, nur zwei geteilte Tokens. Tokens an getrennte verantwortliche Personen verteilen; Rollenmatrix in [Security-Architektur](../01-architecture/security-architecture.md). Policy ist Code: Changes brauchen Tests und Review. Kein Admin-Superuser-Endpoint oder Recht zur Ausführung externer Aktionen.

## Secrets / Storage / Backups
Environment außerhalb Git setzen, `.env` und SQLite durch OS-Rechte schützen. Auf Datenträgerverschlüsselung und Backupzugriff achten. Rotation erfordert Neustart. [Konfiguration](../19-operations/configuration.md), [Backup/Recovery](../19-operations/operations.md). Logs niemals mit Authorization-Headern sammeln.

## Audit / Monitoring / Security
Reviewer kann Audit paginiert lesen. Domainwrites und Audit atomar; keine Nachweise über abgewiesene Logins, keine fälschungssichere Logkette. Health, Disk und Ressourcen extern überwachen. [Threat Model](../../THREAT_MODEL.md) vor Exposition lesen. Fehlender Ingress-/Security-Nachweis blockiert Produktion.

## Devices / Workers / Cloud
Nicht implementiert. Keine USB-Rechte, privilegierten Container, SSH-Schlüssel, MQTT-Broker oder Cloud-Credentials hinzufügen, um nicht vorhandene Features „zu aktivieren“. Es existiert keine solche Konfiguration. Die optionale `ATZE_SD_ROOT` ist lediglich eine lokal provisionierte Speicherwurzel, kein Device-Adapter.
