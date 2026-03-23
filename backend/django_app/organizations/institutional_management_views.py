"""
Institutional Management Views - API endpoints for institutional portal and management.
Handles seat allocation, bulk imports, student management, and analytics.
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Sum, Count
from django.http import HttpResponse
from datetime import date, timedelta
import csv
import io
import logging

from .institutional_management_models import (
    InstitutionalPortalAccess,
    InstitutionalSeatPool,
    InstitutionalStudentAllocation,
    InstitutionalBulkImport,
    InstitutionalTrackAssignment,
    InstitutionalSSO,
    InstitutionalDashboardMetrics
)
from .institutional_management_service import InstitutionalManagementService
from .institutional_models import InstitutionalContract
from programs.models import Cohort, Track
from programs.permissions import IsProgramDirector
from users.models import User

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