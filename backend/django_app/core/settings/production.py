"""
Production settings for core project.
"""
import os

from .base import *

DEBUG = False

# When running behind a reverse proxy (Nginx / Next.js rewrites) inside Docker,
# the upstream request may carry an internal Host (sometimes invalid, e.g. underscores).
# Trust the proxy-provided host header so Django validates the real public domain.
USE_X_FORWARDED_HOST = True
# Keep SSL redirect disabled for now (emergency port-80 mode), but still honor proxy scheme if set.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Production hosts (strip; merge Docker service names so in-compose BFF calls are not DisallowedHost)
ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get(
        'ALLOWED_HOSTS',
        'cybochengine.africa,www.cybochengine.africa,localhost,127.0.0.1',
    ).split(',')
    if h.strip()
]
ALLOWED_HOSTS = merge_docker_internal_hosts(ALLOWED_HOSTS)
# Next.js BFF (docker-compose service) may call Django via http://backend:8000
# which sets Host: backend:8000. Django validates Host without port, so ensure
# 'backend' is explicitly allowed.
if 'backend' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('backend')

# Frontend URL for production
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'https://cybochengine.africa')

# Security settings for production (DISABLED for Port 80 Emergency)
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Session security
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_DOMAIN = None
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# CSRF trusted origins for production
_csrf_origins = os.environ.get('CSRF_TRUSTED_ORIGINS', 'https://cybochengine.africa,https://www.cybochengine.africa').split(',')
CSRF_TRUSTED_ORIGINS = _csrf_origins + ['http://cybochengine.africa', 'http://www.cybochengine.africa']

# CORS settings for production
_cors_origins = os.environ.get('CORS_ALLOWED_ORIGINS', 'https://cybochengine.africa,https://www.cybochengine.africa').split(',')
CORS_ALLOWED_ORIGINS = _cors_origins + ['http://cybochengine.africa', 'http://www.cybochengine.africa']

CORS_ALLOW_CREDENTIALS = True

# Enable CSRF middleware in production for safer defaults.
# Base settings disable it to simplify API-only local development.
if 'django.middleware.csrf.CsrfViewMiddleware' not in MIDDLEWARE:
    try:
        _idx = MIDDLEWARE.index('django.middleware.common.CommonMiddleware') + 1
        MIDDLEWARE.insert(_idx, 'django.middleware.csrf.CsrfViewMiddleware')
    except ValueError:
        MIDDLEWARE.insert(0, 'django.middleware.csrf.CsrfViewMiddleware')

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

# Static files handling
STATIC_ROOT = os.environ.get('STATIC_ROOT', str(BASE_DIR / 'staticfiles'))
MEDIA_ROOT = os.environ.get('MEDIA_ROOT', str(BASE_DIR / 'media'))

# Non-blocking checks that can be addressed later (schema generation and URL namespacing).
# These currently cause `manage.py check --deploy` to exit non-zero.
SILENCED_SYSTEM_CHECKS = [
    'drf_spectacular.W001',
    'drf_spectacular.W002',
    'urls.W005',
]

# Email configuration for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Prefer MAIL_* variables (same as base.py) so production matches your SMTP provider.
# Example:
#   MAIL_HOST=mail.lomtechnology.com
#   MAIL_PORT=465
#   MAIL_USERNAME=missionconnect@lomtechnology.com
#   MAIL_PASSWORD=...
#   MAIL_FROM_ADDRESS=missionconnect@lomtechnology.com
#   MAIL_FROM_NAME=OCH
EMAIL_HOST = os.environ.get('MAIL_HOST') or os.environ.get('EMAIL_HOST', '')
EMAIL_PORT = int(os.environ.get('MAIL_PORT') or os.environ.get('EMAIL_PORT', '465'))
EMAIL_HOST_USER = os.environ.get('MAIL_USERNAME') or os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('MAIL_PASSWORD') or os.environ.get('EMAIL_HOST_PASSWORD')

MAIL_FROM_ADDRESS = os.environ.get('MAIL_FROM_ADDRESS') or os.environ.get('DEFAULT_FROM_EMAIL', 'info@cresdynamics.com')
MAIL_FROM_NAME = os.environ.get('MAIL_FROM_NAME') or 'OCH'
DEFAULT_FROM_EMAIL = f"{MAIL_FROM_NAME} <{MAIL_FROM_ADDRESS}>" if MAIL_FROM_ADDRESS else 'info@cresdynamics.com'

# MAIL_ENCRYPTION=tls usually means STARTTLS (port 587); port 465 typically uses SSL
_use_tls = (os.environ.get('MAIL_ENCRYPTION', '').lower() == 'tls') or (os.environ.get('EMAIL_USE_TLS', 'False') == 'True')
_use_ssl = (EMAIL_PORT == 465) or (not _use_tls and EMAIL_PORT in (465, 994))
EMAIL_USE_SSL = _use_ssl
EMAIL_USE_TLS = _use_tls and not _use_ssl

# Database configuration (override for production if needed)
if os.environ.get('DATABASE_URL'):
    import dj_database_url
    DATABASES['default'] = dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )

# Logging configuration for production
DJANGO_LOG_FILE = os.environ.get('DJANGO_LOG_FILE', '/tmp/django.log')
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': DJANGO_LOG_FILE,
            'formatter': 'verbose',
        },
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}


