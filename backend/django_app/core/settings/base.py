"""
Django settings for core project - Base configuration.
"""
import logging
import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Sentry for error tracking in production
if not os.environ.get('DEBUG', 'False').lower() == 'true' and os.environ.get('SENTRY_DSN'):
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration

    # Configure Sentry to exclude PII
    sentry_logging = LoggingIntegration(
        level=logging.INFO,
        event_level=logging.ERROR,
    )

    def _sentry_before_send(event, hint):
        """Remove PII from Sentry events."""
        if 'request' in event and 'data' in event['request']:
            # Remove sensitive data from form data
            if 'password' in event['request']['data']:
                event['request']['data']['password'] = '[FILTERED]'
            if 'token' in event['request']['data']:
                event['request']['data']['token'] = '[FILTERED]'
            if 'secret' in event['request']['data']:
                event['request']['data']['secret'] = '[FILTERED]'
        return event

    sentry_sdk.init(
        dsn=os.environ.get('SENTRY_DSN'),
        integrations=[
            DjangoIntegration(
                transaction_style='url',
                middleware_spans=True,
                signals_spans=True,
            ),
            sentry_logging,
        ],
        traces_sample_rate=0.1,
        send_default_pii=False,  # Don't send PII to Sentry
        environment=os.environ.get('DJANGO_SETTINGS_MODULE', 'development'),
        before_send=_sentry_before_send
    )

# Priority: 1) Project root, 2) backend/django_app (legacy), 3) backend (legacy)
# NOTE: In Docker, environment variables are already set - don't override them
PROJECT_ROOT = BASE_DIR.parent.parent  # /home/caleb/kiptoo/och/ongozaCyberHub

# Check if running in Docker (don't override env vars if they're already set properly)
IN_DOCKER = bool(
    os.environ.get("IN_DOCKER")
) or os.path.exists("/.dockerenv")

# Always load local .env files for development
env_path = BASE_DIR / '.env'
if env_path.exists():
    load_dotenv(env_path, override=not IN_DOCKER)
    print(f"Loaded .env from django_app: {env_path}")
else:
    root_env = PROJECT_ROOT / '.env'
    if root_env.exists():
        load_dotenv(root_env, override=not IN_DOCKER)
        print(f"Loaded .env from project root: {root_env}")

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-change-me-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# Institutional reporting defaults (used for ROI/engagement calculations)
# These values are intentionally configurable so institutions can match their internal valuation model.
INSTITUTIONAL_REPORTING = {
    # Assumed value delivered per certified student (used for ROI% proxy)
    # ROI% = ((certified_students * value_per_certified_student) - annual_cost) / annual_cost * 100
    'VALUE_PER_CERTIFIED_STUDENT_KES': int(os.environ.get('VALUE_PER_CERTIFIED_STUDENT_KES', '50000')),
    # Engagement score weights (0-100)
    # engagement_score = w_activity*active_rate + w_progress*avg_progress + w_login*login_score
    'ENGAGEMENT_WEIGHTS': {
        'activity': float(os.environ.get('ENGAGEMENT_WEIGHT_ACTIVITY', '0.4')),
        'progress': float(os.environ.get('ENGAGEMENT_WEIGHT_PROGRESS', '0.4')),
        'login': float(os.environ.get('ENGAGEMENT_WEIGHT_LOGIN', '0.2')),
    },
    # Normalize avg_login_frequency against this ceiling (sessions per student per 30d)
    'LOGIN_FREQUENCY_TARGET_30D': float(os.environ.get('LOGIN_FREQUENCY_TARGET_30D', '8')),
}

# Employer Stream C pricing: convert USD catalog → KES for storage/display.
EMPLOYER_PRICING_USD_TO_KES = float(os.environ.get('EMPLOYER_PRICING_USD_TO_KES', '160.0'))


