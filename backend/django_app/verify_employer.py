#!/usr/bin/env python
import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

from django.contrib.auth import get_user_model

from users.models import UserRole

User = get_user_model()

try:
    user = User.objects.get(email='employer@och.com')
    print(f'✅ User found: {user.email}')
    print(f'✅ Account Status: {user.account_status}')
    print(f'✅ Email Verified: {user.email_verified}')

    # Check password
    if user.check_password('Ongoza@#1'):
        print('✅ Password is correct')
    else:
        print('❌ Password is incorrect')

    # Check roles
    user_roles = UserRole.objects.filter(user=user).select_related('role')
    role_names = [ur.role.name for ur in user_roles]
    print(f'✅ Roles: {role_names}')

    if 'sponsor_admin' in role_names:
        print('✅ User has correct employer role')
    else:
        print('❌ User missing employer role')

    # Check organization
    if hasattr(user, 'org_id') and user.org_id:
        print(f'✅ Organization: {user.org_id.name} ({user.org_id.org_type})')
    else:
        print('❌ No organization linked')

    print('\n🎯 LOGIN CREDENTIALS:')
    print('Email: employer@och.com')
    print('Password: Ongoza@#1')
    print('Login URL: http://localhost:3000/login/sponsor')

except User.DoesNotExist:
    print('❌ User not found')
except Exception as e:
    print(f'❌ Error: {e}')

