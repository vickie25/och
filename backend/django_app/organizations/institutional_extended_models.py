"""
Extended Institutional Models - SSO, Academic Calendar, Track Assignments
"""
from django.db import models
from django.contrib.postgres.fields import ArrayField
import uuid

# Add these fields to the existing InstitutionalContract model
# This would be done via Django migration in practice

class InstitutionalContractExtension(models.Model):
    """
    Extension fields for InstitutionalContract to support additional features.
    In practice, these would be added to the main InstitutionalContract model.
    """
    
    # SSO Integration
    sso_enabled = models.BooleanField(default=False)
    sso_provider_type = models.CharField(
        max_length=50,
        choices=[
            ('saml2', 'SAML 2.0'),
            ('oidc', 'OpenID Connect'),
            ('ldap', 'LDAP'),
        ],
        blank=True
    )
    sso_entity_id = models.CharField(max_length=255, blank=True)
    sso_url = models.URLField(blank=True)
    sso_certificate = models.TextField(blank=True)
    domain_auto_enrollment = models.BooleanField(default=False)
    allowed_domains = ArrayField(
        models.CharField(max_length=255),
        default=list,
        blank=True,
        help_text='Domains allowed for auto-enrollment'
    )
    
    # Academic Calendar Alignment
    academic_calendar_alignment = models.BooleanField(default=False)
    semester_start = models.CharField(
        max_length=20,
        choices=[
            ('january', 'January (Spring)'),
            ('august', 'August (Fall)'),
            ('september', 'September (Fall)'),
            ('june', 'June (Summer)'),
        ],
        blank=True
    )
    quarter_system = models.BooleanField(default=False)
    quarter_start = models.CharField(
        max_length=20,
        choices=[
            ('september', 'Fall Quarter'),
            ('january', 'Winter Quarter'),
            ('march', 'Spring Quarter'),
            ('june', 'Summer Quarter'),
        ],
        blank=True
    )
    
    # Fiscal Year Alignment
    fiscal_year_alignment = models.BooleanField(default=False)
    fiscal_year_start = models.CharField(
        max_length=20,
        choices=[
            ('july', 'July - June'),
            ('january', 'January - December'),
            ('october', 'October - September'),
        ],
        default='july'
    )
    
    # Summer Program Options
    summer_program_enabled = models.BooleanField(default=False)
    summer_pricing_type = models.CharField(
        max_length=20,
        choices=[
            ('reduced_rate', 'Reduced Rate (50% discount)'),
            ('full_rate', 'Full Rate'),
            ('pause_billing', 'Pause Billing'),
        ],
        default='reduced_rate'
    )
    summer_months = ArrayField(
        models.CharField(max_length=10),
        default=lambda: ['june', 'july', 'august'],
        help_text='Months considered as summer period'
    )
    
    class Meta:
        abstract = True


class InstitutionalSeatPool(models.Model):
    """
    Manage seat pools within institutional contracts.
    Allows departments/cohorts to have dedicated seat allocations.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.ForeignKey(
        'InstitutionalContract',
        on_delete=models.CASCADE,
        related_name='seat_pools'
    )
    
    name = models.CharField(max_length=255)
    pool_type = models.CharField(
        max_length=20,
        choices=[
            ('department', 'Department'),
            ('cohort', 'Cohort'),
            ('program', 'Program'),
            ('general', 'General Pool'),
        ],
        default='general'
    )
    
    allocated_seats = models.IntegerField()
    description = models.TextField(blank=True)
    
    # Pool management
    is_active = models.BooleanField(default=True)
    auto_assign = models.BooleanField(
        default=False,
        help_text='Automatically assign students to this pool based on criteria'
    )
    assignment_criteria = models.JSONField(
        default=dict,
        help_text='Criteria for auto-assignment (department, program, etc.)'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'institutional_seat_pools'
        unique_together = ['contract', 'name']
    
    def __str__(self):
        return f"{self.contract.contract_number} - {self.name}"
    
    @property
    def active_students_count(self):
        """Count of active students in this pool"""
        return self.student_assignments.filter(
            student__is_active=True
        ).count()
    
    @property
    def available_seats(self):
        """Available seats in this pool"""
        return self.allocated_seats - self.active_students_count
    
    @property
    def utilization_rate(self):
        """Utilization rate as percentage"""
        if self.allocated_seats == 0:
            return 0.0
        return (self.active_students_count / self.allocated_seats) * 100


class InstitutionalSeatPoolAssignment(models.Model):
    """
    Assign students to specific seat pools within a contract.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pool = models.ForeignKey(
        InstitutionalSeatPool,
        on_delete=models.CASCADE,
        related_name='student_assignments'
    )
    student = models.ForeignKey(
        'InstitutionalStudent',
        on_delete=models.CASCADE,
        related_name='pool_assignments'
    )
    
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='pool_assignments_created'
    )
    
    class Meta:
        db_table = 'institutional_seat_pool_assignments'
        unique_together = ['pool', 'student']
    
    def __str__(self):
        return f"{self.student.user.email} -> {self.pool.name}"