def merge_docker_internal_hosts(hosts):
    """Extend ALLOWED_HOSTS for Docker internal Host headers and local dev."""
    out = list(hosts)
    if IN_DOCKER:
        for _h in (
            'django',
            'nginx',
            'nextjs',
            'fastapi',
            'host.docker.internal',
        ):
            if _h not in out:
                out.append(_h)
    # Host-run Django (or narrow .env ALLOWED_HOSTS) while DEBUG is on: avoid DisallowedHost
    # for localhost / Docker Desktop gateway when the Next BFF calls http://127.0.0.1:8000 or
    # http://host.docker.internal:8000.
    if os.environ.get('DEBUG', 'False').lower() == 'true':
        for _h in (
            'localhost',
            '127.0.0.1',
            '0.0.0.0',
            'host.docker.internal',
            'testserver',
        ):
            if _h not in out:
                out.append(_h)
    return out


# Honor ALLOWED_HOSTS from the environment (Docker Compose sets this with `django`, `nginx`, etc.).
# Previously this was hardcoded after load_dotenv, which ignored compose-injected hosts and caused
# DisallowedHost (400 HTML) for server-side fetches to http://django:8000 from Next.js.
_allowed_env = (os.environ.get('ALLOWED_HOSTS') or '').strip()
if _allowed_env:
    ALLOWED_HOSTS = [h.strip() for h in _allowed_env.split(',') if h.strip()]
else:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

ALLOWED_HOSTS = merge_docker_internal_hosts(ALLOWED_HOSTS)

# MFA Exemption (Emergency/Local)
MFA_EXEMPT_EMAILS = [
    'admin@ongoza.com',
    'cresdynamics@gmail.com',
    'nelsonochieng516@gmail.com',
    'wilsonndambuki47@gmail.com',
    'kelvinmaina202@gmail.com',
]

# Enable APPEND_SLASH to support both with and without trailing slashes
APPEND_SLASH = True

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',

    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_spectacular',
    'corsheaders',

    # Local apps (order matters - users before organizations)
    'users',
    'organizations',
    'progress',
    'student_dashboard',
    'notifications',
    'mentorship',
    'profiler',
    'foundations',
    'coaching',
    'curriculum',
    'recipes',
    'missions',
    'dashboard',
    'subscriptions',
    'django_apscheduler',       # Periodic jobs (grace period, renewals)
    'mentorship_coordination',
    'mentors',
    'programs',
    'director_dashboard',        # Move before cohorts to fix circular dependency
    'cohorts',                 # Cohort management system
    'finance',                 # Financial management system
    'sponsor_dashboard',
    'sponsors',
    'support',
    'talentscope',
    'marketplace',
    'community',
    'api',
    'shared_schemas',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',  # Disabled for API endpoints
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'users.middleware.consent_middleware.ConsentMiddleware',
    'core.middleware.LoginRateLimitMiddleware',
    'core.middleware.SecurityHeadersMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# Database
USE_SQLITE = os.environ.get('USE_SQLITE', 'False').lower() == 'true'

if USE_SQLITE:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'ongozacyberhub'),
            'USER': os.environ.get('DB_USER', 'postgres'),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432'),
            'OPTIONS': {
                'options': '-c search_path=public'
            },
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    # CommonPasswordValidator has been disabled to allow common passwords.
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files (User uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'users.User'

# Password hashing - Use bcrypt for better security
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.Argon2PasswordHasher',
]

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
]

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER': 'core.exceptions.custom_exception_handler',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.ScopedRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        # anon rate must be high enough for login/SSO + homepage polling during normal usage
        # while still preventing abuse.
        'anon': '1000/hour',
        'user': '5000/day',
        # OAuth endpoints: allow reasonable bursts without locking users out during retries.
        'oauth': '60/min',
    }
}

# JWT Settings
# Use JWT_SECRET_KEY from environment, fallback to SECRET_KEY for backward compatibility
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', SECRET_KEY)
JWT_ALGORITHM = os.environ.get('JWT_ALGORITHM', 'HS256')

