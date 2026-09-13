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
