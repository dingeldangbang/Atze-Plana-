from datetime import datetime
from enum import Enum
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, AwareDatetime, field_validator

Text = Annotated[str, Field(min_length=1, max_length=2000)]


class Input(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class ProjectInput(Input):
    name: Annotated[str, Field(min_length=1, max_length=120)]
    description: str = Field(default='', max_length=2000)


class Project(ProjectInput):
    id: str
    created_at: datetime


class EvidenceInput(Input):
    project_id: str
    claim: Text
    source_url: HttpUrl
    observed_at: AwareDatetime
    source_type: Literal['manual', 'document', 'measurement']
    provider: Text
    extraction_method: Text
    content: Annotated[str, Field(min_length=1, max_length=20000)]
    confidence: float = Field(ge=0, le=1, allow_inf_nan=False)

    @field_validator('observed_at')
    @classmethod
    def not_future(cls, value):
        from datetime import timezone
        if value > datetime.now(timezone.utc):
            raise ValueError('Observation cannot be in the future')
        return value


class Evidence(EvidenceInput):
    id: str
    created_at: datetime
    sha256: str
    state: Literal['unverified', 'verified', 'rejected'] = 'unverified'
    review_reason: str | None = None


class Review(Input):
    state: Literal['verified', 'rejected']
    reason: Text


class Action(str, Enum):
    READ = 'read'
    WRITE = 'write'
    FLASH = 'flash'
    FIRMWARE = 'firmware'
    EDL_WRITE = 'edl_write'
    PRODUCTION_DEPLOY = 'production_deploy'
    PAYMENT = 'payment'


class TaskInput(Input):
    project_id: str
    title: Annotated[str, Field(min_length=1, max_length=200)]
    action: Action
    evidence_ids: list[str] = Field(default_factory=list, max_length=50)
    preconditions_met: bool = False


class Task(TaskInput):
    id: str
    created_at: datetime
    created_by: str


class Decision(Input):
    task_id: str
    state: Literal['blocked', 'eligible', 'approval_required', 'approved']
    risk: Literal['low', 'medium', 'high']
    reasons: list[str]
    evidence_ids: list[str]
    confidence: float
    approval_id: str | None = None
    executed: Literal[False] = False


class ApprovalInput(Input):
    reason: Text


class Approval(ApprovalInput):
    id: str
    task_id: str
    created_at: datetime
    actor: str


class StopInput(Input):
    active: bool
    reason: Text


class Stop(StopInput):
    pass


class Audit(Input):
    id: str
    created_at: datetime
    actor: str
    event: str
    entity_id: str
    details: dict
