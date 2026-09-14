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
| AI-001 | Defaults/roles | isolated DB | prepare/run without policy | BLOCK, zero sockets | response/count asserted. | [test_ai_privacy.py: test_ai_default_and_roles](../../tests/test_ai_privacy.py) |
| AI-002 | Real HTTP transport | explicit policy/consent | send once | untrusted receipt, no result/memory, replay blocked | asserted. | [test_ai_privacy.py: test_ai_actual_transport_and_no_adoption](../../tests/test_ai_privacy.py) |
| AI-003 | Recognized secrets | isolated request | submit patterns | 409 before persistence/egress | response/socket count asserted. | [test_ai_privacy.py: test_ai_secret_rejection](../../tests/test_ai_privacy.py) |
| AI-004 | Context boundary | second project evidence | select foreign ID | BLOCK; own selection confidential | asserted. | [test_ai_privacy.py: test_ai_context_isolation](../../tests/test_ai_privacy.py) |
| AI-005 | Consent freshness | prepared request | change policy/hash/stop | BLOCK, no egress | asserted. | [test_ai_privacy.py: test_ai_stale_policy_hash_and_stop](../../tests/test_ai_privacy.py) |
| AI-006 | Real receiver failure responses | allowed request | redirect/tools/bad JSON/oversize | no fallback/adoption | asserted. | [test_ai_privacy.py: test_ai_transport_failures_no_fallback](../../tests/test_ai_privacy.py) |
| AI-007 | Origin constraints | bad startup config | construct gateway | reject before socket | ValueError asserted. | [test_ai_privacy.py: test_ai_reject_unsafe_origin](../../tests/test_ai_privacy.py) |
| AI-008 | Actual TLS | ephemeral self-signed test cert | untrusted then trusted handshake | cert failure then receipt | no model claim. | [test_ai_privacy.py: test_ai_real_tls](../../tests/test_ai_privacy.py) |
| AI-009 | Remote policy | configured HTTPS endpoint without connection | default lock/external deny | blocked before transport. | [test_ai_privacy.py: test_ai_remote_privacy_lock](../../tests/test_ai_privacy.py) |
| AI-010 | Limits/task Memory | actual local records | duplicate/oversize/foreign-task context | blocked before egress. | [test_ai_privacy.py: test_ai_bounds_and_task_memory](../../tests/test_ai_privacy.py) |
| AI-011 | Auth/output/read contracts | configured transport | missing/reused token and empty output | block, audit readable. | [test_ai_privacy.py: test_ai_missing_auth_invalid_output_and_reads](../../tests/test_ai_privacy.py) |
| AI-012 | No action privilege | write task and missing provider | actual APIs | BLOCK with zero transmission. | [test_ai_privacy.py: test_ai_write_task_and_unconfigured_model](../../tests/test_ai_privacy.py) |
| AI-013 | Startup ambiguity | duplicate configured IDs | load config | reject, not last-wins. | [test_ai_privacy.py: test_ai_duplicate_startup_config](../../tests/test_ai_privacy.py) |
| AI-014 | Known credentials | raw platform/provider tokens without labels | prepare | BLOCK before persistence/transport. | [test_ai_privacy.py: test_ai_known_unlabelled_credentials](../../tests/test_ai_privacy.py) |
| CH-001: pending blocks; a real report enables bounded triage; reviewer adoption stores only checked-scope references, not unchecked primary text. | [test_challenge.py: test_mandatory_challenge_and_explicit_adoption](../../tests/test_challenge.py) |
| CH-002: operator/reviewer cannot act as worker; worker cannot write primary evidence; forged PASS and replay are rejected. | [test_challenge.py: test_worker_credentials_separate_and_forgery_rejected](../../tests/test_challenge.py) |
| CH-003: missing service credential leaves pending result blocked; no in-process auto-report or approval path. | [test_challenge.py: test_unconfigured_worker_has_no_fallback](../../tests/test_challenge.py) |
| CH-004: independently scanned project evidence contradicting an identical variant/property blocks despite not being selected by primary. | [test_challenge.py: test_contradiction_not_selected_by_primary_stops_line](../../tests/test_challenge.py) |
| CH-005: identity, unit/condition, measurement and causality gaps yield concrete CONDITIONAL findings, not rhetorical confirmation. | [test_challenge.py: test_specific_unknowns_cannot_pass](../../tests/test_challenge.py) |
| CH-006: absent alternative remains a concrete gap; worker emits no fabricated device or counter-source. | [test_challenge.py: test_no_alternative_is_not_invented](../../tests/test_challenge.py) |
| CH-007: new evidence invalidates a prior approval; a new challenge and human approval are both required before adoption. | [test_challenge.py: test_stale_evidence_invalidates_reports_approvals_and_adoption](../../tests/test_challenge.py) |
| CH-008: newest result and newest challenge must pass; old package/adoption and old job cannot bypass pending work. | [test_challenge.py: test_new_result_and_rechallenge_invalidate_old_pass](../../tests/test_challenge.py) |
| CH-009: expired leases are reclaimable, old leases rejected, evidence changes during worker run prevent commit. | [test_challenge.py: test_lease_expiry_reclaim_and_snapshot_race](../../tests/test_challenge.py) |
| CH-010: stop blocks schedule/claims/complete; report/audit failure rolls back completion instead of permitting acceptance. | [test_challenge.py: test_challenge_stop_and_audit_atomicity](../../tests/test_challenge.py) |
| CH-011: duplicate/foreign references and shared/short worker credentials cannot establish a challenge boundary. | [test_challenge.py: test_claim_references_and_service_config](../../tests/test_challenge.py) |
| CH-012: truncated scope, missing/corrupt/rejected sources and declared unsupported actions/calculations never receive a fake PASS. | [test_challenge.py: test_rule_boundaries_and_scope](../../tests/test_challenge.py) |
| CH-013: worker rejects credential-bearing/remote-plaintext origins, missing credentials and redirects instead of faking a result. | [test_challenge.py: test_worker_transport_constraints](../../tests/test_challenge.py) |
| CH-014: unknown values are not promoted by matching strings; alternative rationale alone is not evidence and unreviewed sources remain conditional. | [test_challenge.py: test_unreviewed_sources_alternatives_and_unknown_sentinels](../../tests/test_challenge.py) |
| CH-015: retrieved decision-memory carries challenge provenance and becomes BLOCK after evidence changes; no stale acceptance in RAG. | [test_challenge.py: test_adopted_memory_retrieval_revalidates_challenge](../../tests/test_challenge.py) |
| CH-016: accepted challenge does not bypass atomic audit on adoption; audit failure creates no decision-memory or index entry. | [test_challenge.py: test_adoption_audit_failure_rolls_back_memory](../../tests/test_challenge.py) |
| CH-017: bounded snapshot and finding limits stop the line instead of silently validating a truncated context. | [test_challenge.py: test_scope_limits_block_instead_of_partial_validation](../../tests/test_challenge.py) |
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
| MEM-001: direct fact creation is blocked pending Challenge adoption; inference remains inference even with verified sources; retrieval is never execution permission. | [test_context_storage.py: test_memory_fact_inference_and_live_evidence](../../tests/test_context_storage.py) |
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
| TRI-001: Challenge is mandatory; only READ can be eligible without approval, high-impact decisions remain conditional and never execute. | [test_core.py: test_approval_policy](../../tests/test_core.py) |
| TRI-002: low confidence, unverified evidence or absent preconditions block approval. | [test_core.py: test_blocking_conditions](../../tests/test_core.py) |
| SEC-003: persisted stop blocks even approved tasks after application restart. | [test_core.py: test_emergency_stop_persistent](../../tests/test_core.py) |
| API-002: reject blank names, extra fields, foreign/duplicate/missing references and over-limit lists. | [test_core.py: test_input_integrity](../../tests/test_core.py) |
| EVD-002: future timestamps, non-HTTP URLs and out-of-range confidence are rejected. | [test_core.py: test_invalid_observation](../../tests/test_core.py) |
| TRI-003: rejected or absent evidence blocks, including at the confidence threshold. | [test_core.py: test_rejected_and_empty_evidence](../../tests/test_core.py) |
| AUD-001: domain mutation and audit persist together; failed references create neither. | [test_core.py: test_audit_and_transaction](../../tests/test_core.py) |
| SEC-004: storage failure returns redacted 503, not a SQL or filesystem traceback. | [test_core.py: test_storage_error_redacted](../../tests/test_core.py) |
| DOC-001: authenticated schema reflects supported APIs and bearer authentication. | [test_core.py: test_schema](../../tests/test_core.py) |
| SEC-005: both roles can inspect real stop state; write is reviewer-only. | [test_core.py: test_stop_read](../../tests/test_core.py) |
| LM-001 | opt-in gate | previous PASS report | run without consent | overwritten BLOCKED before I/O, no model success. | [test_local_model_runner.py: test_local_model_requires_opt_in](../../tests/test_local_model_runner.py) |
| LM-002 | real missing file | opt-in | preflight | BLOCKED, not simulated success. | [test_local_model_runner.py: test_local_model_missing_artifacts](../../tests/test_local_model_runner.py) |
| LM-003 | byte integrity helper | explicitly synthetic small file | size/hash/symlink checks | genuine hash checks, NOT model proof. | [test_local_model_runner.py: test_local_model_artifact_hash](../../tests/test_local_model_runner.py) |
| PLAN-001 | selected real sources | temp evidence/memory/archive | create/lock | hashes/provenance only, no truth/permissions | asserted. | [test_plan.py: test_plan_real_multi_resource_manifest](../../tests/test_plan.py) |
| PLAN-002 | role/optimistic boundaries | current lock | append old/new versions | wrong roles/stale expectations blocked. | [test_plan.py: test_plan_roles_and_immutable_versions](../../tests/test_plan.py) |
| PLAN-003 | stop/reset/revoke | actual control audit | lock then stop | no revived lock, revoke allowed during stop. | [test_plan.py: test_plan_stop_and_revocation](../../tests/test_plan.py) |
| PLAN-004 | referential integrity | actual two projects/tasks | foreign/duplicate/missing/unsupported refs | 422/404 and rollback. | [test_plan.py: test_plan_isolation_and_missing_sources](../../tests/test_plan.py) |
| PLAN-005 | actual file mutation | challenged task with archive lock | corrupt blob | lock/triage/adopt BLOCK, no hidden IO fallback. | [test_plan.py: test_plan_corrupt_archive_blocks_triage_and_adopt](../../tests/test_plan.py) |
| PLAN-006 | exact source state | unreviewed source selected | review changes metadata | stale/hash mismatch refuses lock. | [test_plan.py: test_plan_source_review_staleness_and_lock_hash](../../tests/test_plan.py) |
| PLAN-007 | entire decision chain | real challenge/approval/adopt | append PLAN version | approval and RAG decision invalidated. | [test_plan.py: test_plan_version_invalidates_approval_and_rag](../../tests/test_plan.py) |
| PLAN-008 | transaction failure | real SQLite trigger | audit insert abort | no half-created PLAN/version. | [test_plan.py: test_plan_audit_failure_rolls_back](../../tests/test_plan.py) |
| PLAN-009 | real HTTP transport | bound archive context | no lock/extra refs/revoke | blocked; current exact lock sends actual selected text only. | [test_plan.py: test_ai_cannot_bypass_plan_and_archive_context](../../tests/test_plan.py) |
| PLAN-010 | prepared request before PLAN, 9 sources, locked secret | real API | fail closed without any transport. | [test_plan.py: test_ai_plan_bounds_secrets_and_late_creation](../../tests/test_plan.py) |
| PLAN-011 | isolated SQLite corruption | alter saved context after consent hash | no real HTTP transport. | [test_plan.py: test_ai_plan_request_integrity_fault](../../tests/test_plan.py) |
| PLAN-012 | isolated persisted-record faults | corrupt source/hash/dependency scope | real SQLite/API | 503/422 and no partial PLAN. | [test_plan.py: test_plan_integrity_dependency_faults](../../tests/test_plan.py) |
| PLAN-013 | actual UTF-8 archive blobs | 9 x128KiB | 1MiB source cap blocks without truncation. | [test_plan.py: test_plan_byte_budget](../../tests/test_plan.py) |
| PLAN-014 | actual Evidence/Memory/archive API records | 65 dependencies or >1MiB combined | fail413, no truncation/partial PLAN. | [test_plan.py: test_plan_dependency_budgets](../../tests/test_plan.py) |
| PLAN-015 | real concurrent API/SQLite transactions | two writers same expected version | exactly one201/one409, no lost update. | [test_plan.py: test_plan_concurrent_optimistic_append](../../tests/test_plan.py) |
| REAL-001: a new operational database/UI has no seeded projects, telemetry, tasks or results; mode is explicit. | [test_reality.py: test_operational_start_has_no_seeded_data](../../tests/test_reality.py) |
| REAL-002: persistent test DB marker rejects switching to operational mode without changing/deleting data. | [test_reality.py: test_test_database_cannot_be_opened_operational](../../tests/test_reality.py) |
| REAL-003: an operational database cannot be switched to test mode even if currently empty. | [test_reality.py: test_operational_database_cannot_be_used_as_test](../../tests/test_reality.py) |
| REAL-004: legacy nonempty database is refused for test mode rather than silently seeded or relabelled. | [test_reality.py: test_unmarked_existing_database_not_adopted_as_test](../../tests/test_reality.py) |
| REAL-005: blob-root mode marker rejects cross-mode sharing independently of database separation. | [test_reality.py: test_storage_root_cannot_cross_modes](../../tests/test_reality.py) |
| REAL-006: test storage refuses pre-existing unlabelled originals instead of marking them as test data. | [test_reality.py: test_unmarked_existing_blobs_not_adopted_as_test](../../tests/test_reality.py) |
| REAL-007: absent implementation, absent config and actual configured-path outage have distinct statuses and null measurements. | [test_reality.py: test_availability_dimensions_and_real_failure](../../tests/test_reality.py) |
| REAL-008: unknown operating mode is rejected, never interpreted as permission to enable test behavior. | [test_reality.py: test_invalid_mode_fails_closed](../../tests/test_reality.py) |
| REAL-009: absent explicit opt-in overwrites a stale PASS report with BLOCKED without starting tests. | [test_reality.py: test_smoke_requires_opt_in_and_invalidates_old_report](../../tests/test_reality.py) |
| REAL-010: real HTTP smoke uses a fresh process/DB/roots/tokens, not inherited operational paths or credentials. | [test_reality.py: test_smoke_real_isolated_process_ignores_operational_paths](../../tests/test_reality.py) |
| REAL-011: an injected test failure produces FAIL with error, not hardcoded/stale PASS, and stops the real child. | [test_reality.py: test_smoke_failure_does_not_leave_pass](../../tests/test_reality.py) |
| REAL-012: CLI no longer accepts a user-supplied target URL for fixture writes. | [test_reality.py: test_smoke_rejects_arbitrary_target](../../tests/test_reality.py) |
| REAL-013: runtime mock imports and assert-only test success are rejected by the narrow guardrail. | [test_reality.py: test_reality_boundary_guard](../../tests/test_reality.py) |
| REAL-014: a filesystem capacity probe without total size yields UNAVAILABLE/null, not an invented 100 percent. | [test_reality.py: test_zero_capacity_has_no_invented_percentage](../../tests/test_reality.py) |
| REAL-015: newly appearing unlabelled tier is not initialized by GET; reviewed restart binds its mode explicitly. | [test_reality.py: test_late_unmarked_tier_is_unavailable_until_reviewed_restart](../../tests/test_reality.py) |
| OPS-001: backup integrity and restored project read work; existing destination is never overwritten. | [test_tools.py: test_backup_restore](../../tests/test_tools.py) |
| DOC-002: OpenAPI, generated references, local links and environment coverage pass the worker gate. | [test_tools.py: test_docs_consistent](../../tests/test_tools.py) |
| CFG-001: documented environment names configure startup and persistent path without defaults for secrets. | [test_tools.py: test_environment_config](../../tests/test_tools.py) |
| DOC-003: changed generated output causes nonzero check status instead of silent acceptance. | [test_tools.py: test_documentation_drift_detection](../../tests/test_tools.py) |
| DOC-004: missing local reference is detected and existing reference is accepted. | [test_tools.py: test_broken_link_detection](../../tests/test_tools.py) |
| DB-THREAD-001 | FastAPI lifecycle handoff | real SQLite/two threads | enter/use/exit separately | commit and rollback correct. | [test_tools.py: test_connection_dependency_thread_handoff](../../tests/test_tools.py) |
| UNI-001: ignored/secret files excluded, pending source seen, no source excerpt. | [test_universe.py: test_inventory_exclusions_and_pending_files](../../tests/test_universe.py) |
| UNI-002: exception pass not a stub; whole empty function candidate, syntax distinct. | [test_universe.py: test_legitimate_pass_and_syntax](../../tests/test_universe.py) |
| UNI-003: actual byte copy, idempotent backup, corrupt backup/symlink rejected. | [test_universe.py: test_backup_integrity_and_symlinks](../../tests/test_universe.py) |
| UNI-004: report writer cannot overwrite symlink target. | [test_universe.py: test_report_symlink_refused](../../tests/test_universe.py) |
| UNI-005: multiple stacks, actual commands without collect/dry-run; unknown blocked. | [test_universe.py: test_multi_stack_and_unknown](../../tests/test_universe.py) |
| UNI-006: real failing/successful/timeout processes, no shell; no stdout leak. | [test_universe.py: test_actual_process_exit_and_timeout](../../tests/test_universe.py) |
| UNI-007: no --execute means no code runs, saved report BLOCKED, nonzero exit. | [test_universe.py: test_plan_only_fails_closed](../../tests/test_universe.py) |
