from django.db import migrations
from django.utils.text import slugify


# Expand the initial KE seed list to the expected full set used by the UI.
# Idempotent: uses update_or_create keyed by `code`.
MORE_KENYAN_UNIVERSITIES = [
    # Public / chartered (commonly expected in "all KE universities" lists)
    {"name": "Multimedia University of Kenya", "code": "MMU", "country": "KE", "city": "Nairobi"},
    {"name": "University of Embu", "code": "EMBU", "country": "KE", "city": "Embu"},
    {"name": "Tharaka University", "code": "THARAKA", "country": "KE", "city": "Tharaka Nithi"},
    {"name": "Garissa University", "code": "GARISSA", "country": "KE", "city": "Garissa"},
    # Private (highly common / requested)
    {"name": "St. Paul's University", "code": "SPU", "country": "KE", "city": "Limuru"},
    {"name": "Pan Africa Christian University", "code": "PACU", "country": "KE", "city": "Nairobi"},
    {"name": "Kiriri Women's University of Science and Technology", "code": "KWUST", "country": "KE", "city": "Nairobi"},
    {"name": "Riara University", "code": "RIARA", "country": "KE", "city": "Nairobi"},
]


def seed_more_kenyan_universities(apps, schema_editor):
    University = apps.get_model("community", "University")

    for uni in MORE_KENYAN_UNIVERSITIES:
        name = uni["name"].strip()
        code = uni["code"].strip().upper()
        slug = slugify(name)[:100]

        University.objects.update_or_create(
            code=code,
            defaults={
                "name": name,
                "slug": slug,
                "short_name": code,
                "country": uni.get("country", "KE"),
                "city": uni.get("city"),
                "is_active": True,
                "timezone": "Africa/Nairobi",
            },
        )


class Migration(migrations.Migration):
    dependencies = [
        ("community", "0004_seed_kenyan_universities"),
    ]

    operations = [
        migrations.RunPython(seed_more_kenyan_universities, migrations.RunPython.noop),
    ]

