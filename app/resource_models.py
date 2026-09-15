"""Resource registry: operator-uploaded content, hash-verified storage, versions, reference links; never deletion."""
import base64
import binascii
from typing import Annotated, Literal
from pydantic import Field, field_validator
from app.models import Input, Text

MAX_CONTENT_BYTES = 4 * 1024 * 1024  # bounded single upload for the target hardware resource frame; split larger files externally

ResourceKind = Literal['file', 'image', 'pdf', 'cad', 'measurement', 'dataset', 'database_result',
                       'query', 'software', 'configuration', 'log']
ResourceState = Literal['active', 'deactivated']
LinkState = Literal['active', 'unlinked']


class _ContentInput(Input):
    content_base64: Annotated[str, Field(min_length=1, max_length=6_000_000)]

    @field_validator('content_base64')
    @classmethod
    def decode_bounded(cls, value):
        try:
            data = base64.b64decode(value, validate=True)
        except (binascii.Error, ValueError):
            raise ValueError('content_base64 must be valid single-line base64')
        if not data:
            raise ValueError('content must not be empty')
        if len(data) > MAX_CONTENT_BYTES:
            raise ValueError(f'content exceeds the {MAX_CONTENT_BYTES}-byte single-upload bound')
        return value


class ResourceUploadInput(_ContentInput):
    name: Annotated[str, Field(min_length=1, max_length=200)]
    kind: ResourceKind
    source: Text  # declared origin; operator assertion, never verified
    description: str = Field(default='', max_length=2000)


class NewVersionInput(_ContentInput):
    note: str = Field(default='', max_length=2000)


class LinkInput(Input):
    target_kind: Literal['task', 'project']
    target_id: str


class UnlinkInput(Input):
    link_id: str


class ResourceDeactivateInput(Input):
    confirm: Literal[True]
    reason: Text


class Resource(Input):
    id: str
    family_id: str
    version: int = Field(ge=1)
    predecessor_id: str | None
    name: str
    kind: ResourceKind
    source: str
    description: str
    version_note: str
    sha256: str
    size_bytes: int
    tier: Literal['local', 'sd']
    key: str
    state: ResourceState
    created_by: str
    created_at: str
    deactivated_at: str | None = None


class ResourceLink(Input):
    id: str
    resource_id: str
    target_kind: Literal['task', 'project']
    target_id: str
    state: LinkState
    created_by: str
    created_at: str
    unlinked_at: str | None = None


class PreviewResult(Input):
    encoding: Literal['TEXT', 'BINARY']
    text_preview: str | None
    char_count: int | None
    size_bytes: int


class CompareResult(Input):
    left_id: str
    right_id: str
    relation: Literal['IDENTICAL', 'DIFFERENT']
    left_sha256: str
    right_sha256: str
    left_size_bytes: int
    right_size_bytes: int
    common_prefix_bytes: int
    common_suffix_bytes: int
