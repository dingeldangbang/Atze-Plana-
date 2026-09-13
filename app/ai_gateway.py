"""Only model egress transport. No model import/download, tools, proxies or fallback."""
import hashlib
import http.client
import json
import os
import re
import ssl
from urllib.parse import urlsplit
from app.ai_models import AIConfig


class GateDenied(Exception):
    """Public reason code only; never include provider payload or credential."""


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def scan(text):
    # Conservative rejection, not a complete semantic DLP classifier.
    patterns = [r'-----BEGIN [A-Z ]*PRIVATE KEY-----',
                r"(?i)\b(password|passwd|secret|token|api[_ -]?key|cookie|session|authorization)[\s\"'\\]*[=:][\s\"'\\]*\S+",
                r'(?i)\bbearer\s+\S+', r'\b(?:hf_|sk-|ghp_|github_pat_)[A-Za-z0-9_-]{8,}',
                r'\bAKIA[A-Z0-9]{16}\b']
    if any(re.search(p, text) for p in patterns):
        raise GateDenied('SECRET_PATTERN_BLOCKED')


def origin(config):
    p = urlsplit(config.origin)
    if p.scheme not in {'https', 'http'} or not p.hostname or p.username or p.password or p.query or p.fragment or p.path not in {'', '/'}:
        raise ValueError('AI provider must be an explicit HTTP(S) origin')
    if config.mode == 'LOCAL' and p.hostname not in {'127.0.0.1', '::1'}:
        raise ValueError('LOCAL requires literal loopback, not a hostname')
    if p.scheme != 'https' and config.mode != 'LOCAL':
        raise ValueError('Every off-host AI connection requires HTTPS')
    if p.port is not None and not 1 <= p.port <= 65535:
        raise ValueError('Invalid port')
    return p


class ExternalDataGateway:
    def __init__(self, path=None, forbidden_tokens=()):
        self.forbidden_tokens = forbidden_tokens
        config = AIConfig.model_validate_json(path.read_text()) if path else AIConfig()
        self.providers = {p.id: p for p in config.providers}
        if len(self.providers) != len(config.providers):
            raise ValueError('Duplicate AI provider ID')
        for p in config.providers:
            origin(p)
        self.config_hash = fingerprint(config.model_dump())

    def provider(self, provider_id):
        if provider_id not in self.providers:
            raise GateDenied('PROVIDER_NOT_CONFIGURED')
        return self.providers[provider_id]

    def model_provider(self, provider_id):
        self.provider(provider_id)
        return OpenAICompatibleProvider(self, provider_id)

    def send(self, provider_id, model, context, max_tokens):
        """Called only after persisted request consent/policy validation by AI service."""
        provider = self.provider(provider_id)
        target = origin(provider)
        token = os.environ.get(provider.token_env, '')
        if len(token) < 32 or token in self.forbidden_tokens or '\r' in token or '\n' in token:
            raise GateDenied('PROVIDER_AUTH_NOT_CONFIGURED')
        scan(context)
        if target.scheme == 'https':
            tls = ssl.create_default_context()
            tls.minimum_version = ssl.TLSVersion.TLSv1_2
            conn = http.client.HTTPSConnection(target.hostname, target.port, timeout=15, context=tls)
        else:
            conn = http.client.HTTPConnection(target.hostname, target.port, timeout=15)
        try:
            conn.request('POST', '/v1/chat/completions', body=json.dumps({
                'model': model, 'messages': [{'role': 'user', 'content': context}],
                'max_tokens': max_tokens, 'stream': False}).encode(),
                headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'})
            response = conn.getresponse()
            if response.status != 200:
                raise GateDenied('PROVIDER_HTTP_ERROR_NO_FALLBACK')
            raw = response.read(65537)
            if len(raw) > 65536:
                raise GateDenied('PROVIDER_RESPONSE_TOO_LARGE')
            value = json.loads(raw)
            message = value['choices'][0]['message']
            if message.get('tool_calls') or message.get('function_call'):
                raise GateDenied('MODEL_TOOLS_FORBIDDEN')
            text = message['content']
            if not isinstance(text, str) or not text.strip() or len(text) > 16000:
                raise GateDenied('INVALID_PROVIDER_OUTPUT')
            scan(text)
            return text
        finally:
            conn.close()


class OpenAICompatibleProvider:
    """ModelProvider contract for configured HF/local/custom compatible text servers."""
    def __init__(self, gateway, provider_id):
        self.gateway = gateway
        self.provider_id = provider_id

    def generate(self, model: str, context: str, max_tokens: int) -> str:
        return self.gateway.send(self.provider_id, model, context, max_tokens)
