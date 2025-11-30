import os
from pathlib import Path

import pytest

from coffeebuddy.infrastructure.runtime.config import ConfigError, load_service_config


def _set_min_env(monkeypatch, tmp_path: Path):
    vault_token = tmp_path / "vault.token"
    vault_token.write_text("token")
    env = {
        "SLACK_SIGNING_SECRET": "secret",
        "SLACK_BOT_TOKEN": "xoxb-token",
        "DATABASE_URL": "postgresql://user:pass@db:5432/coffeebuddy",
        "KAFKA_BROKERS": "kafka:9092",
        "VAULT_ADDR": "https://vault.local",
        "VAULT_ROLE": "coffeebuddy",
        "VAULT_TOKEN_PATH": str(vault_token),
        "ORY_ISSUER_URL": "https://ory.local",
        "ORY_AUDIENCE": "coffeebuddy",
        "ORY_CLIENT_ID": "coffeebuddy-client",
    }
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    return env


def test_load_service_config_reads_expected_fields(monkeypatch, tmp_path):
    _set_min_env(monkeypatch, tmp_path)
    monkeypatch.setenv("SERVICE_NAME", "cb-runtime")
    config = load_service_config()
    assert config.service_name == "cb-runtime"
    assert config.database.url.startswith("postgresql://")
    assert config.kafka.brokers == ["kafka:9092"]
    assert config.vault.token_path.exists()
    assert config.metrics.path == "/metrics"


def test_load_service_config_requires_mandatory_keys(monkeypatch):
    monkeypatch.delenv("SLACK_SIGNING_SECRET", raising=False)
    with pytest.raises(ConfigError):
        load_service_config()