"""MCP discovery: actual isolated HTTPS peer, synthetic protocol data, not Bright Data live proof."""
from dataclasses import replace
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import ssl
import subprocess
import threading
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.mcp_client import DiscoveryClient, VERSION
from app.ai_gateway import GateDenied
from conftest import seed, task


@pytest.fixture
def peer(tmp_path, monkeypatch):
    seen, behavior = [], {'case':'json'}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # Only isolated peer logs; never dump bearer credentials.
        def do_DELETE(self):
            seen.append(('DELETE', self.path, None))
            self.send_response(500 if behavior['case']=='cleanup' else 204);self.end_headers()
        def do_POST(self):
            body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            seen.append(('POST',self.path,body))
            assert self.headers['Authorization']=='Bearer synthetic-oauth-access'
            case=behavior['case']
            if case=='http':
                self.send_response(302);self.send_header('Location','https://example.org/not-followed');self.end_headers();return
            if body['method']=='notifications/initialized':
                self.send_response(202);self.end_headers();return
            if body['method']=='initialize':
                result={'protocolVersion':'invalid' if case=='version' else VERSION,'capabilities':{'tools':{}}}
            else:
                result={'tools':[{'name':'search_engine','inputSchema':{'type':'object'},'description':'Untrusted instruction ignored'},
                                 {'name':'dangerous_unselected','inputSchema':{'type':'object'}}]}
                if case=='pagination':result['nextCursor']='not-silently-ignored'
                if case=='duplicate':result['tools']*=2
                if case=='malformed':result['tools']=[{'name':'search_engine'}]
            response={'jsonrpc':'2.0','id':999 if case=='id' else body['id'],'result':result}
            if case=='server-request':response={'jsonrpc':'2.0','id':body['id'],'method':'sampling/createMessage','params':{}}
            raw=json.dumps(response).encode()
            if case=='broken_json':raw=b'not json'
            if case=='keys':raw=b'{"jsonrpc":"2.0","id":1,"id":1,"result":{}}'
            if case=='oversize':raw=b'x'*(512*1024+1)
            if case=='reflection':raw=b'{"value":"synthetic-oauth-access"}'
            if case=='sse':raw=b'event: message\ndata: '+raw+b'\n\n'
            self.send_response(200)
            self.send_header('Content-Type','text/event-stream' if case=='sse' else 'application/json')
            self.send_header('Mcp-Session-Id','isolated-session')
            self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
    key,cert=tmp_path/'key.pem',tmp_path/'cert.pem'
    subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-keyout',str(key),'-out',str(cert),'-days','1','-subj','/CN=127.0.0.1','-addext','subjectAltName=IP:127.0.0.1'],check=True,capture_output=True,timeout=20)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    tls=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);tls.minimum_version=ssl.TLSVersion.TLSv1_2;tls.load_cert_chain(cert,key)
    server.socket=tls.wrap_socket(server.socket,server_side=True)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    def connection(self):
        context=ssl.create_default_context(cafile=str(cert));context.minimum_version=ssl.TLSVersion.TLSv1_2
        return http.client.HTTPSConnection('127.0.0.1',server.server_port,timeout=self.remaining(),context=context)
    monkeypatch.setattr(DiscoveryClient,'connection',connection)
    yield seen,behavior,server
    server.shutdown();server.server_close();thread.join(timeout=3)


@pytest.mark.parametrize('case',['json','sse'])
def test_mcp_real_tls_handshake_and_cleanup(peer,case):
    """MCP-001: actual verified TLS/JSON or SSE → ordered RPC and cleanup, only candidate names, no tools/call."""
    seen,behavior,_=peer;behavior['case']=case
    result=DiscoveryClient('synthetic-oauth-access').discover()
    assert result['candidate_tools']==['search_engine'] and not result['allowed_for_action']
    assert 'Untrusted' not in json.dumps(result)
    assert [v[2]['method'] if v[2] else v[0] for v in seen]==['initialize','notifications/initialized','tools/list','DELETE']
    assert all(v[1]=='/mcp' for v in seen)


@pytest.mark.parametrize('case',['http','version','id','pagination','duplicate','malformed','oversize','reflection','server-request','cleanup','keys'])
def test_mcp_response_fail_closed(peer,case):
    """MCP-002: real adverse TLS replies → reject redirect/format/scope/injection/cleanup; no fallback or tool execution."""
    seen,behavior,_=peer;behavior['case']=case
    with pytest.raises(GateDenied):DiscoveryClient('synthetic-oauth-access').discover()
    assert all(v[1]=='/mcp' and (not v[2] or v[2]['method']!='tools/call') for v in seen)


