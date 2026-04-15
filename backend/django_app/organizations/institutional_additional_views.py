"""
Additional Institutional Billing Views - SSO, Bulk Import, Academic Calendar
"""
import csv
import io
import logging

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.db import transaction
from django.shortcuts import get_object_or_404
from programs.permissions import IsProgramDirector
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from users.models import User

from organizations.models import OrganizationMember
from users.models import Role, UserRole

from .institutional_models import InstitutionalContract, InstitutionalStudent
from .institutional_service import InstitutionalBillingService
from .institutional_management_service import InstitutionalManagementService
from .institutional_management_models import InstitutionalAcademicCalendar, InstitutionalSSO
from .institutional_management_models import InstitutionalStudentAllocation, InstitutionalTrackAssignment
from programs.models import Track
from .scim_models import InstitutionalSCIMToken

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def institution_onboarding_preview(request):
    """
    GET /api/v1/institutional/institution-onboarding-preview/?organization=<id>&contract=<uuid>
    Public preview for institution onboarding links.
    """
    org_id = request.query_params.get('organization')
    contract_id = request.query_params.get('contract')
    if not org_id or not contract_id:
        return Response(
            {'detail': 'organization and contract are required'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        contract = InstitutionalContract.objects.select_related('organization').get(
            id=contract_id,
            organization_id=org_id,
        )
    except InstitutionalContract.DoesNotExist:
        return Response({'detail': 'Contract not found'}, status=status.HTTP_404_NOT_FOUND)

    org = contract.organization
    return Response(
        {
            'organization': {
                'id': org.id,
                'name': org.name,
                'contact_email': org.contact_email,
                'contact_person_name': org.contact_person_name,
            },
            'contract': {
                'id': str(contract.id),
                'type': 'institution',
                'status': contract.status,
                'start_date': contract.start_date,
                'end_date': contract.end_date,
            },
        }
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def institution_onboarding_complete(request):
    """
    POST /api/v1/institutional/institution-onboarding-complete/
    Creates/updates the institution admin user, assigns org membership + role.
    """
    org_id = request.data.get('organization')
    contract_id = request.data.get('contract')
    email = (request.data.get('email') or '').strip().lower()
    first_name = (request.data.get('first_name') or '').strip()
    last_name = (request.data.get('last_name') or '').strip()
    password = request.data.get('password') or ''
    terms_accepted = bool(request.data.get('terms_accepted'))

    if not org_id or not contract_id:
        return Response({'detail': 'organization and contract are required'}, status=status.HTTP_400_BAD_REQUEST)
    if len(password) < 8:
        return Response({'detail': 'Password must be at least 8 characters.'}, status=status.HTTP_400_BAD_REQUEST)
    if not email:
        return Response({'detail': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)
    if not terms_accepted:
        return Response({'detail': 'You must accept the Terms and Conditions.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        contract = InstitutionalContract.objects.select_related('organization').get(
            id=contract_id,
            organization_id=org_id,
        )
    except InstitutionalContract.DoesNotExist:
        return Response({'detail': 'Contract not found'}, status=status.HTTP_404_NOT_FOUND)

    org = contract.organization
    with transaction.atomic():
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email,
                'first_name': first_name or (org.contact_person_name or org.name),
                'last_name': last_name,
                'email_verified': True,
                'account_status': 'active',
                'org_id': org,
            },
        )
        if not created:
            if first_name:
                user.first_name = first_name
            if last_name:
                user.last_name = last_name
            if getattr(user, 'org_id_id', None) is None:
                user.org_id = org
            if getattr(user, 'account_status', None) != 'active':
                user.account_status = 'active'
            user.email_verified = True
        user.set_password(password)
        user.save()

        OrganizationMember.objects.get_or_create(
            organization=org,
            user=user,
            defaults={'role': 'admin'},
        )

        role = (
            Role.objects.filter(name='institution_admin').first()
            or Role.objects.filter(name='organization_admin').first()
        )
        if role is None:
            role = Role.objects.create(
                name='institution_admin',
                display_name='Institution Admin',
                description='Admin access for institution/organization portal users',
                is_system_role=True,
            )

        UserRole.objects.get_or_create(
            user=user,
            role=role,
            scope='org',
            scope_ref=None,
            org_id=org,
            defaults={'assigned_by': None, 'is_active': True},
        )

    next_path = f"/dashboard/institution?organization={org.id}&contract={contract.id}"
    return Response({'success': True, 'email': email, 'organization': org.id, 'contract': str(contract.id), 'next': next_path})


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

                    # Validate email formatting (deliverability checks require external verification)
                    try:
                        validate_email(email)
                    except ValidationError:
                        results['errors'].append(f'Row {row_num}: Invalid email address')
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
        sso_config = request.data.get('sso_config', {}) or {}

        contract = get_object_or_404(InstitutionalContract, id=contract_id)

        # Accept either the newer InstitutionalSSO schema or legacy keys.
        protocol = (sso_config.get('protocol') or sso_config.get('provider_type') or '').strip().lower()
        if protocol in ('saml', 'saml2', 'saml_2_0'):
            protocol = 'saml2'
        if protocol in ('oidc', 'openid', 'open_id_connect'):
            protocol = 'oidc'

        provider_name = (sso_config.get('provider_name') or sso_config.get('provider') or 'Institution SSO').strip()
        entity_id = (sso_config.get('entity_id') or '').strip()
        sso_url = (sso_config.get('sso_url') or '').strip()
        x509_cert = (sso_config.get('x509_cert') or sso_config.get('certificate') or '').strip()
        slo_url = (sso_config.get('slo_url') or '').strip()

        if not protocol or not sso_url:
            return Response(
                {'error': 'sso_config.protocol/provider_type and sso_config.sso_url are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        auto_domains = sso_config.get('auto_enrollment_domains') or sso_config.get('allowed_domains') or []
        auto_enabled = bool(sso_config.get('auto_enrollment_enabled') or sso_config.get('domain_auto_enrollment'))

        provisioning = bool(sso_config.get('user_provisioning_enabled', False))
        deprovisioning = bool(sso_config.get('deprovisioning_enabled', False))
        attribute_mapping = sso_config.get('attribute_mapping') or {}
        status_value = (sso_config.get('status') or 'testing').strip().lower()
        if status_value not in {'draft', 'testing', 'active', 'disabled'}:
            status_value = 'testing'

        with transaction.atomic():
            cfg, _created = InstitutionalSSO.objects.update_or_create(
                contract=contract,
                defaults={
                    'protocol': protocol,
                    'provider_name': provider_name,
                    'entity_id': entity_id,
                    'sso_url': sso_url,
                    'slo_url': slo_url,
                    'x509_cert': x509_cert,
                    'auto_enrollment_domains': auto_domains or [],
                    'auto_enrollment_enabled': auto_enabled,
                    'user_provisioning_enabled': provisioning,
                    'deprovisioning_enabled': deprovisioning,
                    'attribute_mapping': attribute_mapping,
                    'status': status_value,
                    'created_by': request.user,
                }
            )

        return Response({
            'message': 'SSO integration configured successfully',
            'sso_config_id': str(cfg.id),
            'status': cfg.status,
            'auto_enrollment_enabled': cfg.auto_enrollment_enabled,
        })

    except Exception as e:
        logger.error(f'SSO setup error: {str(e)}')
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, IsProgramDirector])
def scim_token_admin(request, contract_id):
    """
    GET  /api/v1/institutional/contracts/{id}/scim-token/
      - returns token metadata (no raw token, since it's hashed)
    POST /api/v1/institutional/contracts/{id}/scim-token/
      - rotates token and returns the NEW raw token exactly once so it can be copied into Okta/Azure
    """
    contract = get_object_or_404(InstitutionalContract, id=contract_id)

    token_obj = InstitutionalSCIMToken.objects.filter(contract=contract).first()
    if request.method == 'GET':
        return Response({
            'contract_id': str(contract.id),
            'has_token': bool(token_obj),
            'is_active': bool(token_obj.is_active) if token_obj else False,
            'created_at': token_obj.created_at.isoformat() if token_obj else None,
            'last_used_at': token_obj.last_used_at.isoformat() if token_obj and token_obj.last_used_at else None,
        })

    # Rotate/reveal new token
    token_obj, raw = InstitutionalSCIMToken.rotate_token(contract)
    return Response({
        'contract_id': str(contract.id),
        'rotated': True,
        'token': raw,
        'created_at': token_obj.created_at.isoformat(),
    })


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

        # Assign tracks to institutional allocations (this is the source of dept + progress).
        allocations = InstitutionalStudentAllocation.objects.filter(
            seat_pool__contract=contract,
            status__in=['allocated', 'active', 'completed'],
        ).select_related('user')

        if department_filter:
            allocations = allocations.filter(department=department_filter)

        results = {
            'students_processed': 0,
            'tracks_assigned': 0,
            'errors': []
        }

        with transaction.atomic():
            for allocation in allocations:
                try:
                    for track_assignment in track_assignments:
                        track_id = track_assignment.get('track_id')
                        assignment_type = track_assignment.get('assignment_type') or (
                            'mandatory' if track_assignment.get('is_mandatory', True) else 'optional'
                        )
                        due_date = track_assignment.get('completion_deadline') or track_assignment.get('due_date')
                        custom_requirements = track_assignment.get('custom_requirements') or {}

                        if not track_id:
                            continue

                        track = get_object_or_404(Track, id=track_id)
                        obj, created = InstitutionalTrackAssignment.objects.get_or_create(
                            contract=contract,
                            student_allocation=allocation,
                            track=track,
                            defaults={
                                'assignment_type': assignment_type,
                                'due_date': due_date,
                                'department': allocation.department,
                                'custom_requirements': custom_requirements,
                                'assigned_by': request.user,
                            }
                        )
                        if not created:
                            # Update existing assignment type/deadline if provided.
                            updates = {}
                            if assignment_type and obj.assignment_type != assignment_type:
                                updates['assignment_type'] = assignment_type
                            if due_date:
                                updates['due_date'] = due_date
                            if custom_requirements:
                                updates['custom_requirements'] = custom_requirements
                            if updates:
                                for k, v in updates.items():
                                    setattr(obj, k, v)
                                obj.save(update_fields=list(updates.keys()) + ['updated_at'])

                        results['tracks_assigned'] += 1

                    results['students_processed'] += 1

                except Exception as e:
                    results['errors'].append(f'Student {allocation.user.email}: {str(e)}')

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


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsProgramDirector])
def set_academic_calendar(request, contract_id):
    """
    POST /api/v1/institutional/contracts/{id}/academic-calendar/
    Upsert academic calendar settings for a contract and (optionally) realign billing schedules.
    """
    try:
        contract = get_object_or_404(InstitutionalContract, id=contract_id)

        payload = request.data or {}
        calendar_type = payload.get('calendar_type')
        academic_year_start = payload.get('academic_year_start')
        academic_year_end = payload.get('academic_year_end')
        periods = payload.get('periods', [])
        break_periods = payload.get('break_periods', [])
        summer_program_enabled = bool(payload.get('summer_program_enabled', False))
        summer_billing_mode = payload.get('summer_billing_mode', 'full_rate')
        summer_discount_rate = payload.get('summer_discount_rate', 0)
        billing_aligned_to_calendar = bool(payload.get('billing_aligned_to_calendar', False))
        billing_period_mapping = payload.get('billing_period_mapping', {})

        if not calendar_type or not academic_year_start or not academic_year_end:
            return Response(
                {'error': 'calendar_type, academic_year_start, academic_year_end are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            cal, _created = InstitutionalAcademicCalendar.objects.update_or_create(
                contract=contract,
                defaults={
                    'calendar_type': calendar_type,
                    'academic_year_start': academic_year_start,
                    'academic_year_end': academic_year_end,
                    'periods': periods or [],
                    'break_periods': break_periods or [],
                    'summer_program_enabled': summer_program_enabled,
                    'summer_billing_mode': summer_billing_mode,
                    'summer_discount_rate': summer_discount_rate,
                    'billing_aligned_to_calendar': billing_aligned_to_calendar,
                    'billing_period_mapping': billing_period_mapping or {},
                }
            )

        realign = bool(payload.get('realign', True))
        alignment_result = None
        if realign:
            try:
                alignment_result = InstitutionalBillingService.realign_contract_to_academic_calendar(contract.id)
            except Exception as e:
                alignment_result = {'aligned': False, 'error': str(e)}

        return Response({
            'message': 'Academic calendar saved',
            'calendar_id': str(cal.id),
            'realignment': alignment_result,
        })

    except Exception as e:
        logger.error(f'Academic calendar save error: {str(e)}')
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
        # This endpoint is legacy; return the canonical enterprise dashboard analytics
        # used by the platform (no placeholders).
        analytics = InstitutionalManagementService.get_institutional_analytics(str(contract_id))
        return Response(analytics)

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
