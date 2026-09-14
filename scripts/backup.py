"""Database-only SQLite backup. Archive/cache blob roots are NOT included."""
import argparse
from pathlib import Path
import sqlite3


def backup(source: Path, destination: Path):
    source = source.resolve(strict=True)
    # Exclusive creation avoids accidental overwrite; umask-independent owner-only permissions.
    import os
    fd = os.open(destination, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(fd)
    try:
        src = sqlite3.connect(source.as_uri() + '?mode=ro', uri=True)
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    print('Database-only backup integrity (archive/cache roots NOT included):', backup(args.source, args.destination))
