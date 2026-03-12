"""
Billing Engine Services - Core business logic for subscription management
"""
import uuid
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from .billing_engine import (
    EnhancedSubscription, SubscriptionPlanVersion, BillingPeriod,
    DunningSequence, SubscriptionChange, ProrationCredit, SubscriptionInvoice
)


class SubscriptionLifecycleManager:
    """Manages subscription state transitions and lifecycle events."""
    
    @staticmethod
    def create_trial_subscription(user, plan_version, billing_cycle='monthly'):
        """Create new trial subscription."""
        trial_days = plan_version.trial_days
        trial_start = timezone.now()
        trial_end = trial_start + timedelta(days=trial_days)
        
        # Calculate cycle anchor based on signup day
        cycle_anchor_day = trial_end.day
        
        subscription = EnhancedSubscription.objects.create(
            user=user,
            plan_version=plan_version,
            status='TRIAL',
            billing_cycle=billing_cycle,
            cycle_anchor_day=cycle_anchor_day,
            current_period_start=trial_start,
            current_period_end=trial_end,
            trial_start=trial_start,
            trial_end=trial_end
        )
        
        # Create audit record
        SubscriptionChange.objects.create(
            subscription=subscription,
            change_type='trial_conversion',
            reason='user_initiated',
            description=f'Trial subscription created for {plan_version.name}',
            created_by=user
        )
        
        return subscription
    
    @staticmethod
    def convert_trial_to_active(subscription):
        """Convert trial subscription to active with payment."""
        if subscription.status != 'TRIAL':
            raise ValidationError("Can only convert TRIAL subscriptions")
        
        # Calculate first billing period
        period_start = timezone.now()
        if subscription.billing_cycle == 'monthly':
            period_end = period_start + timedelta(days=30)
        else:
            period_end = period_start + timedelta(days=365)
        
        subscription.status = 'ACTIVE'
        subscription.current_period_start = period_start
        subscription.current_period_end = period_end
        subscription.save()
        
        # Create billing period
        BillingPeriod.objects.create(
            subscription=subscription,
            period_start=period_start,
            period_end=period_end,
            status='current',
            amount=subscription.plan_version.price_monthly if subscription.billing_cycle == 'monthly' 
                   else subscription.plan_version.price_annual,
            currency='USD'
        )
        
        return subscription


class BillingCycleManager:
    """Manages billing cycle calculations and renewals."""
    
    @staticmethod
    def calculate_next_billing_date(subscription):
        """Calculate next billing date based on cycle anchor."""
        if subscription.billing_cycle == 'monthly':
            # Monthly cycle - same day each month
            next_month = subscription.current_period_end.replace(day=1) + timedelta(days=32)
            try:
                return next_month.replace(day=subscription.cycle_anchor_day)
            except ValueError:
                # Handle months with fewer days
                import calendar
                last_day = calendar.monthrange(next_month.year, next_month.month)[1]
                return next_month.replace(day=min(subscription.cycle_anchor_day, last_day))
        else:
            # Annual cycle - same date next year
            try:
                return subscription.current_period_end.replace(
                    year=subscription.current_period_end.year + 1
                )
            except ValueError:
                # Handle leap year edge case
                return subscription.current_period_end.replace(
                    year=subscription.current_period_end.year + 1,
                    month=2,
                    day=28
                )
    
    @staticmethod
    def process_renewal(subscription):
        """Process subscription renewal."""
        if subscription.status != 'ACTIVE':
            return False
        
        next_period_start = subscription.current_period_end
        next_period_end = BillingCycleManager.calculate_next_billing_date(subscription)
        
        # Create new billing period
        billing_period = BillingPeriod.objects.create(
            subscription=subscription,
            period_start=next_period_start,
            period_end=next_period_end,
            status='current',
            amount=subscription.plan_version.price_monthly if subscription.billing_cycle == 'monthly'
                   else subscription.plan_version.price_annual,
            currency='USD'
        )
        
        # Update subscription period
        subscription.current_period_start = next_period_start
        subscription.current_period_end = next_period_end
        subscription.save()
        
        return billing_period


