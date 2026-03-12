"""
Academic Discount and Promotional Pricing Models
Implements academic verification and promotional code system
"""
import uuid
from decimal import Decimal
from datetime import datetime, timedelta
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import re

User = get_user_model()


class AcademicDiscount(models.Model):
    """Academic discount verification and management."""
    
    VERIFICATION_METHOD_CHOICES = [
        ('edu_email', 'Educational Email Domain'),
        ('manual_upload', 'Manual Document Upload'),
        ('admin_verified', 'Admin Verified'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Verification'),
        ('verified', 'Verified'),
        ('expired', 'Expired'),
        ('rejected', 'Rejected'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='academic_discount'
    )
    
    # Verification Details
    verification_method = models.CharField(max_length=20, choices=VERIFICATION_METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Educational Institution Info
    institution_name = models.CharField(max_length=255, blank=True)
    institution_domain = models.CharField(max_length=100, blank=True)
    student_email = models.EmailField(help_text='Educational email address')
    
    # Document Upload (for manual verification)
    uploaded_document = models.FileField(
        upload_to='academic_verification/',
        null=True,
        blank=True,
        help_text='Student ID, transcript, or enrollment verification'
    )
    document_type = models.CharField(
        max_length=50,
        choices=[
            ('student_id', 'Student ID Card'),
            ('transcript', 'Official Transcript'),
            ('enrollment_letter', 'Enrollment Verification Letter'),
            ('class_schedule', 'Current Class Schedule'),
        ],
        blank=True
    )
    
    # Discount Configuration
    discount_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('30.00'),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Discount percentage (30% = 30.00)'
    )
    
    # Validity Period
    verified_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    last_reverification_sent = models.DateTimeField(null=True, blank=True)
    
    # Admin Review
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='academic_reviews_completed'
    )
    review_notes = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'academic_discounts'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'expires_at']),
            models.Index(fields=['institution_domain']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.status} ({self.discount_rate}% discount)"
    
    def clean(self):
        """Validate academic discount data."""
        if self.verification_method == 'edu_email':
            if not self.student_email.endswith('.edu'):
                raise ValidationError('Educational email must end with .edu domain')
            self.institution_domain = self.student_email.split('@')[1]
        
        if self.verification_method == 'manual_upload' and not self.uploaded_document:
            raise ValidationError('Document upload required for manual verification')
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    @property
    def is_valid(self):
        """Check if discount is currently valid."""
        return (
            self.status == 'verified' and
            self.expires_at and
            self.expires_at > timezone.now()
        )
    
    @property
    def days_until_expiry(self):
        """Days until discount expires."""
        if not self.expires_at:
            return None
        return (self.expires_at - timezone.now()).days
    
    def verify_discount(self, verified_by=None):
        """Mark discount as verified."""
        self.status = 'verified'
        self.verified_at = timezone.now()
        self.expires_at = timezone.now() + timedelta(days=365)  # 1 year validity
        self.reviewed_by = verified_by
        self.save()
    
    def send_reverification_reminder(self):
        """Send reverification reminder (30 days before expiry)."""
        if self.days_until_expiry == 30:
            # Send email reminder
            self.last_reverification_sent = timezone.now()
            self.save()
            return True
        return False
    
    @classmethod
    def auto_verify_edu_email(cls, user, edu_email):
        """Auto-verify educational email addresses."""
        # Check against known educational domains
        domain = edu_email.split('@')[1]
        
        if domain.endswith('.edu'):
            discount, created = cls.objects.get_or_create(
                user=user,
                defaults={
                    'verification_method': 'edu_email',
                    'student_email': edu_email,
                    'institution_domain': domain,
                    'status': 'verified',
                    'verified_at': timezone.now(),
                    'expires_at': timezone.now() + timedelta(days=365)
                }
            )
            
            if not created and discount.status != 'verified':
                discount.verify_discount()
            
            return discount
        
        return None


