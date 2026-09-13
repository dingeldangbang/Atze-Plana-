"""Actual pinned local HF inference; no download, target URL, fixtures in product, or fallback.

Run in a non-root Linux network namespace with loopback only. Caller stages two
hash-pinned public artifacts first; no platform inputs/credentials are inherited.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import tarfile
from tempfile import TemporaryDirectory
import time
import httpx

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / 'validation/local-model.lock.json'


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def verify(path, spec):
    require(path.is_file() and not path.is_symlink(), 'Pinned artifact missing or symlink')
    require(path.stat().st_size == spec['size'], 'Artifact size mismatch')
    with path.open('rb') as stream:
        actual = hashlib.file_digest(stream, 'sha256').hexdigest()
    require(actual == spec['sha256'], 'Artifact SHA256 mismatch')
    return actual


def stop(process):
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def wait_ready(client, process, token=None):
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        require(process.poll() is None, 'Child exited before readiness; no fallback')
        try:
            if client.get('/health', headers={'Authorization': 'Bearer '+token} if token else {}, timeout=1).status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(0.1)
    raise RuntimeError('Child readiness deadline exceeded')


def isolated_network():
    require(os.geteuid() != 0, 'Model/Core test must NOT run as root')
    require({name for _, name in socket.if_nameindex()} == {'lo'}, 'Require isolated Linux namespace with loopback only')
    with socket.socket() as probe:
        probe.settimeout(1)
        try:
            probe.connect(('192.0.2.1', 443))  # documentation-only address; never send content
        except OSError as error:
            import errno
            require(error.errno == errno.ENETUNREACH, 'Must prove no external network route')
        else:
            raise RuntimeError('External network route unexpectedly available')


def run(model_path, runtime_archive, report_path, *, allow_fixtures=False):
    report_path = Path(report_path).resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = dict(status='NOT_RUN', timestamp=datetime.now(timezone.utc).isoformat(),
                  scope='REAL LOCAL MODEL; SYNTHETIC TEST INPUT; NO QUALITY/PRODUCTION/MCP CLAIM', checks=[])
    def save():
        report_path.write_text(json.dumps(report, indent=2)+'\n')
    save()  # replace any old success before validation
    try:
        require(allow_fixtures, 'Explicit --allow-fixtures required')
        spec = json.loads(LOCK.read_text())
        report['manifest_sha256'] = hashlib.sha256(LOCK.read_bytes()).hexdigest()
        model_path, runtime_archive = Path(model_path).absolute(), Path(runtime_archive).absolute()
        report['model_sha256'] = verify(model_path, spec['model'])
        report['runtime_sha256'] = verify(runtime_archive, spec['runtime'])
        isolated_network()
        report.update(status='RUNNING', model=spec['model']['id'], revision=spec['model']['revision'],
                      runtime=spec['runtime']['revision'], network='LOOPBACK_ONLY_NO_EXTERNAL_ROUTE', uid=os.geteuid())
        save()
        with TemporaryDirectory(prefix='atze-real-model-test-') as temp, socket.socket() as listener:
            root = Path(temp)
            with tarfile.open(runtime_archive) as archive:
                archive.extractall(root/'runtime', filter='data')
            binaries = list((root/'runtime').rglob('llama-server'))
            require(len(binaries) == 1, 'Expected exactly one pinned llama-server')
            binary = binaries[0]
            with socket.socket() as free:
                free.bind(('127.0.0.1', 0))
                model_port = free.getsockname()[1]
            listener.bind(('127.0.0.1', 0)); listener.listen()
            model_url = f'http://127.0.0.1:{model_port}'
            core_url = f'http://127.0.0.1:{listener.getsockname()[1]}'
            operator, reviewer, model_token = [secrets.token_urlsafe(48) for _ in range(3)]
            auth_file = root/'model-auth'
            auth_file.write_text(model_token+'\n'); auth_file.chmod(0o600)
            base_env = {'PATH': os.defpath, 'HOME': str(root), 'LANG': 'C.UTF-8',
                        'LD_LIBRARY_PATH': str(Path(sys.executable).resolve().parent.parent/'lib')}
            model_env = {**base_env, 'LD_LIBRARY_PATH': str(binary.parent)}
            config = root/'providers.json'
            config.write_text(json.dumps({'providers':[{'id':'pinned-local','mode':'LOCAL','origin':model_url,
                              'token_env':'ATZE_AI_TOKEN_TEST_MODEL','region':'local-test'}]}))
            core_env = {**base_env, 'ATZE_MODE':'test','ATZE_DB_PATH':str(root/'core.db'),
                        'ATZE_STORAGE_ROOT':str(root/'objects'),'ATZE_OPERATOR_TOKEN':operator,
                        'ATZE_REVIEWER_TOKEN':reviewer,'ATZE_AI_CONFIG':str(config),'ATZE_AI_TOKEN_TEST_MODEL':model_token}
            # No platform/challenge/GitHub/HF secrets are inherited by either child.
            with (root/'model.log').open('w') as log, (root/'core.log').open('w') as core_log:
                model = subprocess.Popen([str(binary), '-m', str(model_path), '--host','127.0.0.1','--port',str(model_port),
                    '--alias','pinned-local-model','--api-key-file',str(auth_file),'--ctx-size','1024','--parallel','1',
                    '--threads','2','--threads-http','2','--n-gpu-layers','0','--seed','42','--no-webui','--no-webui-mcp-proxy'],
                    env=model_env, cwd=root, stdout=log, stderr=log)
                core = None
                try:
                    with httpx.Client(base_url=model_url, trust_env=False, timeout=20) as local:
                        wait_ready(local, model, model_token)
                        require(local.get('/v1/models').status_code in {401,403}, 'Model auth not enforced')
                    report['checks'].append({'id':'LM-LOAD','status':'PASS','model_pid':model.pid,'meaning':'pinned model server ready; auth enforced'})
                    save()
                    core = subprocess.Popen([sys.executable,'-m','uvicorn','app.main:create_app','--factory','--fd',str(listener.fileno()),'--no-access-log'],
                                            env=core_env,cwd=ROOT,pass_fds=(listener.fileno(),),stdout=core_log,stderr=core_log)
                    with httpx.Client(base_url=core_url,trust_env=False,timeout=60) as client:
                        wait_ready(client,core)
                        def call(method,path,body=None,role='operator',expected=200):
                            response=client.request(method,path,json=body,headers={'Authorization':'Bearer '+(operator if role=='operator' else reviewer)})
                            require(response.status_code==expected, f'Unexpected HTTP status at {path}: {response.status_code}')
                            return response.json()
                        require(call('GET','/health')['mode']=='test','Not a disposable test instance')
                        require(call('GET','/api/runtime')['mode']=='test','Authenticated mode not test')
                        project=call('POST','/api/projects',{'name':'Synthetic local model validation'},expected=201)
                        task=call('POST','/api/tasks',{'project_id':project['id'],'title':'Synthetic inference only','action':'read','evidence_ids':[],'preconditions_met':True},expected=201)
                        metadata=call('POST','/api/ai/models',{'provider_id':'pinned-local','model':'pinned-local-model',
                            'revision':spec['model']['revision'],'license':spec['model']['license'],'capabilities':['analysis'],'context_length':1024,
                            'quantization':spec['model']['quantization'],'hardware':'CPU worker, 2 threads; not a 2GB benchmark',
                            'evaluation':'Actual isolated inference pending','security_review':'Pinned archive/weights hashed, non-root loopback-only namespace, no tools'},role='reviewer',expected=201)
                        body={'task_id':task['id'],'model_id':metadata['id'],'purpose':'analysis','classification':'PUBLIC',
                              'prompt':'This is a synthetic integration test. Reply with exactly the single word READY.'}
                        def infer():
                            request=call('POST','/api/ai/requests',body,expected=201)
                            return call('POST',f"/api/ai/requests/{request['id']}/run",{'context_hash':request['context_hash'],'reason':'Explicit isolated model test; no real project data'},role='reviewer')
                        denied=infer()
                        require(denied['attempt']['state']=='BLOCKED' and denied['output'] is None,'Default DENY failed')
                        call('POST','/api/ai/policy',{'providers':['pinned-local'],'models':[metadata['id']],'projects':[project['id']],
                            'tasks':['analysis'],'data_classes':['PUBLIC'],'regions':['local-test'],'max_output_tokens':32},role='reviewer',expected=201)
                        started=time.monotonic(); answer=infer(); elapsed=time.monotonic()-started
                        require(answer['attempt']['state']=='DRAFT_UNCHALLENGED','Real inference did not produce draft')
                        report['actual_output']=answer['output']  # explicitly synthetic prompt/output, never operational input
                        require(isinstance(answer['output'],str) and answer['output'].strip(),'Empty inference output')
                        require(answer['output'].strip().rstrip('.!').upper()=='READY','Model did not meet simple instruction criterion')
                        require(not answer['allowed_for_action'],'Model granted action authority')
                        require(call('GET','/api/results')==[],'Model auto-created authoritative Result')
                        require(call('POST',f"/api/tasks/{task['id']}/triage")['state']=='blocked','Unchallenged model escaped triage')
                        require(call('GET','/api/ai/status')['policy']['external_ai'] is False,'External AI enabled')
                        report['checks'].append({'id':'LM-INFER','status':'PASS','seconds':round(elapsed,3),'attempt_id':answer['attempt']['id'],
                                                'meaning':'real pinned inference through consent/gateway, default deny and no action/adoption bypass'})
                finally:
                    if core is not None: stop(core)
                    stop(model)
                    # Logs may contain credential filenames/input; never publish raw logs.
                    report['children_stopped'] = model.poll() is not None and (core is None or core.poll() is not None)
                    if not any(item['id'] == 'LM-INFER' for item in report['checks']):
                        log.flush(); core_log.flush()
                        diagnostic = '\n'.join((root/name).read_text(errors='replace')[-2000:] for name in ['model.log','core.log'])
                        for secret in (operator, reviewer, model_token):
                            diagnostic = diagnostic.replace(secret, '[REDACTED_TEST_CREDENTIAL]')
                        report['sanitized_test_diagnostic'] = diagnostic
                    report['model_exit_code'] = model.returncode
                    report['core_exit_code'] = core.returncode if core is not None else None
        report['status']='PASS'
    except Exception as error:
        report.update(status='FAIL' if report['status']=='RUNNING' else 'BLOCKED', error_type=type(error).__name__, reason=str(error))
        raise
    finally:
        report['finished_at']=datetime.now(timezone.utc).isoformat();save()
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model',type=Path,required=True)
    parser.add_argument('--runtime-archive',type=Path,required=True)
    parser.add_argument('--report',type=Path,default=Path('reports/local-model.json'))
    parser.add_argument('--allow-fixtures',action='store_true')
    args=parser.parse_args()
    try:
        run(args.model,args.runtime_archive,args.report,allow_fixtures=args.allow_fixtures)
    except Exception:
        print('Local model validation BLOCKED/FAIL; inspect structured report, no fallback.',file=sys.stderr)
        raise SystemExit(1)
    print('PASS real pinned local inference; synthetic inputs only; not full agent/MCP/security acceptance.')
