"""Synthetic isolated security/transport inputs. Receipt server is NOT model inference."""
import hashlib
import json
import ssl
import subprocess
import threading
from dataclasses import replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.ai_gateway import ExternalDataGateway, GateDenied, scan
from app.ai_models import ProviderConfig
from conftest import seed, task


@pytest.fixture
def receiver():
    """Real loopback HTTP contract receiver, not a fake model or production adapter."""
    seen = []
    output = {'status': 200, 'tools': False, 'raw': None}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass
        def do_POST(self):
            body = self.rfile.read(int(self.headers['Content-Length']))
            seen.append((self.path, json.loads(body)))
            self.send_response(output['status'])
            self.send_header('Location', 'http://127.0.0.1:9/never-follow')
            self.end_headers()
            message = {'content': 'transport receipt ' + hashlib.sha256(body).hexdigest()}
            if output['tools']:
                message['tool_calls'] = [{'function': {'name': 'terminal'}}]
            self.wfile.write(output['raw'] if output['raw'] is not None else json.dumps({'choices': [{'message': message}]}).encode())
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server, seen, output
    server.shutdown()
    server.server_close()
    thread.join()


@pytest.fixture
def ai(tmp_path, settings, receiver, monkeypatch):
    server, seen, output = receiver
    monkeypatch.setenv('ATZE_AI_TOKEN_TRANSPORT_TEST', 'isolated-transport-credential-' * 2)
    config = tmp_path / 'providers.json'
    config.write_text(json.dumps({'providers': [{'id': 'contract', 'mode': 'LOCAL', 'origin': f'http://127.0.0.1:{server.server_port}', 'token_env': 'ATZE_AI_TOKEN_TRANSPORT_TEST', 'region': 'local-test'}]}))
    with TestClient(create_app(replace(settings, ai_config_path=config))) as client:
        client.headers['Authorization'] = 'Bearer ' + settings.operator_token
        reviewer = {'Authorization': 'Bearer ' + settings.reviewer_token}
        project, evidence = seed(client, reviewer)
        tid = task(client, project, evidence)
        model = client.post('/api/ai/models', headers=reviewer, json={
            'provider_id': 'contract', 'model': 'synthetic-transport-contract-not-model', 'revision': 'a'*40,
            'license': 'synthetic test metadata', 'capabilities': ['analysis'], 'context_length': 4096,
            'hardware': 'No model tested', 'evaluation': 'Transport contract only', 'security_review': 'Isolated test receiver'}).json()
        body = {'task_id': tid, 'model_id': model['id'], 'purpose': 'analysis', 'classification': 'PUBLIC', 'prompt': 'Explicit synthetic transport test, not project evidence'}
        pol = {'providers': ['contract'], 'models': [model['id']], 'projects': [project['id']], 'tasks': ['analysis'], 'data_classes': ['PUBLIC', 'CONFIDENTIAL'], 'regions': ['local-test']}
        yield client, reviewer, body, pol, seen, output, settings, config


def request_and_run(ai, *, consent=None):
    client, reviewer, body, pol, *_ = ai
    request = client.post('/api/ai/requests', json=body)
    assert request.status_code == 201, request.text
    request = request.json()
    return client.post('/api/ai/requests/'+request['id']+'/run', headers=reviewer,
                       json=consent or {'context_hash': request['context_hash'], 'reason': 'Explicit isolated transport test'}).json(), request


def test_ai_default_and_roles(ai):
    """AI-001 | Defaults/roles | isolated DB | prepare/run without policy | BLOCK, zero sockets | response/count asserted."""
    c, r, body, pol, seen, *_ = ai
    assert c.get('/api/ai/status').json()['policy']['privacy_lock'] is True
    assert c.post('/api/ai/policy', json=pol).status_code == 403
    result, request = request_and_run(ai)
    assert result['attempt']['reason'] == 'POLICY_ALLOWLIST_DENIED'
    assert not seen and result['output'] is None
    assert c.post('/api/ai/requests/'+request['id']+'/run', json={'context_hash': request['context_hash'], 'reason': 'Operator cannot send'}).status_code == 403


