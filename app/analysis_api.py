"""Evidence analysis: deterministic contradiction candidates and source ranking; CALCULATED, never truth."""
import json

from fastapi import Depends, Query

from app.models import Input
from app.store import get


class ContradictionQuery(Input):
    project_id: str


def _project_evidence(db, project_id):
    project = get(db, 'project', project_id)  # 404 if unknown
    rows = db.execute("SELECT body FROM records WHERE kind='evidence' AND json_extract(body,'$.\"project_id\"')=? ORDER BY seq",
                      (project_id,)).fetchall()
    return project, [json.loads(row[0]) for row in rows]


def _observations(evidence):
    """Flatten (evidence, observation) pairs; an evidence may carry zero or more declared observations."""
    return [(evidence, observation) for evidence in evidence for observation in evidence.get('observations', [])]


def _same_value(left, right):
    if left.get('unit') != right.get('unit'):
        return False
    try:
        return float(left['value']) == float(right['value'])
    except (TypeError, ValueError):
        return str(left.get('value')) == str(right.get('value'))


def contradictions(project_id, evidence):
    """Deterministic grouping by (subject, attribute); differing value/unit pairs are CANDIDATES, never verdicts."""
    pairs = _observations(evidence)
    groups = {}
    for record, observation in pairs:
        groups.setdefault((str(observation.get('subject', '')).strip(), str(observation.get('attribute', '')).strip()), []).append((record, observation))
    candidates, corroborated = [], []
    for (subject, attribute), members in sorted(groups.items()):
        if not subject or not attribute:
            continue
        values = [{'value': o.get('value'), 'unit': o.get('unit'), 'evidence_id': r['id'],
                   'evidence_state': r['state'], 'observed_at': r['observed_at'], 'provider': r['provider']}
                  for r, o in members]
        conflicting = []
        for index, (_, observation) in enumerate(members):
            if any(not _same_value(observation, other) for _, other in members[index + 1:]):
                conflicting.append(index)
        if conflicting:
            scope = 'within_record' if len({r['id'] for r, _ in members}) == 1 else 'across_records'
            candidates.append({'subject': subject, 'attribute': attribute, 'scope': scope, 'values': values})
        elif len(members) > 1:
            corroborated.append({'subject': subject, 'attribute': attribute, 'occurrences': len(members), 'values': values})
    return {'project_id': project_id, 'evidence_count': len(evidence), 'observation_count': len(pairs),
            'contradiction_candidates': candidates, 'corroborated_subject_attributes': corroborated,
            'result_class': 'CALCULATED', 'prediction': 'NONE',
            'method': 'deterministic exact-match grouping on (subject, attribute) after whitespace strip; value/unit equality (numeric when both parse as float)',
            'limits': 'Contradictions are candidates for human resolution, never verdicts; missing subjects/attributes are not grouped; CONTRADICTED in the status vocabulary means candidate here'}


RANKING = {'verified': 3, 'unverified': 2, 'rejected': 1}


def source_ranking(project_id, evidence):
    """Documented deterministic order: review state, then declared confidence, then recency. Not source quality truth."""
    ranked = sorted(evidence, key=lambda e: (RANKING.get(e['state'], 0), e['confidence'], e['observed_at']), reverse=True)
    rows = [{'rank': index + 1, 'evidence_id': record['id'], 'claim': record['claim'], 'state': record['state'],
             'confidence': record['confidence'], 'observed_at': record['observed_at'], 'provider': record['provider'],
             'source_type': record['source_type'],
             'rule_trace': [f"review_state={record['state']}", f"confidence={record['confidence']}",
                            f"observed_at={record['observed_at']}"]}
            for index, record in enumerate(ranked)]
    return {'project_id': project_id, 'evidence_count': len(evidence), 'ranking': rows,
            'result_class': 'CALCULATED', 'prediction': 'NONE',
            'rules': ['1. review state (verified > unverified > rejected)', '2. declared confidence (higher first)',
                      '3. observation recency (newer first)'],
            'limits': 'The ranking is a documented deterministic order over declared fields, not a truth or source-quality guarantee; confidence and provider are owner assertions; EXTERNAL_SOURCE discipline still applies'}


def register_analysis_api(app, actor, connection, store):
    DB = Depends(connection, scope='function')

    @app.post('/api/analysis/contradictions', tags=['analysis'],
              openapi_extra={'x-role': 'both', 'x-side-effects': 'None; deterministic CALCULATED query over stored evidence observations; contradiction output is a candidate set for human resolution, never a verdict, never auto-adopted'})
    def contradictions_endpoint(body: ContradictionQuery, who=Depends(actor), db=DB) -> dict:
        _, evidence = _project_evidence(db, body.project_id)
        return contradictions(body.project_id, evidence)

    @app.get('/api/analysis/source-ranking', tags=['analysis'],
             openapi_extra={'x-role': 'both', 'x-side-effects': 'None; deterministic CALCULATED ranking over declared fields (review state, confidence, recency); not a truth or source-quality claim'})
    def ranking_endpoint(project_id: str = Query(min_length=1), who=Depends(actor), db=DB) -> dict:
        _, evidence = _project_evidence(db, project_id)
        return source_ranking(project_id, evidence)
