"""
Real-time Financial Monitoring Service
Tracks payment success rates, invoice delivery, and compliance in real-time
"""
from django.utils import timezone
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from celery import shared_task
from datetime import datetime, timedelta
import logging

from .dynamic_content_models import (
    PaymentSuccessRateTracking, InvoiceDeliveryTracking, 
    DunningRecoveryTracking, PCIComplianceMonitoring
)
from subscriptions.models import PaymentTransaction, SubscriptionInvoice, UserSubscription

logger = logging.getLogger(__name__)


class RealTimeFinancialMonitor:
    """Real-time monitoring service for financial metrics"""
    
    @staticmethod
    def track_payment_attempt(payment_transaction: PaymentTransaction):
        """Track a payment attempt in real-time"""
        today = timezone.now().date()
        current_hour = timezone.now().hour
        
        # Get or create tracking record for today
        tracking, created = PaymentSuccessRateTracking.objects.get_or_create(
            date=today,
            hour=None,  # Daily tracking
            defaults={
                'total_attempts': 0,
                'successful_payments': 0,
                'failed_payments': 0,
                'gateway_breakdown': {},
                'threshold_percentage': 95.00,
            }
        )
        
        # Update totals
        tracking.total_attempts += 1
        
        if payment_transaction.status == 'completed':
            tracking.successful_payments += 1
        else:
            tracking.failed_payments += 1
        
        # Update gateway breakdown
        gateway_name = payment_transaction.gateway.name if payment_transaction.gateway else 'unknown'
        if gateway_name not in tracking.gateway_breakdown:
            tracking.gateway_breakdown[gateway_name] = {'success': 0, 'failed': 0}
        
        if payment_transaction.status == 'completed':
            tracking.gateway_breakdown[gateway_name]['success'] += 1
        else:
            tracking.gateway_breakdown[gateway_name]['failed'] += 1
        
        # Calculate success rate
        if tracking.total_attempts > 0:
            tracking.success_rate_percentage = (tracking.successful_payments / tracking.total_attempts) * 100
        
        # Check if below threshold
        if tracking.success_rate_percentage < tracking.threshold_percentage and not tracking.below_threshold_alert_sent:
            RealTimeFinancialMonitor._send_payment_success_rate_alert(tracking)
            tracking.below_threshold_alert_sent = True
        
        tracking.save()
        
        # Also track hourly
        RealTimeFinancialMonitor._track_hourly_payment(payment_transaction, today, current_hour)
    
    @staticmethod
    def _track_hourly_payment(payment_transaction: PaymentTransaction, date, hour):
        """Track payment at hourly granularity"""
        tracking, created = PaymentSuccessRateTracking.objects.get_or_create(
            date=date,
            hour=hour,
            defaults={
                'total_attempts': 0,
                'successful_payments': 0,
                'failed_payments': 0,
                'gateway_breakdown': {},
                'threshold_percentage': 95.00,
            }
        )
        
        tracking.total_attempts += 1
        
        if payment_transaction.status == 'completed':
            tracking.successful_payments += 1
        else:
            tracking.failed_payments += 1
        
        # Update gateway breakdown
        gateway_name = payment_transaction.gateway.name if payment_transaction.gateway else 'unknown'
        if gateway_name not in tracking.gateway_breakdown:
            tracking.gateway_breakdown[gateway_name] = {'success': 0, 'failed': 0}
        
        if payment_transaction.status == 'completed':
            tracking.gateway_breakdown[gateway_name]['success'] += 1
        else:
            tracking.gateway_breakdown[gateway_name]['failed'] += 1
        
        # Calculate success rate
        if tracking.total_attempts > 0:
            tracking.success_rate_percentage = (tracking.successful_payments / tracking.total_attempts) * 100
        
        tracking.save()
    
    @staticmethod
    def track_invoice_delivery(invoice: SubscriptionInvoice, transaction_completed_at: datetime):
        """Track invoice delivery timing for SLA compliance"""
        invoice_generated_at = invoice.created_at
        invoice_sent_at = invoice.sent_at or timezone.now()
        
        # Calculate timing metrics
        generation_time = (invoice_generated_at - transaction_completed_at).total_seconds()
        delivery_time = (invoice_sent_at - invoice_generated_at).total_seconds() if invoice.sent_at else None
        total_time = (invoice_sent_at - transaction_completed_at).total_seconds()
        
        # Check SLA compliance (5 minutes = 300 seconds)
        meets_5min_sla = total_time <= 300
        sla_breach_reason = ''
        
        if not meets_5min_sla:
            if generation_time > 180:  # 3 minutes for generation
                sla_breach_reason = 'Slow invoice generation'
            elif delivery_time and delivery_time > 120:  # 2 minutes for delivery
                sla_breach_reason = 'Slow email delivery'
            else:
                sla_breach_reason = 'Overall process delay'
        
        # Create tracking record
        InvoiceDeliveryTracking.objects.create(
            invoice=invoice,
            transaction_completed_at=transaction_completed_at,
            invoice_generated_at=invoice_generated_at,
            invoice_sent_at=invoice_sent_at,
            generation_time_seconds=int(generation_time),
            delivery_time_seconds=int(delivery_time) if delivery_time else None,
            total_time_seconds=int(total_time),
            meets_5min_sla=meets_5min_sla,
            sla_breach_reason=sla_breach_reason,
        )
        
        # Send alert if SLA is breached
        if not meets_5min_sla:
            RealTimeFinancialMonitor._send_invoice_sla_breach_alert(invoice, total_time, sla_breach_reason)
    
    @staticmethod
    def start_dunning_cycle(subscription: UserSubscription, failed_payment_amount: float):
        """Start a new dunning cycle for failed payment"""
        # Check if there's already an active cycle
        existing_cycle = DunningRecoveryTracking.objects.filter(
            subscription=subscription,
            status='active'
        ).first()
        
        if existing_cycle:
            # Update existing cycle
            existing_cycle.total_attempts += 1
            existing_cycle.timeline.append({
                'date': timezone.now().isoformat(),
                'action': 'payment_retry',
                'result': 'failed',
                'amount': failed_payment_amount,
            })
            existing_cycle.save()
        else:
            # Create new dunning cycle
            DunningRecoveryTracking.objects.create(
                subscription=subscription,
                cycle_start_date=timezone.now(),
                total_attempts=1,
                email_reminders_sent=0,
                payment_retries=1,
                status='active',
                timeline=[{
                    'date': timezone.now().isoformat(),
                    'action': 'cycle_started',
                    'result': 'payment_failed',
                    'amount': failed_payment_amount,
                }]
            )
    
    @staticmethod
    def record_dunning_recovery(subscription: UserSubscription, recovered_amount: float):
        """Record successful dunning recovery"""
        cycle = DunningRecoveryTracking.objects.filter(
            subscription=subscription,
            status='active'
        ).first()
        
        if cycle:
            cycle.status = 'recovered'
            cycle.recovered_at = timezone.now()
            cycle.recovery_amount = recovered_amount
            cycle.cycle_end_date = timezone.now()
            cycle.timeline.append({
                'date': timezone.now().isoformat(),
                'action': 'payment_recovered',
                'result': 'success',
                'amount': recovered_amount,
            })
            cycle.save()
            
            # Check overall recovery rate
            RealTimeFinancialMonitor._check_dunning_recovery_rate()
    
    @staticmethod
    def record_pci_violation(violation_type: str, severity: str, description: str, 
                           affected_systems: list, detection_method: str):
        """Record a PCI compliance violation"""
        PCIComplianceMonitoring.objects.create(
            violation_type=violation_type,
            severity=severity,
            description=description,
            affected_systems=affected_systems,
            potential_impact=RealTimeFinancialMonitor._assess_violation_impact(violation_type, severity),
            detection_method=detection_method,
            status='open',
        )
        
        # Send immediate alert for critical violations
        if severity == 'critical':
            RealTimeFinancialMonitor._send_critical_pci_violation_alert(
                violation_type, description, affected_systems
            )
    
    @staticmethod
    def _send_payment_success_rate_alert(tracking: PaymentSuccessRateTracking):
        """Send alert when payment success rate drops below threshold"""
        subject = f"ALERT: Payment Success Rate Below {tracking.threshold_percentage}%"
        message = f"""
        Payment Success Rate Alert
        
        Current Success Rate: {tracking.success_rate_percentage:.1f}%
        Target Threshold: {tracking.threshold_percentage}%
        
        Today's Statistics:
        - Total Attempts: {tracking.total_attempts}
        - Successful: {tracking.successful_payments}
        - Failed: {tracking.failed_payments}
        
        Gateway Breakdown:
        {RealTimeFinancialMonitor._format_gateway_breakdown(tracking.gateway_breakdown)}
        
        Immediate action required to investigate and resolve payment issues.
        """
        
        admin_emails = ['admin@och.com', 'finance@och.com']
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=admin_emails,
            fail_silently=True
        )
    
    @staticmethod
    def _send_invoice_sla_breach_alert(invoice: SubscriptionInvoice, total_time: float, reason: str):
        """Send alert when invoice delivery SLA is breached"""
        subject = f"ALERT: Invoice Delivery SLA Breach - {invoice.invoice_number}"
        message = f"""
        Invoice Delivery SLA Breach
        
        Invoice: {invoice.invoice_number}
        User: {invoice.user.email}
        Total Delivery Time: {total_time/60:.1f} minutes
        SLA Target: 5 minutes
        
        Breach Reason: {reason}
        
        Please investigate the invoice delivery process to prevent future breaches.
        """
        
        admin_emails = ['admin@och.com', 'finance@och.com']
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=admin_emails,
            fail_silently=True
        )
    
    @staticmethod
    def _send_critical_pci_violation_alert(violation_type: str, description: str, affected_systems: list):
        """Send immediate alert for critical PCI violations"""
        subject = "CRITICAL: PCI Compliance Violation Detected"
        message = f"""
        CRITICAL PCI COMPLIANCE VIOLATION
        
        Violation Type: {violation_type}
        Severity: CRITICAL
        
        Description: {description}
        
        Affected Systems: {', '.join(affected_systems)}
        
        IMMEDIATE ACTION REQUIRED:
        1. Investigate the violation immediately
        2. Implement containment measures
        3. Document remediation steps
        4. Report to compliance team
        
        This violation must be resolved within 24 hours to maintain PCI compliance.
        """
        
        admin_emails = ['admin@och.com', 'security@och.com', 'compliance@och.com']
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=admin_emails,
            fail_silently=True
        )
    
    @staticmethod
    def _check_dunning_recovery_rate():
        """Check if dunning recovery rate meets 80% target"""
        # Check last 90 days
        ninety_days_ago = timezone.now() - timedelta(days=90)
        
        cycles = DunningRecoveryTracking.objects.filter(
            cycle_start_date__gte=ninety_days_ago
        )
        
        total_cycles = cycles.count()
        recovered_cycles = cycles.filter(status='recovered').count()
        
        if total_cycles > 0:
            recovery_rate = (recovered_cycles / total_cycles) * 100
            
            if recovery_rate < 80.0:
                RealTimeFinancialMonitor._send_dunning_recovery_rate_alert(recovery_rate, total_cycles, recovered_cycles)
    
    @staticmethod
    def _send_dunning_recovery_rate_alert(recovery_rate: float, total_cycles: int, recovered_cycles: int):
        """Send alert when dunning recovery rate is below target"""
        subject = f"ALERT: Dunning Recovery Rate Below 80% Target"
        message = f"""
        Dunning Recovery Rate Alert
        
        Current Recovery Rate: {recovery_rate:.1f}%
        Target: 80%
        
        Last 90 Days Statistics:
        - Total Cycles: {total_cycles}
        - Recovered: {recovered_cycles}
        - Failed: {total_cycles - recovered_cycles}
        
        Please review dunning processes and strategies to improve recovery rates.
        """
        
        admin_emails = ['admin@och.com', 'finance@och.com']
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=admin_emails,
            fail_silently=True
        )
    
    @staticmethod
    def _format_gateway_breakdown(breakdown: dict) -> str:
        """Format gateway breakdown for email"""
        lines = []
        for gateway, stats in breakdown.items():
            total = stats['success'] + stats['failed']
            rate = (stats['success'] / total * 100) if total > 0 else 0
            lines.append(f"- {gateway.title()}: {rate:.1f}% ({stats['success']}/{total})")
        return '\n'.join(lines)
    
    @staticmethod
    def _assess_violation_impact(violation_type: str, severity: str) -> str:
        """Assess the potential impact of a PCI violation"""
        impact_map = {
            'data_storage': 'Potential exposure of cardholder data',
            'transmission': 'Risk of data interception during transmission',
            'access_control': 'Unauthorized access to payment systems',
            'logging': 'Inability to detect and respond to security incidents',
            'encryption': 'Data may be accessible in plain text',
            'network_security': 'Network-based attacks on payment infrastructure',
        }
        
        base_impact = impact_map.get(violation_type, 'Unknown security risk')
        
        if severity == 'critical':
            return f"CRITICAL: {base_impact}. Immediate remediation required."
        elif severity == 'high':
            return f"HIGH: {base_impact}. Urgent attention needed."
        else:
            return f"{severity.upper()}: {base_impact}"


