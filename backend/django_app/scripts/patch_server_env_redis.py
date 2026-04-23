from __future__ import annotations

from pathlib import Path


TARGET = Path("/var/www/och/backend/django_app/.env")

UPDATES = {
    "REDIS_HOST": "redis",
    "REDIS_PORT": "6379",
    "CELERY_BROKER_URL": "redis://redis:6379/0",
    "CELERY_RESULT_BACKEND": "redis://redis:6379/0",
    "USE_REDIS_CACHE": "true",
}


def main() -> int:
    if not TARGET.exists():
        print("MISSING", str(TARGET))
        return 2

    lines = TARGET.read_text(encoding="utf-8", errors="ignore").splitlines()
    out: list[str] = []
    seen: set[str] = set()

    for line in lines:
        if not line or line.lstrip().startswith("#") or "=" not in line:
            out.append(line)
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        if k in UPDATES:
            out.append(f"{k}={UPDATES[k]}")
            seen.add(k)
        else:
            out.append(line)

    # Append any missing keys
    out.append("")
    out.append("# Redis/Celery (patched by patch_server_env_redis.py)")
    for k, v in UPDATES.items():
        if k not in seen:
            out.append(f"{k}={v}")

    TARGET.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")
    print("PATCHED", str(TARGET))
    for k in UPDATES:
        print("SET", k, UPDATES[k])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

