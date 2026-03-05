"""
Sponsor/Employer API Views for OCH SMP Technical Specifications.
Implements all required APIs for sponsor/employer dashboard operations.
"""
import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
from django.shortcuts import get_object_or_404
from django.db import models, transaction
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth
from django.db.utils import OperationalError
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.http import StreamingHttpResponse, HttpResponse
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import generics, status, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from organizations.models import Organization, OrganizationMember, OrganizationEnrollmentInvoice
from users.models import ConsentScope, UserRole, Role
from users.utils.consent_utils import check_consent
from programs.models import Cohort, Enrollment
from .models import (
    Sponsor, SponsorCohort, SponsorStudentCohort, SponsorAnalytics,
    SponsorIntervention, SponsorFinancialTransaction, SponsorCohortBilling,
    RevenueShareTracking, SponsorCohortAssignment, ManualFinanceInvoice,
)
from .serializers import (
    SponsorSerializer, SponsorCohortSerializer, SponsorDashboardSerializer,
    SponsorAnalyticsSerializer
)
from .permissions import IsSponsorUser, IsSponsorAdmin, IsPlatformFinance, check_sponsor_access, is_platform_finance
from . import services as sponsor_services

User = get_user_model()


# =============================================================================
# 🔑 Identity & Organization APIs (prefix /api/v1/auth)
# =============================================================================

