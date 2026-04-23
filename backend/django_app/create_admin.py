import os
import django
from django.contrib.auth import get_user_model

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

User = get_user_model()

email = 'admin@ongoza.com'
password = 'AdminPassword123'
username = 'admin'
first_name = 'System'
last_name = 'Administrator'

if not User.objects.filter(email=email).exists():
    User.objects.create_superuser(
        email=email, 
        password=password, 
        username=username,
        first_name=first_name,
        last_name=last_name
    )
    print(f"Superuser created successfully: {email}")
else:
    user = User.objects.get(email=email)
    user.set_password(password)
    user.username = username
    user.first_name = first_name
    user.last_name = last_name
    user.is_superuser = True
    user.is_staff = True
    user.save()
    print(f"Superuser updated successfully: {email}")
