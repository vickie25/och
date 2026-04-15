"""
Additional URL patterns for institutional billing features
"""
from django.urls import path

from . import institutional_additional_views
from . import scim_views

# Add these to the existing institutional_urls.py
additional_urlpatterns = [
    # Onboarding (public)
    path('institution-onboarding-preview/', institutional_additional_views.institution_onboarding_preview, name='institution-onboarding-preview'),
    path('institution-onboarding-complete/', institutional_additional_views.institution_onboarding_complete, name='institution-onboarding-complete'),

    # Bulk Import
    path('students/bulk-import/', institutional_additional_views.bulk_import_students, name='bulk-import-students'),

    # SSO Integration
    path('contracts/<uuid:contract_id>/sso/', institutional_additional_views.setup_sso_integration, name='setup-sso'),

    # Track Assignments
    path('contracts/<uuid:contract_id>/assign-tracks/', institutional_additional_views.assign_mandatory_tracks, name='assign-tracks'),

    # Academic Calendar
    path('academic-calendar-options/', institutional_additional_views.academic_calendar_options, name='academic-calendar-options'),
    path('contracts/<uuid:contract_id>/academic-calendar/', institutional_additional_views.set_academic_calendar, name='set-academic-calendar'),

    # Enhanced Dashboard Analytics
    path('contracts/<uuid:contract_id>/dashboard-analytics/', institutional_additional_views.institutional_dashboard_analytics, name='dashboard-analytics'),

    # SCIM 2.0 Provisioning (contract-scoped)
    path('contracts/<uuid:contract_id>/scim-token/', institutional_additional_views.scim_token_admin, name='scim-token-admin'),
    path('contracts/<uuid:contract_id>/scim/v2/ServiceProviderConfig', scim_views.scim_service_provider_config, name='scim-service-provider-config'),
    path('contracts/<uuid:contract_id>/scim/v2/Users', scim_views.scim_users, name='scim-users'),
    path('contracts/<uuid:contract_id>/scim/v2/Users/<str:external_id>', scim_views.scim_user_detail, name='scim-user-detail'),
]
