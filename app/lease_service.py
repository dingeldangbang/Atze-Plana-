"""Lease lifecycle: create, compute effective state, consume exactly once per authorized use."""
from datetime import datetime, timedelta

from fastapi import HTTPException
from pydantic import field_validator

from app.lease_models import LeaseCreate, MAX_TTL_HOURS
from app.store import get, put, audit, identity, now
from app.context import update


def _parse_expires(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        raise ValueError('expires_at must be ISO-8601 with UTC offset')
    if parsed.utcoffset() is None:
        raise ValueError('expires_at must include a UTC offset')
    return parsed


class LeaseValidation(LeaseCreate):

    @field_validator('expires_at')
    @classmethod
    def bounded_future(cls, value):
        parsed = _parse_expires(value)
        moment = datetime.now(parsed.tzinfo)
        if parsed <= moment:
            raise ValueError('expires_at must lie in the future')
        if parsed > moment + timedelta(hours=MAX_TTL_HOURS):
            raise ValueError(f'expires_at must not exceed a {MAX_TTL_HOURS}-hour TTL')
        return value


def effective_state(lease: dict) -> str:
    """Stored state is append-only; expiry/exhaustion are computed, never silently rewritten."""
    if lease['state'] == 'revoked':
        return 'revoked'
    if datetime.fromisoformat(lease['expires_at'].replace('Z', '+00:00')) <= datetime.now(
            datetime.fromisoformat(lease['expires_at'].replace('Z', '+00:00')).tzinfo):
        return 'expired'
    if lease['uses_count'] >= lease['max_uses']:
        return 'exhausted'
    return 'active'


def public(lease: dict) -> dict:
    value = dict(lease)
    value['effective_state'] = effective_state(lease)
    value['uses_remaining'] = max(0, lease['max_uses'] - lease['uses_count'])
    return value


def create_lease(db, who, body: LeaseCreate) -> dict:
    from app.storage import guard
    guard(db)  # granting permissions under emergency stop is blocked; revocation stays allowed
    target = get(db, body.scope_kind, body.scope_id)  # scope must be a real existing record
    if body.tool is not None:
        from app.mcp_client import CANDIDATES
        if body.tool not in CANDIDATES:
            raise HTTPException(422, 'Lease tool must be in the MCP allowlist')
    _parse_expires(body.expires_at)  # shape checked again here for direct service use
    value = dict(id=identity(), action=body.action, scope_kind=body.scope_kind, scope_id=body.scope_id,
                 scope_name=target.get('name') or target.get('title') or target['id'],
                 tool=body.tool, expires_at=body.expires_at, max_uses=body.max_uses, uses_count=0,
                 state='active', created_at=now(), created_by=who, reason=body.reason,
                 revoked_at=None, revoke_reason=None)
    put(db, 'lease', value)
    audit(db, who, 'lease.created', value['id'],
          {'action': value['action'], 'scope_kind': value['scope_kind'], 'scope_id': value['scope_id'],
           'tool': value['tool'], 'expires_at': value['expires_at'], 'max_uses': value['max_uses']})
    return value


def consume_lease(db, who, action: str, task_id: str, tool: str) -> dict:
    """Authorize one use: the lease substitutes the per-call human consent, never a technical gate.

    A use is consumed at reservation time — a later transport failure does not refund it.
    """
    task = get(db, 'task', task_id)
    rows = db.execute("SELECT body FROM records WHERE kind='lease' ORDER BY seq").fetchall()
    import json as _json
    candidates = [_json.loads(row[0]) for row in rows]
    matching = [lease for lease in candidates
                if lease['action'] == action and lease['state'] == 'active'
                and ((lease['scope_kind'] == 'task' and lease['scope_id'] == task_id)
                     or (lease['scope_kind'] == 'project' and lease['scope_id'] == task['project_id']))
                and (lease['tool'] is None or lease['tool'] == tool)]
    usable = [lease for lease in matching if effective_state(lease) == 'active']
    if not usable:
        detail = 'Permission lease required: no active lease covers this action, scope and tool'
        if matching:
            detail = f"Permission lease not usable ({'/'.join(sorted({effective_state(l) for l in matching}))})"
        raise HTTPException(403, detail)
    lease = usable[0]
    lease['uses_count'] += 1
    update(db, lease)
    audit(db, who, 'lease.used', lease['id'],
          {'action': action, 'task_id': task_id, 'tool': tool,
           'uses_remaining': max(0, lease['max_uses'] - lease['uses_count'])})
    return lease


def revoke_lease(db, who, lease_id: str, reason: str) -> dict:
    lease = get(db, 'lease', lease_id)
    if lease['state'] == 'revoked':
        raise HTTPException(409, 'Lease is already revoked')
    lease.update(state='revoked', revoked_at=now(), revoke_reason=reason)
    update(db, lease)
    audit(db, who, 'lease.revoked', lease['id'], {'reason': reason})
    return lease
