# TODO — unvollständige, fehlerhafte und fehlende Teile

Stand 2026-09-14. Basis: Branch `arena/01a09e11-atze-plana`, Commit `f1ed5dd`. Diese Liste ist eine **Arbeitsliste**, kein Statuszertifikat und keine Erfolgsmeldung. Verbindlich bleibt [REALITY_POLICY](REALITY_POLICY.md): Implemented / Configured / Tested / Validated / Production Ready werden getrennt bewertet, fehlende Adapter bleiben BLOCKED.

## Tatsächlich ausgeführte Prüfgrundlage dieser Liste

| Prüfung | Befehl | Ergebnis |
|---|---|---|
| Unit-/Integration-/Security-Suite | `python -m pytest -q --cov=app --cov-report=term-missing` | **169 passed**, 2 bekannte Warnungen, 98 % App-Coverage, 42 nicht überdeckte Statements |
| Dokumentations-/OpenAPI-Konsistenz | `python scripts/docs.py --check` | PASS (4 generierte Produkte, 9 Envvariablen) |
| Realitäts-Grenzprüfung | `python scripts/reality_check.py` | PASS (enges AST-/Smoke-Gate, kein semantischer Beweis) |
| OpenAPI-Vertragsabgleich | eigener Abgleich `openapi.yaml` ↔ Routendekorationen | 43 Pfade; **16 Operationen ohne `x-role`/`x-side-effects`** |
| Defektprobe Schema-only-Modus | `create_app(schema_only=True)` + `GET /health` | **AttributeError** (`'NoneType' object has no attribute 'connect'`) |

Nicht ausgeführt und deshalb hier ausdrücklich **nicht** als Ergebnis behauptet: Browser-E2E, HTTP-/Worker-Smoke, Paketbuild, Android-Build, lokale Modell-CI, Lasttest, Deployment. Diese Gates stehen in [TEST_REPORT](TEST_REPORT.md), [APK_RELEASE_REPORT](APK_RELEASE_REPORT.md) und [FINAL_VALIDATION_REPORT](FINAL_VALIDATION_REPORT.md).

Legende: `P1` = korrektheits-/sicherheitsrelevant, vor jedem Release. `P2` = Vollständigkeit/Bedienbarkeit. `P3` = Zielplattform, benötigt externe Ressourcen (Hardware, Credentials, Autorisierung).
Status nach Policy: `DEFECT` (nachvollziehbarer Fehler im vorhandenen Code), `PARTIAL` (teilweise implementiert), `MISSING` (Funktion fehlt im vorhandenen Modul), `NOT IMPLEMENTED` (kein Adapter/Workflow), `BLOCKED` (externe Voraussetzung fehlt).

---

## A. Konkrete Code-Defekte und Robustheitslücken

- [ ] **TODO-001 · `GET /health` bricht im Schema-only-Modus ab** — `DEFECT` · P2
  - Nachweis: `create_app(schema_only=True)` setzt `store = None`; `health()` nutzt `db=DB` → `AttributeError: 'NoneType' object has no attribute 'connect'` (in dieser Session reproduziert). [app/main.py](app/main.py) Zeilen 26–30, 77–80.
  - Warum relevant: [docs/19-operations/configuration.md](docs/19-operations/configuration.md) dokumentiert `schema_only=True` als legitimen Betriebsweg für die OpenAPI-Erzeugung; jeder Health-Check dagegen liefert 500 statt einer ehrlichen Antwort.
  - Fertig, wenn: Health im Schema-only-Modus einen expliziten Nicht-Betriebszustand (z. B. `SCHEMA_ONLY`) liefert oder die Route dort nicht registriert wird; Regressionstest ergänzt; Dokumentation synchron aktualisiert.

- [ ] **TODO-002 · 16 API-Operationen ohne Rollen-/Nebeneffekt-Vertrag** — `PARTIAL` · P1
  - Nachweis: eigener Abgleich gegen [openapi.yaml](openapi.yaml) — `GET /health`, `GET /api/runtime`, `GET /api/openapi.json`, `POST/GET /api/projects`, `POST/GET /api/evidence`, `GET /api/evidence/{id}`, `POST /api/evidence/{id}/review`, `POST/GET /api/tasks`, `POST /api/tasks/{id}/triage`, `POST /api/tasks/{id}/approve`, `GET/POST /api/control/stop`, `GET /api/audit` tragen kein `x-role`/`x-side-effects`.
  - Warum relevant: Alle neueren Module (PLAN, AI, MCP, Challenge, Context) deklarieren den Vertrag explizit; der Kern verlässt sich stattdessen auf hartkodierte Spezialfälle in [scripts/docs.py](scripts/docs.py) Zeilen 42–68. Rollen-/Effektaussagen sind damit an zwei Stellen definiert und können auseinanderlaufen.
  - Fertig, wenn: alle `/api/`- und `/health`-Operationen den Vertrag deklarieren, `scripts/docs.py` die Fallback-Sonderfälle verliert und `python scripts/docs.py` neu generiert + `--check` PASS liefert.

