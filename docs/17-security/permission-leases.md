# Permission Leases — begrenzte, ablaufende, widerrufbare Vorfreygaben (D5)

Stand 2026-09-15, Baseline 245 ausgeführte Tests PASS vor diesem Inkrement; dieses Inkrement ergänzt 9 Tests (254 PASS). Eine Lease ist eine **vorab erteilte, begrenzte Ausführungserlaubnis** — sie ersetzt ausschließlich die menschliche Einzelfreigabe, **niemals ein technisches Gate**.

## Zweck / Semantik
Die Master-Anforderung nennt Allow Once / Task / Temporary / Revoke als Freigabeform. Eine Lease ist ein Reviewer-Grant mit: **Aktion** (zunächst genau `mcp.tools_call`, der einzige Pfad mit realer Durchsetzung), **Zielbindung** (Task oder Projekt), **optionaler Tool-Bindung** (innerhalb der MCP-Allowlist), **Pflicht-Ablaufzeit** (ISO-8601, max. 24 h TTL), **Nutzungslimit** (max_uses ≤ 100) und **Widerruf**. Der Operator kann damit `POST /api/mcp/brightdata/call` ausführen, **ohne** dass die technischen Gates (Allowlist, Argument-/Result-Grenzen, PUBLIC/Projekt/Region, Privacy/Local-only/Remote, Not-Stop, PLAN-Aktualität) irgendwie beeinflusst werden — sie laufen unverändert weiter. Der Reviewer-Einzelconsent-Pfad bleibt unverändert nebeneinander bestehen.

## Verbrauchs- und Zustandsmodell
- **Verbrauch bei Reservierung:** `uses_count` wird vor dem I/O incrementiert; ein späterer Transportfehler erstattet keine Nutzung (die Erlaubnis wurde ausgeübt, das versuchen ist der Akt).
- **Append-only Speicher:** der gespeicherte Zustand ist `active`/`revoked`; `expired` und `exhausted` werden **berechnet** (`effective_state`), nie still umgeschrieben.
- **Nicht aktiv nutzbare Leases** (abgelaufen/erschöpft/widerrufen) führen beim Operator-Call zu 403 mit explizitem Grund; ohne jede Lease ebenfalls 403 (Default-Deny bleibt erhalten).
- **Stop-Asymmetrie:** Gewähren unter Not-Stop ist blockiert (409); **Widerruf ist unter Not-Stop erlaubt** (risikoreduzierend). Gesperrte Ausführung bleibt in jedem Fall verweigert.
- Audit: `lease.created` / `lease.used` / `lease.revoked`.

## API-Vertrag
| Route | Rolle | Wirkung | Fehler |
|---|---|---|---|
| POST /api/leases | reviewer | Lease gewähren (Scope muss existieren; Tool ∈ Allowlist; Ablauf in Zukunft, TTL ≤ 24 h; max_uses 1–100; reason Pflicht) + Audit | 403, 404 Scope, 422, 409 Stop |
| GET /api/leases, /{id} | both | Lesende Registry inkl. `effective_state`/`uses_remaining` | 401, 404 |
| POST /api/leases/{id}/revoke | reviewer | Bestätigter Widerruf (confirm+reason), unter Stop erlaubt; Daten bleiben erhalten, kein Lösch-Endpunkt | 403, 404, 409 erneut, 422 |
| POST /api/mcp/brightdata/call | reviewer (Einzelfreigabe) **oder** operator (aktive Lease, Verbrauch je Nutzung) | Werkzeugausführung wie im [MCP-Vertrag](../22-mcp/brightdata.md); Operator ohne nutzbare Lease → 403 | s. MCP-Vertrag |

## Grenzen / Nicht implementiert
Leases existieren zunächst **nur** für `mcp.tools_call` — weitere Aktionen (z. B. Agent-Run-Consent, Discovery) dürfen nur nach echter Durchsetzungspflege ergänzt werden; die Action-Liste ist bewusst ein Literal mit einem Wert. Keine Lease für Discovery (Metadaten-Consent bleibt Reviewer-einzeln). Keine Übertragung/Delegation an Dritte, kein „Workflow"-Scope jenseits Task/Projekt, kein automatischer Ablauf-Job (Ablauf wird bei Lese-/Nutzungszeit berechnet). Keine UI (API-only; die [PLAN-UI-Spezifikation](../21-plan/plan-ui-interaction-spec.md) gilt, sobald Oberfläche ergänzt wird). Roadmap 17 Security → PARTIAL erweitert ([Modulmatrix](../00-overview/roadmap.md)); D5 aus [MASTER_ABGLEICH](../../MASTER_ABGLEICH.md) damit geschlossen.