class PromotionalCode(models.Model):
    """Promotional pricing codes for marketing campaigns."""
    
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage Discount'),
        ('fixed_amount', 'Fixed Dollar Amount'),
        ('extended_trial', 'Extended Trial Period'),
        ('bonus_credits', 'Bonus Mentorship Credits'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('expired', 'Expired'),
        ('disabled', 'Disabled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Code Configuration
    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text='Promotional code (e.g., CYBER2024, STUDENT50)'
    )
    name = models.CharField(max_length=100, help_text='Internal name for tracking')
    description = models.TextField(help_text='Marketing description of the promotion')
    
    # Discount Configuration
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Percentage (50.00 = 50%) or dollar amount ($10.00)'
    )
    
    # Extended Trial Configuration
    extended_trial_days = models.IntegerField(
        default=0,
        help_text='Additional trial days (for extended_trial type)'
    )
    
    # Bonus Credits Configuration
    bonus_credits = models.IntegerField(
        default=0,
        help_text='Bonus mentorship credits (for bonus_credits type)'
    )
    
    # Validity Period
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField()
    
    # Usage Limits
    max_redemptions = models.IntegerField(
        default=1000,
        help_text='Maximum number of times this code can be used'
    )
    max_redemptions_per_user = models.IntegerField(
        default=1,
        help_text='Maximum redemptions per user'
    )
    current_redemptions = models.IntegerField(default=0)
    
    # Plan Eligibility
    eligible_plans = models.JSONField(
        default=list,
        help_text='List of plan IDs eligible for this promotion (empty = all plans)'
    )\n    new_customers_only = models.BooleanField(\n        default=False,\n        help_text='Only available to users without existing subscriptions'\n    )\n    \n    # Stacking Rules\n    stackable_with_academic = models.BooleanField(\n        default=False,\n        help_text='Can be combined with academic discount'\n    )\n    stackable_with_other_promos = models.BooleanField(\n        default=False,\n        help_text='Can be combined with other promotional codes'\n    )\n    \n    # Status and Metadata\n    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')\n    created_by = models.ForeignKey(\n        User,\n        on_delete=models.SET_NULL,\n        null=True,\n        related_name='created_promo_codes'\n    )\n    created_at = models.DateTimeField(auto_now_add=True)\n    updated_at = models.DateTimeField(auto_now=True)\n    \n    class Meta:\n        db_table = 'promotional_codes'\n        ordering = ['-created_at']\n        indexes = [\n            models.Index(fields=['code', 'status']),\n            models.Index(fields=['valid_from', 'valid_until']),\n            models.Index(fields=['status']),\n        ]\n    \n    def __str__(self):\n        return f\"{self.code} - {self.get_discount_type_display()}\"\n    \n    def clean(self):\n        \"\"\"Validate promotional code data.\"\"\"\n        # Ensure code is uppercase and alphanumeric\n        if self.code:\n            self.code = self.code.upper().strip()\n            if not re.match(r'^[A-Z0-9]+$', self.code):\n                raise ValidationError('Code must contain only uppercase letters and numbers')\n        \n        # Validate discount value based on type\n        if self.discount_type == 'percentage' and self.discount_value > 100:\n            raise ValidationError('Percentage discount cannot exceed 100%')\n        \n        if self.discount_type == 'fixed_amount' and self.discount_value <= 0:\n            raise ValidationError('Fixed amount discount must be greater than 0')\n        \n        # Validate date range\n        if self.valid_until <= self.valid_from:\n            raise ValidationError('Valid until date must be after valid from date')\n    \n    def save(self, *args, **kwargs):\n        self.clean()\n        super().save(*args, **kwargs)\n    \n    @property\n    def is_active(self):\n        \"\"\"Check if promotional code is currently active.\"\"\"\n        now = timezone.now()\n        return (\n            self.status == 'active' and\n            self.valid_from <= now <= self.valid_until and\n            self.current_redemptions < self.max_redemptions\n        )\n    \n    @property\n    def redemptions_remaining(self):\n        \"\"\"Number of redemptions remaining.\"\"\"\n        return max(0, self.max_redemptions - self.current_redemptions)\n    \n    @property\n    def usage_percentage(self):\n        \"\"\"Percentage of maximum redemptions used.\"\"\"\n        if self.max_redemptions == 0:\n            return 0\n        return (self.current_redemptions / self.max_redemptions) * 100\n    \n    def can_be_used_by(self, user, plan_id=None):\n        \"\"\"Check if code can be used by specific user and plan.\"\"\"\n        if not self.is_active:\n            return False, \"Promotional code is not active\"\n        \n        # Check user redemption limit\n        user_redemptions = PromotionalCodeRedemption.objects.filter(\n            code=self,\n            user=user\n        ).count()\n        \n        if user_redemptions >= self.max_redemptions_per_user:\n            return False, \"You have already used this promotional code\"\n        \n        # Check new customer requirement\n        if self.new_customers_only:\n            from .billing_engine import EnhancedSubscription\n            has_subscription = EnhancedSubscription.objects.filter(user=user).exists()\n            if has_subscription:\n                return False, \"This code is only available to new customers\"\n        \n        # Check plan eligibility\n        if self.eligible_plans and plan_id and plan_id not in self.eligible_plans:\n            return False, \"This code is not valid for the selected plan\"\n        \n        return True, \"Code is valid\"\n    \n    def calculate_discount(self, original_amount, billing_cycle='monthly'):\n        \"\"\"Calculate discount amount for given price.\"\"\"\n        if self.discount_type == 'percentage':\n            return original_amount * (self.discount_value / 100)\n        elif self.discount_type == 'fixed_amount':\n            return min(self.discount_value, original_amount)\n        else:\n            return Decimal('0.00')\n    \n    def redeem(self, user, subscription=None):\n        \"\"\"Redeem promotional code for user.\"\"\"\n        can_use, message = self.can_be_used_by(user)\n        if not can_use:\n            raise ValidationError(message)\n        \n        # Create redemption record\n        redemption = PromotionalCodeRedemption.objects.create(\n            code=self,\n            user=user,\n            subscription=subscription,\n            discount_amount=self.calculate_discount(\n                subscription.plan_version.price_monthly if subscription else Decimal('0.00')\n            ) if subscription else Decimal('0.00')\n        )\n        \n        # Update redemption count\n        self.current_redemptions += 1\n        self.save()\n        \n        return redemption