- [ ] **TODO-003 · `stop_revision` wird aus Audit-IDs abgeleitet** — `PARTIAL` · P1
  - Nachweis: [app/plan_service.py](app/plan_service.py) Zeile 79 liest `latest(db,'audit','event','control.stop_changed')`; [THREAT_MODEL](THREAT_MODEL.md) hält fest, dass Audit weder kryptografisch verkettet noch gegen DB-Administratoren geschützt ist.
  - Warum relevant: Eine zentrale Staleness-/Invalidierungsgröße für PLAN, Challenge und Adoption hängt an einer Tabelle, die laut eigenem Threat Model manipuliert werden kann.
  - Fertig, wenn: Stop-Revision aus einer dedizierten, monotonen Control-Tabelle (mit Actor, Zeitstempel, Revision) stammt und Manipulations-/Negativtests ergänzt sind.

- [ ] **TODO-004 · `plan_service.status()` ohne Guard für fehlende Version** — `DEFECT` (latent) · P2
  - Nachweis: [app/plan_service.py](app/plan_service.py) Zeilen 138–142 greifen auf `version['id']` zu, ohne `version is None` zu prüfen. Über die API derzeit nicht erreichbar (`create_plan` schreibt Version atomar), aber jeder künftige Pfad/Teilfehler erzeugt 500 statt `BLOCKED`.
  - Fertig, wenn: `None`-Fall als expliziter `BLOCKED`-Zustand mit Grund behandelt und getestet ist.

- [ ] **TODO-005 · Evidence-Text ist nicht durchsuchbar** — `MISSING` · P1
  - Nachweis: `index_text()` wird nur aus `create_memory`, `adopt_result`, `storage.archive` und `reindex` (archive/memory) aufgerufen — [app/context.py](app/context.py) Zeile 23, [app/challenge_service.py](app/challenge_service.py) Zeile 154, [app/storage.py](app/storage.py) Zeile 153, [app/context_api.py](app/context_api.py) Zeile 97. `POST /api/evidence` indiziert nichts.
  - Warum relevant: Die UI-Sektion „Projektkontext durchsuchen“ ([app/static/index.html](app/static/index.html)) verspricht Quellensuche; Evidence-Originaltexte (max. 20 000 Zeichen) sind für FTS unsichtbar. `reindex` kann sie ebenfalls nicht nachziehen, weil es nur `archive`/`memory` selektiert.
  - Fertig, wenn: Evidence-Inhalt indiziert wird (oder die UI/Doku die Grenze ausdrücklich und sichtbar nennt), `reindex` den Typ einschließt und Retrieval-Tests Evidence-Treffer prüfen.

- [ ] **TODO-006 · Retrieval rechnet pro Treffer komplette Challenge-Snapshots neu** — `PARTIAL` · P2
  - Nachweis: [app/context.py](app/context.py) Zeilen 56–68: pro Treffer Einzelabfragen für jede Evidence-Referenz plus `decide_task()` (inkl. Snapshot-Hashing) für Decision-Memory; bis zu 30 Treffer je Query ([app/context_models.py](app/context_models.py) Zeile 83).
  - Warum relevant: Semantisch gewollt (Aktualität statt Cache), aber ohne Messung/Begrenzung; [docs/18-deployment/free-tier.md](docs/18-deployment/free-tier.md) nennt SQLite-Serialisierung als Engpass. Kein Lasttest vorhanden.
  - Fertig, wenn: Batch-Abfragen statt N+1, dokumentierte Obergrenze und ein tatsächlicher Messwert (keine Schätzung) vorliegen.

- [ ] **TODO-007 · Listen haben keine Gesamtanzahl/Paginierungsmetadaten** — `MISSING` · P2
  - Nachweis: [app/store.py](app/store.py) Zeile 71 `listing()` liefert nur `limit`/`offset`; alle 8 Listenendpunkte ohne Total. UI-Fußzeile: „Listen zeigen maximal 100 Einträge“.
  - Fertig, wenn: Paginierungsinformation (oder dokumentierter Cursor) verfügbar ist und UI/Doku sie nutzen.

- [ ] **TODO-008 · `POST /api/control/stop` antwortet mit dem Eingabekörper** — `PARTIAL` · P2
  - Nachweis: [app/main.py](app/main.py) Zeilen 163–167 gibt `body` zurück; `Stop` erbt nur `active`/`reason` ([app/models.py](app/models.py) Zeilen 122–128). Kein Actor, kein Zeitstempel, keine Revision — wer wann gestoppt hat, ist nur über das reviewer-only Audit sichtbar.
  - Fertig, wenn: Stop-Zustand Actor/Zeitstempel/Revision trägt und beide Endpunkte dasselbe Modell liefern.

- [ ] **TODO-009 · Inkonsistente `created_by`-Typisierung** — `PARTIAL` · P3
  - Nachweis: `Task.created_by: str` ([app/models.py](app/models.py) Zeile 89) vs. `Result.created_by: Literal['operator']` ([app/challenge_models.py](app/challenge_models.py) Zeile 39).
  - Fertig, wenn: einheitliche Rollentypisierung über alle erzeugten Records.

