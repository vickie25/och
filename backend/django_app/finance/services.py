"""
Financial Services - Complete Implementation
Handles analytics, reporting, compliance, and automation
"""

from django.db import models, transaction
from django.utils import timezone
from django.db.models import Sum, Avg, Count, Q
from decimal import Decimal
from datetime import datetime, timedelta, date
import logging
from typing import Dict, List, Optional, Tuple
import json

from .models import *
from .dashboard_models import *
from subscriptions.models import UserSubscription, PaymentTransaction
from programs.models import Enrollment
from cohorts.models import CohortPayment

logger = logging.getLogger(__name__)


class DynamicPricingService:
    """Service for dynamic pricing calculations using PricingTier model"""
    
    @classmethod
    def get_institution_rate(cls, student_count: int, currency: str = 'USD') -> Optional[Decimal]:
        """Get per-student rate for given student count using dynamic pricing"""
        tiers = PricingTier.get_active_tiers('institution', currency)
        
        for tier in tiers:
            if tier.is_quantity_in_range(student_count):
                return tier.price_per_unit
        
        # Fallback to hardcoded rates if no dynamic tiers found
        from .institution_invoicing import PER_STUDENT_MONTHLY_USD
        if currency == 'USD' and student_count <= 50:
            return PER_STUDENT_MONTHLY_USD.get('tier_1_50')
        elif currency == 'USD' and student_count <= 200:
            return PER_STUDENT_MONTHLY_USD.get('tier_51_200')
        elif currency == 'USD' and student_count <= 500:
            return PER_STUDENT_MONTHLY_USD.get('tier_201_500')
        elif currency == 'USD':
            return PER_STUDENT_MONTHLY_USD.get('tier_500_plus')
        
        return None
    
    @classmethod
    def get_employer_rate(cls, plan: str, currency: str = 'USD') -> Optional[Decimal]:
        """Get monthly retainer for employer plan using dynamic pricing"""
        tiers = PricingTier.get_active_tiers('employer', currency)
        
        for tier in tiers:
            if tier.name == plan:
                return tier.price_per_unit
        
        # Fallback to hardcoded rates if no dynamic tiers found
        from .employer_invoicing import EMPLOYER_RETAINER_USD
        if currency == 'USD':
            return EMPLOYER_RETAINER_USD.get(plan)
        
        return None
    
    @classmethod
    def calculate_institution_invoice(cls, contract, billing_cycle: str = 'monthly') -> Optional[Decimal]:
        """Calculate institution contract invoice amount using dynamic pricing"""
        student_count = int(contract.seat_cap or 0)
        if student_count < 1:
            return None
        
        rate = cls.get_institution_rate(student_count)
        if not rate:
            return None
        
        monthly_total = rate * student_count
        
        if billing_cycle == 'quarterly':
            return monthly_total * 3
        elif billing_cycle == 'annual':
            # Apply annual discount from dynamic pricing or fallback
            tiers = PricingTier.get_active_tiers('institution', 'USD')
            annual_discount = Decimal('0')
            
            for tier in tiers:
                if tier.is_quantity_in_range(student_count):
                    annual_discount = tier.annual_discount_percent
                    break
            
            annual_total = monthly_total * 12
            discount_amount = annual_total * (annual_discount / 100)
            return (annual_total - discount_amount).quantize(Decimal('0.01'))
        else:
            return monthly_total
    
    @classmethod
    def calculate_employer_invoice(cls, contract) -> Optional[Decimal]:
        """Calculate employer contract invoice amount using dynamic pricing"""
        plan = contract.employer_plan
        if not plan:
            return None
        
        if plan == 'custom':
            return contract.total_value or Decimal('0')
        
        rate = cls.get_employer_rate(plan)
        if not rate:
            return None
        
        return rate
    
    @classmethod
    def update_pricing_record(cls, tier_id: str, new_price: Decimal, new_discount: Decimal = None, 
                             reason: str = '', changed_by_user=None):
        """Update pricing and track history"""
        with transaction.atomic():
            tier = PricingTier.objects.get(id=tier_id)
            
            # Record history
            PricingHistory.objects.create(
                pricing_tier=tier,
                old_price_per_unit=tier.price_per_unit,
                new_price_per_unit=new_price,
                old_annual_discount=tier.annual_discount_percent,
                new_annual_discount=new_discount or tier.annual_discount_percent,
                change_reason=reason,
                changed_by=changed_by_user
            )
            
            # Update tier
            tier.price_per_unit = new_price
            if new_discount is not None:
                tier.annual_discount_percent = new_discount
            tier.save()
            
            logger.info(f"Updated pricing tier {tier.name}: {tier.price_per_unit} {tier.currency}")


