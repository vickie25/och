"""
Employer Contract System Models
Implements Stream C: Employer/Organization Talent Supply Contracts
"""
import uuid
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from organizations.models import Organization

User = get_user_model()


class EmployerContractTier(models.Model):
    """Retainer tier definitions with candidate access guarantees."""

    TIER_CHOICES = [
        ('starter', 'Starter'),
        ('growth', 'Growth'),
        ('enterprise', 'Enterprise'),
        ('custom', 'Custom')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tier_name = models.CharField(max_length=20, choices=TIER_CHOICES, unique=True)
    display_name = models.CharField(max_length=100)
    monthly_retainer = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='Monthly retainer fee in USD'
    )
    candidates_per_quarter = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text='Candidate access limit per quarter (null = unlimited)'
    )
    placement_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='Per-candidate successful placement fee'
    )
    placement_fee_cap_multiplier = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=2.0,
        help_text='Monthly placement fee cap as multiple of retainer'
    )
    dedicated_account_manager = models.BooleanField(default=False)
    priority_matching = models.BooleanField(default=False)
    custom_reports = models.BooleanField(default=False)
    exclusive_pipeline_access = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'employer_contract_tiers'
        ordering = ['monthly_retainer']

    def __str__(self):
        return f"{self.display_name} - ${self.monthly_retainer}/month"

    def get_monthly_placement_fee_cap(self):
        """Calculate monthly placement fee cap."""
        return self.monthly_retainer * self.placement_fee_cap_multiplier


