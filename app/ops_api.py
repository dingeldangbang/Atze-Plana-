"""Operations API: reviewer-triggered verified backups and sandboxed resource re-verification; fail-closed, no deletion."""
import hashlib
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Literal

from fastapi import Depends, HTTPException

from app.models import Input, Text
from app.store import get, listing, put, audit, identity, now
from app.sandbox import run_isolated


class BackupInput(Input):
    confirm: Literal[True]
    reason: Text
    note: str = ''


def _database_backup(source: Path, destination: Path) -> str:
    """Same semantics as scripts/backup.py: exclusive 0o600 creation, SQLite backup API, integrity check, cleanup on failure."""
    fd = os.open(destination, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(fd)
    try:
        src = sqlite3.connect(source.resolve().as_uri() + '?mode=ro', uri=True)
        try:
            dst = sqlite3.connect(destination)
            try:
                src.backup(dst)
                result = dst.execute('PRAGMA integrity_check').fetchall()
                if result != [('ok',)]:
                    raise RuntimeError(f'Backup integrity check failed: {result}')
            finally:
                dst.close()
        finally:
            src.close()
    except BaseException:
        destination.unlink(missing_ok=True)
        raise
    return 'ok'


SANDBOX_JOB = Path(__file__).resolve().parents[1] / 'scripts' / 'sandbox_jobs' / 'verify_resource.py'
SANDBOX_MEMORY_MB = 256
SANDBOX_TIMEOUT_SECONDS = 20


class VerifyInput(Input):
    confirm: Literal[True]
    reason: Text


def register_ops_api(app, settings, actor, reviewer, connection, store, storage):
    DB = Depends(connection, scope='function')

    @app.post('/api/operations/backups', status_code=201, tags=['operations'],
              openapi_extra={'x-role': 'reviewer', 'x-side-effects': 'Create a verified SQLite snapshot (exclusive 0o600 file, SQLite backup API, integrity_check) plus a durable backup record and audit; DATABASE-ONLY scope, object roots are documented separately; allowed under emergency stop (read-only snapshot); no deletion endpoint, no automation'})
    def create_backup(body: BackupInput, who=Depends(reviewer), db=DB) -> dict:
        target_dir = settings.db_path.parent / 'backups'
        target_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        destination = target_dir / f'atze-backup-{identity()}.db'
        try:
            integrity = _database_backup(settings.db_path, destination)
            digest = hashlib.sha256(destination.read_bytes()).hexdigest()
            size = destination.stat().st_size
            verify = sqlite3.connect(destination.as_uri() + '?mode=ro', uri=True)
            try:
                counts = dict(verify.execute('SELECT kind, COUNT(*) FROM records GROUP BY kind').fetchall())
                total = verify.execute('SELECT COUNT(*) FROM records').fetchone()[0]
            finally:
                verify.close()
        except Exception as error:  # fail-closed: no partial backup record is ever persisted
            raise HTTPException(503, f'Verified backup could not be created ({type(error).__name__}); no record persisted')
        value = dict(id=identity(), scope='DATABASE_ONLY', path=str(destination.relative_to(settings.db_path.parent)),
                     sha256=digest, size_bytes=size, integrity=integrity, record_counts=counts, total_records=total,
                     note=body.note, reason=body.reason, created_at=now(), created_by=who)
        put(db, 'backup', value)
        audit(db, who, 'operations.backup_created', value['id'],
              {'path': value['path'], 'sha256': digest, 'size_bytes': size, 'integrity': integrity,
               'total_records': total, 'reason': body.reason})
        return value

    @app.get('/api/operations/backups', tags=['operations'],
             openapi_extra={'x-role': 'both', 'x-side-effects': 'None; read-only list of verified backup records; a record proves only the snapshot at creation time, not an offsite copy or a restore drill'})
    def backups(limit: int = 100, offset: int = 0, who=Depends(actor), db=DB) -> list[dict]:
        return listing(db, 'backup', limit, offset)

    @app.post('/api/operations/verify/resource/{resource_id}', status_code=201, tags=['operations'],
              openapi_extra={'x-role': 'reviewer', 'x-side-effects': 'Re-verify one stored resource object in an isolated subprocess (separate process, rlimits address space/CPU/file size, hard timeout, minimal env, read-only inputs); durable verification record + audit; process isolation only, NOT a network/filesystem namespace or seccomp sandbox; stop blocks execution; MATCH proves byte equality with the stored hash only, never content safety or truth'})
    def verify_resource(resource_id: str, body: VerifyInput, who=Depends(reviewer), db=DB) -> dict:
        from app.storage import guard
        guard(db)  # execution semantics: the emergency stop blocks subprocess execution
        record = get(db, 'resource', resource_id)
        root = storage.roots.get(record.get('tier'))
        if root is None:
            raise HTTPException(503, 'Requested storage tier is not configured for verification')
        sandbox = run_isolated([sys.executable, SANDBOX_JOB, '--db', settings.db_path,
                                '--storage-root', root, '--resource', resource_id],
                               timeout_seconds=SANDBOX_TIMEOUT_SECONDS, memory_mb=SANDBOX_MEMORY_MB)
        outcome = f"EXIT_{sandbox['exit_code']}" if sandbox['exit_code'] not in (0, None) else 'TIMEOUT'
        job = {}
        if sandbox['exit_code'] == 0:
            try:
                job = json.loads(sandbox['stdout_tail'].strip().splitlines()[-1])
                outcome = job.get('outcome', 'NO_RESULT')
            except (ValueError, IndexError):
                outcome = 'NO_RESULT'
        value = dict(id=identity(), resource_id=resource_id, family_id=record.get('family_id'),
                     kind=record.get('kind'), outcome=outcome, job_result=job, sandbox={
                         'isolation': 'subprocess + rlimits + hard timeout + minimal env; NOT a network/filesystem namespace or seccomp sandbox',
                         'memory_mb': SANDBOX_MEMORY_MB, 'timeout_seconds': SANDBOX_TIMEOUT_SECONDS,
                         'exit_code': sandbox['exit_code'], 'timed_out': sandbox['timed_out'],
                         'duration_seconds': sandbox['duration_seconds']},
                     reason=body.reason, created_at=now(), created_by=who)
        put(db, 'verification', value)
        audit(db, who, 'operations.resource_verified', value['id'],
              {'resource_id': resource_id, 'outcome': outcome, 'duration_seconds': sandbox['duration_seconds'],
               'reason': body.reason})
        return value
