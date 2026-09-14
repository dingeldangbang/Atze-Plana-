"""Telemetry: real device-submitted measurements only; no invented values or hardware claims."""
from datetime import datetime
from typing import Annotated, Literal
from pydantic import Field, field_validator
from app.models import Input, Text

Kind = Literal['voltage', 'current', 'rpm', 'temperature', 'imu', 'throttle', 'steering', 'speed', 'custom']
Quality = Literal['ok', 'suspect']


class DeviceInput(Input):
    name: Annotated[str, Field(min_length=1, max_length=120)]
    description: str = Field(default='', max_length=2000)


class Device(DeviceInput):
    id: str
    state: Literal['active', 'deactivated']
    created_at: str
    deactivated_at: str | None = None


class DeclaredRange(Input):
    minimum: float = Field(allow_inf_nan=False)
    maximum: float = Field(allow_inf_nan=False)


class SensorInput(Input):
    name: Annotated[str, Field(min_length=1, max_length=120)]
    kind: Kind
    unit: str = Field(default='', max_length=32)
    declared_range: DeclaredRange | None = None
    identification: Literal['IDENTIFIED', 'UNKNOWN'] = 'UNKNOWN'
    note: str = Field(default='', max_length=2000)

    @field_validator('declared_range')
    @classmethod
    def ordered_range(cls, value):
        if value is not None and value.minimum >= value.maximum:
            raise ValueError('declared_range minimum must be lower than maximum')
        return value

    @field_validator('unit')
    @classmethod
    def unit_is_label_only(cls, value):
        if len(value.encode()) > 32:
            raise ValueError('unit is a display label, not a verified calibration')
        return value


class Sensor(SensorInput):
    id: str
    device_id: str
    state: Literal['active', 'deactivated']
    created_at: str
    deactivated_at: str | None = None


class Sample(Input):
    sensor_id: str
    value: float = Field(allow_inf_nan=False)
    timestamp: str  # device-declared ISO-8601; validated and stored verbatim, never invented
    quality: Quality = 'ok'

    @field_validator('timestamp')
    @classmethod
    def aware_iso_timestamp(cls, value):
        try:
            parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError('timestamp must be ISO-8601')
        if parsed.utcoffset() is None:
            raise ValueError('timestamp must include a UTC offset')
        return value


class IngestInput(Input):
    samples: list[Sample] = Field(min_length=1, max_length=1000)
    session: str = Field(default='', max_length=120)
    conditions: str = Field(default='', max_length=2000)


class Batch(Input):
    id: str
    device_id: str
    session: str
    conditions: str
    received_at: str
    sample_count: int
    first_timestamp: str
    last_timestamp: str
    sensor_ids: list[str]
    flagged_out_of_range: int
    suspect_samples: int
    sha256: str
    size_bytes: int
    tier: Literal['local', 'sd']
    key: str
    version: Literal[1] = 1


class BatchSamples(Input):
    batch: Batch
    samples: list[Sample]
    model_config = {'str_strip_whitespace': False}


class DeactivateInput(Input):
    confirm: Literal[True]
    reason: Text
