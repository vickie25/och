import os
import django
from django.contrib.auth import get_user_model
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

from users.models import Role, UserRole

User = get_user_model()
email = 'director@example.com'
password = 'director123'

# Create or update user
user, created = User.objects.get_or_create(
    email=email,
    defaults={
        'username': 'director',
        'first_name': 'Director',
        'last_name': 'User',
        'is_active': True,
        'account_status': 'active',
        'email_verified': True,
        'email_verified_at': timezone.now(),
        'activated_at': timezone.now(),
        'mfa_enabled': False
    }
)

if created:
    user.set_password(password)
    user.save()
    print(f"User {email} created.")
else:
    user.set_password(password)
    user.is_active = True
    user.account_status = 'active'
    user.email_verified = True
    user.save()
    print(f"User {email} updated.")

# Assign role
role_name = 'program_director'
role = Role.objects.get(name=role_name)
UserRole.objects.get_or_create(
    user=user,
    role=role,
    scope='global',
    defaults={'is_active': True}
)

print(f"Role {role_name} assigned to {email}.")
