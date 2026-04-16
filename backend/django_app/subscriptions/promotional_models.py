"""
Supplemental models for the enhanced billing engine.

NOTE: Core models `AcademicDiscount` and `PromotionalCode` live in `subscriptions.models`.
This module defines additional tracking/config entities referenced by the enhanced billing services.
"""

import uuid
from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from django.contrib.auth import get_user_model

User = get_user_model()


class PromotionalCodeRedemption(models.Model):
    """Track promotional code usage and redemptions (enhanced billing)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.ForeignKey(
        'subscriptions.PromotionalCode',
        on_delete=models.CASCADE,
        related_name='enhanced_redemptions',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='enhanced_promo_redemptions',
    )
    subscription = models.ForeignKey(
        'subscriptions.EnhancedSubscription',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='promo_redemptions',
    )

    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
    )
    original_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    final_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )

    extended_trial_days_applied = models.IntegerField(default=0)
    bonus_credits_applied = models.IntegerField(default=0)

    redeemed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        db_table = 'promotional_code_redemptions'
        ordering = ['-redeemed_at']
        indexes = [
            models.Index(fields=['code', 'user']),
            models.Index(fields=['user', 'redeemed_at']),
            models.Index(fields=['redeemed_at']),
        ]

    def __str__(self):
        return f"{self.user.email} redeemed {self.code.code}"


class EnhancedTrialConfiguration(models.Model):
    """Plan-specific trial period configuration for enhanced subscriptions."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan_version = models.OneToOneField(
        'subscriptions.SubscriptionPlanVersion',
        on_delete=models.CASCADE,
        related_name='trial_config',
    )

    trial_days = models.IntegerField(
        default=14,
        validators=[MinValueValidator(0), MaxValueValidator(365)],
    )
    requires_payment_method = models.BooleanField(
        default=False,
        help_text='Require payment method for trial.',
    )
    auto_convert_trial = models.BooleanField(
        default=True,
        help_text='Automatically convert to paid after trial.',
    )

    grace_period_days = models.IntegerField(
        default=3,
        help_text='Grace period after payment failure (3 for monthly, 7 for annual).',
    )
    renewal_attempt_days_before = models.IntegerField(
        default=1,
        help_text='Days before period end to attempt renewal.',
    )
    trial_reminder_days = models.JSONField(
        default=lambda: [7, 3, 1],
        help_text='Days before trial end to send reminders.',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'enhanced_trial_configurations'

    def __str__(self):
        return f"{self.plan_version.name} - {self.trial_days} day trial"


class GracePeriodTracking(models.Model):
    """Track grace periods for failed payments on enhanced subscriptions."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(
        'subscriptions.EnhancedSubscription',
        on_delete=models.CASCADE,
        related_name='grace_periods',
    )
    billing_period = models.ForeignKey(
        'subscriptions.BillingPeriod',
        on_delete=models.CASCADE,
        related_name='grace_periods',
    )

    started_at = models.DateTimeField(auto_now_add=True)
    ends_at = models.DateTimeField()
    grace_days = models.IntegerField()

    is_active = models.BooleanField(default=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_type = models.CharField(
        max_length=20,
        choices=[
            ('payment_success', 'Payment Successful'),
            ('grace_expired', 'Grace Period Expired'),
            ('manual_resolution', 'Manual Resolution'),
        ],
        null=True,
        blank=True,
    )

    notifications_sent = models.JSONField(
        default=list,
        help_text='List of notification dates sent',
    )

    class Meta:
        db_table = 'grace_period_tracking'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['subscription', 'is_active']),
            models.Index(fields=['ends_at', 'is_active']),
        ]

    def __str__(self):
        return f"Grace period for {self.subscription.user.email} - {self.grace_days} days"

    @property
    def days_remaining(self):
        if not self.is_active:
            return 0
        return max(0, (self.ends_at - timezone.now()).days)

    @property
    def hours_remaining(self):
        if not self.is_active:
            return 0
        delta = self.ends_at - timezone.now()
        return max(0, int(delta.total_seconds() / 3600))

    def resolve(self, resolution_type):
        self.is_active = False
        self.resolved_at = timezone.now()
        self.resolution_type = resolution_type
        self.save(update_fields=['is_active', 'resolved_at', 'resolution_type'])

