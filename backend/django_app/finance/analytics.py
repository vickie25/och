"""
Financial analytics and reporting system.
Provides comprehensive dashboards and metrics for all user types.
"""
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from django.db import models
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Invoice, Payment, Transaction, Wallet, Credit, Contract

User = get_user_model()


class FinancialMetric(models.Model):
    """Store calculated financial metrics for performance."""
    
    METRIC_TYPES = [
        ('revenue_total', 'Total Revenue'),
        ('revenue_subscription', 'Subscription Revenue'),
        ('revenue_institution', 'Institution Revenue'),
        ('revenue_employer', 'Employer Revenue'),
        ('revenue_cohort', 'Cohort Revenue'),
        ('payment_success_rate', 'Payment Success Rate'),
        ('churn_rate', 'Churn Rate'),
        ('customer_growth', 'Customer Growth'),
        ('avg_revenue_per_user', 'Average Revenue Per User'),
        ('cohort_utilization', 'Cohort Utilization'),
        ('cost_per_hire', 'Cost Per Hire'),
        ('placement_rate', 'Placement Rate'),
        ('roi_institution', 'Institution ROI'),
        ('roi_employer', 'Employer ROI'),
    ]
    
    PERIOD_TYPES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    metric_type = models.CharField(max_length=30, choices=METRIC_TYPES)
    period_type = models.CharField(max_length=10, choices=PERIOD_TYPES)
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    # Metric values
    value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    count = models.IntegerField(default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Segmentation
    organization_id = models.UUIDField(null=True, blank=True)
    user_segment = models.CharField(max_length=50, blank=True)
    
    # Metadata
    calculated_at = models.DateTimeField(auto_now_add=True)
    is_current = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'financial_metrics'
        unique_together = ['metric_type', 'period_type', 'period_start', 'organization_id', 'user_segment']
        indexes = [
            models.Index(fields=['metric_type', 'period_start']),
            models.Index(fields=['organization_id', 'metric_type']),
            models.Index(fields=['is_current', 'calculated_at']),
        ]
    
    def __str__(self):
        return f"{self.get_metric_type_display()} - {self.period_start.date()}"


class RevenueStream(models.Model):
    """Track revenue by different streams."""
    
    STREAM_TYPES = [
        ('subscription', 'Subscription Revenue'),
        ('institution', 'Institution Contracts'),
        ('employer', 'Employer Partnerships'),
        ('cohort', 'Cohort Enrollments'),
        ('marketplace', 'Marketplace Fees'),
        ('mentorship', 'Mentorship Services'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stream_type = models.CharField(max_length=20, choices=STREAM_TYPES)
    
    # Revenue data
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    
    # Source tracking
    source_id = models.UUIDField(help_text='ID of the source (invoice, contract, etc.)')
    source_type = models.CharField(max_length=20)
    
    # Customer info
    customer_id = models.UUIDField(null=True, blank=True)
    customer_type = models.CharField(max_length=20, blank=True)  # user, organization
    
    # Timing
    recognized_date = models.DateField()
    payment_date = models.DateField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'revenue_streams'
        indexes = [
            models.Index(fields=['stream_type', 'recognized_date']),
            models.Index(fields=['customer_id', 'stream_type']),
            models.Index(fields=['recognized_date']),
        ]
    
    def __str__(self):
        return f"{self.get_stream_type_display()} - ${self.amount}"


class CustomerMetrics(models.Model):
    """Customer-specific financial metrics."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer_id = models.UUIDField()
    customer_type = models.CharField(max_length=20)  # user, organization
    
    # Financial metrics
    total_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    monthly_recurring_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    lifetime_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Engagement metrics
    first_payment_date = models.DateField(null=True, blank=True)
    last_payment_date = models.DateField(null=True, blank=True)
    payment_count = models.IntegerField(default=0)
    
    # Cohort analysis
    cohort_month = models.DateField(help_text='Month when customer first paid')
    months_active = models.IntegerField(default=0)
    
    # Status
    is_active = models.BooleanField(default=True)
    churn_date = models.DateField(null=True, blank=True)
    churn_reason = models.CharField(max_length=100, blank=True)
    
    # Metadata
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'customer_metrics'
        unique_together = ['customer_id', 'customer_type']
        indexes = [
            models.Index(fields=['customer_type', 'is_active']),
            models.Index(fields=['cohort_month']),
            models.Index(fields=['churn_date']),
        ]
    
    def __str__(self):
        return f"Customer {self.customer_id} - ${self.total_revenue}"


class FinancialAnalytics:
    """Service class for financial analytics calculations."""
    
    @staticmethod
    def calculate_revenue_metrics(start_date, end_date, organization_id=None):
        """Calculate revenue metrics for a period."""
        
        # Base queryset
        invoices = Invoice.objects.filter(
            status='paid',
            paid_date__range=[start_date, end_date]
        )
        
        if organization_id:
            invoices = invoices.filter(organization_id=organization_id)
        
        # Revenue by type
        revenue_by_type = invoices.values('type').annotate(
            total=Sum('total'),
            count=Count('id')
        )
        
        # Total revenue
        total_revenue = invoices.aggregate(total=Sum('total'))['total'] or Decimal('0')
        
        # Payment success rate
        all_payments = Payment.objects.filter(
            created_at__range=[start_date, end_date]
        )
        if organization_id:
            all_payments = all_payments.filter(invoice__organization_id=organization_id)
        
        total_payments = all_payments.count()
        successful_payments = all_payments.filter(status='success').count()
        success_rate = (successful_payments / total_payments * 100) if total_payments > 0 else 0
        
        return {
            'total_revenue': total_revenue,
            'revenue_by_type': list(revenue_by_type),
            'payment_success_rate': success_rate,
            'total_invoices': invoices.count(),
            'total_payments': total_payments,
            'successful_payments': successful_payments
        }
    
    @staticmethod
    def calculate_customer_growth(start_date, end_date):
        """Calculate customer growth metrics."""
        
        # New customers (first payment in period)
        new_customers = CustomerMetrics.objects.filter(
            first_payment_date__range=[start_date, end_date]
        ).count()
        
        # Churned customers
        churned_customers = CustomerMetrics.objects.filter(
            churn_date__range=[start_date, end_date]
        ).count()
        
        # Active customers at start and end
        active_start = CustomerMetrics.objects.filter(
            is_active=True,
            first_payment_date__lt=start_date
        ).count()
        
        active_end = CustomerMetrics.objects.filter(
            is_active=True,
            first_payment_date__lte=end_date
        ).count()
        
        # Growth rate
        growth_rate = ((active_end - active_start) / active_start * 100) if active_start > 0 else 0
        
        # Churn rate
        churn_rate = (churned_customers / active_start * 100) if active_start > 0 else 0
        
        return {
            'new_customers': new_customers,
            'churned_customers': churned_customers,
            'active_customers_start': active_start,
            'active_customers_end': active_end,
            'growth_rate': growth_rate,
            'churn_rate': churn_rate
        }
    
    @staticmethod
    def calculate_cohort_analysis(cohort_month):
        """Calculate cohort retention and revenue analysis."""
        
        customers = CustomerMetrics.objects.filter(cohort_month=cohort_month)
        
        # Monthly retention
        retention_data = []
        for month in range(12):  # 12 months
            period_start = cohort_month + timedelta(days=30 * month)
            period_end = period_start + timedelta(days=30)
            
            active_customers = customers.filter(
                Q(churn_date__isnull=True) | Q(churn_date__gt=period_end)
            ).count()
            
            retention_rate = (active_customers / customers.count() * 100) if customers.count() > 0 else 0
            
            retention_data.append({
                'month': month,
                'active_customers': active_customers,
                'retention_rate': retention_rate
            })
        
        return {
            'cohort_month': cohort_month,
            'initial_customers': customers.count(),
            'retention_data': retention_data
        }
    
    @staticmethod
    def calculate_institution_roi(organization_id, start_date, end_date):
        """Calculate ROI metrics for institutions."""
        
        # Revenue from institution
        revenue = Invoice.objects.filter(
            organization_id=organization_id,
            status='paid',
            paid_date__range=[start_date, end_date]
        ).aggregate(total=Sum('total'))['total'] or Decimal('0')
        
        # Costs (simplified - would need more detailed cost tracking)
        # For now, estimate based on student count and platform costs
        
        # Student progress metrics (would integrate with curriculum system)
        # Placement rates (would integrate with marketplace system)
        
        return {
            'organization_id': organization_id,
            'period_revenue': revenue,
            'estimated_costs': revenue * Decimal('0.7'),  # Placeholder
            'roi_percentage': 30,  # Placeholder
            'student_count': 0,  # Would get from enrollment system
            'completion_rate': 0,  # Would get from curriculum system
            'placement_rate': 0,  # Would get from marketplace system
        }

    @staticmethod
    def calculate_subscription_analytics(start_date, end_date):
        """
        OCH student subscription metrics aligned with FinancialDashboardView / list_user_subscriptions.
        Amounts are in KES (plan prices and Paystack ledger).
        """
        from collections import defaultdict

        from subscriptions.models import (
            PaymentTransaction,
            SubscriptionPlan,
            UserSubscription,
        )

        paying_statuses = ['active', 'trial']

        def mrr_for_row(us):
            p = us.plan
            if (
                us.billing_interval == SubscriptionPlan.BILLING_ANNUAL
                and p.price_annual is not None
                and p.price_annual > 0
            ):
                return p.price_annual / Decimal('12')
            return p.price_monthly or Decimal('0')

        paying_qs = UserSubscription.objects.filter(status__in=paying_statuses).select_related(
            'plan'
        )
        mrr_total = Decimal('0')
        plan_stats = defaultdict(
            lambda: {
                'count': 0,
                'mrr_kes': Decimal('0'),
                'plan_name': '',
                'plan_display_name': '',
                'tier': '',
            }
        )
        for us in paying_qs.iterator():
            m = mrr_for_row(us)
            mrr_total += m
            pid = str(us.plan_id)
            p = us.plan
            cat = p.catalog or {}
            disp = (cat.get('display_name') or '').strip() or p.name.replace('_', ' ').title()
            plan_stats[pid]['count'] += 1
            plan_stats[pid]['mrr_kes'] += m
            plan_stats[pid]['plan_name'] = p.name
            plan_stats[pid]['plan_display_name'] = disp
            plan_stats[pid]['tier'] = p.tier

        plan_distribution = sorted(
            [
                {
                    'plan_id': pid,
                    'plan_name': v['plan_name'],
                    'plan_display_name': v['plan_display_name'],
                    'tier': v['tier'],
                    'paying_subscribers': v['count'],
                    'mrr_kes': float(v['mrr_kes']),
                }
                for pid, v in plan_stats.items()
            ],
            key=lambda x: -x['mrr_kes'],
        )

        active_count = UserSubscription.objects.filter(status='active').count()
        trial_count = UserSubscription.objects.filter(status='trial').count()
        past_due_count = UserSubscription.objects.filter(status='past_due').count()
        canceled_total = UserSubscription.objects.filter(status='canceled').count()

        new_in_period = UserSubscription.objects.filter(
            created_at__range=[start_date, end_date]
        ).count()
        canceled_in_period = UserSubscription.objects.filter(
            status='canceled',
            updated_at__range=[start_date, end_date],
        ).count()

        paying_base = max(active_count + trial_count, 1)
        churn_rate_period = (Decimal(canceled_in_period) / Decimal(paying_base)) * Decimal('100')

        tx_completed = PaymentTransaction.objects.filter(
            status='completed',
            created_at__range=[start_date, end_date],
        )
        paystack_revenue_kes = tx_completed.aggregate(t=Sum('amount'))['t'] or Decimal('0')
        paystack_tx_count = tx_completed.count()

        paystack_completed_payments = []
        for tx in tx_completed.select_related('user').order_by('-created_at')[:200]:
            paystack_completed_payments.append(
                {
                    'id': str(tx.id),
                    'amount': float(tx.amount),
                    'currency': tx.currency or 'KES',
                    'created_at': tx.created_at.isoformat(),
                    'processed_at': tx.processed_at.isoformat() if tx.processed_at else None,
                    'user_email': getattr(tx.user, 'email', None) or '',
                    'gateway_transaction_id': (tx.gateway_transaction_id or '')[:120],
                }
            )

        return {
            'currency': 'KES',
            'active_subscribers': active_count,
            'trial_subscribers': trial_count,
            'paying_subscribers': active_count + trial_count,
            'past_due_subscribers': past_due_count,
            'canceled_total': canceled_total,
            'mrr_kes': float(mrr_total),
            'arr_kes_approx': float(mrr_total * Decimal('12')),
            'new_subscriptions_in_period': new_in_period,
            'canceled_subscriptions_in_period': canceled_in_period,
            'subscription_churn_rate_period_pct': float(churn_rate_period),
            'paystack_completed_revenue_kes_period': float(paystack_revenue_kes),
            'paystack_completed_transactions_period': paystack_tx_count,
            'paystack_completed_payments': paystack_completed_payments,
            'plan_distribution': plan_distribution,
        }

    @staticmethod
    def update_financial_metrics():
        """Update all financial metrics (run daily via cron)."""
        
        today = timezone.now().date()
        
        # Calculate daily metrics
        start_date = today
        end_date = today + timedelta(days=1)
        
        revenue_metrics = FinancialAnalytics.calculate_revenue_metrics(start_date, end_date)
        
        # Store metrics
        FinancialMetric.objects.update_or_create(
            metric_type='revenue_total',
            period_type='daily',
            period_start=start_date,
            period_end=end_date,
            defaults={
                'value': revenue_metrics['total_revenue'],
                'count': revenue_metrics['total_invoices'],
                'is_current': True
            }
        )
        
        FinancialMetric.objects.update_or_create(
            metric_type='payment_success_rate',
            period_type='daily',
            period_start=start_date,
            period_end=end_date,
            defaults={
                'percentage': revenue_metrics['payment_success_rate'],
                'count': revenue_metrics['total_payments'],
                'is_current': True
            }
        )
        
        # Calculate monthly metrics
        month_start = today.replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        monthly_revenue = FinancialAnalytics.calculate_revenue_metrics(month_start, month_end)
        monthly_growth = FinancialAnalytics.calculate_customer_growth(month_start, month_end)
        
        FinancialMetric.objects.update_or_create(
            metric_type='revenue_total',
            period_type='monthly',
            period_start=month_start,
            period_end=month_end,
            defaults={
                'value': monthly_revenue['total_revenue'],
                'count': monthly_revenue['total_invoices'],
                'is_current': True
            }
        )
        
        FinancialMetric.objects.update_or_create(
            metric_type='customer_growth',
            period_type='monthly',
            period_start=month_start,
            period_end=month_end,
            defaults={
                'percentage': monthly_growth['growth_rate'],
                'count': monthly_growth['new_customers'],
                'is_current': True
            }
        )
        
        FinancialMetric.objects.update_or_create(
            metric_type='churn_rate',
            period_type='monthly',
            period_start=month_start,
            period_end=month_end,
            defaults={
                'percentage': monthly_growth['churn_rate'],
                'count': monthly_growth['churned_customers'],
                'is_current': True
            }
        )