def test_ai_actual_transport_and_no_adoption(ai):
    """AI-002 | Real HTTP transport | explicit policy/consent | send once | untrusted receipt, no result/memory, replay blocked | asserted."""
    c, r, body, pol, seen, *_ = ai
    assert c.post('/api/ai/policy', headers=r, json=pol).status_code == 201
    result, request = request_and_run(ai)
    assert result['attempt']['state'] == 'DRAFT_UNCHALLENGED'
    assert result['output'].startswith('transport receipt ') and result['allowed_for_action'] is False
    assert len(seen) == 1 and seen[0][0] == '/v1/chat/completions'
    assert c.get('/api/results').json() == []
    again = c.post('/api/ai/requests/'+request['id']+'/run', headers=r, json={'context_hash': request['context_hash'], 'reason': 'Replay is forbidden'}).json()
    assert again['attempt']['reason'] == 'REQUEST_NOT_PENDING' and len(seen) == 1
    audit = c.get('/api/audit', headers=r).text
    assert body['prompt'] not in audit and result['output'] not in audit


@pytest.mark.parametrize('text', ['password: test-secret-value', '{"password":"test-secret-value"}', 'Bearer synthetic-secret', '-----BEGIN PRIVATE KEY-----', 'hf_syntheticcredentialvalue'])
def test_ai_secret_rejection(ai, text):
    """AI-003 | Recognized secrets | isolated request | submit patterns | 409 before persistence/egress | response/socket count asserted."""
    c, r, body, pol, seen, *_ = ai
    body['prompt'] = text
    assert c.post('/api/ai/requests', json=body).status_code == 409
    assert not seen


def test_ai_context_isolation(ai):
    """AI-004 | Context boundary | second project evidence | select foreign ID | BLOCK; own selection confidential | asserted."""
    c, r, body, pol, seen, *_ = ai
    project, evidence = seed(c, r)
    body['evidence_ids'] = [evidence['id']]
    assert c.post('/api/ai/requests', json=body).json()['detail'] == 'CROSS_PROJECT_CONTEXT'
    body['task_id'] = task(c, project, evidence)
    value = c.post('/api/ai/requests', json=body).json()
    assert value['effective_classification'] == 'CONFIDENTIAL'
    assert evidence['id'] in value['context'] and not seen
    body['classification'] = 'SECRET'
    assert c.post('/api/ai/requests', json=body).status_code == 409


def test_ai_stale_policy_hash_and_stop(ai):
    """AI-005 | Consent freshness | prepared request | change policy/hash/stop | BLOCK, no egress | asserted."""
    c, r, body, pol, seen, *_ = ai
    c.post('/api/ai/policy', headers=r, json=pol)
    req = c.post('/api/ai/requests', json=body).json()
    c.post('/api/ai/policy', headers=r, json=pol)
    result = c.post('/api/ai/requests/'+req['id']+'/run', headers=r, json={'context_hash': req['context_hash'], 'reason': 'stale consent check'}).json()
    assert result['attempt']['reason'] == 'STALE_POLICY_OR_CONFIG'
    result, _ = request_and_run(ai, consent={'context_hash': '0'*64, 'reason': 'hash mismatch check'})
    assert result['attempt']['reason'] == 'CONTEXT_HASH_MISMATCH'
    c.post('/api/control/stop', headers=r, json={'active': True, 'reason': 'stop model transport'})
    result, _ = request_and_run(ai)
    assert result['attempt']['reason'] == 'EMERGENCY_STOP' and not seen


@pytest.mark.parametrize('failure', ['redirect', 'tools', 'invalid', 'oversize'])
def test_ai_transport_failures_no_fallback(ai, failure):
    """AI-006 | Real receiver failure responses | allowed request | redirect/tools/bad JSON/oversize | no fallback/adoption | asserted."""
    c, r, body, pol, seen, output, *_ = ai
    c.post('/api/ai/policy', headers=r, json=pol)
    if failure == 'redirect': output['status'] = 302
    if failure == 'tools': output['tools'] = True
    if failure == 'invalid': output['raw'] = b'not JSON'
    if failure == 'oversize': output['raw'] = b'X'*65537
    result, _ = request_and_run(ai)
    assert result['attempt']['state'] in {'BLOCKED', 'UNAVAILABLE'}
    assert result['output'] is None and len(seen) == 1


