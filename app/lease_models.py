"""Permission leases: bounded, expiring, revocable pre-grants; never a substitute for technical gates."""
from typing import Annotated, Literal
from pydantic import Field

from app.models import Input, Text

LeaseAction = Literal['mcp.tools_call']  # only actions with a real enforcement path may be leased
MAX_TTL_HOURS = 24
MAX_USES = 100


class LeaseCreate(Input):
    action: LeaseAction
    scope_kind: Literal['task', 'project']
    scope_id: str
    tool: str | None = None  # optional: bind the lease to exactly one allowlisted tool
    expires_at: str  # ISO-8601 with UTC offset; required, bounded TTL (see lease_service)
    max_uses: Annotated[int, Field(ge=1, le=MAX_USES)] = 1
    reason: Text


class LeaseRevoke(Input):
    confirm: Literal[True]
    reason: Text
