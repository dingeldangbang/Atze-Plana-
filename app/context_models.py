"""Storage/Memory are distinct from evidence truth and executable permissions."""
from typing import Annotated, Literal
from pydantic import Field, field_validator
from app.models import Input, Text

Tier = Literal['local', 'sd']
Content = Annotated[str, Field(min_length=1, max_length=65536)]


class LinkedInput(Input):
    project_id: str
    evidence_ids: list[str] = Field(default_factory=list, max_length=50)


class ArchiveInput(LinkedInput):
    relative_path: str = Field(min_length=1, max_length=240)
    content: Content
    placement: Literal['auto', 'local'] = 'auto'

    @field_validator('relative_path')
    @classmethod
    def safe_logical_path(cls, value):
        import re
        if not re.fullmatch(r'[A-Za-z0-9._/-]+', value) or any(p in {'', '.', '..'} for p in value.split('/')):
            raise ValueError('Use relative ASCII path segments; no empty, dot or traversal segments')
        return value

    model_config = {'str_strip_whitespace': False}


class Replica(Input):
    tier: Tier
    key: str


class Archive(Input):
    id: str
    project_id: str
    logical_path: str
    sha256: str
    size_bytes: int
    created_at: str
    evidence_ids: list[str]
    tier: Tier
    key: str
    retained_copies: list[Replica]
    version: Literal[1] = 1


class ArchiveContent(Input):
    object: Archive
    content: str
    model_config = {'str_strip_whitespace': False}


class MoveInput(Input):
    target: Tier
    reason: Text


class MemoryInput(LinkedInput):
    category: Literal['fact', 'inference', 'decision', 'task_history', 'user_preference',
                      'project_state', 'device_history', 'test_history', 'repair_history',
                      'trend_history', 'agent_history']
    content: Text
    task_id: str | None = None
    commit_sha: str | None = Field(default=None, pattern=r'^[0-9a-f]{40}$')


class Memory(MemoryInput):
    decision_result_id: str | None = None
    decision_challenge_id: str | None = None
    decision_fingerprint: str | None = None
    id: str
    created_at: str
    sha256: str
    state: Literal['recorded'] = 'recorded'


class RetrievalQuery(Input):
    project_id: str
    query: str = Field(min_length=1, max_length=256)
    limit: int = Field(default=10, ge=1, le=30)


class EvidenceState(Input):
    id: str
    state: Literal['unverified', 'verified', 'rejected']


class RetrievalHit(Input):
    decision_result_id: str | None = None
    decision_challenge_id: str | None = None
    decision_status: Literal['ACCEPT', 'CONDITIONAL', 'BLOCK'] | None = None
    source_id: str
    source_type: Literal['archive', 'memory']
    category: str
    location: str
    logical_path: str
    timestamp: str
    sha256: str
    version: Literal[1] = 1
    start_char: int
    end_char: int
    text: str
    evidence: list[EvidenceState]
    evidence_state: Literal['unverified', 'verified', 'rejected']
    commit_sha: str | None = None
    allowed_for_action: Literal[False] = False
    model_config = {'str_strip_whitespace': False}


class CacheInput(Input):
    task_id: str
    content: Content
    ttl_seconds: int = Field(default=3600, ge=60, le=86400)
    model_config = {'str_strip_whitespace': False}


class CacheObject(Input):
    id: str
    task_id: str
    project_id: str
    tier: Tier
    key: str
    size_bytes: int
    sha256: str
    created_at: str
    expires_at: str
    state: Literal['active', 'expired']
    deleted: bool


class CleanupInput(Input):
    reason: Text
    limit: int = Field(default=20, ge=1, le=100)


class CleanupResult(Input):
    deleted_ids: list[str]


class TierHealth(Input):
    tier: str
    implemented: bool
    configured: bool
    status: Literal["AVAILABLE", "BLOCKED", "NOT_CONFIGURED", "UNAVAILABLE"]
    resource_kind: Literal["FILESYSTEM_PATH"] | None = None
    available: bool
    total_bytes: int | None = None
    used_bytes: int | None = None
    free_bytes: int | None = None
    used_percent: float | None = None
    reason: str | None = None


class StorageHealth(Input):
    tiers: list[TierHealth]
    cache_active_bytes: int
    cache_expired_bytes: int
    archive_logical_bytes: int
    source_retention: Literal[True] = True


class ReindexInput(Input):
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)
    reason: Text


class ReindexResult(Input):
    indexed_ids: list[str]
    next_offset: int
