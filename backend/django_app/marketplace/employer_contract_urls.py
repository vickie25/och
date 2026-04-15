from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import employer_contract_views

# Create router for viewsets if we convert to viewsets later
router = DefaultRouter()

urlpatterns = [
    # Contract Tier Management
    path('tiers/', employer_contract_views.list_contract_tiers, name='list-contract-tiers'),
    path('tiers/create/', employer_contract_views.create_contract_tier, name='create-contract-tier'),

    # Contract Management
    path('contracts/', employer_contract_views.list_contracts, name='list-contracts'),
    path('contracts/create/', employer_contract_views.create_contract_proposal, name='create-contract'),
    path('contracts/<uuid:contract_id>/', employer_contract_views.get_contract_details, name='contract-details'),
    path('contracts/<uuid:contract_id>/exclusivity/', employer_contract_views.update_contract_exclusivity, name='contract-exclusivity'),
    path('contracts/<uuid:contract_id>/transition/', employer_contract_views.transition_contract_status, name='transition-contract'),
    path('contracts/<uuid:contract_id>/performance/', employer_contract_views.get_contract_performance, name='contract-performance'),

    # Candidate Requirements
    path('requirements/', employer_contract_views.list_candidate_requirements, name='list-requirements'),
    path('requirements/submit/', employer_contract_views.submit_candidate_requirement, name='submit-requirement'),
    path('requirements/<uuid:requirement_id>/candidates/', employer_contract_views.get_requirement_candidates, name='requirement-candidates'),
    path('requirements/<uuid:requirement_id>/recommendations/', employer_contract_views.get_requirement_recommendations, name='requirement-recommendations'),
    path('waitlist/', employer_contract_views.list_waitlisted_candidates, name='waitlist'),

    # Candidate Presentations
    path('presentations/<uuid:presentation_id>/status/', employer_contract_views.update_candidate_status, name='update-candidate-status'),

    # Analytics and Dashboards
    path('analytics/dashboard/', employer_contract_views.get_employer_analytics_dashboard, name='analytics-dashboard'),
    path('analytics/sla/', employer_contract_views.get_sla_dashboard, name='sla-dashboard'),

    # Replacement Guarantees
    path('guarantees/', employer_contract_views.list_replacement_guarantees, name='list-guarantees'),
    path('guarantees/claim/', employer_contract_views.claim_replacement_guarantee, name='claim-guarantee'),

    # Include router URLs
    path('', include(router.urls)),
]
