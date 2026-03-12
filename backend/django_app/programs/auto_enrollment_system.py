"""
Automated Cohort Enrollment System
Handles payment-to-enrollment automation for the financial module
"""
from django.db import models, transaction
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from celery import shared_task
from datetime import datetime, timedelta
import logging

from programs.models import Cohort, Enrollment
from subscriptions.models import UserSubscription, PaymentTransaction
from users.models import User

logger = logging.getLogger(__name__)


class AutoEnrollmentRule(models.Model):
    """Rules for automatic cohort enrollment based on payment"""
    TRIGGER_CHOICES = [
        ('payment_success', 'Successful Payment'),
        ('subscription_active', 'Subscription Activated'),
        ('trial_converted', 'Trial Converted to Paid'),
    ]
    
    ENROLLMENT_TYPE_CHOICES = [
        ('auto_paid', 'Auto-Enrolled (Paid)'),
        ('auto_scholarship', 'Auto-Enrolled (Scholarship)'),
        ('auto_sponsored', 'Auto-Enrolled (Sponsored)'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Trigger conditions
    trigger_event = models.CharField(max_length=50, choices=TRIGGER_CHOICES)
    subscription_tiers = models.JSONField(
        default=list,
        help_text='List of subscription tiers that trigger enrollment: ["starter", "premium"]'
    )
    
    # Target cohort selection
    target_cohorts = models.ManyToManyField(
        Cohort,
        related_name='auto_enrollment_rules',
        blank=True,
        help_text='Specific cohorts to enroll into'
    )
    cohort_selection_criteria = models.JSONField(
        default=dict,
        help_text='Criteria for automatic cohort selection: {"track_type": "primary", "status": "active"}'
    )
    
    # Enrollment settings
    enrollment_type = models.CharField(max_length=20, choices=ENROLLMENT_TYPE_CHOICES, default='auto_paid')
    priority_order = models.IntegerField(default=0, help_text='Higher numbers = higher priority')
    
    # Capacity management
    respect_seat_limits = models.BooleanField(default=True)
    use_waitlist_when_full = models.BooleanField(default=True)
    
    # Status and metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'auto_enrollment_rules'
        ordering = ['-priority_order', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_trigger_event_display()})"


class EnrollmentAutomationLog(models.Model):
    """Log of automated enrollment actions"""
    STATUS_CHOICES = [
        ('success', 'Successfully Enrolled'),
        ('waitlisted', 'Added to Waitlist'),
        ('failed', 'Enrollment Failed'),
        ('skipped', 'Skipped (Conditions Not Met)'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollment_automation_logs')
    rule = models.ForeignKey(AutoEnrollmentRule, on_delete=models.CASCADE, related_name='automation_logs')
    cohort = models.ForeignKey(Cohort, on_delete=models.CASCADE, related_name='automation_logs', null=True, blank=True)
    
    # Trigger information
    trigger_event = models.CharField(max_length=50)
    trigger_data = models.JSONField(default=dict, help_text='Data that triggered the enrollment')
    
    # Result
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    enrollment = models.ForeignKey(
        Enrollment, 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='automation_logs'
    )
    
    # Details
    processing_time_ms = models.IntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'enrollment_automation_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['rule', 'created_at']),
            models.Index(fields=['trigger_event', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.rule.name} - {self.status}"


class AutoEnrollmentService:
    """Service for handling automated cohort enrollment"""
    
    @staticmethod
    def process_payment_success(payment_transaction: PaymentTransaction):
        """Process successful payment for potential auto-enrollment"""
        if not payment_transaction.subscription:
            return
        
        user = payment_transaction.user
        subscription = payment_transaction.subscription
        
        # Find applicable rules
        applicable_rules = AutoEnrollmentRule.objects.filter(
            is_active=True,
            trigger_event='payment_success',
            subscription_tiers__contains=[subscription.plan.name]
        ).order_by('-priority_order')
        
        for rule in applicable_rules:
            try:
                AutoEnrollmentService._execute_enrollment_rule(
                    user=user,
                    rule=rule,
                    trigger_data={
                        'payment_id': str(payment_transaction.id),
                        'amount': float(payment_transaction.amount),
                        'subscription_tier': subscription.plan.name,
                        'payment_method': payment_transaction.gateway.name if payment_transaction.gateway else 'unknown'
                    }
                )
            except Exception as e:
                logger.error(f"Failed to execute enrollment rule {rule.id} for user {user.id}: {str(e)}")
    
    @staticmethod
    def process_subscription_activation(subscription: UserSubscription):
        """Process subscription activation for potential auto-enrollment"""
        user = subscription.user
        
        # Find applicable rules
        applicable_rules = AutoEnrollmentRule.objects.filter(
            is_active=True,
            trigger_event='subscription_active',
            subscription_tiers__contains=[subscription.plan.name]
        ).order_by('-priority_order')
        
        for rule in applicable_rules:
            try:
                AutoEnrollmentService._execute_enrollment_rule(
                    user=user,
                    rule=rule,
                    trigger_data={
                        'subscription_id': str(subscription.id),
                        'subscription_tier': subscription.plan.name,
                        'activation_date': subscription.current_period_start.isoformat() if subscription.current_period_start else None
                    }
                )
            except Exception as e:
                logger.error(f"Failed to execute enrollment rule {rule.id} for user {user.id}: {str(e)}")
    
    @staticmethod
    def _execute_enrollment_rule(user: User, rule: AutoEnrollmentRule, trigger_data: dict):
        """Execute a specific enrollment rule for a user"""
        start_time = timezone.now()
        
        try:
            # Check if user is already enrolled in any cohorts from this rule
            if rule.target_cohorts.exists():
                existing_enrollments = Enrollment.objects.filter(
                    user=user,
                    cohort__in=rule.target_cohorts.all(),
                    status__in=['active', 'pending_payment']
                )
                if existing_enrollments.exists():
                    AutoEnrollmentService._log_enrollment_attempt(
                        user=user,
                        rule=rule,
                        status='skipped',
                        trigger_data=trigger_data,
                        notes='User already enrolled in target cohort',
                        processing_time_ms=AutoEnrollmentService._calculate_processing_time(start_time)
                    )
                    return
            
            # Select target cohort
            target_cohort = AutoEnrollmentService._select_target_cohort(rule, user)
            if not target_cohort:
                AutoEnrollmentService._log_enrollment_attempt(
                    user=user,
                    rule=rule,
                    status='skipped',
                    trigger_data=trigger_data,
                    notes='No suitable cohort found',
                    processing_time_ms=AutoEnrollmentService._calculate_processing_time(start_time)
                )
                return
            
            # Check capacity
            if rule.respect_seat_limits:
                current_enrollment = target_cohort.enrollments.filter(status='active').count()
                if current_enrollment >= target_cohort.seat_cap:
                    if rule.use_waitlist_when_full:
                        # Add to waitlist
                        from programs.models import Waitlist
                        waitlist_position = Waitlist.objects.filter(cohort=target_cohort, active=True).count() + 1
                        
                        Waitlist.objects.create(
                            cohort=target_cohort,
                            user=user,
                            position=waitlist_position,
                            seat_type=AutoEnrollmentService._get_seat_type_from_enrollment_type(rule.enrollment_type),
                            enrollment_type='director'  # Auto-enrollment is director-initiated
                        )
                        
                        AutoEnrollmentService._log_enrollment_attempt(
                            user=user,
                            rule=rule,
                            cohort=target_cohort,
                            status='waitlisted',
                            trigger_data=trigger_data,
                            notes=f'Added to waitlist at position {waitlist_position}',
                            processing_time_ms=AutoEnrollmentService._calculate_processing_time(start_time)
                        )
                        
                        # Send waitlist notification
                        AutoEnrollmentService._send_waitlist_notification(user, target_cohort, waitlist_position)
                        return
                    else:
                        AutoEnrollmentService._log_enrollment_attempt(
                            user=user,
                            rule=rule,
                            cohort=target_cohort,
                            status='skipped',
                            trigger_data=trigger_data,
                            notes='Cohort at capacity and waitlist not enabled',
                            processing_time_ms=AutoEnrollmentService._calculate_processing_time(start_time)
                        )
                        return
            
            # Create enrollment
            with transaction.atomic():
                enrollment = Enrollment.objects.create(
                    cohort=target_cohort,
                    user=user,
                    enrollment_type='director',  # Auto-enrollment is director-initiated
                    seat_type=AutoEnrollmentService._get_seat_type_from_enrollment_type(rule.enrollment_type),
                    payment_status='paid' if 'paid' in rule.enrollment_type else 'waived',
                    status='active'
                )
                
                AutoEnrollmentService._log_enrollment_attempt(
                    user=user,
                    rule=rule,
                    cohort=target_cohort,
                    status='success',
                    enrollment=enrollment,
                    trigger_data=trigger_data,
                    notes=f'Successfully enrolled in {target_cohort.name}',
                    processing_time_ms=AutoEnrollmentService._calculate_processing_time(start_time)
                )
                
                # Send enrollment confirmation
                AutoEnrollmentService._send_enrollment_confirmation(user, target_cohort, enrollment)
                
        except Exception as e:
            AutoEnrollmentService._log_enrollment_attempt(
                user=user,
                rule=rule,
                status='failed',
                trigger_data=trigger_data,
                error_message=str(e),
                processing_time_ms=AutoEnrollmentService._calculate_processing_time(start_time)
            )
            raise
    
    @staticmethod
    def _select_target_cohort(rule: AutoEnrollmentRule, user: User) -> Cohort:
        """Select the best target cohort for enrollment"""
        # If specific cohorts are defined, use them
        if rule.target_cohorts.exists():
            # Select the first active cohort with available seats
            for cohort in rule.target_cohorts.filter(status='active').order_by('start_date'):
                if not rule.respect_seat_limits:
                    return cohort
                
                current_enrollment = cohort.enrollments.filter(status='active').count()
                if current_enrollment < cohort.seat_cap:
                    return cohort
            
            # If all specific cohorts are full, return the first one for waitlist
            return rule.target_cohorts.filter(status='active').first()
        
        # Use selection criteria
        criteria = rule.cohort_selection_criteria
        cohorts = Cohort.objects.filter(status='active')
        
        # Apply criteria filters
        if 'track_type' in criteria:
            cohorts = cohorts.filter(track__track_type=criteria['track_type'])
        
        if 'program_category' in criteria:
            cohorts = cohorts.filter(track__program__category=criteria['program_category'])
        
        if 'start_date_after' in criteria:
            start_date = datetime.fromisoformat(criteria['start_date_after']).date()
            cohorts = cohorts.filter(start_date__gte=start_date)
        
        # Select cohort with available capacity
        for cohort in cohorts.order_by('start_date'):
            if not rule.respect_seat_limits:
                return cohort
            
            current_enrollment = cohort.enrollments.filter(status='active').count()
            if current_enrollment < cohort.seat_cap:
                return cohort
        
        # Return first cohort for waitlist if all are full
        return cohorts.first()
    
    @staticmethod
    def _get_seat_type_from_enrollment_type(enrollment_type: str) -> str:
        """Convert enrollment type to seat type"""
        mapping = {
            'auto_paid': 'paid',
            'auto_scholarship': 'scholarship',
            'auto_sponsored': 'sponsored',
        }
        return mapping.get(enrollment_type, 'paid')
    
    @staticmethod
    def _calculate_processing_time(start_time) -> int:
        """Calculate processing time in milliseconds"""
        return int((timezone.now() - start_time).total_seconds() * 1000)
    
    @staticmethod
    def _log_enrollment_attempt(user, rule, status, trigger_data, cohort=None, enrollment=None, 
                               error_message='', notes='', processing_time_ms=0):
        """Log an enrollment attempt"""
        EnrollmentAutomationLog.objects.create(
            user=user,
            rule=rule,
            cohort=cohort,
            trigger_event=rule.trigger_event,
            trigger_data=trigger_data,
            status=status,
            enrollment=enrollment,
            processing_time_ms=processing_time_ms,
            error_message=error_message,
            notes=notes
        )
    
    @staticmethod
    def _send_enrollment_confirmation(user: User, cohort: Cohort, enrollment: Enrollment):
        """Send enrollment confirmation email"""
        subject = f"Welcome to {cohort.name}!"
        message = f"""
        Congratulations! You have been automatically enrolled in {cohort.name}.
        
        Cohort Details:
        - Track: {cohort.track.name if cohort.track else 'N/A'}
        - Start Date: {cohort.start_date.strftime('%B %d, %Y')}
        - Mode: {cohort.get_mode_display()}
        
        Your enrollment is now active. You can access your learning materials and track your progress in your student dashboard.
        
        Welcome to the OCH community!
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True
        )
    
    @staticmethod
    def _send_waitlist_notification(user: User, cohort: Cohort, position: int):
        """Send waitlist notification email"""
        subject = f"You're on the waitlist for {cohort.name}"
        message = f"""
        Thank you for your subscription! You have been added to the waitlist for {cohort.name}.
        
        Waitlist Position: #{position}
        
        We'll notify you as soon as a seat becomes available. In the meantime, you can access other learning materials in your dashboard.
        
        Thank you for your patience!
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True
        )


# Celery tasks for async processing
@shared_task
def process_payment_success_enrollment(payment_transaction_id):
    """Async task to process payment success enrollment"""
    try:
        payment_transaction = PaymentTransaction.objects.get(id=payment_transaction_id)
        AutoEnrollmentService.process_payment_success(payment_transaction)
    except PaymentTransaction.DoesNotExist:
        logger.error(f"Payment transaction {payment_transaction_id} not found for enrollment processing")
    except Exception as e:
        logger.error(f"Failed to process payment success enrollment for transaction {payment_transaction_id}: {str(e)}")


@shared_task
def process_subscription_activation_enrollment(subscription_id):
    """Async task to process subscription activation enrollment"""
    try:
        subscription = UserSubscription.objects.get(id=subscription_id)
        AutoEnrollmentService.process_subscription_activation(subscription)
    except UserSubscription.DoesNotExist:
        logger.error(f"Subscription {subscription_id} not found for enrollment processing")
    except Exception as e:
        logger.error(f"Failed to process subscription activation enrollment for subscription {subscription_id}: {str(e)}")


@shared_task
def generate_enrollment_automation_report():
    """Generate daily report of enrollment automation activity"""
    yesterday = timezone.now().date() - timedelta(days=1)
    
    logs = EnrollmentAutomationLog.objects.filter(
        created_at__date=yesterday
    )
    
    stats = {
        'total_attempts': logs.count(),
        'successful_enrollments': logs.filter(status='success').count(),
        'waitlisted': logs.filter(status='waitlisted').count(),
        'failed': logs.filter(status='failed').count(),
        'skipped': logs.filter(status='skipped').count(),
    }
    
    # Send report to admins
    subject = f"Enrollment Automation Report - {yesterday.strftime('%B %d, %Y')}"
    message = f"""
    Daily Enrollment Automation Report
    
    Total Attempts: {stats['total_attempts']}
    Successful Enrollments: {stats['successful_enrollments']}
    Waitlisted: {stats['waitlisted']}
    Failed: {stats['failed']}
    Skipped: {stats['skipped']}
    
    Success Rate: {(stats['successful_enrollments'] / stats['total_attempts'] * 100) if stats['total_attempts'] > 0 else 0:.1f}%
    """
    
    admin_emails = ['admin@och.com']  # Configure admin emails
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=admin_emails,
        fail_silently=True
    )