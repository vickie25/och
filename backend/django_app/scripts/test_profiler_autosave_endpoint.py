import os
import sys


def main() -> int:
    sys.path.insert(0, "/app")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.production")
    import django

    django.setup()

    from django.contrib.auth import get_user_model
    from rest_framework.test import APIRequestFactory, force_authenticate

    from profiler.models import ProfilerSession
    from profiler.views import autosave_response

    User = get_user_model()

    # Create a disposable user
    email = "profiler-smoke@example.com"
    u = User.objects.filter(email=email).first()
    if not u:
        u = User.objects.create_user(email=email, username="profiler_smoke", password="x")
    u.is_active = True
    u.email_verified = True
    u.account_status = "active"
    u.save()

    # Create a profiler session row (required by autosave endpoint)
    s = ProfilerSession.objects.filter(user=u).first()
    if not s:
        s = ProfilerSession.objects.create(
            user=u,
            status="started",
            current_section="welcome",
            current_question_index=0,
        )
    # Ensure session_token exists
    if not s.session_token:
        from profiler.session_manager import session_manager

        s.session_token = session_manager.generate_session_token()
        s.save(update_fields=["session_token"])

    factory = APIRequestFactory()
    req = factory.post(
        "/api/v1/profiler/autosave",
        {"session_token": s.session_token, "question_id": "q-smoke", "answer": {"v": 1}},
        format="json",
    )
    force_authenticate(req, user=u)
    resp = autosave_response(req)
    print("STATUS", resp.status_code)
    print("DATA", getattr(resp, "data", None))
    return 0 if resp.status_code == 200 else 10


if __name__ == "__main__":
    raise SystemExit(main())

