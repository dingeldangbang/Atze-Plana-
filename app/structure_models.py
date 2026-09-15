"""AXM structure builder MVP: versioned declarative sitemap/component models; CALCULATED generation, no file writes."""
from typing import Annotated, Literal

from pydantic import Field

from app.models import Input

NodeKind = Literal['page', 'section', 'component', 'action', 'data']
EdgeKind = Literal['contains', 'triggers', 'depends_on']
MAX_NODES = 64
MAX_EDGES = 128
LOCAL_ID_PATTERN = r'^[a-z0-9][a-z0-9_-]{0,63}$'


class StructureInput(Input):
    name: Annotated[str, Field(min_length=1, max_length=120)]
    description: str = Field(default='', max_length=2000)


class Structure(StructureInput):
    id: str
    version: int
    state: Literal['active', 'deactivated']
    created_at: str
    created_by: str
    deactivated_at: str | None = None


class NodeInput(Input):
    local_id: Annotated[str, Field(pattern=LOCAL_ID_PATTERN)]
    kind: NodeKind
    name: Annotated[str, Field(min_length=1, max_length=120)]
    permissions: list[Annotated[str, Field(min_length=1, max_length=64)]] = Field(default_factory=list, max_length=8)
    note: str = Field(default='', max_length=2000)


class EdgeInput(Input):
    source: Annotated[str, Field(min_length=1, max_length=64)]
    target: Annotated[str, Field(min_length=1, max_length=64)]
    kind: EdgeKind


class VersionInput(Input):
    nodes: list[NodeInput] = Field(min_length=1, max_length=MAX_NODES)
    edges: list[EdgeInput] = Field(default_factory=list, max_length=MAX_EDGES)
    note: str = Field(default='', max_length=2000)


class StructureCreateInput(VersionInput):
    name: Annotated[str, Field(min_length=1, max_length=120)]
    description: str = Field(default='', max_length=2000)


class StructureDeactivateInput(Input):
    confirm: Literal[True]
    reason: Annotated[str, Field(min_length=8, max_length=500)]


class StructureVersion(Input):
    id: str
    structure_id: str
    version: int
    predecessor_id: str | None
    nodes: list[dict]
    edges: list[dict]
    manifest_hash: str
    note: str
    created_at: str
    created_by: str
