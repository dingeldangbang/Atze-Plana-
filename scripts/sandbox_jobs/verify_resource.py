"""Self-contained sandboxed verification job: re-read a stored resource object and recompute its SHA-256.

Runs in an isolated subprocess (rlimits/timeout; see app/sandbox.py). Reads the database and the object
file READ-ONLY, imports no app code, prints exactly one JSON object, and never writes anywhere.
"""
import argparse
import hashlib
import json
import os
import sqlite3
import stat
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', required=True, help='SQLite database file (opened read-only)')
    parser.add_argument('--storage-root', required=True, help='Local object root (read-only)')
    parser.add_argument('--resource', required=True, help='Resource record id')
    arguments = parser.parse_args()

    database = sqlite3.connect(f'file:{Path(arguments.db).resolve()}?mode=ro', uri=True)
    try:
        row = database.execute("SELECT body FROM records WHERE kind='resource' AND id=?",
                               (arguments.resource,)).fetchone()
    finally:
        database.close()
    if row is None:
        print(json.dumps({'resource_id': arguments.resource, 'outcome': 'NOT_FOUND'}))
        return 0
    record = json.loads(row[0])
    key = record.get('key')
    tier = record.get('tier')
    try:
        path = Path(arguments.storage_root) / (key + '.blob')
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        try:
            if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                raise OSError('object is not a regular file')
            data = b''
            while True:
                chunk = os.read(descriptor, 1 << 20)
                if not chunk:
                    break
                data += chunk
                if len(data) > (8 << 20):
                    raise OSError('object exceeds the verification size bound')
        finally:
            os.close(descriptor)
    except OSError as error:
        print(json.dumps({'resource_id': record['id'], 'tier': tier, 'outcome': f'UNAVAILABLE:{type(error).__name__}'}))
        return 0
    recomputed = hashlib.sha256(data).hexdigest()
    outcome = 'MATCH' if recomputed == record.get('sha256') and len(data) == record.get('size_bytes') else 'MISMATCH'
    print(json.dumps({'resource_id': record['id'], 'tier': tier, 'stored_sha256': record.get('sha256'),
                      'recomputed_sha256': recomputed, 'size_bytes': len(data), 'outcome': outcome}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
