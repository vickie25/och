import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()
from django.core.cache import cache
cache.clear()
print('Cache explicitly cleared!')