def setup(client,reviewer):
    p,e=seed(client,reviewer);tid=task(client,p,e)
    body={'task_id':tid,'allow_external_discovery':True,'reason':'Explicit isolated metadata discovery'}
    pol={'privacy_lock':False,'local_only':False,'allow_remote':True,'external_ai':False,'projects':[p['id']],
         'data_classes':['PUBLIC'],'regions':['brightdata-provider-managed']}
    return body,pol


def test_mcp_api_default_deny_roles_and_config(client,reviewer,peer):
    """MCP-003: actual API auth/default policy/absent OAuth; no network and durable BLOCKED evidence."""
    body,pol=setup(client,reviewer)
    assert not client.get('/api/mcp/brightdata/status').json()['configured']
    assert client.post('/api/mcp/brightdata/discover',json=body).status_code==403
    assert client.post('/api/mcp/brightdata/discover',json=body,headers=reviewer).json()['attempt']['state']=='BLOCKED'
    client.post('/api/ai/policy',headers=reviewer,json=pol)
    result=client.post('/api/mcp/brightdata/discover',json=body,headers=reviewer).json()
    assert result['attempt']['reason']=='MCP_OAUTH_NOT_CONFIGURED_OR_INVALID' and peer[0]==[]


def test_mcp_api_real_peer_and_stop_plan_gates(settings,reviewer,peer):
    """MCP-004: full real HTTP API→TLS peer with explicit policy; stop/privacy/PLAN deny further IO; no source text transferred."""
    settings=replace(settings,brightdata_oauth_token='synthetic-oauth-access')
    with TestClient(create_app(settings)) as c:
        c.headers['Authorization']='Bearer '+settings.operator_token
        body,pol=setup(c,reviewer);c.post('/api/ai/policy',headers=reviewer,json=pol)
        result=c.post('/api/mcp/brightdata/discover',headers=reviewer,json=body).json()
        assert result['attempt']['state']=='DISCOVERED' and result['catalog']['candidate_tools']==['search_engine']
        assert body['task_id'] not in json.dumps(peer[0]) and body['reason'] not in json.dumps(peer[0])
        for key in ['allow_remote','local_only','privacy_lock']:
            altered={**pol,key:False if key=='allow_remote' else True}
            c.post('/api/ai/policy',headers=reviewer,json=altered)
            assert c.post('/api/mcp/brightdata/discover',headers=reviewer,json=body).json()['attempt']['state']=='BLOCKED'
        c.post('/api/ai/policy',headers=reviewer,json=pol)
        c.post('/api/control/stop',headers=reviewer,json={'active':True,'reason':'Isolated stop'})
        assert c.post('/api/mcp/brightdata/discover',headers=reviewer,json=body).json()['attempt']['reason']=='EMERGENCY_STOP'
        c.post('/api/control/stop',headers=reviewer,json={'active':False,'reason':'Isolated reset'})
        eid=c.get('/api/evidence').json()[0]['id']
        c.post('/api/plans',json={'task_id':body['task_id'],'title':'Unapproved actual context','resources':[{'kind':'evidence','id':eid}]})
        assert c.post('/api/mcp/brightdata/discover',headers=reviewer,json=body).json()['attempt']['reason']=='MCP_PLAN_CONTEXT_NOT_CURRENT'
        assert len(peer[0])==4


def test_mcp_certificate_verification(peer,monkeypatch):
    """MCP-005: untrusted real TLS certificate refused, never CERT_NONE/-k fallback."""
    _,_,server=peer
    monkeypatch.setattr(DiscoveryClient,'connection',lambda self:http.client.HTTPSConnection('127.0.0.1',server.server_port,timeout=2,context=ssl.create_default_context()))
    with pytest.raises(ssl.SSLCertVerificationError):DiscoveryClient('synthetic-oauth-access').discover()