class PromotionalCodeRedemption(models.Model):\n    \"\"\"Track promotional code usage and redemptions.\"\"\"\n    \n    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)\n    code = models.ForeignKey(\n        PromotionalCode,\n        on_delete=models.CASCADE,\n        related_name='redemptions'\n    )\n    user = models.ForeignKey(\n        User,\n        on_delete=models.CASCADE,\n        related_name='promo_redemptions'\n    )\n    subscription = models.ForeignKey(\n        'EnhancedSubscription',\n        on_delete=models.SET_NULL,\n        null=True,\n        blank=True,\n        related_name='promo_redemptions'\n    )\n    \n    # Redemption Details\n    discount_amount = models.DecimalField(\n        max_digits=10,\n        decimal_places=2,\n        default=Decimal('0.00')\n    )\n    original_amount = models.DecimalField(\n        max_digits=10,\n        decimal_places=2,\n        null=True,\n        blank=True\n    )\n    final_amount = models.DecimalField(\n        max_digits=10,\n        decimal_places=2,\n        null=True,\n        blank=True\n    )\n    \n    # Extended Benefits Applied\n    extended_trial_days_applied = models.IntegerField(default=0)\n    bonus_credits_applied = models.IntegerField(default=0)\n    \n    # Metadata\n    redeemed_at = models.DateTimeField(auto_now_add=True)\n    ip_address = models.GenericIPAddressField(null=True, blank=True)\n    user_agent = models.TextField(blank=True)\n    \n    class Meta:\n        db_table = 'promotional_code_redemptions'\n        unique_together = ['code', 'user']  # Prevent duplicate redemptions\n        ordering = ['-redeemed_at']\n        indexes = [\n            models.Index(fields=['code', 'user']),\n            models.Index(fields=['user', 'redeemed_at']),\n            models.Index(fields=['redeemed_at']),\n        ]\n    \n    def __str__(self):\n        return f\"{self.user.email} redeemed {self.code.code}\"\n\n\nclass EnhancedTrialConfiguration(models.Model):\n    \"\"\"Plan-specific trial period configurations.\"\"\"\n    \n    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)\n    plan_version = models.OneToOneField(\n        'SubscriptionPlanVersion',\n        on_delete=models.CASCADE,\n        related_name='trial_config'\n    )\n    \n    # Trial Configuration\n    trial_days = models.IntegerField(\n        default=14,\n        validators=[MinValueValidator(0), MaxValueValidator(365)]\n    )\n    requires_payment_method = models.BooleanField(\n        default=False,\n        help_text='Require credit card for trial (Premium plans)'\n    )\n    auto_convert_trial = models.BooleanField(\n        default=True,\n        help_text='Automatically convert to paid after trial'\n    )\n    \n    # Grace Period Configuration\n    grace_period_days = models.IntegerField(\n        default=3,\n        help_text='Grace period after payment failure (3 for monthly, 7 for annual)'\n    )\n    \n    # Auto-renewal Configuration\n    renewal_attempt_days_before = models.IntegerField(\n        default=1,\n        help_text='Days before period end to attempt renewal'\n    )\n    \n    # Notification Configuration\n    trial_reminder_days = models.JSONField(\n        default=lambda: [7, 3, 1],\n        help_text='Days before trial end to send reminders'\n    )\n    \n    created_at = models.DateTimeField(auto_now_add=True)\n    updated_at = models.DateTimeField(auto_now=True)\n    \n    class Meta:\n        db_table = 'enhanced_trial_configurations'\n    \n    def __str__(self):\n        return f\"{self.plan_version.name} - {self.trial_days} day trial\"\n\n\nclass GracePeriodTracking(models.Model):\n    \"\"\"Track grace periods for failed payments.\"\"\"\n    \n    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)\n    subscription = models.ForeignKey(\n        'EnhancedSubscription',\n        on_delete=models.CASCADE,\n        related_name='grace_periods'\n    )\n    billing_period = models.ForeignKey(\n        'BillingPeriod',\n        on_delete=models.CASCADE,\n        related_name='grace_periods'\n    )\n    \n    # Grace Period Details\n    started_at = models.DateTimeField(auto_now_add=True)\n    ends_at = models.DateTimeField()\n    grace_days = models.IntegerField()\n    \n    # Status\n    is_active = models.BooleanField(default=True)\n    resolved_at = models.DateTimeField(null=True, blank=True)\n    resolution_type = models.CharField(\n        max_length=20,\n        choices=[\n            ('payment_success', 'Payment Successful'),\n            ('grace_expired', 'Grace Period Expired'),\n            ('manual_resolution', 'Manual Resolution'),\n        ],\n        null=True,\n        blank=True\n    )\n    \n    # Notifications\n    notifications_sent = models.JSONField(\n        default=list,\n        help_text='List of notification dates sent'\n    )\n    \n    class Meta:\n        db_table = 'grace_period_tracking'\n        ordering = ['-started_at']\n        indexes = [\n            models.Index(fields=['subscription', 'is_active']),\n            models.Index(fields=['ends_at', 'is_active']),\n        ]\n    \n    def __str__(self):\n        return f\"Grace period for {self.subscription.user.email} - {self.grace_days} days\"\n    \n    @property\n    def days_remaining(self):\n        \"\"\"Days remaining in grace period.\"\"\"\n        if not self.is_active:\n            return 0\n        return max(0, (self.ends_at - timezone.now()).days)\n    \n    @property\n    def hours_remaining(self):\n        \"\"\"Hours remaining in grace period.\"\"\"\n        if not self.is_active:\n            return 0\n        delta = self.ends_at - timezone.now()\n        return max(0, int(delta.total_seconds() / 3600))\n    \n    def resolve(self, resolution_type):\n        \"\"\"Resolve grace period.\"\"\"\n        self.is_active = False\n        self.resolved_at = timezone.now()\n        self.resolution_type = resolution_type\n        self.save()