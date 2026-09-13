# Production — CONDITIONAL / nicht freigegeben

Es wurde kein Produktionssystem bereitgestellt. Die aktuelle Implementierung ist ein Single-Workspace-Kern mit geteilten Rollen-Tokens. Sie ist nicht für unkontrollierten öffentlichen Zugriff, Multi-Tenancy oder kritische Geräteaktionen freigegeben.

## Voraussetzungen vor Freigabe
- Explizite menschliche Deployment-Freigabe, Zielhost und Verantwortliche festlegen.
- TLS-Ingress, Zugriffsnetz/VPN, Request-Body-Limit (z. B. 128 KiB), Timeouts und getestete Ratenbegrenzung einrichten. Die App begrenzt Felder, aber nicht die Größe des eingelesenen Requests.
- Dienst unter eigenem unprivilegiertem OS-Nutzer; `umask 077`, lokale persistente SQLite-Datei, kein Docker-Socket/USB/Host-Shell.
- Tokens getrennt verwahren und verteilen, keine Admin-Credentials im Browser unbekannter Herkunft; Rotation erfordert Prozessneustart.
- Backup und Restore auf separatem Datenpfad testen; Monitoring für 503, Speicher, Disk und Response-Latenz.
- Personenbezogene Informationen und sensible Quelltexte nicht ohne Datenschutzkonzept speichern.
- Lizenzentscheidung, Security-Review, Lasttests, Browser-E2E und Rollback-Abnahme nachholen.

## Startprofil (nach Freigabe)
Ein Uvicorn-Worker hinter dem kontrollierten Ingress. Environment durch Secret-Manager oder eine nur dem Dienst lesbare Datei. Absolute `ATZE_DB_PATH`; `uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000 --workers 1`. Keine `--reload`-Option. Forwarded-Header nur von vertrauenswürdigen Proxies akzeptieren; das Proxy-Vertrauensmodell ist deploymentabhängig und hier nicht vorkonfiguriert.

[2-GB-Planung](docs/18-deployment/free-tier.md), [Backups/Recovery](docs/19-operations/operations.md), [Threat Model](THREAT_MODEL.md).
