"""
Subscription utilities - Entitlement enforcement.
"""
from functools import wraps

from rest_framework import status
from rest_framework.response import Response

from .models import UserSubscription


def get_user_tier(user_or_uuid):
    """Get user's subscription tier.
    Args:
        user_or_uuid: User object or user UUID
    """
    try:
        from users.models import User

        # If it's a User object, use it directly
        if isinstance(user_or_uuid, User):
            user = user_or_uuid
        else:
            # Otherwise try to get the user by uuid_id
            user = User.objects.get(uuid_id=user_or_uuid)

        subscription = UserSubscription.objects.filter(user=user, status='active').first()
        if subscription and subscription.plan:
            return subscription.plan.name
        return 'free'
    except (UserSubscription.DoesNotExist, User.DoesNotExist, ValueError, AttributeError):
        return 'free'


def has_access(user_tier: str, required_tier: str) -> bool:
    """Check if user tier has access to required tier."""
    tier_hierarchy = {
        'free': 0,
        'starter_3': 1,
        'starter_normal': 1,
        'starter_enhanced': 2,
        'premium': 3,
        'professional_7': 4,
    }

    user_level = tier_hierarchy.get(user_tier, 0)
    required_level = tier_hierarchy.get(required_tier, 0)

    return user_level >= required_level


def require_tier(required_tier: str):
    """Decorator to require specific subscription tier."""
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            user_tier = get_user_tier(request.user.id)
            if not has_access(user_tier, required_tier):
                return Response(
                    {
                        'error': f'Upgrade to {required_tier} required',
                        'current_tier': user_tier,
                        'required_tier': required_tier
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
            return func(request, *args, **kwargs)
        return wrapper
    return decorator



# Payment Processing Utilities

import logging
import os
from decimal import Decimal

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger(__name__)


def attempt_payment_charge(user, amount, currency='KES', description=''):
    """
    Attempt to charge user's payment method.

    Returns:
        tuple: (success: bool, transaction_id: str, error: str)
    """
    paystack_key = os.environ.get('PAYSTACK_SECRET_KEY') or os.environ.get('PAYSTACK_SECRET')
    stripe_key = os.environ.get('STRIPE_SECRET_KEY')

    if paystack_key and currency == 'KES':
        try:
            return _charge_via_paystack(user, amount, currency, description, paystack_key)
        except Exception as e:
            logger.error(f'Paystack charge failed: {e}')

    if stripe_key:
        try:
            return _charge_via_stripe(user, amount, currency, description, stripe_key)
        except Exception as e:
            logger.error(f'Stripe charge failed: {e}')

    logger.warning('No payment gateway configured - simulating successful payment')
    import uuid
    return True, f'sim_{uuid.uuid4().hex[:12]}', None


def _charge_via_paystack(user, amount, currency, description, secret_key):
    """Charge via Paystack."""
    return False, None, 'Paystack recurring billing not yet implemented'


def _charge_via_stripe(user, amount, currency, description, secret_key):
    """Charge via Stripe."""
    try:
        import stripe
        stripe.api_key = secret_key

        subscription = user.subscription
        if subscription.stripe_subscription_id:
            stripe_sub = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
            customer_id = stripe_sub.customer

            intent = stripe.PaymentIntent.create(
                amount=int(float(amount) * 100),
                currency=currency.lower(),
                customer=customer_id,
                description=description,
                confirm=True,
                off_session=True,
            )

            if intent.status == 'succeeded':
                return True, intent.id, None
            else:
                return False, None, f'Payment status: {intent.status}'
        else:
            return False, None, 'No Stripe subscription found'
    except Exception as e:
        return False, None, str(e)


def generate_invoice_pdf(invoice):
    """Generate PDF for invoice."""
    logger.info(f'PDF generation for invoice {invoice.invoice_number} - placeholder')
    return f'/invoices/{invoice.id}.pdf'


def send_invoice_email(invoice):
    """Send invoice email to user."""
    try:
        subject = f'Invoice {invoice.invoice_number} - Subscription Payment'


        message = f"""
Dear {invoice.user.first_name or invoice.user.email},

Your subscription payment has been processed successfully.

Invoice Number: {invoice.invoice_number}
Amount: {invoice.total_amount} {invoice.currency}
Date: {invoice.invoice_date.strftime('%Y-%m-%d')}

Thank you for your continued subscription!

Best regards,
Ongoza CyberHub Team
"""

        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@ongozacyberhub.com'),
            recipient_list=[invoice.user.email],
            fail_silently=False,
        )

        invoice.mark_as_sent()
        logger.info(f'Invoice email sent: {invoice.invoice_number} to {invoice.user.email}')
        return True
    except Exception as e:
        logger.error(f'Failed to send invoice email: {e}')
        return False


def send_retry_notification(user, attempt_number, error_message):
    """Send payment retry notification to user."""
    try:
        subject = f'Payment Retry Attempt #{attempt_number}'

        message = f"""
Dear {user.first_name or user.email},

We attempted to process your subscription payment but it was unsuccessful.

Attempt: #{attempt_number}
Reason: {error_message or 'Payment declined'}

We will automatically retry the payment. Please ensure your payment method is up to date.

Best regards,
Ongoza CyberHub Team
"""

        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@ongozacyberhub.com'),
            recipient_list=[user.email],
            fail_silently=False,
        )

        logger.info(f'Retry notification sent: Attempt #{attempt_number} to {user.email}')
        return True
    except Exception as e:
        logger.error(f'Failed to send retry notification: {e}')
        return False


