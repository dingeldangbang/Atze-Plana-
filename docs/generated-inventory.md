# Source inventory (generated)

- `app/__init__.py`: (package marker)
- `app/config.py`: Settings
- `app/context.py`: update, references, index_text, create_memory, retrieve
- `app/context_api.py`: register_context_api
- `app/context_models.py`: LinkedInput, ArchiveInput, Replica, Archive, ArchiveContent, MoveInput, MemoryInput, Memory, RetrievalQuery, EvidenceState, RetrievalHit, CacheInput, CacheObject, CleanupInput, CleanupResult, TierHealth, StorageHealth, ReindexInput, ReindexResult
- `app/main.py`: create_app
- `app/models.py`: Input, ProjectInput, Project, EvidenceInput, Evidence, Review, Action, TaskInput, Task, Decision, ApprovalInput, Approval, StopInput, Stop, Audit
- `app/storage.py`: guard, Storage
- `app/store.py`: now, identity, Store, get, put, listing, audit, stopped
- `app/triage.py`: evaluate

Environment: `ATZE_DB_PATH`, `ATZE_MODE`, `ATZE_OPERATOR_TOKEN`, `ATZE_REVIEWER_TOKEN`, `ATZE_SD_ROOT`, `ATZE_STORAGE_ROOT`
