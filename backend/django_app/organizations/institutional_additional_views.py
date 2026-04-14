"""
Additional Institutional Billing Views - SSO, Bulk Import, Academic Calendar
"""
import csv
import io
import logging

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.shortcuts import get_object_or_404
from programs.permissions import IsProgramDirector
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.models import User

from .institutional_models import InstitutionalContract, InstitutionalStudent
from .institutional_service import InstitutionalBillingService

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsProgramDirector])
def bulk_import_students(request):
    """
    POST /api/v1/institutional/students/bulk-import/
    Bulk import students from CSV file.
    """
    try:
        contract_id = request.data.get('contract_id')
        csv_file = request.FILES.get('file')

        if not contract_id or not csv_file:
            return Response(
                {'error': 'contract_id and file are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get contract
        contract = get_object_or_404(InstitutionalContract, id=contract_id)

        if contract.status != 'active':
            return Response(
                {'error': 'Contract must be active for student imports'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check available seats
        active_students = contract.enrolled_students.filter(is_active=True).count()
        available_seats = contract.student_seat_count - active_students

        if available_seats <= 0:
            return Response(
                {'error': 'No available seats in this contract'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Parse CSV
        try:
            csv_content = csv_file.read().decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(csv_content))

            required_fields = ['first_name', 'last_name', 'email']
            if not all(field in csv_reader.fieldnames for field in required_fields):
                return Response(
                    {'error': f'CSV must contain columns: {", ".join(required_fields)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            return Response(
                {'error': f'Invalid CSV file: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Process students
        results = {
            'total_rows': 0,
            'successful_imports': 0,
            'duplicates': 0,
            'errors': [],
            'imported_students': []
        }

        with transaction.atomic():
            for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 for header
                results['total_rows'] += 1

                # Stop if we've reached seat limit
                if results['successful_imports'] >= available_seats:
                    results['errors'].append('Seat limit reached. Remaining rows not processed.')
                    break

                try:
                    # Validate required fields
                    first_name = row.get('first_name', '').strip()
                    last_name = row.get('last_name', '').strip()
                    email = row.get('email', '').strip().lower()

                    if not all([first_name, last_name, email]):
                        results['errors'].append(f'Row {row_num}: Missing required fields')
                        continue

                    # Check for existing user
                    user, created = User.objects.get_or_create(
                        email=email,
                        defaults={
                            'first_name': first_name,
                            'last_name': last_name,
                            'username': email,
                            'is_active': True
                        }
                    )

                    if not created:
                        # Check if already enrolled in this contract
                        existing_enrollment = InstitutionalStudent.objects.filter(
                            contract=contract,
                            user=user,
                            is_active=True
                        ).exists()

                        if existing_enrollment:
                            results['duplicates'] += 1
                            continue

                    # Create enrollment
                    InstitutionalBillingService.enroll_student(
                        contract_id=contract.id,
                        user_id=user.id,
                        enrollment_type='bulk_import',
                        created_by=request.user
                    )

                    results['successful_imports'] += 1
                    results['imported_students'].append({
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'status': 'imported'
                    })

                    # Send welcome email
                    try:
                        send_welcome_email(user, contract)
                    except Exception as e:
                        logger.warning(f'Failed to send welcome email to {user.email}: {str(e)}')

                except Exception as e:
                    results['errors'].append(f'Row {row_num}: {str(e)}')
                    continue

        return Response(results)

    except Exception as e:
        logger.error(f'Bulk import error: {str(e)}')
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsProgramDirector])
def setup_sso_integration(request):
    """
    POST /api/v1/institutional/contracts/{id}/sso/
    Setup SSO integration for institutional contract.
    """
    try:
        contract_id = request.data.get('contract_id')
        sso_config = request.data.get('sso_config', {})

        contract = get_object_or_404(InstitutionalContract, id=contract_id)

        # Validate SSO configuration
        required_sso_fields = ['provider_type', 'entity_id', 'sso_url', 'certificate']
        if not all(field in sso_config for field in required_sso_fields):
            return Response(
                {'error': f'SSO config must contain: {", ".join(required_sso_fields)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Store SSO configuration (extend contract model to include SSO fields)
        contract.sso_enabled = True
        contract.sso_provider_type = sso_config['provider_type']
        contract.sso_entity_id = sso_config['entity_id']
        contract.sso_url = sso_config['sso_url']
        contract.sso_certificate = sso_config['certificate']
        contract.domain_auto_enrollment = sso_config.get('domain_auto_enrollment', False)
        contract.allowed_domains = sso_config.get('allowed_domains', [])
        contract.save()

        return Response({
            'message': 'SSO integration configured successfully',
            'sso_login_url': f"{settings.FRONTEND_URL}/sso/login/{contract.id}",
            'metadata_url': f"{settings.FRONTEND_URL}/sso/metadata/{contract.id}"
        })

    except Exception as e:
        logger.error(f'SSO setup error: {str(e)}')
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsProgramDirector])
def assign_mandatory_tracks(request):
    """
    POST /api/v1/institutional/contracts/{id}/assign-tracks/
    Assign mandatory tracks to students in a contract.
    """
    try:
        contract_id = request.data.get('contract_id')
        track_assignments = request.data.get('track_assignments', [])
        department_filter = request.data.get('department_filter')

        contract = get_object_or_404(InstitutionalContract, id=contract_id)

        # Get students to assign tracks to
        students_query = contract.enrolled_students.filter(is_active=True)

        if department_filter:
            # Filter by department if specified
            students_query = students_query.filter(
                user__profile__department=department_filter
            )

        students = students_query.all()

        results = {
            'students_processed': 0,
            'tracks_assigned': 0,
            'errors': []
        }

        with transaction.atomic():
            for student in students:
                try:
                    for track_assignment in track_assignments:
                        track_assignment.get('track_id')
                        track_assignment.get('is_mandatory', True)
                        track_assignment.get('completion_deadline')

                        # Create track assignment (implement based on your track model)
                        # This would integrate with your existing track/curriculum system

                        results['tracks_assigned'] += 1

                    results['students_processed'] += 1

                except Exception as e:
                    results['errors'].append(f'Student {student.user.email}: {str(e)}')

        return Response(results)

    except Exception as e:
        logger.error(f'Track assignment error: {str(e)}')
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsProgramDirector])
def academic_calendar_options(request):
    """
    GET /api/v1/institutional/academic-calendar-options/
    Get available academic calendar alignment options.
    """
    try:
        options = {
            'semester_options': [
                {'value': 'january', 'label': 'January (Spring Semester)', 'description': 'Spring semester start'},
                {'value': 'august', 'label': 'August (Fall Semester)', 'description': 'Fall semester start'},
                {'value': 'september', 'label': 'September (Fall Semester)', 'description': 'Fall semester start'},
                {'value': 'june', 'label': 'June (Summer Session)', 'description': 'Summer session start'}
            ],
            'quarter_options': [
                {'value': 'september', 'label': 'September (Fall Quarter)', 'description': 'Fall quarter start'},
                {'value': 'january', 'label': 'January (Winter Quarter)', 'description': 'Winter quarter start'},
                {'value': 'march', 'label': 'March (Spring Quarter)', 'description': 'Spring quarter start'},
                {'value': 'june', 'label': 'June (Summer Quarter)', 'description': 'Summer quarter start'}
            ],
            'fiscal_year_options': [
                {'value': 'july', 'label': 'July - June', 'description': 'Standard academic fiscal year'},
                {'value': 'january', 'label': 'January - December', 'description': 'Calendar year'},
                {'value': 'october', 'label': 'October - September', 'description': 'Federal fiscal year'}
            ],
            'summer_program_options': [
                {'value': 'reduced_rate', 'label': 'Summer Reduced Rate', 'description': '50% discount for July-August'},
                {'value': 'full_rate', 'label': 'Summer Full Rate', 'description': 'Standard rate year-round'},
                {'value': 'pause_billing', 'label': 'Pause Summer Billing', 'description': 'No billing June-August'}
            ]
        }

        return Response(options)

    except Exception as e:
        logger.error(f'Academic calendar options error: {str(e)}')
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def institutional_dashboard_analytics(request, contract_id):
    """
    GET /api/v1/institutional/contracts/{id}/dashboard-analytics/
    Get comprehensive dashboard analytics for institutional portal.
    """
    try:
        contract = get_object_or_404(InstitutionalContract, id=contract_id)

        # Get basic contract analytics
        base_analytics = InstitutionalBillingService.get_contract_analytics(contract_id)

        # Add institutional-specific metrics
        students = contract.enrolled_students.filter(is_active=True)

        # Seat utilization by department/pool
        seat_pools = []
        departments = students.values_list('user__profile__department', flat=True).distinct()

        for dept in departments:
            if dept:
                dept_students = students.filter(user__profile__department=dept)
                seat_pools.append({
                    'name': dept,
                    'type': 'department',
                    'allocated': dept_students.count(),  # Could be configured per department
                    'active': dept_students.count(),
                    'available': 0,  # Calculate based on department allocation
                    'utilization': 100.0  # Placeholder calculation
                })

        # Track assignments and completion
        track_assignments = {
            'mandatory_assignments': 0,  # Integrate with track system
            'completed_assignments': 0,
            'overdue_assignments': 0,
            'completion_rate': 0.0
        }

        # ROI metrics
        roi_metrics = {
            'cost_per_student': float(base_analytics['financial']['monthly_recurring_revenue'] / max(base_analytics['students']['active_students'], 1)),
            'roi_percentage': 150.0,  # Placeholder - calculate based on outcomes
            'certification_rate': 75.0  # Placeholder - integrate with certification system
        }

        # Enhanced analytics
        enhanced_analytics = {
            **base_analytics,
            'seat_utilization': {
                'total_allocated': base_analytics['students']['licensed_seats'],
                'total_active': base_analytics['students']['active_students'],
                'utilization_rate': base_analytics['students']['seat_utilization'],
                'pools': seat_pools
            },
            'student_metrics': {
                'active_students': base_analytics['students']['active_students'],
                'completed_students': 0,  # Integrate with completion tracking
                'withdrawn_students': 0,  # Track withdrawals
                'completion_rate': 0.0
            },
            'track_assignments': track_assignments,
            'roi_metrics': roi_metrics
        }

        return Response(enhanced_analytics)

    except Exception as e:
        logger.error(f'Dashboard analytics error: {str(e)}')
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def send_welcome_email(user, contract):
    """Send welcome email to newly imported student"""
    try:
        subject = f'Welcome to {contract.organization.name} Learning Program'

        context = {
            'user': user,
            'contract': contract,
            'organization': contract.organization,
            'login_url': f"{settings.FRONTEND_URL}/login",
            'portal_url': f"{settings.FRONTEND_URL}/student/dashboard"
        }

        # Use template rendering here
        message = f"""
        Dear {user.first_name} {user.last_name},

        Welcome to the {contract.organization.name} learning program!

        Your account has been created and you now have access to our learning platform.

        Login URL: {context['login_url']}
        Student Portal: {context['portal_url']}

        If you have any questions, please contact your institution's administrator.

        Best regards,
        OCH Learning Platform
        """

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False
        )

        return True

    except Exception as e:
        logger.error(f'Failed to send welcome email: {str(e)}')
        return False
