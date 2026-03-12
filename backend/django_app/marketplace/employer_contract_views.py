"""
Employer Contract API Views
Complete API for employer contract management
"""
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Count, Avg, Sum
from datetime import datetime, timedelta, date
from decimal import Decimal

from .employer_contracts import (
    EmployerContract, EmployerContractTier, CandidateRequirement,
    CandidatePresentation, SuccessfulPlacement, ContractPerformanceMetrics,
    ReplacementGuarantee
)
from .employer_contract_services import (
    ContractLifecycleService, CandidateMatchingService, SLAMonitoringService,
    PlacementFeeService, PerformanceTrackingService, ReplacementGuaranteeService
)
from organizations.models import Organization
from .employer_contract_serializers import (
    EmployerContractSerializer, EmployerContractCreateSerializer,
    RetainerTierSerializer, CandidateRequirementSerializer,
    CandidateRequirementCreateSerializer, CandidatePresentationSerializer,
    CandidatePresentationCreateSerializer, SuccessfulPlacementSerializer,
    SuccessfulPlacementCreateSerializer, ContractPerformanceMetricSerializer,
    ReplacementGuaranteeSerializer, ReplacementGuaranteeCreateSerializer,
    ContractSLATrackingSerializer, ContractDashboardSerializer,
    RequirementDashboardSerializer, PerformanceAnalyticsSerializer
)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