class FinancialAnalyticsService:
    """Service for financial analytics and metrics calculation"""
    
    @classmethod
    def calculate_mrr(cls, as_of_date: date = None) -> Decimal:
        """Calculate Monthly Recurring Revenue"""
        if not as_of_date:
            as_of_date = timezone.now().date()
        
        # Active subscriptions MRR
        subscription_mrr = UserSubscription.objects.filter(
            status='active',
            current_period_start__lte=as_of_date,
            current_period_end__gte=as_of_date
        ).aggregate(
            total=Sum('plan__price_monthly')
        )['total'] or Decimal('0')
        
        # Institution contracts (monthly equivalent)
        institution_mrr = Contract.objects.filter(
            type='institution',
            status='active',
            start_date__lte=as_of_date,
            end_date__gte=as_of_date
        ).aggregate(
            total=Sum('total_value')
        )['total'] or Decimal('0')
        institution_mrr = institution_mrr / 12  # Convert annual to monthly
        
        # Employer contracts
        employer_mrr = Contract.objects.filter(
            type='employer',
            status='active',
            start_date__lte=as_of_date,
            end_date__gte=as_of_date
        ).aggregate(
            total=Sum('total_value')
        )['total'] or Decimal('0')
        employer_mrr = employer_mrr / 12  # Convert annual to monthly
        
        total_mrr = subscription_mrr + institution_mrr + employer_mrr
        
        # Store metric
        RevenueMetrics.objects.update_or_create(
            metric_type='mrr',
            revenue_stream='total',
            period_start=as_of_date.replace(day=1),
            period_end=as_of_date,
            defaults={'value': total_mrr, 'currency': 'USD'}
        )
        
        return total_mrr
    
    @classmethod
    def calculate_arr(cls, as_of_date: date = None) -> Decimal:
        """Calculate Annual Recurring Revenue"""
        mrr = cls.calculate_mrr(as_of_date)
        arr = mrr * 12
        
        if not as_of_date:
            as_of_date = timezone.now().date()
        
        RevenueMetrics.objects.update_or_create(
            metric_type='arr',
            revenue_stream='total',
            period_start=as_of_date.replace(day=1),
            period_end=as_of_date,
            defaults={'value': arr, 'currency': 'USD'}
        )
        
        return arr
    
    @classmethod
    def calculate_churn_rate(cls, period_start: date, period_end: date) -> Decimal:
        """Calculate churn rate for a given period"""
        # Customers at start of period
        start_customers = UserSubscription.objects.filter(
            status='active',
            created_at__lt=period_start
        ).count()
        
        # Customers who churned during period
        churned_customers = UserSubscription.objects.filter(
            status__in=['canceled', 'past_due'],
            updated_at__range=[period_start, period_end]
        ).count()
        
        churn_rate = Decimal('0')
        if start_customers > 0:
            churn_rate = (Decimal(churned_customers) / Decimal(start_customers)) * 100
        
        RevenueMetrics.objects.update_or_create(
            metric_type='churn_rate',
            revenue_stream='subscriptions',
            period_start=period_start,
            period_end=period_end,
            defaults={'value': churn_rate, 'currency': 'USD'}
        )
        
        return churn_rate
    
    @classmethod
    def calculate_ltv(cls, cohort_start: date = None) -> Decimal:
        """Calculate Customer Lifetime Value"""
        if not cohort_start:
            cohort_start = timezone.now().date() - timedelta(days=365)
        
        # Average monthly revenue per user
        arpu = cls.calculate_arpu()
        
        # Average customer lifespan (inverse of churn rate)
        churn_rate = cls.calculate_churn_rate(
            cohort_start, 
            timezone.now().date()
        )
        
        if churn_rate > 0:
            avg_lifespan_months = 100 / churn_rate  # Convert percentage to months
            ltv = arpu * Decimal(avg_lifespan_months)
        else:
            ltv = arpu * 24  # Default 24 months if no churn
        
        RevenueMetrics.objects.update_or_create(
            metric_type='ltv',
            revenue_stream='subscriptions',
            period_start=cohort_start,
            period_end=timezone.now().date(),
            defaults={'value': ltv, 'currency': 'USD'}
        )
        
        return ltv
    
    @classmethod
    def calculate_arpu(cls, period_start: date = None, period_end: date = None) -> Decimal:
        """Calculate Average Revenue Per User"""
        if not period_end:
            period_end = timezone.now().date()
        if not period_start:
            period_start = period_end - timedelta(days=30)
        
        # Total revenue in period
        total_revenue = PaymentTransaction.objects.filter(
            status='completed',
            processed_at__date__range=[period_start, period_end]
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # Active users in period
        active_users = UserSubscription.objects.filter(
            status='active',
            current_period_start__lte=period_end,
            current_period_end__gte=period_start
        ).count()
        
        arpu = Decimal('0')
        if active_users > 0:
            arpu = total_revenue / Decimal(active_users)
        
        RevenueMetrics.objects.update_or_create(
            metric_type='arpu',
            revenue_stream='total',
            period_start=period_start,
            period_end=period_end,
            defaults={'value': arpu, 'currency': 'USD'}
        )
        
        return arpu
    
    @classmethod
    def calculate_conversion_rate(cls, period_start: date, period_end: date) -> Decimal:
        """Calculate trial to paid conversion rate"""
        # Trials started in period
        trials_started = UserSubscription.objects.filter(
            status='trial',
            created_at__date__range=[period_start, period_end]
        ).count()
        
        # Trials converted to paid
        trials_converted = UserSubscription.objects.filter(
            status='active',
            created_at__date__range=[period_start, period_end]
        ).exclude(
            current_period_start=models.F('created_at')
        ).count()
        
        conversion_rate = Decimal('0')
        if trials_started > 0:
            conversion_rate = (Decimal(trials_converted) / Decimal(trials_started)) * 100
        
        RevenueMetrics.objects.update_or_create(
            metric_type='conversion_rate',
            revenue_stream='subscriptions',
            period_start=period_start,
            period_end=period_end,
            defaults={'value': conversion_rate, 'currency': 'USD'}
        )
        
        return conversion_rate
    
    @classmethod
    def generate_revenue_breakdown(cls, period_start: date, period_end: date) -> Dict:
        """Generate comprehensive revenue breakdown"""
        # Subscription revenue
        subscription_revenue = PaymentTransaction.objects.filter(
            subscription__isnull=False,
            status='completed',
            processed_at__date__range=[period_start, period_end]
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # Cohort revenue
        cohort_revenue = CohortPayment.objects.filter(
            status='completed',
            completed_at__date__range=[period_start, period_end]
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # Institution revenue (from invoices)
        institution_revenue = Invoice.objects.filter(
            type='institution',
            status='paid',
            paid_date__date__range=[period_start, period_end]
        ).aggregate(total=Sum('total'))['total'] or Decimal('0')
        
        # Employer revenue
        employer_revenue = Invoice.objects.filter(
            type='employer',
            status='paid',
            paid_date__date__range=[period_start, period_end]
        ).aggregate(total=Sum('total'))['total'] or Decimal('0')
        
        total_revenue = (
            subscription_revenue + 
            cohort_revenue + 
            institution_revenue + 
            employer_revenue
        )
        
        return {
            'subscription_revenue': float(subscription_revenue),
            'cohort_revenue': float(cohort_revenue),
            'institution_revenue': float(institution_revenue),
            'employer_revenue': float(employer_revenue),
            'total_revenue': float(total_revenue),
            'period_start': period_start.isoformat(),
            'period_end': period_end.isoformat()
        }

class FinancialReportingService:
    """Service for generating financial reports"""
    
    @classmethod
    def generate_revenue_summary_report(cls, period_start: date, period_end: date, user: User) -> FinancialReport:
        """Generate comprehensive revenue summary report"""
        report = FinancialReport.objects.create(
            report_type='revenue_summary',
            title=f'Revenue Summary: {period_start} to {period_end}',
            period_start=period_start,
            period_end=period_end,
            generated_by=user,
            status='generating'
        )
        
        try:
            # Generate report data
            analytics = FinancialAnalyticsService()
            revenue_breakdown = analytics.generate_revenue_breakdown(period_start, period_end)
            
            # Calculate key metrics
            mrr = analytics.calculate_mrr(period_end)
            arr = analytics.calculate_arr(period_end)
            churn_rate = analytics.calculate_churn_rate(period_start, period_end)
            
            report_data = {
                'revenue_breakdown': revenue_breakdown,
                'key_metrics': {
                    'mrr': float(mrr),
                    'arr': float(arr),
                    'churn_rate': float(churn_rate)
                },
                'generated_at': timezone.now().isoformat()
            }
            
            # Store report data and mark as completed
            report.filters = report_data
            report.status = 'completed'
            report.completed_at = timezone.now()
            report.save()
            
            logger.info(f"Revenue summary report generated: {report.id}")
            
        except Exception as e:
            report.status = 'failed'
            report.save()
            logger.error(f"Failed to generate revenue summary report: {str(e)}")
            raise
        
        return report
    
    @classmethod
    def generate_subscription_analytics_report(cls, period_start: date, period_end: date, user: User) -> FinancialReport:
        """Generate detailed subscription analytics report"""
        report = FinancialReport.objects.create(
            report_type='subscription_analytics',
            title=f'Subscription Analytics: {period_start} to {period_end}',
            period_start=period_start,
            period_end=period_end,
            generated_by=user,
            status='generating'
        )
        
        try:
            # Subscription metrics
            total_subscriptions = UserSubscription.objects.filter(
                created_at__date__range=[period_start, period_end]
            ).count()
            
            active_subscriptions = UserSubscription.objects.filter(
                status='active',
                current_period_start__lte=period_end,
                current_period_end__gte=period_start
            ).count()
            
            # Plan distribution
            plan_distribution = UserSubscription.objects.filter(
                status='active'
            ).values('plan__name').annotate(
                count=Count('id'),
                revenue=Sum('plan__price_monthly')
            )
            
            # Trial conversions
            trial_conversions = UserSubscription.objects.filter(
                status='active',
                created_at__date__range=[period_start, period_end]
            ).exclude(
                current_period_start=models.F('created_at')
            ).count()
            
            report_data = {
                'subscription_metrics': {
                    'total_subscriptions': total_subscriptions,
                    'active_subscriptions': active_subscriptions,
                    'trial_conversions': trial_conversions
                },
                'plan_distribution': list(plan_distribution),
                'generated_at': timezone.now().isoformat()
            }
            
            report.filters = report_data
            report.status = 'completed'
            report.completed_at = timezone.now()
            report.save()
            
        except Exception as e:
            report.status = 'failed'
            report.save()
            logger.error(f"Failed to generate subscription analytics report: {str(e)}")
            raise
        
        return report
    
    @classmethod
    def generate_cohort_financials_report(cls, period_start: date, period_end: date, user: User) -> FinancialReport:
        """Generate cohort financial performance report"""
        report = FinancialReport.objects.create(
            report_type='cohort_financials',
            title=f'Cohort Financials: {period_start} to {period_end}',
            period_start=period_start,
            period_end=period_end,
            generated_by=user,
            status='generating'
        )
        
        try:
            # Cohort revenue
            cohort_payments = CohortPayment.objects.filter(
                completed_at__date__range=[period_start, period_end],
                status='completed'
            )
            
            total_cohort_revenue = cohort_payments.aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0')
            
            # Cohort enrollment metrics
            enrollments = Enrollment.objects.filter(
                joined_at__date__range=[period_start, period_end]
            )
            
            enrollment_metrics = {
                'total_enrollments': enrollments.count(),
                'paid_enrollments': enrollments.filter(seat_type='paid').count(),
                'scholarship_enrollments': enrollments.filter(seat_type='scholarship').count(),
                'sponsored_enrollments': enrollments.filter(seat_type='sponsored').count()
            }
            
            report_data = {
                'cohort_revenue': float(total_cohort_revenue),
                'enrollment_metrics': enrollment_metrics,
                'generated_at': timezone.now().isoformat()
            }
            
            report.filters = report_data
            report.status = 'completed'
            report.completed_at = timezone.now()
            report.save()
            
        except Exception as e:
            report.status = 'failed'
            report.save()
            logger.error(f"Failed to generate cohort financials report: {str(e)}")
            raise
        
        return report

class CashFlowService:
    """Service for cash flow management and projections"""
    
    @classmethod
    def generate_cash_flow_projection(cls, projection_type: str, period_start: date, period_end: date) -> CashFlowProjection:
        """Generate cash flow projection"""
        projection = CashFlowProjection.objects.create(
            projection_type=projection_type,
            period_start=period_start,
            period_end=period_end
        )
        
        try:
            # Calculate revenue projections based on historical data
            historical_period = period_end - period_start
            historical_start = period_start - historical_period
            
            # Subscription revenue projection
            historical_subscription = PaymentTransaction.objects.filter(
                subscription__isnull=False,
                status='completed',
                processed_at__date__range=[historical_start, period_start]
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            # Apply growth rate (simplified - could use more sophisticated modeling)
            growth_rate = Decimal('1.1')  # 10% growth assumption
            projection.subscription_revenue = historical_subscription * growth_rate
            
            # Institution revenue projection
            historical_institution = Invoice.objects.filter(
                type='institution',
                status='paid',
                paid_date__date__range=[historical_start, period_start]
            ).aggregate(total=Sum('total'))['total'] or Decimal('0')
            projection.institution_revenue = historical_institution * growth_rate
            
            # Employer revenue projection
            historical_employer = Invoice.objects.filter(
                type='employer',
                status='paid',
                paid_date__date__range=[historical_start, period_start]
            ).aggregate(total=Sum('total'))['total'] or Decimal('0')
            projection.employer_revenue = historical_employer * growth_rate
            
            # Cohort revenue projection
            historical_cohort = CohortPayment.objects.filter(
                status='completed',
                completed_at__date__range=[historical_start, period_start]
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            projection.cohort_revenue = historical_cohort * growth_rate
            
            # Expense projections
            historical_mentor_payouts = MentorPayout.objects.filter(
                period_start__gte=historical_start,
                period_end__lte=period_start,
                status='paid'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            projection.mentor_payouts = historical_mentor_payouts * growth_rate
            
            # Operational costs (estimated)
            projection.operational_costs = projection.subscription_revenue * Decimal('0.3')  # 30% of revenue
            projection.marketing_costs = projection.subscription_revenue * Decimal('0.15')  # 15% of revenue
            
            # Confidence score based on data availability
            projection.confidence_score = Decimal('75.0')  # Default confidence
            
            projection.save()  # This will trigger auto-calculation of totals
            
        except Exception as e:
            logger.error(f"Failed to generate cash flow projection: {str(e)}")
            raise
        
        return projection
    
    @classmethod
    def update_all_projections(cls):
        """Update all active cash flow projections"""
        today = timezone.now().date()
        
        # Weekly projections
        cls.generate_cash_flow_projection(
            'weekly',
            today,
            today + timedelta(weeks=1)
        )
        
        # Monthly projections
        cls.generate_cash_flow_projection(
            'monthly',
            today,
            today + timedelta(days=30)
        )
        
        # Quarterly projections
        cls.generate_cash_flow_projection(
            'quarterly',
            today,
            today + timedelta(days=90)
        )
        
        # Annual projections
        cls.generate_cash_flow_projection(
            'annual',
            today,
            today + timedelta(days=365)
        )

class ComplianceService:
    """Service for compliance management and audit trails"""
    
    @classmethod
    def create_audit_log(cls, user: User, action_type: str, resource_type: str, 
                        resource_id: str, old_values: dict = None, new_values: dict = None,
                        ip_address: str = None, user_agent: str = None) -> AuditLog:
        """Create comprehensive audit log entry"""
        
        # Generate human-readable summary
        changes_summary = cls._generate_changes_summary(action_type, resource_type, old_values, new_values)
        
        audit_log = AuditLog.objects.create(
            user=user,
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values or {},
            new_values=new_values or {},
            changes_summary=changes_summary,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        logger.info(f"Audit log created: {audit_log.id} - {changes_summary}")
        return audit_log
    
    @classmethod
    def _generate_changes_summary(cls, action_type: str, resource_type: str, 
                                 old_values: dict, new_values: dict) -> str:
        """Generate human-readable summary of changes"""
        if action_type == 'create':
            return f"Created new {resource_type}"
        elif action_type == 'delete':
            return f"Deleted {resource_type}"
        elif action_type == 'update' and old_values and new_values:
            changes = []
            for key, new_value in new_values.items():
                old_value = old_values.get(key)
                if old_value != new_value:
                    changes.append(f"{key}: {old_value} → {new_value}")
            return f"Updated {resource_type}: {', '.join(changes)}"
        else:
            return f"{action_type.title()} {resource_type}"
    
    @classmethod
    def check_compliance_status(cls) -> Dict:
        """Check overall compliance status"""
        compliance_records = ComplianceRecord.objects.all()
        
        total_records = compliance_records.count()
        compliant_records = compliance_records.filter(status='compliant').count()
        non_compliant_records = compliance_records.filter(status='non_compliant').count()
        pending_records = compliance_records.filter(status='pending_review').count()
        
        compliance_rate = 0
        if total_records > 0:
            compliance_rate = (compliant_records / total_records) * 100
        
        # Check for overdue reviews
        overdue_reviews = compliance_records.filter(
            next_review_date__lt=timezone.now().date()
        ).count()
        
        return {
            'total_records': total_records,
            'compliant_records': compliant_records,
            'non_compliant_records': non_compliant_records,
            'pending_records': pending_records,
            'compliance_rate': compliance_rate,
            'overdue_reviews': overdue_reviews
        }
    
    @classmethod
    def generate_audit_report(cls, period_start: date, period_end: date, user: User) -> FinancialReport:
        """Generate comprehensive audit report"""
        report = FinancialReport.objects.create(
            report_type='audit_report',
            title=f'Audit Report: {period_start} to {period_end}',
            period_start=period_start,
            period_end=period_end,
            generated_by=user,
            status='generating'
        )
        
        try:
            # Audit log statistics
            audit_logs = AuditLog.objects.filter(
                created_at__date__range=[period_start, period_end]
            )
            
            audit_stats = {
                'total_actions': audit_logs.count(),
                'actions_by_type': dict(
                    audit_logs.values('action_type').annotate(
                        count=Count('id')
                    ).values_list('action_type', 'count')
                ),
                'actions_by_user': dict(
                    audit_logs.values('user__email').annotate(
                        count=Count('id')
                    ).values_list('user__email', 'count')
                )
            }
            
            # Compliance status
            compliance_status = cls.check_compliance_status()
            
            report_data = {
                'audit_statistics': audit_stats,
                'compliance_status': compliance_status,
                'generated_at': timezone.now().isoformat()
            }
            
            report.filters = report_data
            report.status = 'completed'
            report.completed_at = timezone.now()
            report.save()
            
        except Exception as e:
            report.status = 'failed'
            report.save()
            logger.error(f"Failed to generate audit report: {str(e)}")
            raise
        
        return report

class FinancialAlertService:
    """Service for financial alerts and monitoring"""
    
    @classmethod
    def check_revenue_alerts(cls):
        """Check for revenue-related alerts"""
        today = timezone.now().date()
        last_month = today - timedelta(days=30)
        
        # Calculate current and previous month revenue
        current_revenue = PaymentTransaction.objects.filter(
            status='completed',
            processed_at__date__range=[last_month, today]
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        previous_month_start = last_month - timedelta(days=30)
        previous_revenue = PaymentTransaction.objects.filter(
            status='completed',
            processed_at__date__range=[previous_month_start, last_month]
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # Check for revenue drop
        if previous_revenue > 0:
            revenue_change = ((current_revenue - previous_revenue) / previous_revenue) * 100
            if revenue_change < -10:  # 10% drop threshold
                cls._create_alert(
                    alert_type='revenue_drop',
                    severity='high',
                    title='Revenue Drop Detected',
                    description=f'Revenue dropped by {abs(revenue_change):.1f}% compared to previous month',
                    data={
                        'current_revenue': float(current_revenue),
                        'previous_revenue': float(previous_revenue),
                        'change_percentage': float(revenue_change)
                    }
                )
    
    @classmethod
    def check_churn_alerts(cls):
        """Check for churn rate alerts"""
        today = timezone.now().date()
        last_month = today - timedelta(days=30)
        
        churn_rate = FinancialAnalyticsService.calculate_churn_rate(last_month, today)
        
        # Alert if churn rate exceeds threshold
        if churn_rate > 5:  # 5% monthly churn threshold
            cls._create_alert(
                alert_type='churn_spike',
                severity='high' if churn_rate > 10 else 'medium',
                title='High Churn Rate Detected',
                description=f'Monthly churn rate is {churn_rate:.1f}%',
                data={'churn_rate': float(churn_rate)}
            )
    
    @classmethod
    def check_payment_failure_alerts(cls):
        """Check for payment failure alerts"""
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        failed_payments = PaymentTransaction.objects.filter(
            status='failed',
            processed_at__date=yesterday
        ).count()
        
        if failed_payments > 10:  # Threshold for failed payments
            cls._create_alert(
                alert_type='payment_failure',
                severity='medium',
                title='High Payment Failure Rate',
                description=f'{failed_payments} payment failures detected yesterday',
                data={'failed_payments': failed_payments}
            )
    
    @classmethod
    def _create_alert(cls, alert_type: str, severity: str, title: str, 
                     description: str, data: dict = None):
        """Create financial alert"""
        # Check if similar alert already exists
        existing_alert = FinancialAlert.objects.filter(
            alert_type=alert_type,
            status='active',
            created_at__date=timezone.now().date()
        ).first()
        
        if not existing_alert:
            alert = FinancialAlert.objects.create(
                alert_type=alert_type,
                severity=severity,
                title=title,
                description=description,
                data=data or {}
            )
            logger.warning(f"Financial alert created: {alert.title}")
            return alert
    
    @classmethod
    def run_all_checks(cls):
        """Run all financial alert checks"""
        cls.check_revenue_alerts()
        cls.check_churn_alerts()
        cls.check_payment_failure_alerts()

class KPIService:
    """Service for KPI tracking and management"""
    
    @classmethod
    def update_all_kpis(cls):
        """Update all financial KPIs"""
        today = timezone.now().date()
        
        # Revenue KPIs
        cls._update_kpi('Monthly Recurring Revenue', 'revenue', 
                       FinancialAnalyticsService.calculate_mrr(), 'currency')
        
        cls._update_kpi('Annual Recurring Revenue', 'revenue',
                       FinancialAnalyticsService.calculate_arr(), 'currency')
        
        # Growth KPIs
        last_month = today - timedelta(days=30)
        churn_rate = FinancialAnalyticsService.calculate_churn_rate(last_month, today)
        cls._update_kpi('Monthly Churn Rate', 'retention', churn_rate, 'percentage')
        
        # Efficiency KPIs
        arpu = FinancialAnalyticsService.calculate_arpu()
        cls._update_kpi('Average Revenue Per User', 'efficiency', arpu, 'currency')
        
        ltv = FinancialAnalyticsService.calculate_ltv()
        cls._update_kpi('Customer Lifetime Value', 'profitability', ltv, 'currency')
    
    @classmethod
    def _update_kpi(cls, name: str, category: str, current_value: Decimal, unit: str):
        """Update individual KPI"""
        kpi, created = FinancialKPI.objects.get_or_create(
            name=name,
            category=category,
            defaults={'current_value': current_value, 'unit': unit}
        )
        
        if not created:
            kpi.previous_value = kpi.current_value
            kpi.current_value = current_value
            kpi.save()
        
        return kpi