"""
Financial automation system for invoice generation, payment processing, and dunning management.
Implements automated workflows to achieve >95% payment success rate and 80% recovery rate.
"""
import logging
import uuid
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db import models
from django.template.loader import render_to_string
from django.utils import timezone

try:
    from celery import shared_task
except ImportError:  # pragma: no cover - fallback for dev environments without Celery
    def shared_task(*args, **kwargs):
        """
        Fallback no-op decorator when Celery is not installed.
        Allows importing this module without requiring Celery.
        """
        def decorator(func):
            return func
        return decorator

from .audit import log_financial_action, log_security_event
from .models import Invoice, Payment

User = get_user_model()
logger = logging.getLogger(__name__)


class AutomationRule(models.Model):
    """Configurable automation rules for financial operations."""

    RULE_TYPES = [
        ('invoice_generation', 'Invoice Generation'),
        ('payment_retry', 'Payment Retry'),
        ('dunning_sequence', 'Dunning Sequence'),
        ('late_fee', 'Late Fee Application'),
        ('account_suspension', 'Account Suspension'),
        ('collection_escalation', 'Collection Escalation'),
    ]

    TRIGGER_TYPES = [
        ('time_based', 'Time Based'),
        ('event_based', 'Event Based'),
        ('amount_based', 'Amount Based'),
        ('status_based', 'Status Based'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    rule_type = models.CharField(max_length=30, choices=RULE_TYPES)
    trigger_type = models.CharField(max_length=20, choices=TRIGGER_TYPES)

    # Rule configuration
    conditions = models.JSONField(default=dict, help_text='Rule conditions and parameters')
    actions = models.JSONField(default=dict, help_text='Actions to execute when triggered')

    # Control settings
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0, help_text='Higher numbers = higher priority')
    max_executions = models.IntegerField(null=True, blank=True, help_text='Max times to execute')
    execution_count = models.IntegerField(default=0)

    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_executed = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'automation_rules'
        ordering = ['-priority', 'name']
        indexes = [
            models.Index(fields=['rule_type', 'is_active']),
            models.Index(fields=['trigger_type', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_rule_type_display()})"


class DunningSequence(models.Model):
    """Dunning management for failed payments with automated recovery."""

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='dunning_sequences')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dunning_sequences')

    # Sequence configuration
    sequence_name = models.CharField(max_length=100, default='Standard Dunning')
    total_attempts = models.IntegerField(default=5)
    current_attempt = models.IntegerField(default=0)

    # Status and timing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    started_at = models.DateTimeField(auto_now_add=True)
    next_attempt_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)

    # Recovery tracking
    original_amount = models.DecimalField(max_digits=15, decimal_places=2)
    recovered_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Metadata
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'finance_dunning_sequences'
        indexes = [
            models.Index(fields=['status', 'next_attempt_at']),
            models.Index(fields=['user', 'status']),
        ]

    def __str__(self):
        return f"Dunning for Invoice {self.invoice.invoice_number} - Attempt {self.current_attempt}/{self.total_attempts}"

    @property
    def recovery_rate(self):
        """Calculate recovery rate percentage."""
        if self.original_amount == 0:
            return 0
        return (self.recovered_amount / self.original_amount * 100)


