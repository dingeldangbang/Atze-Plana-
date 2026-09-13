# Source inventory (generated)

- `app/__init__.py`: (package marker)
- `app/challenge_api.py`: register_challenge_api
- `app/challenge_models.py`: Claim, Alternative, ResultInput, Result, ChallengeRequest, Finding, Analysis, WorkItem, Completion, ChallengeReport, JobStatus, Why
- `app/challenge_rules.py`: normalized, equal_value, analyze
- `app/challenge_service.py`: digest, latest, current_result, snapshot, make_job, submit_result, claim_job, complete_job, challenge_gate, decide_task, adopt_result
- `app/challenge_worker.py`: NoRedirects, run_once, main
- `app/config.py`: Settings
- `app/context.py`: update, references, index_text, create_memory, retrieve
- `app/context_api.py`: register_context_api
- `app/context_models.py`: LinkedInput, ArchiveInput, Replica, Archive, ArchiveContent, MoveInput, MemoryInput, Memory, RetrievalQuery, EvidenceState, RetrievalHit, CacheInput, CacheObject, CleanupInput, CleanupResult, TierHealth, StorageHealth, ReindexInput, ReindexResult
- `app/main.py`: create_app
- `app/models.py`: Input, ProjectInput, Project, Observation, EvidenceInput, Evidence, Review, Action, TaskInput, Task, Decision, ApprovalInput, Approval, StopInput, Stop, Audit
- `app/storage.py`: guard, Storage
- `app/store.py`: now, identity, Store, get, put, listing, audit, stopped
- `app/triage.py`: evaluate

Environment: `ATZE_CHALLENGE_TOKEN`, `ATZE_DB_PATH`, `ATZE_MODE`, `ATZE_OPERATOR_TOKEN`, `ATZE_REVIEWER_TOKEN`, `ATZE_SD_ROOT`, `ATZE_STORAGE_ROOT`
