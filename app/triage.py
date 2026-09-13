"""Deterministic policy; no execution, tool calls, or model-generated approval."""
from app.models import Decision


def evaluate(task, evidence, stop_active=False, approval_id=None):
    action = task['action']
    risk = 'low' if action == 'read' else 'medium' if action == 'write' else 'high'
    reasons = []
    if stop_active:
        reasons.append('Emergency stop is active')
    if not task['preconditions_met']:
        reasons.append('Preconditions not attested by operator')
    if not evidence:
        reasons.append('Evidence is required')
    if any(e['state'] != 'verified' for e in evidence):
        reasons.append('All evidence must be reviewed and verified')
    confidence = min((e['confidence'] for e in evidence), default=0.0)
    if confidence < 0.8:
        reasons.append('Minimum reported evidence confidence is below 0.8')
    state = 'blocked'
    if not reasons:
        state = 'eligible' if action == 'read' else 'approved' if approval_id else 'approval_required'
        reasons = ['Read is policy-eligible; no execution implemented' if action == 'read' else
                   'Human approval recorded; no execution implemented' if approval_id else
                   'Non-read actions require separate reviewer approval']
    return Decision(task_id=task['id'], state=state, risk=risk, reasons=reasons,
                    evidence_ids=task['evidence_ids'], confidence=confidence,
                    approval_id=approval_id)
