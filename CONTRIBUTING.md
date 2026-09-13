# Contribution

Vor Änderungen [Baseline](PROJECT_BASELINE.md), [Entwicklungsablauf](DEVELOPMENT.md) und [Security](SECURITY.md) lesen. Kleine überprüfbare Änderungen mit Tests, aktualisierten Dokumenten und ehrlichen Nachweisen einreichen. Keine echte Hardware ohne ausdrückliche Erlaubnis verwenden. Kein Commit von `.env`, Messdaten mit Personenbezug oder Credentials.

PR-Beschreibung: Zweck, implementierter Umfang, Tests und tatsächliche Ergebnisse, Risiken, Migration, nicht geprüfte Bereiche. CI und generierte Dokumentation müssen konsistent sein. Lizenz ist noch nicht festgelegt; der Eigentümer muss vor externer Distribution entscheiden.

## Verbindliche Realitätsprüfung v0.2.1
[REALITY_POLICY](REALITY_POLICY.md) gilt für jeden Beitrag. Keine Mock-/Demo-/Fake-Provider oder unbemerkten Fallbacks im Betriebsweg. Tests/Fehler-Injektionen bleiben getrennt; `python scripts/reality_check.py` und `python scripts/smoke.py --allow-fixtures` tatsächlich ausführen. Der Smoke startet ausschließlich seine eigene temporäre Testinstanz. Laufreports beweisen keine Geräte-/Providerintegration. [Getrennte Integrationsnachweise](docs/17-security/reality-audit.md).