- [ ] **TODO-010 · 42 nicht überdeckte Statements; Worker-Kern kaum unitgetestet** — `PARTIAL` · P1
  - Nachweis (Coverage-Lauf dieser Session):
    | Modul | Coverage | Nicht überdeckt |
    |---|---|---|
    | [app/challenge_worker.py](app/challenge_worker.py) | **42 %** | Zeilen 28–40, 44–60, 64 — HTTP-Claim/Complete-Pfad, CLI-Argumentprüfung, Pollschleife, Exit-Codes |
    | [app/mcp_client.py](app/mcp_client.py) | 94 % | 60, 62, 70, 76, 81, 91, 96 |
    | [app/storage.py](app/storage.py) | 98 % | 45, 63–64, 77 |
    | [app/ai_gateway.py](app/ai_gateway.py) | 99 % | 39 (ungültiger Port) |
    | [app/ai_service.py](app/ai_service.py) | 99 % | 95 (`PLAN_CONTEXT_CHANGED`) |
    | [app/mcp_api.py](app/mcp_api.py) | 98 % | 61 (`MCP_POLICY_CHANGED`) |
  - Warum relevant: Der Worker ist das Pflichtgate jeder Freigabe; sein reales Transport-/CLI-Verhalten wird nur im separaten HTTP-Smoke geübt, nicht in der Regressionssuite. Zwei Gate-Zweige (`PLAN_CONTEXT_CHANGED`, `MCP_POLICY_CHANGED`) sind unbeobachtet.
  - Fertig, wenn: Worker-Transport gegen einen echten lokalen Loopback-Peer, CLI-Validierung und beide Gate-Zweige in `tests/` regressionsgeprüft sind; Coverage-Bericht neu ausgeführt.

---

## B. Unvollständige API-Oberfläche und Attribute

- [ ] **TODO-020 · Geschriebene Recordarten ohne Lesezugang** — `MISSING` · P1
  - Nachweis: 20 Recordarten werden geschrieben, nur 8 sind listenbar (`ai_model, archive, audit, evidence, memory, project, result, task`); Einzel-GET existiert für `evidence`, `ai_request`, `ai_attempt`, `archive/content`, `cache/content`.
  - Ganz ohne API-Leseweg: `approval`, `mcp_discovery`, `plan_lock`, `plan_revocation`, `cache` (Metadaten), `challenge_job`/`challenge_report` (nur indirekt über `/api/results/{id}/why`), `ai_policy` (nur als Bestandteil von `/api/ai/status`), `ai_request` (keine Liste offener Anfragen).
  - Warum relevant: Freigaben, Sperren, Widerrufe und Discovery-Versuche sind nur über Audit rekonstruierbar; Operator/Reviewer können den eigenen Zustand nicht vollständig abfragen.
  - Fertig, wenn: je Recordart ein read-only Endpunkt (mit Rolle/Nebeneffekt-Vertrag) existiert, OpenAPI/APIs.md neu generiert sind und Tests die Rollengrenzen prüfen.

- [ ] **TODO-021 · Keine Einzel-GETs für Task, Project, Plan, Result** — `MISSING` · P2
  - Nachweis: einzige Einzel-GETs laut OpenAPI sind `/api/evidence/{id}`, `/api/ai/requests/{id}`, `/api/ai/attempts/{id}`. Die UI behilft sich mit `plans/{id}/versions?limit=1` ([app/static/app.js](app/static/app.js) Zeile 168).
  - Fertig, wenn: `GET /api/tasks/{id}`, `GET /api/projects/{id}`, `GET /api/plans/{id}`, `GET /api/results/{id}` vorhanden, dokumentiert und getestet sind.

- [ ] **TODO-022 · Keine Request-Größen-, Rate- und Timeout-Begrenzung in der App** — `MISSING` · P1
  - Nachweis: [docs/08-network/APIs.md](docs/08-network/APIs.md) „No application rate limiter“; [THREAT_MODEL](THREAT_MODEL.md) „Request wird vor Feldvalidierung gelesen; Reverse Proxy erforderlich“; [SECURITY](SECURITY.md) nennt fehlende Rate-Limits als ungelöstes Risiko. Kein entsprechendes Middleware-Element in [app/main.py](app/main.py).
  - Fertig, wenn: Body-Limit und Rate-Limit entweder implementiert oder ein konkret geprüfttes Ingress-Deployment dokumentiert ist (Konfiguration allein genügt nicht, siehe Policy-Achse Configured ≠ Validated).

- [ ] **TODO-023 · Security-Header unvollständig** — `PARTIAL` · P1
  - Nachweis: [app/main.py](app/main.py) Zeilen 60–67 setzen `X-Content-Type-Options`, `Referrer-Policy`, `Cache-Control`, CSP. Es fehlen `frame-ancestors`/`X-Frame-Options` (Clickjacking), `Strict-Transport-Security`, `Permissions-Policy`; `form-action` ist nicht begrenzt.
  - Fertig, wenn: Header-Satz ergänzt und per Test auf tatsächliche Antworten geprüft ist.

