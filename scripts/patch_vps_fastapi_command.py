from __future__ import annotations

from pathlib import Path

import yaml


COMPOSE_PATH = Path("/var/www/och/docker-compose.yml")


def main() -> int:
    if not COMPOSE_PATH.exists():
        print("MISSING", str(COMPOSE_PATH))
        return 2

    data = yaml.safe_load(COMPOSE_PATH.read_text(encoding="utf-8", errors="ignore")) or {}
    services = data.get("services") or {}
    if "fastapi" not in services:
        print("NO_FASTAPI_SERVICE")
        return 3

    fastapi = services["fastapi"]

    # Force a compatible command line (the Dockerfile.prod CMD includes a uvicorn flag
    # that isn't supported in this environment and causes a crash loop).
    fastapi["command"] = [
        "uvicorn",
        "main:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8001",
        "--workers",
        "2",
        "--log-level",
        "info",
        "--timeout-keep-alive",
        "5",
    ]

    services["fastapi"] = fastapi
    data["services"] = services
    COMPOSE_PATH.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    print("PATCHED_FASTAPI_COMMAND", str(COMPOSE_PATH))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