class EmployerContract(models.Model):
    """Employer talent supply contracts with complete lifecycle management."""

    STATUS_CHOICES = [
        ('proposal', 'Proposal - Sales team prepared contract proposal'),
        ('negotiation', 'Negotiation - Employer reviewing and requesting modifications'),
        ('signed', 'Signed - Both parties executed contract'),
        ('active', 'Active - Contract period active, employer has platform access'),
        ('renewal', 'Renewal - At contract end, renewal being negotiated'),
        ('terminated', 'Terminated - Contract ended or terminated'),
        ('suspended', 'Suspended - Temporarily suspended due to issues')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='employer_contracts'
    )
    tier = models.ForeignKey(
        EmployerContractTier,
        on_delete=models.PROTECT,
        related_name='contracts'
    )

    # Contract Details
    contract_number = models.CharField(max_length=50, unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='proposal', db_index=True)

    # Contract Terms
    start_date = models.DateField()
    end_date = models.DateField()
    monthly_retainer = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Locked-in monthly retainer (may differ from tier if custom)'
    )
    placement_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Locked-in placement fee per successful candidate'
    )
    candidates_per_quarter = models.IntegerField(
        null=True,
        blank=True,
        help_text='Candidate access limit (null = unlimited)'
    )

    # SLA Terms
    time_to_shortlist_days = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1)],
        help_text='SLA: Days to provide first candidate shortlist'
    )
    minimum_quality_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=75.0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Minimum candidate quality score percentage'
    )
    minimum_mission_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=70.0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Minimum mission completion score percentage'
    )
    replacement_guarantee_days = models.IntegerField(
        default=60,
        validators=[MinValueValidator(1)],
        help_text='Days for replacement guarantee (60 standard, 90 enterprise)'
    )
    target_placement_success_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=70.0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Target placement success rate percentage'
    )

    # Exclusivity Terms
    has_exclusivity = models.BooleanField(default=False)
    exclusivity_premium_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=50.0,
        help_text='Exclusivity premium percentage (typically 50%)'
    )
    exclusivity_duration_months = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text='Exclusivity duration in months'
    )
    exclusivity_window_hours = models.IntegerField(
        default=48,
        validators=[MinValueValidator(1)],
        help_text='Exclusive candidate presentation window in hours'
    )

    # Performance Tracking
    current_placement_success_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Current actual placement success rate'
    )
    performance_discount_eligible = models.BooleanField(default=False)
    performance_review_due = models.DateField(null=True, blank=True)

    # Contract Management
    auto_renew = models.BooleanField(default=False)
    renewal_notice_days = models.IntegerField(
        default=60,
        validators=[MinValueValidator(1)],
        help_text='Days notice required for renewal'
    )
    assigned_account_manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_employer_contracts',
        help_text='Dedicated account manager for Growth/Enterprise tiers'
    )

    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_employer_contracts'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    signed_at = models.DateTimeField(null=True, blank=True)
    activated_at = models.DateTimeField(null=True, blank=True)
    terminated_at = models.DateTimeField(null=True, blank=True)

    # Contract Terms and Notes
    special_terms = models.JSONField(
        default=dict,
        blank=True,
        help_text='Custom contract terms and conditions'
    )
    internal_notes = models.TextField(blank=True)

    class Meta:
        db_table = 'employer_contracts'
        indexes = [
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['status', 'start_date']),
            models.Index(fields=['end_date']),
            models.Index(fields=['performance_review_due']),
        ]

    def __str__(self):
        return f"{self.contract_number} - {self.organization.name} ({self.status})"

    def is_active(self):
        """Check if contract is currently active."""
        return (
            self.status == 'active' and
            self.start_date <= timezone.now().date() <= self.end_date
        )

    def get_effective_monthly_retainer(self):
        """Get effective monthly retainer including exclusivity premium."""
        base_retainer = self.monthly_retainer
        if self.has_exclusivity:
            premium = base_retainer * (self.exclusivity_premium_rate / 100)
            return base_retainer + premium
        return base_retainer

    def get_monthly_placement_fee_cap(self):
        """Calculate monthly placement fee cap."""
        return self.get_effective_monthly_retainer() * 2

    def get_quarterly_candidate_usage(self, quarter_start=None):
        """Get candidate usage for current or specified quarter."""
        if not quarter_start:
            now = timezone.now().date()
            quarter_start = datetime(now.year, ((now.month - 1) // 3) * 3 + 1, 1).date()

        quarter_end = quarter_start + timedelta(days=90)  # Approximate quarter

        return CandidatePresentation.objects.filter(
            contract=self,
            presented_at__date__range=[quarter_start, quarter_end]
        ).count()

    def can_access_more_candidates(self):
        """Check if employer can access more candidates this quarter."""
        if not self.candidates_per_quarter:  # Unlimited
            return True

        current_usage = self.get_quarterly_candidate_usage()
        return current_usage < self.candidates_per_quarter

    @staticmethod
    def generate_contract_number():
        """Generate unique contract number."""
        year = timezone.now().year
        last_contract = EmployerContract.objects.filter(
            contract_number__startswith=f'EMP-{year}-'
        ).order_by('-contract_number').first()

        if last_contract:
            last_num = int(last_contract.contract_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        return f'EMP-{year}-{new_num:04d}'


class CandidateRequirement(models.Model):
    """Employer candidate requirements and job specifications."""

    PRIORITY_CHOICES = [
        ('low', 'Low Priority'),
        ('medium', 'Medium Priority'),
        ('high', 'High Priority'),
        ('urgent', 'Urgent')
    ]

    STATUS_CHOICES = [
        ('open', 'Open - Actively sourcing candidates'),
        ('shortlisted', 'Shortlisted - Candidates provided'),
        ('interviewing', 'Interviewing - In interview process'),
        ('filled', 'Filled - Position filled'),
        ('cancelled', 'Cancelled - Requirement cancelled'),
        ('on_hold', 'On Hold - Temporarily paused')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.ForeignKey(
        EmployerContract,
        on_delete=models.CASCADE,
        related_name='candidate_requirements'
    )

    # Requirement Details
    title = models.CharField(max_length=255)
    description = models.TextField()
    required_skills = models.JSONField(default=list, help_text='Required skills and technologies')
    preferred_skills = models.JSONField(default=list, help_text='Preferred/nice-to-have skills')
    minimum_tier_level = models.CharField(
        max_length=20,
        default='tier_1',
        help_text='Minimum curriculum tier completion required'
    )
    required_tracks = models.JSONField(
        default=list,
        help_text='Required curriculum tracks (defender, grc, etc.)'
    )

    # Position Details
    location = models.CharField(max_length=255, blank=True)
    remote_allowed = models.BooleanField(default=False)
    employment_type = models.CharField(
        max_length=20,
        choices=[
            ('full_time', 'Full Time'),
            ('part_time', 'Part Time'),
            ('contract', 'Contract'),
            ('internship', 'Internship')
        ],
        default='full_time'
    )
    salary_min = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    salary_max = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    salary_currency = models.CharField(max_length=3, default='USD')

    # Requirement Management
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open', db_index=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    positions_count = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    positions_filled = models.IntegerField(default=0, validators=[MinValueValidator(0)])

    # SLA Tracking
    submitted_at = models.DateTimeField(auto_now_add=True)
    shortlist_due_at = models.DateTimeField()
    first_shortlist_sent_at = models.DateTimeField(null=True, blank=True)
    sla_met = models.BooleanField(null=True, blank=True)

    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_requirements'
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'candidate_requirements'
        indexes = [
            models.Index(fields=['contract', 'status']),
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['shortlist_due_at']),
        ]

    def __str__(self):
        return f"{self.title} - {self.contract.organization.name}"

    def save(self, *args, **kwargs):
        if not self.shortlist_due_at:
            # Set SLA due date based on contract terms
            self.shortlist_due_at = timezone.now() + timedelta(
                days=self.contract.time_to_shortlist_days
            )
        super().save(*args, **kwargs)

    def is_sla_overdue(self):
        """Check if SLA is overdue."""
        return (
            not self.first_shortlist_sent_at and
            timezone.now() > self.shortlist_due_at
        )

    def get_remaining_positions(self):
        """Get number of positions still to be filled."""
        return self.positions_count - self.positions_filled


class CandidatePresentation(models.Model):
    """Tracks candidates presented to employers."""

    STATUS_CHOICES = [
        ('presented', 'Presented - Candidate shown to employer'),
        ('reviewed', 'Reviewed - Employer reviewed candidate'),
        ('shortlisted', 'Shortlisted - Added to employer shortlist'),
        ('interviewed', 'Interviewed - Interview conducted'),
        ('rejected', 'Rejected - Employer rejected candidate'),
        ('hired', 'Hired - Candidate successfully hired'),
        ('withdrawn', 'Withdrawn - Candidate withdrew from process')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.ForeignKey(
        EmployerContract,
        on_delete=models.CASCADE,
        related_name='candidate_presentations'
    )
    requirement = models.ForeignKey(
        CandidateRequirement,
        on_delete=models.CASCADE,
        related_name='candidate_presentations'
    )
    candidate = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='employer_presentations',
        help_text='Student/candidate being presented'
    )

    # Presentation Details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='presented', db_index=True)
    match_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Algorithm-calculated match score'
    )
    quality_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Candidate quality assessment score'
    )
    mission_completion_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Mission completion score'
    )

    # Exclusivity Tracking
    is_exclusive = models.BooleanField(default=False)
    exclusivity_expires_at = models.DateTimeField(null=True, blank=True)

    # Timeline Tracking
    presented_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    shortlisted_at = models.DateTimeField(null=True, blank=True)
    interviewed_at = models.DateTimeField(null=True, blank=True)
    decision_at = models.DateTimeField(null=True, blank=True)

    # Employer Feedback
    employer_rating = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Employer rating of candidate (1-5 stars)'
    )
    employer_notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)

    class Meta:
        db_table = 'candidate_presentations'
        unique_together = ['requirement', 'candidate']
        indexes = [
            models.Index(fields=['contract', 'status']),
            models.Index(fields=['candidate', 'status']),
            models.Index(fields=['presented_at']),
            models.Index(fields=['exclusivity_expires_at']),
        ]

    def __str__(self):
        return f"{self.candidate.email} -> {self.requirement.title} ({self.status})"

    def is_exclusivity_active(self):
        """Check if exclusivity window is still active."""
        return (
            self.is_exclusive and
            self.exclusivity_expires_at and
            timezone.now() < self.exclusivity_expires_at
        )


