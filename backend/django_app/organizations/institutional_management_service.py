"""
Institutional Management Service - Complete seat allocation and student management system.
Handles bulk imports, seat pooling, track assignments, and SSO integration.
"""
import csv
import io
import logging
from datetime import date, timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from programs.models import Cohort, Enrollment, Track

from users.models import User

from .institutional_management_models import (
    InstitutionalBulkImport,
    InstitutionalDashboardMetrics,
    InstitutionalSeatPool,
    InstitutionalSSO,
    InstitutionalStudentAllocation,
    InstitutionalTrackAssignment,
)
from .institutional_models import InstitutionalContract

logger = logging.getLogger(__name__)


class InstitutionalManagementService:
    """Service class for institutional management operations"""

    @staticmethod
    def create_seat_pool(contract_id, name, allocated_seats, pool_type='general',
                        department='', allowed_tracks=None, created_by=None):
        """
        Create a new seat pool for an institutional contract.

        Args:
            contract_id: InstitutionalContract UUID
            name: Pool name
            allocated_seats: Number of seats to allocate
            pool_type: Type of pool (general, department, program, cohort)
            department: Department name (if applicable)
            allowed_tracks: List of track IDs that can use this pool
            created_by: User who created the pool

        Returns:
            InstitutionalSeatPool instance
        """
        try:
            contract = InstitutionalContract.objects.get(id=contract_id)

            # Validate seat allocation doesn't exceed contract limit
            total_allocated = InstitutionalSeatPool.objects.filter(
                contract=contract
            ).aggregate(
                total=models.Sum('allocated_seats')
            )['total'] or 0

            if total_allocated + allocated_seats > contract.student_seat_count:
                raise ValueError(
                    f"Cannot allocate {allocated_seats} seats. "
                    f"Contract limit: {contract.student_seat_count}, "
                    f"Already allocated: {total_allocated}"
                )

            seat_pool = InstitutionalSeatPool.objects.create(
                contract=contract,
                name=name,
                pool_type=pool_type,
                allocated_seats=allocated_seats,
                department=department,
                allowed_tracks=allowed_tracks or [],
                created_by=created_by
            )

            logger.info(f"Created seat pool {name} with {allocated_seats} seats for contract {contract.contract_number}")
            return seat_pool

        except InstitutionalContract.DoesNotExist:
            raise ValueError(f"Contract {contract_id} not found")

    @staticmethod
    def allocate_student_to_pool(seat_pool_id, user_id, assigned_cohort_id=None,
                                assigned_tracks=None, department='', allocated_by=None):
        """
        Allocate a student to a seat pool.

        Args:
            seat_pool_id: InstitutionalSeatPool UUID
            user_id: User ID to allocate
            assigned_cohort_id: Cohort to assign student to
            assigned_tracks: List of mandatory track IDs
            department: Department assignment
            allocated_by: User who made the allocation

        Returns:
            InstitutionalStudentAllocation instance
        """
        try:
            seat_pool = InstitutionalSeatPool.objects.get(id=seat_pool_id)
            user = User.objects.get(id=user_id)

            # Check if pool has available seats
            if not seat_pool.can_allocate_seats(1):
                raise ValueError(f"No available seats in pool {seat_pool.name}")

            # Check if student is already allocated in this contract
            existing_allocation = InstitutionalStudentAllocation.objects.filter(
                seat_pool__contract=seat_pool.contract,
                user=user,
                status__in=['allocated', 'active']
            ).first()

            if existing_allocation:
                raise ValueError(f"Student {user.email} is already allocated in this contract")

            with transaction.atomic():
                # Create allocation
                allocation = InstitutionalStudentAllocation.objects.create(
                    seat_pool=seat_pool,
                    user=user,
                    assigned_cohort_id=assigned_cohort_id,
                    assigned_tracks=assigned_tracks or [],
                    department=department,
                    allocated_by=allocated_by,
                    status='allocated'
                )

                # Allocate seat from pool
                seat_pool.allocate_seats(1)

                # Create enrollment if cohort is assigned
                if assigned_cohort_id:
                    cohort = Cohort.objects.get(id=assigned_cohort_id)
                    enrollment = Enrollment.objects.create(
                        cohort=cohort,
                        user=user,
                        enrollment_type='director',
                        seat_type='sponsored',
                        payment_status='waived',
                        status='active'
                    )
                    allocation.enrollment = enrollment
                    allocation.activate()
                    allocation.save()

                # Create mandatory track assignments
                if assigned_tracks:
                    InstitutionalManagementService._create_track_assignments(
                        allocation, assigned_tracks, allocated_by
                    )

                logger.info(f"Allocated student {user.email} to seat pool {seat_pool.name}")
                return allocation

        except (InstitutionalSeatPool.DoesNotExist, User.DoesNotExist) as e:
            raise ValueError(str(e))

    @staticmethod
    def _create_track_assignments(allocation, track_ids, assigned_by):
        """Create mandatory track assignments for a student allocation"""
        for track_id in track_ids:
            try:
                track = Track.objects.get(id=track_id)
                InstitutionalTrackAssignment.objects.create(
                    contract=allocation.seat_pool.contract,
                    student_allocation=allocation,
                    track=track,
                    assignment_type='mandatory',
                    assigned_by=assigned_by,
                    department=allocation.department
                )
            except Track.DoesNotExist:
                logger.warning(f"Track {track_id} not found for assignment")

    @staticmethod
    def process_bulk_import(contract_id, seat_pool_id, csv_content, import_settings, uploaded_by):
        """
        Process bulk student import from CSV.

        Args:
            contract_id: InstitutionalContract UUID
            seat_pool_id: InstitutionalSeatPool UUID
            csv_content: CSV file content as string
            import_settings: Import configuration dict
            uploaded_by: User who uploaded the file

        Returns:
            InstitutionalBulkImport instance
        """
        try:
            contract = InstitutionalContract.objects.get(id=contract_id)
            seat_pool = InstitutionalSeatPool.objects.get(id=seat_pool_id)

            # Parse CSV
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            rows = list(csv_reader)

            # Create bulk import record
            bulk_import = InstitutionalBulkImport.objects.create(
                contract=contract,
                seat_pool=seat_pool,
                filename=import_settings.get('filename', 'bulk_import.csv'),
                file_size=len(csv_content),
                total_records=len(rows),
                import_settings=import_settings,
                uploaded_by=uploaded_by,
                status='processing',
                started_at=timezone.now()
            )

            # Process rows
            results = {
                'created': [],
                'updated': [],
                'failed': [],
                'duplicates': []
            }
            errors = []

            for i, row in enumerate(rows):
                try:
                    result = InstitutionalManagementService._process_import_row(
                        row, seat_pool, import_settings, uploaded_by
                    )
                    results[result['status']].append(result)
                    bulk_import.processed_records += 1

                    if result['status'] in ['created', 'updated']:
                        bulk_import.successful_records += 1
                    else:
                        bulk_import.failed_records += 1

                except Exception as e:
                    error_msg = f"Row {i+1}: {str(e)}"
                    errors.append(error_msg)
                    bulk_import.failed_records += 1
                    logger.error(f"Bulk import error: {error_msg}")

            # Update bulk import record
            bulk_import.import_results = results
            bulk_import.error_log = errors
            bulk_import.status = 'completed' if bulk_import.failed_records == 0 else 'partial'
            bulk_import.completed_at = timezone.now()
            bulk_import.save()

            logger.info(f"Bulk import completed: {bulk_import.successful_records} successful, {bulk_import.failed_records} failed")
            return bulk_import

        except Exception as e:
            logger.error(f"Bulk import failed: {str(e)}")
            if 'bulk_import' in locals():
                bulk_import.status = 'failed'
                bulk_import.error_log = [str(e)]
                bulk_import.completed_at = timezone.now()
                bulk_import.save()
            raise

    @staticmethod
    def _process_import_row(row, seat_pool, import_settings, uploaded_by):
        """Process a single row from bulk import CSV"""
        email = row.get('email', '').strip().lower()
        first_name = row.get('first_name', '').strip()
        last_name = row.get('last_name', '').strip()
        department = row.get('department', '').strip()

        if not email:
            raise ValueError("Email is required")

        # Validate email format
        if '@' not in email:
            raise ValueError(f"Invalid email format: {email}")

        # Check for duplicates in this contract
        existing_allocation = InstitutionalStudentAllocation.objects.filter(
            seat_pool__contract=seat_pool.contract,
            user__email=email,
            status__in=['allocated', 'active']
        ).first()

        if existing_allocation:
            return {
                'status': 'duplicates',
                'email': email,
                'message': 'Already allocated in this contract'
            }

        # Get or create user
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email,
                'first_name': first_name,
                'last_name': last_name,
                'is_active': True,
                'account_status': 'active'
            }
        )

        if not created and import_settings.get('update_existing', False):
            # Update existing user
            user.first_name = first_name or user.first_name
            user.last_name = last_name or user.last_name
            user.save()

        # Allocate to seat pool
        try:
            allocation = InstitutionalManagementService.allocate_student_to_pool(
                seat_pool_id=seat_pool.id,
                user_id=user.id,
                assigned_cohort_id=import_settings.get('default_cohort'),
                assigned_tracks=import_settings.get('default_tracks', []),
                department=department,
                allocated_by=uploaded_by
            )

            # Send welcome email if enabled
            if import_settings.get('send_welcome_emails', False):
                InstitutionalManagementService._send_welcome_email(user, seat_pool.contract)

            return {
                'status': 'created' if created else 'updated',
                'email': email,
                'allocation_id': str(allocation.id),
                'message': 'Successfully allocated'
            }

        except Exception as e:
            raise ValueError(f"Failed to allocate {email}: {str(e)}")

    @staticmethod
    def _send_welcome_email(user, contract):
        """Send welcome email to newly allocated student"""
        try:
            subject = f"Welcome to {contract.organization.name} Learning Program"
            message = f"""
Dear {user.first_name or user.email},

Welcome to the {contract.organization.name} learning program powered by OCH!

Your account has been created and you now have access to our cybersecurity training platform.

Getting Started:
1. Log in to your account at {settings.FRONTEND_URL}
2. Complete your profile setup
3. Begin your assigned learning tracks

If you have any questions, please contact your program administrator or our support team.

Best regards,
The OCH Team
            """

            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True
            )

        except Exception as e:
            logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")

    @staticmethod
    def calculate_dashboard_metrics(contract_id):
        """
        Calculate and cache dashboard metrics for an institutional contract.

        Args:
            contract_id: InstitutionalContract UUID

        Returns:
            InstitutionalDashboardMetrics instance
        """
        try:
            start_time = timezone.now()
            contract = InstitutionalContract.objects.get(id=contract_id)

            # Get or create metrics record
            metrics, created = InstitutionalDashboardMetrics.objects.get_or_create(
                contract=contract
            )

            # Calculate seat utilization metrics
            seat_pools = contract.seat_pools.all()
            metrics.total_allocated_seats = sum(pool.allocated_seats for pool in seat_pools)
            metrics.total_active_seats = sum(pool.active_seats for pool in seat_pools)
            metrics.total_available_seats = sum(pool.available_seats for pool in seat_pools)
            metrics.utilization_rate = (
                (metrics.total_active_seats / metrics.total_allocated_seats * 100)
                if metrics.total_allocated_seats > 0 else 0
            )

            # Calculate student metrics
            allocations = InstitutionalStudentAllocation.objects.filter(
                seat_pool__contract=contract
            )
            metrics.total_students = allocations.count()
            metrics.active_students = allocations.filter(status='active').count()
            metrics.completed_students = allocations.filter(status='completed').count()
            metrics.withdrawn_students = allocations.filter(status='withdrawn').count()

            # Calculate progress metrics
            active_allocations = allocations.filter(status='active')
            if active_allocations.exists():
                # This would need integration with actual progress tracking
                metrics.avg_completion_rate = 75.0  # Placeholder
                metrics.avg_progress_percentage = 65.0  # Placeholder
                metrics.students_on_track = int(active_allocations.count() * 0.7)
                metrics.students_behind = active_allocations.count() - metrics.students_on_track

            # Calculate track assignment metrics
            track_assignments = InstitutionalTrackAssignment.objects.filter(
                contract=contract
            )
            metrics.mandatory_assignments = track_assignments.filter(assignment_type='mandatory').count()
            metrics.completed_assignments = track_assignments.filter(status='completed').count()
            metrics.overdue_assignments = track_assignments.filter(status='overdue').count()

            # Calculate ROI metrics
            if metrics.total_students > 0:
                metrics.cost_per_student = contract.annual_amount / metrics.total_students
            metrics.avg_completion_time_days = 90  # Placeholder
            metrics.certification_rate = 85.0  # Placeholder

            # Calculate engagement metrics (placeholders - would need actual tracking)
            metrics.avg_login_frequency = 4.2
            metrics.avg_session_duration_minutes = 45
            metrics.last_30_days_activity = int(metrics.active_students * 0.8)

            # Save metrics
            end_time = timezone.now()
            metrics.calculation_duration_seconds = int((end_time - start_time).total_seconds())
            metrics.save()

            logger.info(f"Calculated dashboard metrics for contract {contract.contract_number}")
            return metrics

        except InstitutionalContract.DoesNotExist:
            raise ValueError(f"Contract {contract_id} not found")

    @staticmethod
    def recycle_inactive_seats(contract_id, days_inactive=30):
        """
        Recycle seats from inactive students.

        Args:
            contract_id: InstitutionalContract UUID
            days_inactive: Days of inactivity before recycling

        Returns:
            Dictionary with recycling results
        """
        try:
            contract = InstitutionalContract.objects.get(id=contract_id)
            cutoff_date = timezone.now() - timedelta(days=days_inactive)

            # Find inactive allocations
            inactive_allocations = InstitutionalStudentAllocation.objects.filter(
                seat_pool__contract=contract,
                status='active',
                seat_pool__auto_recycle=True,
                progress_last_updated__lt=cutoff_date
            )

            recycled_count = 0
            results = {
                'recycled_students': [],
                'seats_recycled': 0,
                'errors': []
            }

            for allocation in inactive_allocations:
                try:
                    # Check if student has any recent activity (placeholder logic)
                    # In real implementation, this would check actual user activity

                    allocation.recycle()
                    recycled_count += 1

                    results['recycled_students'].append({
                        'email': allocation.user.email,
                        'seat_pool': allocation.seat_pool.name,
                        'inactive_days': (timezone.now() - allocation.progress_last_updated).days
                    })

                except Exception as e:
                    results['errors'].append(f"Failed to recycle {allocation.user.email}: {str(e)}")

            results['seats_recycled'] = recycled_count
            logger.info(f"Recycled {recycled_count} inactive seats for contract {contract.contract_number}")
            return results

        except InstitutionalContract.DoesNotExist:
            raise ValueError(f"Contract {contract_id} not found")

    @staticmethod
    def _send_invitation_email(invitation, base_url):
        """Send invitation email to prospective student"""
        try:
            from django.conf import settings
            from django.core.mail import send_mail

            contract = invitation.contract
            organization_name = contract.organization.name

            # Build invitation URL with token
            invitation_url = f"{base_url}?token={invitation.token}"

            subject = f"You're invited to join {organization_name}'s learning program"

            message = f"""
Dear {invitation.first_name or invitation.email},

You've been invited to join {organization_name}'s cybersecurity learning program powered by OCH!

Your program includes:
- Access to industry-leading cybersecurity curriculum
- Hands-on missions and labs
- Expert mentorship and support
- Portfolio building opportunities
- Career readiness preparation

Click the link below to accept your invitation and get started:
{invitation_url}

This invitation expires on {invitation.expires_at.strftime('%B %d, %Y')}.

If you have any questions, please contact your program administrator.

Best regards,
The {organization_name} Team
            """

            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[invitation.email],
                fail_silently=True
            )

            logger.info(f"Invitation email sent to {invitation.email} for {organization_name}")

        except Exception as e:
            logger.error(f"Failed to send invitation email to {invitation.email}: {str(e)}")
        """
        Set up SSO integration for an institutional contract.

        Args:
            contract_id: InstitutionalContract UUID
            sso_config: SSO configuration dictionary
            created_by: User who set up the SSO

        Returns:
            InstitutionalSSO instance
        """
        try:
            contract = InstitutionalContract.objects.get(id=contract_id)

            # Create or update SSO configuration
            sso, created = InstitutionalSSO.objects.get_or_create(
                contract=contract,
                defaults={
                    'protocol': sso_config['protocol'],
                    'provider_name': sso_config['provider_name'],
                    'sso_url': sso_config['sso_url'],
                    'created_by': created_by
                }
            )

            if not created:
                # Update existing configuration
                for key, value in sso_config.items():
                    if hasattr(sso, key):
                        setattr(sso, key, value)
                sso.save()

            logger.info(f"SSO integration configured for contract {contract.contract_number}")
            return sso

        except InstitutionalContract.DoesNotExist:
            raise ValueError(f"Contract {contract_id} not found")

    @staticmethod
    def get_institutional_analytics(contract_id, date_range_days=30):
        """
        Get comprehensive analytics for an institutional contract.

        Args:
            contract_id: InstitutionalContract UUID
            date_range_days: Number of days to include in analytics

        Returns:
            Dictionary with comprehensive analytics
        """
        try:
            contract = InstitutionalContract.objects.get(id=contract_id)
            end_date = date.today()
            end_date - timedelta(days=date_range_days)

            # Get cached metrics
            metrics = InstitutionalDashboardMetrics.objects.filter(contract=contract).first()
            if not metrics:
                metrics = InstitutionalManagementService.calculate_dashboard_metrics(contract_id)

            # Compile analytics
            analytics = {
                'contract_info': {
                    'contract_number': contract.contract_number,
                    'organization': contract.organization.name,
                    'status': contract.status,
                    'start_date': contract.start_date.isoformat(),
                    'end_date': contract.end_date.isoformat(),
                    'licensed_seats': contract.student_seat_count,
                    'monthly_cost': float(contract.monthly_amount),
                    'annual_cost': float(contract.annual_amount)
                },
                'seat_utilization': {
                    'total_allocated': metrics.total_allocated_seats,
                    'total_active': metrics.total_active_seats,
                    'total_available': metrics.total_available_seats,
                    'utilization_rate': float(metrics.utilization_rate),
                    'pools': []
                },
                'student_metrics': {
                    'total_students': metrics.total_students,
                    'active_students': metrics.active_students,
                    'completed_students': metrics.completed_students,
                    'withdrawn_students': metrics.withdrawn_students,
                    'completion_rate': float(metrics.avg_completion_rate),
                    'avg_progress': float(metrics.avg_progress_percentage)
                },
                'track_assignments': {
                    'mandatory_assignments': metrics.mandatory_assignments,
                    'completed_assignments': metrics.completed_assignments,
                    'overdue_assignments': metrics.overdue_assignments,
                    'completion_rate': (
                        (metrics.completed_assignments / metrics.mandatory_assignments * 100)
                        if metrics.mandatory_assignments > 0 else 0
                    )
                },
                'roi_metrics': {
                    'cost_per_student': float(metrics.cost_per_student),
                    'avg_completion_time_days': metrics.avg_completion_time_days,
                    'certification_rate': float(metrics.certification_rate),
                    'roi_percentage': 150.0  # Placeholder calculation
                },
                'engagement': {
                    'avg_login_frequency': float(metrics.avg_login_frequency),
                    'avg_session_duration': metrics.avg_session_duration_minutes,
                    'active_last_30_days': metrics.last_30_days_activity,
                    'engagement_score': 78.5  # Placeholder
                }
            }

            # Add seat pool details
            for pool in contract.seat_pools.all():
                analytics['seat_utilization']['pools'].append({
                    'name': pool.name,
                    'type': pool.pool_type,
                    'allocated': pool.allocated_seats,
                    'active': pool.active_seats,
                    'available': pool.available_seats,
                    'utilization': float(pool.utilization_rate)
                })

            return analytics

        except InstitutionalContract.DoesNotExist:
            raise ValueError(f"Contract {contract_id} not found")
