"""Lease registry API: reviewer grants, both roles read, reviewer-confirmed revocation (allowed under stop)."""
from fastapi import Depends

from app.lease_models import LeaseCreate, LeaseRevoke
from app.lease_service import LeaseValidation, create_lease, effective_state, public, revoke_lease
from app.store import get, listing


def register_lease_api(app, actor, reviewer, connection, store):
    DB = Depends(connection, scope='function')

    @app.post('/api/leases', status_code=201, tags=['leases'],
              openapi_extra={'x-role': 'reviewer', 'x-side-effects': 'Grant a bounded, expiring, revocable permission lease (Allow Once/Task/Temporary); scope must exist; TTL <= 24h; stop blocks granting, never revoking; a lease substitutes per-call human consent only, never technical gates; audit lease.created'})
    def create(body: LeaseValidation, who=Depends(reviewer), db=DB) -> dict:
        return public(create_lease(db, who, body))

    @app.get('/api/leases', tags=['leases'],
             openapi_extra={'x-role': 'both', 'x-side-effects': 'None; read-only registry with computed effective state (active/expired/exhausted/revoked); stored records stay append-only'})
    def leases(limit: int = 100, offset: int = 0, who=Depends(actor), db=DB) -> list[dict]:
        return [public(lease) for lease in listing(db, 'lease', limit, offset)]

    @app.get('/api/leases/{lease_id}', tags=['leases'],
             openapi_extra={'x-role': 'both', 'x-side-effects': 'None; read-only single lease with computed effective state'})
    def lease(lease_id: str, who=Depends(actor), db=DB) -> dict:
        return public(get(db, 'lease', lease_id))

    @app.post('/api/leases/{lease_id}/revoke', tags=['leases'],
              openapi_extra={'x-role': 'reviewer', 'x-side-effects': 'Confirmed revocation + audit; allowed under emergency stop (risk-reducing); lease data retained, no deletion endpoint'})
    def revoke(lease_id: str, body: LeaseRevoke, who=Depends(reviewer), db=DB) -> dict:
        return public(revoke_lease(db, who, lease_id, body.reason))
