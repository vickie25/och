from pathlib import Path


TARGET = Path(
    "/var/www/och/frontend/nextjs_app/app/api/profiling/enhanced/session/[sessionId]/complete/route.ts"
)


def main() -> int:
    if not TARGET.exists():
        print("MISSING", str(TARGET))
        return 2

    text = TARGET.read_text(encoding="utf-8", errors="ignore")
    if "AbortSignal.timeout(120000)" in text:
        print("ALREADY_OK")
        return 0

    if "AbortSignal.timeout(15000)" not in text:
        print("UNEXPECTED_CONTENT")
        return 3

    text2 = text.replace("AbortSignal.timeout(15000)", "AbortSignal.timeout(120000)")
    TARGET.write_text(text2, encoding="utf-8")
    print("PATCHED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

