from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml


_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "storage" / "spec" / "schema.yaml"


def load_schema_spec(path: Path | None = None) -> Dict[str, Any]:
    """Load the canonical schema specification."""
    spec_path = path or _SCHEMA_PATH
    with spec_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)