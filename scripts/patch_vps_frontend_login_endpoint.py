from __future__ import annotations

from pathlib import Path


TARGET = Path("/var/www/och/frontend/nextjs_app/app/api/auth/login/route.ts")


def main() -> int:
    if not TARGET.exists():
        print("MISSING", str(TARGET))
        return 2

    text = TARGET.read_text(encoding="utf-8", errors="ignore")

    old = "${djangoUrl}/v1/auth/login/simple"
    new = "${djangoUrl}/api/v1/auth/login"

    if old not in text and new in text:
        print("ALREADY_PATCHED")
        return 0

    if old not in text:
        print("PATTERN_NOT_FOUND")
        return 3

    patched = text.replace(old, new)
    TARGET.write_text(patched, encoding="utf-8")
    print("PATCHED", str(TARGET))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