# Contract Tier Management
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def list_contract_tiers(request):
    """List all available contract tiers."""
    tiers = EmployerContractTier.objects.filter(is_active=True).order_by('monthly_retainer')
    serializer = RetainerTierSerializer(tiers, many=True)
    return Response({'tiers': serializer.data})


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def create_contract_tier(request):
    """Create new contract tier (admin only)."""
    serializer = RetainerTierSerializer(data=request.data)
    if serializer.is_valid():
        tier = serializer.save()
        return Response(RetainerTierSerializer(tier).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Contract Management
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def list_contracts(request):
    """List employer contracts with filtering and pagination."""
    contracts = EmployerContract.objects.select_related('organization', 'tier').order_by('-created_at')
    
    # Filtering
    status_filter = request.GET.get('status')
    if status_filter:
        contracts = contracts.filter(status=status_filter)
    
    organization_id = request.GET.get('organization_id')
    if organization_id:
        contracts = contracts.filter(organization_id=organization_id)
    
    tier_name = request.GET.get('tier')
    if tier_name:
        contracts = contracts.filter(tier__tier_name=tier_name)
    
    # Pagination
    paginator = StandardResultsSetPagination()
    page = paginator.paginate_queryset(contracts, request)
    
    serializer = EmployerContractSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_contract_proposal(request):
    """Create new contract proposal."""
    try:
        organization_id = request.data.get('organization_id')
        tier_name = request.data.get('tier_name')
        start_date = datetime.strptime(request.data.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(request.data.get('end_date'), '%Y-%m-%d').date()
        
        organization = get_object_or_404(Organization, id=organization_id)
        
        # Extract custom terms
        custom_terms = {
            'has_exclusivity': request.data.get('has_exclusivity', False),
            'exclusivity_duration_months': request.data.get('exclusivity_duration_months'),
            'custom_sla_days': request.data.get('custom_sla_days'),
            'custom_guarantee_days': request.data.get('custom_guarantee_days'),
            'special_requirements': request.data.get('special_requirements', [])
        }
        
        contract = ContractLifecycleService.create_contract_proposal(
            organization=organization,
            tier_name=tier_name,
            start_date=start_date,
            end_date=end_date,
            created_by=request.user,
            **custom_terms
        )
        
        serializer = EmployerContractSerializer(contract)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_contract_details(request, contract_id):
    """Get detailed contract information."""
    contract = get_object_or_404(EmployerContract, id=contract_id)
    
    # Get related data
    recent_requirements = CandidateRequirement.objects.filter(
        contract=contract
    ).order_by('-submitted_at')[:10]
    
    recent_presentations = CandidatePresentation.objects.filter(
        contract=contract
    ).order_by('-presented_at')[:10]
    
    performance_metrics = ContractPerformanceMetrics.objects.filter(
        contract=contract
    ).order_by('-period_end').first()
    
    response_data = {
        'contract': EmployerContractSerializer(contract).data,
        'recent_requirements': CandidateRequirementSerializer(recent_requirements, many=True).data,
        'recent_presentations': CandidatePresentationSerializer(recent_presentations, many=True).data,
        'performance_metrics': ContractPerformanceMetricsSerializer(performance_metrics).data if performance_metrics else None,
        'quarterly_usage': {
            'candidates_used': contract.get_quarterly_candidate_usage(),
            'candidates_limit': contract.candidates_per_quarter,
            'can_access_more': contract.can_access_more_candidates()
        }
    }
    
    return Response(response_data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def transition_contract_status(request, contract_id):
    """Transition contract to new status."""
    try:
        contract = get_object_or_404(EmployerContract, id=contract_id)
        new_status = request.data.get('new_status')
        notes = request.data.get('notes', '')
        
        updated_contract = ContractLifecycleService.transition_contract_status(
            contract=contract,
            new_status=new_status,
            user=request.user,
            notes=notes
        )
        
        serializer = EmployerContractSerializer(updated_contract)
        return Response({
            'message': f'Contract status updated to {new_status}',
            'contract': serializer.data
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# Candidate Requirements Management
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def submit_candidate_requirement(request):
    """Submit new candidate requirement."""
    try:
        contract_id = request.data.get('contract_id')
        contract = get_object_or_404(EmployerContract, id=contract_id)
        
        if not contract.is_active():
            return Response(
                {'error': 'Contract must be active to submit requirements'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not contract.can_access_more_candidates():
            return Response(
                {'error': 'Quarterly candidate limit reached'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        requirement_data = request.data.copy()
        requirement_data['contract'] = contract.id
        requirement_data['created_by'] = request.user.id
        
        serializer = CandidateRequirementCreateSerializer(data=requirement_data)
        if serializer.is_valid():
            requirement = serializer.save()
            
            # Auto-match candidates if requested
            if request.data.get('auto_match', True):
                candidates = CandidateMatchingService.find_matching_candidates(requirement)
                if candidates:
                    presentations = CandidateMatchingService.present_candidates_to_employer(
                        requirement, candidates, request.user
                    )
                    
                    return Response({
                        'requirement': CandidateRequirementSerializer(requirement).data,
                        'candidates_presented': len(presentations),
                        'message': f'Requirement submitted and {len(presentations)} candidates presented'
                    }, status=status.HTTP_201_CREATED)
            
            return Response(CandidateRequirementSerializer(requirement).data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def list_candidate_requirements(request):
    """List candidate requirements with filtering."""
    requirements = CandidateRequirement.objects.select_related('contract').order_by('-submitted_at')
    
    # Filtering
    contract_id = request.GET.get('contract_id')
    if contract_id:
        requirements = requirements.filter(contract_id=contract_id)
    
    status_filter = request.GET.get('status')
    if status_filter:
        requirements = requirements.filter(status=status_filter)
    
    priority_filter = request.GET.get('priority')
    if priority_filter:
        requirements = requirements.filter(priority=priority_filter)
    
    # Pagination
    paginator = StandardResultsSetPagination()
    page = paginator.paginate_queryset(requirements, request)
    
    serializer = CandidateRequirementSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_requirement_candidates(request, requirement_id):
    """Get candidates presented for a requirement."""
    requirement = get_object_or_404(CandidateRequirement, id=requirement_id)
    
    presentations = CandidatePresentation.objects.filter(
        requirement=requirement
    ).select_related('candidate').order_by('-presented_at')
    
    serializer = CandidatePresentationSerializer(presentations, many=True)
    return Response({
        'requirement': CandidateRequirementSerializer(requirement).data,
        'presentations': serializer.data
    })


# Candidate Presentation Management
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def update_candidate_status(request, presentation_id):
    """Update candidate presentation status."""
    try:
        presentation = get_object_or_404(CandidatePresentation, id=presentation_id)
        new_status = request.data.get('status')
        
        if new_status not in dict(CandidatePresentation.STATUS_CHOICES):
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_status = presentation.status
        presentation.status = new_status
        
        # Set status-specific timestamps
        if new_status == 'reviewed':
            presentation.reviewed_at = timezone.now()
        elif new_status == 'shortlisted':
            presentation.shortlisted_at = timezone.now()
        elif new_status == 'interviewed':
            presentation.interviewed_at = timezone.now()
        elif new_status in ['rejected', 'hired']:
            presentation.decision_at = timezone.now()
        
        # Update employer feedback
        if 'employer_rating' in request.data:
            presentation.employer_rating = request.data['employer_rating']
        if 'employer_notes' in request.data:
            presentation.employer_notes = request.data['employer_notes']
        if 'rejection_reason' in request.data:
            presentation.rejection_reason = request.data['rejection_reason']
        
        presentation.save()
        
        # Handle successful hire
        if new_status == 'hired':
            start_date_str = request.data.get('start_date')
            if start_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                salary_offered = request.data.get('salary_offered')
                
                placement = PlacementFeeService.record_successful_placement(
                    presentation=presentation,
                    start_date=start_date,
                    salary_offered=Decimal(str(salary_offered)) if salary_offered else None
                )
                
                return Response({
                    'message': 'Candidate hired successfully',
                    'presentation': CandidatePresentationSerializer(presentation).data,
                    'placement': SuccessfulPlacementSerializer(placement).data
                })
        
        return Response({
            'message': f'Candidate status updated from {old_status} to {new_status}',
            'presentation': CandidatePresentationSerializer(presentation).data
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# Performance and Analytics
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_contract_performance(request, contract_id):
    """Get contract performance metrics."""
    contract = get_object_or_404(EmployerContract, id=contract_id)
    
    # Get date range
    period_start = request.GET.get('period_start')
    period_end = request.GET.get('period_end')
    
    if period_start:
        period_start = datetime.strptime(period_start, '%Y-%m-%d').date()
    else:
        period_start = contract.start_date
    
    if period_end:
        period_end = datetime.strptime(period_end, '%Y-%m-%d').date()
    else:
        period_end = timezone.now().date()
    
    # Calculate metrics
    metrics = PerformanceTrackingService.calculate_performance_metrics(
        contract, period_start, period_end
    )
    
    # Get placement fee summary
    current_month = timezone.now().date().replace(day=1)
    fee_summary = PlacementFeeService.calculate_monthly_placement_fees(contract, current_month)
    
    return Response({
        'performance_metrics': ContractPerformanceMetricSerializer(metrics).data,
        'current_month_fees': {
            'placements_count': fee_summary['placements_count'],
            'total_fees': float(fee_summary['total_fees']),
            'fee_cap': float(fee_summary['fee_cap']),
            'capped_fees': float(fee_summary['capped_fees']),
            'cap_applied': fee_summary['cap_applied']
        },
        'renewal_pricing': ContractLifecycleService.calculate_renewal_pricing(contract)
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_sla_dashboard(request):
    """Get SLA monitoring dashboard."""
    overdue_requirements = SLAMonitoringService.check_overdue_requirements()
    sla_alerts = SLAMonitoringService.send_sla_alerts()
    
    # Get SLA compliance by contract
    active_contracts = EmployerContract.objects.filter(status='active')
    compliance_data = []
    
    for contract in active_contracts:
        compliance_rate = SLAMonitoringService.calculate_sla_compliance_rate(contract)
        if compliance_rate is not None:
            compliance_data.append({
                'contract_id': str(contract.id),
                'contract_number': contract.contract_number,
                'organization': contract.organization.name,
                'compliance_rate': float(compliance_rate),
                'sla_days': contract.time_to_shortlist_days
            })
    
    return Response({
        'overdue_count': overdue_requirements.count(),
        'alerts': sla_alerts,
        'compliance_by_contract': compliance_data,
        'overall_compliance': sum(c['compliance_rate'] for c in compliance_data) / len(compliance_data) if compliance_data else 0
    })


# Replacement Guarantee Management
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def claim_replacement_guarantee(request):
    """Claim replacement guarantee for a placement."""
    try:
        placement_id = request.data.get('placement_id')
        claim_reason = request.data.get('claim_reason')
        candidate_left_date = datetime.strptime(request.data.get('candidate_left_date'), '%Y-%m-%d').date()
        
        placement = get_object_or_404(SuccessfulPlacement, id=placement_id)
        
        guarantee = ReplacementGuaranteeService.claim_replacement_guarantee(
            placement=placement,
            claim_reason=claim_reason,
            candidate_left_date=candidate_left_date
        )
        
        return Response({
            'message': 'Replacement guarantee claimed successfully',
            'guarantee_id': str(guarantee.id),
            'replacement_due_date': guarantee.replacement_due_date,
            'days_employed': guarantee.days_employed
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def list_replacement_guarantees(request):
    """List replacement guarantee claims."""
    guarantees = ReplacementGuarantee.objects.select_related(
        'original_placement__presentation__contract'
    ).order_by('-claimed_at')
    
    # Filtering
    status_filter = request.GET.get('status')
    if status_filter:
        guarantees = guarantees.filter(status=status_filter)
    
    contract_id = request.GET.get('contract_id')
    if contract_id:
        guarantees = guarantees.filter(original_placement__presentation__contract_id=contract_id)
    
    # Check for overdue guarantees
    overdue_guarantees = ReplacementGuaranteeService.check_overdue_guarantees()
    
    guarantee_data = []
    for guarantee in guarantees:
        data = {
            'id': str(guarantee.id),
            'contract_number': guarantee.original_placement.presentation.contract.contract_number,
            'organization': guarantee.original_placement.presentation.contract.organization.name,
            'candidate_email': guarantee.original_placement.presentation.candidate.email,
            'status': guarantee.status,
            'claim_reason': guarantee.claim_reason,
            'days_employed': guarantee.days_employed,
            'replacement_due_date': guarantee.replacement_due_date,
            'is_overdue': guarantee in overdue_guarantees,
            'claimed_at': guarantee.claimed_at
        }
        guarantee_data.append(data)
    
    return Response({
        'guarantees': guarantee_data,
        'overdue_count': overdue_guarantees.count()
    })


# Analytics and Reporting
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_employer_analytics_dashboard(request):
    """Get comprehensive employer analytics dashboard."""
    
    # Contract status distribution
    contract_stats = EmployerContract.objects.values('status').annotate(count=Count('id'))
    
    # Active contracts summary
    active_contracts = EmployerContract.objects.filter(status='active')
    total_active_value = sum(c.get_effective_monthly_retainer() * 12 for c in active_contracts)
    
    # Performance summary
    recent_metrics = ContractPerformanceMetrics.objects.filter(
        period_end__gte=timezone.now().date() - timedelta(days=90)
    )
    
    avg_success_rate = recent_metrics.aggregate(avg=Avg('placement_success_rate'))['avg'] or 0
    avg_sla_compliance = recent_metrics.aggregate(avg=Avg('sla_compliance_rate'))['avg'] or 0
    
    # Monthly placement trends
    current_month = timezone.now().date().replace(day=1)
    monthly_placements = []
    
    for i in range(6):  # Last 6 months
        month_start = current_month - timedelta(days=i*30)
        month_end = month_start + timedelta(days=30)
        
        placements_count = SuccessfulPlacement.objects.filter(
            start_date__range=[month_start, month_end]
        ).count()
        
        monthly_placements.append({
            'month': month_start.strftime('%Y-%m'),
            'placements': placements_count
        })
    
    return Response({
        'contract_distribution': list(contract_stats),
        'active_contracts_count': active_contracts.count(),
        'total_annual_contract_value': float(total_active_value),
        'performance_summary': {
            'avg_placement_success_rate': float(avg_success_rate),
            'avg_sla_compliance_rate': float(avg_sla_compliance),
            'total_placements_ytd': SuccessfulPlacement.objects.filter(
                start_date__year=timezone.now().year
            ).count()
        },
        'monthly_placement_trends': monthly_placements[::-1],  # Reverse for chronological order
        'top_performing_contracts': [
            {
                'contract_number': m.contract.contract_number,
                'organization': m.contract.organization.name,
                'success_rate': float(m.placement_success_rate),
                'placements': m.candidates_hired
            }
            for m in recent_metrics.order_by('-placement_success_rate')[:5]
        ]
    })