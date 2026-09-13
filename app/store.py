"""Single-host SQLite storage. Domain writes and audit share one transaction."""
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from uuid import uuid4
from fastapi import HTTPException


def now():
    return datetime.now(timezone.utc).isoformat()


def identity():
    return str(uuid4())


class Store:
    def __init__(self, path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(self.path, timeout=5)
        try:
            db.execute('PRAGMA journal_mode=WAL')
        finally:
            db.close()
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS records (seq INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT UNIQUE NOT NULL, kind TEXT NOT NULL, body TEXT NOT NULL)')
            db.execute('CREATE INDEX IF NOT EXISTS records_kind ON records(kind, seq)')
            db.execute('CREATE TABLE IF NOT EXISTS control (id INTEGER PRIMARY KEY CHECK(id=1), active INTEGER NOT NULL, reason TEXT NOT NULL)')
            db.execute("CREATE UNIQUE INDEX IF NOT EXISTS archive_namespace ON records(json_extract(body, '$.logical_path')) WHERE kind='archive'")
            db.execute("CREATE VIRTUAL TABLE IF NOT EXISTS context_fts USING fts5(project_id UNINDEXED, source_id UNINDEXED, start_char UNINDEXED, end_char UNINDEXED, text)")
            db.execute("INSERT OR IGNORE INTO control VALUES(1, 0, 'Initial state')")

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        try:
            db.execute('BEGIN IMMEDIATE')
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()


def get(db, kind, key):
    row = db.execute('SELECT body FROM records WHERE kind=? AND id=?', (kind, key)).fetchone()
    if row is None:
        raise HTTPException(404, f'{kind} not found')
    return json.loads(row[0])


def put(db, kind, value):
    db.execute('INSERT INTO records(id,kind,body) VALUES(?,?,?)', (value['id'], kind, json.dumps(value)))
    return value


def listing(db, kind, limit=100, offset=0):
    return [json.loads(row[0]) for row in db.execute('SELECT body FROM records WHERE kind=? ORDER BY seq LIMIT ? OFFSET ?', (kind, limit, offset))]


def audit(db, actor, event, entity_id, details=None):
    put(db, 'audit', dict(id=identity(), created_at=now(), actor=actor, event=event, entity_id=entity_id, details=details or {}))


def stopped(db):
    active, reason = db.execute('SELECT active,reason FROM control WHERE id=1').fetchone()
    return dict(active=bool(active), reason=reason)
