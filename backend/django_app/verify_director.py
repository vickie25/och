import os
import django
from django.contrib.auth import get_user_model

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

User = get_user_model()
email = 'director@example.com'
exists = User.objects.filter(email=email).exists()
print(f"User {email} exists: {exists}")

if exists:
    user = User.objects.get(email=email)
    print(f"Is active: {user.is_active}")
    print(f"Account status: {user.account_status}")
    print(f"Email verified: {user.email_verified}")
    from users.models import UserRole
    roles = UserRole.objects.filter(user=user).values_list('role__name', flat=True)
    print(f"Roles: {list(roles)}")
