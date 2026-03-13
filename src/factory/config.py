"""Configuration for the multi-agent factory."""

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class ServerConfig:
    model: str = "mlx-community/Qwen2.5-Coder-7B-Instruct-4bit"
    host: str = "127.0.0.1"
    port: int = 8080


@dataclass
class AgentConfig:
    max_attempts: int = 5
    execution_timeout: int = 60
    llm_timeout: int = 120
    max_tokens_per_turn: int = 4096
    total_token_budget: int = 50_000
    temperature: float = 0.0
    stagnation_threshold: int = 3  # same error N times → stuck


@dataclass
class Config:
    server: ServerConfig = field(default_factory=ServerConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    workspace_dir: str = "workspace/output"
    log_level: str = "INFO"

    @classmethod
    def load(cls, path: Path | None = None) -> "Config":
        """Load config from factory.toml/yaml or return defaults."""
        if path and path.exists():
            raw = yaml.safe_load(path.read_text())
            return cls._from_dict(raw)
        # Try default locations
        for name in ("factory.yaml", "factory.toml"):
            p = Path(name)
            if p.exists():
                raw = yaml.safe_load(p.read_text())
                return cls._from_dict(raw)
        return cls()

    @classmethod
    def _from_dict(cls, raw: dict) -> "Config":
        cfg = cls()
        if "server" in raw:
            for k, v in raw["server"].items():
                if hasattr(cfg.server, k):
                    setattr(cfg.server, k, v)
        if "agent" in raw:
            for k, v in raw["agent"].items():
                if hasattr(cfg.agent, k):
                    setattr(cfg.agent, k, v)
        if "workspace_dir" in raw:
            cfg.workspace_dir = raw["workspace_dir"]
        if "log_level" in raw:
            cfg.log_level = raw["log_level"]
        return cfg
