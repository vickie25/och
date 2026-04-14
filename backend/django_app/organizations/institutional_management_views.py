"""
Institutional Management Views - API endpoints for institutional portal and management.
Handles seat allocation, bulk imports, student management, and analytics.
"""
import csv
import logging
from datetime import date, timedelta

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from programs.models import Cohort
from programs.permissions import IsProgramDirector
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.models import User

from .institutional_management_models import (
    InstitutionalBulkImport,
    InstitutionalPortalAccess,
    InstitutionalSeatPool,
    InstitutionalStudentAllocation,
    InstitutionalTrackAssignment,
)
from .institutional_management_service import InstitutionalManagementService
from .institutional_models import InstitutionalContract

logger = logging.getLogger(__name__)


def _can_access_institutional_contract(request, contract_id):
    """Program directors / staff may access any contract; others need portal_access row."""
    if not request.user.is_authenticated or not contract_id:
        return False
    if not InstitutionalContract.objects.filter(id=contract_id).exists():
        return False
    if IsProgramDirector().has_permission(request, None):
        return True
    return InstitutionalPortalAccess.objects.filter(
        user=request.user,
        contract_id=contract_id,
        is_active=True,
    ).exists()


class InstitutionalPortalPermission(permissions.BasePermission):
    """Portal users with contract access, or program directors (full institutional API)."""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if IsProgramDirector().has_permission(request, view):
            return True
        return InstitutionalPortalAccess.objects.filter(
            user=request.user,
            is_active=True,
        ).exists()

    def has_object_permission(self, request, view, obj):
        if IsProgramDirector().has_permission(request, view):
            return True
        contract_id = getattr(obj, 'contract_id', None)
        if contract_id is None and hasattr(obj, 'contract'):
            contract_id = getattr(obj.contract, 'id', None)
        if not contract_id:
            return False
        return InstitutionalPortalAccess.objects.filter(
            user=request.user,
            contract_id=contract_id,
            is_active=True,
        ).exists()