@api_view(['POST'])
@permission_classes([])
def sponsor_signup(request):
    """POST /api/v1/auth/signup - Create sponsor/employer admin accounts."""
    data = request.data
    
    required_fields = ['email', 'password', 'first_name', 'last_name', 'organization_name']
    for field in required_fields:
        if field not in data:
            return Response({
                'error': f'{field} is required'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        with transaction.atomic():
            # Create user
            user = User.objects.create_user(
                email=data['email'],
                password=data['password'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                user_type='sponsor_admin'
            )
            
            # Create sponsor organization
            from django.utils.text import slugify
            org_slug = slugify(data['organization_name'])[:50]
            
            sponsor = Sponsor.objects.create(
                slug=org_slug,
                name=data['organization_name'],
                sponsor_type=data.get('sponsor_type', 'corporate'),
                contact_email=data['email'],
                website=data.get('website'),
                country=data.get('country'),
                city=data.get('city'),
                region=data.get('region')
            )
            
            # Create organization record
            org = Organization.objects.create(
                slug=org_slug,
                name=data['organization_name'],
                org_type='sponsor',
                status='active',
                owner=user
            )
            
            # Add user as admin member
            OrganizationMember.objects.create(
                organization=org,
                user=user,
                role='admin'
            )
            
            # Assign sponsor admin role
            sponsor_role, _ = Role.objects.get_or_create(
                name='sponsor_admin',
                defaults={'description': 'Sponsor Administrator'}
            )
            UserRole.objects.create(
                user=user,
                role=sponsor_role,
                scope_type='organization',
                scope_id=str(org.id)
            )
            
            return Response({
                'user_id': str(user.id),
                'sponsor_id': str(sponsor.id),
                'organization_id': str(org.id),
                'message': 'Sponsor account created successfully'
            }, status=status.HTTP_201_CREATED)
            
    except Exception as e:
        return Response({
            'error': f'Failed to create sponsor account: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_sponsor_org(request):
    """POST /api/v1/auth/orgs - Create sponsor/employer organization entity."""
    data = request.data
    
    required_fields = ['name', 'sponsor_type']
    for field in required_fields:
        if field not in data:
            return Response({
                'error': f'{field} is required'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        from django.utils.text import slugify
        org_slug = slugify(data['name'])[:50]
        
        sponsor = Sponsor.objects.create(
            slug=org_slug,
            name=data['name'],
            sponsor_type=data['sponsor_type'],
            contact_email=data.get('contact_email', request.user.email),
            website=data.get('website'),
            country=data.get('country'),
            city=data.get('city'),
            region=data.get('region')
        )
        
        return Response({
            'sponsor_id': str(sponsor.id),
            'slug': sponsor.slug,
            'message': f'Sponsor organization "{sponsor.name}" created successfully'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': f'Failed to create sponsor organization: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsSponsorAdmin])
def add_org_members(request, org_id):
    """POST /api/v1/auth/orgs/{id}/members - Add sponsor admins or staff to the org."""
    data = request.data
    
    required_fields = ['user_emails', 'role']
    for field in required_fields:
        if field not in data:
            return Response({
                'error': f'{field} is required'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        org = get_object_or_404(Organization, id=org_id, org_type='sponsor')
        
        # Verify user has admin access to this org
        if not OrganizationMember.objects.filter(
            organization=org, user=request.user, role='admin'
        ).exists():
            return Response({
                'error': 'Only organization admins can add members'
            }, status=status.HTTP_403_FORBIDDEN)
        
        added_members = []
        for email in data['user_emails']:
            try:
                user = User.objects.get(email=email)
                member, created = OrganizationMember.objects.get_or_create(
                    organization=org,
                    user=user,
                    defaults={'role': data['role']}
                )
                
                if created:
                    added_members.append({
                        'user_id': str(user.id),
                        'email': email,
                        'role': data['role']
                    })
                    
            except User.DoesNotExist:
                continue
        
        return Response({
            'added_members': added_members,
            'message': f'Added {len(added_members)} members to organization'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': f'Failed to add organization members: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsSponsorAdmin])
def assign_sponsor_roles(request, user_id):
    """POST /api/v1/auth/users/{id}/roles - Assign sponsor roles scoped to org/cohort."""
    data = request.data
    
    required_fields = ['role_name', 'scope_type']
    for field in required_fields:
        if field not in data:
            return Response({
                'error': f'{field} is required'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = get_object_or_404(User, id=user_id)
        role = get_object_or_404(Role, name=data['role_name'])
        
        user_role = UserRole.objects.create(
            user=user,
            role=role,
            scope_type=data['scope_type'],
            scope_id=data.get('scope_id')
        )
        
        return Response({
            'user_role_id': str(user_role.id),
            'message': f'Role "{role.name}" assigned to user'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': f'Failed to assign role: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sponsor_profile(request):
    """GET /api/v1/auth/me - Retrieve profile, roles, and consent scopes."""
    user = request.user
    
    # Get user roles
    user_roles = UserRole.objects.filter(user=user).select_related('role')
    roles_data = [{
        'role_name': ur.role.name,
        'scope_type': ur.scope_type,
        'scope_id': ur.scope_id
    } for ur in user_roles]
    
    # Get consent scopes
    consent_scopes = ConsentScope.objects.filter(user=user, granted=True)
    consents_data = [{
        'scope_type': cs.scope_type,
        'granted_at': cs.granted_at.isoformat(),
        'expires_at': cs.expires_at.isoformat() if cs.expires_at else None
    } for cs in consent_scopes]
    
    # Get sponsor organizations: from OrganizationMember and from user.org_id (sponsor users often have org_id set at creation)
    sponsor_orgs = list(
        Organization.objects.filter(
            org_type='sponsor',
            organizationmember__user=user
        ).distinct()
    )
    # Include user's direct org_id if it's a sponsor org and not already in the list
    if getattr(user, 'org_id', None) and hasattr(user.org_id, 'org_type') and user.org_id.org_type == 'sponsor':
        if user.org_id not in sponsor_orgs:
            sponsor_orgs.append(user.org_id)

    orgs_data = []
    for org in sponsor_orgs:
        try:
            member = OrganizationMember.objects.get(organization=org, user=user)
            role = member.role
        except OrganizationMember.DoesNotExist:
            role = 'admin'  # user.org_id implies they own/admin the org
        orgs_data.append({
            'id': str(org.id),
            'name': org.name,
            'slug': org.slug,
            'role': role,
        })
    
    return Response({
        'user_id': str(user.id),
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'user_type': user.user_type,
        'roles': roles_data,
        'consent_scopes': consents_data,
        'sponsor_organizations': orgs_data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_consent_scopes(request):
    """POST /api/v1/auth/consents - Update consent scopes (e.g., employer view of candidate)."""
    data = request.data
    
    required_fields = ['scope_type', 'granted']
    for field in required_fields:
        if field not in data:
            return Response({
                'error': f'{field} is required'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        consent, created = ConsentScope.objects.update_or_create(
            user=request.user,
            scope_type=data['scope_type'],
            defaults={
                'granted': data['granted'],
                'granted_at': timezone.now() if data['granted'] else None,
                'expires_at': None
            }
        )
        
        return Response({
            'consent_id': str(consent.id),
            'scope_type': consent.scope_type,
            'granted': consent.granted,
            'message': f'Consent scope "{consent.scope_type}" updated'
        })
        
    except Exception as e:
        return Response({
            'error': f'Failed to update consent: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# 📚 Program & Cohort Management APIs (prefix /api/v1/programs)
# =============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsSponsorAdmin])
def create_sponsored_cohort(request):
    """POST /api/v1/programs/cohorts - Create sponsored cohorts."""
    data = request.data
    
    required_fields = ['name', 'track_slug', 'sponsor_slug']
    for field in required_fields:
        if field not in data:
            return Response({
                'error': f'{field} is required'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        sponsor = get_object_or_404(Sponsor, slug=data['sponsor_slug'])
        
        cohort = SponsorCohort.objects.create(
            sponsor=sponsor,
            name=data['name'],
            track_slug=data['track_slug'],
            target_size=data.get('target_size', 100),
            start_date=data.get('start_date'),
            expected_graduation_date=data.get('expected_graduation_date'),
            budget_allocated=data.get('budget_allocated', 0),
            placement_goal=data.get('placement_goal', 0)
        )
        
        return Response({
            'cohort_id': str(cohort.id),
            'name': cohort.name,
            'sponsor': sponsor.name,
            'track_slug': cohort.track_slug,
            'message': 'Sponsored cohort created successfully'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': f'Failed to create cohort: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsSponsorAdmin])
def enroll_sponsored_students(request, cohort_id):
    """
    POST /api/v1/programs/cohorts/{id}/enrollments - DISABLED
    Sponsors cannot enroll students. Sponsors can only post jobs and connect with job-ready students.
    """
    return Response({
        'error': 'Sponsors cannot enroll students. Sponsors can only post jobs and connect with job-ready students through the marketplace.',
        'detail': 'Enrollment functionality has been removed for sponsors. Please contact a program director for student enrollment.'
    }, status=status.HTTP_403_FORBIDDEN)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsSponsorUser])
def list_sponsored_students(request, cohort_id):
    """GET /api/v1/programs/cohorts/{id}/enrollments - List sponsored students in a cohort."""
    try:
        cohort = get_object_or_404(SponsorCohort, id=cohort_id)
        
        # Check sponsor access
        sponsor = check_sponsor_access(request.user, cohort.sponsor.slug)
        
        enrollments = SponsorStudentCohort.objects.filter(
            sponsor_cohort=cohort,
            is_active=True
        ).select_related('student')
        
        students_data = []
        for enrollment in enrollments:
            # Check consent for employer view
            has_consent = ConsentScope.objects.filter(
                user=enrollment.student,
                scope_type='employer_share',
                granted=True
            ).exists()
            
            student_data = {
                'enrollment_id': str(enrollment.id),
                'student_id': str(enrollment.student.id),
                'name': f"{enrollment.student.first_name} {enrollment.student.last_name}".strip(),
                'email': enrollment.student.email if has_consent else None,
                'enrollment_status': enrollment.enrollment_status,
                'completion_percentage': float(enrollment.completion_percentage),
                'joined_at': enrollment.joined_at.isoformat(),
                'last_activity_at': enrollment.last_activity_at.isoformat() if enrollment.last_activity_at else None,
                'has_employer_consent': has_consent
            }
            students_data.append(student_data)
        
        return Response({
            'cohort_id': str(cohort.id),
            'cohort_name': cohort.name,
            'students': students_data,
            'total_students': len(students_data)
        })
        
    except Exception as e:
        return Response({
            'error': f'Failed to list students: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsSponsorUser])
def cohort_reports(request, cohort_id):
    """GET /api/v1/programs/cohorts/{id}/reports - View seat utilization, completion rates, and payments."""
    try:
        cohort = get_object_or_404(SponsorCohort, id=cohort_id)
        
        # Check sponsor access
        sponsor = check_sponsor_access(request.user, cohort.sponsor.slug)
        
        # Calculate metrics
        total_enrolled = cohort.student_enrollments.filter(is_active=True).count()
        completed_students = cohort.student_enrollments.filter(enrollment_status='completed').count()
        
        # Seat utilization
        seat_utilization = (total_enrolled / cohort.target_size * 100) if cohort.target_size > 0 else 0
        
        # Completion rate
        completion_rate = (completed_students / total_enrolled * 100) if total_enrolled > 0 else 0
        
        # Financial metrics
        billing_records = SponsorCohortBilling.objects.filter(sponsor_cohort=cohort)
        total_cost = sum(record.total_cost for record in billing_records)
        total_revenue = sum(record.revenue_share_kes for record in billing_records)
        net_cost = total_cost - total_revenue
        
        # Payment status
        paid_invoices = billing_records.filter(payment_status='paid').count()
        pending_invoices = billing_records.filter(payment_status='pending').count()
        overdue_invoices = billing_records.filter(payment_status='overdue').count()
        
        return Response({
            'cohort_id': str(cohort.id),
            'cohort_name': cohort.name,
            'seat_utilization': {
                'target_seats': cohort.target_size,
                'used_seats': total_enrolled,
                'utilization_percentage': round(seat_utilization, 2)
            },
            'completion_metrics': {
                'total_enrolled': total_enrolled,
                'completed_students': completed_students,
                'completion_rate': round(completion_rate, 2),
                'average_completion_percentage': float(cohort.completion_rate)
            },
            'financial_summary': {
                'total_cost_kes': float(total_cost),
                'total_revenue_kes': float(total_revenue),
                'net_cost_kes': float(net_cost),
                'budget_allocated_kes': float(cohort.budget_allocated),
                'budget_utilization_pct': round((float(total_cost) / float(cohort.budget_allocated) * 100), 2) if cohort.budget_allocated > 0 else 0
            },
            'payment_status': {
                'paid_invoices': paid_invoices,
                'pending_invoices': pending_invoices,
                'overdue_invoices': overdue_invoices,
                'total_invoices': billing_records.count()
            }
        })
        
    except Exception as e:
        return Response({
            'error': f'Failed to generate reports: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# 💳 Billing & Finance APIs (prefix /api/v1/billing)
# =============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsSponsorUser])
def billing_catalog(request):
    """GET /api/v1/billing/catalog - View pricing models for seats/programs."""
    return Response({
        'pricing_models': [
            {
                'model_type': 'per_seat_monthly',
                'name': 'Per Seat Monthly',
                'description': 'Monthly fee per active student',
                'price_kes': 20000,
                'currency': 'KES',
                'billing_cycle': 'monthly'
            },
            {
                'model_type': 'mentor_session',
                'name': 'Mentor Session',
                'description': 'Per mentor session fee',
                'price_kes': 7000,
                'currency': 'KES',
                'billing_cycle': 'per_session'
            },
            {
                'model_type': 'lab_usage',
                'name': 'Lab Usage',
                'description': 'Per hour lab usage fee',
                'price_kes': 200,
                'currency': 'KES',
                'billing_cycle': 'per_hour'
            },
            {
                'model_type': 'revenue_share',
                'name': 'Revenue Share',
                'description': 'Revenue share from successful placements',
                'percentage': 3.0,
                'description_detail': '3% of first year salary'
            }
        ]
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsSponsorAdmin])
def create_checkout_session(request):
    """POST /api/v1/billing/checkout/sessions - Pay for sponsored seats."""
    data = request.data
    
    required_fields = ['cohort_id', 'seats_count']
    for field in required_fields:
        if field not in data:
            return Response({
                'error': f'{field} is required'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        cohort = get_object_or_404(SponsorCohort, id=data['cohort_id'])
        
        # Calculate amount (20,000 KES per seat per month)
        seats_count = data['seats_count']
        price_per_seat = 20000  # KES
        total_amount = seats_count * price_per_seat
        
        # Create financial transaction
        transaction = SponsorFinancialTransaction.objects.create(
            sponsor=cohort.sponsor,
            cohort=cohort,
            transaction_type='platform_fee',
            description=f'Payment for {seats_count} seats in {cohort.name}',
            amount=total_amount,
            currency='KES',
            status='pending'
        )
        
        # In a real implementation, integrate with payment gateway
        checkout_session = {
            'session_id': str(transaction.id),
            'amount': total_amount,
            'currency': 'KES',
            'seats_count': seats_count,
            'cohort_name': cohort.name,
            'payment_url': f'/payment/checkout/{transaction.id}',  # Mock URL
            'expires_at': (timezone.now() + timedelta(hours=1)).isoformat()
        }
        
        return Response(checkout_session, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': f'Failed to create checkout session: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _build_invoice_item(b):
    """Build a single invoice dict from a SponsorCohortBilling instance with line items."""
    if not getattr(b, 'sponsor_cohort', None):
        return None
    sc = b.sponsor_cohort
    org = getattr(sc, 'organization', None)
    if not org:
        return None
    # Line items: products, prices, seat allocations (paid, scholarship, sponsored)
    line_items = [
        {'description': 'Platform fee (seats)', 'quantity': int(b.students_active or 0), 'unit_price_kes': 20000, 'amount': float(b.platform_cost or 0)},
        {'description': 'Mentor sessions', 'quantity': int(b.mentor_sessions or 0), 'unit_price_kes': 7000, 'amount': float(b.mentor_cost or 0)},
        {'description': 'Lab usage (hours)', 'quantity': int(b.lab_usage_hours or 0), 'unit_price_kes': 200, 'amount': float(b.lab_cost or 0)},
        {'description': 'Scholarship allocation', 'quantity': 1, 'unit_price_kes': float(b.scholarship_cost or 0), 'amount': float(b.scholarship_cost or 0)},
        {'description': 'Revenue share (hires)', 'quantity': int(b.hires or 0), 'unit_price_kes': 0, 'amount': -float(b.revenue_share_kes or 0)},
    ]
    return {
        'id': str(b.id),
        'cohort_id': str(sc.id),
        'cohort_name': getattr(sc, 'name', ''),
        'sponsor_id': str(org.id),
        'sponsor_name': getattr(org, 'name', ''),
        'billing_month': b.billing_month.isoformat() if getattr(b, 'billing_month', None) else '',
        'net_amount': float(b.net_amount or 0),
        'total_cost': float(b.total_cost or 0),
        'currency': 'KES',
        'payment_status': getattr(b, 'payment_status', 'pending') or 'pending',
        'invoice_generated': getattr(b, 'invoice_generated', False),
        'source': 'system',
        'line_items': line_items,
        'students_active': int(b.students_active or 0),
        'mentor_sessions': int(b.mentor_sessions or 0),
        'lab_usage_hours': int(b.lab_usage_hours or 0),
        'hires': int(b.hires or 0),
        'revenue_share_kes': float(b.revenue_share_kes or 0),
        'created_at': b.created_at.isoformat() if getattr(b, 'created_at', None) else None,
    }


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsSponsorUser])
def sponsor_invoices(request):
    """GET /api/v1/billing/invoices - Invoices for user's sponsor org(s), or all invoices for platform Finance."""
    try:
        from .permissions import _user_sponsor_orgs
        sponsor_orgs = list(_user_sponsor_orgs(request.user))

        # Platform Finance (no sponsor org): return all invoices across sponsors + manual invoices
        if not sponsor_orgs:
            if not is_platform_finance(request.user):
                return Response({
                    'error': 'User is not associated with a sponsor organization'
                }, status=status.HTTP_403_FORBIDDEN)
            billing_qs = SponsorCohortBilling.objects.all().select_related(
                'sponsor_cohort', 'sponsor_cohort__organization'
            ).order_by('-billing_month')
            invoices = [x for b in billing_qs if (x := _build_invoice_item(b)) is not None]
            manual = list(
                ManualFinanceInvoice.objects.all().order_by('-created_at').values(
                    'id', 'sponsor_name', 'amount_kes', 'currency', 'status', 'line_items', 'due_date', 'created_at'
                )
            )
            for m in manual:
                invoices.append({
                    'id': str(m['id']),
                    'cohort_id': '',
                    'cohort_name': '',
                    'sponsor_id': '',
                    'sponsor_name': m['sponsor_name'],
                    'billing_month': m['due_date'].isoformat() if m.get('due_date') else '',
                    'net_amount': float(m['amount_kes'] or 0),
                    'total_cost': float(m['amount_kes'] or 0),
                    'currency': m.get('currency') or 'KES',
                    'payment_status': m.get('status') or 'pending',
                    'invoice_generated': False,
                    'source': 'manual',
                    'line_items': m.get('line_items') or [],
                    'students_active': 0,
                    'mentor_sessions': 0,
                    'lab_usage_hours': 0,
                    'hires': 0,
                    'revenue_share_kes': 0,
                    'created_at': m['created_at'].isoformat() if m.get('created_at') else None,
                })
            # Organization enrollment invoices (director-enrolled students from org)
            try:
                org_inv_qs = OrganizationEnrollmentInvoice.objects.all().select_related(
                    'organization'
                ).order_by('-created_at')
                for oi in org_inv_qs:
                    line_items = []
                    for item in (oi.line_items or []):
                        if isinstance(item, dict):
                            line_items.append({
                                'description': item.get('student_name') or item.get('description') or '',
                                'quantity': 1,
                                'unit_price_kes': float(item.get('amount_kes') or item.get('amount') or 0),
                                'amount': float(item.get('amount_kes') or item.get('amount') or 0),
                            })
                        else:
                            line_items.append({'description': str(item), 'quantity': 1, 'unit_price_kes': 0, 'amount': 0})
                    invoices.append({
                        'id': str(oi.id),
                        'cohort_id': '',
                        'cohort_name': '',
                        'sponsor_id': str(oi.organization_id),
                        'sponsor_name': oi.organization.name if oi.organization else oi.contact_person_name,
                        'billing_month': '',
                        'net_amount': float(oi.total_amount_kes or 0),
                        'total_cost': float(oi.total_amount_kes or 0),
                        'currency': oi.currency or 'KES',
                        'payment_status': oi.status or 'pending',
                        'invoice_generated': False,
                        'source': 'org_enrollment',
                        'line_items': line_items,
                        'payment_link': oi.payment_link,
                        'invoice_number': oi.invoice_number,
                        'contact_email': oi.contact_email,
                        'contact_person_name': oi.contact_person_name,
                        'students_active': len(oi.line_items) if oi.line_items else 0,
                        'mentor_sessions': 0,
                        'lab_usage_hours': 0,
                        'hires': 0,
                        'revenue_share_kes': 0,
                        'created_at': oi.created_at.isoformat() if oi.created_at else None,
                    })
            except Exception as oe:
                logger.warning('OrganizationEnrollmentInvoice not available: %s', oe)
            invoices.sort(key=lambda x: (x.get('created_at') or ''), reverse=True)
            return Response({'invoices': invoices, 'total_invoices': len(invoices)})

        # Sponsor-scoped: only invoices for user's orgs (organizations with org_type='sponsor')
        billing_qs = SponsorCohortBilling.objects.filter(
            sponsor_cohort__organization__in=sponsor_orgs
        ).select_related('sponsor_cohort', 'sponsor_cohort__organization').order_by('-billing_month')
        invoices = [x for b in billing_qs if (x := _build_invoice_item(b)) is not None]
        return Response({'invoices': invoices, 'total_invoices': len(invoices)})
    except OperationalError as e:
        logger.exception('sponsor_invoices database error')
        return Response({
            'error': f'Database error (run migrations?): {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        logger.exception('sponsor_invoices failed')
        return Response({
            'error': f'Failed to retrieve invoices: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsPlatformFinance])
def create_manual_invoice(request):
    """POST /api/v1/billing/invoices/create/ - Create a manual invoice (Finance role)."""
    try:
        client = (request.data.get('client') or '').strip()
        if not client:
            return Response({'error': 'client is required'}, status=status.HTTP_400_BAD_REQUEST)
        amount_kes = request.data.get('amount') or request.data.get('total') or 0
        try:
            amount_kes = float(amount_kes)
        except (TypeError, ValueError):
            amount_kes = 0
        due_date = request.data.get('dueDate') or request.data.get('due_date')
        if due_date:
            from datetime import datetime
            if isinstance(due_date, str):
                try:
                    due_date = datetime.strptime(due_date[:10], '%Y-%m-%d').date()
                except ValueError:
                    due_date = None
            else:
                due_date = None
        items = request.data.get('items') or []
        line_items = []
        for it in items:
            line_items.append({
                'description': it.get('description') or '',
                'quantity': int(it.get('quantity') or 0),
                'rate': float(it.get('rate') or 0),
                'amount': float(it.get('amount') or 0),
            })
        inv = ManualFinanceInvoice.objects.create(
            created_by=request.user,
            sponsor_name=client,
            amount_kes=amount_kes,
            currency='KES',
            status='pending',
            line_items=line_items,
            due_date=due_date,
        )
        return Response({
            'id': str(inv.id),
            'sponsor_name': inv.sponsor_name,
            'amount_kes': float(inv.amount_kes),
            'status': inv.status,
            'created_at': inv.created_at.isoformat(),
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        logger.exception('create_manual_invoice failed')
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _is_director_or_finance(user):
    """True if user is program director, staff, or platform finance."""
    if not user or not user.is_authenticated:
        return False
    if getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False):
        return True
    if is_platform_finance(user):
        return True
    from programs.permissions import _has_any_director_permission
    return _has_any_director_permission(user)


def _paystack_initialize_for_invoice(amount_kes, email, callback_url, metadata=None):
    """Initialize Paystack transaction; returns (authorization_url, reference) or (None, None)."""
    import os
    import random
    import string
    import requests
    secret_key = os.environ.get('PAYSTACK_SECRET_KEY') or os.environ.get('PAYSTACK_SECRET')
    if not secret_key:
        logger.warning('PAYSTACK_SECRET_KEY not configured')
        return None, None
    amount_kobo = int(round(float(amount_kes) * 100))
    if amount_kobo <= 0:
        return None, None
    reference = f"och_org_{int(timezone.now().timestamp())}_{''.join(random.choices(string.ascii_lowercase + string.digits, k=10))}"
    payload = {
        'email': email,
        'amount': amount_kobo,
        'currency': 'KES',
        'reference': reference,
        'metadata': metadata or {},
    }
    if callback_url:
        payload['callback_url'] = callback_url
    try:
        resp = requests.post(
            "https://api.paystack.co/transaction/initialize",
            headers={'Authorization': f'Bearer {secret_key}', 'Content-Type': 'application/json'},
            json=payload,
            timeout=10,
        )
        data = resp.json()
        if data.get('status') and data.get('data', {}).get('authorization_url'):
            return data['data']['authorization_url'], reference
    except Exception as e:
        logger.exception('Paystack initialize for org invoice failed: %s', e)
    return None, None


def _list_org_enrollment_invoices(request):
    """GET list of all organization enrollment invoices (Finance/Director)."""
    qs = (
        OrganizationEnrollmentInvoice.objects.all()
        .select_related('organization')
        .order_by('-created_at')
    )
    results = []
    for inv in qs:
        results.append({
            'id': str(inv.id),
            'invoice_number': inv.invoice_number,
            'organization_id': str(inv.organization.id) if inv.organization else None,
            'organization_name': inv.organization.name if inv.organization else '',
            'contact_person_name': inv.contact_person_name,
            'contact_email': inv.contact_email,
            'total_amount_kes': float(inv.total_amount_kes),
            'currency': inv.currency,
            'status': inv.status,
            'created_at': inv.created_at.isoformat(),
            'sent_at': inv.sent_at.isoformat() if inv.sent_at else None,
        })
    return Response({'results': results, 'count': len(results)})


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def create_org_enrollment_invoice(request):
    """GET = list all org enrollment invoices; POST = create (Director/Finance)."""
    if not _is_director_or_finance(request.user):
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    if request.method == 'GET':
        return _list_org_enrollment_invoices(request)
    try:
        organization_id = request.data.get('organization_id')
        if not organization_id:
            return Response({'error': 'organization_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        org = get_object_or_404(Organization, id=organization_id)
        contact_person_name = (request.data.get('contact_person_name') or '').strip() or getattr(org, 'contact_person_name', None) or org.name
        contact_email = (request.data.get('contact_email') or '').strip() or getattr(org, 'contact_email', None)
        contact_phone = (request.data.get('contact_phone') or '').strip() or getattr(org, 'contact_phone', None) or ''
        if not contact_email:
            return Response({'error': 'contact_email is required'}, status=status.HTTP_400_BAD_REQUEST)
        line_items = request.data.get('line_items') or []
        total_amount_kes = request.data.get('total_amount_kes') or 0
        try:
            total_amount_kes = float(total_amount_kes)
        except (TypeError, ValueError):
            total_amount_kes = 0
        if total_amount_kes <= 0:
            return Response({'error': 'total_amount_kes must be positive'}, status=status.HTTP_400_BAD_REQUEST)
        from django.conf import settings
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        invoice_number = f"ORG-INV-{timezone.now().strftime('%Y%m%d')}-{OrganizationEnrollmentInvoice.objects.count() + 1}"
        with transaction.atomic():
            inv = OrganizationEnrollmentInvoice.objects.create(
                organization=org,
                contact_person_name=contact_person_name,
                contact_email=contact_email,
                contact_phone=contact_phone or None,
                line_items=line_items,
                total_amount_kes=total_amount_kes,
                currency='KES',
                status='pending',
                invoice_number=invoice_number,
                created_by=request.user,
            )
            callback_url = f"{frontend_url.rstrip('/')}/pay/invoice/{inv.id}/return"
            auth_url, ref = _paystack_initialize_for_invoice(
                total_amount_kes, contact_email, callback_url,
                metadata={'invoice_id': str(inv.id), 'type': 'org_enrollment'},
            )
            if auth_url and ref:
                inv.payment_link = auth_url
                inv.paystack_reference = ref
                inv.save(update_fields=['payment_link', 'paystack_reference'])
            inv.sent_at = timezone.now()
            inv.save(update_fields=['sent_at'])
        # Update org contact fields if provided
        if request.data.get('contact_person_name') or request.data.get('contact_email') or request.data.get('contact_phone'):
            Organization.objects.filter(id=org.id).update(
                contact_person_name=contact_person_name or org.contact_person_name,
                contact_email=contact_email or org.contact_email,
                contact_phone=contact_phone or org.contact_phone,
            )
        # Send email
        payment_link = inv.payment_link or f"{frontend_url.rstrip('/')}/pay/invoice/{inv.id}"
        try:
            from services.email_service import EmailService
            email_svc = EmailService()
            html = f"""
            <p>Dear {contact_person_name},</p>
            <p>Thank you for enrolling students from {org.name} with Ongoza CyberHub.</p>
            <p><strong>Invoice #{inv.invoice_number or inv.id}</strong></p>
            <p>Total amount: {inv.currency} {inv.total_amount_kes:,.2f}</p>
            <p>Students / plans included in this invoice:</p>
            <ul>
            """
            for item in (inv.line_items or []):
                name = item.get('student_name') or item.get('description') or '-'
                plan = item.get('plan_name') or ''
                amt = item.get('amount_kes') or item.get('amount') or 0
                html += f"<li>{name} — {plan} — KES {amt:,.2f}</li>"
            html += "</ul>"
            if inv.payment_link:
                html += f'<p><a href="{inv.payment_link}" style="background:#0ea5e9;color:#fff;padding:12px 24px;text-decoration:none;border-radius:8px;">Pay with Paystack</a></p>'
            html += f'<p>Or open this link: {payment_link}</p><p>Best regards,<br/>Ongoza CyberHub</p>'
            email_svc._execute_send(contact_email, f"Invoice #{inv.invoice_number or inv.id} – {org.name}", html, "org_enrollment_invoice")
        except Exception as mail_err:
            logger.warning('Failed to send org enrollment invoice email: %s', mail_err)
        return Response({
            'id': str(inv.id),
            'invoice_number': inv.invoice_number,
            'payment_link': inv.payment_link,
            'total_amount_kes': float(inv.total_amount_kes),
            'status': inv.status,
            'created_at': inv.created_at.isoformat(),
        }, status=status.HTTP_201_CREATED)
    except Organization.DoesNotExist:
        return Response({'error': 'Organization not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.exception('create_org_enrollment_invoice failed')
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([])
def get_org_enrollment_invoice(request, invoice_id):
    """GET /api/v1/billing/org-enrollment-invoices/<id>/ - Get invoice (for payment page, no auth required)."""
    try:
        inv = OrganizationEnrollmentInvoice.objects.select_related('organization').get(id=invoice_id)
    except OrganizationEnrollmentInvoice.DoesNotExist:
        return Response({'error': 'Invoice not found'}, status=status.HTTP_404_NOT_FOUND)
    line_items = []
    for item in (inv.line_items or []):
        line_items.append({
            'student_name': item.get('student_name') or item.get('description'),
            'plan_name': item.get('plan_name'),
            'amount_kes': float(item.get('amount_kes') or item.get('amount') or 0),
        })
    return Response({
        'id': str(inv.id),
        'organization_name': inv.organization.name if inv.organization else '',
        'contact_person_name': inv.contact_person_name,
        'invoice_number': inv.invoice_number,
        'line_items': line_items,
        'total_amount_kes': float(inv.total_amount_kes),
        'currency': inv.currency,
        'status': inv.status,
        'payment_link': inv.payment_link,
        'created_at': inv.created_at.isoformat() if inv.created_at else None,
    })


@api_view(['POST'])
@permission_classes([])
def verify_org_enrollment_invoice_payment(request, invoice_id):
    """POST /api/v1/billing/org-enrollment-invoices/<id>/verify-payment/ - Verify Paystack and mark paid."""
    reference = (request.data.get('reference') or '').strip()
    if not reference:
        return Response({'error': 'reference is required'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        inv = OrganizationEnrollmentInvoice.objects.get(id=invoice_id)
    except OrganizationEnrollmentInvoice.DoesNotExist:
        return Response({'error': 'Invoice not found'}, status=status.HTTP_404_NOT_FOUND)
    if inv.paystack_reference != reference:
        return Response({'error': 'Invalid reference for this invoice'}, status=status.HTTP_400_BAD_REQUEST)
    import os
    import requests
    secret_key = os.environ.get('PAYSTACK_SECRET_KEY') or os.environ.get('PAYSTACK_SECRET')
    if not secret_key:
        return Response({'error': 'Payment provider not configured'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    try:
        resp = requests.get(
            f"https://api.paystack.co/transaction/verify/{reference}",
            headers={'Authorization': f'Bearer {secret_key}'},
            timeout=10,
        )
        data = resp.json()
        if data.get('status') and (data.get('data') or {}).get('status') == 'success':
            inv.status = 'paid'
            inv.save(update_fields=['status', 'updated_at'])
            return Response({'status': 'paid', 'invoice_id': str(inv.id)})
    except Exception as e:
        logger.exception('Verify org invoice payment failed: %s', e)
    return Response({'error': 'Payment verification failed'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH', 'PUT'])
@permission_classes([IsAuthenticated, IsPlatformFinance])
def update_org_enrollment_invoice_status(request, invoice_id):
    """PATCH /api/v1/billing/org-enrollment-invoices/<id>/status/ - Finance: update status (e.g. waived)."""
    try:
        inv = OrganizationEnrollmentInvoice.objects.get(id=invoice_id)
    except OrganizationEnrollmentInvoice.DoesNotExist:
        return Response({'error': 'Invoice not found'}, status=status.HTTP_404_NOT_FOUND)
    new_status = (request.data.get('status') or '').strip().lower()
    if new_status not in ('pending', 'paid', 'waived'):
        return Response({'error': 'status must be one of: pending, paid, waived'}, status=status.HTTP_400_BAD_REQUEST)
    inv.status = new_status
    inv.save(update_fields=['status', 'updated_at'])
    return Response({'id': str(inv.id), 'status': inv.status})


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsPlatformFinance])
def platform_finance_overview(request):
    """GET /api/v1/finance/platform/overview - Aggregated finance across all sponsors (platform/internal Finance)."""
    try:
        agg = SponsorCohortBilling.objects.aggregate(
            total_platform_cost=Sum('total_cost'),
            total_net=Sum('net_amount'),
            total_revenue_share=Sum('revenue_share_kes'),
            total_hires=Sum('hires'),
        )
        total_platform_cost = float(agg.get('total_platform_cost') or 0)
        total_revenue_share = float(agg.get('total_revenue_share') or 0)
        total_hires = int(agg.get('total_hires') or 0)
        total_net = float(agg.get('total_net') or 0)
        total_value_created = total_platform_cost  # proxy for display
        total_roi = (total_value_created / total_platform_cost) if total_platform_cost else 0

        cohorts = []
        for b in SponsorCohortBilling.objects.select_related(
            'sponsor_cohort', 'sponsor_cohort__organization'
        ).order_by('-billing_month')[:50]:
            sc = getattr(b, 'sponsor_cohort', None)
            org = getattr(sc, 'organization', None) if sc else None
            if not sc or not org:
                continue
            cohorts.append({
                'cohort_id': str(sc.id),
                'name': getattr(sc, 'name', ''),
                'sponsor_name': getattr(org, 'name', ''),
                'billed_amount': float(b.net_amount or 0),
                'revenue_share': float(b.revenue_share_kes or 0),
                'payment_status': getattr(b, 'payment_status', 'pending') or 'pending',
                'hires': int(b.hires or 0),
                'billing_month': b.billing_month.isoformat() if getattr(b, 'billing_month', None) else '',
            })

        return Response({
            'total_roi': round(total_roi, 2),
            'total_value_created': total_value_created,
            'total_platform_cost': total_platform_cost,
            'total_revenue_share': total_revenue_share,
            'total_hires': total_hires,
            'cohorts': cohorts,
            'revenue_forecast_q2': 0,
        })
    except OperationalError as e:
        logger.exception('platform_finance_overview database error')
        return Response(
            {'error': f'Database error (run migrations?): {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    except Exception as e:
        logger.exception('platform_finance_overview failed')
        return Response(
            {'error': f'Failed to retrieve platform finance overview: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsPlatformFinance])
def revenue_dashboard(request):
    """
    GET /api/v1/finance/platform/revenue-dashboard/
    Returns subscription plans bought, student outsourced, revenue breakdown, time-series, and distribution.
    All data from DB (no dummy data).
    """
    try:
        from subscriptions.models import SubscriptionPlan, UserSubscription, PaymentTransaction

        # 1) Subscription plans bought (count of active paid subscriptions)
        subscription_plans_bought = UserSubscription.objects.filter(status='active').count()

        # 2) Student outsourced (total hires from sponsor cohort billing)
        hires_agg = SponsorCohortBilling.objects.aggregate(total=Sum('hires'))
        student_outsourced = int(hires_agg.get('total') or 0)

        # 3) Revenue breakdown by plan (name, users, revenue in USD)
        plans = SubscriptionPlan.objects.all().order_by('price_monthly')
        breakdown = []
        total_sub_revenue_usd = 0
        for p in plans:
            user_count = UserSubscription.objects.filter(plan=p, status='active').count()
            price = float(p.price_monthly or 0)
            revenue_usd = price * user_count
            total_sub_revenue_usd += revenue_usd
            breakdown.append({
                'id': str(p.id),
                'name': p.name,
                'tier': p.tier,
                'users': user_count,
                'revenue_usd': round(revenue_usd, 2),
                'price_monthly_usd': price,
            })
        for b in breakdown:
            b['percent'] = round((b['revenue_usd'] / total_sub_revenue_usd * 100), 1) if total_sub_revenue_usd else 0

        # 4) Revenue time-series: subscription by month (completed payments), placement by month (billing)
        sub_qs = PaymentTransaction.objects.filter(status='completed').annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(total_usd=Sum('amount')).order_by('month')
        sub_by_month = list(sub_qs)

        # Placement revenue by month (billing)
        placement_by_month = list(
            SponsorCohortBilling.objects.annotate(month=TruncMonth('billing_month'))
            .values('month')
            .annotate(total_kes=Sum('revenue_share_kes'), hires=Sum('hires'))
            .order_by('month')
        )

        # 5) Global distribution: subscribers by country (User.country)
        from users.models import User
        dist_qs = User.objects.filter(
            subscription__status='active'
        ).values('country').annotate(count=Count('id')).order_by('-count')[:50]
        distribution = [{'country': (x['country'] or 'XX').upper(), 'count': x['count']} for x in dist_qs]

        # Available funds / next payout: use total subscription revenue as proxy; next payout in N days from env or default
        total_placement_kes = float(
            SponsorCohortBilling.objects.aggregate(s=Sum('revenue_share_kes')).get('s') or 0
        )

        return Response({
            'subscription_plans_bought': subscription_plans_bought,
            'student_outsourced': student_outsourced,
            'revenue_breakdown': breakdown,
            'total_subscription_revenue_usd': round(total_sub_revenue_usd, 2),
            'revenue_by_month_subscription': [
                {'month': (x['month'].isoformat()[:7] if x.get('month') else ''), 'total_usd': float(x.get('total_usd') or 0)}
                for x in sub_by_month
            ],
            'revenue_by_month_placement': [
                {
                    'month': (x['month'].isoformat()[:7] if x.get('month') else ''),
                    'total_kes': float(x.get('total_kes') or 0),
                    'hires': int(x.get('hires') or 0),
                }
                for x in placement_by_month
            ],
            'distribution': distribution,
            'total_placement_revenue_kes': round(total_placement_kes, 2),
        })
    except Exception as e:
        logger.exception('revenue_dashboard failed')
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsPlatformFinance])
def finance_roi_report_pdf(request):
    """
    GET /api/v1/finance/platform/roi-report/pdf/
    Returns a clean PDF report (ReportLab) with finance ROI and revenue breakdown. All data from DB.
    """
    try:
        from io import BytesIO
        from django.http import HttpResponse as HttpResp

        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib import colors
        except ImportError:
            return Response(
                {'error': 'PDF generation requires reportlab. Install: pip install reportlab'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # Reuse same revenue data as platform overview + subscription totals
        agg = SponsorCohortBilling.objects.aggregate(
            total_platform_cost=Sum('total_cost'),
            total_revenue_share=Sum('revenue_share_kes'),
            total_hires=Sum('hires'),
        )
        total_platform_cost = float(agg.get('total_platform_cost') or 0)
        total_revenue_share = float(agg.get('total_revenue_share') or 0)
        total_hires = int(agg.get('total_hires') or 0)
        total_roi = (total_platform_cost / total_revenue_share) if total_revenue_share else 0

        # Subscription revenue (from subscription plans + active users)
        subscription_kes = 0
        active_users = 0
        try:
            from subscriptions.models import SubscriptionPlan, UserSubscription
            plans = SubscriptionPlan.objects.all()
            for p in plans:
                cnt = UserSubscription.objects.filter(plan=p, status='active').count()
                active_users += cnt
                subscription_kes += float(p.price_monthly or 0) * cnt
            # Backend stores USD; convert to KES
            import os
            usd_to_kes = float(os.environ.get('USD_TO_KES_RATE') or os.environ.get('NEXT_PUBLIC_USD_TO_KES') or 130)
            subscription_kes = round(subscription_kes * usd_to_kes, 2)
        except Exception:
            subscription_kes = 0

        total_revenue = total_platform_cost + subscription_kes

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            topMargin=0.6 * inch,
            bottomMargin=0.6 * inch,
            leftMargin=0.6 * inch,
            rightMargin=0.6 * inch,
        )
        story = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontSize=22,
            textColor=colors.HexColor('#0f172a'),
            spaceAfter=6,
            alignment=1,
        )
        subtitle_style = ParagraphStyle(
            'ReportSubtitle',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#64748b'),
            spaceAfter=24,
            alignment=1,
        )

        story.append(Paragraph('Ongoza CyberHub', title_style))
        story.append(Paragraph('Finance ROI Report', subtitle_style))
        story.append(Spacer(1, 0.15 * inch))

        # Key metrics table
        metrics_data = [
            ['Metric', 'Value'],
            ['Total Revenue (KES)', f'{total_revenue:,.2f}'],
            ['ROI Multiple', f'{total_roi:.2f}x'],
            ['Active Users', str(active_users)],
            ['Placements (Hires)', str(total_hires)],
        ]
        metrics_table = Table(metrics_data, colWidths=[3.2 * inch, 2.8 * inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0ea5e9')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#0f172a')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ]))
        story.append(metrics_table)
        story.append(Spacer(1, 0.25 * inch))

        # Revenue breakdown
        story.append(Paragraph('<b>Revenue Breakdown</b>', styles['Heading3']))
        story.append(Spacer(1, 0.1 * inch))
        breakdown_data = [
            ['Source', 'Amount (KES)'],
            ['Cohort / Platform', f'{total_platform_cost:,.2f}'],
            ['Placement fees', f'{total_revenue_share:,.2f}'],
            ['Subscriptions', f'{subscription_kes:,.2f}'],
            ['Total', f'{total_revenue:,.2f}'],
        ]
        breakdown_table = Table(breakdown_data, colWidths=[3.2 * inch, 2.8 * inch])
        breakdown_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ]))
        story.append(breakdown_table)
        story.append(Spacer(1, 0.4 * inch))

        from datetime import datetime
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#64748b'),
            alignment=1,
        )
        story.append(Paragraph(
            f'Generated on {datetime.now().strftime("%B %d, %Y at %I:%M %p")}',
            footer_style,
        ))
        story.append(Paragraph('Ongoza CyberHub — Finance', footer_style))

        doc.build(story)
        buffer.seek(0)

        response = HttpResp(buffer.read(), content_type='application/pdf')
        filename = f'och-finance-roi-report-{datetime.now().strftime("%Y%m%d")}.pdf'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except Exception as e:
        logger.exception('finance_roi_report_pdf failed')
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsSponsorUser])
def sponsor_entitlements(request):
    """GET /api/v1/billing/entitlements - Check seat entitlements (user role + org, SponsorCohortAssignment)."""
    try:
        # Sponsors are defined by user role and org_type='sponsor', not a separate sponsors table
        sponsor_org = Organization.objects.filter(
            org_type='sponsor',
            organizationmember__user=request.user
        ).first()

        if not sponsor_org:
            return Response({
                'error': 'User is not associated with a sponsor organization'
            }, status=status.HTTP_403_FORBIDDEN)

        # Entitlements from SponsorCohortAssignment (user -> cohort, seat_allocation) + enrollments (org, seat_type=sponsored)
        assignments = SponsorCohortAssignment.objects.filter(
            sponsor_uuid_id=request.user
        ).select_related('cohort_id', 'cohort_id__track').order_by('-created_at')

        entitlements_data = []
        for assignment in assignments:
            cohort = assignment.cohort_id
            seats_allocated = assignment.seat_allocation
            seats_used = Enrollment.objects.filter(
                cohort=cohort,
                org=sponsor_org,
                seat_type='sponsored'
            ).count()
            seats_available = max(0, seats_allocated - seats_used)
            utilization = round((seats_used / seats_allocated * 100), 2) if seats_allocated > 0 else 0
            track_slug = cohort.track.key if getattr(cohort, 'track', None) else getattr(cohort, 'track_id', '') or ''

            entitlements_data.append({
                'cohort_id': str(cohort.id),
                'cohort_name': cohort.name,
                'seats_allocated': seats_allocated,
                'seats_used': seats_used,
                'seats_available': seats_available,
                'utilization_percentage': utilization,
                'track_slug': track_slug,
                'status': getattr(cohort, 'status', 'active'),
            })

        return Response({
            'entitlements': entitlements_data,
            'total_cohorts': len(entitlements_data)
        })

    except Exception as e:
        return Response({
            'error': f'Failed to retrieve entitlements: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# 📢 Notifications & Automation APIs (prefix /api/v1/notifications)
# =============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsSponsorAdmin])
def send_sponsor_message(request):
    """POST /api/v1/notifications/send - Send sponsor/employer messages to students."""
    data = request.data
    
    required_fields = ['recipient_type', 'message', 'subject']
    for field in required_fields:
        if field not in data:
            return Response({
                'error': f'{field} is required'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Get sponsor from user
        sponsor_orgs = Organization.objects.filter(
            org_type='sponsor',
            organizationmember__user=request.user
        ).first()
        
        if not sponsor_orgs:
            return Response({
                'error': 'User is not associated with a sponsor organization'
            }, status=status.HTTP_403_FORBIDDEN)
        
        sponsor = Sponsor.objects.filter(slug=sponsor_orgs.slug).first()
        if not sponsor:
            return Response({
                'error': 'Sponsor organization not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get recipients based on type
        recipients = []
        if data['recipient_type'] == 'cohort' and 'cohort_id' in data:
            cohort = get_object_or_404(SponsorCohort, id=data['cohort_id'], sponsor=sponsor)
            enrollments = SponsorStudentCohort.objects.filter(
                sponsor_cohort=cohort,
                is_active=True
            ).select_related('student')
            recipients = [enrollment.student for enrollment in enrollments]
            
        elif data['recipient_type'] == 'all_students':
            # All sponsored students
            enrollments = SponsorStudentCohort.objects.filter(
                sponsor_cohort__sponsor=sponsor,
                is_active=True
            ).select_related('student')
            recipients = [enrollment.student for enrollment in enrollments]
            
        elif data['recipient_type'] == 'specific_students' and 'student_ids' in data:
            recipients = User.objects.filter(id__in=data['student_ids'])
        
        # TODO: Integrate with actual notification service
        # For now, just log the message
        message_log = {
            'sender': request.user.email,
            'sponsor': sponsor.name,
            'subject': data['subject'],
            'message': data['message'],
            'recipient_count': len(recipients),
            'sent_at': timezone.now().isoformat()
        }
        
        return Response({
            'message_id': f"msg_{timezone.now().timestamp()}",
            'recipients_count': len(recipients),
            'status': 'sent',
            'message': 'Message sent successfully to sponsored students'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': f'Failed to send message: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# 🔒 Consent & Privacy APIs (prefix /api/v1/privacy)
# =============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsSponsorUser])
def sponsor_consents(request):
    """GET /api/v1/privacy/consents/my - View sponsor-related consents granted by students."""
    try:
        # Get sponsor from user
        sponsor_orgs = Organization.objects.filter(
            org_type='sponsor',
            organizationmember__user=request.user
        ).first()
        
        if not sponsor_orgs:
            return Response({
                'error': 'User is not associated with a sponsor organization'
            }, status=status.HTTP_403_FORBIDDEN)
        
        sponsor = Sponsor.objects.filter(slug=sponsor_orgs.slug).first()
        if not sponsor:
            return Response({'consents': []})
        
        # Get sponsored students
        sponsored_students = User.objects.filter(
            sponsor_enrollments__sponsor_cohort__sponsor=sponsor,
            sponsor_enrollments__is_active=True
        ).distinct()
        
        consents_data = []
        for student in sponsored_students:
            # Get consent scopes for this student
            consent_scopes = ConsentScope.objects.filter(
                user=student,
                granted=True
            )
            
            student_consents = {
                'student_id': str(student.id),
                'student_name': f"{student.first_name} {student.last_name}".strip(),
                'student_email': student.email,
                'consents': []
            }
            
            for consent in consent_scopes:
                consent_data = {
                    'scope_type': consent.scope_type,
                    'granted': consent.granted,
                    'granted_at': consent.granted_at.isoformat() if consent.granted_at else None,
                    'expires_at': consent.expires_at.isoformat() if consent.expires_at else None
                }
                student_consents['consents'].append(consent_data)
            
            consents_data.append(student_consents)
        
        return Response({
            'consents': consents_data,
            'total_students': len(consents_data)
        })
        
    except Exception as e:
        return Response({
            'error': f'Failed to retrieve consents: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsSponsorUser])
def check_student_consent(request):
    """POST /api/v1/privacy/check - Real-time consent check (e.g., employer viewing candidate profile)."""
    data = request.data
    
    required_fields = ['student_id', 'scope_type']
    for field in required_fields:
        if field not in data:
            return Response({
                'error': f'{field} is required'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        student = get_object_or_404(User, id=data['student_id'])
        
        # Check if student is sponsored by this user's organization
        sponsor_orgs = Organization.objects.filter(
            org_type='sponsor',
            organizationmember__user=request.user
        ).first()
        
        if not sponsor_orgs:
            return Response({
                'error': 'User is not associated with a sponsor organization'
            }, status=status.HTTP_403_FORBIDDEN)
        
        sponsor = Sponsor.objects.filter(slug=sponsor_orgs.slug).first()
        if not sponsor:
            return Response({
                'has_consent': False,
                'reason': 'Sponsor organization not found'
            })
        
        # Check if student is sponsored
        is_sponsored = SponsorStudentCohort.objects.filter(
            sponsor_cohort__sponsor=sponsor,
            student=student,
            is_active=True
        ).exists()
        
        if not is_sponsored:
            return Response({
                'has_consent': False,
                'reason': 'Student is not sponsored by your organization'
            })
        
        # Check consent
        has_consent = ConsentScope.objects.filter(
            user=student,
            scope_type=data['scope_type'],
            granted=True
        ).exists()
        
        return Response({
            'student_id': str(student.id),
            'scope_type': data['scope_type'],
            'has_consent': has_consent,
            'checked_at': timezone.now().isoformat()
        })
        
    except Exception as e:
        return Response({
            'error': f'Failed to check consent: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# 📊 Analytics & Reporting APIs (prefix /api/v1/analytics)
# =============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsSponsorUser])
def sponsor_metrics(request, metric_key):
    """GET /api/v1/analytics/metrics/{key} - Sponsor dashboards (seat utilization, completion)."""
    try:
        # Get sponsor from user
        sponsor_orgs = Organization.objects.filter(
            org_type='sponsor',
            organizationmember__user=request.user
        ).first()
        
        if not sponsor_orgs:
            return Response({
                'error': 'User is not associated with a sponsor organization'
            }, status=status.HTTP_403_FORBIDDEN)
        
        sponsor = Sponsor.objects.filter(slug=sponsor_orgs.slug).first()
        if not sponsor:
            return Response({
                'error': 'Sponsor organization not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get or create analytics cache
        analytics, created = SponsorAnalytics.objects.get_or_create(
            sponsor=sponsor,
            defaults={
                'total_students': 0,
                'active_students': 0,
                'completion_rate': 0,
                'placement_rate': 0,
                'roi_multiplier': 1.0
            }
        )
        
        # Define available metrics
        metrics_map = {
            'seat_utilization': {
                'total_seats': sum(cohort.target_size for cohort in sponsor.cohorts.filter(is_active=True)),
                'used_seats': analytics.active_students,
                'utilization_percentage': (analytics.active_students / sum(cohort.target_size for cohort in sponsor.cohorts.filter(is_active=True)) * 100) if sum(cohort.target_size for cohort in sponsor.cohorts.filter(is_active=True)) > 0 else 0
            },
            'completion_rates': {
                'overall_completion_rate': float(analytics.completion_rate),
                'total_students': analytics.total_students,
                'active_students': analytics.active_students
            },
            'placement_metrics': {
                'placement_rate': float(analytics.placement_rate),
                'total_hires': analytics.total_hires,
                'hires_last_30d': analytics.hires_last_30d,
                'avg_salary_kes': analytics.avg_salary_kes
            },
            'roi_analysis': {
                'roi_multiplier': float(analytics.roi_multiplier),
                'avg_readiness_score': float(analytics.avg_readiness_score)
            }
        }
        
        if metric_key not in metrics_map:
            return Response({
                'error': f'Unknown metric key: {metric_key}',
                'available_metrics': list(metrics_map.keys())
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'metric_key': metric_key,
            'sponsor_id': str(sponsor.id),
            'sponsor_name': sponsor.name,
            'data': metrics_map[metric_key],
            'last_updated': analytics.last_updated.isoformat()
        })
        
    except Exception as e:
        return Response({
            'error': f'Failed to retrieve metrics: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsSponsorUser])
def export_dashboard_pdf(request, dashboard_id):
    """GET /api/v1/analytics/dashboards/{id}/pdf - Export sponsor-specific analytics reports."""
    try:
        # Get sponsor from user
        sponsor_orgs = Organization.objects.filter(
            org_type='sponsor',
            organizationmember__user=request.user
        ).first()
        
        if not sponsor_orgs:
            return Response({
                'error': 'User is not associated with a sponsor organization'
            }, status=status.HTTP_403_FORBIDDEN)
        
        sponsor = Sponsor.objects.filter(slug=sponsor_orgs.slug).first()
        if not sponsor:
            return Response({
                'error': 'Sponsor organization not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # TODO: Implement actual PDF generation
        # For now, return a mock response
        
        pdf_data = {
            'dashboard_id': dashboard_id,
            'sponsor_name': sponsor.name,
            'generated_at': timezone.now().isoformat(),
            'pdf_url': f'/api/v1/analytics/dashboards/{dashboard_id}/pdf/download',
            'expires_at': (timezone.now() + timedelta(hours=24)).isoformat(),
            'file_size_bytes': 1024000,  # Mock 1MB
            'status': 'ready'
        }
        
        return Response(pdf_data)
        
    except Exception as e:
        return Response({
            'error': f'Failed to export dashboard: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_sponsors_to_cohort(request):
    """POST /api/v1/programs/cohorts/assign-sponsors - Assign sponsors to cohorts"""
    data = request.data
    
    required_fields = ['cohort_id', 'sponsor_assignments']
    for field in required_fields:
        if field not in data:
            return Response({
                'error': f'{field} is required'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        from programs.models import Cohort
        from .models import SponsorCohortAssignment
        
        cohort = get_object_or_404(Cohort, id=data['cohort_id'])
        
        created_assignments = []
        for assignment_data in data['sponsor_assignments']:
            sponsor_uuid = assignment_data.get('sponsor_uuid_id')
            seat_allocation = assignment_data.get('seat_allocation', 1)
            role = assignment_data.get('role', 'funding')
            
            if not sponsor_uuid:
                continue
                
            try:
                sponsor_user = User.objects.get(uuid_id=sponsor_uuid)
                
                assignment, created = SponsorCohortAssignment.objects.get_or_create(
                    sponsor=sponsor_user,
                    cohort=cohort,
                    defaults={
                        'role': role,
                        'seat_allocation': seat_allocation,
                        'start_date': assignment_data.get('start_date'),
                        'end_date': assignment_data.get('end_date'),
                        'funding_agreement_id': assignment_data.get('funding_agreement_id')
                    }
                )
                
                if created:
                    created_assignments.append({
                        'assignment_id': str(assignment.id),
                        'sponsor_email': sponsor_user.email,
                        'cohort_name': cohort.name,
                        'seat_allocation': assignment.seat_allocation,
                        'role': assignment.role
                    })
                    
            except User.DoesNotExist:
                continue
        
        return Response({
            'message': f'Successfully assigned {len(created_assignments)} sponsor(s) to cohort',
            'assignments': created_assignments,
            'cohort_id': str(cohort.id),
            'cohort_name': cohort.name
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': f'Failed to assign sponsors: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_sponsor_assignments(request):
    """GET /api/v1/programs/cohorts/assignments - Get all sponsor assignments"""
    try:
        from .models import SponsorCohortAssignment
        
        assignments = SponsorCohortAssignment.objects.all().select_related('sponsor', 'cohort')
        
        assignments_data = []
        for assignment in assignments:
            assignment_data = {
                'id': str(assignment.id),
                'sponsor_uuid_id': str(assignment.sponsor.uuid_id),
                'sponsor_name': f"{assignment.sponsor.first_name} {assignment.sponsor.last_name}".strip(),
                'sponsor_email': assignment.sponsor.email,
                'cohort_id': str(assignment.cohort.id),
                'cohort_name': assignment.cohort.name,
                'role': assignment.role,
                'seat_allocation': assignment.seat_allocation,
                'start_date': assignment.start_date.isoformat() if assignment.start_date else None,
                'end_date': assignment.end_date.isoformat() if assignment.end_date else None,
                'funding_agreement_id': assignment.funding_agreement_id,
                'created_at': assignment.created_at.isoformat(),
                'updated_at': assignment.updated_at.isoformat()
            }
            assignments_data.append(assignment_data)
        
        return Response({
            'assignments': assignments_data,
            'total_assignments': len(assignments_data)
        })
        
    except Exception as e:
        return Response({
            'error': f'Failed to retrieve assignments: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)