- [ ] **TODO-024 · Keine Auditierung fehlgeschlagener Authentifizierung** — `MISSING` · P1
  - Nachweis: `actor()` wirft 401/403 ohne Audit-Eintrag ([app/main.py](app/main.py) Zeilen 37–52); [SECURITY](SECURITY.md) führt „Auditierung fehlgeschlagener Logins“ als ungelöst.
  - Fertig, wenn: fehlgeschlagene Token-/Rollenprüfungen protokolliert werden, ohne Tokenmaterial zu speichern, plus Negativtest.

- [ ] **TODO-025 · Kein DB-Migrationsmechanismus** — `MISSING` · P1
  - Nachweis: [app/store.py](app/store.py) Zeilen 27–41 nutzt ausschließlich `CREATE TABLE IF NOT EXISTS`; keine Schema-Versionstabelle. [docs/00-overview/roadmap.md](docs/00-overview/roadmap.md) führt „Migrationen“ als offenen Punkt; [RELEASES](RELEASES.md) sagt ausdrücklich keinen datenbewahrenden Downgrade zu.
  - Fertig, wenn: versionierte, getestete Migrationen (vorwärts, mit geprüftem Restore) existieren.

- [ ] **TODO-026 · Freigaben haben keine Ablaufzeit** — `MISSING` · P1
  - Nachweis: [SECURITY](SECURITY.md): „allgemeine zeitliche Expiry fehlt. Vor Einführung von Executoren muss das korrigiert und getestet werden.“ `Approval` trägt nur `created_at` ([app/models.py](app/models.py) Zeilen 112–119).
  - Fertig, wenn: zeit-/zielgebundene Gültigkeit implementiert und gegen Staleness getestet ist — zwingend vor jedem Executor.

- [ ] **TODO-027 · Kein Permission-Lease-Modell** — `NOT IMPLEMENTED` · P1 (Vorbedingung für Tools/Executor)
  - Nachweis: [docs/00-overview/master-acceptance.md](docs/00-overview/master-acceptance.md): „no full Allow Once/Task/Workflow/Temporary/Revoke permission-lease engine“; [FINAL_VALIDATION_REPORT](FINAL_VALIDATION_REPORT.md) nennt Permission-Leases als nächstes offenes Gate.
  - Fertig, wenn: widerrufbare, ablaufende, zielgebundene Leases mit Audit und isolierten Negativtests laufen.

---

## C. Dashboard / Benutzeroberfläche

- [ ] **TODO-040 · UI deckt 13 von 43 Endpunkten ab** — `PARTIAL` · P2
  - Nachweis: [app/static/app.js](app/static/app.js) ruft `projects, evidence, tasks, control/stop, storage/health, runtime, results, ai/status, plans, archive, memory, context/query, ai/policy` sowie `evidence/{id}`, `results/{id}/why`, `results/{id}/challenge`, `tasks/{id}/triage`, `plans…versions/status/locks`, `plan-locks/{id}/revoke` auf.
  - Ohne UI-Zugang (nur API): Evidence-Erfassung und -Review, Task-Erfassung, Approval, Result-Einreichung, Adoption, Memory-/Archive-/Cache-Erfassung, Cache-Cleanup, Relocation, Reindex, AI-Modellregister, AI-Request/Run, MCP-Discovery, Audit-Ansicht.
  - Teilweise dokumentiert ([docs/user/getting-started.md](docs/user/getting-started.md)); die Lückenliste selbst ist nirgends vollständig geführt.
  - Fertig, wenn: entweder die fehlenden Bedienschritte umgesetzt sind oder eine vollständige, geprüfte „API-only“-Matrix in der Benutzerdokumentation steht.

- [ ] **TODO-041 · Browser-E2E prüft nur den PLAN-Pfad** — `PARTIAL` · P1
  - Nachweis: [scripts/browser_plan.cjs](scripts/browser_plan.cjs) enthält 7 Prüfungen, alle PLAN-bezogen; CI-Schritt „Real sandboxed Chromium PLAN UI“ in [.github/workflows/validate.yml](.github/workflows/validate.yml). Challenge-, AI-, Storage-, Login-/Logout- und Fehlerpfade laufen nicht im Browser.
  - Fertig, wenn: E2E die übrigen implementierten Oberflächenpfade (inkl. Ladefehler/Empty-States) real ausführt und Ergebnisse im Report stehen.

- [ ] **TODO-042 · Kein versionierter Screenshot / keine öffentliche Vorschau** — `MISSING` · P3
  - Nachweis: [README](README.md): „Noch kein versionierter Screenshot und kein öffentliches Deployment.“
  - Fertig, wenn: echte, commitgebundene Ansichtsnachweise vorhanden sind (keine Mockups).

---

## D. Test-, Build- und CI-Lücken

- [ ] **TODO-050 · Kein Lint/Typecheck** — `MISSING` · P2
  - Nachweis: [pyproject.toml](pyproject.toml) enthält weder `ruff`/`flake8` noch `mypy`; [.github/workflows/validate.yml](.github/workflows/validate.yml) hat keinen entsprechenden Schritt. [docs/00-overview/master-acceptance.md](docs/00-overview/master-acceptance.md): „lint/typecheck … not inferred from pytest“.
  - Fertig, wenn: konfigurierte, in CI ausgeführte Lint-/Typprüfung mit tatsächlichem Laufergebnis.

