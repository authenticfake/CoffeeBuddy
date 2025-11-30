from __future__ import annotations

import uvicorn

from .container import build_runtime


def main() -> None:
    app = build_runtime()
    config = app.state.config
    uvicorn.run(app, host=config.host, port=config.port, factory=False, log_level="info")


if __name__ == "__main__":
    main()