class PaymentRetryAttempt(models.Model):
    """Track individual payment retry attempts."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dunning_sequence = models.ForeignKey(DunningSequence, on_delete=models.CASCADE, related_name='retry_attempts')
    attempt_number = models.IntegerField()

    # Retry configuration
    retry_method = models.CharField(max_length=50, default='automatic')
    amount = models.DecimalField(max_digits=15, decimal_places=2)

    # Timing
    scheduled_at = models.DateTimeField()
    attempted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Results
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    gateway_response = models.JSONField(default=dict)
    error_message = models.TextField(blank=True)

    class Meta:
        db_table = 'finance_payment_retry_attempts'
        ordering = ['attempt_number']
        indexes = [
            models.Index(fields=['status', 'scheduled_at']),
            models.Index(fields=['dunning_sequence', 'attempt_number']),
        ]

    def __str__(self):
        return f"Retry #{self.attempt_number} for {self.dunning_sequence.invoice.invoice_number}"


class FinancialAutomation:
    """Service class for financial automation operations."""

    @staticmethod
    def generate_invoice_automatically(user_id, invoice_type, amount, due_days=30):
        """Generate invoice automatically with 5-minute delivery SLA."""
        try:
            user = User.objects.get(id=user_id)

            # Create invoice
            invoice = Invoice.objects.create(
                user=user,
                type=invoice_type,
                amount=amount,
                total=amount,  # Tax calculation would be added here
                due_date=timezone.now() + timedelta(days=due_days),
                status='draft'
            )

            # Schedule immediate delivery
            deliver_invoice_task.delay(invoice.id)

            # Log the action
            log_financial_action(
                user=None,  # System action
                action='create',
                entity_type='invoice',
                entity_id=invoice.id,
                description=f'Auto-generated {invoice_type} invoice for ${amount}',
                new_values={'invoice_number': invoice.invoice_number, 'amount': float(amount)},
                risk_level='low'
            )

            return invoice

        except Exception as e:
            logger.error(f"Failed to generate invoice automatically: {e}")
            raise

    @staticmethod
    def initiate_dunning_sequence(invoice_id):
        """Start dunning sequence for failed payment."""
        try:
            invoice = Invoice.objects.get(id=invoice_id)

            # Check if dunning sequence already exists
            existing_sequence = DunningSequence.objects.filter(
                invoice=invoice,
                status='active'
            ).first()

            if existing_sequence:
                return existing_sequence

            # Create new dunning sequence
            sequence = DunningSequence.objects.create(
                invoice=invoice,
                user=invoice.user,
                total_attempts=5,  # Configurable
                next_attempt_at=timezone.now() + timedelta(days=1),
                original_amount=invoice.total
            )

            # Schedule first retry attempt
            schedule_payment_retry.delay(sequence.id, 1)

            # Log the action
            log_financial_action(
                user=None,
                action='create',
                entity_type='dunning',
                entity_id=sequence.id,
                description=f'Started dunning sequence for invoice {invoice.invoice_number}',
                risk_level='medium'
            )

            return sequence

        except Exception as e:
            logger.error(f"Failed to initiate dunning sequence: {e}")
            raise

    @staticmethod
    def calculate_payment_success_rate(start_date=None, end_date=None):
        """Calculate payment success rate for monitoring."""
        if not start_date:
            start_date = timezone.now() - timedelta(days=30)
        if not end_date:
            end_date = timezone.now()

        total_payments = Payment.objects.filter(
            created_at__range=[start_date, end_date]
        ).count()

        successful_payments = Payment.objects.filter(
            created_at__range=[start_date, end_date],
            status='success'
        ).count()

        success_rate = (successful_payments / total_payments * 100) if total_payments > 0 else 0

        return {
            'success_rate': success_rate,
            'total_payments': total_payments,
            'successful_payments': successful_payments,
            'failed_payments': total_payments - successful_payments,
            'period_start': start_date,
            'period_end': end_date
        }

    @staticmethod
    def calculate_dunning_recovery_rate(start_date=None, end_date=None):
        """Calculate dunning recovery rate for monitoring."""
        if not start_date:
            start_date = timezone.now() - timedelta(days=30)
        if not end_date:
            end_date = timezone.now()

        sequences = DunningSequence.objects.filter(
            started_at__range=[start_date, end_date]
        )

        total_amount = sequences.aggregate(total=models.Sum('original_amount'))['total'] or Decimal('0')
        recovered_amount = sequences.aggregate(total=models.Sum('recovered_amount'))['total'] or Decimal('0')

        recovery_rate = (recovered_amount / total_amount * 100) if total_amount > 0 else 0

        return {
            'recovery_rate': recovery_rate,
            'total_sequences': sequences.count(),
            'total_amount': total_amount,
            'recovered_amount': recovered_amount,
            'period_start': start_date,
            'period_end': end_date
        }


# Celery tasks for automation
@shared_task
def deliver_invoice_task(invoice_id):
    """Deliver invoice within 5-minute SLA."""
    try:
        invoice = Invoice.objects.get(id=invoice_id)

        # Generate PDF (placeholder - would integrate with PDF generation service)
        pdf_url = f"https://invoices.ongoza.com/{invoice.invoice_number}.pdf"
        invoice.pdf_url = pdf_url

        # Send email
        send_invoice_email(invoice)

        # Update status
        invoice.status = 'sent'
        invoice.save()

        # Log delivery
        log_financial_action(
            user=None,
            action='update',
            entity_type='invoice',
            entity_id=invoice.id,
            description=f'Invoice {invoice.invoice_number} delivered successfully',
            new_values={'status': 'sent', 'pdf_url': pdf_url},
            risk_level='low'
        )

        return True

    except Exception as e:
        logger.error(f"Failed to deliver invoice {invoice_id}: {e}")
        return False


@shared_task
def schedule_payment_retry(dunning_sequence_id, attempt_number):
    """Schedule payment retry attempt."""
    try:
        sequence = DunningSequence.objects.get(id=dunning_sequence_id)

        if sequence.status != 'active' or attempt_number > sequence.total_attempts:
            return False

        # Create retry attempt
        retry_attempt = PaymentRetryAttempt.objects.create(
            dunning_sequence=sequence,
            attempt_number=attempt_number,
            amount=sequence.original_amount - sequence.recovered_amount,
            scheduled_at=timezone.now() + timedelta(hours=24 * attempt_number)  # Exponential backoff
        )

        # Schedule execution
        execute_payment_retry.apply_async(
            args=[retry_attempt.id],
            eta=retry_attempt.scheduled_at
        )

        return True

    except Exception as e:
        logger.error(f"Failed to schedule payment retry: {e}")
        return False


@shared_task
def execute_payment_retry(retry_attempt_id):
    """Execute payment retry attempt."""
    try:
        retry_attempt = PaymentRetryAttempt.objects.get(id=retry_attempt_id)
        sequence = retry_attempt.dunning_sequence

        retry_attempt.status = 'processing'
        retry_attempt.attempted_at = timezone.now()
        retry_attempt.save()

        # Attempt payment (placeholder - would integrate with payment gateway)
        payment_success = attempt_payment_processing(sequence.invoice, retry_attempt.amount)

        if payment_success:
            retry_attempt.status = 'success'
            sequence.recovered_amount += retry_attempt.amount
            sequence.status = 'completed'
            sequence.completed_at = timezone.now()

            # Update invoice status
            sequence.invoice.status = 'paid'
            sequence.invoice.paid_date = timezone.now()
            sequence.invoice.save()

        else:
            retry_attempt.status = 'failed'
            sequence.current_attempt += 1

            # Schedule next attempt if not exhausted
            if sequence.current_attempt < sequence.total_attempts:
                schedule_payment_retry.delay(sequence.id, sequence.current_attempt + 1)
            else:
                sequence.status = 'failed'
                sequence.completed_at = timezone.now()

        retry_attempt.completed_at = timezone.now()
        retry_attempt.save()
        sequence.save()

        # Log the attempt
        log_financial_action(
            user=sequence.user,
            action='payment',
            entity_type='payment',
            entity_id=retry_attempt.id,
            description=f'Payment retry attempt #{retry_attempt.attempt_number} - {retry_attempt.status}',
            new_values={'status': retry_attempt.status, 'amount': float(retry_attempt.amount)},
            risk_level='medium' if retry_attempt.status == 'failed' else 'low'
        )

        return payment_success

    except Exception as e:
        logger.error(f"Failed to execute payment retry: {e}")
        return False


@shared_task
def update_financial_metrics_daily():
    """Daily task to update financial metrics."""
    from .analytics import FinancialAnalytics

    try:
        FinancialAnalytics.update_financial_metrics()

        # Check success rates and alert if below thresholds
        payment_metrics = FinancialAutomation.calculate_payment_success_rate()
        dunning_metrics = FinancialAutomation.calculate_dunning_recovery_rate()

        # Alert if payment success rate < 95%
        if payment_metrics['success_rate'] < 95:
            log_security_event(
                event_type='payment_fraud',
                severity='high',
                description=f'Payment success rate dropped to {payment_metrics["success_rate"]:.1f}%',
                event_data=payment_metrics
            )

        # Alert if dunning recovery rate < 80%
        if dunning_metrics['recovery_rate'] < 80:
            log_security_event(
                event_type='suspicious_transaction',
                severity='medium',
                description=f'Dunning recovery rate dropped to {dunning_metrics["recovery_rate"]:.1f}%',
                event_data=dunning_metrics
            )

        return True

    except Exception as e:
        logger.error(f"Failed to update financial metrics: {e}")
        return False


def send_invoice_email(invoice):
    """Send invoice email to customer."""
    try:
        recipient_email = invoice.user.email if invoice.user else invoice.organization.contact_email

        context = {
            'invoice': invoice,
            'customer_name': invoice.user.get_full_name() if invoice.user else invoice.organization.name,
            'payment_url': f"https://app.ongoza.com/pay/invoice/{invoice.id}"
        }

        html_content = render_to_string('finance/emails/invoice.html', context)
        text_content = render_to_string('finance/emails/invoice.txt', context)

        send_mail(
            subject=f'Invoice {invoice.invoice_number} from Ongoza CyberHub',
            message=text_content,
            from_email='billing@ongoza.com',
            recipient_list=[recipient_email],
            html_message=html_content,
            fail_silently=False
        )

        return True

    except Exception as e:
        logger.error(f"Failed to send invoice email: {e}")
        return False


def attempt_payment_processing(invoice, amount):
    """Attempt to process payment (placeholder for actual payment gateway integration)."""
    # This would integrate with Paystack or other payment gateway
    # For now, return a simulated success/failure
    import random
    return random.choice([True, False])  # 50% success rate for simulation
