from __future__ import annotations

from pathlib import Path


TARGET = Path("/var/www/och/backend/fastapi_app/routers/v1/profiling.py")


BAD = 'session_ids = redis_client.smembers(f"user_sessions:{user_id}")'

FIX = """rc = _get_redis()
    if rc:
        try:
            session_ids = rc.smembers(f"user_sessions:{user_id}")
        except Exception as e:
            logger.error(f"Redis smembers error: {e}")
            session_ids = set()
    else:
        session_ids = set()"""


def main() -> int:
    if not TARGET.exists():
        print("MISSING", str(TARGET))
        return 2

    text = TARGET.read_text(encoding="utf-8", errors="ignore")

    if BAD not in text and "redis_client.smembers" not in text:
        print("ALREADY_OK")
        return 0

    patched = text.replace(BAD, FIX)

    # Defensive: refuse to write if we didn't remove all redis_client.smembers uses
    if "redis_client.smembers" in patched:
        print("PATCH_INCOMPLETE")
        return 3

    TARGET.write_text(patched, encoding="utf-8")
    print("PATCHED", str(TARGET))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

from pathlib import Path


TARGET = Path("/var/www/och/backend/fastapi_app/routers/v1/profiling.py")


START_OLD = "session_ids = redis_client.smembers(f\"user_sessions:{user_id}\")"
STATUS_OLD = "session_ids = redis_client.smembers(f\"user_sessions:{user_id}\")"


START_NEW = """rc = _get_redis()
    if rc:
        try:
            session_ids = rc.smembers(f"user_sessions:{user_id}")
        except Exception as e:
            logger.error(f"Redis smembers error: {e}")
            session_ids = set()
    else:
        session_ids = set()"""


def main() -> int:
    if not TARGET.exists():
        print("MISSING", str(TARGET))
        return 2

    text = TARGET.read_text(encoding="utf-8", errors="ignore")

    if "redis_client.smembers" not in text:
        print("NO_REDIS_CLIENT_REFS_FOUND")
        return 0

    # Replace ALL occurrences of the known bad line with the safe block.
    # Indentation in the file is 4 spaces under functions; ensure that matches.
    patched = text.replace(START_OLD, START_NEW)

    # If there are still any redis_client references, fail loudly.
    if "redis_client.smembers" in patched:
        print("PATCH_INCOMPLETE")
        return 3

    TARGET.write_text(patched, encoding="utf-8")
    print("PATCHED", str(TARGET))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

