"""Bounded local text storage; safe copy/verify/index switch with retained originals.

Filesystem and SQLite cannot commit atomically. Failed writes may leave orphan blobs;
no automatic orphan/source deletion is attempted. Cache cleanup uses tombstones.
"""
from datetime import datetime, timedelta, timezone
import hashlib
import os
import stat
from uuid import UUID
from fastapi import HTTPException
from app.store import get, put, audit, identity, now, stopped
from app.context import index_text, references, update

MAX_BYTES = 262144  # maximum UTF-8 bytes for 65536 Unicode code points
RESERVE_BYTES = 16 * 1024 * 1024


def guard(db):
    if stopped(db)['active']:
        raise HTTPException(409, 'Emergency stop blocks storage mutation')


class Storage:
    def __init__(self, settings):
        local = settings.storage_root or settings.db_path.parent / 'objects'
        if local.is_symlink():
            raise ValueError('Storage root must not be a symlink')
        local.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.roots = {'local': local.absolute()}
        if settings.sd_root:
            sd = settings.sd_root.absolute()
            # Do not create mount points: an unavailable removable tier stays unavailable.
            if sd.is_symlink() or sd.resolve() == local.resolve() or sd.resolve() in local.resolve().parents or local.resolve() in sd.resolve().parents:
                raise ValueError('Storage roots must be distinct, non-nested, non-symlink paths')
            self.roots['sd'] = sd

    def directory(self, tier):
        root = self.roots.get(tier)
        if root is None:
            raise HTTPException(503, 'Requested storage tier is not configured')
        return os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)

    @staticmethod
    def filename(key):
        if str(UUID(key)) != key:
            raise ValueError('Invalid internal object key')
        return key + '.blob'

    def usage(self, tier):
        directory = self.directory(tier)
        try:
            info = os.fstatvfs(directory)
            total = info.f_blocks * info.f_frsize
            free = info.f_bavail * info.f_frsize
            return {'total_bytes': total, 'free_bytes': free, 'used_bytes': total - free,
                    'used_percent': round((total - free) / total * 100, 2) if total else 100.0}
        finally:
            os.close(directory)

    def choose(self, size, placement='auto'):
        candidates = ['local', 'sd'] if placement == 'auto' else [placement]
        for tier in candidates:
            try:
                usage = self.usage(tier)
                threshold = 85 if tier == 'local' else 90
                if usage['free_bytes'] >= size + RESERVE_BYTES and usage['used_percent'] < threshold:
                    return tier
            except (OSError, HTTPException):
                continue
        raise HTTPException(507, 'No available tier meets capacity/reserve policy')

    def read(self, tier, key):
        directory = self.directory(tier)
        try:
            fd = os.open(self.filename(key), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
            with os.fdopen(fd, 'rb') as file:
                if not stat.S_ISREG(os.fstat(file.fileno()).st_mode):
                    raise HTTPException(503, 'Stored object is not a regular file')
                data = file.read(MAX_BYTES + 1)
                if len(data) > MAX_BYTES:
                    raise HTTPException(503, 'Stored object exceeds supported size')
                return data
        finally:
            os.close(directory)

    def checked(self, value):
        data = self.read(value['tier'], value['key'])
        if len(data) != value['size_bytes'] or hashlib.sha256(data).hexdigest() != value['sha256']:
            raise HTTPException(503, 'Stored object integrity check failed')
        return data

    def write(self, tier, data):
        key = identity()
        directory = self.directory(tier)
        try:
            fd = os.open(self.filename(key), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory)
            with os.fdopen(fd, 'wb') as file:
                file.write(data)
                file.flush()
                os.fsync(file.fileno())
            os.fsync(directory)
        finally:
            os.close(directory)
        if self.read(tier, key) != data:
            raise HTTPException(503, 'Destination verification failed')
        return key

    def archive(self, db, body, who):
        guard(db)
        references(db, body.project_id, body.evidence_ids)
        logical = f'/project/{body.project_id}/{body.relative_path}'
        if db.execute("SELECT 1 FROM records WHERE kind='archive' AND json_extract(body, '$.logical_path')=?", (logical,)).fetchone():
            raise HTTPException(409, 'Archive logical path is immutable and already exists')
        data = body.content.encode()
        tier = self.choose(len(data), body.placement)
        key = self.write(tier, data)
        value = dict(id=identity(), project_id=body.project_id, logical_path=logical, sha256=hashlib.sha256(data).hexdigest(),
                     size_bytes=len(data), created_at=now(), evidence_ids=body.evidence_ids, tier=tier, key=key, retained_copies=[], version=1)
        put(db, 'archive', value)
        index_text(db, body.project_id, value['id'], body.content)
        audit(db, who, 'archive.created', value['id'], {'sha256': value['sha256'], 'tier': tier})
        return value

    def move(self, db, object_id, body, who):
        guard(db)
        value = get(db, 'archive', object_id)
        if value['tier'] == body.target:
            raise HTTPException(409, 'Object is already on the requested tier')
        data = self.checked(value)
        target = self.choose(len(data), body.target)
        key = self.write(target, data)
        source = {'tier': value['tier'], 'key': value['key']}
        value['retained_copies'].append(source)
        value.update(tier=target, key=key)
        update(db, value)
        audit(db, who, 'archive.relocated', object_id, {'source': source, 'target': target, 'sha256': value['sha256'], 'reason': body.reason, 'source_retained': True})
        return value

    def cache(self, db, body, who):
        guard(db)
        task = get(db, 'task', body.task_id)
        data = body.content.encode()
        tier = self.choose(len(data))
        key = self.write(tier, data)
        value = dict(id=identity(), task_id=body.task_id, project_id=task['project_id'], tier=tier, key=key,
                     size_bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), created_at=now(),
                     expires_at=(datetime.now(timezone.utc) + timedelta(seconds=body.ttl_seconds)).isoformat(),
                     state='active', deleted=False)
        put(db, 'cache', value)
        audit(db, who, 'cache.created', value['id'], {'task_id': body.task_id, 'expires_at': value['expires_at']})
        return value

    def cleanup(self, store, body, who):
        # First commit tombstones; never delete a live object before persistent expiry.
        import json
        with store.connect() as db:
            guard(db)
            rows = db.execute("SELECT body FROM records WHERE kind='cache' AND json_extract(body,'$.deleted')=0 AND json_extract(body,'$.expires_at')<=? ORDER BY seq LIMIT ?", (now(), body.limit)).fetchall()
            values = [json.loads(row[0]) for row in rows]
            for value in values:
                value['state'] = 'expired'
                update(db, value)
                audit(db, who, 'cache.expired', value['id'], {'reason': body.reason})
        deleted = []
        for value in values:
            with store.connect() as db:
                guard(db)
                directory = self.directory(value['tier'])
                try:
                    try:
                        os.unlink(self.filename(value['key']), dir_fd=directory)
                    except FileNotFoundError:
                        pass  # retry after crash or externally lost disposable cache
                    os.fsync(directory)
                finally:
                    os.close(directory)
                value['deleted'] = True
                update(db, value)
                audit(db, who, 'cache.deleted', value['id'], {'reason': body.reason})
                deleted.append(value['id'])
        return {'deleted_ids': deleted}

    def health(self, db):
        tiers = []
        for tier in ['ram', 'local', 'sd', 'server', 'cloud']:
            try:
                tiers.append(dict(tier=tier, available=True, **self.usage(tier)))
            except (OSError, HTTPException):
                tiers.append(dict(tier=tier, available=False, reason='Not configured or unavailable; no measurement'))
        def size(kind, suffix='', params=()):
            return db.execute("SELECT COALESCE(SUM(json_extract(body,'$.size_bytes')),0) FROM records WHERE kind=? " + suffix, (kind, *params)).fetchone()[0]
        return dict(tiers=tiers, cache_active_bytes=size('cache', "AND json_extract(body,'$.deleted')=0 AND json_extract(body,'$.expires_at')>?", (now(),)),
                    cache_expired_bytes=size('cache', "AND json_extract(body,'$.deleted')=0 AND json_extract(body,'$.expires_at')<=?", (now(),)),
                    archive_logical_bytes=size('archive'), source_retention=True)
