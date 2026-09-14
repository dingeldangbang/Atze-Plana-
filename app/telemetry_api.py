"""Telemetry ingestion: submitted measurements stored as immutable, hash-verified timestamped batches."""
import hashlib
import json
import secrets
from datetime import datetime
from typing import Annotated
from fastapi import Depends, HTTPException, Query
from app.context import update
from app.store import get, put, listing, audit, identity, now
from app.storage import guard
from app.telemetry_models import (Batch, BatchSamples, DeactivateInput, Device, DeviceInput, IngestInput,
                                  Sample, Sensor, SensorInput)


def parse_timestamp(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def register_telemetry_api(app, settings, bearer, actor, operator, reviewer, connection, store, storage):
    db_dependency = Depends(connection, scope='function')

    def contract(role, effects):
        return {'x-role': role, 'x-side-effects': effects}

    def device_role(credentials=Depends(bearer)):
        token = credentials.credentials if credentials else ''
        if not token:
            raise HTTPException(401, 'Telemetry device bearer token required', headers={'WWW-Authenticate': 'Bearer'})
        if not settings.telemetry_token:
            raise HTTPException(403, 'Telemetry ingestion is not configured; set ATZE_TELEMETRY_TOKEN')
        if not secrets.compare_digest(token.encode(), settings.telemetry_token.encode()):
            raise HTTPException(401, 'Unknown telemetry device token', headers={'WWW-Authenticate': 'Bearer'})
        return 'telemetry-device'

    @app.post('/api/telemetry/devices', response_model=Device, status_code=201, tags=['telemetry'],
              openapi_extra=contract('operator', 'Register declared device identity + audit; no hardware discovery or capability invention; stop blocks'))
    def device_create(body: DeviceInput, who=Depends(operator), db=db_dependency):
        guard(db)
        if db.execute("SELECT 1 FROM records WHERE kind='telemetry_device' AND json_extract(body,'$.name')=?", (body.name,)).fetchone():
            raise HTTPException(409, 'Device name already registered in this workspace')
        value = dict(id=identity(), **body.model_dump(), state='active', created_at=now(), deactivated_at=None)
        put(db, 'telemetry_device', value)
        audit(db, who, 'telemetry.device_registered', value['id'], {'name': body.name})
        return value

    @app.get('/api/telemetry/devices', response_model=list[Device], tags=['telemetry'],
             openapi_extra=contract('both', 'None; declared registry only, no reachability or liveness claims'))
    def devices(limit: Annotated[int, Query(ge=1, le=500)] = 50,
                offset: Annotated[int, Query(ge=0)] = 0, who=Depends(actor), db=db_dependency):
        return listing(db, 'telemetry_device', limit, offset)

    @app.post('/api/telemetry/devices/{device_id}/sensors', response_model=Sensor, status_code=201, tags=['telemetry'],
              openapi_extra=contract('operator', 'Declare sensor identity + audit; declared_range is an owner assertion, not a calibration; stop blocks'))
    def sensor_create(device_id: str, body: SensorInput, who=Depends(operator), db=db_dependency):
        guard(db)
        if get(db, 'telemetry_device', device_id)['state'] != 'active':
            raise HTTPException(409, 'Device is deactivated')
        if db.execute("SELECT 1 FROM records WHERE kind='telemetry_sensor' AND json_extract(body,'$.device_id')=? AND json_extract(body,'$.name')=?",
                      (device_id, body.name)).fetchone():
            raise HTTPException(409, 'Sensor name already declared for this device')
        value = dict(id=identity(), device_id=device_id, **body.model_dump(), state='active', created_at=now(), deactivated_at=None)
        put(db, 'telemetry_sensor', value)
        audit(db, who, 'telemetry.sensor_declared', value['id'], {'device_id': device_id, 'name': body.name, 'kind': body.kind})
        return value

    @app.get('/api/telemetry/devices/{device_id}/sensors', response_model=list[Sensor], tags=['telemetry'],
             openapi_extra=contract('both', 'None; declared registry only, no sensor health or accuracy claims'))
    def sensors(device_id: str, limit: Annotated[int, Query(ge=1, le=500)] = 50,
                offset: Annotated[int, Query(ge=0)] = 0, who=Depends(actor), db=db_dependency):
        get(db, 'telemetry_device', device_id)
        rows = db.execute("SELECT body FROM records WHERE kind='telemetry_sensor' AND json_extract(body,'$.device_id')=? ORDER BY seq LIMIT ? OFFSET ?",
                          (device_id, limit, offset)).fetchall()
        return [json.loads(row[0]) for row in rows]

    @app.post('/api/telemetry/ingest', response_model=Batch, status_code=201, tags=['telemetry'],
              openapi_extra=contract('device', 'Append immutable timestamped batch blob (hash/size verified on read) + metadata + audit; flags out-of-declared-range and device-suspect samples; no sensor-health or physical-truth claims; stop blocks'))
    def ingest(body: IngestInput, who=Depends(device_role), db=db_dependency):
        guard(db)
        sensors = {}
        device_id = None
        for sample in body.samples:
            if sample.sensor_id not in sensors:
                sensor = get(db, 'telemetry_sensor', sample.sensor_id)
                if sensor['state'] != 'active':
                    raise HTTPException(409, 'Sensor is deactivated')
                if device_id is None:
                    device_id = sensor['device_id']
                    if get(db, 'telemetry_device', device_id)['state'] != 'active':
                        raise HTTPException(409, 'Device is deactivated')
                elif sensor['device_id'] != device_id:
                    raise HTTPException(422, 'All samples in one batch must belong to one device')
                sensors[sample.sensor_id] = sensor
        flagged = sum(1 for sample in body.samples
                      if (r := sensors[sample.sensor_id].get('declared_range'))
                      and not (r['minimum'] <= sample.value <= r['maximum']))
        suspect = sum(1 for sample in body.samples if sample.quality == 'suspect')
        ordered = sorted(parse_timestamp(sample.timestamp) for sample in body.samples)
        data = json.dumps([sample.model_dump() for sample in body.samples], sort_keys=True, separators=(',', ':')).encode()
        tier = storage.choose(len(data), 'auto')
        key = storage.write(tier, data)
        value = dict(id=identity(), device_id=device_id, session=body.session, conditions=body.conditions,
                     received_at=now(), sample_count=len(body.samples),
                     first_timestamp=ordered[0].isoformat(), last_timestamp=ordered[-1].isoformat(),
                     sensor_ids=sorted(sensors), flagged_out_of_range=flagged, suspect_samples=suspect,
                     sha256=hashlib.sha256(data).hexdigest(), size_bytes=len(data), tier=tier, key=key, version=1)
        put(db, 'telemetry_batch', value)
        audit(db, who, 'telemetry.ingested', value['id'], {'device_id': device_id, 'sample_count': value['sample_count'],
                                                            'flagged_out_of_range': flagged, 'suspect_samples': suspect,
                                                            'sha256': value['sha256'], 'tier': tier})
        return value

    @app.get('/api/telemetry/batches', response_model=list[Batch], tags=['telemetry'],
             openapi_extra=contract('both', 'None; immutable batch metadata only'))
    def batches(device_id: Annotated[str | None, Query(description='Filter batches by device')] = None,
                limit: Annotated[int, Query(ge=1, le=500)] = 50,
                offset: Annotated[int, Query(ge=0)] = 0, who=Depends(actor), db=db_dependency):
        if device_id is None:
            return listing(db, 'telemetry_batch', limit, offset)
        get(db, 'telemetry_device', device_id)
        rows = db.execute("SELECT body FROM records WHERE kind='telemetry_batch' AND json_extract(body,'$.device_id')=? ORDER BY seq LIMIT ? OFFSET ?",
                          (device_id, limit, offset)).fetchall()
        return [json.loads(row[0]) for row in rows]

    @app.get('/api/telemetry/batches/{batch_id}/samples', response_model=BatchSamples, tags=['telemetry'],
             openapi_extra=contract('both', 'None; hash/size verified blob read; corrupt or unavailable returns 503; raw submitted values, not verified physical truth'))
    def batch_samples(batch_id: str, who=Depends(actor), db=db_dependency):
        value = get(db, 'telemetry_batch', batch_id)
        data = storage.checked(value)
        return BatchSamples(batch=value, samples=[Sample.model_validate(sample) for sample in json.loads(data)])

    @app.post('/api/telemetry/devices/{device_id}/deactivate', response_model=Device, tags=['telemetry'],
              openapi_extra=contract('reviewer', 'Confirmed deactivation + audit; retains devices/sensors/batches, never deletes submitted measurement history; blocks further ingest for this device'))
    def device_deactivate(device_id: str, body: DeactivateInput, who=Depends(reviewer), db=db_dependency):
        value = get(db, 'telemetry_device', device_id)
        if value['state'] != 'active':
            raise HTTPException(409, 'Device is already deactivated')
        value.update(state='deactivated', deactivated_at=now())
        update(db, value)
        audit(db, who, 'telemetry.device_deactivated', device_id, {'reason': body.reason})
        return value

    @app.post('/api/telemetry/sensors/{sensor_id}/deactivate', response_model=Sensor, tags=['telemetry'],
              openapi_extra=contract('reviewer', 'Confirmed deactivation + audit; retains sensors and all previously ingested samples; blocks further ingest for this sensor'))
    def sensor_deactivate(sensor_id: str, body: DeactivateInput, who=Depends(reviewer), db=db_dependency):
        value = get(db, 'telemetry_sensor', sensor_id)
        if value['state'] != 'active':
            raise HTTPException(409, 'Sensor is already deactivated')
        value.update(state='deactivated', deactivated_at=now())
        update(db, value)
        audit(db, who, 'telemetry.sensor_deactivated', sensor_id, {'reason': body.reason})
        return value
