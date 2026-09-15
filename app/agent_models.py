"""Agent registry v1: declared bounded model-work configurations; runs require the full AI consent chain."""
from typing import Annotated, Literal
from pydantic import Field, field_validator
from app.models import Input, Text
from app.ai_models import DataClass
from app.mcp_client import CANDIDATES

Purpose = Literal['analysis', 'plan', 'code']


class AgentInput(Input):
    name: Annotated[str, Field(min_length=1, max_length=120)]
    description: str = Field(default='', max_length=2000)
    model_id: str
    purpose: Purpose
    instruction: Text
    allowed_tools: list[str] = Field(default_factory=list, max_length=8)

    @field_validator('allowed_tools')
    @classmethod
    def tools_within_allowlist(cls, value):
        if len(value) != len(set(value)):
            raise ValueError('allowed_tools must not contain duplicates')
        outside = [tool for tool in value if tool not in CANDIDATES]
        if outside:
            raise ValueError(f'tools outside the MCP candidate allowlist are not declarable: {outside}')
        return value


class Agent(AgentInput):
    id: str
    family_id: str
    version: int = Field(ge=1)
    predecessor_id: str | None
    state: Literal['active', 'deactivated']
    created_by: str
    created_at: str
    deactivated_at: str | None = None


class AssignmentInput(Input):
    target_kind: Literal['task', 'project']
    target_id: str


class UnlinkInput(Input):
    assignment_id: str


class AgentAssignment(Input):
    id: str
    agent_id: str
    target_kind: Literal['task', 'project']
    target_id: str
    state: Literal['active', 'unlinked']
    created_by: str
    created_at: str
    unlinked_at: str | None = None


class AgentRunInput(Input):
    task_id: str
    prompt: Annotated[str, Field(min_length=1, max_length=4000)]
    classification: DataClass = 'CONFIDENTIAL'


class AgentRun(Input):
    id: str
    agent_id: str
    agent_version: int = Field(ge=1)
    task_id: str
    request_id: str
    context_hash: str
    state: Literal['AWAITING_CONSENT', 'BLOCKED', 'DRAFT_UNCHALLENGED', 'UNAVAILABLE']
    attempt_id: str | None
    blocked_reason: str | None
    created_by: str
    created_at: str
    outcome_at: str | None = None


class AgentDeactivateInput(Input):
    confirm: Literal[True]
    reason: Text