@pytest.mark.parametrize('mode,url', [('LOCAL', 'http://localhost:80'), ('SELF_HOSTED','http://127.0.0.1'), ('PRIVATE_ENDPOINT','http://host'), ('EXTERNAL_PROVIDER','http://host'), ('LOCAL','https://user:pw@127.0.0.1'), ('LOCAL','http://127.0.0.1/path'), ('LOCAL','http://127.0.0.1:0'), ('SELF_HOSTED','https://host:0')])
def test_ai_reject_unsafe_origin(tmp_path, mode, url):
    """AI-007 | Origin constraints | bad startup config | construct gateway | reject before socket | ValueError asserted."""
    path = tmp_path/'bad.json'
    path.write_text(json.dumps({'providers':[{'id':'bad','mode':mode,'origin':url,'region':'unknown','token_env':'ATZE_AI_TOKEN_TEST'}]}))
    with pytest.raises(ValueError): ExternalDataGateway(path)


def test_ai_real_tls(receiver, tmp_path, monkeypatch):
    """AI-008 | Actual TLS | ephemeral self-signed test cert | untrusted then trusted handshake | cert failure then receipt | no model claim."""
    server, seen, _ = receiver
    cert, key = tmp_path/'cert.pem', tmp_path/'key.pem'
    subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-keyout',str(key),'-out',str(cert),'-days','1','-subj','/CN=127.0.0.1','-addext','subjectAltName=IP:127.0.0.1'], check=True, capture_output=True, timeout=20)
    tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    tls.minimum_version = ssl.TLSVersion.TLSv1_2
    tls.load_cert_chain(cert,key)
    server.socket = tls.wrap_socket(server.socket, server_side=True)
    config = tmp_path/'tls.json'
    config.write_text(json.dumps({'providers':[{'id':'tls','mode':'SELF_HOSTED','origin':f'https://127.0.0.1:{server.server_port}','region':'test','token_env':'ATZE_AI_TOKEN_TEST'}]}))
    monkeypatch.setenv('ATZE_AI_TOKEN_TEST','ephemeral-test-only-'*3)
    gateway = ExternalDataGateway(config)
    with pytest.raises(ssl.SSLCertVerificationError): gateway.send('tls','not-a-model','synthetic receipt test',16)
    assert not seen
    monkeypatch.setenv('SSL_CERT_FILE',str(cert))
    assert gateway.send('tls','not-a-model','synthetic receipt test',16).startswith('transport receipt')
    assert len(seen) == 1


def test_ai_remote_privacy_lock(ai):
    """AI-009 | Remote policy | configured HTTPS endpoint without connection | default lock/external deny | blocked before transport."""
    c, r, body, pol, seen, output, settings, config = ai
    data = json.loads(config.read_text());data['providers'][0].update(mode='EXTERNAL_PROVIDER',origin='https://127.0.0.1:9')
    config.write_text(json.dumps(data))
    with TestClient(create_app(replace(settings,ai_config_path=config))) as other:
        other.headers.update(c.headers)
        other.post('/api/ai/policy',headers=r,json=pol)
        altered = (other,r,body,pol,seen,output,settings,config)
        result,_ = request_and_run(altered)
        assert result['attempt']['reason']=='REMOTE_EXPORT_DENIED'
        pol.update(privacy_lock=False,local_only=False,allow_remote=True)
        other.post('/api/ai/policy',headers=r,json=pol)
        req=other.post('/api/ai/requests',json=body).json()
        result=other.post('/api/ai/requests/'+req['id']+'/run',headers=r,json={'context_hash':req['context_hash'],'allow_remote':True,'reason':'explicit synthetic remote test'}).json()
        assert result['attempt']['reason']=='EXTERNAL_AI_DENIED' and not seen


