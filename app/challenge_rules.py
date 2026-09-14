"""Independent deterministic rule engine, run by a separate credentialed process.

No prompts, web fetching, invented observations or general semantic truth checking.
"""
import hashlib
from decimal import Decimal, InvalidOperation
from app.challenge_models import Analysis

POLICY_VERSION = 'challenge-2-context'
MAX_PROJECT_EVIDENCE = 500
MAX_SNAPSHOT_EVIDENCE_BYTES = 4 * 1024 * 1024
MAX_FINDINGS = 500
UNKNOWN = {'?', 'unknown', 'unbekannt', 'unspecified', 'n/a', 'nan', 'inf', '-inf', 'infinity', '-infinity', 'not known', '*'}


def normalized(value):
    return value.strip().casefold()


def equal_value(a, b):
    try:
        x, y = Decimal(a), Decimal(b)
        if x.is_finite() and y.is_finite():
            return x == y
    except InvalidOperation:
        pass
    return normalized(a) == normalized(b)


def analyze(snapshot):
    task, result, evidence = snapshot['task'], snapshot['result'], snapshot['evidence']
    by_id = {item['id']: item for item in evidence}
    findings, alternatives = [], []
    omitted = 0

    def add(check, severity, code, message, ids=(), next_validation='Review the referenced original evidence and record missing inputs'):
        nonlocal omitted
        if len(findings) >= MAX_FINDINGS:
            omitted += 1
            return
        findings.append(dict(check=check, severity=severity, code=code, message=message,
                             evidence_ids=list(ids), next_validation=next_validation))

    if snapshot.get('plan_context') and snapshot['plan_context']['state'] != 'CURRENT':
        add('evidence', 'block', 'PLAN_CONTEXT_NOT_CURRENT', 'Task PLAN lacks a current verified context binding; no permission or truth inferred')
    if snapshot.get('truncated'):
        add('evidence', 'block', 'SCOPE_LIMIT', 'Project evidence exceeds bounded challenge scope; no partial PASS')
    referenced = set(task['evidence_ids'])
    for item in result['claims'] + result['alternatives']:
        referenced.update(item['evidence_ids'])
    for key in sorted(referenced):
        item = by_id.get(key)
        if not item:
            add('evidence', 'block', 'MISSING_SOURCE', 'Referenced source is missing', [key])
            continue
        if hashlib.sha256(item['content'].encode()).hexdigest() != item['sha256']:
            add('evidence', 'block', 'SOURCE_HASH', 'Source text does not match stored SHA-256', [key])
        if item['state'] == 'rejected':
            add('evidence', 'block', 'REJECTED_SOURCE', 'Referenced evidence is rejected', [key])
        elif item['state'] != 'verified' or item['confidence'] < 0.8:
            add('evidence', 'condition', 'UNVALIDATED_SOURCE', 'Source review or reported confidence is insufficient', [key])
    observations = [(e, o) for e in evidence for o in e.get('observations', []) if e['state'] != 'rejected']
    for index, claim in enumerate(result['claims']):
        if any(normalized(claim[k]) in UNKNOWN for k in ['subject', 'variant', 'revision', 'attribute', 'value', 'unit', 'conditions']):
            add('evidence', 'condition', 'UNKNOWN_PARAMETER', f'Claim {index}: explicit unknown/sentinel parameter is not verified identity or measurement', claim['evidence_ids'])
        matching = []
        for e, observation in observations:
            if all(normalized(observation[k]) == normalized(claim[k]) for k in ['subject', 'variant', 'revision', 'attribute']):
                if any(normalized(observation[k]) != normalized(claim[k]) for k in ['unit', 'conditions']):
                    if e['id'] in claim['evidence_ids']:
                        add('consistency', 'condition', 'INCOMPARABLE', f'Claim {index}: units or test conditions differ; no conversion/normalization assumed', [e['id']])
                    continue
                matching.append((e, observation))
                if not equal_value(observation['value'], claim['value']):
                    add('consistency', 'block', 'CONTRADICTION', f"Claim {index}: {claim['value']} conflicts with {observation['value']} {observation['unit']} for identical declared identity/conditions", [e['id']], 'Resolve variant/revision/date/conditions against original sources; do not choose a preferred value')
        support = [(e, o) for e, o in matching if e['id'] in claim['evidence_ids'] and e['state'] == 'verified' and equal_value(o['value'], claim['value'])]
        if not support:
            add('evidence', 'condition', 'IDENTITY_OR_SUPPORT_UNKNOWN', f'Claim {index}: no verified structured support for exact subject/variant/revision/property/value', claim['evidence_ids'])
        else:
            add('evidence', 'info', 'STRUCTURED_SUPPORT', f'Claim {index}: matching submitted structured observation; not independently extracted truth', [e['id'] for e, _ in support])
        if claim['requires_measurement'] and not any(o['basis'] == 'measurement' and e['source_type'] == 'measurement' for e, o in support):
            add('evidence', 'condition', 'MEASUREMENT_MISSING', f'Claim {index}: real-measurement provenance not recorded; manufacturer/manual statement is not measurement', claim['evidence_ids'], result['falsification_test'])
        if claim['causal']:
            add('causality', 'condition', 'CAUSALITY_UNPROVEN', f'Claim {index}: no validated controlled-experiment contract is implemented; correlation is not causation', claim['evidence_ids'], result['falsification_test'])
        # Counter-candidates are discovered from all project evidence, not invented names.
        for e, o in observations:
            if normalized(o['subject']) != normalized(claim['subject']) and e['state'] == 'verified' and all(normalized(o[k]) == normalized(claim[k]) for k in ['attribute', 'unit', 'conditions']) and equal_value(o['value'], claim['value']):
                candidate = dict(subject=o['subject'], variant=o['variant'], revision=o['revision'], evidence_id=e['id'], attribute=o['attribute'], value=o['value'], unit=o['unit'], scope='matches this property only; not a suitability recommendation')
                if len(alternatives) < 50 and candidate not in alternatives:
                    alternatives.append(candidate)
    if not any(f['check'] == 'consistency' for f in findings):
        add('consistency', 'info', 'NO_STRUCTURED_CONFLICT', 'No contradiction found in submitted comparable structured observations; not proof of absence elsewhere')
    supported_alternatives = []
    for candidate in result['alternatives']:
        refs = [by_id[k] for k in candidate['evidence_ids'] if k in by_id]
        if refs and all(e['state'] == 'verified' for e in refs) and any(normalized(o['subject']) == normalized(candidate['subject']) for e in refs for o in e.get('observations', [])):
            supported_alternatives.append(candidate['subject'])
        else:
            add('alternative', 'condition', 'ALTERNATIVE_UNSUPPORTED', f"Declared alternative {candidate['subject']} lacks verified identity support", candidate['evidence_ids'])
    if not alternatives and not supported_alternatives:
        add('alternative', 'condition', 'NO_ALTERNATIVE', 'No evidence-backed alternative found in submitted project scope; none invented', next_validation='Research and document a comparable alternative, including exclusion rationale')
    else:
        add('alternative', 'info', 'ALTERNATIVES_FOUND', 'Evidence-backed counter-candidates or documented alternatives found; ranking is not independently validated')
    if not any(f['check'] == 'causality' for f in findings):
        add('causality', 'info', 'NO_DECLARED_CAUSAL_CLAIM', 'No causal claim declared; free-text causality is not semantically inferred')
    if normalized(result['falsification_test']) in UNKNOWN:
        add('causality', 'condition', 'NO_FALSIFICATION_TEST', 'Falsification proposal is explicitly unknown; no test invented')
    for uncertainty in result['unknowns']:
        add('evidence', 'condition', 'DECLARED_UNKNOWN', uncertainty, next_validation=result['falsification_test'])
    if not task['preconditions_met']:
        add('action', 'block', 'PRECONDITIONS', 'Task preconditions are not attested')
    if task['action'] not in {'read', 'write'}:
        add('action', 'condition', 'INDEPENDENT_LIVE_VALIDATION_REQUIRED', 'High-impact action lacks independently validated device/provider/permission evidence; different URLs alone do not establish independence')
    if result['kind'] == 'action':
        add('action', 'block', 'NO_EXECUTOR', 'No execution adapter/permission contract is implemented; an action result cannot authorize execution')
    elif result['kind'] == 'calculation':
        add('evidence', 'condition', 'CALCULATION_NOT_RECOMPUTED', 'No general calculation parser/recomputation implemented; structured value match is not a numerical proof')
    if not any(f['check'] == 'action' for f in findings):
        add('action', 'info', 'RECOMMENDATION_ONLY', 'Metadata recommendation only; human approval for non-read and no external execution')
    if omitted:
        findings.append(dict(check='evidence', severity='block', code='FINDING_LIMIT', message=f'{omitted} additional findings exceed bounded scope; no partial PASS', evidence_ids=[], next_validation='Reduce/split the result scope for complete review'))
    verdict = 'BLOCK' if any(f['severity'] == 'block' for f in findings) else 'CONDITIONAL' if any(f['severity'] == 'condition' for f in findings) else 'PASS'
    return Analysis(verdict=verdict, findings=findings, alternatives=alternatives[:50], policy_version=POLICY_VERSION)
