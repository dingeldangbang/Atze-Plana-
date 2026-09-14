"""Provider-neutral bounded contracts; metadata is attestation, never live discovery."""
from typing import Literal, Protocol
from pydantic import Field
from app.models import Input

Mode = Literal['LOCAL', 'SELF_HOSTED', 'PRIVATE_ENDPOINT', 'EXTERNAL_PROVIDER']
DataClass = Literal['PUBLIC', 'INTERNAL', 'PROJECT', 'DEVICE', 'PERSONAL', 'CONFIDENTIAL', 'SECRET', 'CREDENTIAL']


class ProviderConfig(Input):
    id: str = Field(pattern=r'^[a-zA-Z0-9_-]{1,64}$')
    mode: Mode
    origin: str = Field(max_length=512)
    token_env: str = Field(pattern=r'^ATZE_AI_TOKEN_[A-Z0-9_]{1,64}$')
    region: str = Field(min_length=1, max_length=80)


class AIConfig(Input):
    providers: list[ProviderConfig] = Field(default_factory=list, max_length=20)


class AIPolicy(Input):
    privacy_lock: bool = True
    local_only: bool = True
    external_ai: bool = False
    allow_remote: bool = False
    providers: list[str] = Field(default_factory=list, max_length=20)
    models: list[str] = Field(default_factory=list, max_length=100)
    projects: list[str] = Field(default_factory=list, max_length=100)
    tasks: list[Literal['analysis', 'plan', 'code']] = Field(default_factory=list, max_length=3)
    data_classes: list[DataClass] = Field(default_factory=list, max_length=8)
    regions: list[str] = Field(default_factory=list, max_length=20)
    max_context_chars: int = Field(default=8000, ge=1, le=16000)
    max_output_tokens: int = Field(default=128, ge=1, le=512)


class ModelRegistration(Input):
    provider_id: str = Field(max_length=64)
    model: str = Field(min_length=1, max_length=200)
    revision: str = Field(pattern=r'^[a-f0-9]{40,64}$')
    license: str = Field(min_length=1, max_length=200)
    capabilities: list[Literal['analysis', 'plan', 'code']] = Field(min_length=1, max_length=3)
    context_length: int = Field(ge=1, le=10000000)
    quantization: str | None = Field(default=None, max_length=80)
    hardware: str = Field(min_length=1, max_length=500)
    evaluation: str = Field(min_length=1, max_length=500)
    security_review: str = Field(min_length=1, max_length=500)


class AIRequest(Input):
    plan_lock_id: str | None = None
    task_id: str
    model_id: str
    purpose: Literal['analysis', 'plan', 'code']
    classification: DataClass = 'CONFIDENTIAL'
    prompt: str = Field(min_length=1, max_length=8000)
    evidence_ids: list[str] = Field(default_factory=list, max_length=8)
    memory_ids: list[str] = Field(default_factory=list, max_length=8)


class AIConsent(Input):
    context_hash: str = Field(pattern=r'^[a-f0-9]{64}$')
    allow_remote: bool = False
    reason: str = Field(min_length=8, max_length=500)


class ModelProvider(Protocol):
    def generate(self, model: str, context: str, max_tokens: int) -> str: ...


class AgentProvider(ModelProvider, Protocol):
    """Planning text only; no implicit tool authority."""


class EmbeddingProvider(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...


class VisionProvider(Protocol):
    def describe(self, image: bytes) -> str: ...


class SpeechProvider(Protocol):
    def transcribe(self, audio: bytes) -> str: ...


class RerankerProvider(Protocol):
    def rank(self, query: str, documents: list[str]) -> list[int]: ...
