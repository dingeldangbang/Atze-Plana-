# ADR-007 — PLAN versions and fail-closed Context Lock

Accepted 2026-09-14. Baseline 05ea6d5: 120 executed tests, 97.78% core coverage, successful Python build. Existing source records/storage, reviewer roles, immutable Result/Challenge flow and AI consent inspected first.

## Bounded implementation
One PLAN per task; project derived from actual task. Immutable numbered versions select up to16 real Evidence/Memory/text-Archive resources with declared relationship and context category (project/task/object/device/test/research/software/repair). Labels do not implement hardware/repair engines. No phantom binary/PDF/CAD parser or filesystem path input.

Version creation resolves same-project resources (task-bound Memory only for same task), hashes actual text/checked archive bytes and metadata/evidence dependencies. Maximum1MiB selected plus dependency bytes, at most64 distinct Evidence dependencies. Version manifest contains provenance/hashes/review states, NOT copied plaintext or truth promotion. Reviewer can lock only latest version with matching expected manifest hash; version append uses optimistic expected-version ID. Revocation append-only. Empty/superseded/stale/missing/unavailable/corrupt sources block, not partial PASS. Stop revisions invalidate prior locks even after stop reset.

Once a task has PLAN, AI cannot omit its current lock or inject additional source IDs. Selected sources expand solely from locked version; existing privacy/classification/secret/context-size/consent gates remain. Archive text usable through this explicit path only. Bound request rechecks PLAN before transport (including source file integrity). Legacy tasks without PLAN retain explicit manual context path.

Challenge snapshots incorporate the current PLAN gate when present. Gate re-evaluated with real storage before claim/complete/triage/approval/adoption/RAG decision reads. Changed version/lock/revocation/source/stop invalidates report and approval; new worker challenge required, no server-generated substitute. New rule policy version intentionally invalidates old reports; API and independent worker updated together. Context Lock grants neither tool rights nor truth/approval. Lock persistence is not a physical file lock: external host modifications/in-flight operations cannot be recalled. Sources are immutable through supported APIs but filesystem+SQLite cannot be jointly atomic.

## Limits / safety
Source integrity VERIFIED is only a byte/hash statement. Manual review values retained verbatim; no MEASURED/CALCULATED/VERIFIED truth inferred from URL, context label or Memory. No continuous file watcher, no encrypted secretcache, universal binary workspace, permission leases, MCP/executor or production approval. Sequential checks add bounded synchronous IO; no 2GB throughput claim. Missing storage verification fails closed. No operational sample data. Dedicated real tests plus previous Core/model/Android pipelines required; only actual outcomes reported.
