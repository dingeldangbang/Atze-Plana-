# Validation artifacts

Dieser Ordner enthält lokal erzeugte Test-/Audit-/Smoke-/Buildreports. Nur diese README wird versioniert; tatsächliche Laufreports lädt CI als Artefakte hoch. Keine Produktionsdaten, Tokens oder Gerätebeobachtungen hier committen.

JUnit: individuelle Testfälle, tatsächliche Ergebnisse, Zeiten und Fehler. Coverage: Python-Statements. Dependency-Audit: Advisory-Abgleich. Smoke: tatsächliche HTTP-Antworten mit synthetischen Fixture-IDs, keine externen Aktionen. Reports hängen am geprüften CI-Commit; zusammenfassende Ergebnisse stehen im [Validierungsbericht](../FINAL_VALIDATION_REPORT.md).
