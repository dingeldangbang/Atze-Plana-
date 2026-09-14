"""Trend contracts: deterministic CALCULATED analysis over submitted samples; never MEASURED, never predicted."""
from typing import Annotated, Literal
from pydantic import Field, field_validator
from app.models import Input

TrendType = Literal['drift', 'level_shift', 'variance_change', 'out_of_range_rate', 'suspect_rate']


class TrendQueryInput(Input):
    sensor_id: str
    session: Annotated[str, Field(max_length=120)] | None = None  # None/empty = all sessions

    @field_validator('session')
    @classmethod
    def empty_session_means_all(cls, value):
        return value or None


class CheckResult(Input):
    type: TrendType
    status: Literal['VERIFIED TREND', 'INSUFFICIENT EVIDENCE']
    sample_count: int
    statistic: str
    value: float | None
    threshold: str
    failed_criteria: list[str]
    details: dict


class TrendReport(Input):
    sensor_id: str
    device_id: str
    session: str | None
    sample_count: int
    window_start: str | None
    window_end: str | None
    batch_ids: list[str]
    checks: list[CheckResult]
    verified_types: list[TrendType]
    summary_status: Literal['VERIFIED TREND', 'INSUFFICIENT EVIDENCE']
    basis: Literal['SUBMITTED_DEVICE_SAMPLES']
    result_class: Literal['CALCULATED']
    prediction: Literal['NONE']


class CheckSpec(Input):
    type: TrendType
    statistic: str
    criteria: dict
    description: str


class CheckCatalog(Input):
    checks: list[CheckSpec]
    limits: dict
