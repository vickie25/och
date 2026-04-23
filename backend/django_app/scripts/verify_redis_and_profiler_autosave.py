import os
import sys


def main() -> int:
    sys.path.insert(0, "/app")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.production")
    import django

    django.setup()

    from django.conf import settings

    print("REDIS_HOST", getattr(settings, "REDIS_HOST", None))
    print("REDIS_PORT", getattr(settings, "REDIS_PORT", None))
    print("CELERY_BROKER_URL", getattr(settings, "CELERY_BROKER_URL", None))

    from profiler.session_manager import session_manager

    ok_client = session_manager.redis_client is not None
    print("SESSION_MANAGER_HAS_CLIENT", ok_client)
    if not ok_client:
        return 10

    token = session_manager.generate_session_token()
    print("TOKEN", token)
    assert session_manager.save_session(token, {"hello": "world"}, ttl=60) is True
    got = session_manager.get_session(token)
    print("GET_SESSION", got)
    assert got and got.get("hello") == "world"

    assert session_manager.autosave_response(token, "q1", {"a": 1}) is True
    got2 = session_manager.get_session(token)
    print("GET_AFTER_AUTOSAVE_HAS_RESPONSES", bool(got2 and got2.get("responses")))

    assert session_manager.delete_session(token) is True
    got3 = session_manager.get_session(token)
    print("GET_AFTER_DELETE", got3)

    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

