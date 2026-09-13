from typing import Literal
from pydantic import Field
from app.models import Input, Text


class Claim(Input):
    subject: Text
    variant: Text
    revision: Text
    attribute: Text
    value: Text
    unit: Text
    conditions: Text
    evidence_ids: list[str] = Field(min_length=1, max_length=20)
    requires_measurement: bool = True
    causal: bool = False


class Alternative(Input):
    subject: Text
    rationale: Text
    evidence_ids: list[str] = Field(min_length=1, max_length=20)


class ResultInput(Input):
    task_id: str
    kind: Literal['research', 'calculation', 'plan', 'action', 'presentation']
    summary: Text
    primary_worker: Text
    claims: list[Claim] = Field(min_length=1, max_length=20)
    alternatives: list[Alternative] = Field(default_factory=list, max_length=10)
    unknowns: list[Text] = Field(default_factory=list, max_length=20)
    falsification_test: Text


class Result(ResultInput):
    id: str
    created_at: str
    created_by: Literal['operator']


class ChallengeRequest(Input):
    reason: Text


class Finding(Input):
    check: Literal['evidence', 'consistency', 'alternative', 'causality', 'action']
    severity: Literal['info', 'condition', 'block']
    code: str
    message: str
    evidence_ids: list[str] = Field(default_factory=list)
    next_validation: str


class Analysis(Input):
    verdict: Literal['PASS', 'CONDITIONAL', 'BLOCK']
    scope: Literal['submitted_structured_claims_only'] = 'submitted_structured_claims_only'
    findings: list[Finding]
    alternatives: list[dict]
    policy_version: str


class WorkItem(Input):
    job_id: str
    lease: str
    fingerprint: str
    snapshot: dict


class Completion(Input):
    lease: str
    fingerprint: str
    analysis: Analysis


class ChallengeReport(Input):
    id: str
    job_id: str
    result_id: str
    fingerprint: str
    created_at: str
    worker_identity: Literal['challenge-worker']
    analysis: Analysis


class JobStatus(Input):
    id: str
    result_id: str
    state: Literal['pending', 'running', 'completed', 'superseded']
    fingerprint: str
    created_at: str
    reason: str
    lease_expires_at: str | None = None


class Why(Input):
    result: Result
    decision: dict
    latest_job: JobStatus | None
    report: ChallengeReport | None
    current: bool