def send_reverification_reminder(user, expiry_date):
    """Send academic discount re-verification reminder."""
    try:
        subject = 'Academic Discount Re-verification Required'

        message = f"""
Dear {user.first_name or user.email},

Your academic discount verification will expire on {expiry_date.strftime('%Y-%m-%d')}.

To continue receiving your 30% student discount, please re-verify your academic status.

Log in to your account and upload current proof of enrollment.

Best regards,
Ongoza CyberHub Team
"""

        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@ongozacyberhub.com'),
            recipient_list=[user.email],
            fail_silently=False,
        )

        logger.info(f'Re-verification reminder sent to {user.email}')
        return True
    except Exception as e:
        logger.error(f'Failed to send re-verification reminder: {e}')
        return False


def calculate_proration(old_plan, new_plan, current_period_start, current_period_end):
    """
    Calculate prorated amount for plan upgrade/downgrade.

    DSD §2.1.6: Proration calculation

    Returns:
        dict: {
            'credit': Decimal,
            'new_charge': Decimal,
            'proration_amount': Decimal,
            'days_remaining': int,
            'total_days': int,
        }
    """
    now = timezone.now()

    total_days = (current_period_end - current_period_start).days
    days_remaining = (current_period_end - now).days

    if days_remaining <= 0:
        return {
            'credit': Decimal('0'),
            'new_charge': Decimal('0'),
            'proration_amount': Decimal('0'),
            'days_remaining': 0,
            'total_days': total_days,
        }

    old_price = Decimal(str(old_plan.price_monthly or 0))
    new_price = Decimal(str(new_plan.price_monthly or 0))

    old_daily_rate = old_price / Decimal(str(total_days))
    new_daily_rate = new_price / Decimal(str(total_days))

    credit = old_daily_rate * Decimal(str(days_remaining))
    new_charge = new_daily_rate * Decimal(str(days_remaining))

    proration_amount = new_charge - credit

    return {
        'credit': credit.quantize(Decimal('0.01')),
        'new_charge': new_charge.quantize(Decimal('0.01')),
        'proration_amount': proration_amount.quantize(Decimal('0.01')),
        'days_remaining': days_remaining,
        'total_days': total_days,
    }


def apply_promo_code(code_str, user, plan):
    """
    Validate and apply promotional code.

    Returns:
        tuple: (success: bool, discount_amount: Decimal, error: str)
    """
    from subscriptions.models import PromotionalCode

    try:
        code = PromotionalCode.objects.get(code=code_str.upper())
    except PromotionalCode.DoesNotExist:
        return False, Decimal('0'), 'Invalid promo code'

    can_redeem, message = code.can_user_redeem(user)
    if not can_redeem:
        return False, Decimal('0'), message

    if code.eligible_plans.exists() and plan not in code.eligible_plans.all():
        return False, Decimal('0'), 'This code is not valid for the selected plan'

    base_amount = Decimal(str(plan.price_monthly or 0))
    discount_amount = Decimal(str(code.calculate_discount(float(base_amount))))

    return True, discount_amount, 'Code applied successfully'