# NOTE: Never print secret key material (DJANGO_SECRET_KEY/JWT_SECRET_KEY) to logs.
# If you need to debug key wiring locally, inspect env vars directly.

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),  # 15 minutes as required
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),     # 7 days as required
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'SIGNING_KEY': JWT_SECRET_KEY,  # Use dedicated JWT secret key (rest_framework_simplejwt will use this)
    'ALGORITHM': JWT_ALGORITHM,
    'VERIFYING_KEY': None,  # Use SIGNING_KEY for verification too
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

if DEBUG:
    print("=" * 60)
    print("DJANGO JWT CONFIGURATION (safe summary):")
    print(f"JWT_ALGORITHM: {JWT_ALGORITHM}")
    print(f"Has DJANGO_SECRET_KEY env: {bool(os.environ.get('DJANGO_SECRET_KEY'))}")
    print(f"Has JWT_SECRET_KEY env: {bool(os.environ.get('JWT_SECRET_KEY'))}")
    print(f"Keys match: {JWT_SECRET_KEY == SECRET_KEY}")
    print("=" * 60)

# CORS Settings
CORS_ALLOWED_ORIGINS = [
    "https://cybochengine.africa",
    "https://www.cybochengine.africa",
    "http://cybochengine.africa",
    "http://www.cybochengine.africa",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost",       # Nginx proxy on port 80
    "http://127.0.0.1",       # Nginx proxy on port 80 via 127.0.0.1
    "http://localhost:80",    # Explicit port 80
    "http://127.0.0.1:80",    # Explicit port 80 via 127.0.0.1
    "http://127.0.0.1:51219", # Browser preview port
    "http://localhost:51219", # Alternative browser preview port
    "http://127.0.0.1:53732", # Current browser preview port
    "http://localhost:53732", # Alternative current browser preview port
]

CORS_ALLOW_CREDENTIALS = True

# CSRF Settings for API
CSRF_TRUSTED_ORIGINS = [
    "https://cybochengine.africa",
    "https://www.cybochengine.africa",
    "http://cybochengine.africa",
    "http://www.cybochengine.africa",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost",       # Nginx proxy on port 80
    "http://127.0.0.1",       # Nginx proxy on port 80 via 127.0.0.1
    "http://localhost:80",    # Explicit port 80
    "http://127.0.0.1:80",    # Explicit port 80 via 127.0.0.1
    "http://127.0.0.1:51219", # Browser preview port
    "http://localhost:51219", # Alternative browser preview port
    "http://127.0.0.1:53732", # Current browser preview port
    "http://localhost:53732", # Alternative current browser preview port
]

# Redis Configuration
# Use Redis service name in Docker, localhost for local development
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = os.environ.get('REDIS_PORT', '6379')
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', None)

# Cache Configuration (using Redis if available, fallback to dummy cache)
# Use environment variable to control cache backend
USE_REDIS_CACHE = os.environ.get('USE_REDIS_CACHE', 'false').lower() == 'true'

if USE_REDIS_CACHE:
    try:
        from django_redis.cache import RedisCache
        CACHES = {
            "default": {
                "BACKEND": "django_redis.cache.RedisCache",
                "LOCATION": f"redis://{REDIS_HOST}:{REDIS_PORT}/1",
                "OPTIONS": {
                    "CLIENT_CLASS": "django_redis.client.DefaultClient",
                },
                "KEY_PREFIX": "och",
                "TIMEOUT": 300,  # 5 minutes default timeout
            }
        }
    except (ImportError, ModuleNotFoundError):
        # Fallback to dummy cache if django_redis is not available
        print("WARNING: django_redis not available, using dummy cache backend")
        CACHES = {
            "default": {
                "BACKEND": "django.core.cache.backends.dummy.DummyCache",
            }
        }
