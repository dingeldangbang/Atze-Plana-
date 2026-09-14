"""Bounded Bright Data MCP transport: discovery plus allowlisted tools/call; no auth fallback."""
import hashlib
import http.client
import json
import ssl
import time
from app.ai_gateway import GateDenied

HOST = 'mcp.brightdata.com'
PATH = '/mcp'
VERSION = '2025-06-18'
MAX_BYTES = 512 * 1024
CANDIDATES = {'search_engine', 'scrape_as_markdown'}
MAX_ARGUMENT_BYTES = 4096
MAX_CONTENT_ITEMS = 64
MAX_EXCERPT_CHARS = 16384


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise GateDenied('MCP_DUPLICATE_JSON_KEY')
        value[key] = item
    return value


class DiscoveryClient:
    def __init__(self, token):
        if not token or not token.isascii() or any(ord(c) <= 32 or ord(c) >= 127 for c in token) or len(token) > 8192:
            raise GateDenied('MCP_OAUTH_NOT_CONFIGURED_OR_INVALID')
        self.token = token
        self.session = None
        self.deadline = time.monotonic() + 12

    def connection(self):
        # Do not honor SSLKEYLOGFILE: authentication transport secrets must not be cached.
        tls = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        tls.load_default_certs()
        tls.minimum_version = ssl.TLSVersion.TLSv1_2
        return http.client.HTTPSConnection(HOST, timeout=self.remaining(), context=tls)

    def remaining(self):
        seconds = self.deadline - time.monotonic()
        if seconds <= 0:
            raise GateDenied('MCP_DEADLINE_EXCEEDED')
        return min(seconds, 3)

    def exchange(self, method, message=None, notification=False):
        headers = {'Authorization': 'Bearer ' + self.token,
                   'Accept': 'application/json, text/event-stream', 'Content-Type': 'application/json',
                   'MCP-Protocol-Version': VERSION}
        if self.session:
            headers['Mcp-Session-Id'] = self.session
        conn = self.connection()
        conn.set_debuglevel(0)  # Never emit Authorization/session headers through HTTP debug tracing.
        try:
            conn.request(method, PATH, body=json.dumps(message).encode() if message else None, headers=headers)
            response = conn.getresponse()
            new_session = response.getheader('Mcp-Session-Id')
            if new_session:
                if len(new_session) > 256 or not new_session.isascii() or any(ord(c) < 33 or ord(c) > 126 for c in new_session):
                    raise GateDenied('MCP_INVALID_SESSION')
                if self.session and new_session != self.session:
                    raise GateDenied('MCP_SESSION_CHANGED')
                self.session = new_session
            if method == 'DELETE':
                if response.status not in {200, 202, 204}:
                    raise GateDenied('MCP_SESSION_CLEANUP_UNCONFIRMED')
                return None
            if notification:
                if response.status not in {202, 204}:
                    raise GateDenied('MCP_NOTIFICATION_REJECTED')
                return None
            if response.status != 200:
                raise GateDenied(f'MCP_HTTP_{response.status}_NO_FALLBACK')
            mime = response.getheader('Content-Type', '').split(';')[0].strip().lower()
            if mime not in {'application/json', 'text/event-stream'}:
                raise GateDenied('MCP_UNSUPPORTED_CONTENT_TYPE')
            raw = b''
            while True:
                self.remaining()
                if conn.sock:
                    conn.sock.settimeout(self.remaining())
                block = response.read1(min(8192, MAX_BYTES + 1 - len(raw)))
                raw += block
                if len(raw) > MAX_BYTES:
                    raise GateDenied('MCP_RESPONSE_TOO_LARGE')
                if mime == 'text/event-stream' and b'\n\n' in raw.replace(b'\r\n', b'\n'):
                    # Only one bounded response event supported; never execute requests/notifications.
                    event = raw.replace(b'\r\n', b'\n').split(b'\n\n', 1)[0]
                    data = b'\n'.join(line[5:].lstrip(b' ') for line in event.split(b'\n') if line.startswith(b'data:'))
                    if not data:
                        raise GateDenied('MCP_UNSUPPORTED_SSE_EVENT')
                    raw = data
                    break
                if not block:
                    if mime == 'text/event-stream':
                        raise GateDenied('MCP_INCOMPLETE_SSE_EVENT')
                    break
            text = raw.decode('utf-8')
            if self.token in text:
                raise GateDenied('MCP_CREDENTIAL_REFLECTION')
            value = json.loads(text, object_pairs_hook=unique_object)
            if not isinstance(value, dict) or value.get('jsonrpc') != '2.0' or type(value.get('id')) is not int or value['id'] != message['id'] or 'method' in value or 'error' in value or not isinstance(value.get('result'), dict):
                raise GateDenied('MCP_INVALID_RPC_RESPONSE')
            return value['result']
        finally:
            conn.close()

    def discover(self):
        try:
            initial = self.exchange('POST', {'jsonrpc':'2.0', 'id':1, 'method':'initialize', 'params':{
                'protocolVersion':VERSION, 'capabilities':{}, 'clientInfo':{'name':'atze-discovery-only', 'version':'0.4.0.dev0'}}})
            if initial.get('protocolVersion') != VERSION or not isinstance(initial.get('capabilities', {}).get('tools'), dict):
                raise GateDenied('MCP_PROTOCOL_OR_TOOLS_UNSUPPORTED')
            self.exchange('POST', {'jsonrpc':'2.0', 'method':'notifications/initialized'}, notification=True)
            result = self.exchange('POST', {'jsonrpc':'2.0', 'id':2, 'method':'tools/list', 'params':{}})
            tools = result.get('tools')
            if ('nextCursor' in result and result['nextCursor'] is not None) or not isinstance(tools, list) or len(tools) > 200:
                raise GateDenied('MCP_CATALOG_SCOPE_UNSUPPORTED')
            names = []
            for tool in tools:
                if not isinstance(tool, dict) or not isinstance(tool.get('name'), str) or not isinstance(tool.get('inputSchema'), dict):
                    raise GateDenied('MCP_INVALID_TOOL_DESCRIPTOR')
                if tool['name'] in CANDIDATES:
                    if tool['name'] in names:
                        raise GateDenied('MCP_DUPLICATE_TOOL')
                    names.append(tool['name'])
            return {'candidate_tools': sorted(names), 'catalog_sha256': hashlib.sha256(json.dumps(result, sort_keys=True).encode()).hexdigest(),
                    'source':'EXTERNAL_SOURCE', 'tool_execution':'AVAILABLE_AS_SEPARATE_BOUNDED_ENDPOINT', 'allowed_for_action':False}
        finally:
            if self.session:
                self.exchange('DELETE')

    def call(self, tool, arguments):
        # Bounded allowlisted tools/call only; arguments are caller-supplied, results EXTERNAL_SOURCE.
        if tool not in CANDIDATES:
            raise GateDenied('MCP_TOOL_NOT_ALLOWLISTED')
        if not isinstance(arguments, dict):
            raise GateDenied('MCP_INVALID_TOOL_ARGUMENTS')
        encoded = json.dumps(arguments)
        if len(encoded.encode()) > MAX_ARGUMENT_BYTES:
            raise GateDenied('MCP_TOOL_ARGUMENTS_TOO_LARGE')
        if self.token in encoded:
            raise GateDenied('MCP_CREDENTIAL_IN_ARGUMENTS')
        try:
            initial = self.exchange('POST', {'jsonrpc':'2.0', 'id':1, 'method':'initialize', 'params':{
                'protocolVersion':VERSION, 'capabilities':{}, 'clientInfo':{'name':'atze-tools-call-bounded', 'version':'0.4.0.dev0'}}})
            if initial.get('protocolVersion') != VERSION or not isinstance(initial.get('capabilities', {}).get('tools'), dict):
                raise GateDenied('MCP_PROTOCOL_OR_TOOLS_UNSUPPORTED')
            self.exchange('POST', {'jsonrpc':'2.0', 'method':'notifications/initialized'}, notification=True)
            result = self.exchange('POST', {'jsonrpc':'2.0', 'id':2, 'method':'tools/call',
                                            'params':{'name':tool, 'arguments':arguments}})
            content = result.get('content')
            if not isinstance(content, list) or len(content) > MAX_CONTENT_ITEMS:
                raise GateDenied('MCP_INVALID_TOOL_RESULT')
            texts = []
            for item in content:
                if not isinstance(item, dict) or not isinstance(item.get('type'), str):
                    raise GateDenied('MCP_INVALID_TOOL_CONTENT')
                if item.get('type') == 'text' and isinstance(item.get('text'), str):
                    texts.append(item['text'])
            return {'tool': tool, 'is_error': bool(result.get('isError')), 'content_items': len(content),
                    'excerpt': '\n'.join(texts)[:MAX_EXCERPT_CHARS],
                    'result_sha256': hashlib.sha256(json.dumps(result, sort_keys=True).encode()).hexdigest(),
                    'result_size_bytes': len(json.dumps(result).encode()),
                    'source': 'EXTERNAL_SOURCE', 'allowed_for_action': False}
        finally:
            if self.session:
                self.exchange('DELETE')
