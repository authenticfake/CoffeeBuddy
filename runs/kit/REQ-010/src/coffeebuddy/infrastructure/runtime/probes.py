from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Protocol, Tuple

from .config import ServiceConfig


@dataclass(frozen=True)
class ProbeResult:
    name: str
    passed: bool
    detail: str
    duration_ms: float


class Probe(Protocol):
    name: str

    async def check(self) -> ProbeResult:
        ...


class ReadinessRegistry:
    """Registers async probes and evaluates readiness sequentially."""

    def __init__(self) -> None:
        self._probes: List[Probe] = []

    def register(self, probe: Probe) -> None:
        self._probes.append(probe)

    async def evaluate(self) -> Tuple[bool, List[ProbeResult]]:
        results: List[ProbeResult] = []
        overall = True
        for probe in self._probes:
            result = await probe.check()
            results.append(result)
            if not result.passed:
                overall = False
        return overall, results


class EnvironmentProbe:
    """Ensures critical runtime artifacts (Vault token, env) exist before declaring readiness."""

    name = "environment"

    def __init__(self, config: ServiceConfig) -> None:
        self._config = config

    async def check(self) -> ProbeResult:
        start = time.perf_counter()
        missing: list[str] = []

        vault_token_path: Path = self._config.vault.token_path
        if not vault_token_path.exists():
            missing.append(f"vault_token_missing:{vault_token_path}")

        if not self._config.kafka.brokers:
            missing.append("kafka_brokers_missing")

        passed = len(missing) == 0
        detail = "ok" if passed else ";".join(missing)
        duration_ms = (time.perf_counter() - start) * 1000
        await asyncio.sleep(0)  # yield control
        return ProbeResult(name=self.name, passed=passed, detail=detail, duration_ms=duration_ms)


__all__ = ["ProbeResult", "Probe", "ReadinessRegistry", "EnvironmentProbe"]