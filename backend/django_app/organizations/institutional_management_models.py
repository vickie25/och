"""
Institutional Management Models - Complete seat allocation and portal management system.
Extends the institutional billing system with full management capabilities.
"""
import uuid
from datetime import date

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from programs.models import Cohort, Enrollment, Track

from users.models import User

from .institutional_models import InstitutionalContract


class InstitutionalPortalAccess(models.Model):
    """
    Portal access management for institutional administrators.
    Controls who can access the institutional management portal.
    """
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('manager', 'Manager'),
        ('viewer', 'Viewer'),
    ]

    PERMISSION_CHOICES = [
        ('full_access', 'Full Access'),
        ('seat_management', 'Seat Management Only'),
        ('reporting_only', 'Reporting Only'),
        ('student_management', 'Student Management Only'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.ForeignKey(
        InstitutionalContract,
        on_delete=models.CASCADE,
        related_name='portal_access'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='institutional_portal_access'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='viewer')
    permissions = models.JSONField(
        default=list,
        help_text='List of specific permissions: ["seat_management", "reporting", "student_import"]'
    )
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_portal_access'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'institutional_portal_access'
        unique_together = ['contract', 'user']
        indexes = [
            models.Index(fields=['contract', 'is_active']),
            models.Index(fields=['user', 'is_active']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.contract.contract_number} ({self.role})"


class InstitutionalSeatPool(models.Model):
    """
    Seat pool management for institutions.
    Tracks allocated vs active seats across cohorts.
    """
    POOL_TYPE_CHOICES = [
        ('general', 'General Pool'),
        ('department', 'Department Specific'),
        ('program', 'Program Specific'),
        ('cohort', 'Cohort Specific'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.ForeignKey(
        InstitutionalContract,
        on_delete=models.CASCADE,
        related_name='seat_pools'
    )
    name = models.CharField(max_length=200)
    pool_type = models.CharField(max_length=20, choices=POOL_TYPE_CHOICES, default='general')

    # Seat allocation
    allocated_seats = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text='Total seats purchased/allocated to this pool'
    )
    active_seats = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Currently occupied seats'
    )
    reserved_seats = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Seats reserved but not yet assigned'
    )

    # Pool configuration
    department = models.CharField(max_length=200, blank=True)
    allowed_tracks = models.JSONField(
        default=list,
        help_text='List of track IDs that can use this pool'
    )
    allowed_cohorts = models.JSONField(
        default=list,
        help_text='List of cohort IDs that can use this pool'
    )

    # Recycling settings
    auto_recycle = models.BooleanField(
        default=True,
        help_text='Automatically recycle seats when students complete/leave'
    )
    recycle_delay_days = models.IntegerField(
        default=7,
        help_text='Days to wait before recycling a seat'
    )

    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'institutional_seat_pools'
        indexes = [
            models.Index(fields=['contract', 'pool_type']),
            models.Index(fields=['contract', 'department']),
        ]

    def __str__(self):
        return f"{self.name} - {self.contract.organization.name}"

    @property
    def available_seats(self):
        """Calculate available seats in the pool"""
        return self.allocated_seats - self.active_seats - self.reserved_seats

    @property
    def utilization_rate(self):
        """Calculate seat utilization percentage"""
        if self.allocated_seats == 0:
            return 0
        return (self.active_seats / self.allocated_seats) * 100

    def can_allocate_seats(self, count):
        """Check if pool has enough available seats"""
        return self.available_seats >= count

    def allocate_seats(self, count, reserve=False):
        """Allocate seats from the pool"""
        if not self.can_allocate_seats(count):
            raise ValueError(f"Not enough available seats. Available: {self.available_seats}, Requested: {count}")

        if reserve:
            self.reserved_seats += count
        else:
            self.active_seats += count

        self.save()

    def release_seats(self, count, from_reserved=False):
        """Release seats back to the pool"""
        if from_reserved:
            self.reserved_seats = max(0, self.reserved_seats - count)
        else:
            self.active_seats = max(0, self.active_seats - count)

        self.save()

    def reserve_seats(self, count):
        """Reserve seats without allocating them (for invitations)"""
        if not self.can_allocate_seats(count):
            raise ValueError(f"Not enough available seats. Available: {self.available_seats}, Requested: {count}")

        self.reserved_seats += count
        self.save()


class InstitutionalStudentAllocation(models.Model):
    """
    Student seat allocation tracking.
    Links students to specific seat pools and tracks utilization.
    """
    STATUS_CHOICES = [
        ('allocated', 'Allocated'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('completed', 'Completed'),
        ('withdrawn', 'Withdrawn'),
        ('recycled', 'Recycled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seat_pool = models.ForeignKey(
        InstitutionalSeatPool,
        on_delete=models.CASCADE,
        related_name='student_allocations'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='institutional_allocations'
    )
    enrollment = models.OneToOneField(
        Enrollment,
        on_delete=models.CASCADE,
        related_name='seat_allocation',
        null=True,
        blank=True
    )

    # Allocation details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='allocated')
    allocated_at = models.DateTimeField(auto_now_add=True)
    activated_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    recycled_at = models.DateTimeField(null=True, blank=True)

    # Assignment details
    assigned_cohort = models.ForeignKey(
        Cohort,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='institutional_allocations'
    )
    assigned_tracks = models.JSONField(
        default=list,
        help_text='List of mandatory track IDs assigned by institution'
    )
    department = models.CharField(max_length=200, blank=True)

    # Progress tracking
    mandatory_tracks_completed = models.JSONField(default=list)
    completion_deadline = models.DateField(null=True, blank=True)
    progress_last_updated = models.DateTimeField(null=True, blank=True)

    # Metadata
    allocated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='allocated_students'
    )
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'institutional_student_allocations'
        unique_together = ['seat_pool', 'user']
        indexes = [
            models.Index(fields=['seat_pool', 'status']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['assigned_cohort', 'status']),
            models.Index(fields=['completion_deadline']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.seat_pool.name} ({self.status})"

    def activate(self):
        """Activate the student allocation"""
        if self.status == 'allocated':
            self.status = 'active'
            self.activated_at = timezone.now()
            self.save()

    def complete(self):
        """Mark allocation as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()

        # Auto-recycle if enabled
        if self.seat_pool.auto_recycle:
            self.recycle()

    def recycle(self):
        """Recycle the seat allocation"""
        self.status = 'recycled'
        self.recycled_at = timezone.now()
        self.save()

        # Release seat back to pool
        self.seat_pool.release_seats(1)


class InstitutionalBulkImport(models.Model):
    """
    Bulk student import tracking.
    Manages CSV uploads and processing status.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('partial', 'Partially Completed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.ForeignKey(
        InstitutionalContract,
        on_delete=models.CASCADE,
        related_name='bulk_imports'
    )
    seat_pool = models.ForeignKey(
        InstitutionalSeatPool,
        on_delete=models.CASCADE,
        related_name='bulk_imports'
    )

    # Import details
    filename = models.CharField(max_length=255)
    file_size = models.IntegerField()
    total_records = models.IntegerField(default=0)
    processed_records = models.IntegerField(default=0)
    successful_records = models.IntegerField(default=0)
    failed_records = models.IntegerField(default=0)

    # Processing status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Results
    import_results = models.JSONField(
        default=dict,
        help_text='Detailed results: {created: [], updated: [], failed: [], duplicates: []}'
    )
    error_log = models.JSONField(
        default=list,
        help_text='List of errors encountered during processing'
    )

    # Configuration
    import_settings = models.JSONField(
        default=dict,
        help_text='Import settings: {auto_enroll: bool, send_emails: bool, default_cohort: id}'
    )

    # Metadata
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'institutional_bulk_imports'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['contract', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"Import {self.filename} - {self.contract.organization.name}"


class InstitutionalTrackAssignment(models.Model):
    """
    Mandatory track assignments for institutional students.
    Enforces curriculum requirements set by institutions.
    """
    ASSIGNMENT_TYPE_CHOICES = [
        ('mandatory', 'Mandatory'),
        ('recommended', 'Recommended'),
        ('optional', 'Optional'),
    ]

    STATUS_CHOICES = [
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('overdue', 'Overdue'),
        ('waived', 'Waived'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.ForeignKey(
        InstitutionalContract,
        on_delete=models.CASCADE,
        related_name='track_assignments'
    )
    student_allocation = models.ForeignKey(
        InstitutionalStudentAllocation,
        on_delete=models.CASCADE,
        related_name='track_assignments'
    )
    track = models.ForeignKey(
        Track,
        on_delete=models.CASCADE,
        related_name='institutional_assignments'
    )

    # Assignment details
    assignment_type = models.CharField(max_length=20, choices=ASSIGNMENT_TYPE_CHOICES, default='mandatory')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='assigned')

    # Deadlines and progress
    assigned_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Progress tracking
    progress_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    last_activity = models.DateTimeField(null=True, blank=True)

    # Department/customization
    department = models.CharField(max_length=200, blank=True)
    custom_requirements = models.JSONField(
        default=dict,
        help_text='Custom completion requirements for this assignment'
    )

    # Metadata
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assigned_tracks'
    )
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'institutional_track_assignments'
        unique_together = ['student_allocation', 'track']
        indexes = [
            models.Index(fields=['contract', 'assignment_type']),
            models.Index(fields=['status', 'due_date']),
            models.Index(fields=['track', 'status']),
        ]

    def __str__(self):
        return f"{self.student_allocation.user.email} - {self.track.name} ({self.assignment_type})"

    @property
    def is_overdue(self):
        """Check if assignment is overdue"""
        if not self.due_date or self.status in ['completed', 'waived']:
            return False
        return date.today() > self.due_date

    def mark_started(self):
        """Mark assignment as started"""
        if self.status == 'assigned':
            self.status = 'in_progress'
            self.started_at = timezone.now()
            self.save()

    def mark_completed(self):
        """Mark assignment as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.progress_percentage = 100
        self.save()


class InstitutionalSSO(models.Model):
    """
    SSO configuration for institutional contracts.
    Supports SAML 2.0 and OpenID Connect integration.
    """
    PROTOCOL_CHOICES = [
        ('saml2', 'SAML 2.0'),
        ('oidc', 'OpenID Connect'),
        ('oauth2', 'OAuth 2.0'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('testing', 'Testing'),
        ('active', 'Active'),
        ('disabled', 'Disabled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.OneToOneField(
        InstitutionalContract,
        on_delete=models.CASCADE,
        related_name='sso_config'
    )

    # SSO Configuration
    protocol = models.CharField(max_length=20, choices=PROTOCOL_CHOICES)
    provider_name = models.CharField(max_length=200)
    entity_id = models.CharField(max_length=500, blank=True)
    sso_url = models.URLField()
    slo_url = models.URLField(blank=True, help_text='Single Logout URL')

    # Certificates and keys
    x509_cert = models.TextField(blank=True, help_text='X.509 Certificate')
    private_key = models.TextField(blank=True, help_text='Private Key (encrypted)')

    # Domain-based auto-enrollment
    auto_enrollment_domains = models.JSONField(
        default=list,
        help_text='List of email domains for auto-enrollment: ["university.edu", "school.org"]'
    )
    auto_enrollment_enabled = models.BooleanField(default=False)
    default_seat_pool = models.ForeignKey(
        InstitutionalSeatPool,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='Default seat pool for auto-enrolled users'
    )

    # User provisioning
    user_provisioning_enabled = models.BooleanField(default=False)
    deprovisioning_enabled = models.BooleanField(default=False)
    attribute_mapping = models.JSONField(
        default=dict,
        help_text='SAML/OIDC attribute mapping: {email: "mail", first_name: "givenName"}'
    )

    # Status and metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    last_sync = models.DateTimeField(null=True, blank=True)
    sync_errors = models.JSONField(default=list)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'institutional_sso'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['auto_enrollment_enabled']),
        ]

    def __str__(self):
        return f"SSO {self.provider_name} - {self.contract.organization.name}"


class InstitutionalDashboardMetrics(models.Model):
    """
    Cached dashboard metrics for institutional contracts.
    Updated daily for performance optimization.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.OneToOneField(
        InstitutionalContract,
        on_delete=models.CASCADE,
        related_name='dashboard_metrics'
    )

    # Seat utilization metrics
    total_allocated_seats = models.IntegerField(default=0)
    total_active_seats = models.IntegerField(default=0)
    total_available_seats = models.IntegerField(default=0)
    utilization_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Student metrics
    total_students = models.IntegerField(default=0)
    active_students = models.IntegerField(default=0)
    completed_students = models.IntegerField(default=0)
    withdrawn_students = models.IntegerField(default=0)

    # Progress metrics
    avg_completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    avg_progress_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    students_on_track = models.IntegerField(default=0)
    students_behind = models.IntegerField(default=0)

    # Track assignment metrics
    mandatory_assignments = models.IntegerField(default=0)
    completed_assignments = models.IntegerField(default=0)
    overdue_assignments = models.IntegerField(default=0)

    # ROI metrics
    cost_per_student = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    avg_completion_time_days = models.IntegerField(default=0)
    certification_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Engagement metrics
    avg_login_frequency = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    avg_session_duration_minutes = models.IntegerField(default=0)
    last_30_days_activity = models.IntegerField(default=0)

    # Metadata
    calculated_at = models.DateTimeField(auto_now=True)
    calculation_duration_seconds = models.IntegerField(default=0)

    class Meta:
        db_table = 'institutional_dashboard_metrics'
        indexes = [
            models.Index(fields=['calculated_at']),
        ]

    def __str__(self):
        return f"Metrics - {self.contract.organization.name}"


class InstitutionalAcademicCalendar(models.Model):
    """
    Academic calendar alignment for institutional contracts.
    Supports semester, quarter, and fiscal year alignment.
    """
    CALENDAR_TYPE_CHOICES = [
        ('semester', 'Semester System'),
        ('quarter', 'Quarter System'),
        ('trimester', 'Trimester System'),
        ('fiscal', 'Fiscal Year'),
        ('custom', 'Custom Calendar'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.OneToOneField(
        InstitutionalContract,
        on_delete=models.CASCADE,
        related_name='academic_calendar'
    )

    # Calendar configuration
    calendar_type = models.CharField(max_length=20, choices=CALENDAR_TYPE_CHOICES)
    academic_year_start = models.DateField()
    academic_year_end = models.DateField()

    # Periods definition
    periods = models.JSONField(
        default=list,
        help_text='List of academic periods: [{name: "Fall 2024", start: "2024-09-01", end: "2024-12-15"}]'
    )

    # Break periods
    break_periods = models.JSONField(
        default=list,
        help_text='List of break periods: [{name: "Winter Break", start: "2024-12-16", end: "2025-01-15"}]'
    )

    # Summer program settings
    SUMMER_BILLING_MODE_CHOICES = [
        ('full_rate', 'Full Rate'),
        ('reduced_rate', 'Reduced Rate'),
        ('pause', 'Pause Billing'),
    ]
    summer_program_enabled = models.BooleanField(default=False)
    summer_billing_mode = models.CharField(
        max_length=20,
        choices=SUMMER_BILLING_MODE_CHOICES,
        default='full_rate',
        help_text='How to handle billing during summer break months'
    )
    summer_discount_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text='Percentage discount for summer-only programs'
    )

    # Billing alignment
    billing_aligned_to_calendar = models.BooleanField(default=False)
    billing_period_mapping = models.JSONField(
        default=dict,
        help_text='Mapping of billing periods to academic periods'
    )

    # Metadata
    timezone = models.CharField(max_length=50, default='UTC')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'institutional_academic_calendars'

    def __str__(self):
        return f"{self.calendar_type} - {self.contract.organization.name}"

    def get_current_period(self):
        """Get the current academic period"""
        today = date.today()
        for period in self.periods:
            start_date = date.fromisoformat(period['start'])
            end_date = date.fromisoformat(period['end'])
            if start_date <= today <= end_date:
                return period
        return None

    def is_break_period(self, check_date=None):
        """Check if given date (or today) is in a break period"""
        if not check_date:
            check_date = date.today()

        for break_period in self.break_periods:
            start_date = date.fromisoformat(break_period['start'])
            end_date = date.fromisoformat(break_period['end'])
            if start_date <= check_date <= end_date:
                return True
        return False


class InstitutionalInvitation(models.Model):
    """
    Email-based student invitations for institutional contracts.
    Allows pre-reserving seats for students who haven't joined yet.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('expired', 'Expired'),
        ('revoked', 'Revoked'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.ForeignKey(
        InstitutionalContract,
        on_delete=models.CASCADE,
        related_name='student_invitations'
    )
    seat_pool = models.ForeignKey(
        InstitutionalSeatPool,
        on_delete=models.CASCADE,
        related_name='invitations'
    )

    # Invitation details
    email = models.EmailField(db_index=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=200, blank=True)

    # Assignment configuration (applied when accepted)
    assigned_cohort = models.ForeignKey(
        Cohort,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='institutional_invitations'
    )
    assigned_tracks = models.JSONField(default=list, blank=True)

    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    token = models.CharField(max_length=255, unique=True, db_index=True)
    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sent_institutional_invitations'
    )
    invited_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    accepted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='accepted_institutional_invitations'
    )

    # Metadata
    reminder_count = models.IntegerField(default=0)
    last_reminder_sent = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'institutional_invitations'
        unique_together = ['contract', 'email', 'status']
        indexes = [
            models.Index(fields=['contract', 'status']),
            models.Index(fields=['email', 'status']),
            models.Index(fields=['token']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"Invitation {self.email} - {self.contract.organization.name} ({self.status})"

    def save(self, *args, **kwargs):
        # Generate token if not set
        if not self.token:
            import secrets
            self.token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        """Check if invitation has expired"""
        if self.status != 'pending':
            return False
        return timezone.now() > self.expires_at

    @property
    def days_until_expiry(self):
        """Calculate days until invitation expires"""
        if self.status != 'pending':
            return 0
        delta = self.expires_at - timezone.now()
        return max(0, delta.days)

    def accept(self, user):
        """Mark invitation as accepted by a user"""
        self.status = 'accepted'
        self.accepted_at = timezone.now()
        self.accepted_by = user
        self.save()

        # Release reserved seat and create actual allocation
        self.seat_pool.release_seats(1, from_reserved=True)

    def revoke(self):
        """Revoke the invitation and release reserved seat"""
        self.status = 'revoked'
        self.save()

        # Release reserved seat
        self.seat_pool.release_seats(1, from_reserved=True)

    def expire(self):
        """Mark invitation as expired and release reserved seat"""
        if self.status == 'pending':
            self.status = 'expired'
            self.save()

            # Release reserved seat
            self.seat_pool.release_seats(1, from_reserved=True)


class InstitutionalSeatForfeiture(models.Model):
    """
    Record seat forfeitures at cohort start when unused capacity is not assigned by deadline.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.ForeignKey(
        InstitutionalContract,
        on_delete=models.CASCADE,
        related_name='seat_forfeitures'
    )
    seat_pool = models.ForeignKey(
        InstitutionalSeatPool,
        on_delete=models.CASCADE,
        related_name='seat_forfeitures'
    )
    cohort = models.ForeignKey(
        Cohort,
        on_delete=models.CASCADE,
        related_name='institutional_seat_forfeitures'
    )
    forfeited_seats = models.IntegerField(validators=[MinValueValidator(1)])
    forfeited_at = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=255, default='Unused seats forfeited at cohort start')

    class Meta:
        db_table = 'institutional_seat_forfeitures'
        unique_together = ['seat_pool', 'cohort']
        indexes = [
            models.Index(fields=['contract', 'forfeited_at']),
            models.Index(fields=['cohort', 'forfeited_at']),
        ]

    def __str__(self):
        return f"Forfeit {self.forfeited_seats} seats - {self.contract.contract_number} - {self.cohort.name}"
