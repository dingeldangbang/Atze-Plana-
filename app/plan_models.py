"""Immutable bounded PLAN references. A context label is not a device or truth claim."""
from typing import Literal
from pydantic import Field
from app.models import Input, Text


class PlanResource(Input):
    kind: Literal['evidence', 'memory', 'archive']
    id: str = Field(min_length=1, max_length=100)
    relationship: Literal['input', 'reference', 'supports', 'contradicts'] = 'input'


class PlanContent(Input):
    title: str = Field(min_length=1, max_length=160)
    context_type: Literal['project', 'task', 'object', 'device', 'test', 'research', 'software', 'repair'] = 'task'
    resources: list[PlanResource] = Field(min_length=1, max_length=16)


class PlanCreate(PlanContent):
    task_id: str


class PlanRevise(PlanContent):
    expected_version_id: str


class PlanLockInput(Input):
    version_id: str
    manifest_hash: str = Field(pattern=r'^[a-f0-9]{64}$')
    reason: Text


class PlanRevoke(Input):
    reason: Text


class Plan(Input):
    id: str
    task_id: str
    project_id: str
    created_at: str


class PlanVersion(PlanContent):
    id: str
    plan_id: str
    version: int
    created_at: str
    manifest: dict
    manifest_hash: str


class PlanLock(Input):
    id: str
    plan_id: str
    version_id: str
    manifest_hash: str
    created_at: str
    actor: Literal['reviewer']
    reason_hash: str


class PlanStatus(Input):
    plan_id: str
    version_id: str | None
    lock_id: str | None
    state: Literal['CURRENT', 'UNLOCKED', 'SUPERSEDED', 'REVOKED', 'STALE', 'BLOCKED']
    reason: str
    manifest_hash: str | None
    allowed_for_action: Literal[False] = False
