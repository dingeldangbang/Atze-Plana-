"""Structure builder API: operator-created versioned models, both-role reads, deterministic generation, confirmed deactivation."""
import json
from types import SimpleNamespace

from fastapi import Depends, HTTPException

from app.structure_models import (Structure, StructureCreateInput, StructureDeactivateInput,
                                  StructureVersion, VersionInput)
from app.structure_service import generate_routes, generate_skeleton, manifest_hash, stored_hash, validate_model
from app.store import get, listing, put, audit, identity, now, stopped


def register_structure_api(app, actor, operator, reviewer, connection, store):
    DB = Depends(connection, scope='function')

    def current_version(db, structure_id):
        row = db.execute("SELECT body FROM records WHERE kind='structure_version' "
                         "AND json_extract(body,'$.\"structure_id\"')=? "
                         "ORDER BY json_extract(body,'$.\"version\"') DESC LIMIT 1", (structure_id,)).fetchone()
        if row is None:
            raise HTTPException(409, 'Structure has no version yet')
        return json.loads(row[0])

    @app.post('/api/structures', response_model=Structure, status_code=201, tags=['structures'],
              openapi_extra={'x-role': 'operator', 'x-side-effects': 'Create a structure registry entry plus immutable version 1 from the fully specified model; structural validation (unique local ids, edge endpoints, contains forest, unique generated routes) before persistence; stop blocks'})
    def create(body: StructureCreateInput, who=Depends(operator), db=DB) -> dict:
        if stopped(db)['active']:
            raise HTTPException(409, 'Emergency stop blocks structure creation')
        validate_model(body.nodes, body.edges)
        structure = dict(id=identity(), name=body.name, description=body.description, version=1,
                         state='active', created_at=now(), created_by=who, deactivated_at=None)
        version = dict(id=identity(), structure_id=structure['id'], version=1, predecessor_id=None,
                       nodes=[node.model_dump() for node in body.nodes],
                       edges=[edge.model_dump() for edge in body.edges],
                       manifest_hash=manifest_hash(body.nodes, body.edges), note=body.note,
                       created_at=now(), created_by=who)
        put(db, 'structure', structure)
        put(db, 'structure_version', version)
        audit(db, who, 'structure.created', structure['id'],
              {'name': body.name, 'version': 1, 'nodes': len(body.nodes), 'edges': len(body.edges),
               'manifest_hash': version['manifest_hash']})
        return structure

    @app.get('/api/structures', response_model=list[Structure], tags=['structures'],
             openapi_extra={'x-role': 'both', 'x-side-effects': 'None; read-only registry'})
    def structures(limit: int = 100, offset: int = 0, who=Depends(actor), db=DB) -> list[dict]:
        return listing(db, 'structure', limit, offset)

    @app.get('/api/structures/{structure_id}', response_model=Structure, tags=['structures'],
             openapi_extra={'x-role': 'both', 'x-side-effects': 'None; read-only single structure'})
    def structure(structure_id: str, who=Depends(actor), db=DB) -> dict:
        return get(db, 'structure', structure_id)

    @app.get('/api/structures/{structure_id}/versions', response_model=list[StructureVersion], tags=['structures'],
             openapi_extra={'x-role': 'both', 'x-side-effects': 'None; immutable append-only version history with manifest hashes'})
    def versions(structure_id: str, limit: int = 100, offset: int = 0, who=Depends(actor), db=DB) -> list[dict]:
        get(db, 'structure', structure_id)
        rows = db.execute("SELECT body FROM records WHERE kind='structure_version' "
                          "AND json_extract(body,'$.\"structure_id\"')=? "
                          "ORDER BY json_extract(body,'$.\"version\"') DESC LIMIT ? OFFSET ?",
                          (structure_id, limit, offset)).fetchall()
        return [json.loads(row[0]) for row in rows]

    @app.post('/api/structures/{structure_id}/versions', response_model=StructureVersion, status_code=201, tags=['structures'],
              openapi_extra={'x-role': 'operator', 'x-side-effects': 'Append a new immutable fully-specified model version (predecessor chain; identical manifest rejected 409; full validation; stop blocks); previous versions stay unchanged'})
    def new_version(structure_id: str, body: VersionInput, who=Depends(operator), db=DB) -> dict:
        if stopped(db)['active']:
            raise HTTPException(409, 'Emergency stop blocks structure versions')
        structure = get(db, 'structure', structure_id)
        if structure['state'] != 'active':
            raise HTTPException(409, 'Structure is deactivated')
        validate_model(body.nodes, body.edges)
        previous = current_version(db, structure_id)
        digest = manifest_hash(body.nodes, body.edges)
        if digest == previous['manifest_hash']:
            raise HTTPException(409, 'Identical model content; a new version must change the model')
        version = dict(id=identity(), structure_id=structure_id, version=previous['version'] + 1,
                       predecessor_id=previous['id'],
                       nodes=[node.model_dump() for node in body.nodes],
                       edges=[edge.model_dump() for edge in body.edges],
                       manifest_hash=digest, note=body.note, created_at=now(), created_by=who)
        put(db, 'structure_version', version)
        structure['version'] = version['version']
        from app.context import update
        update(db, structure)
        audit(db, who, 'structure.versioned', structure_id,
              {'version': version['version'], 'predecessor_id': previous['id'], 'nodes': len(body.nodes),
               'edges': len(body.edges), 'manifest_hash': digest})
        return version

    @app.get('/api/structures/{structure_id}/generate', tags=['structures'],
             openapi_extra={'x-role': 'both', 'x-side-effects': 'None; deterministic CALCULATED generation of the routing overview and the UI placeholder skeleton from one stored version; no file is written, no code is executed; empty placeholders, never invented content'})
    def generate(structure_id: str, version: int = 0, who=Depends(actor), db=DB) -> dict:
        get(db, 'structure', structure_id)
        if version:
            row = db.execute("SELECT body FROM records WHERE kind='structure_version' "
                             "AND json_extract(body,'$.\"structure_id\"')=? "
                             "AND json_extract(body,'$.\"version\"')=?", (structure_id, version)).fetchone()
            if row is None:
                raise HTTPException(404, 'Requested structure version not found')
            record = json.loads(row[0])
        else:
            record = current_version(db, structure_id)
        if stored_hash(record) != record['manifest_hash']:
            raise HTTPException(503, 'Stored version does not match its manifest hash; generation refused')
        nodes = [SimpleNamespace(**item) for item in record['nodes']]
        edges = [SimpleNamespace(**item) for item in record['edges']]
        return {'structure_id': structure_id, 'version': record['version'], 'manifest_hash': record['manifest_hash'],
                'routes': generate_routes(nodes, edges),
                'ui_skeleton': generate_skeleton(nodes, edges),
                'result_class': 'CALCULATED', 'prediction': 'NONE',
                'basis': 'STRUCTURE_VERSION_MANIFEST',
                'limits': 'Routing overview and empty UI placeholders derived deterministically from the stored model version; placeholders carry no content, permissions are declared metadata (not enforced authorization), generation writes no files'}

    @app.post('/api/structures/{structure_id}/deactivate', response_model=Structure, tags=['structures'],
              openapi_extra={'x-role': 'reviewer', 'x-side-effects': 'Confirmed deactivation + audit; all versions and history are retained; no deletion endpoint exists; stop blocks'})
    def deactivate(structure_id: str, body: StructureDeactivateInput, who=Depends(reviewer), db=DB) -> dict:
        if stopped(db)['active']:
            raise HTTPException(409, 'Emergency stop blocks structure deactivation')
        value = get(db, 'structure', structure_id)
        if value['state'] != 'active':
            raise HTTPException(409, 'Structure is already deactivated')
        value.update(state='deactivated', deactivated_at=now())
        from app.context import update
        update(db, value)
        audit(db, who, 'structure.deactivated', value['id'], {'reason': body.reason})
        return value
