"""Fail-closed environment configuration; never logs credentials."""
import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    db_path: Path
    operator_token: str = field(repr=False)
    reviewer_token: str = field(repr=False)

    storage_root: Path | None = None
    sd_root: Path | None = None

    mode: str = "operational"
    challenge_token: str = field(default="", repr=False)

    ai_config_path: Path | None = None

    def __post_init__(self):
        if self.challenge_token and (len(self.challenge_token) < 32 or self.challenge_token in {self.operator_token, self.reviewer_token}):
            raise ValueError('Challenge credential must be separate and at least 32 characters')
        if self.mode not in {"operational", "test"}:
            raise ValueError("ATZE_MODE must be operational or test")
        if min(len(self.operator_token), len(self.reviewer_token)) < 32:
            raise ValueError('Both API tokens must contain at least 32 characters')
        if self.operator_token == self.reviewer_token:
            raise ValueError('Operator and reviewer credentials must differ')

    @classmethod
    def from_env(cls):
        return cls(Path(os.getenv('ATZE_DB_PATH', 'data/atze.db')),
                   os.getenv('ATZE_OPERATOR_TOKEN', ''), os.getenv('ATZE_REVIEWER_TOKEN', ''),
                   Path(os.getenv('ATZE_STORAGE_ROOT')) if os.getenv('ATZE_STORAGE_ROOT') else None,
                   Path(os.getenv('ATZE_SD_ROOT')) if os.getenv('ATZE_SD_ROOT') else None,
                   os.getenv('ATZE_MODE', 'operational'),
                   os.getenv('ATZE_CHALLENGE_TOKEN', ''),
                   Path(os.environ['ATZE_AI_CONFIG']) if os.getenv('ATZE_AI_CONFIG') else None)
