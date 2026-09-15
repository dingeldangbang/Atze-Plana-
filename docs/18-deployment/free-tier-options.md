# Free-Tier-Optionen — gleichwertige Anschlussmöglichkeiten je Bereich

Stand 2026-09-15. Diese Übersicht benennt je Bereich, **welche Free-Tier-Optionen** (Nutzungs-/Kostenklasse externer Anbieter) es gibt und **welchen exakten Einrichtungspfad** der Core dafür bereits implementiert hat. Alles hier ist **OPTION, kein Anspruch**: Anbieter-Konditionen ändern sich; vor Nutzung die aktuellen Anbieterbedingungen prüfen. Bis ein API-Schlüssel des Eigentümers vorliegt, bleibt jede externe Anbindung **NOT CONFIGURED** — konfiguriert ≠ validiert, und **niemals Free-Tier-Fallback auf Beispieldaten** (Master-Vorgabe, [MASTER_ABGLEICH](../../MASTER_ABGLEICH.md) Bereich 26).

## Bereich KI-Provider — vollständiger Anschlusspfad implementiert

Der Core spricht OpenAI-kompatible `POST {origin}/v1/chat/completions`-Endpoints ([Modell-Gateway-Vertrag](../02-core/model-gateway.md)). Anbieter mit **dauerhaftem Free-Tier ohne Kreditkarte** (Beispiele, Stand der Recherche 2026-09, unverbindlich): **Google AI Studio (Gemini API)**, **Groq**, **Mistral (La Plateforme)**, **OpenRouter (Free-Modelle)**, **Cloudflare Workers AI**, **Cohere**, **Cerebras**, **NVIDIA NIM** — nahezu alle mit OpenAI-kompatiblem Endpoint und teils erheblichen Tages-/Minuten-Limits. SambaNova hat seinen Free-Tier nach aktueller Recherche eingestellt; Vercel AI Gateway verlangt eine Karte.

### Einrichtung (exakter Pfad, alles real implementiert)

1. **Konto + Schlüssel beim Anbieter** (Eigentümerentscheidung; Schlüssel niemals ins Repository): z. B. Groq Console, Google AI Studio, Mistral Console, OpenRouter Keys.
2. **Provider-Datei** (z. B. `/etc/atze/ai-providers.json`) und Umgebungsvariable `ATZE_AI_CONFIG` auf ihren Pfad setzen:
   ```json
   {"providers": [
     {"id": "groq-free", "mode": "EXTERNAL_PROVIDER", "origin": "https://api.groq.com/openai",
      "token_env": "ATZE_AI_TOKEN_GROQ", "region": "groq-free-tier"}
   ]}
   ```
   `token_env` muss dem Muster `ATZE_AI_TOKEN_[A-Z0-9_]+` folgen; der Schlüssel selbst wird nur als Umgebungsvariable `ATZE_AI_TOKEN_GROQ` hinterlegt (nie in Dateien/Logs). Origin-Beispiele OpenAI-kompatibel: Mistral `https://api.mistral.ai`, Google Gemini `https://generativelanguage.googleapis.com/v1beta/openai`, OpenRouter `https://openrouter.ai/api`.
3. **Modell registrieren** (Reviewer): `POST /api/ai/models` mit `provider_id`, `model` (Modellname des Anbieters), `revision` (40–64 Hex — z. B. SHA-1/SHA-256 des Modell-Standes, soweit der Anbieter ihn nennt), `license`, `capabilities` ⊆ analysis/plan/code, `context_length`, `hardware`, `evaluation`, `security_review` (Metadaten sind Reviewer-Angaben, keine Validierung).
4. **Policy-Allowlists** (Reviewer): `POST /api/ai/policy` mit `privacy_lock: false`, `local_only: false`, `allow_remote: true`, `external_ai` je nach Klasse, `providers: ["groq-free"]`, `models: [<modell-id>]`, `projects: [...]`, `tasks`, `data_classes: ["PUBLIC", ...]`, `regions: ["groq-free-tier"]`. Default bleibt **Local-only**; jede externe Klasse muss ausdrücklich allowlisted sein (Default-Deny).
5. **Nutzung mit Consent-Kette**: Operator `POST /api/ai/requests` → Reviewer-Einzelconsent (`context_hash` + Grund) → gebundener Transport; Alternativ für MCP tools/call: Permission-Lease ([Vertrag](../17-security/permission-leases.md)).
6. **Validierung**: die erste echte Anfrage aus der **Zielumgebung** (Netz dort prüfen — die Entwicklungs-Sandbox dieser Reihe hat nachgewiesene Provider-Host-Blockaden; hier bleibt jede externe Anbindung NOT CONFIGURED/NOT VALIDATED). Ausgaben bleiben EXTERNAL_SOURCE, nie verifizierte Wahrheit.

## Bereich Web-Research (Bright-Data-MCP)
Discovery und begrenztes reviewerbestätigtes `tools/call` sind implementiert ([Vertrag](../22-mcp/brightdata.md)). Anschluss: `ATZE_BRIGHTDATA_OAUTH_TOKEN` (OAuth-Access-Token; kein API-Key/Query-URL). Ob der Anbieter ein für dich ausreichendes kostenloses Kontingent bietet, ist eine **Anbieterfrage zum Zeitpunkt der Nutzung** — hier NOT CONFIGURED, keine Netzvalidierung aus dieser Umgebung möglich.

## Bereich Telemetrie — die Gratis-Option läuft bereits
Die Ingestion (`ATZE_TELEMETRY_TOKEN`) braucht **keinen externen Anbieter und keine Kosten**: HTTP-Ingestion ist vollständig lokal implementiert ([Vertrag](../23-telemetry/telemetry.md)). Aktivierung genügt — ohne Token bleibt Ingest inaktiv (403 NOT CONFIGURED).

## Bereich Cloud (09) / Deployment (18)
Free-Tier-Kontingente von Cloud-Anbietern erfordern Konto- und Auslieferungsentscheidungen des Eigentümers (Ingress, Domain, Secrets; [PRODUCTION.md](../../PRODUCTION.md)). Es existiert **kein Cloud-Adapter** (NOT IMPLEMENTED) — bis zur Entscheidung wird nichts vorgetäuscht.

## Lokale Gratis-Optionen (bereits aktiv, ohne externe Kosten)
- **Lokaler Provider-Mode** (`mode: LOCAL`, z. B. Loopback-Endpoint) — Transport real nachgewiesen; ein echtes lokales Modell ist der separate CI-Worker-Nachweis ([lokale Modellvalidierung](../14-testing/local-model-validation.md)).
- **Speicher-Tiers** local/SD — Dateisystem, keine Anbieterkosten ([Storage-Architektur](../20-context-storage/architecture.md)).
- **CLI, Lasttest, Monitoring** — vollständig lokal lauffähig.

## Pflegeregel
Diese Seite wird bei jeder Änderung des Anbietermarkts oder jeder realen Anbindung aktualisiert; ein Anbietername hier ist keine Zusicherung von Konditionen. Sobald ein Schlüssel hinterlegt und aus der Zielumgebung validiert wurde, wandert der Eintrag von OPTION zu CONFIGURED mit Nachweislink.
