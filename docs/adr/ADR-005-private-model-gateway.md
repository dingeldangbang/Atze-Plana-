# ADR-005 — Privacy-first model boundary

Status: accepted, bounded first implementation; 2026-09-14.

## Before changes
Core has SQLite/FTS, same-workspace shared operator/reviewer roles, isolated Challenge credential and immutable reports. No model runtime, Hugging Face SDK, MCP transport, tool sandbox or external provider adapter exists. Only Challenge worker makes runtime HTTP calls (server origin, no redirects). No local model/runtime/weights found during inspection. Existing APIs/storage/triage must remain intact.

## Decision
Add provider-independent contracts and one real OpenAI-compatible text HTTP adapter usable by separately operated llama.cpp/vLLM/TGI/Ollama/custom/HF endpoints. Core never imports weights, executes generated code, downloads models or runs remote-code model repositories. Abstract modality contracts are NOT implemented modality providers.

ExternalDataGateway is the sole new model network path. Default privacy lock + local only + external deny; empty provider registry, empty policy allowlists. Configuration is trusted host configuration; arbitrary URLs/tokens cannot be supplied by API/model output. All off-host modes require verified TLS 1.2+, authenticated transport, exact provider/model/project/task/class/region allowlists and explicit remote permission. LOCAL HTTP only literal loopback; local endpoints still require authentication. No automatic fallback, redirect, proxy, discovery or provisioning.

Reviewer registers metadata and approves exact immutable request context before inference. Approval does not authorize tools/adoption. Whole-request classification cannot be lower than selected existing context (conservatively CONFIDENTIAL). Secret scanner rejects recognized credentials for all modes rather than attempting lossy unsafe redaction; it is not proof against encoded/unknown secrets. No entire-project context, filesystem access or model tool execution. Limited selected Evidence/Memory IDs from same task project; archive/binary modalities deferred. Model output remains untrusted draft; no automatic Result/Memory/adoption. Existing Challenge/Triage remains mandatory.

## Audit and races
Durable pending-outcome record before transport; current policy/config/stop and request permission checked again under SQLite write lock before sending. Network call bounded; lock serializes privacy/approval changes but cannot preempt an already in-flight request. Failed/unknown outcomes never auto-retried. Audit contains IDs/hashes/classifications/reason codes, not prompts, tokens or model response. Reviewed request context lives in ordinary local database; recognized SECRET/CREDENTIAL rejected before persistence, no encrypted-at-rest storage claim.

## Limits / release gates
This is NOT complete HF agent/MCP integration. Actual HF local model, private endpoint, remote provider, smolagents, MCP, independent-model Challenge, tool sandbox, automatic offloading, comprehensive classifier, encrypted cache, ingress/OS egress enforcement and provider region/revision attestation require separate real validation. Metadata is manually attested, not a catalogue discovery result. TLS protects transit, not plaintext processing by provider. Shared-role reviewer is not independent identity. Python boundary is not a host firewall; future adapters must use it, OS-level universal egress guarantees are unproven. No release until broader requested gates are met.