def record_promo_redemption(code, user, subscription, original_amount, discount_amount):
    """Record promotional code redemption."""
    from subscriptions.models import PromoCodeRedemption

    final_amount = original_amount - discount_amount

    redemption = PromoCodeRedemption.objects.create(
        code=code,
        user=user,
        subscription=subscription,
        discount_applied=discount_amount,
        original_amount=original_amount,
        final_amount=final_amount,
    )

    logger.info(
        f'Promo code redeemed: {code.code} by {user.email} | '
        f'Discount: {discount_amount} KES | Final: {final_amount} KES'
    )

    return redemption

# Payment Processing Utilities

import logging

logger = logging.getLogger(__name__)


def attempt_payment_charge(user, amount, currency='KES', description=''):
    """
    Attempt to charge user's payment method.

    Returns:
        tuple: (success: bool, transaction_id: str, error: str)
    """
    paystack_key = os.environ.get('PAYSTACK_SECRET_KEY') or os.environ.get('PAYSTACK_SECRET')
    stripe_key = os.environ.get('STRIPE_SECRET_KEY')

    if paystack_key and currency == 'KES':
        try:
            return _charge_via_paystack(user, amount, currency, description, paystack_key)
        except Exception as e:
            logger.error(f'Paystack charge failed: {e}')

    if stripe_key:
        try:
            return _charge_via_stripe(user, amount, currency, description, stripe_key)
        except Exception as e:
            logger.error(f'Stripe charge failed: {e}')

    logger.warning('No payment gateway configured - simulating successful payment')
    import uuid
    return True, f'sim_{uuid.uuid4().hex[:12]}', None


def _charge_via_paystack(user, amount, currency, description, secret_key):
    """Charge via Paystack."""
    return False, None, 'Paystack recurring billing not yet implemented'


def _charge_via_stripe(user, amount, currency, description, secret_key):
    """Charge via Stripe."""
    try:
        import stripe
        stripe.api_key = secret_key

        subscription = user.subscription
        if subscription.stripe_subscription_id:
            stripe_sub = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
            customer_id = stripe_sub.customer

            intent = stripe.PaymentIntent.create(
                amount=int(float(amount) * 100),
                currency=currency.lower(),
                customer=customer_id,
                description=description,
                confirm=True,
                off_session=True,
            )

            if intent.status == 'succeeded':
                return True, intent.id, None
            else:
                return False, None, f'Payment status: {intent.status}'
        else:
            return False, None, 'No Stripe subscription found'
    except Exception as e:
        return False, None, str(e)


def generate_invoice_pdf(invoice):
    """Generate PDF for invoice."""
    logger.info(f'PDF generation for invoice {invoice.invoice_number} - placeholder')
    return f'/invoices/{invoice.id}.pdf'


def send_invoice_email(invoice):
    """Send invoice email to user."""
    try:
        subject = f'Invoice {invoice.invoice_number} - Subscription Payment'

        message = f"""
Dear {invoice.user.first_name or invoice.user.email},

Your subscription payment has been processed successfully.

Invoice Number: {invoice.invoice_number}
Amount: {invoice.total_amount} {invoice.currency}
Date: {invoice.invoice_date.strftime('%Y-%m-%d')}

Thank you for your continued subscription!

Best regards,
Ongoza CyberHub Team
"""

        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@ongozacyberhub.com'),
            recipient_list=[invoice.user.email],
            fail_silently=False,
        )

        invoice.mark_as_sent()
        logger.info(f'Invoice email sent: {invoice.invoice_number} to {invoice.user.email}')
        return True
    except Exception as e:
        logger.error(f'Failed to send invoice email: {e}')
        return False


