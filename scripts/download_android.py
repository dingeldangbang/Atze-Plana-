"""Retrieve the bounded CI APK mirror when the Actions blob host is unreachable.

Uses existing gh authentication, never a token argument. Verifies exact successful
workflow revision, complete chunks and the independent build-step SHA256 evidence.
This is byte-integrity verification, NOT a local apksigner/install test. Those
checks are required from the selected CI run. No GitHub release is created.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
import subprocess

REPOSITORY = 'dingeldangbang/Atze-Plana-'


def api(path):
    return json.loads(subprocess.check_output(['gh', 'api', f'repos/{REPOSITORY}/{path}'], text=True))


def assemble(run, annotations, revision, built_parents=()):
    if (run.get('head_sha') not in {revision, *built_parents} or run.get('conclusion') != 'success'
            or run.get('status') != 'completed' or run.get('path') != '.github/workflows/android.yml'):
        raise ValueError('Expected successful Android workflow at exact revision')
    evidence = [json.loads(a['message']) for a in annotations if a.get('title') == 'ANDROID_ARTIFACT_EVIDENCE']
    chunks = [json.loads(a['message']) for a in annotations if a.get('title') == 'ANDROID_APK_BYTES']
    if len(evidence) != 1 or not chunks or len(chunks) > 10:
        raise ValueError('Missing or ambiguous CI APK evidence')
    evidence = evidence[0]
    if (evidence.get('source_revision') != revision
            or evidence.get('build-status.txt', '').strip() != 'BUILD_PASS; INSTALL_NOT_RUN'
            or evidence.get('validation-status.txt', '').strip() != 'EMULATOR_INSTALL_START_TEST_PASS'
            or 'atze_result=PASS' not in evidence.get('instrumentation.txt', '')
            or 'Verified using v2 scheme (APK Signature Scheme v2): true' not in evidence.get('app-signature.txt', '')):
        raise ValueError('Build, v2 signature or emulator evidence missing')
    artifacts = [a for a in evidence['apks'] if a['file'] == 'atze-app-debug.apk']
    if len(artifacts) != 1:
        raise ValueError('Missing unambiguous app digest')
    artifact = artifacts[0]
    if not 0 < artifact['bytes'] <= 27000:
        raise ValueError('APK exceeds mirror bound')
    chunks.sort(key=lambda c: c['index'])
    for index, chunk in enumerate(chunks):
        if (chunk['index'] != index or chunk['count'] != len(chunks)
                or chunk['source_revision'] != revision or chunk['file'] != artifact['file']
                or chunk['bytes'] != artifact['bytes'] or chunk['sha256'] != artifact['sha256']
                or len(chunk['base64']) > 3600):
            raise ValueError('Mixed, duplicated, missing or oversized APK chunks')
    data = base64.b64decode(''.join(c['base64'] for c in chunks), validate=True)
    if len(data) != artifact['bytes'] or hashlib.sha256(data).hexdigest() != artifact['sha256']:
        raise ValueError('APK integrity mismatch')
    return data, evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', required=True, type=int)
    parser.add_argument('--revision', required=True, help='Full 40-character source commit from the selected workflow')
    parser.add_argument('--output-dir', type=Path, default=Path('reports/android-download'))
    args = parser.parse_args()
    if args.run_id <= 0 or not re.fullmatch('[a-f0-9]{40}', args.revision):
        parser.error('Positive run ID and full lowercase revision required')
    run = api(f'actions/runs/{args.run_id}')
    jobs = api(f'actions/runs/{args.run_id}/jobs?per_page=100')['jobs']
    if len(jobs) != 1 or jobs[0]['conclusion'] != 'success':
        raise ValueError('Expected single successful Android job')
    check_id = int(jobs[0]['check_run_url'].rsplit('/', 1)[1])
    annotations = api(f'check-runs/{check_id}/annotations?per_page=100')
    # PR workflows build GitHub's synthetic merge revision, not necessarily head_sha.
    # Verify parentage independently through the commit API, never from APK annotations.
    commit = api(f'commits/{args.revision}')
    if commit['sha'] != args.revision:
        raise ValueError('Unexpected built commit')
    data, evidence = assemble(run, annotations, args.revision, [p['sha'] for p in commit['parents']])
    args.output_dir.mkdir(parents=True, exist_ok=True)
    destination = args.output_dir / 'atze-app-debug.apk'
    # No APK is written at all unless all evidence/integrity gates passed.
    temporary = destination.with_suffix('.apk.tmp')
    temporary.write_bytes(data)
    temporary.replace(destination)
    (args.output_dir / 'SHA256SUMS').write_text(hashlib.sha256(data).hexdigest() + '  atze-app-debug.apk\n')
    (args.output_dir / 'artifact-evidence.json').write_text(json.dumps(evidence, indent=2) + '\n')
    (args.output_dir / 'app-signature.txt').write_text(evidence['app-signature.txt'])
    (args.output_dir / 'source-sha256.txt').write_text(evidence['source-sha256.txt'])
    print(f'CI APK bytes verified: {destination} ({len(data)} bytes). Signature/install checked in CI, not locally.')


if __name__ == '__main__':
    main()
