"""Resource registry API: uploaded content stored hash-verified; links are references, deactivation retains data."""
import base64
import hashlib
import json
from typing import Annotated
from fastapi import Depends, HTTPException, Query, Response
from app.context import update
from app.resource_models import (CompareResult, LinkInput, NewVersionInput, PreviewResult, Resource,
                                 ResourceDeactivateInput, ResourceKind, ResourceLink, ResourceState,
                                 ResourceUploadInput, UnlinkInput)
from app.store import get, put, audit, identity, now
from app.storage import guard


def register_resource_api(app, actor, operator, reviewer, connection, storage):
    db_dependency = Depends(connection, scope='function')

    def contract(role, effects):
        return {'x-role': role, 'x-side-effects': effects}

    def family_records(db, family_id):
        rows = db.execute("SELECT body FROM records WHERE kind='resource' AND json_extract(body,'$.family_id')=? ORDER BY json_extract(body,'$.version')",
                          (family_id,)).fetchall()
        return [json.loads(row[0]) for row in rows]

    def latest_family_record(db, family_id):
        row = db.execute("SELECT body FROM records WHERE kind='resource' AND json_extract(body,'$.family_id')=? ORDER BY json_extract(body,'$.version') DESC LIMIT 1",
                         (family_id,)).fetchone()
        return json.loads(row[0])

    def store_content(data):
        tier = storage.choose(len(data), 'auto')
        key = storage.write(tier, data)
        return tier, key, hashlib.sha256(data).hexdigest(), len(data)

    @app.post('/api/resources', response_model=Resource, status_code=201, tags=['resources'],
              openapi_extra=contract('operator', 'Append immutable content blob + registry record + audit; hash/size verified on read; content safety/virus scan NOT IMPLEMENTED (operator responsibility); stop blocks'))
    def upload(body: ResourceUploadInput, who=Depends(operator), db=db_dependency):
        guard(db)
        data = base64.b64decode(body.content_base64, validate=True)
        tier, key, digest, size = store_content(data)
        value = dict(id=identity(), family_id=None, version=1, predecessor_id=None,
                     **body.model_dump(exclude={'content_base64'}), version_note='', sha256=digest,
                     size_bytes=size, tier=tier, key=key, state='active', created_by=who,
                     created_at=now(), deactivated_at=None)
        value['family_id'] = value['id']
        put(db, 'resource', value)
        audit(db, who, 'resource.uploaded', value['id'],
              {'name': value['name'], 'kind': value['kind'], 'sha256': digest, 'size_bytes': size, 'version': 1})
        return value

    @app.get('/api/resources', response_model=list[Resource], tags=['resources'],
             openapi_extra=contract('both', 'None; registry metadata only, no content safety or availability claims'))
    def resources(query: Annotated[str | None, Query(max_length=200, description='Name substring or sha256 prefix (>=8 chars)')] = None,
                  kind: ResourceKind | None = None, state: ResourceState | None = None,
                  limit: Annotated[int, Query(ge=1, le=500)] = 50,
                  offset: Annotated[int, Query(ge=0)] = 0, who=Depends(actor), db=db_dependency):
        conditions = ["kind='resource'"]
        params = []
        if kind is not None:
            conditions.append("json_extract(body,'$.kind')=?")
            params.append(kind)
        if state is not None:
            conditions.append("json_extract(body,'$.state')=?")
            params.append(state)
        if query is not None:
            escaped = query.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
            conditions.append("(json_extract(body,'$.name') LIKE ? COLLATE NOCASE ESCAPE '\\' "
                              "OR (length(?) >= 8 AND lower(substr(json_extract(body,'$.sha256'),1,length(?))) = lower(?)))")
            params.extend([f'%{escaped}%', query, query, query])
        rows = db.execute(f"SELECT body FROM records WHERE {' AND '.join(conditions)} ORDER BY seq LIMIT ? OFFSET ?",
                          (*params, limit, offset)).fetchall()
        return [json.loads(row[0]) for row in rows]

    @app.get('/api/resources/{resource_id}', response_model=Resource, tags=['resources'],
             openapi_extra=contract('both', 'None; registry metadata only'))
    def resource_detail(resource_id: str, who=Depends(actor), db=db_dependency):
        return get(db, 'resource', resource_id)

    @app.get('/api/resources/{resource_id}/content', tags=['resources'],
             openapi_extra=contract('both', 'None; hash/size verified blob read; corrupt or unavailable returns 503; raw submitted bytes, not verified content safety'))
    def resource_content(resource_id: str, who=Depends(actor), db=db_dependency):
        value = get(db, 'resource', resource_id)
        data = storage.checked(value)
        return Response(content=data, media_type='application/octet-stream',
                        headers={'X-Atze-Resource-Id': value['id'], 'X-Atze-Family-Id': value['family_id'],
                                 'X-Atze-Sha256': value['sha256'], 'X-Atze-Size-Bytes': str(value['size_bytes']),
                                 'X-Atze-Version': str(value['version'])})

    @app.get('/api/resources/{resource_id}/preview', response_model=PreviewResult, tags=['resources'],
             openapi_extra=contract('both', 'None; hash-verified read; UTF-8 preview or explicit BINARY marker, never interpreted content claims'))
    def resource_preview(resource_id: str, who=Depends(actor), db=db_dependency):
        value = get(db, 'resource', resource_id)
        data = storage.checked(value)
        try:
            text = data.decode('utf-8')
        except UnicodeDecodeError:
            return PreviewResult(encoding='BINARY', text_preview=None, char_count=None, size_bytes=len(data))
        return PreviewResult(encoding='TEXT', text_preview=text[:200], char_count=len(text), size_bytes=len(data))

    @app.get('/api/resources/{resource_id}/versions', response_model=list[Resource], tags=['resources'],
             openapi_extra=contract('both', 'None; immutable family version history'))
    def resource_versions(resource_id: str, who=Depends(actor), db=db_dependency):
        value = get(db, 'resource', resource_id)
        return family_records(db, value['family_id'])

    @app.post('/api/resources/{resource_id}/versions', response_model=Resource, status_code=201, tags=['resources'],
              openapi_extra=contract('operator', 'Append new immutable version blob + record + audit; identical content rejected; deactivated family blocks; stop blocks'))
    def new_version(resource_id: str, body: NewVersionInput, who=Depends(operator), db=db_dependency):
        guard(db)
        current = get(db, 'resource', resource_id)
        latest = latest_family_record(db, current['family_id'])
        if latest['state'] != 'active':
            raise HTTPException(409, 'Resource family is deactivated')
        data = base64.b64decode(body.content_base64, validate=True)
        digest = hashlib.sha256(data).hexdigest()
        if digest == latest['sha256']:
            raise HTTPException(409, 'Identical content is not a new version')
        tier, key, digest, size = store_content(data)
        value = dict(id=identity(), family_id=latest['family_id'], version=latest['version'] + 1,
                     predecessor_id=latest['id'], name=latest['name'], kind=latest['kind'],
                     source=latest['source'], description=latest['description'], version_note=body.note,
                     sha256=digest, size_bytes=size, tier=tier, key=key, state='active', created_by=who,
                     created_at=now(), deactivated_at=None)
        put(db, 'resource', value)
        audit(db, who, 'resource.versioned', value['id'],
              {'family_id': value['family_id'], 'version': value['version'], 'predecessor_id': latest['id'],
               'sha256': digest, 'size_bytes': size})
        return value

    @app.post('/api/resources/{resource_id}/links', response_model=ResourceLink, status_code=201, tags=['resources'],
              openapi_extra=contract('operator', 'Append reference link + audit; no file copy; existing task/project target required; stop blocks'))
    def link_resource(resource_id: str, body: LinkInput, who=Depends(operator), db=db_dependency):
        guard(db)
        resource = get(db, 'resource', resource_id)
        if resource['state'] != 'active':
            raise HTTPException(409, 'Resource is deactivated')
        get(db, body.target_kind, body.target_id)
        if db.execute("SELECT 1 FROM records WHERE kind='resource_link' AND json_extract(body,'$.resource_id')=? "
                      "AND json_extract(body,'$.target_kind')=? AND json_extract(body,'$.target_id')=? "
                      "AND json_extract(body,'$.state')='active'", (resource_id, body.target_kind, body.target_id)).fetchone():
            raise HTTPException(409, 'Active link to this target already exists')
        value = dict(id=identity(), resource_id=resource_id, target_kind=body.target_kind,
                     target_id=body.target_id, state='active', created_by=who, created_at=now(), unlinked_at=None)
        put(db, 'resource_link', value)
        audit(db, who, 'resource.linked', value['id'],
              {'resource_id': resource_id, 'target_kind': body.target_kind, 'target_id': body.target_id})
        return value

    @app.get('/api/resources/{resource_id}/links', response_model=list[ResourceLink], tags=['resources'],
             openapi_extra=contract('both', 'None; reference list including unlinked history'))
    def resource_links(resource_id: str, who=Depends(actor), db=db_dependency):
        get(db, 'resource', resource_id)
        rows = db.execute("SELECT body FROM records WHERE kind='resource_link' AND json_extract(body,'$.resource_id')=? ORDER BY seq",
                          (resource_id,)).fetchall()
        return [json.loads(row[0]) for row in rows]

    @app.post('/api/resources/{resource_id}/unlink', response_model=ResourceLink, tags=['resources'],
              openapi_extra=contract('operator', 'Mark link unlinked + audit; reference removed, content and history retained; stop blocks'))
    def unlink_resource(resource_id: str, body: UnlinkInput, who=Depends(operator), db=db_dependency):
        guard(db)
        get(db, 'resource', resource_id)
        value = get(db, 'resource_link', body.link_id)
        if value['resource_id'] != resource_id:
            raise HTTPException(404, 'Link belongs to another resource')
        if value['state'] != 'active':
            raise HTTPException(409, 'Link is already unlinked')
        value.update(state='unlinked', unlinked_at=now())
        update(db, value)
        audit(db, who, 'resource.unlinked', value['id'],
              {'resource_id': resource_id, 'target_kind': value['target_kind'], 'target_id': value['target_id']})
        return value

    @app.get('/api/resources/{resource_id}/compare/{other_id}', response_model=CompareResult, tags=['resources'],
             openapi_extra=contract('both', 'None; hash-verified byte comparison of two uploaded resources, no interpretation'))
    def compare_resources(resource_id: str, other_id: str, who=Depends(actor), db=db_dependency):
        left = get(db, 'resource', resource_id)
        right = get(db, 'resource', other_id)
        left_data = storage.checked(left)
        right_data = storage.checked(right)
        if left_data == right_data:
            return CompareResult(left_id=left['id'], right_id=right['id'], relation='IDENTICAL',
                                 left_sha256=left['sha256'], right_sha256=right['sha256'],
                                 left_size_bytes=left['size_bytes'], right_size_bytes=right['size_bytes'],
                                 common_prefix_bytes=len(left_data), common_suffix_bytes=len(left_data))
        prefix = 0
        for a, b in zip(left_data, right_data):
            if a != b:
                break
            prefix += 1
        suffix = 0
        while suffix < min(len(left_data), len(right_data)) - prefix:
            if left_data[len(left_data) - 1 - suffix] != right_data[len(right_data) - 1 - suffix]:
                break
            suffix += 1
        return CompareResult(left_id=left['id'], right_id=right['id'], relation='DIFFERENT',
                             left_sha256=left['sha256'], right_sha256=right['sha256'],
                             left_size_bytes=left['size_bytes'], right_size_bytes=right['size_bytes'],
                             common_prefix_bytes=prefix, common_suffix_bytes=suffix)

    @app.post('/api/resources/{resource_id}/deactivate', response_model=Resource, tags=['resources'],
              openapi_extra=contract('reviewer', 'Confirmed family-wide deactivation + audit; retains all versions and content (never deletes); blocks new versions/links'))
    def deactivate_resource(resource_id: str, body: ResourceDeactivateInput, who=Depends(reviewer), db=db_dependency):
        guard(db)
        value = get(db, 'resource', resource_id)
        if value['state'] != 'active':
            raise HTTPException(409, 'Resource family is already deactivated')
        for record in family_records(db, value['family_id']):
            if record['state'] == 'active':
                record.update(state='deactivated', deactivated_at=now())
                update(db, record)
        value.update(state='deactivated', deactivated_at=now())
        audit(db, who, 'resource.deactivated', value['id'],
              {'family_id': value['family_id'], 'versions': len(family_records(db, value['family_id'])),
               'reason': body.reason})
        return get(db, 'resource', resource_id)
