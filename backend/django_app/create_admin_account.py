import os
import sys

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')

import django
django.setup()

from django.db import connection
from django.db.utils import ProgrammingError
from django.contrib.auth import get_user_model
import traceback
import re
import time

User = get_user_model()

def fix_all_users_columns():
    email = "admin@example.com"
    username = "SystemAdmin"
    password = "Admin_Password123!"

    print("Attempting to create admin account and auto-patching missing columns...")
    max_retries = 30
    retries = 0

    while retries < max_retries:
        retries += 1
        try:
            user = User.objects.filter(email=email).first()
            if not user:
                try:
                    user = User.objects.create_superuser(
                        email=email,
                        username=username,
                        password=password
                    )
                except TypeError:
                    user = User.objects.create_superuser(
                        email=email,
                        password=password
                    )
            else:
                user.set_password(password)
                user.is_staff = True
                user.is_superuser = True
                
            if hasattr(user, 'role'):
                user.role = 'ADMIN'
            
            user.save()
            print("\n✅ Admin account successfully created/updated!")
            print(f"📧 Email: {email}")
            print(f"🔑 Password: {password}")
            return
            
        except ProgrammingError as e:
            error_text = str(e)
            match = re.search(r'column users\.(\w+) does not exist', error_text)
            if match:
                missing_column = match.group(1)
                print(f"Auto-fixing missing column: {missing_column}")
                with connection.cursor() as cursor:
                    # Let's peek at the model to find the correct type
                    try:
                        field = User._meta.get_field(missing_column)
                        internal_type = field.get_internal_type()
                        
                        col_type = "VARCHAR(255)"
                        if internal_type == 'BooleanField':
                            col_type = "BOOLEAN DEFAULT False"
                        elif internal_type == 'UUIDField':
                            col_type = "UUID"
                        elif internal_type in ('IntegerField', 'BigAutoField', 'AutoField', 'ForeignKey'):
                            if "uuid" in missing_column:
                                col_type = "UUID"
                            else:
                                col_type = "INTEGER"
                        elif internal_type == 'DateTimeField':
                            col_type = "TIMESTAMP WITH TIME ZONE"
                        elif internal_type == 'JSONField':
                            col_type = "JSONB DEFAULT '{}'::jsonb"
                            
                        cursor.execute(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {missing_column} {col_type};")
                    except Exception as meta_ex:
                        print(f"  Fallback field type used due to: {meta_ex}")
                        cursor.execute(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {missing_column} VARCHAR(255);")
            else:
                print("Could not auto-fix schema error:")
                print(error_text)
                return
        except Exception as e:
            traceback.print_exc()
            return

if __name__ == "__main__":
    fix_all_users_columns()