else:
    # Use dummy cache for local development (no Redis required)
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.dummy.DummyCache",
        }
    }

# Celery Configuration
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', f'redis://{REDIS_HOST}:{REDIS_PORT}/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', f'redis://{REDIS_HOST}:{REDIS_PORT}/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000

# Celery Beat Schedule (periodic tasks)
CELERY_BEAT_SCHEDULE = {}
try:
    from director_dashboard.celery_config import DIRECTOR_DASHBOARD_BEAT_SCHEDULE

    CELERY_BEAT_SCHEDULE.update(DIRECTOR_DASHBOARD_BEAT_SCHEDULE)
except ImportError:
    pass
try:
    from subscriptions.celery_beat_config import CELERY_BEAT_SCHEDULE as SUBSCRIPTIONS_BEAT_SCHEDULE

    CELERY_BEAT_SCHEDULE.update(SUBSCRIPTIONS_BEAT_SCHEDULE)
except ImportError:
    pass

# Monitoring & Metrics
ENABLE_METRICS = os.environ.get('ENABLE_METRICS', 'False').lower() == 'true'

# Frontend URL for email links and redirects
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')

# Google OAuth 2.0 Configuration
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID') or os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET') or os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET')

# Email: set MAIL_* (or EMAIL_*) for SMTP — see development.py for console fallback when MAIL_HOST is unset.
MAIL_FROM_ADDRESS = os.environ.get('MAIL_FROM_ADDRESS') or os.environ.get('EMAIL_FROM_ADDRESS', '')
MAIL_FROM_NAME = os.environ.get('MAIL_FROM_NAME') or os.environ.get('EMAIL_FROM_NAME', 'Ongoza CyberHub')
if MAIL_FROM_ADDRESS:
    DEFAULT_FROM_EMAIL = f"{MAIL_FROM_NAME} <{MAIL_FROM_ADDRESS}>"
else:
    DEFAULT_FROM_EMAIL = f"{MAIL_FROM_NAME} <noreply@localhost>"

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('MAIL_HOST') or os.environ.get('EMAIL_HOST', '')
EMAIL_PORT = int(os.environ.get('MAIL_PORT') or os.environ.get('EMAIL_PORT', '465'))
EMAIL_HOST_USER = os.environ.get('MAIL_USERNAME') or os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('MAIL_PASSWORD') or os.environ.get('EMAIL_HOST_PASSWORD', '')

# MAIL_ENCRYPTION=tls usually means STARTTLS (port 587); port 465 typically uses SSL
_use_tls = (os.environ.get('MAIL_ENCRYPTION', '').lower() == 'tls')
_use_ssl = (EMAIL_PORT == 465) or (not _use_tls and EMAIL_PORT in (465, 994))
EMAIL_USE_SSL = _use_ssl
EMAIL_USE_TLS = _use_tls and not _use_ssl
EMAIL_TIMEOUT = 30  # 30 seconds timeout to prevent hanging

# Token expiry settings
ACTIVATION_TOKEN_EXPIRY = int(os.environ.get('ACTIVATION_TOKEN_EXPIRY', 24))
PASSWORD_RESET_TOKEN_EXPIRY = int(os.environ.get('PASSWORD_RESET_TOKEN_EXPIRY', 1))

# MFA: TOTP secret encryption at rest (use MFA_TOTP_ENCRYPTION_KEY or fallback to SECRET_KEY)
MFA_TOTP_ENCRYPTION_KEY = os.environ.get('MFA_TOTP_ENCRYPTION_KEY') or SECRET_KEY

# MFA Exemptions (Emergency/Local)
EMERGENCY_MFA_EXEMPT = [
    'admin@ongoza.com',
    'cresdynamics@gmail.com',
    'nelsonochieng516@gmail.com',
    'wilsonndambuki47@gmail.com',
]