- [ ] **TODO-051 · Runtime- und Entwicklungsabhängigkeiten nicht getrennt** — `PARTIAL` · P2
  - Nachweis: [requirements.lock](requirements.lock) mischt Runtime (`fastapi`, `uvicorn`, `pydantic`) mit Werkzeugen (`pytest`, `coverage`, `build`, `pip-audit`, `pip_api`); [pyproject.toml](pyproject.toml) deklariert nur `fastapi`/`uvicorn` und keine Dev-Extras. [docs/18-deployment/free-tier.md](docs/18-deployment/free-tier.md) warnt vor parallelen Builds/Tests auf knappem RAM.
  - Fertig, wenn: getrennte Runtime-/Dev-Sets (Extras oder zweite Lockdatei) und ein schlanker Produktionsinstallationsweg dokumentiert und getestet sind.

- [ ] **TODO-052 · Kein reproduzierbarer Build-Nachweis** — `PARTIAL` · P2
  - Nachweis: [FINAL_VALIDATION_REPORT](FINAL_VALIDATION_REPORT.md): sdist-`tar.gz`-Bytes unterscheiden sich trotz `SOURCE_DATE_EPOCH` (Archivmetadaten); „Kein vollständig bitreproduzierbares Release behauptet“.
  - Fertig, wenn: entweder Reproduzierbarkeit erreicht oder die Abweichung als akzeptierte, begründete Grenze in den Release-Gates festgehalten ist.

- [ ] **TODO-053 · Kein automatisierter Gesamt-Backup-/Restore-Test** — `MISSING` · P1
  - Nachweis: [scripts/backup.py](scripts/backup.py) sichert ausschließlich SQLite („Archive/cache blob roots are NOT included“); kein Restore-Skript im Repo. [RELEASES](RELEASES.md): „vollständiger konsistenter Multi-Tier-Backup-/Restore-Nachweis vor Produktion. Das SQLite-Backup allein genügt nicht.“
  - Fertig, wenn: Backup + Restore über DB **und** alle Objektwurzeln (inkl. Modusmarker) als real ausgeführter, geprüfter Ablauf existiert.

- [ ] **TODO-054 · Kein Last-/2-GB-/Retention-Nachweis** — `NOT IMPLEMENTED` · P1
  - Nachweis: [docs/18-deployment/free-tier.md](docs/18-deployment/free-tier.md) enthält ein Planungsbudget, ausdrücklich „keine Messwerte oder Zusage“; kein Cleanup-Daemon, keine automatische Retention, keine Orphan-GC ([app/storage.py](app/storage.py) Docstring).
  - Fertig, wenn: gemessene Werte (RAM, Latenz, parallele Clients, OOM-/Disk-Verhalten) und automatische Retention/Cleanup vorliegen.

- [ ] **TODO-055 · Verifikationsartefakte liegen nicht im Repo** — `PARTIAL` · P3
  - Nachweis: `.gitignore` schließt `reports/*` aus; nur [reports/README.md](reports/README.md) bleibt. Alle PASS-Aussagen in den Root-Reports verweisen auf lokale/CI-Artefakte.
  - Fertig, wenn: Entscheidung getroffen ist, welche Artefakte (Hashes, JUnit-Zusammenfassung) commitgebunden nachweisbar sein sollen — ohne Betriebsdaten zu publizieren.

---

## E. Security- und Identitäts-Gates

- [ ] **TODO-060 · Keine individuelle Identität, kein MFA, keine Session-Revocation** — `NOT IMPLEMENTED` · P1
  - Nachweis: [SECURITY](SECURITY.md) „Geteilte Rollen sind keine individuelle Identität … Keine MFA, Session-Revoke, per-project ACL“; [THREAT_MODEL](THREAT_MODEL.md) „gleicher Mensch kann beide Secrets besitzen“.
  - Fertig, wenn: Benutzer-/Rollenmodell mit Widerruf und getesteter Trennung existiert.

- [ ] **TODO-061 · Keine Tenant-/Projektgrenze** — `MISSING` · P2
  - Nachweis: [THREAT_MODEL](THREAT_MODEL.md) „beide Rollen sehen alle Projekte, keine Tenant-Grenze“.
  - Fertig, wenn: projektbezogene ACL oder ausdrückliche, geprüfte Ein-Workspace-Grenze im Betriebsmodell.

- [ ] **TODO-062 · Audit nicht manipulationssicher** — `MISSING` · P1
  - Nachweis: [THREAT_MODEL](THREAT_MODEL.md) „nicht kryptografisch verkettet, keine externe Senke“; DB-Administratoren können Auditdaten ändern ([SECURITY](SECURITY.md)).
  - Fertig, wenn: Hash-Kette oder externe, schreibgeschützte Senke plus Negativtests.

- [ ] **TODO-063 · Daten unverschlüsselt at rest** — `MISSING` · P1
  - Nachweis: [SECURITY](SECURITY.md) „Archive, FTS und Memory liegen unverschlüsselt auf Disk“; [FINAL_VALIDATION_REPORT](FINAL_VALIDATION_REPORT.md) „Legacy Memory/Cache/Core DB nicht verschlüsselt-at-rest; keine globale Secretcachegarantie“.
  - Fertig, wenn: Verschlüsselung (oder ausdrücklich autorisiertes Restrisiko mit Kompensation) für DB, Archive, Cache und Secretcache.