def test_mcp_invalid_credential_and_deadline(tmp_path, monkeypatch):
    """MCP-006: invalid bearer/header injection and expired deadline stop before transport."""
    for token in ['', 'bad\r\nheader', 'not ascii ä']:
        with pytest.raises(GateDenied):DiscoveryClient(token)
    keylog=tmp_path/'forbidden-keylog'
    monkeypatch.setenv('SSLKEYLOGFILE',str(keylog))
    client=DiscoveryClient('synthetic-oauth-access')
    connection=client.connection()
    assert connection._context.check_hostname and connection._context.verify_mode==ssl.CERT_REQUIRED
    assert connection._context.keylog_filename is None and not keylog.exists()
    connection.close()
    client.deadline=0
    with pytest.raises(GateDenied):client.remaining()


def test_mcp_reserved_audit_failure_prevents_io(settings,reviewer,peer):
    """MCP-007: real SQLite audit insert failure rolls back attempt before any TLS traffic."""
    import sqlite3
    settings=replace(settings,brightdata_oauth_token='synthetic-oauth-access')
    with TestClient(create_app(settings)) as c:
        c.headers['Authorization']='Bearer '+settings.operator_token
        body,pol=setup(c,reviewer);c.post('/api/ai/policy',headers=reviewer,json=pol)
        with sqlite3.connect(settings.db_path) as db:
            db.execute("CREATE TRIGGER fail_mcp BEFORE INSERT ON records WHEN NEW.kind='audit' AND json_extract(NEW.body,'$.event')='mcp.discovery_reserved' BEGIN SELECT RAISE(ABORT,'isolated audit failure'); END")
        with pytest.raises(sqlite3.IntegrityError):c.post('/api/mcp/brightdata/discover',headers=reviewer,json=body)
        assert peer[0]==[]


def test_mcp_scope_mismatch(settings,reviewer,peer):
    """MCP-008: missing project/data-class/region permission or explicit consent cannot contact peer."""
    settings=replace(settings,brightdata_oauth_token='synthetic-oauth-access')
    with TestClient(create_app(settings)) as c:
        c.headers['Authorization']='Bearer '+settings.operator_token
        body,pol=setup(c,reviewer)
        for field in ['projects','data_classes','regions']:
            c.post('/api/ai/policy',headers=reviewer,json={**pol,field:[]})
            assert c.post('/api/mcp/brightdata/discover',headers=reviewer,json=body).json()['attempt']['reason']=='MCP_TASK_PROJECT_CLASS_REGION_DENIED'
        c.post('/api/ai/policy',headers=reviewer,json=pol)
        assert c.post('/api/mcp/brightdata/discover',headers=reviewer,json={**body,'allow_external_discovery':False}).json()['attempt']['state']=='BLOCKED'
        assert peer[0]==[]


@pytest.mark.parametrize('case,state',[('id','BLOCKED'),('broken_json','UNAVAILABLE')])
def test_mcp_api_transport_outcome_persisted(settings,reviewer,peer,case,state):
    """MCP-009: real bad peer responses persist failure without catalog/credential disclosure."""
    settings=replace(settings,brightdata_oauth_token='synthetic-oauth-access')
    with TestClient(create_app(settings)) as c:
        c.headers['Authorization']='Bearer '+settings.operator_token
        body,pol=setup(c,reviewer);c.post('/api/ai/policy',headers=reviewer,json=pol)
        peer[1]['case']=case
        result=c.post('/api/mcp/brightdata/discover',headers=reviewer,json=body).json()
        assert result['attempt']['state']==state and result['catalog'] is None
        assert 'synthetic-oauth-access' not in json.dumps(result)
        events=c.get('/api/audit',headers=reviewer).json()
        assert any(v['event']=='mcp.discovery_outcome' for v in events)


def test_mcp_separate_platform_credential(settings):
    """MCP-010: configuration cannot reuse a platform role credential for external authentication."""
    with pytest.raises(ValueError):replace(settings,brightdata_oauth_token=settings.operator_token)


from test_ai_privacy import ai, receiver  # Explicit isolated real HTTP transport fixtures, not model inference.


def test_mcp_oauth_never_model_context(ai):
    """MCP-011: configured OAuth credential in prompt is blocked by the actual model API before any HTTP transport."""
    _, _, body, _, seen, _, settings, _ = ai
    credential = 'opaque-brightdata-oauth-test-credential'
    with TestClient(create_app(replace(settings, brightdata_oauth_token=credential))) as c:
        c.headers['Authorization'] = 'Bearer ' + settings.operator_token
        result = c.post('/api/ai/requests', json={**body, 'prompt': credential})
        assert result.status_code == 409 and result.json()['detail'] == 'KNOWN_CREDENTIAL_BLOCKED'
        assert seen == []
