import os
from __future__ import annotations

from pathlib import Path


ENV_PATH = Path("/var/www/och/backend/django_app/.env")


def set_kv(text: str, key: str, value: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    found = False
    for line in lines:
        if line.startswith(f"{key}="):
            out.append(f"{key}={value}")
            found = True
        else:
            out.append(line)
    if not found:
        # append at end with a newline separator if needed
        if out and out[-1].strip() != "":
            out.append("")
        out.append(f"{key}={value}")
    return "\n".join(out).rstrip() + "\n"


def main() -> int:
    # IMPORTANT: do not print secrets
    secret = os.environ.get('PAYSTACK_SECRET_KEY', '')
    public = "pk_live_60a0fe198db26cfb743f17a7ab76630e5a75c2b9"

    if not ENV_PATH.exists():
        print("MISSING_ENV", str(ENV_PATH))
        return 2

    text = ENV_PATH.read_text(encoding="utf-8", errors="ignore")
    text = set_kv(text, "PAYSTACK_SECRET_KEY", secret)
    text = set_kv(text, "PAYSTACK_PUBLIC_KEY", public)
    ENV_PATH.write_text(text, encoding="utf-8")
    print("OK_KEYS_WRITTEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