- [ ] **TODO-064 · Secret-Erkennung nur muster-/bekannt-tokenbasiert** — `PARTIAL` · P1
  - Nachweis: [app/ai_gateway.py](app/ai_gateway.py) Zeilen 20–27 (fünf Regexmuster) und Zeilen 64–68 (bekannte Tokens); eigener Kommentar: „Conservative rejection, not a complete semantic DLP classifier“; [docs/02-core/model-gateway.md](docs/02-core/model-gateway.md) nennt kodiert/base64-Secrets als offen.
  - Fertig, wenn: Erweiterung um kodierte/entropiebasierte Erkennung oder dokumentierte, autorisierte Grenze mit zusätzlichem Review-Schritt.

- [ ] **TODO-065 · Kein universeller Egress-/OS-Lock** — `NOT IMPLEMENTED` · P1
  - Nachweis: [AGENTS.md](AGENTS.md) und [REALITY_POLICY](REALITY_POLICY.md): Python-Gateway ist „KEIN universeller OS-/Netzwerkbeweis“; Challenge-Control-Transport separat; MCP-/Agent-Tools fehlen; kein isolierter Executor ([docs/00-overview/roadmap.md](docs/00-overview/roadmap.md) Bereich 13).
  - Fertig, wenn: authentifiziertes TLS-/Egress-Gateway, Filesystem-/Syscall-Isolation und Escape-Abnahme real getestet sind.

- [ ] **TODO-066 · Kein unabhängiger Security-Audit/Pentest** — `NOT IMPLEMENTED` · P1
  - Nachweis: [THREAT_MODEL](THREAT_MODEL.md) „Kein Penetrationstest, kein Secret-Scanner-Vollscan der gesamten Git-Historie“; [SECURITY](SECURITY.md) „kein dedizierter Security-Kontakt oder SLA festgelegt“.
  - Fertig, wenn: externer Audit, Historien-Scan und definierter Meldekanal (inkl. `security.txt`) vorhanden sind.

- [ ] **TODO-067 · Keine Lizenz** — `MISSING` · P1 (blockiert Distribution)
  - Nachweis: kein `LICENSE`-Datei im Repo; [README](README.md): „Eine Lizenzentscheidung des Repository-Eigentümers ist vor externer Distribution erforderlich.“
  - Fertig, wenn: Eigentümerentscheidung getroffen und Datei ergänzt ist. **Nicht vom Agenten zu erfinden.**

---

## F. Teilweise implementierte Module — was genau fehlt

- [ ] **TODO-070 · Challenge: keine echte Unabhängigkeit** — `PARTIAL` · P1
  - Nachweis: [docs/02-core/challenge-worker.md](docs/02-core/challenge-worker.md): Worker und Server verwenden **denselben** versionierten Regelcode; „organisatorische Unabhängigkeit, getrennte Modelle und unabhängige Online-Suchprovider sind nicht implementiert“; „Getrennte Prozesse auf demselben Entwicklungsnutzer sind KEINE OS-/Sandbox-Isolation“.
  - Zusätzlich: ACCEPT gilt ausschließlich für `submitted_structured_claims_only` ([app/challenge_models.py](app/challenge_models.py) Zeile 57); keine Einheitenumrechnung, keine freie Mathematik, keine Semantik-/Kausalitätsprüfung ([app/challenge_rules.py](app/challenge_rules.py)).
  - Fertig, wenn: getrennte Accounts/Secrets/Deployment, ein wirklich unabhängiger Prüfkanal (zweiter Regel-/Modellsatz oder geprüfte externe Quelle) und Abnahmetests.

- [ ] **TODO-071 · Modell-Gateway: fünf Provider-Verträge ohne Implementierung** — `PARTIAL` · P1
  - Nachweis: [app/ai_models.py](app/ai_models.py) Zeilen 67–88 deklarieren `ModelProvider`, `AgentProvider`, `EmbeddingProvider`, `VisionProvider`, `SpeechProvider`, `RerankerProvider` als `Protocol`; implementiert ist nur `OpenAICompatibleProvider` (ein Text-HTTP-Pfad, [app/ai_gateway.py](app/ai_gateway.py) Zeilen 111–119).
  - Ebenso offen: Modell-Discovery, Revision-/Lizenzattestation, Ressourcen-/Kostenplanung, Offloading, harter Gesamtdeadline ([docs/02-core/model-gateway.md](docs/02-core/model-gateway.md) Zeile 43; Socket-Timeout 15 s ist keine Deadline).
  - Fertig, wenn: je Modalität ein realer, getesteter Provider oder die ausdrückliche Rücknahme des Vertrags aus Code/Doku.

- [ ] **TODO-072 · Kein operativer lokaler Modellworker** — `NOT IMPLEMENTED` · P1
  - Nachweis: [docs/14-testing/local-model-validation.md](docs/14-testing/local-model-validation.md) und [validation/local-model.lock.json](validation/local-model.lock.json) sind CI-gebunden; [docs/17-security/reality-audit.md](docs/17-security/reality-audit.md): „HF Local Model … NO live installation/integration, NOT CONFIGURED, NOT RUN, BLOCKED“.
  - Fertig, wenn: gepinnte Gewichte/Runtime lokal betrieben, Inferenz real ausgeführt und als Betriebsweg abgenommen ist.

