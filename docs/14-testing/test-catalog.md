# Test catalog (generated)

Every test definition is catalogued from its AST; parametrizations produce separate JUnit cases.
Actual results are in `reports/junit.xml` after running pytest, not inferred by this worker.

## Shared test procedure

- Preconditions: Python 3.11+, locked dependencies; isolated pytest temporary SQLite DB.
- Inputs: synthetic fixtures in [conftest](../../tests/conftest.py), never device observations.
- Actions/expected results: linked test bodies and assertions below are authoritative.
- Execution: `python -m pytest --junitxml=reports/junit.xml`.
- Actual result/status/evidence: JUnit testcase failure/error/skipped and timestamps; CI artifact.
- No test execution is performed by documentation generation itself.

| Test ID / purpose / expected result | Executable case |
|---|---|
| STO-001: original UTF-8 whitespace/hash survives storage and restart; duplicate namespace cannot overwrite. | [test_context_storage.py: test_archive_original_namespace_and_restart](../../tests/test_context_storage.py) |
| STO-002: absolute, traversal, empty, encoded or platform-specific path segments are rejected. | [test_context_storage.py: test_logical_path_rejection](../../tests/test_context_storage.py) |
| STO-003: reviewer relocation preserves original, hash and namespace; retrieval resolves the new location. | [test_context_storage.py: test_copy_verify_switch_retains_source_and_citations](../../tests/test_context_storage.py) |
| STO-004: failed destination verification cannot switch the index or destroy the original. | [test_context_storage.py: test_destination_failure_leaves_authoritative_source](../../tests/test_context_storage.py) |
| STO-005: failed relocation audit rolls back location; unreferenced copies may remain, original remains readable. | [test_context_storage.py: test_archive_audit_failure_rolls_back_metadata](../../tests/test_context_storage.py) |
| STO-006: corrupt source blocks reads/migration; object symlink cannot expose arbitrary host files. | [test_context_storage.py: test_corruption_and_symlink_are_not_followed](../../tests/test_context_storage.py) |
| STO-007: capacity policy falls back to configured SD, rejects all-full tiers and reports unavailable remote tiers honestly. | [test_context_storage.py: test_capacity_policy_and_unavailable_tier](../../tests/test_context_storage.py) |
| STO-008: stop blocks archive/cache creation, relocation and cleanup; existing originals remain readable. | [test_context_storage.py: test_stop_blocks_storage_writes](../../tests/test_context_storage.py) |
| CACHE-001: only expired cache is deleted; archive, live cache and memory survive; repeat cleanup is safe. | [test_context_storage.py: test_cache_expiry_cleanup_and_archive_separation](../../tests/test_context_storage.py) |
| CACHE-002: failure after physical deletion leaves a committed tombstone and cleanup can retry missing file. | [test_context_storage.py: test_cache_delete_crash_retry](../../tests/test_context_storage.py) |
| MEM-001: fact creation needs verified evidence; inference remains inference even with verified sources; retrieval is never execution permission. | [test_context_storage.py: test_memory_fact_inference_and_live_evidence](../../tests/test_context_storage.py) |
| RAG-001: lexical retrieval returns real character spans/hashes, isolates projects and treats FTS syntax as words. | [test_context_storage.py: test_retrieval_positions_project_filter_and_query_safety](../../tests/test_context_storage.py) |
| MEM-002: foreign/duplicate evidence and task references are rejected; commit is format-checked attestation only. | [test_context_storage.py: test_cross_project_refs_and_commit_attestation](../../tests/test_context_storage.py) |
| STO-009: missing SD never gets created, overlapping/symlink roots fail startup, absent tier cannot receive data. | [test_context_storage.py: test_missing_sd_and_root_boundaries](../../tests/test_context_storage.py) |
| MIG-001: v0.1 records/control survive additive FTS/namespace schema initialization and repeated startup. | [test_context_storage.py: test_additive_upgrade_preserves_v1_data](../../tests/test_context_storage.py) |
| RAG-002: paginated reviewer rebuild restores derived FTS; rejected evidence remains rejected without granting use. | [test_context_storage.py: test_reindex_from_originals_and_rejected_evidence](../../tests/test_context_storage.py) |
| STO-010: missing index source, oversized blobs and nonregular objects fail closed rather than return false content. | [test_context_storage.py: test_index_and_nonregular_storage_fail_closed](../../tests/test_context_storage.py) |
| TX-001: failure at transaction finalization returns 503, never a success sent before commit; mutation rolls back. | [test_context_storage.py: test_transaction_finalization_precedes_success](../../tests/test_context_storage.py) |
| SEC-001: missing or identical credentials prevent startup; no insecure default. | [test_core.py: test_config_fails_closed](../../tests/test_core.py) |
| API-001: health and static UI are public; data and specification require credentials. | [test_core.py: test_public_surface](../../tests/test_core.py) |
| SEC-002: reviewers cannot create projects and operators cannot access audit or stop. | [test_core.py: test_role_separation](../../tests/test_core.py) |
| EVD-001: content hash is real, evidence starts unverified, review is role-bound and immutable. | [test_core.py: test_evidence_provenance_and_review](../../tests/test_core.py) |
| TRI-001: only READ is eligible without reviewer approval; no decision executes an action. | [test_core.py: test_approval_policy](../../tests/test_core.py) |
| TRI-002: low confidence, unverified evidence or absent preconditions block approval. | [test_core.py: test_blocking_conditions](../../tests/test_core.py) |
| SEC-003: persisted stop blocks even approved tasks after application restart. | [test_core.py: test_emergency_stop_persistent](../../tests/test_core.py) |
| API-002: reject blank names, extra fields, foreign/duplicate/missing references and over-limit lists. | [test_core.py: test_input_integrity](../../tests/test_core.py) |
| EVD-002: future timestamps, non-HTTP URLs and out-of-range confidence are rejected. | [test_core.py: test_invalid_observation](../../tests/test_core.py) |
| TRI-003: rejected or absent evidence blocks, including at the confidence threshold. | [test_core.py: test_rejected_and_empty_evidence](../../tests/test_core.py) |
| AUD-001: domain mutation and audit persist together; failed references create neither. | [test_core.py: test_audit_and_transaction](../../tests/test_core.py) |
| SEC-004: storage failure returns redacted 503, not a SQL or filesystem traceback. | [test_core.py: test_storage_error_redacted](../../tests/test_core.py) |
| DOC-001: authenticated schema reflects supported APIs and bearer authentication. | [test_core.py: test_schema](../../tests/test_core.py) |
| SEC-005: both roles can inspect real stop state; write is reviewer-only. | [test_core.py: test_stop_read](../../tests/test_core.py) |
| OPS-001: backup integrity and restored project read work; existing destination is never overwritten. | [test_tools.py: test_backup_restore](../../tests/test_tools.py) |
| DOC-002: OpenAPI, generated references, local links and environment coverage pass the worker gate. | [test_tools.py: test_docs_consistent](../../tests/test_tools.py) |
| CFG-001: documented environment names configure startup and persistent path without defaults for secrets. | [test_tools.py: test_environment_config](../../tests/test_tools.py) |
| DOC-003: changed generated output causes nonzero check status instead of silent acceptance. | [test_tools.py: test_documentation_drift_detection](../../tests/test_tools.py) |
| DOC-004: missing local reference is detected and existing reference is accepted. | [test_tools.py: test_broken_link_detection](../../tests/test_tools.py) |