class ProrationCalculator:
    """Handles proration calculations for mid-cycle plan changes."""
    
    @staticmethod
    def calculate_upgrade_proration(subscription, new_plan_version):
        """Calculate proration for plan upgrade."""
        if subscription.status != 'ACTIVE':
            return {'credit': Decimal('0.00'), 'charge': Decimal('0.00'), 'net': Decimal('0.00')}
        
        now = timezone.now()
        if now >= subscription.current_period_end:
            return {'credit': Decimal('0.00'), 'charge': Decimal('0.00'), 'net': Decimal('0.00')}
        
        # Calculate remaining days
        total_days = (subscription.current_period_end - subscription.current_period_start).days
        remaining_days = (subscription.current_period_end - now).days
        
        # Current plan daily cost
        current_price = (
            subscription.plan_version.price_annual if subscription.billing_cycle == 'annual'
            else subscription.plan_version.price_monthly
        )
        current_daily_cost = current_price / total_days
        
        # New plan daily cost
        new_price = (
            new_plan_version.price_annual if subscription.billing_cycle == 'annual'
            else new_plan_version.price_monthly
        )
        new_daily_cost = new_price / total_days
        
        # Calculate credit and charge
        credit = current_daily_cost * remaining_days
        charge = new_daily_cost * remaining_days
        net_charge = charge - credit
        
        return {
            'credit': credit,
            'charge': charge,
            'net': max(Decimal('0.00'), net_charge),
            'remaining_days': remaining_days
        }
    
    @staticmethod
    def apply_plan_change(subscription, new_plan_version, user=None):
        """Apply plan change with proration."""
        with transaction.atomic():
            # Calculate proration
            proration = ProrationCalculator.calculate_upgrade_proration(subscription, new_plan_version)
            
            # Store old plan for audit
            old_plan = subscription.plan_version
            
            # Update subscription
            subscription.plan_version = new_plan_version
            subscription.save()
            
            # Create audit record
            change_record = SubscriptionChange.objects.create(
                subscription=subscription,
                change_type='plan_change',
                old_value=f"{old_plan.name} v{old_plan.version}",
                new_value=f"{new_plan_version.name} v{new_plan_version.version}",
                reason='user_initiated' if user else 'admin_initiated',
                description=f'Plan changed from {old_plan.name} to {new_plan_version.name}',
                proration_credit=proration['credit'],
                proration_charge=proration['charge'],
                net_proration=proration['net'],
                created_by=user
            )
            
            # Create proration credit if applicable
            if proration['credit'] > 0:
                ProrationCredit.objects.create(
                    subscription=subscription,
                    subscription_change=change_record,
                    amount=proration['credit'],
                    currency='USD',
                    status='pending'
                )
            
            return {
                'subscription': subscription,
                'proration': proration,
                'change_record': change_record
            }


class DunningManager:
    """Manages payment failure recovery and dunning sequences."""
    
    @staticmethod
    def initiate_dunning_sequence(subscription, billing_period):
        """Start dunning sequence for failed payment."""
        # Determine grace period based on billing cycle
        grace_days = 7 if subscription.billing_cycle == 'annual' else 3
        
        dunning = DunningSequence.objects.create(
            subscription=subscription,
            billing_period=billing_period,
            status='active',
            retry_schedule=[1, 3, 7],  # Retry on day 1, 3, and 7
            current_attempt=0,
            max_attempts=3,
            grace_period_days=grace_days,
            grace_period_end=timezone.now() + timedelta(days=grace_days),
            next_retry_at=timezone.now() + timedelta(days=1)
        )
        
        # Transition subscription to PAST_DUE
        subscription.transition_to('PAST_DUE', 'Payment failed, dunning sequence initiated')
        
        return dunning
    
    @staticmethod
    def process_dunning_retries():
        """Process all pending dunning retries."""
        pending_retries = DunningSequence.objects.filter(
            status='active',
            next_retry_at__lte=timezone.now()
        )
        
        results = []
        for dunning in pending_retries:
            success = dunning.execute_retry()
            results.append({
                'dunning_id': dunning.id,
                'subscription_id': dunning.subscription.id,
                'attempt': dunning.current_attempt,
                'success': success
            })
        
        return results


class InvoiceGenerator:
    """Generates and manages subscription invoices."""
    
    @staticmethod
    def create_subscription_invoice(billing_period):
        """Create invoice for billing period."""
        subscription = billing_period.subscription
        
        # Calculate amounts
        subtotal = billing_period.amount
        tax_amount = Decimal('0.00')  # Add tax calculation logic here
        total_amount = subtotal + tax_amount
        
        # Generate invoice
        invoice = SubscriptionInvoice.objects.create(
            subscription=subscription,
            billing_period=billing_period,
            invoice_number=SubscriptionInvoice.generate_invoice_number(),
            status='draft',
            subtotal=subtotal,
            tax_amount=tax_amount,
            total_amount=total_amount,
            currency='USD',
            due_date=timezone.now() + timedelta(days=7),
            line_items=[{
                'description': f'{subscription.plan_version.name} - {subscription.billing_cycle.title()} Subscription',
                'quantity': 1,
                'unit_price': float(billing_period.amount),
                'total': float(billing_period.amount)
            }]
        )
        
        # Apply any available proration credits
        invoice.apply_proration_credits()
        
        # Link to billing period
        billing_period.invoice = invoice
        billing_period.save()
        
        return invoice
    
    @staticmethod
    def send_invoice(invoice):
        """Send invoice to customer."""
        # Add email sending logic here
        invoice.status = 'sent'
        invoice.sent_at = timezone.now()
        invoice.save()
        
        return True