_mfa_exempt = os.environ.get('MFA_EXEMPT_EMAILS', '')
MFA_EXEMPT_EMAILS = [email.strip().lower() for email in _mfa_exempt.split(',') if email.strip()]
# Merge with emergency list for local setup
for email in EMERGENCY_MFA_EXEMPT:
    if email.lower() not in MFA_EXEMPT_EMAILS:
        MFA_EXEMPT_EMAILS.append(email.lower())

# SMS: provider (textsms = sms.textsms.co.ke, textbelt = testing, twilio = production)
SMS_PROVIDER = (os.environ.get('SMS_PROVIDER') or 'textsms').lower()
# TextSMS (https://sms.textsms.co.ke)
TEXTSMS_PARTNER_ID = os.environ.get('TEXTSMS_PARTNER_ID', '')
TEXTSMS_API_KEY = os.environ.get('TEXTSMS_API_KEY', '')
TEXTSMS_SENDER_ID = os.environ.get('TEXTSMS_SENDER_ID', '')
# Twilio
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
TWILIO_FROM_NUMBER = os.environ.get('TWILIO_FROM_NUMBER', '')

# AI/LLM Configuration
CHAT_GPT_API_KEY = os.environ.get('CHAT_GPT_API_KEY', os.environ.get('OPENAI_API_KEY', ''))
AI_COACH_MODEL = os.environ.get('AI_COACH_MODEL', 'gpt-4o-mini')

# drf-spectacular (Swagger/OpenAPI) Settings
SPECTACULAR_SETTINGS = {
    'TITLE': 'OCH Cyber Talent Engine API',
    'DESCRIPTION': '''
    Comprehensive API for the OCH Cyber Talent Engine platform.

    This API provides endpoints for:
    - User authentication and management
    - Program, Track, and Cohort management
    - Mentorship coordination
    - Student dashboards and progress tracking
    - Missions and portfolio management
    - Director dashboards and analytics

    **Authentication**: Use JWT Bearer tokens. Obtain tokens via `/api/v1/auth/login` or `/api/v1/auth/login/`
    ''',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SCHEMA_PATH_PREFIX': '/api/v1/',
    'COMPONENT_SPLIT_REQUEST': True,
    'COMPONENT_NO_READ_ONLY_REQUIRED': True,
    'TAGS': [
        {'name': 'Authentication', 'description': 'User authentication and JWT token management'},
        {'name': 'Users', 'description': 'User management and profiles'},
        {'name': 'Programs', 'description': 'Program, Track, and Cohort management'},
        {'name': 'Director Dashboard', 'description': 'Director dashboard and analytics'},
        {'name': 'Mentorship', 'description': 'Mentorship coordination and sessions'},
        {'name': 'Missions', 'description': 'Mission submissions and approvals'},
        {'name': 'Coaching', 'description': 'Coaching and habit tracking'},
        {'name': 'Portfolio', 'description': 'Portfolio management'},
        {'name': 'Organizations', 'description': 'Organization management'},
        {'name': 'Progress', 'description': 'Progress tracking'},
        {'name': 'Subscriptions', 'description': 'Subscription and billing'},
    ],
    'SECURITY': [
        {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
        }
    ],
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'displayOperationId': False,
        'defaultModelsExpandDepth': 1,
        'defaultModelExpandDepth': 1,
        'displayRequestDuration': True,
        'docExpansion': 'list',
        'filter': True,
        'showExtensions': True,
        'showCommonExtensions': True,
        'tryItOutEnabled': True,
    },
    'REDOC_UI_SETTINGS': {
        'hideDownloadButton': False,
        'hideHostname': False,
        'hideLoading': False,
        'nativeScrollbars': False,
        'requiredPropsFirst': True,
        'scrollYOffset': 0,
        'showExtensions': True,
        'sortPropsAlphabetically': True,
        'theme': {
            'colors': {
                'primary': {
                    'main': '#FF6B35',  # OCH Orange
                }
            }
        },
    },
}