- [ ] **TODO-073 · MCP: nur Discovery, kein Toolaufruf** — `PARTIAL` · P2
  - Nachweis: [app/mcp_api.py](app/mcp_api.py) `tool_execution: 'NOT_IMPLEMENTED'`; [docs/22-mcp/brightdata.md](docs/22-mcp/brightdata.md): OAuth-**Login/Refresh fehlt**, keine `tools/call`-Ausführung, keine Live-Provider-Abnahme; persistierte `mcp_discovery`-Records sind über keine API lesbar (siehe TODO-020).
  - Fertig, wenn: Tool-Vertrag mit Permission-Lease, Sandbox und realem Providertest — sonst ausdrücklich als Dauerzustand dokumentiert.

- [ ] **TODO-074 · PLAN: kein universeller Kontext** — `PARTIAL` · P2
  - Nachweis: [docs/21-plan/context-lock.md](docs/21-plan/context-lock.md) und [FINAL_VALIDATION_REPORT](FINAL_VALIDATION_REPORT.md): nur 1–16 Evidence-/Memory-/Text-Archivquellen, 1 MiB-Grenze ([app/plan_service.py](app/plan_service.py) Zeile 7), keine PDF/CAD/3D/Binär-/Device-/Research-/Repair-Engines, kein Object Workspace/Executor; Filesystem+SQLite ohne gemeinsamen atomaren Commit.
  - Fertig, wenn: weitere Quellentypen mit echtem Parser/Hash-Nachweis oder bestätigte Grenze.

- [ ] **TODO-075 · Storage: keine Remote-/Cloud-/RAM-Tiers, kein SD-Hardwarenachweis** — `PARTIAL` · P2
  - Nachweis: [docs/17-security/reality-audit.md](docs/17-security/reality-audit.md): „RAM-/Server-/Cloud-Storage: NO / NOT CONFIGURED / NOT RUN / BLOCKED“; SD-Pfad ist ein Dateisystemadapter ohne Hotplug-/Powerloss-Test; `ATZE_SD_ROOT` wird nicht gemountet/angelegt ([app/storage.py](app/storage.py) Zeilen 32–37).
  - Offen laut [docs/20-context-storage/mobile-roadmap.md](docs/20-context-storage/mobile-roadmap.md): Tier 3/4-Provideradapter, Rebalancing, Quoten, Offline-Queue/Sync, Indexbudgets/Eviction.
  - Fertig, wenn: mindestens ein weiterer Tier real provisioniert, getestet und in Backup/Restore eingebunden ist.

- [ ] **TODO-076 · Android: read-only Statusclient** — `PARTIAL` · P3
  - Nachweis: [android/README.md](android/README.md): einziger Vorgang ist `GET /api/runtime`; kein PLAN-Editor, keine Core-TLS-Live-Session aus der App, kein AAB, keine Produktionssignatur (ephemere Debug-Keys), keine Honeywell-/Repair-/Fastboot-/EDL-Fähigkeit; Emulator ≠ physisches Gerät.
  - Fertig, wenn: autorisierte physische Geräte, geprüfte Release-Signatur und echte Core-Anbindung nachgewiesen sind.

- [ ] **TODO-077 · Evidence: keine Quellenrangfolge/Widerspruchserkennung** — `PARTIAL` · P2
  - Nachweis: [docs/00-overview/roadmap.md](docs/00-overview/roadmap.md) Bereich 16: „keine Quellenrangfolge, automatische Wahrheit/Aktualität oder Widerspruchserkennung“; `observations` sind manuell eingereichte Metadaten ohne Extraktion ([docs/02-core/challenge-worker.md](docs/02-core/challenge-worker.md) Zeile 49); `confidence` ist eine gemeldete, keine gemessene Größe ([app/models.py](app/models.py) Zeile 44).
  - Fertig, wenn: Rangfolgen-/Aktualitäts-/Konfliktmodell mit Tests, ohne Wahrheit zu behaupten.

---

## G. Nicht implementierte Master-Bereiche

Nachweis je Bereich: [docs/00-overview/roadmap.md](docs/00-overview/roadmap.md), [docs/00-overview/master-acceptance.md](docs/00-overview/master-acceptance.md), [docs/17-security/reality-audit.md](docs/17-security/reality-audit.md). Alle Punkte sind `NOT IMPLEMENTED` / `BLOCKED`; keine Dummy-Verzeichnisse anlegen (Policy).

