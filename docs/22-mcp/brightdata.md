# Bright Data MCP — bounded discovery increment

Design2026-09-14, baseline146 executed tests PASS before changes. Source: complete https://docs.brightdata.com/llms.txt (version2026-09-09.1), remote quickstart and https://docs.brightdata.com/products/mcp-server/remote/oauth.md fetched on2026-09-14. Provider documentation is EXTERNAL_SOURCE, not proof of a configured/tested connection.

## Purpose / explicit non-goals
Implement real Streamable HTTP JSON-RPC initialize → initialized → tools/list, restricted discovery of search_engine/scrape_as_markdown names. **No tools/call, web scraping, searches, model delegation, sampling, elicitation, account creation, zones, dataset purchases, OAuth login/refresh or device proxies.** This is a real bounded MCP client, not a simulated provider or complete MCP/agent platform. Selected names are a local candidate allowlist, never enabled permissions or verified semantics.

## Inputs / configuration / permissions
Configure a short-lived Bright Data **OAuth access token**, resource mcp.brightdata.com / scope mcp, through ATZE_BRIGHTDATA_OAUTH_TOKEN in the server environment/secret management. Never paste it in chat, Git, URL, report or request body. Restart Core after rotation. No refresh token stored. API key and OAuth token are NOT interchangeable: provider docs use query parameters for API keys but Authorization Bearer for OAuth. This client implements only OAuth header delivery, no query-token fallback.

Reviewer POST /api/mcp/brightdata/discover takes task_id, allow_external_discovery=true, reason and optional plan_lock_id. Existing read task with attested preconditions, explicit project allowlist, PUBLIC data class and provider region approval (`brightdata-provider-managed`, an attestation label NOT a residency guarantee) required in AI policy; privacy_lock=false, local_only=false and allow_remote=true. external_ai may remain false; no AI model allowlist is granted. Default policy denies. If provider-managed routing does not meet your residency requirements, do not approve this label. PLAN, when present, must be current; no selected context is transmitted.

Existing reviewer credential is workspace-wide, not identity-verified human presence. Discovery approval is once per API call, not a durable tool lease. Every explicit repetition requires a new reviewer call. GET /api/mcp/brightdata/status is authenticated/read-only and performs no network I/O. Status never treats configured token as valid OAuth or a live provider proof.

## Wire/data/security contract
Fixed https://mcp.brightdata.com/mcp only. TLS≥1.2 with certificate+hostname verification, bearer header, no environment proxy, redirects or fallback. Static client metadata, protocol version2025-06-18 and empty capabilities only; no task/project IDs, source text, reason, model context or system credentials sent. Bounded JSON and SSE response parsing, matching JSON-RPC IDs, no server-request execution, no unsupported version/pagination acceptance. Limits:3 RPC POSTs plus optional session DELETE,512KiB per response,200 tool descriptors, 12-second deadline checked between operations and3-second socket timeouts (OS DNS resolution is not interruptible by this client; not an absolute wall-clock guarantee), no automatic retries of potentially stateful calls. Session header in RAM only, never logs/SQLite; explicit cleanup attempted, unconfirmed cleanup prevents successful discovery.

Response: durable attempt id/state/reason, source=EXTERNAL_SOURCE, fixed candidate names, catalogue hash, allowed_for_action=false. Raw descriptions, schemas, server instructions and tokens never returned/stored. Catalogue hash is integrity/provenance of received metadata, NOT source truth or tool safety. No automatic Evidence/Memory/PLAN write/adoption.

## Transactions / failure / recovery
Attempt and audit commit before external I/O; stop/policy/PLAN checked again under serialized SQLite transaction before sending. Audit failure before reservation means no I/O. Global stop/Privacy Lock blocks new dispatch; cannot recall in-flight traffic or preempt the serialized transaction. Interrupted attempt can remain STARTED and requires operator investigation; never silently retried or marked complete. Failed auth/status/format/bounds/cleanup are explicit BLOCKED/UNAVAILABLE, no partial catalog success. Missing/expired token: configure/rotate securely, then new explicit call; do not disable TLS or substitute an API key URL.

## Validation / limits
Actual transport tests use an explicitly isolated synthetic MCP peer over verified local TLS, not a Bright Data live service or a model. Current live provider test remains NOT CONFIGURED/NOT VALIDATED without authorized OAuth credentials; no scraping success claimed. Existing model/privacy and Challenge tests remain mandatory. Host-admin access, regex DLP, SQLite plaintext, OS egress enforcement, full lease/sandbox/region/budget/tool-execution architecture remain outside this discovery increment. No globally configured macOS/Android proxy and no claim that a self-hosted client makes provider processing local.


## API operation and executed evidence
No application rate limiter; use trusted ingress limits. GET status and POST discover require bearer authentication; wrong role403, missing task404, invalid schema422, storage503. Discovery result uses HTTP200 with an explicit attempt state (BLOCKED/UNAVAILABLE/DISCOVERED); never treat200 alone as successful connection or execution permission. Each request grants at most the documented metadata handshake/list/cleanup sequence, no durable permission and no automatic retries. Provider billing/residency are not verified: confirm account terms before enabling even discovery. No purchases or scraping calls implemented.

Request shape (substitute a real task ID, not sample evidence):
```json
{"task_id":"ACTUAL_TASK_ID","allow_external_discovery":true,"reason":"Explicitly approve provider metadata discovery only"}
```
Supply platform reviewer bearer to Core, NOT the Bright Data token. The provider credential comes only from configured server settings. Set a plan_lock_id as well when the task has a PLAN. The default-deny policy must first be deliberately changed for the documented metadata scope; changing it does not grant any model or tool permission automatically.

Important functions: `mcp_api.gate` evaluates task/project/class/region/consent/stop/PLAN policy; `register_mcp_api.discover` reserves and audits before I/O and rechecks before dispatch; `ExternalDataGateway.discover_brightdata` is the application egress entry; `DiscoveryClient.exchange` validates bounded authenticated wire messages; `discover` enforces handshake/catalogue/cleanup and projects only fixed candidate names. Inputs/outputs, dependencies, permissions, errors and security inherit the above contract. Direct Python function invocation is not a separately authenticated boundary.

Executed baseline146 PASS; new suite169 PASS (23 added parametrized cases),97.65% app statement coverage,2 known warnings. Normal and optimized real HTTP smokes43 checked responses each, including new MCP status/default-deny routes; four independent Challenge workers. Build/docs/OpenAPI/reality gate PASS. No production mocks: the TLS peer is explicitly synthetic test infrastructure and never registered as a Bright Data production endpoint. Live vendor/OAuth issuer/expiry/billing/region checks remain NOT VALIDATED. Session cleanup failures block success; any cleanup after a deadline failure may itself be unconfirmed and requires inspection. Current Core must be restarted to load new routes/configuration.

MCP-011 additionally proves that a configured opaque OAuth credential in a model prompt is rejected by the actual model API before any HTTP transport. This tests the gateway credential binding rather than assuming the pattern scanner recognizes opaque tokens.