# Celery tasks for periodic monitoring
@shared_task
def daily_financial_metrics_summary():
    """Generate daily summary of financial metrics"""
    yesterday = timezone.now().date() - timedelta(days=1)
    
    # Payment success rate
    payment_tracking = PaymentSuccessRateTracking.objects.filter(
        date=yesterday,
        hour__isnull=True
    ).first()
    
    # Invoice delivery metrics
    invoice_deliveries = InvoiceDeliveryTracking.objects.filter(
        transaction_completed_at__date=yesterday
    )
    
    # PCI violations
    pci_violations = PCIComplianceMonitoring.objects.filter(
        detected_at__date=yesterday
    )
    
    # Generate summary report
    subject = f"Daily Financial Metrics Summary - {yesterday.strftime('%B %d, %Y')}"
    message = f"""
    Daily Financial Metrics Summary
    
    Payment Success Rate:
    - Success Rate: {payment_tracking.success_rate_percentage:.1f}% if payment_tracking else 'No data'}
    - Total Attempts: {payment_tracking.total_attempts if payment_tracking else 0}
    - Target Met: {'Yes' if payment_tracking and payment_tracking.success_rate_percentage >= 95 else 'No'}
    
    Invoice Delivery:
    - Total Invoices: {invoice_deliveries.count()}
    - SLA Compliant: {invoice_deliveries.filter(meets_5min_sla=True).count()}
    - Average Delivery Time: {invoice_deliveries.aggregate(avg=models.Avg('total_time_seconds'))['avg'] or 0:.0f} seconds
    
    PCI Compliance:
    - New Violations: {pci_violations.count()}
    - Critical Violations: {pci_violations.filter(severity='critical').count()}
    - Open Violations: {PCIComplianceMonitoring.objects.filter(status='open').count()}
    
    Dashboard: http://localhost:3000/dashboard/admin/billing
    """
    
    admin_emails = ['admin@och.com', 'finance@och.com']
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=admin_emails,
        fail_silently=True
    )


@shared_task
def cleanup_old_tracking_data():
    """Clean up old tracking data beyond retention period"""
    # Keep 2 years of payment tracking data
    two_years_ago = timezone.now().date() - timedelta(days=730)
    PaymentSuccessRateTracking.objects.filter(date__lt=two_years_ago).delete()
    
    # Keep 1 year of invoice delivery data
    one_year_ago = timezone.now().date() - timedelta(days=365)
    InvoiceDeliveryTracking.objects.filter(transaction_completed_at__date__lt=one_year_ago).delete()
    
    # Keep 7 years of PCI compliance data (regulatory requirement)
    seven_years_ago = timezone.now().date() - timedelta(days=2555)
    PCIComplianceMonitoring.objects.filter(detected_at__date__lt=seven_years_ago).delete()
    
    logger.info("Completed cleanup of old financial tracking data")