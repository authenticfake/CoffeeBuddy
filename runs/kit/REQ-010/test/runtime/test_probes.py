from pathlib import Path

import pytest

from coffeebuddy.infrastructure.runtime.config import (
    DatabaseConfig,
    KafkaConfig,
    MetricsConfig,
    OryConfig,
    ServiceConfig,
    SlackConfig,
    VaultConfig,
)
from coffeebuddy.infrastructure.runtime.probes import EnvironmentProbe


def _service_config(tmp_path: Path) -> ServiceConfig:
    token = tmp_path / "vault.token"
    token.write_text("token")
    return ServiceConfig(
        service_name="cb",
        environment="test",
        version="0.0.1",
        host="0.0.0.0",
        port=8080,
        slack=SlackConfig(signing_secret="secret", bot_token="token", app_id=None),
        database=DatabaseConfig(url="postgresql://x", pool_min_size=1, pool_max_size=5),
        kafka=KafkaConfig(brokers=["broker:9092"], security_protocol="PLAINTEXT", sasl_username=None, sasl_password=None),
        vault=VaultConfig(address="https://vault", role="role", token_path=token, secret_paths=["secret/data/coffeebuddy"]),
        ory=OryConfig(issuer_url="https://ory", audience="cb", client_id="client"),
        metrics=MetricsConfig(path="/metrics", multiprocess_dir=None, enable_default_process_metrics=True),
        debug_enabled=False,
    )


@pytest.mark.anyio
async def test_environment_probe_passes_when_token_exists(tmp_path):
    config = _service_config(tmp_path)
    probe = EnvironmentProbe(config)
    result = await probe.check()
    assert result.passed
    assert result.detail == "ok"


@pytest.mark.anyio
async def test_environment_probe_fails_without_token(tmp_path):
    config = _service_config(tmp_path)
    missing_path = tmp_path / "missing"
    config = ServiceConfig(
        **{
            **config.__dict__,
            "vault": VaultConfig(
                address=config.vault.address,
                role=config.vault.role,
                token_path=missing_path,
                secret_paths=config.vault.secret_paths,
            ),
        }
    )
    probe = EnvironmentProbe(config)
    result = await probe.check()
    assert not result.passed
    assert "vault_token_missing" in result.detail