class InstitutionalTrackAssignment(models.Model):
    """
    Mandatory track assignments for institutional students.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.ForeignKey(
        'InstitutionalContract',
        on_delete=models.CASCADE,
        related_name='track_assignments'
    )
    student = models.ForeignKey(
        'InstitutionalStudent',
        on_delete=models.CASCADE,
        related_name='track_assignments'
    )
    
    # Track information (integrate with your existing track system)
    track_id = models.UUIDField()  # Reference to track in curriculum system
    track_name = models.CharField(max_length=255)
    
    # Assignment details
    is_mandatory = models.BooleanField(default=True)
    assigned_at = models.DateTimeField(auto_now_add=True)
    completion_deadline = models.DateField(null=True, blank=True)
    
    # Progress tracking
    status = models.CharField(
        max_length=20,
        choices=[
            ('assigned', 'Assigned'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('overdue', 'Overdue'),
            ('waived', 'Waived'),
        ],
        default='assigned'
    )
    
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    completion_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00
    )
    
    # Department/program filtering
    department_filter = models.CharField(max_length=255, blank=True)
    program_filter = models.CharField(max_length=255, blank=True)
    
    assigned_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='track_assignments_created'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'institutional_track_assignments'
        unique_together = ['student', 'track_id']
        indexes = [
            models.Index(fields=['contract', 'status']),
            models.Index(fields=['completion_deadline', 'status']),
        ]
    
    def __str__(self):
        return f"{self.student.user.email} - {self.track_name}"
    
    @property
    def is_overdue(self):
        """Check if assignment is overdue"""
        if not self.completion_deadline:
            return False
        
        from django.utils import timezone
        return (
            self.status not in ['completed', 'waived'] and
            self.completion_deadline < timezone.now().date()
        )
    
    def mark_completed(self):
        """Mark assignment as completed"""
        from django.utils import timezone
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.completion_percentage = 100.00
        self.save()


class InstitutionalBillingAdjustment(models.Model):
    """
    Academic calendar and seasonal billing adjustments.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.ForeignKey(
        'InstitutionalContract',
        on_delete=models.CASCADE,
        related_name='billing_adjustments'
    )
    
    adjustment_type = models.CharField(
        max_length=30,
        choices=[
            ('summer_discount', 'Summer Program Discount'),
            ('semester_alignment', 'Semester Alignment'),
            ('fiscal_year_alignment', 'Fiscal Year Alignment'),
            ('holiday_pause', 'Holiday Billing Pause'),
            ('custom_adjustment', 'Custom Adjustment'),
        ]
    )
    
    # Adjustment period
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Adjustment details
    adjustment_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text='Percentage adjustment (negative for discounts)'
    )
    fixed_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text='Fixed amount adjustment'
    )
    
    description = models.TextField()
    is_recurring = models.BooleanField(
        default=False,
        help_text='Apply this adjustment annually'
    )
    
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'institutional_billing_adjustments'
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.contract.contract_number} - {self.adjustment_type}"


class InstitutionalSSOConfiguration(models.Model):
    """
    SSO configuration for institutional contracts.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.OneToOneField(
        'InstitutionalContract',
        on_delete=models.CASCADE,
        related_name='sso_config'
    )
    
    # SSO Provider Details
    provider_type = models.CharField(
        max_length=20,
        choices=[
            ('saml2', 'SAML 2.0'),
            ('oidc', 'OpenID Connect'),
            ('ldap', 'LDAP'),
        ]
    )
    
    provider_name = models.CharField(max_length=255)
    entity_id = models.CharField(max_length=255, unique=True)
    sso_url = models.URLField()
    slo_url = models.URLField(blank=True)  # Single Logout URL
    
    # Certificates and Keys
    x509_certificate = models.TextField()
    private_key = models.TextField(blank=True)
    
    # Attribute Mapping
    attribute_mapping = models.JSONField(
        default=dict,
        help_text='Map SSO attributes to user fields'
    )
    
    # Auto-enrollment settings
    domain_auto_enrollment = models.BooleanField(default=False)
    allowed_domains = ArrayField(
        models.CharField(max_length=255),
        default=list,
        blank=True
    )
    
    # User provisioning
    auto_create_users = models.BooleanField(default=True)
    auto_update_users = models.BooleanField(default=True)
    default_user_role = models.CharField(max_length=50, default='student')
    
    # Status
    is_active = models.BooleanField(default=True)
    last_sync = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'institutional_sso_configurations'
    
    def __str__(self):
        return f"{self.contract.contract_number} - {self.provider_name}"