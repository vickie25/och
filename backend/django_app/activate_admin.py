import os
import django
from django.contrib.auth import get_user_model

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

User = get_user_model()
user = User.objects.get(email='admin@ongoza.com')
user.account_status = 'active'
user.email_verified = True
user.is_active = True
user.save()
print("Admin activated successfully")