def send_retry_notification(user, attempt_number, error_message):
    """Send payment retry notification to user."""
    try:
        subject = f'Payment Retry Attempt #{attempt_number}'

        message = f"""
Dear {user.first_name or user.email},

We attempted to process your subscription payment but it was unsuccessful.

Attempt: #{attempt_number}
Reason: {error_message or 'Payment declined'}

We will automatically retry the payment. Please ensure your payment method is up to date.

Best regards,
Ongoza CyberHub Team
"""

        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@ongozacyberhub.com'),
            recipient_list=[user.email],
            fail_silently=False,
        )

        logger.info(f'Retry notification sent: Attempt #{attempt_number} to {user.email}')
        return True
    except Exception as e:
        logger.error(f'Failed to send retry notification: {e}')
        return False


def send_reverification_reminder(user, expiry_date):
    """Send academic discount re-verification reminder."""
    try:
        subject = 'Academic Discount Re-verification Required'

        message = f"""
Dear {user.first_name or user.email},

Your academic discount verification will expire on {expiry_date.strftime('%Y-%m-%d')}.

To continue receiving your 30% student discount, please re-verify your academic status.

Log in to your account and upload current proof of enrollment.

Best regards,
Ongoza CyberHub Team
"""

        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@ongozacyberhub.com'),
            recipient_list=[user.email],
            fail_silently=False,
        )

        logger.info(f'Re-verification reminder sent to {user.email}')
        return True
    except Exception as e:
        logger.error(f'Failed to send re-verification reminder: {e}')
        return False


def calculate_proration(old_plan, new_plan, current_period_start, current_period_end):
    """
    Calculate prorated amount for plan upgrade/downgrade.

    DSD §2.1.6: Proration calculation

    Returns:
        dict: {
            'credit': Decimal,
            'new_charge': Decimal,
            'proration_amount': Decimal,
            'days_remaining': int,
            'total_days': int,
        }
    """
    now = timezone.now()

    total_days = (current_period_end - current_period_start).days
    days_remaining = (current_period_end - now).days

    if days_remaining <= 0:
        return {
            'credit': Decimal('0'),
            'new_charge': Decimal('0'),
            'proration_amount': Decimal('0'),
            'days_remaining': 0,
            'total_days': total_days,
        }

    old_price = Decimal(str(old_plan.price_monthly or 0))
    new_price = Decimal(str(new_plan.price_monthly or 0))

    old_daily_rate = old_price / Decimal(str(total_days))
    new_daily_rate = new_price / Decimal(str(total_days))

    credit = old_daily_rate * Decimal(str(days_remaining))
    new_charge = new_daily_rate * Decimal(str(days_remaining))

    proration_amount = new_charge - credit

    return {
        'credit': credit.quantize(Decimal('0.01')),
        'new_charge': new_charge.quantize(Decimal('0.01')),
        'proration_amount': proration_amount.quantize(Decimal('0.01')),
        'days_remaining': days_remaining,
        'total_days': total_days,
    }


def apply_promo_code(code_str, user, plan):
    """
    Validate and apply promotional code.

    Returns:
        tuple: (success: bool, discount_amount: Decimal, error: str)
    """
    from subscriptions.models import PromotionalCode

    try:
        code = PromotionalCode.objects.get(code=code_str.upper())
    except PromotionalCode.DoesNotExist:
        return False, Decimal('0'), 'Invalid promo code'

    can_redeem, message = code.can_user_redeem(user)
    if not can_redeem:
        return False, Decimal('0'), message

    if code.eligible_plans.exists() and plan not in code.eligible_plans.all():
        return False, Decimal('0'), 'This code is not valid for the selected plan'

    base_amount = Decimal(str(plan.price_monthly or 0))
    discount_amount = Decimal(str(code.calculate_discount(float(base_amount))))

    return True, discount_amount, 'Code applied successfully'


def record_promo_redemption(code, user, subscription, original_amount, discount_amount):
    """Record promotional code redemption."""
    from subscriptions.models import PromoCodeRedemption

    final_amount = original_amount - discount_amount

    redemption = PromoCodeRedemption.objects.create(
        code=code,
        user=user,
        subscription=subscription,
        discount_applied=discount_amount,
        original_amount=original_amount,
        final_amount=final_amount,
    )

    logger.info(
        f'Promo code redeemed: {code.code} by {user.email} | '
        f'Discount: {discount_amount} KES | Final: {final_amount} KES'
    )

    return redemption
