import os
import sys


def main() -> int:
    sys.path.insert(0, "/app")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.production")
    import django

    django.setup()
    from django.db import connection

    print("DB_VENDOR", connection.vendor)

    from users.models import User

    print("USERS_COUNT", User.objects.count())

    # Phase 4 tables (just basic ORM hits)
    from missions.models import Mission
    from mentorship.models import ChatMessage  # type: ignore
    from progress.models import Progress  # type: ignore

    print("MISSIONS_COUNT", Mission.objects.count())
    print("MENTORSHIP_CHAT_MESSAGES_COUNT", ChatMessage.objects.count())
    print("PROGRESS_COUNT", Progress.objects.count())

    # Phase 5 tables
    from sponsors.models import Sponsor  # type: ignore
    from sponsor_dashboard.models import SponsorDashboardCache  # type: ignore
    from marketplace.models import Employer  # type: ignore

    print("SPONSORS_COUNT", Sponsor.objects.count())
    print("SPONSOR_CACHE_COUNT", SponsorDashboardCache.objects.count())
    print("EMPLOYERS_COUNT", Employer.objects.count())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

