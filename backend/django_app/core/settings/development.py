"""
Development settings for core project.
"""
from .base import *

DEBUG = True

# Allow override via environment; fall back to dev defaults
# Leading-dot entries match any subdomain (Django docs): .ngrok-free.dev → *.ngrok-free.dev
_TUNNEL_HOST_SUFFIXES = (
    '.ngrok-free.dev',
    '.ngrok.io',
    '.ngrok.app',
)

if os.environ.get('ALLOWED_HOSTS'):
    ALLOWED_HOSTS = [h.strip() for h in os.environ.get('ALLOWED_HOSTS', '').split(',') if h.strip()]
else:
    ALLOWED_HOSTS = [
        'localhost', '127.0.0.1', '0.0.0.0', 'testserver', 'nginx', 'django'
    ]

ALLOWED_HOSTS = merge_docker_internal_hosts(ALLOWED_HOSTS)

# Paystack/callback webhooks hit the public tunnel URL — must allow Host header (set ALLOW_TUNNEL_HOSTS=false to skip)
if os.environ.get('ALLOW_TUNNEL_HOSTS', 'true').lower() == 'true':
    for _sfx in _TUNNEL_HOST_SUFFIXES:
        if _sfx not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(_sfx)

# Frontend URL for development
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')

# Session settings for OAuth (cross-origin)
SESSION_COOKIE_SAMESITE = 'Lax'  # Allow cross-origin session cookies in development
SESSION_COOKIE_SECURE = False  # Not secure in development (no HTTPS)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_DOMAIN = None  # Allow localhost/127.0.0.1
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = False
CSRF_TRUSTED_ORIGINS = os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',') if os.environ.get('CSRF_TRUSTED_ORIGINS') else [
    'http://localhost:3000', 'http://127.0.0.1:3000'
]

# CORS settings for development
# Allow override via environment variable
if os.environ.get('CORS_ALLOWED_ORIGINS'):
    CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',')
else:
    CORS_ALLOWED_ORIGINS = [
        'http://localhost:3000',
        'http://127.0.0.1:3000',
        'http://localhost:3001',  # In case Next.js runs on different port
        'http://localhost',       # Nginx proxy on port 80
        'http://127.0.0.1',       # Nginx proxy on port 80 via 127.0.0.1
        'http://localhost:80',    # Explicit port 80
        'http://127.0.0.1:80',    # Explicit port 80 via 127.0.0.1
        # Browser preview ports (IDE specific)
        'http://127.0.0.1:51219',
        'http://localhost:51219',
        'http://127.0.0.1:53732',
        'http://localhost:53732',
    ]

# For development, allow all localhost origins with any port
# This helps with browser preview and development tools
if os.environ.get('DEBUG', 'False') == 'True':
    CORS_ALLOW_ALL_ORIGINS = True
    CORS_ALLOW_CREDENTIALS = True
else:
    CORS_ALLOW_CREDENTIALS = True

CORS_ALLOWED_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

CORS_ALLOWED_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# Development-specific settings
INSTALLED_APPS = INSTALLED_APPS + [
    'django_extensions',  # Optional: for enhanced shell, etc.
]

# Use PostgreSQL for development (consistent with production)
# DATABASES already configured in base.py with PostgreSQL
# Override with USE_SQLITE=true environment variable if SQLite is needed for testing
USE_SQLITE_FORCE = os.environ.get('USE_SQLITE', 'false').lower() == 'true'
if USE_SQLITE_FORCE:
    # Use SQLite only if explicitly requested via environment variable
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
# Otherwise, DATABASES from base.py (PostgreSQL) is used
# Or set DATABASE_URL (see production.py) to override
if not USE_SQLITE_FORCE and os.environ.get('DATABASE_URL'):
    import dj_database_url
    DATABASES = {'default': dj_database_url.config(default=os.environ.get('DATABASE_URL'), conn_max_age=600)}

# Use .env MAIL_* (SMTP) when MAIL_HOST is set; otherwise console for local testing
if os.environ.get('MAIL_HOST'):
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Logging configuration for development
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}