class SuccessfulPlacement(models.Model):
    """Tracks successful candidate placements and fee billing."""

    STATUS_CHOICES = [
        ('placed', 'Placed - Candidate started employment'),
        ('confirmed', 'Confirmed - Completed probation period'),
        ('fee_billed', 'Fee Billed - Placement fee invoiced'),
        ('fee_paid', 'Fee Paid - Placement fee received'),
        ('replaced', 'Replaced - Candidate left, replacement provided'),
        ('guarantee_expired', 'Guarantee Expired - Guarantee period ended')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    presentation = models.OneToOneField(
        CandidatePresentation,
        on_delete=models.CASCADE,
        related_name='successful_placement'
    )

    # Placement Details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='placed', db_index=True)
    start_date = models.DateField(help_text='Candidate employment start date')
    salary_offered = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    salary_currency = models.CharField(max_length=3, default='USD')

    # Fee Calculation
    placement_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Calculated placement fee for this hire'
    )
    fee_billed_at = models.DateTimeField(null=True, blank=True)
    fee_paid_at = models.DateTimeField(null=True, blank=True)

    # Guarantee Tracking
    guarantee_end_date = models.DateField(help_text='End of replacement guarantee period')
    guarantee_used = models.BooleanField(default=False)
    replacement_count = models.IntegerField(default=0)

    # Performance Tracking
    candidate_left_date = models.DateField(null=True, blank=True)
    left_within_guarantee = models.BooleanField(null=True, blank=True)
    replacement_provided_at = models.DateTimeField(null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'successful_placements'
        indexes = [
            models.Index(fields=['status', 'start_date']),
            models.Index(fields=['guarantee_end_date']),
            models.Index(fields=['fee_billed_at']),
        ]

    def __str__(self):
        return f"Placement: {self.presentation.candidate.email} -> {self.presentation.requirement.title}"

    def is_guarantee_active(self):
        """Check if replacement guarantee is still active."""
        return (
            timezone.now().date() <= self.guarantee_end_date and
            not self.guarantee_used
        )

    def calculate_days_employed(self):
        """Calculate days candidate was employed."""
        end_date = self.candidate_left_date or timezone.now().date()
        return (end_date - self.start_date).days


class ContractPerformanceMetrics(models.Model):
    """Tracks contract performance metrics for annual reviews."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.ForeignKey(
        EmployerContract,
        on_delete=models.CASCADE,
        related_name='performance_metrics'
    )

    # Reporting Period
    period_start = models.DateField()
    period_end = models.DateField()

    # Candidate Metrics
    candidates_presented = models.IntegerField(default=0)
    candidates_shortlisted = models.IntegerField(default=0)
    candidates_interviewed = models.IntegerField(default=0)
    candidates_hired = models.IntegerField(default=0)

    # Performance Calculations
    placement_success_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='(Hired / Presented) * 100'
    )
    shortlist_conversion_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='(Shortlisted / Presented) * 100'
    )
    interview_conversion_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='(Interviewed / Shortlisted) * 100'
    )
    hire_conversion_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='(Hired / Interviewed) * 100'
    )

    # SLA Metrics
    avg_time_to_shortlist = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Average days to provide first shortlist'
    )
    sla_compliance_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Percentage of requirements meeting SLA'
    )

    # Financial Metrics
    total_retainer_paid = models.DecimalField(max_digits=12, decimal_places=2)
    total_placement_fees = models.DecimalField(max_digits=12, decimal_places=2)
    total_contract_value = models.DecimalField(max_digits=12, decimal_places=2)

    # Quality Metrics
    avg_candidate_quality_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    avg_employer_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Average employer rating of presented candidates'
    )

    # Guarantee Metrics
    placements_within_guarantee = models.IntegerField(default=0)
    guarantee_claims = models.IntegerField(default=0)
    replacements_provided = models.IntegerField(default=0)

    # Performance Assessment
    performance_grade = models.CharField(
        max_length=2,
        choices=[
            ('A+', 'Exceptional (>90% success rate)'),
            ('A', 'Excellent (80-90% success rate)'),
            ('B', 'Good (70-79% success rate)'),
            ('C', 'Acceptable (60-69% success rate)'),
            ('D', 'Below Standard (50-59% success rate)'),
            ('F', 'Poor (<50% success rate)')
        ],
        null=True,
        blank=True
    )
    discount_eligible = models.BooleanField(default=False)
    requires_improvement_plan = models.BooleanField(default=False)

    # Metadata
    calculated_at = models.DateTimeField(auto_now_add=True)
    calculated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='calculated_performance_metrics'
    )

    class Meta:
        db_table = 'contract_performance_metrics'
        unique_together = ['contract', 'period_start', 'period_end']
        indexes = [
            models.Index(fields=['contract', 'period_end']),
            models.Index(fields=['placement_success_rate']),
            models.Index(fields=['performance_grade']),
        ]

    def __str__(self):
        return f"Performance: {self.contract.contract_number} ({self.period_start} - {self.period_end})"


class ReplacementGuarantee(models.Model):
    """Tracks replacement guarantee claims and fulfillment."""

    STATUS_CHOICES = [
        ('claimed', 'Claimed - Employer requested replacement'),
        ('approved', 'Approved - Replacement request approved'),
        ('sourcing', 'Sourcing - Finding replacement candidates'),
        ('presented', 'Presented - Replacement candidates provided'),
        ('fulfilled', 'Fulfilled - Replacement successfully placed'),
        ('expired', 'Expired - Guarantee period expired'),
        ('denied', 'Denied - Replacement request denied')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    original_placement = models.ForeignKey(
        SuccessfulPlacement,
        on_delete=models.CASCADE,
        related_name='replacement_guarantees'
    )

    # Guarantee Details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='claimed', db_index=True)
    claim_reason = models.TextField(help_text='Reason for replacement request')
    candidate_left_date = models.DateField()
    days_employed = models.IntegerField(help_text='Days original candidate was employed')

    # Replacement Process
    replacement_due_date = models.DateField(help_text='Date replacement candidates due (10 business days)')
    replacement_candidates_provided = models.IntegerField(default=0)
    replacement_placement = models.ForeignKey(
        'SuccessfulPlacement',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replaced_placements',
        help_text='New placement that replaced original'
    )

    # Timeline
    claimed_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    fulfilled_at = models.DateTimeField(null=True, blank=True)

    # Internal Processing
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_replacement_guarantees'
    )
    internal_notes = models.TextField(blank=True)

    class Meta:
        db_table = 'replacement_guarantees'
        indexes = [
            models.Index(fields=['status', 'replacement_due_date']),
            models.Index(fields=['claimed_at']),
        ]

    def __str__(self):
        return f"Replacement: {self.original_placement.presentation.candidate.email} ({self.status})"

    def is_overdue(self):
        """Check if replacement is overdue."""
        return (
            self.status in ['claimed', 'approved', 'sourcing'] and
            timezone.now().date() > self.replacement_due_date
        )
