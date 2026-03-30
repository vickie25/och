from django.db import migrations
from django.utils.text import slugify


KENYAN_UNIVERSITIES = [
    # Public universities
    {"name": "University of Nairobi", "code": "UON", "country": "KE", "city": "Nairobi"},
    {"name": "Kenyatta University", "code": "KU", "country": "KE", "city": "Nairobi"},
    {"name": "Jomo Kenyatta University of Agriculture and Technology", "code": "JKUAT", "country": "KE", "city": "Juja"},
    {"name": "Egerton University", "code": "EGERTON", "country": "KE", "city": "Njoro"},
    {"name": "Moi University", "code": "MOI", "country": "KE", "city": "Eldoret"},
    {"name": "Maseno University", "code": "MASENO", "country": "KE", "city": "Maseno"},
    {"name": "Technical University of Kenya", "code": "TUK", "country": "KE", "city": "Nairobi"},
    {"name": "Technical University of Mombasa", "code": "TUM", "country": "KE", "city": "Mombasa"},
    {"name": "Dedan Kimathi University of Technology", "code": "DEKUT", "country": "KE", "city": "Nyeri"},
    {"name": "Masinde Muliro University of Science and Technology", "code": "MMUST", "country": "KE", "city": "Kakamega"},
    {"name": "University of Eldoret", "code": "UOE", "country": "KE", "city": "Eldoret"},
    {"name": "Kisii University", "code": "KISII", "country": "KE", "city": "Kisii"},
    {"name": "Chuka University", "code": "CHUKA", "country": "KE", "city": "Chuka"},
    {"name": "Pwani University", "code": "PWANI", "country": "KE", "city": "Kilifi"},
    {"name": "Laikipia University", "code": "LAIKIPIA", "country": "KE", "city": "Nyahururu"},
    {"name": "South Eastern Kenya University", "code": "SEKU", "country": "KE", "city": "Kitui"},
    {"name": "University of Kabianga", "code": "KABIANGA", "country": "KE", "city": "Kericho"},
    {"name": "Karatina University", "code": "KARU", "country": "KE", "city": "Karatina"},
    {"name": "Meru University of Science and Technology", "code": "MUST", "country": "KE", "city": "Meru"},
    {"name": "Machakos University", "code": "MACHAKOS", "country": "KE", "city": "Machakos"},
    {"name": "Kirinyaga University", "code": "KYU", "country": "KE", "city": "Kerugoya"},
    {"name": "Taita Taveta University", "code": "TTU", "country": "KE", "city": "Voi"},
    {"name": "Kaimosi Friends University", "code": "KAFU", "country": "KE", "city": "Kaimosi"},
    {"name": "Murang'a University of Technology", "code": "MUT", "country": "KE", "city": "Murang'a"},
    {"name": "Maasai Mara University", "code": "MMARAU", "country": "KE", "city": "Narok"},
    {"name": "Kibabii University", "code": "KIBU", "country": "KE", "city": "Bungoma"},
    {"name": "Rongo University", "code": "RONGO", "country": "KE", "city": "Rongo"},
    {"name": "Co-operative University of Kenya", "code": "CUK", "country": "KE", "city": "Nairobi"},
    # Private universities (common)
    {"name": "Strathmore University", "code": "STRATH", "country": "KE", "city": "Nairobi"},
    {"name": "United States International University - Africa", "code": "USIU", "country": "KE", "city": "Nairobi"},
    {"name": "Daystar University", "code": "DAYSTAR", "country": "KE", "city": "Athi River"},
    {"name": "Africa Nazarene University", "code": "ANU", "country": "KE", "city": "Ongata Rongai"},
    {"name": "Catholic University of Eastern Africa", "code": "CUEA", "country": "KE", "city": "Nairobi"},
    {"name": "Mount Kenya University", "code": "MKU", "country": "KE", "city": "Thika"},
    {"name": "Zetech University", "code": "ZETECH", "country": "KE", "city": "Ruiru"},
    {"name": "KCA University", "code": "KCA", "country": "KE", "city": "Nairobi"},
    {"name": "Kabarak University", "code": "KABARAK", "country": "KE", "city": "Nakuru"},
    {"name": "Jaramogi Oginga Odinga University of Science and Technology", "code": "JOOUST", "country": "KE", "city": "Bondo"},
]


def seed_kenyan_universities(apps, schema_editor):
    University = apps.get_model('community', 'University')

    for uni in KENYAN_UNIVERSITIES:
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
        ('community', '0003_add_discord_style_community'),
    ]

    operations = [
        migrations.RunPython(seed_kenyan_universities, migrations.RunPython.noop),
    ]