- [ ] **TODO-080 · 04 Agents** — Agent Builder, Runtime, Tool-Registry, Lifecycle. Vorbedingung: Tool→Permission→Task→Triage→Execution-Vertrag plus isolierte Negativtests (TODO-027, TODO-065).
- [ ] **TODO-081 · 05 Devices** — USB/WiFi/BLE/Serial/Discovery/Device Bridge. Vorbedingung: konkreter Gerätevertrag und autorisierte Testgeräte; keine automatischen Scans ohne Freigabe.
- [ ] **TODO-082 · 07 IoT / ESP32 / Telemetrie** — keine gemessenen Spannungs-/Strom-/Drehzahl-/Temperatur-/Drehmomentwerte; keine erfundenen Sensorik.
- [ ] **TODO-083 · 08 Network** — Monitoring, Discovery, MQTT, SSH, Incident-Executor fehlen (eigene HTTP-API ist vorhanden).
- [ ] **TODO-084 · 09 Cloud** — kein Hybrid-/Multi-Cloud-/Edge-/Provider-Adapter, kein Provisioning.
- [ ] **TODO-085 · 10 Web Research** — Bright Data SERP/Scraping/Browser/Crawl/Extraction/PDF/Cache/Rate-Handling; URLs sind bisher nur manuelle Referenzen (`EvidenceInput.source_url`, keine Server-Fetches).
- [ ] **TODO-086 · 11 3D / Unity** — keine Unity-Version, Module, Szenen, Assets, Avatare, Worlds, Digital Twins, kein Editor-/Headless-Build.
- [ ] **TODO-087 · 13 Sandbox-Isolation** — Cache-TTL/Cleanup vorhanden, aber kein Executor und kein isolierter Workspace.
- [ ] **TODO-088 · 15 Trends** — keine Anomalie-, Lifecycle- oder Proaktivitätsengine; kein Trenddatensatz.
- [ ] **TODO-089 · Invasive Aktionen** — `FLASH`, `FIRMWARE`, `EDL_WRITE`, `PRODUCTION_DEPLOY`, `PAYMENT` sind nur Enum-Werte zur Triage ([app/models.py](app/models.py) Zeilen 68–75). **Keine Commands, keine Firmware, keine Zahlung, kein Deploy.** Bleibt BLOCKED bis zu herstellerspezifischen Freigaben, geprüften Images und dem Freigabevertrag aus TODO-026/TODO-027.
- [ ] **TODO-090 · Offline-Sync / Mobile Project Server** — Queue- und Sync-Vertrag laut [docs/20-context-storage/mobile-roadmap.md](docs/20-context-storage/mobile-roadmap.md) definiert, aber nicht implementiert.

---

## H. Release- und Betriebs-Gates

- [ ] **TODO-095 · Kein Deployment / kein Ingress** — `NOT IMPLEMENTED` · P1 — Nachweis: [PRODUCTION.md](PRODUCTION.md), [docs/18-deployment/free-tier.md](docs/18-deployment/free-tier.md) („Kein 2-GB-Lasttest oder Free-Tier-Deployment wurde durchgeführt“), [README](README.md) („kein Deployment, Ingress erforderlich“).
- [ ] **TODO-096 · Kein Tag / GitHub-Release** — `BLOCKED` · P2 — Nachweis: [RELEASES](RELEASES.md): alle Versionen 0.1.0–0.4.0.dev0 „nicht veröffentlicht“; PR/CI ist kein Release.
- [ ] **TODO-097 · Keine automatische Überwachung** — `MISSING` · P2 — Nachweis: [docs/00-overview/roadmap.md](docs/00-overview/roadmap.md) Bereich 19: Runbooks/Health/SQLite-Backup vorhanden, „keine automatische Überwachung oder Backups“.
- [ ] **TODO-098 · Upgrade-/Rollback-Weg nur manuell** — `PARTIAL` · P1 — Nachweis: [RELEASES](RELEASES.md) „PLAN upgrade / rollback“: alle alten Prozesse stoppen, kein Mischbetrieb, kein datenbewahrender Downgrade. Kein Werkzeug/Checklistenskript im Repo.

---

## I. Empfohlene Reihenfolge

1. **Klein, real, sofort prüfbar:** TODO-001, TODO-002, TODO-004, TODO-008, TODO-009, TODO-010, TODO-021 — jeder Punkt mit Test + synchroner Doku/OpenAPI-Regenerierung.
2. **Korrektheits-/Sicherheitskern:** TODO-003, TODO-005, TODO-023, TODO-024, TODO-020, TODO-026.
3. **Betriebsvoraussetzungen:** TODO-025, TODO-053, TODO-054, TODO-022, TODO-062, TODO-063.
4. **Vor jeder Tool-/Agent-/Executor-Arbeit zwingend:** TODO-027, TODO-065, TODO-070.
5. **Nur mit externen, autorisierten Ressourcen:** TODO-072, TODO-073, TODO-075, TODO-076, TODO-080 … TODO-090.
6. **Eigentümerentscheidungen (nicht delegierbar):** TODO-067 Lizenz, TODO-095/096 Deployment und Release, TODO-066 externer Audit.

Jeder erledigte Punkt erfordert laut [AGENTS.md](AGENTS.md): Code + Tests + OpenAPI + Konfiguration + Dokumentation im selben Schnitt, tatsächlich ausgeführte `scripts/docs.py --check`, `scripts/reality_check.py`, pytest, Build und isolierter Smoke — und eine getrennte Bewertung nach Implemented / Configured / Tested / Validated / Production Ready. Ein grüner Teiltest ersetzt kein Plattform-Release.