def test_ai_bounds_and_task_memory(ai):
    """AI-010 | Limits/task Memory | actual local records | duplicate/oversize/foreign-task context | blocked before egress."""
    c, r, body, pol, seen, *_ = ai
    project, evidence = seed(c,r)
    tid = task(c,project,evidence)
    mid = c.post('/api/memory',json={'project_id':project['id'],'task_id':tid,'category':'inference','content':'Synthetic memory only','evidence_ids':[]}).json()['id']
    body.update(task_id=task(c,project,evidence),memory_ids=[mid])
    assert c.post('/api/ai/requests',json=body).json()['detail']=='CROSS_TASK_MEMORY'
    body.update(task_id=tid)
    assert c.post('/api/ai/requests',json=body).status_code==201
    body['memory_ids']=[mid,mid]
    assert c.post('/api/ai/requests',json=body).json()['detail']=='DUPLICATE_CONTEXT'
    body.update(memory_ids=[mid]*8,evidence_ids=[evidence['id']])
    assert c.post('/api/ai/requests',json=body).json()['detail']=='CONTEXT_COUNT_EXCEEDED'
    body.update(memory_ids=[],evidence_ids=[],purpose='code')
    assert c.post('/api/ai/requests',json=body).json()['detail']=='MODEL_CAPABILITY_DENIED'
    body.update(purpose='analysis',prompt='X'*8000)
    assert c.post('/api/ai/requests',json=body).json()['detail']=='CONTEXT_SIZE_EXCEEDED' and not seen


def test_ai_missing_auth_invalid_output_and_reads(ai, monkeypatch):
    """AI-011 | Auth/output/read contracts | configured transport | missing/reused token and empty output | block, audit readable."""
    c,r,body,pol,seen,output,settings,_=ai
    c.post('/api/ai/policy',headers=r,json=pol)
    monkeypatch.delenv('ATZE_AI_TOKEN_TRANSPORT_TEST')
    value, req=request_and_run(ai)
    assert value['attempt']['reason']=='PROVIDER_AUTH_NOT_CONFIGURED' and not seen
    assert c.get('/api/ai/requests/'+req['id']).json()['state']=='CONSUMED'
    assert c.get('/api/ai/attempts/'+value['attempt']['id']).json()['output_hash'] is None
    assert len(c.get('/api/ai/models').json())==1
    monkeypatch.setenv('ATZE_AI_TOKEN_TRANSPORT_TEST',settings.operator_token)
    value,_=request_and_run(ai)
    assert value['attempt']['reason']=='PROVIDER_AUTH_NOT_CONFIGURED' and not seen
    monkeypatch.setenv('ATZE_AI_TOKEN_TRANSPORT_TEST','isolated-transport-credential-'*2)
    output['raw']=b'{"choices":[{"message":{"content":""}}]}'
    value,_=request_and_run(ai)
    assert value['attempt']['reason']=='INVALID_PROVIDER_OUTPUT'


def test_ai_write_task_and_unconfigured_model(ai):
    """AI-012 | No action privilege | write task and missing provider | actual APIs | BLOCK with zero transmission."""
    c,r,body,pol,seen,*_=ai
    c.post('/api/ai/policy',headers=r,json=pol)
    project,evidence=seed(c,r)
    body['task_id']=task(c,project,evidence,action='write')
    result,_=request_and_run(ai)
    assert result['attempt']['reason']=='READ_TASK_PRECONDITIONS_REQUIRED' and not seen
    registration=c.get('/api/ai/models').json()[0]
    for name in ['id','created_at','approval_state','validation']: registration.pop(name)
    registration['provider_id']='absent'
    assert c.post('/api/ai/models',headers=r,json=registration).status_code==409


def test_ai_duplicate_startup_config(ai):
    """AI-013 | Startup ambiguity | duplicate configured IDs | load config | reject, not last-wins."""
    *_,config=ai
    data=json.loads(config.read_text());data['providers']*=2;config.write_text(json.dumps(data))
    with pytest.raises(ValueError): ExternalDataGateway(config)


def test_ai_known_unlabelled_credentials(ai):
    """AI-014 | Known credentials | raw platform/provider tokens without labels | prepare | BLOCK before persistence/transport."""
    c,r,body,pol,seen,output,settings,_=ai
    for secret in [settings.operator_token,settings.reviewer_token,settings.challenge_token,'isolated-transport-credential-'*2]:
        body['prompt']='Unlabelled synthetic credential input '+secret
        value=c.post('/api/ai/requests',json=body)
        assert value.status_code==409 and value.json()['detail']=='KNOWN_CREDENTIAL_BLOCKED'
        assert secret not in c.get('/api/audit',headers=r).text
    assert not seen