class InstitutionalSeatPoolViewSet(viewsets.ModelViewSet):
    """ViewSet for managing institutional seat pools"""

    permission_classes = [IsAuthenticated, InstitutionalPortalPermission]

    def get_queryset(self):
        """Filter seat pools by user's contract access"""
        user_contracts = InstitutionalPortalAccess.objects.filter(
            user=self.request.user,
            is_active=True
        ).values_list('contract_id', flat=True)

        return InstitutionalSeatPool.objects.filter(
            contract_id__in=user_contracts
        ).select_related('contract__organization')

    def list(self, request):
        """
        GET /api/v1/institutional/seat-pools/
        List seat pools with utilization metrics.
        """
        try:
            queryset = self.get_queryset()

            # Apply filters
            contract_id = request.query_params.get('contract_id')
            if contract_id:
                queryset = queryset.filter(contract_id=contract_id)

            pool_type = request.query_params.get('pool_type')
            if pool_type:
                queryset = queryset.filter(pool_type=pool_type)

            pools_data = []
            for pool in queryset:
                pools_data.append({
                    'id': str(pool.id),
                    'name': pool.name,
                    'pool_type': pool.pool_type,
                    'contract': {
                        'id': str(pool.contract.id),
                        'contract_number': pool.contract.contract_number,
                        'organization': pool.contract.organization.name
                    },
                    'allocated_seats': pool.allocated_seats,
                    'active_seats': pool.active_seats,
                    'reserved_seats': pool.reserved_seats,
                    'available_seats': pool.available_seats,
                    'utilization_rate': round(pool.utilization_rate, 2),
                    'department': pool.department,
                    'auto_recycle': pool.auto_recycle,
                    'recycle_delay_days': pool.recycle_delay_days,
                    'created_at': pool.created_at.isoformat()
                })

            return Response({'seat_pools': pools_data})

        except Exception as e:
            logger.error(f"Error listing seat pools: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def create(self, request):
        """
        POST /api/v1/institutional/seat-pools/
        Create a new seat pool.
        """
        try:
            data = request.data

            # Validate required fields
            required_fields = ['contract_id', 'name', 'allocated_seats']
            for field in required_fields:
                if not data.get(field):
                    return Response(
                        {'error': f'{field} is required'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Create seat pool
            seat_pool = InstitutionalManagementService.create_seat_pool(
                contract_id=data['contract_id'],
                name=data['name'],
                allocated_seats=int(data['allocated_seats']),
                pool_type=data.get('pool_type', 'general'),
                department=data.get('department', ''),
                allowed_tracks=data.get('allowed_tracks', []),
                created_by=request.user
            )

            return Response({
                'id': str(seat_pool.id),
                'message': f'Seat pool "{seat_pool.name}" created with {seat_pool.allocated_seats} seats'
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error creating seat pool: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def allocate_student(self, request, pk=None):
        """
        POST /api/v1/institutional/seat-pools/{id}/allocate_student/
        Allocate a student to this seat pool.
        """
        try:
            seat_pool = self.get_object()
            data = request.data

            user_id = data.get('user_id')
            email = data.get('email')

            if not user_id and not email:
                return Response(
                    {'error': 'Either user_id or email is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get user by ID or email
            if user_id:
                user = get_object_or_404(User, id=user_id)
            else:
                user = get_object_or_404(User, email=email)

            # Allocate student
            allocation = InstitutionalManagementService.allocate_student_to_pool(
                seat_pool_id=seat_pool.id,
                user_id=user.id,
                assigned_cohort_id=data.get('assigned_cohort_id'),
                assigned_tracks=data.get('assigned_tracks', []),
                department=data.get('department', ''),
                allocated_by=request.user
            )

            return Response({
                'allocation_id': str(allocation.id),
                'message': f'Student {user.email} allocated successfully',
                'status': allocation.status
            })

        except Exception as e:
            logger.error(f"Error allocating student: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def students(self, request, pk=None):
        """
        GET /api/v1/institutional/seat-pools/{id}/students/
        Get students allocated to this seat pool.
        """
        try:
            seat_pool = self.get_object()

            # Apply filters
            status_filter = request.query_params.get('status')
            department_filter = request.query_params.get('department')

            allocations = seat_pool.student_allocations.select_related('user', 'enrollment__cohort')

            if status_filter:
                allocations = allocations.filter(status=status_filter)
            if department_filter:
                allocations = allocations.filter(department=department_filter)

            students_data = []
            for allocation in allocations:
                student_data = {
                    'allocation_id': str(allocation.id),
                    'user': {
                        'id': allocation.user.id,
                        'email': allocation.user.email,
                        'first_name': allocation.user.first_name,
                        'last_name': allocation.user.last_name
                    },
                    'status': allocation.status,
                    'department': allocation.department,
                    'allocated_at': allocation.allocated_at.isoformat(),
                    'activated_at': allocation.activated_at.isoformat() if allocation.activated_at else None,
                    'assigned_tracks': allocation.assigned_tracks,
                    'completion_deadline': allocation.completion_deadline.isoformat() if allocation.completion_deadline else None
                }

                if allocation.enrollment:
                    student_data['enrollment'] = {
                        'id': str(allocation.enrollment.id),
                        'cohort': allocation.enrollment.cohort.name if allocation.enrollment.cohort else None,
                        'status': allocation.enrollment.status
                    }

                students_data.append(student_data)

            return Response({
                'students': students_data,
                'total_count': len(students_data)
            })

        except Exception as e:
            logger.error(f"Error getting seat pool students: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class InstitutionalBulkImportViewSet(viewsets.ModelViewSet):
    """ViewSet for managing bulk student imports"""

    permission_classes = [IsAuthenticated, InstitutionalPortalPermission]

    def get_queryset(self):
        """Filter bulk imports by user's contract access"""
        user_contracts = InstitutionalPortalAccess.objects.filter(
            user=self.request.user,
            is_active=True
        ).values_list('contract_id', flat=True)

        return InstitutionalBulkImport.objects.filter(
            contract_id__in=user_contracts
        ).select_related('contract__organization', 'seat_pool')

    def list(self, request):
        """
        GET /api/v1/institutional/bulk-imports/
        List bulk import records.
        """
        try:
            queryset = self.get_queryset()

            # Apply filters
            contract_id = request.query_params.get('contract_id')
            if contract_id:
                queryset = queryset.filter(contract_id=contract_id)

            status_filter = request.query_params.get('status')
            if status_filter:
                queryset = queryset.filter(status=status_filter)

            imports_data = []
            for import_record in queryset.order_by('-created_at')[:20]:
                imports_data.append({
                    'id': str(import_record.id),
                    'filename': import_record.filename,
                    'contract': {
                        'id': str(import_record.contract.id),
                        'contract_number': import_record.contract.contract_number,
                        'organization': import_record.contract.organization.name
                    },
                    'seat_pool': {
                        'id': str(import_record.seat_pool.id),
                        'name': import_record.seat_pool.name
                    },
                    'status': import_record.status,
                    'total_records': import_record.total_records,
                    'successful_records': import_record.successful_records,
                    'failed_records': import_record.failed_records,
                    'created_at': import_record.created_at.isoformat(),
                    'completed_at': import_record.completed_at.isoformat() if import_record.completed_at else None
                })

            return Response({'imports': imports_data})

        except Exception as e:
            logger.error(f"Error listing bulk imports: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def create(self, request):
        """
        POST /api/v1/institutional/bulk-imports/
        Process a bulk student import from CSV.
        """
        try:
            # Get form data
            contract_id = request.data.get('contract_id')
            seat_pool_id = request.data.get('seat_pool_id')
            csv_file = request.FILES.get('csv_file')

            if not all([contract_id, seat_pool_id, csv_file]):
                return Response(
                    {'error': 'contract_id, seat_pool_id, and csv_file are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Read CSV content
            csv_content = csv_file.read().decode('utf-8')

            # Import settings
            import_settings = {
                'filename': csv_file.name,
                'auto_enroll': request.data.get('auto_enroll', False),
                'send_welcome_emails': request.data.get('send_welcome_emails', True),
                'update_existing': request.data.get('update_existing', False),
                'default_cohort': request.data.get('default_cohort'),
                'default_tracks': request.data.getlist('default_tracks[]') or []
            }

            # Process bulk import
            bulk_import = InstitutionalManagementService.process_bulk_import(
                contract_id=contract_id,
                seat_pool_id=seat_pool_id,
                csv_content=csv_content,
                import_settings=import_settings,
                uploaded_by=request.user
            )

            return Response({
                'import_id': str(bulk_import.id),
                'status': bulk_import.status,
                'total_records': bulk_import.total_records,
                'successful_records': bulk_import.successful_records,
                'failed_records': bulk_import.failed_records,
                'message': f'Bulk import processed: {bulk_import.successful_records} successful, {bulk_import.failed_records} failed'
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error processing bulk import: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def retrieve(self, request, pk=None):
        """
        GET /api/v1/institutional/bulk-imports/{id}/
        Get detailed bulk import results.
        """
        try:
            bulk_import = self.get_object()

            return Response({
                'id': str(bulk_import.id),
                'filename': bulk_import.filename,
                'contract': {
                    'id': str(bulk_import.contract.id),
                    'contract_number': bulk_import.contract.contract_number,
                    'organization': bulk_import.contract.organization.name
                },
                'seat_pool': {
                    'id': str(bulk_import.seat_pool.id),
                    'name': bulk_import.seat_pool.name
                },
                'status': bulk_import.status,
                'total_records': bulk_import.total_records,
                'processed_records': bulk_import.processed_records,
                'successful_records': bulk_import.successful_records,
                'failed_records': bulk_import.failed_records,
                'import_results': bulk_import.import_results,
                'error_log': bulk_import.error_log,
                'import_settings': bulk_import.import_settings,
                'created_at': bulk_import.created_at.isoformat(),
                'started_at': bulk_import.started_at.isoformat() if bulk_import.started_at else None,
                'completed_at': bulk_import.completed_at.isoformat() if bulk_import.completed_at else None
            })

        except Exception as e:
            logger.error(f"Error retrieving bulk import: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['POST'])
@permission_classes([IsAuthenticated, InstitutionalPortalPermission])
def onboard_student(request):
    """
    POST /api/v1/institutional/onboard-student/
    Onboard a single student with full enrollment - creates user if needed,
    allocates to seat pool, assigns to cohort/tracks.
    Similar to director's bulk_create_enrollments but for single student.
    """
    try:
        data = request.data
        contract_id = data.get('contract_id')
        seat_pool_id = data.get('seat_pool_id')

        if not contract_id or not seat_pool_id:
            return Response(
                {'error': 'contract_id and seat_pool_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not _can_access_institutional_contract(request, contract_id):
            return Response(
                {'error': 'Access denied to this contract'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get or create user
        email = data.get('email', '').strip().lower()
        user_id = data.get('user_id')

        if not email and not user_id:
            return Response(
                {'error': 'Either email or user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get or create user
        if user_id:
            user = get_object_or_404(User, id=user_id)
        else:
            # Try to find existing user
            user = User.objects.filter(email=email).first()

            if not user:
                # Create new user if not found
                first_name = data.get('first_name', '')
                last_name = data.get('last_name', '')

                user = User.objects.create(
                    email=email,
                    username=email,
                    first_name=first_name,
                    last_name=last_name,
                    is_active=True,
                    account_status='active'
                )
                user_created = True
            else:
                user_created = False

        # Check if already allocated in this contract
        existing_allocation = InstitutionalStudentAllocation.objects.filter(
            seat_pool__contract_id=contract_id,
            user=user,
            status__in=['allocated', 'active']
        ).first()

        if existing_allocation:
            return Response({
                'success': False,
                'error': 'Student already allocated in this contract',
                'allocation_id': str(existing_allocation.id),
                'status': existing_allocation.status
            }, status=status.HTTP_400_BAD_REQUEST)

        # Allocate to seat pool
        allocation = InstitutionalManagementService.allocate_student_to_pool(
            seat_pool_id=seat_pool_id,
            user_id=user.id,
            assigned_cohort_id=data.get('assigned_cohort_id'),
            assigned_tracks=data.get('assigned_tracks', []),
            department=data.get('department', ''),
            allocated_by=request.user
        )

        # Send welcome email
        send_welcome = data.get('send_welcome_email', True)
        if send_welcome and user_created:
            InstitutionalManagementService._send_welcome_email(
                user,
                allocation.seat_pool.contract
            )

        return Response({
            'success': True,
            'message': 'Student onboarded successfully',
            'allocation_id': str(allocation.id),
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name
            },
            'status': allocation.status,
            'user_created': user_created,
            'enrollment': {
                'cohort_id': str(allocation.enrollment.cohort.id) if allocation.enrollment and allocation.enrollment.cohort else None,
                'enrollment_id': str(allocation.enrollment.id) if allocation.enrollment else None
            } if allocation.enrollment else None
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Error onboarding student: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated, InstitutionalPortalPermission])
def invite_student(request):
    """
    POST /api/v1/institutional/invite-student/
    Invite a student by email - sends invitation link to join the institution's program.
    Student gets pre-allocated seat when they accept.
    """
    try:
        data = request.data
        contract_id = data.get('contract_id')
        seat_pool_id = data.get('seat_pool_id')
        email = data.get('email', '').strip().lower()

        if not all([contract_id, seat_pool_id, email]):
            return Response(
                {'error': 'contract_id, seat_pool_id, and email are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not _can_access_institutional_contract(request, contract_id):
            return Response(
                {'error': 'Access denied to this contract'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Validate email
        if '@' not in email:
            return Response(
                {'error': 'Invalid email format'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if email already has active allocation in this contract
        existing = InstitutionalStudentAllocation.objects.filter(
            seat_pool__contract_id=contract_id,
            user__email=email,
            status__in=['allocated', 'active', 'invited']
        ).first()

        if existing:
            return Response({
                'success': False,
                'error': 'Student already invited or allocated in this contract',
                'status': existing.status
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create placeholder allocation with 'invited' status
        seat_pool = get_object_or_404(InstitutionalSeatPool, id=seat_pool_id)

        # Check seat availability
        if not seat_pool.can_allocate_seats(1):
            return Response({
                'success': False,
                'error': 'No available seats in this pool'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Reserve a seat (but don't fully allocate yet)
        seat_pool.reserve_seats(1)

        # Create invitation record
        from .institutional_management_models import InstitutionalInvitation
        invitation = InstitutionalInvitation.objects.create(
            contract_id=contract_id,
            seat_pool=seat_pool,
            email=email,
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            department=data.get('department', ''),
            assigned_cohort_id=data.get('assigned_cohort_id'),
            assigned_tracks=data.get('assigned_tracks', []),
            invited_by=request.user,
            expires_at=timezone.now() + timedelta(days=7)
        )

        # Send invitation email
        InstitutionalManagementService._send_invitation_email(
            invitation,
            request.build_absolute_uri('/institutional/accept-invitation/')
        )

        return Response({
            'success': True,
            'message': f'Invitation sent to {email}',
            'invitation_id': str(invitation.id),
            'expires_at': invitation.expires_at.isoformat()
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Error inviting student: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, InstitutionalPortalPermission])
def manage_cohort_enrollments(request, cohort_id=None):
    """
    GET /api/v1/institutional/cohorts/{id}/enrollments/
    POST /api/v1/institutional/cohorts/{id}/enrollments/

    List or manage enrollments for a specific cohort - similar to director capability.
    """
    try:
        if request.method == 'GET':
            cohort = get_object_or_404(Cohort, id=cohort_id)

            # Get enrollments for this cohort within user's contracts
            allocations = InstitutionalStudentAllocation.objects.filter(
                enrollment__cohort=cohort,
                status__in=['active', 'allocated', 'completed']
            ).select_related('user', 'seat_pool', 'enrollment')

            # Filter by contract access
            user_contracts = InstitutionalPortalAccess.objects.filter(
                user=request.user,
                is_active=True
            ).values_list('contract_id', flat=True)

            allocations = allocations.filter(seat_pool__contract_id__in=user_contracts)

            enrollments_data = []
            for allocation in allocations:
                enrollments_data.append({
                    'allocation_id': str(allocation.id),
                    'user': {
                        'id': allocation.user.id,
                        'email': allocation.user.email,
                        'first_name': allocation.user.first_name,
                        'last_name': allocation.user.last_name
                    },
                    'seat_pool': allocation.seat_pool.name,
                    'department': allocation.department,
                    'status': allocation.status,
                    'enrollment_status': allocation.enrollment.status if allocation.enrollment else None,
                    'payment_status': allocation.enrollment.payment_status if allocation.enrollment else None,
                    'joined_at': allocation.allocated_at.isoformat()
                })

            return Response({
                'cohort': {
                    'id': str(cohort.id),
                    'name': cohort.name,
                    'track': cohort.track.name if cohort.track else None
                },
                'enrollments': enrollments_data,
                'total': len(enrollments_data)
            })

        elif request.method == 'POST':
            # Add student to cohort enrollment
            data = request.data
            allocation_id = data.get('allocation_id')

            if not allocation_id:
                return Response(
                    {'error': 'allocation_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            allocation = get_object_or_404(
                InstitutionalStudentAllocation,
                id=allocation_id
            )

            # Verify access
            if not _can_access_institutional_contract(request, allocation.seat_pool.contract_id):
                return Response(
                    {'error': 'Access denied'},
                    status=status.HTTP_403_FORBIDDEN
                )

            cohort = get_object_or_404(Cohort, id=cohort_id)

            # Create enrollment
            from programs.models import Enrollment
            enrollment, created = Enrollment.objects.get_or_create(
                cohort=cohort,
                user=allocation.user,
                defaults={
                    'enrollment_type': 'director',
                    'seat_type': 'sponsored',
                    'payment_status': 'waived',
                    'status': 'active',
                    'org': allocation.seat_pool.contract.organization
                }
            )

            # Link enrollment to allocation
            allocation.enrollment = enrollment
            allocation.activate()
            allocation.save()

            return Response({
                'success': True,
                'message': 'Student enrolled in cohort',
                'enrollment_id': str(enrollment.id),
                'status': enrollment.status
            })

    except Exception as e:
        logger.error(f"Error managing cohort enrollments: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated, InstitutionalPortalPermission])
def bulk_enroll_students(request):
    """
    POST /api/v1/institutional/bulk-enroll/
    Bulk enroll multiple existing allocations to a specific cohort.
    Similar to director's bulk_create_enrollments.
    """
    try:
        data = request.data
        cohort_id = data.get('cohort_id')
        allocation_ids = data.get('allocation_ids', [])

        if not cohort_id or not allocation_ids:
            return Response(
                {'error': 'cohort_id and allocation_ids are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        cohort = get_object_or_404(Cohort, id=cohort_id)

        # Get allocations for user's contracts
        user_contracts = InstitutionalPortalAccess.objects.filter(
            user=request.user,
            is_active=True
        ).values_list('contract_id', flat=True)

        allocations = InstitutionalStudentAllocation.objects.filter(
            id__in=allocation_ids,
            seat_pool__contract_id__in=user_contracts,
            status__in=['allocated', 'active']
        )

        results = {
            'enrolled': [],
            'errors': []
        }

        from programs.models import Enrollment

        for allocation in allocations:
            try:
                # Create enrollment
                enrollment, created = Enrollment.objects.get_or_create(
                    cohort=cohort,
                    user=allocation.user,
                    defaults={
                        'enrollment_type': 'director',
                        'seat_type': 'sponsored',
                        'payment_status': 'waived',
                        'status': 'active',
                        'org': allocation.seat_pool.contract.organization
                    }
                )

                # Link to allocation
                allocation.enrollment = enrollment
                allocation.activate()
                allocation.save()

                results['enrolled'].append({
                    'allocation_id': str(allocation.id),
                    'user_email': allocation.user.email,
                    'enrollment_id': str(enrollment.id)
                })

            except Exception as e:
                results['errors'].append({
                    'allocation_id': str(allocation.id),
                    'user_email': allocation.user.email,
                    'error': str(e)
                })

        return Response({
            'success': True,
            'cohort_id': str(cohort_id),
            'enrolled_count': len(results['enrolled']),
            'error_count': len(results['errors']),
            'results': results
        })

    except Exception as e:
        logger.error(f"Error bulk enrolling students: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, InstitutionalPortalPermission])
def available_cohorts(request):
    """
    GET /api/v1/institutional/available-cohorts/
    List active cohorts available for institutional student assignment.
    """
    try:
        contract_id = request.query_params.get('contract_id')
        track_id = request.query_params.get('track_id')

        if not contract_id:
            return Response(
                {'error': 'contract_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not _can_access_institutional_contract(request, contract_id):
            return Response(
                {'error': 'Access denied to this contract'},
                status=status.HTTP_403_FORBIDDEN
            )

        from programs.models import Cohort

        # Get active cohorts
        cohorts = Cohort.objects.filter(
            status__in=['registration', 'active', 'in_progress']
        ).select_related('track', 'calendar')

        # Filter by track if specified
        if track_id:
            cohorts = cohorts.filter(track_id=track_id)

        # Get seat pool allowed cohorts for this contract
        seat_pools = InstitutionalSeatPool.objects.filter(contract_id=contract_id)
        allowed_cohort_ids = set()
        for pool in seat_pools:
            allowed_cohort_ids.update(pool.allowed_cohorts or [])

        # If pools have specific cohort restrictions, filter
        if allowed_cohort_ids:
            cohorts = cohorts.filter(id__in=allowed_cohort_ids)

        cohorts_data = []
        for cohort in cohorts:
            # Calculate seat availability
            enrolled_count = cohort.enrollments.filter(status='active').count()
            available_seats = max(0, cohort.seat_cap - enrolled_count)

            cohorts_data.append({
                'id': str(cohort.id),
                'name': cohort.name,
                'track': {
                    'id': str(cohort.track.id) if cohort.track else None,
                    'name': cohort.track.name if cohort.track else None
                },
                'start_date': cohort.start_date.isoformat() if cohort.start_date else None,
                'end_date': cohort.end_date.isoformat() if cohort.end_date else None,
                'status': cohort.status,
                'mode': cohort.mode,
                'seat_cap': cohort.seat_cap,
                'enrolled_count': enrolled_count,
                'available_seats': available_seats,
                'mentor_ratio': cohort.mentor_ratio,
                'is_open_for_enrollment': cohort.is_open_for_enrollment
            })

        return Response({
            'cohorts': cohorts_data,
            'total': len(cohorts_data)
        })

    except Exception as e:
        logger.error(f"Error getting available cohorts: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, InstitutionalPortalPermission])
def available_tracks(request):
    """
    GET /api/v1/institutional/available-tracks/
    List active tracks available for institutional student assignment.
    """
    try:
        contract_id = request.query_params.get('contract_id')

        if not contract_id:
            return Response(
                {'error': 'contract_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not _can_access_institutional_contract(request, contract_id):
            return Response(
                {'error': 'Access denied to this contract'},
                status=status.HTTP_403_FORBIDDEN
            )

        from programs.models import Track

        # Get active tracks
        tracks = Track.objects.filter(
            is_active=True
        ).select_related('program')

        # Get seat pool allowed tracks for this contract
        seat_pools = InstitutionalSeatPool.objects.filter(contract_id=contract_id)
        allowed_track_ids = set()
        for pool in seat_pools:
            allowed_track_ids.update(pool.allowed_tracks or [])

        # If pools have specific track restrictions, filter
        if allowed_track_ids:
            tracks = tracks.filter(id__in=allowed_track_ids)

        tracks_data = []
        for track in tracks:
            # Get active cohorts count for this track
            active_cohorts_count = track.cohorts.filter(
                status__in=['registration', 'active', 'in_progress']
            ).count()

            tracks_data.append({
                'id': str(track.id),
                'name': track.name,
                'description': track.description,
                'program': {
                    'id': str(track.program.id) if track.program else None,
                    'name': track.program.name if track.program else None
                },
                'duration_weeks': track.duration_weeks,
                'difficulty_level': track.difficulty_level,
                'certification_offered': track.certification_offered,
                'active_cohorts_count': active_cohorts_count,
                'skills': track.skills[:10] if track.skills else [],  # Top 10 skills
                'estimated_hours': track.estimated_hours
            })

        return Response({
            'tracks': tracks_data,
            'total': len(tracks_data)
        })

    except Exception as e:
        logger.error(f"Error getting available tracks: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated, InstitutionalPortalPermission])
def institutional_dashboard(request):
    """
    GET /api/v1/institutional/dashboard/
    Get institutional dashboard with comprehensive metrics.
    """
    try:
        contract_id = request.query_params.get('contract_id')
        if not contract_id:
            return Response(
                {'error': 'contract_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not _can_access_institutional_contract(request, contract_id):
            return Response(
                {'error': 'Access denied to this contract'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get comprehensive analytics
        analytics = InstitutionalManagementService.get_institutional_analytics(contract_id)

        return Response(analytics)

    except Exception as e:
        logger.error(f"Error getting institutional dashboard: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, InstitutionalPortalPermission])
def student_progress_report(request):
    """
    GET /api/v1/institutional/student-progress/
    Get detailed student progress report.
    """
    try:
        contract_id = request.query_params.get('contract_id')
        if not contract_id:
            return Response(
                {'error': 'contract_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not _can_access_institutional_contract(request, contract_id):
            return Response(
                {'error': 'Access denied to this contract'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get student allocations with progress
        allocations = InstitutionalStudentAllocation.objects.filter(
            seat_pool__contract_id=contract_id,
            status__in=['active', 'completed']
        ).select_related('user', 'seat_pool', 'enrollment__cohort')

        students_data = []
        for allocation in allocations:
            # Get track assignments
            track_assignments = InstitutionalTrackAssignment.objects.filter(
                student_allocation=allocation
            ).select_related('track')

            assignments_data = []
            for assignment in track_assignments:
                assignments_data.append({
                    'track_name': assignment.track.name,
                    'assignment_type': assignment.assignment_type,
                    'status': assignment.status,
                    'progress_percentage': float(assignment.progress_percentage),
                    'due_date': assignment.due_date.isoformat() if assignment.due_date else None,
                    'is_overdue': assignment.is_overdue
                })

            student_data = {
                'user': {
                    'id': allocation.user.id,
                    'email': allocation.user.email,
                    'first_name': allocation.user.first_name,
                    'last_name': allocation.user.last_name
                },
                'seat_pool': allocation.seat_pool.name,
                'department': allocation.department,
                'status': allocation.status,
                'allocated_at': allocation.allocated_at.isoformat(),
                'track_assignments': assignments_data,
                'overall_progress': 65.0,  # Placeholder - would calculate from actual progress
                'last_activity': '2024-01-15T10:30:00Z',  # Placeholder
                'completion_rate': 75.0  # Placeholder
            }

            if allocation.enrollment and allocation.enrollment.cohort:
                student_data['cohort'] = {
                    'id': str(allocation.enrollment.cohort.id),
                    'name': allocation.enrollment.cohort.name
                }

            students_data.append(student_data)

        return Response({
            'students': students_data,
            'summary': {
                'total_students': len(students_data),
                'avg_progress': 68.5,  # Placeholder
                'on_track_students': int(len(students_data) * 0.7),
                'behind_students': int(len(students_data) * 0.3)
            }
        })

    except Exception as e:
        logger.error(f"Error getting student progress report: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated, InstitutionalPortalPermission])
def recycle_seats(request):
    """
    POST /api/v1/institutional/recycle-seats/
    Recycle inactive student seats.
    """
    try:
        contract_id = request.data.get('contract_id')
        days_inactive = int(request.data.get('days_inactive', 30))

        if not contract_id:
            return Response(
                {'error': 'contract_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not _can_access_institutional_contract(request, contract_id):
            return Response(
                {'error': 'Access denied to this contract'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Recycle seats
        results = InstitutionalManagementService.recycle_inactive_seats(
            contract_id=contract_id,
            days_inactive=days_inactive
        )

        return Response({
            'message': f'Recycled {results["seats_recycled"]} seats from inactive students',
            'recycled_students': results['recycled_students'],
            'seats_recycled': results['seats_recycled'],
            'errors': results['errors']
        })

    except Exception as e:
        logger.error(f"Error recycling seats: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, InstitutionalPortalPermission])
def export_student_data(request):
    """
    GET /api/v1/institutional/export-students/
    Export student data as CSV.
    """
    try:
        contract_id = request.query_params.get('contract_id')
        if not contract_id:
            return Response(
                {'error': 'contract_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not _can_access_institutional_contract(request, contract_id):
            return Response(
                {'error': 'Access denied to this contract'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get student allocations
        allocations = InstitutionalStudentAllocation.objects.filter(
            seat_pool__contract_id=contract_id
        ).select_related('user', 'seat_pool', 'enrollment__cohort')

        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="students_export_{date.today()}.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Email', 'First Name', 'Last Name', 'Department', 'Seat Pool',
            'Status', 'Allocated Date', 'Cohort', 'Progress %', 'Last Activity'
        ])

        for allocation in allocations:
            writer.writerow([
                allocation.user.email,
                allocation.user.first_name,
                allocation.user.last_name,
                allocation.department,
                allocation.seat_pool.name,
                allocation.status,
                allocation.allocated_at.strftime('%Y-%m-%d'),
                allocation.enrollment.cohort.name if allocation.enrollment and allocation.enrollment.cohort else '',
                '65%',  # Placeholder
                '2024-01-15'  # Placeholder
            ])

        return response

    except Exception as e:
        logger.error(f"Error exporting student data: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_portal_access(request):
    """
    GET /api/v1/institutional/portal-access/
    Get user's institutional portal access permissions.
    """
    try:
        access_records = InstitutionalPortalAccess.objects.filter(
            user=request.user,
            is_active=True
        ).select_related('contract__organization')

        access_data = []
        for access in access_records:
            access_data.append({
                'contract': {
                    'id': str(access.contract.id),
                    'contract_number': access.contract.contract_number,
                    'organization': access.contract.organization.name
                },
                'role': access.role,
                'permissions': access.permissions,
                'last_login': access.last_login.isoformat() if access.last_login else None
            })

        return Response({
            'portal_access': access_data,
            'has_access': len(access_data) > 0
        })

    except Exception as e:
        logger.error(f"Error getting portal access: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
