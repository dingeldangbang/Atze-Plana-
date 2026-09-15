# Release-Checkliste — Arbeitsdokument mit Statusregeln je Punkt

Stand 2026-09-15. Arbeitsdokument (Delta D7 aus [MASTER_ABGLEICH](MASTER_ABGLEICH.md)), aufgebaut aus den realen Repo-Disziplinen — nicht aus der Konversation erfunden. **Ein Release erfordert jeden Punkt mit Status DONE (mit Nachweis-Link) oder einer expliziten, begründeten Eigentümerfreigabe für BLOCKED/OPEN.** CONDITIONAL-Punkte blockieren ein Vollplattform-Release, können aber ein begrenztes Inkrement-Release tragen, wenn der Umfang im Release-Hinweis genannt wird.

Statusregeln: **DONE** = Nachweis-Link vorhanden und aktuell · **OPEN** = Arbeit ausständig · **BLOCKED** = externe Voraussetzung (Hardware/Account/Eigentümerentscheidung) fehlt, ehrlich ausgewiesen · **CONDITIONAL** = teilweise erfüllt, Grenze dokumentiert.

## 1. Qualitäts-Gates (alle DONE erforderlich)
| Punkt | Regel | Status | Nachweis |
|---|---|---|---|
| Testsuite | `python -m pytest -q` vollständig PASS, keine xfail-Vertuschung | DONE | CI-Run `validate` ([Status](https://github.com/dingeldangbang/Atze-Plana-/actions)) |
| Dokumentations-Drift | `python scripts/docs.py --check` PASS (OpenAPI/APIs/Testkatalog/Inventory konsistent) | DONE | CI-Run `validate` |
| Realitätsprüfung | `python scripts/reality_check.py` PASS (keine verbotenen Importe/URLs, kein assert-only Smoke) | DONE | CI-Run `validate` |
| HTTP-Smoke | `python scripts/smoke.py --allow-fixtures` PASS gegen frische Wegwerf-Instanz | DONE | CI-Run `validate` |
| Browser-Gate | Echtes Chromium (CDP) gegen die UI in CI, alle Checks PASS | DONE | CI-Run `validate`, Browser-Report im Job-Log |
| CI gesamt | Alle Workflows (`validate`, `universe`, `local-model`, `android`) grün auf dem Release-Commit | DONE | GitHub Actions |

## 2. Abnahme-Dokumente (vorhanden und aktuell)
| Punkt | Regel | Status | Nachweis |
|---|---|---|---|
| Testbericht | [TEST_REPORT.md](TEST_REPORT.md) reflektiert den Release-Stand (historische Abschnitte bleiben unverändert) | CONDITIONAL | Bericht dokumentiert Stand des jeweiligen Inkrements |
| Finale Validierung | [FINAL_VALIDATION_REPORT.md](FINAL_VALIDATION_REPORT.md) nennt offene Gates ehrlich | CONDITIONAL | Siehe Bericht |
| Master-Abnahme | [Master-Matrix](docs/00-overview/master-acceptance.md): jeder Bereich mit Umfang **und** Lücke; Vollplattform-Release bleibt BLOCKED, bis Lücken geschlossen oder Eigentümerfreigabe erteilt | CONDITIONAL | Matrix |
| APK-Bericht | [APK_RELEASE_REPORT.md](APK_RELEASE_REPORT.md) für Android-Artefakte (Debug-Umfang) | CONDITIONAL | Bericht |

## 3. Freigabe-Entscheidungen (Eigentümer, nicht Agentenrecht)
| Punkt | Regel | Status | Nachweis |
|---|---|---|---|
| Release-Signaturschlüssel | Eigentümer stellt Release-Key bereit oder bestätigt Debug-Key-Fallback ausdrücklich | BLOCKED | Ephemerer Debugschlüssel ist der dokumentierte Fallback |
| Lizenz | LICENSE-Datei durch Eigentümer entschieden (Repo erfindet keine Lizenz) | BLOCKED | Offen (Delta D8) |
| Auslieferungsformate | `release/`-Ordner (`app-release.apk`/`.aab`/`checksums.txt`): Eigentümerentscheidung über AAB und Ordnerstruktur | BLOCKED | Inhaltlich gedeckt durch APK-Bericht + SHA256SUMS |
| Produktionsdeployment | Ingress, Domain, Secrets, Free-Tier-/Anbieterkonto: Betreiber stellt bereit; kein Auto-Deployment | BLOCKED | [PRODUCTION.md](PRODUCTION.md) |

## 4. Betriebs-Voraussetzungen
| Punkt | Regel | Status | Nachweis |
|---|---|---|---|
| Backup/Restore | Backup erstellt **und** Restore inklusive Hashprüfung nachgewiesen | OPEN | Wird mit dem Operations-Inkrement geschlossen |
| 2-GB-Rahmen | „2 GB" = Zielhardware-RAM (Honeywell CT45P-XON); kein Lasttest auf dem Gerät durchgeführt | CONDITIONAL | [Free-Tier-Planung](docs/18-deployment/free-tier.md) |
| Not-Stop & Rollback | Stop-Mechanismus getestet; Rollback-/Downgrade-Grenzen dokumentiert (kein Mischbetrieb Alt/Neu) | CONDITIONAL | [Betriebshandbuch](docs/19-operations/operations.md) |

## Regel zur Pflege
Diese Checkliste wird **je Inkrement** aktualisiert; ein Status ohne Nachweis-Link ist ungültig. Ein grünes CI-Badge allein ist keine Release-Freigabe: Die Master-Matrix definiert den Gesamtumfang, diese Checkliste die Freigabefähigkeit des konkreten Artefakts.
