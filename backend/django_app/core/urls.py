"""
URL configuration for core project.
"""
import datetime

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from subscriptions.views import paystack_webhook

from core.settings.metrics import metrics_view
from users.views.oidc_views import (
    jwks,
    oauth_authorize,
    oauth_introspect,
    oauth_token,
    oauth_userinfo,
    openid_configuration,
)


@api_view(['GET'])
@authentication_classes([])  # No auth required
@permission_classes([])      # No permissions required
def health_check(request):
    """Public health check endpoint for Docker healthchecks and monitoring.

    This endpoint is unauthenticated and bypasses all permission checks
    to allow Docker healthchecks and load balancers to verify service status.

    Returns:
        JSON response with service status and timestamp.
    """
    return JsonResponse({
        "status": "healthy",
        "service": "django",
        "timestamp": str(datetime.datetime.now()),
        "version": "1.3-nuclear"
    }, status=200)


urlpatterns = [
    path('health/', health_check, name='health-check-root'),
    path('api/v1/health/', health_check, name='health-check-api'),
    path('cyboch-ops-panel/', admin.site.urls),

    # OIDC Discovery Endpoints
    path('.well-known/openid-configuration', openid_configuration, name='openid-configuration'),
    path('.well-known/jwks.json', jwks, name='jwks'),
    path('api/v1/.well-known/jwks.json', jwks, name='jwks-api'),

    # OAuth2/OIDC Endpoints
    path('api/v1/oauth/authorize', oauth_authorize, name='oauth-authorize'),
    path('api/v1/oauth/token', oauth_token, name='oauth-token'),
    path('api/v1/oauth/userinfo', oauth_userinfo, name='oauth-userinfo'),
    path('api/v1/oauth/introspect', oauth_introspect, name='oauth-introspect'),

    # API Documentation (Swagger UI)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Alternative paths for easier access
    path('swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui-alt'),
    path('api-docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='api-docs'),

    # Prometheus Metrics
    path('metrics', metrics_view, name='metrics'),

    # API Versioning
    path('api/v1/', include('api.urls')),

    # Paystack webhook (alternate path; also available at api/v1/subscription/webhooks/paystack)
    path('paystack/webhook/', paystack_webhook, name='paystack-webhook-root'),
    # Frontend compatibility - API without version prefix
    path('api/', include('api.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


