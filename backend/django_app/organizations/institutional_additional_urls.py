"""
Additional URL patterns for institutional billing features
"""
from django.urls import path
from . import institutional_additional_views

# Add these to the existing institutional_urls.py
additional_urlpatterns = [
    # Bulk Import
    path('students/bulk-import/', institutional_additional_views.bulk_import_students, name='bulk-import-students'),
    
    # SSO Integration
    path('contracts/<uuid:contract_id>/sso/', institutional_additional_views.setup_sso_integration, name='setup-sso'),
    
    # Track Assignments
    path('contracts/<uuid:contract_id>/assign-tracks/', institutional_additional_views.assign_mandatory_tracks, name='assign-tracks'),
    
    # Academic Calendar
    path('academic-calendar-options/', institutional_additional_views.academic_calendar_options, name='academic-calendar-options'),
    
    # Enhanced Dashboard Analytics
    path('contracts/<uuid:contract_id>/dashboard-analytics/', institutional_additional_views.institutional_dashboard_analytics, name='dashboard-analytics'),
]