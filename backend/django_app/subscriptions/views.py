"""
API views for Subscription Engine.
"""
import hashlib
import hmac
import json
import logging
import os
import random
import re
import string

import requests
from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import (
    TIER_FREE,
    PaymentGateway,
    PaymentSettings,
    PaymentTransaction,
    SubscriptionPlan,
    UserSubscription,
)
from .serializers import (
    UpgradeSubscriptionSerializer,
)

logger = logging.getLogger(__name__)
User = get_user_model()


def get_stream_policy():
    """Admin-managed Stream A policy (PaymentSettings.student_subscription_policy)."""
    try:
        row = PaymentSettings.objects.get(setting_key='student_subscription_policy')
        return row.setting_value or {}
    except PaymentSettings.DoesNotExist:
        return {
            'grace_period_days_monthly': 3,
            'grace_period_days_annual': 7,
            'renewal_attempt_days_before': 1,
            'academic_discount_percent': 30,
            'promo_single_code_per_checkout': True,
            'auto_renewal_default': True,
            'downgrade_effective': 'end_of_period',
            'upgrade_effective': 'immediate',
            'usd_to_kes_rate': 130,
        }


def _serialize_plan_for_api(plan, include_counts=False):
    """Student / finance plan row with Stream A catalog."""
    catalog = plan.catalog or {}
    user_count = 0
    revenue = 0.0
    if include_counts:
        user_count = UserSubscription.objects.filter(plan=plan, status__in=['active', 'trial']).count()
        pm = float(plan.price_monthly or 0)
        pa = float(plan.price_annual or 0)
        revenue = user_count * (pa if plan.billing_interval == SubscriptionPlan.BILLING_ANNUAL else pm)
    mode_note = catalog.get('mode_note', '')
    if not mode_note and plan.tier == 'starter':
        mode_note = 'Pro: Tier 2–6 access; mentorship credits per catalog.'
    return {
        'id': str(plan.id),
        'name': plan.name,
        'tier': plan.tier,
        'stream': getattr(plan, 'stream', SubscriptionPlan.STREAM_STUDENT),
        'billing_interval': getattr(plan, 'billing_interval', 'monthly'),
        'sort_order': getattr(plan, 'sort_order', 0),
        'is_listed': getattr(plan, 'is_listed', True),
        'price_monthly': float(plan.price_monthly or 0),
        'price_annual': float(plan.price_annual) if plan.price_annual is not None else None,
        'catalog': catalog,
        'features': plan.features or [],
        'ai_coach_daily_limit': plan.ai_coach_daily_limit,
        'portfolio_item_limit': plan.portfolio_item_limit,
        'missions_access_type': plan.missions_access_type,
        'mentorship_access': plan.mentorship_access,
        'talentscope_access': plan.talentscope_access,
        'marketplace_contact': plan.marketplace_contact,
        'enhanced_access_days': plan.enhanced_access_days,
        'mode_note': mode_note,
        'users': user_count,
        'revenue': revenue,
    }


PAYSTACK_VERIFY_URL = "https://api.paystack.co/transaction/verify/{}"
PAYSTACK_INITIALIZE_URL = "https://api.paystack.co/transaction/initialize"


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def subscription_status(request):
    """
    GET /api/v1/subscription/status
    Get user's subscription status.
    """
    user = request.user

    try:
        subscription = user.subscription
        plan = subscription.plan
    except UserSubscription.DoesNotExist:
        # Default to free tier
        return Response({
            'tier': 'free',
            'days_enhanced_left': None,
            'can_upgrade': True,
            'features': [],
            'next_payment': None,
            'status': 'active',
            'ai_coach_daily_limit': 0,
            'policy': get_stream_policy(),
        })

    # Map DB tier to frontend tier name
    # DB: free | starter | premium   →   Frontend: free | starter | professional
    TIER_MAP = {'free': 'free', 'starter': 'starter', 'premium': 'professional'}
    tier = TIER_MAP.get(plan.tier, plan.tier)

    # Can upgrade if not already on premium/professional
    can_upgrade = plan.tier not in ('premium',)

    return Response({
        'tier': tier,
        'plan_name': plan.name,
        'plan_tier': plan.tier,
        'plan_catalog': getattr(plan, 'catalog', None) or {},
        'billing_interval': getattr(subscription, 'billing_interval', 'monthly'),
        'trial_end': subscription.trial_end.isoformat() if getattr(subscription, 'trial_end', None) else None,
        'cancel_at_period_end': getattr(subscription, 'cancel_at_period_end', False),
        'grace_period_end': subscription.grace_period_end.isoformat() if getattr(subscription, 'grace_period_end', None) else None,
        'days_enhanced_left': subscription.days_enhanced_left,
        'enhanced_access_until': subscription.enhanced_access_expires_at,
        'can_upgrade': can_upgrade,
        'features': plan.features or [],
        'next_payment': subscription.current_period_end,
        'next_billing_date': subscription.current_period_end,
        'status': subscription.status,
        'current_period_start': subscription.current_period_start,
        'current_period_end': subscription.current_period_end,
        'pending_downgrade_plan': getattr(getattr(subscription, 'pending_downgrade_plan', None), 'name', None),
        'pending_downgrade_effective_at': subscription.current_period_end if getattr(subscription, 'pending_downgrade_plan', None) else None,
        'ai_coach_daily_limit': plan.ai_coach_daily_limit,
        'policy': get_stream_policy(),
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upgrade_subscription(request):
    """
    POST /api/v1/subscription/upgrade
    Upgrade subscription with proration and promo code support.
    Body: {
        "plan": "starter_3" | "professional_7",
        "promo_code": "CYBER2026" (optional),
        "mock": true (optional)
    }
    """
    from .utils import (
        apply_promo_code,
        attempt_payment_charge,
        calculate_proration,
        record_promo_redemption,
    )

    serializer = UpgradeSubscriptionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    plan_identifier = serializer.validated_data['plan']
    promo_code = request.data.get('promo_code', '').strip()
    mock_upgrade = request.data.get('mock', False)

    # Find plan
    try:
        plan = SubscriptionPlan.objects.get(name=plan_identifier)
    except SubscriptionPlan.DoesNotExist:
        tier_mapping = {
            'starter_3': 'starter',
            'professional_7': 'premium',
            'free': 'free',
        }
        tier = tier_mapping.get(plan_identifier, plan_identifier)
        try:
            plan = SubscriptionPlan.objects.get(tier=tier)
        except SubscriptionPlan.DoesNotExist:
            return Response(
                {'error': f'Invalid plan: {plan_identifier}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    user = request.user

    try:
        with transaction.atomic():
            # Get current subscription
            try:
                current_subscription = user.subscription
                old_plan = current_subscription.plan
            except UserSubscription.DoesNotExist:
                # Create new subscription
                current_subscription = None
                old_plan = None

            # Calculate base amount
            base_amount = plan.price_monthly or 0

            # Apply academic discount if active
            try:
                if hasattr(user, 'academic_discount') and user.academic_discount.is_active():
                    # Academic discount applies only to Pro (starter) and Premium tiers.
                    if plan.tier in ['starter', 'premium']:
                        base_amount = user.academic_discount.calculate_discounted_price(base_amount)
                        logger.info(f'Academic discount applied: {base_amount} KES')
            except Exception:
                pass

            # Apply promo code if provided
            promo_discount = Decimal('0')
            promo_code_obj = None
            if promo_code:
                # Prevent stacking: only one promo code per subscription
                # (A subscription that already has any promo redemption cannot apply another code.)
                from .models import PromoCodeRedemption
                if current_subscription and PromoCodeRedemption.objects.filter(subscription=current_subscription).exists():
                    return Response(
                        {'error': 'A promo code has already been applied to this subscription'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                success, discount_amount, error = apply_promo_code(promo_code, user, plan)
                if success:
                    promo_discount = discount_amount
                    from .models import PromotionalCode
                    promo_code_obj = PromotionalCode.objects.get(code=promo_code.upper())
                else:
                    return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

            # Calculate proration if upgrading existing subscription
            proration_amount = Decimal('0')
            if current_subscription and old_plan and old_plan != plan:
                proration_data = calculate_proration(
                    old_plan, plan,
                    current_subscription.current_period_start,
                    current_subscription.current_period_end
                )
                proration_amount = proration_data['proration_amount']
                logger.info(f'Proration calculated: {proration_amount} KES')

            # Calculate final amount
            final_amount = max(Decimal('0'), Decimal(str(base_amount)) - promo_discount + proration_amount)

            # Process payment if not mock and amount > 0
            if not mock_upgrade and final_amount > 0:
                success, transaction_id, error = attempt_payment_charge(
                    user=user,
                    amount=float(final_amount),
                    currency='KES',
                    description=f'Subscription upgrade to {plan.name}'
                )

                if not success:
                    return Response(
                        {'error': f'Payment failed: {error}'},
                        status=status.HTTP_402_PAYMENT_REQUIRED
                    )
            else:
                transaction_id = f'mock_upgrade_{timezone.now().timestamp()}'

            # Create or update subscription
            if current_subscription:
                current_subscription.plan = plan
                current_subscription.status = 'active'
                if not current_subscription.current_period_start:
                    current_subscription.current_period_start = timezone.now()
                if not current_subscription.current_period_end:
                    current_subscription.current_period_end = timezone.now() + timedelta(days=30)
            else:
                current_subscription = UserSubscription.objects.create(
                    user=user,
                    plan=plan,
                    status='active',
                    current_period_start=timezone.now(),
                    current_period_end=timezone.now() + timedelta(days=30),
                )

            # Set enhanced access for starter tier
            if plan.tier == 'starter':
                if not current_subscription.enhanced_access_expires_at:
                    current_subscription.enhanced_access_expires_at = timezone.now() + timedelta(days=180)

            current_subscription.save()

            # Create payment transaction
            transaction = PaymentTransaction.objects.create(
                user=user,
                subscription=current_subscription,
                amount=final_amount,
                currency='KES',
                status='completed',
                gateway_transaction_id=transaction_id,
                processed_at=timezone.now(),
            )

            # Record promo code redemption
            if promo_code_obj:
                record_promo_redemption(
                    promo_code_obj, user, current_subscription,
                    Decimal(str(base_amount)), promo_discount
                )

            # Generate invoice if payment was made
            if final_amount > 0:
                from .models import SubscriptionInvoice
                SubscriptionInvoice.objects.create(
                    invoice_number=SubscriptionInvoice.generate_invoice_number(),
                    user=user,
                    subscription=current_subscription,
                    transaction=transaction,
                    status='paid',
                    subtotal=Decimal(str(plan.price_monthly or 0)),
                    discount_amount=promo_discount,
                    total_amount=final_amount,
                    currency='KES',
                    invoice_date=timezone.now(),
                    due_date=timezone.now(),
                    paid_at=timezone.now(),
                    line_items=[{
                        'description': f'{plan.name} subscription upgrade',
                        'quantity': 1,
                        'unit_price': float(plan.price_monthly or 0),
                        'total': float(final_amount),
                    }],
                )

            logger.info(f'Upgrade successful: {user.email} → {plan.name} | Amount: {final_amount} KES')

            return Response({
                'success': True,
                'plan': plan.name,
                'tier': plan.tier,
                'amount_charged': float(final_amount),
                'promo_discount': float(promo_discount),
                'proration_amount': float(proration_amount),
                'message': 'Subscription upgraded successfully',
            }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f'Upgrade error for {user.email}: {e}', exc_info=True)
        return Response(
            {'error': f'Failed to upgrade subscription: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def stripe_webhook(request):
    """
    POST /api/v1/subscription/webhooks/stripe
    Handle Stripe webhooks.
    """

    stripe_key = os.environ.get('STRIPE_SECRET_KEY')
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')

    if not stripe_key or not webhook_secret:
        return Response({'error': 'Stripe not configured'}, status=status.HTTP_400_BAD_REQUEST)

    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        import stripe
        stripe.api_key = stripe_key
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except ValueError:
        return Response({'error': 'Invalid payload'}, status=status.HTTP_400_BAD_REQUEST)
    except stripe.error.SignatureVerificationError:
        return Response({'error': 'Invalid signature'}, status=status.HTTP_400_BAD_REQUEST)

    # Handle events
    from subscriptions.tasks import process_stripe_webhook_task
    process_stripe_webhook_task.delay(event)

    return Response({'status': 'received'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def billing_history(request):
    """
    GET /api/v1/subscription/billing-history
    Get user's billing history (payment transactions).
    """
    user = request.user

    # Get payment transactions for this user
    transactions = PaymentTransaction.objects.filter(
        user=user,
        status='completed'
    ).select_related('subscription', 'gateway').order_by('-created_at')[:12]  # Last 12 transactions

    billing_history = []
    for transaction in transactions:
        # Get plan name from subscription
        plan_name = 'Subscription'
        if transaction.subscription and transaction.subscription.plan:
            plan_name = transaction.subscription.plan.name.replace('_', ' ').title()

        billing_history.append({
            'id': str(transaction.id),
            'date': transaction.created_at.isoformat(),
            'amount': float(transaction.amount),
            'currency': transaction.currency,
            'status': transaction.status,
            'plan_name': plan_name,
            'description': f'{plan_name} - {transaction.created_at.strftime("%B %Y")}',
            'gateway_transaction_id': transaction.gateway_transaction_id,
        })

    # If no transactions but user has subscription, create entries from subscription periods
    if not billing_history:
        try:
            subscription = user.subscription
            if subscription:
                # Create billing entry for current period
                billing_history.append({
                    'id': f'sub_{subscription.id}',
                    'date': subscription.current_period_start.isoformat() if subscription.current_period_start else timezone.now().isoformat(),
                    'amount': float(subscription.plan.price_monthly or 0),
                    'currency': 'KES',
                    'status': subscription.status,
                    'plan_name': subscription.plan.name.replace('_', ' ').title(),
                    'description': f'{subscription.plan.name.replace("_", " ").title()} - {subscription.current_period_start.strftime("%B %Y") if subscription.current_period_start else timezone.now().strftime("%B %Y")}',
                    'gateway_transaction_id': subscription.stripe_subscription_id or 'subscription',
                })
        except UserSubscription.DoesNotExist:
            pass

    return Response({
        'billing_history': billing_history,
        'total': len(billing_history),
    }, status=status.HTTP_200_OK)


# ── NEW ENDPOINTS ────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_user_subscriptions(request):
    """
    GET /api/v1/subscription/users
    Return all user subscriptions with details for finance dashboard.
    Supports filtering by plan.
    """
    plan_id = request.query_params.get('plan')

    subscriptions = UserSubscription.objects.select_related('user', 'plan').filter(
        status__in=['active', 'trial']
    )

    if plan_id:
        subscriptions = subscriptions.filter(plan_id=plan_id)

    data = []
    for sub in subscriptions:
        cat = sub.plan.catalog or {}
        display = (cat.get('display_name') or '').strip() or sub.plan.name.replace('_', ' ').title()
        data.append({
            'id': str(sub.id),
            'user_id': str(sub.user.id),
            'user_email': sub.user.email,
            'user_name': sub.user.get_full_name() or sub.user.email,
            'plan_id': str(sub.plan.id),
            'plan_name': sub.plan.name,
            'plan_display_name': display,
            'plan_tier': sub.plan.tier,
            'billing_interval': getattr(sub, 'billing_interval', None) or sub.plan.billing_interval,
            'price_monthly': float(sub.plan.price_monthly or 0),
            'status': sub.status,
            'current_period_start': sub.current_period_start.isoformat() if sub.current_period_start else None,
            'current_period_end': sub.current_period_end.isoformat() if sub.current_period_end else None,
            'enhanced_access_expires_at': sub.enhanced_access_expires_at.isoformat() if sub.enhanced_access_expires_at else None,
            'days_remaining': (sub.current_period_end - timezone.now()).days if sub.current_period_end else None,
            'created_at': sub.created_at.isoformat(),
        })

    return Response(data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_plans(request):
    """
    GET /api/v1/subscription/plans
    Stream A student-listed plans + policy. Legacy: falls back to all plans if none match stream filter.
    """
    qs = SubscriptionPlan.objects.filter(
        stream=SubscriptionPlan.STREAM_STUDENT,
        is_listed=True,
    ).order_by('sort_order', 'name')
    if not qs.exists():
        qs = SubscriptionPlan.objects.all().order_by('sort_order', 'name', 'price_monthly')
    data = [_serialize_plan_for_api(p, include_counts=True) for p in qs]
    return Response({'plans': data, 'policy': get_stream_policy()}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def list_plans_public(request):
    """
    GET /api/v1/subscription/plans/public
    Student Stream A listed plans for marketing (no auth).
    """
    qs = SubscriptionPlan.objects.filter(
        stream=SubscriptionPlan.STREAM_STUDENT,
        is_listed=True,
    ).order_by('sort_order', 'name')
    if not qs.exists():
        qs = SubscriptionPlan.objects.all().order_by('sort_order', 'name', 'price_monthly')
    data = [_serialize_plan_for_api(p, include_counts=False) for p in qs]
    return Response({'plans': data, 'policy': get_stream_policy()}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def simulate_payment(request):
    """
    POST /api/v1/subscription/simulate-payment
    Simulates a full payment checkout (no real gateway).
    Body: { "plan": "starter_3" | "professional_7" | "free" }

    Flow mirrors a real payment success:
      1. Resolve plan
      2. Create/update UserSubscription (status=active, 30-day period)
      3. Set enhanced_access_expires_at for starter tier (180 days, first time only)
      4. Log a completed PaymentTransaction (sim_...)
      5. Sync MarketplaceProfile tier
    """
    plan_identifier = request.data.get('plan')
    if not plan_identifier:
        return Response({'error': 'plan is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        plan = SubscriptionPlan.objects.get(name=plan_identifier)
    except SubscriptionPlan.DoesNotExist:
        tier_map = {'starter_3': 'starter', 'professional_7': 'premium', 'free': 'free'}
        tier = tier_map.get(plan_identifier, plan_identifier)
        plan = SubscriptionPlan.objects.filter(tier=tier).first()
        if not plan:
            available = list(SubscriptionPlan.objects.values_list('name', 'tier', flat=False))
            return Response(
                {'error': f'Plan "{plan_identifier}" not found. Available: {available}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    user = request.user
    now = timezone.now()
    catalog = plan.catalog or {}

    # Billing interval: explicit body override (e.g. Premium monthly vs annual SKU on one plan row)
    billing_interval = request.data.get('billing_interval') or plan.billing_interval
    if plan.name == 'och_premium' and request.data.get('billing_interval') == 'annual':
        billing_interval = SubscriptionPlan.BILLING_ANNUAL
    elif plan.name == 'och_premium' and request.data.get('billing_interval') == 'monthly':
        billing_interval = SubscriptionPlan.BILLING_MONTHLY

    if billing_interval == SubscriptionPlan.BILLING_ANNUAL:
        period_days = 365
        charge_amount = plan.price_annual or 0
    else:
        period_days = 30
        charge_amount = plan.price_monthly or 0

    trial_days = int(catalog.get('trial_days') or 0)
    if plan.tier == TIER_FREE or plan.billing_interval == SubscriptionPlan.BILLING_NONE:
        trial_days = 0
    requires_pm = bool(catalog.get('trial_requires_payment_method'))
    payment_method_ref = (request.data.get('payment_method') or '').strip()
    payment_gateway = (request.data.get('gateway') or 'stripe').strip().lower()
    if requires_pm and trial_days > 0 and not payment_method_ref:
        return Response(
            {'error': 'Payment method is required to start a trial for this plan'},
            status=status.HTTP_400_BAD_REQUEST
        )
    sub_status = 'trial' if trial_days > 0 else 'active'
    trial_end = (now + timezone.timedelta(days=trial_days)) if trial_days > 0 else None

    try:
        with transaction.atomic():
            existing = UserSubscription.objects.filter(user=user).first()

            # Enhanced access: only set once per lifetime on first starter subscription
            enhanced_until = None
            if plan.tier == 'starter':
                if existing and existing.enhanced_access_expires_at:
                    enhanced_until = existing.enhanced_access_expires_at  # keep original window
                else:
                    enhanced_until = now + timezone.timedelta(days=180)

            subscription, _ = UserSubscription.objects.update_or_create(
                user=user,
                defaults={
                    'plan': plan,
                    'status': sub_status,
                    'billing_interval': billing_interval,
                    'trial_end': trial_end,
                    'current_period_start': now,
                    'current_period_end': now + timezone.timedelta(days=period_days),
                    'enhanced_access_expires_at': enhanced_until,
                    'payment_method_ref': payment_method_ref or None,
                    'payment_gateway': payment_gateway if payment_method_ref else None,
                    'payment_method_added_at': now if payment_method_ref else None,
                }
            )

            # Log simulated payment transaction
            import uuid as _uuid
            sim_tx_id = f'sim_{_uuid.uuid4().hex[:12]}'
            PaymentTransaction.objects.create(
                user=user,
                subscription=subscription,
                amount=charge_amount,
                currency='KES',
                status='completed',
                gateway_transaction_id=sim_tx_id,
                gateway_response={
                    'simulated': True,
                    'plan': plan.name,
                    'billing_interval': billing_interval,
                },
                processed_at=now,
            )

            # Sync MarketplaceProfile
            mp_map = {'free': 'free', 'starter': 'starter', 'premium': 'professional'}
            mp_tier = mp_map.get(plan.tier, 'free')
            try:
                mp = user.marketplace_profile
                mp.tier = mp_tier
                mp.last_updated_at = now
                mp.save(update_fields=['tier', 'last_updated_at'])
            except Exception:
                pass

            days_left = subscription.days_enhanced_left
            if plan.tier == 'premium':
                mode = 'professional'
            elif days_left and days_left > 0:
                mode = 'enhanced'
            else:
                mode = 'normal'

            logger.info(f'[simulate_payment] {user.email} → {plan.name} | tx={sim_tx_id} | mode={mode}')

            return Response({
                'success': True,
                'transaction_id': sim_tx_id,
                'plan': plan.name,
                'tier': plan.tier,
                'mode': mode,
                'enhanced_access_days_left': days_left,
                'period_end': subscription.current_period_end,
                'message': f'Payment simulated. You are now on the {plan.name} plan.',
            }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f'[simulate_payment] Error for {user.email}: {e}')
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_subscription(request):
    """
    POST /api/v1/subscription/cancel
    Marks subscription as canceled. Access continues until current_period_end;
    the scheduler then downgrades to Free Tier automatically.
    """
    user = request.user
    try:
        subscription = user.subscription
    except UserSubscription.DoesNotExist:
        return Response({'error': 'No active subscription found'}, status=status.HTTP_404_NOT_FOUND)

    if subscription.status == 'canceled':
        return Response({'error': 'Subscription is already canceled'}, status=status.HTTP_400_BAD_REQUEST)

    cancel_type = (request.data.get('type') or request.data.get('cancellation_type') or 'end_of_period').strip().lower()
    if cancel_type not in ['end_of_period', 'immediate']:
        return Response({'error': 'type must be end_of_period or immediate'}, status=status.HTTP_400_BAD_REQUEST)

    if cancel_type == 'immediate':
        # Immediate cancellation: revoke access immediately by ending the period now.
        subscription.status = 'canceled'
        subscription.cancel_at_period_end = False
        subscription.current_period_end = timezone.now()
        subscription.save(update_fields=['status', 'cancel_at_period_end', 'current_period_end', 'updated_at'])
        access_until = subscription.current_period_end
        message = 'Subscription canceled immediately. Access has ended.'
    else:
        # Default: end-of-period cancellation.
        subscription.status = 'canceled'
        subscription.cancel_at_period_end = True
        subscription.save(update_fields=['status', 'cancel_at_period_end', 'updated_at'])
        access_until = subscription.current_period_end
        message = 'Subscription canceled. You retain access until the end of your billing period.'

    logger.info(f'[cancel_subscription] {user.email} canceled. Access until {subscription.current_period_end}')

    return Response({
        'success': True,
        'message': message,
        'access_until': access_until,
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_legacy_trial_payment_method(request):
    """
    POST /api/v1/subscription/payment-method
    Save a payment method for a legacy trial and auto-convert to active immediately.
    Body: { "payment_method": "pm_...", "gateway": "stripe"|"paystack" }
    """
    from datetime import timedelta
    import calendar

    payment_method_ref = (request.data.get('payment_method') or '').strip()
    payment_gateway = (request.data.get('gateway') or 'stripe').strip().lower()
    if not payment_method_ref:
        return Response({'error': 'payment_method is required'}, status=status.HTTP_400_BAD_REQUEST)
    if payment_gateway not in ['stripe', 'paystack']:
        return Response({'error': 'gateway must be stripe or paystack'}, status=status.HTTP_400_BAD_REQUEST)

    user = request.user
    try:
        sub = user.subscription
    except UserSubscription.DoesNotExist:
        return Response({'error': 'No subscription found'}, status=status.HTTP_404_NOT_FOUND)

    if sub.status != 'trial':
        return Response({'error': 'No active trial subscription found'}, status=status.HTTP_400_BAD_REQUEST)
    if sub.trial_end and timezone.now() > sub.trial_end:
        return Response({'error': 'Trial has already ended'}, status=status.HTTP_400_BAD_REQUEST)

    now = timezone.now()

    def add_month_anchored(dt):
        # dt + 1 calendar month, clamp day
        year = dt.year + (dt.month // 12)
        month = dt.month % 12 + 1
        last_day = calendar.monthrange(year, month)[1]
        day = min(dt.day, last_day)
        return dt.replace(year=year, month=month, day=day)

    # Convert to active immediately (billing starts now)
    sub.payment_method_ref = payment_method_ref
    sub.payment_gateway = payment_gateway
    sub.payment_method_added_at = now
    sub.status = 'active'
    sub.cancel_at_period_end = False
    sub.current_period_start = now
    if sub.billing_interval == SubscriptionPlan.BILLING_ANNUAL:
        try:
            sub.current_period_end = now.replace(year=now.year + 1)
        except ValueError:
            sub.current_period_end = now.replace(year=now.year + 1, month=2, day=28)
    else:
        sub.current_period_end = add_month_anchored(now)
    sub.save(update_fields=[
        'payment_method_ref', 'payment_gateway', 'payment_method_added_at',
        'status', 'cancel_at_period_end', 'current_period_start', 'current_period_end',
        'updated_at'
    ])

    return Response({
        'success': True,
        'message': 'Payment method saved. Trial converted to active subscription.',
        'subscription': {
            'id': str(sub.id),
            'status': sub.status,
            'current_period_end': sub.current_period_end.isoformat() if sub.current_period_end else None,
        }
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def schedule_downgrade(request):
    """
    POST /api/v1/subscription/downgrade
    Schedule a downgrade effective at current_period_end (no refunds).
    Body: { "plan": "<plan_name>" }
    """
    plan_identifier = (request.data.get('plan') or '').strip()
    if not plan_identifier:
        return Response({'error': 'plan is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        new_plan = SubscriptionPlan.objects.get(name=plan_identifier)
    except SubscriptionPlan.DoesNotExist:
        return Response({'error': 'Invalid plan'}, status=status.HTTP_400_BAD_REQUEST)

    user = request.user
    try:
        sub = user.subscription
    except UserSubscription.DoesNotExist:
        return Response({'error': 'No active subscription found'}, status=status.HTTP_404_NOT_FOUND)

    if sub.plan_id == new_plan.id:
        return Response({'error': 'Already on that plan'}, status=status.HTTP_400_BAD_REQUEST)

    sub.pending_downgrade_plan = new_plan
    sub.save(update_fields=['pending_downgrade_plan', 'updated_at'])

    try:
        from .email_service import SubscriptionEmailService
        SubscriptionEmailService.send_downgrade_scheduled_email(
            user=user,
            current_plan_name=sub.plan.name,
            new_plan_name=new_plan.name,
            effective_date=sub.current_period_end or timezone.now(),
        )
    except Exception:
        pass

    return Response({
        'success': True,
        'message': 'Downgrade scheduled',
        'effective_date': sub.current_period_end,
        'pending_plan': new_plan.name,
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_scheduled_downgrade(request):
    """
    POST /api/v1/subscription/downgrade/cancel
    Remove any scheduled downgrade before period end.
    """
    user = request.user
    try:
        sub = user.subscription
    except UserSubscription.DoesNotExist:
        return Response({'error': 'No active subscription found'}, status=status.HTTP_404_NOT_FOUND)

    sub.pending_downgrade_plan = None
    sub.save(update_fields=['pending_downgrade_plan', 'updated_at'])

    return Response({'success': True, 'message': 'Scheduled downgrade canceled'}, status=status.HTTP_200_OK)


# ── Paystack ─────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def paystack_config(request):
    """
    GET /api/v1/subscription/paystack/config?plan=starter_3
    Returns Paystack popup config: amount_in_kobo, currency, plan name.
    Public key should be set in frontend env (NEXT_PUBLIC_PAYSTACK_PUBLIC_KEY).
    """
    plan_identifier = request.query_params.get('plan')
    if not plan_identifier:
        return Response({'error': 'plan is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        plan = SubscriptionPlan.objects.get(name=plan_identifier)
    except SubscriptionPlan.DoesNotExist:
        tier_map = {'starter_3': 'starter', 'professional_7': 'premium', 'free': 'free'}
        tier = tier_map.get(plan_identifier, plan_identifier)
        plan = SubscriptionPlan.objects.filter(tier=tier).first()
        if not plan:
            return Response(
                {'error': f'Plan "{plan_identifier}" not found'},
                status=status.HTTP_400_BAD_REQUEST
            )

    default_currency = (os.environ.get('PAYSTACK_DEFAULT_CURRENCY') or 'KES').upper()
    if not plan.price_monthly or float(plan.price_monthly) <= 0:
        return Response({
            'amount_in_kobo': 0,
            'currency': default_currency,
            'plan': plan.name,
            'tier': plan.tier,
            'message': 'Free plan — no payment required',
            'default_currency': default_currency,
            'supported_channels': ['card', 'bank', 'mobile_money', 'ussd', 'bank_transfer'],
            'billing_intervals': ['monthly', 'yearly'],
        }, status=status.HTTP_200_OK)

    # KES: amount in cents (smallest unit; 100 KES = 10000 cents). Merchant uses KES.
    usd_per_month = float(plan.price_monthly)
    kes_per_month = usd_per_month * 130  # rough USD to KES
    amount_in_cents = int(round(kes_per_month * 100))
    if amount_in_cents < 10000:
        amount_in_cents = 10000  # Paystack min e.g. 100 KES
    return Response({
        'amount_in_kobo': amount_in_cents,
        'currency': default_currency,
        'plan': plan.name,
        'tier': plan.tier,
        'default_currency': default_currency,
        'supported_channels': ['card', 'bank', 'mobile_money', 'ussd', 'bank_transfer'],
        'billing_intervals': ['monthly', 'yearly'],
    }, status=status.HTTP_200_OK)


def _paystack_plan_and_amount(plan_identifier, interval=None):
    """Resolve plan and return (plan, amount_in_cents) for KES. amount_in_cents 0 if free.
    For Kenya we treat SubscriptionPlan.price_monthly as KSh directly.
    If interval=='yearly', charge 12 × monthly KSh (any discount should be encoded in the plan price).
    """
    try:
        plan = SubscriptionPlan.objects.get(name=plan_identifier)
    except SubscriptionPlan.DoesNotExist:
        tier_map = {'starter_3': 'starter', 'professional_7': 'premium', 'free': 'free'}
        tier = tier_map.get(plan_identifier, plan_identifier)
        plan = SubscriptionPlan.objects.filter(tier=tier).first()
        if not plan:
            return None, 0
    if not plan.price_monthly or float(plan.price_monthly) <= 0:
        return plan, 0
    if interval == 'yearly':
        kes_amount = float(plan.price_monthly) * 12.0
    else:
        kes_amount = float(plan.price_monthly)
    amount_in_cents = int(round(kes_amount * 100))
    # Do not clamp to a higher minimum here – send the exact KSh amount.
    # If Paystack enforces a higher minimum, it will reject the transaction.
    return plan, amount_in_cents


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def paystack_initialize(request):
    """
    POST /api/v1/subscription/paystack/initialize
    Body: { "plan": "starter_3", "callback_url": "https://..." } (callback_url optional)
    Initializes transaction on Paystack with KES from backend so currency is supported.
    Returns { authorization_url, reference }.
    """
    plan_identifier = (request.data.get('plan') or '').strip()
    interval = (request.data.get('interval') or '').strip().lower()
    if interval != 'yearly':
        interval = None

    plan, amount_in_cents = _paystack_plan_and_amount(plan_identifier, interval=interval)
    if not plan:
        return Response({'error': f'Plan "{plan_identifier}" not found'}, status=status.HTTP_400_BAD_REQUEST)
    if amount_in_cents <= 0:
        return Response({'error': 'Free plan — use simulate-payment'}, status=status.HTTP_400_BAD_REQUEST)

    secret_key = os.environ.get('PAYSTACK_SECRET_KEY') or os.environ.get('PAYSTACK_SECRET')
    if not secret_key:
        logger.error('PAYSTACK_SECRET_KEY not configured')
        return Response({'error': 'Payment provider not configured'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    email = getattr(request.user, 'email', None) or ''
    if not email:
        return Response({'error': 'User email required'}, status=status.HTTP_400_BAD_REQUEST)

    reference = f"och_{int(timezone.now().timestamp())}_{request.user.id}_{''.join(random.choices(string.ascii_lowercase + string.digits, k=8))}"
    callback_url = (request.data.get('callback_url') or os.environ.get('PAYSTACK_CALLBACK_URL', '')).strip()
    if callback_url:
        callback_url = f"{callback_url.rstrip('/')}?reference={reference}"

    metadata = {'plan': plan.name}
    if interval == 'yearly':
        metadata['interval'] = 'yearly'
    default_currency = (os.environ.get('PAYSTACK_DEFAULT_CURRENCY') or 'KES').upper()
    currency = (request.data.get('currency') or default_currency).upper()
    payload = {
        'email': email,
        'amount': amount_in_cents,
        'currency': currency,
        'reference': reference,
        'metadata': metadata,
    }
    if callback_url:
        payload['callback_url'] = callback_url

    channels = request.data.get('channels')
    if channels:
        if isinstance(channels, str):
            try:
                channels = json.loads(channels)
            except json.JSONDecodeError:
                channels = [c.strip() for c in channels.split(',') if c.strip()]
        if isinstance(channels, list) and channels:
            payload['channels'] = channels

    try:
        resp = requests.post(
            PAYSTACK_INITIALIZE_URL,
            headers={
                'Authorization': f'Bearer {secret_key}',
                'Content-Type': 'application/json',
            },
            json=payload,
            timeout=10,
        )
        data = resp.json()
    except requests.RequestException:
        logger.exception('Paystack initialize request failed')
        return Response({'error': 'Could not start payment'}, status=status.HTTP_502_BAD_GATEWAY)

    if not data.get('status'):
        msg = data.get('message', 'Currency not supported by merchant or invalid request')
        return Response({'error': msg}, status=status.HTTP_400_BAD_REQUEST)

    inner = data.get('data') or {}
    authorization_url = inner.get('authorization_url')
    if not authorization_url:
        return Response({'error': 'No authorization URL from Paystack'}, status=status.HTTP_502_BAD_GATEWAY)

    return Response({
        'authorization_url': authorization_url,
        'reference': reference,
        'currency': currency,
        'channels': payload.get('channels'),
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def paystack_verify(request):
    """
    POST /api/v1/subscription/paystack/verify
    Body: { "reference": "paystack_ref_from_popup" }
    Verifies the transaction with Paystack, then creates/updates subscription and payment record.
    """
    reference = (request.data.get('reference') or '').strip()
    if not reference:
        return Response({'error': 'reference is required'}, status=status.HTTP_400_BAD_REQUEST)

    secret_key = os.environ.get('PAYSTACK_SECRET_KEY') or os.environ.get('PAYSTACK_SECRET')
    if not secret_key:
        logger.error('PAYSTACK_SECRET_KEY not configured')
        return Response({'error': 'Payment provider not configured'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    try:
        resp = requests.get(
            PAYSTACK_VERIFY_URL.format(reference),
            headers={'Authorization': f'Bearer {secret_key}'},
            timeout=10,
        )
        data = resp.json()
    except requests.RequestException:
        logger.exception('Paystack verify request failed')
        return Response({'error': 'Verification request failed'}, status=status.HTTP_502_BAD_GATEWAY)

    if not data.get('status'):
        return Response(
            {'error': data.get('message', 'Verification failed')},
            status=status.HTTP_400_BAD_REQUEST
        )

    payload = data.get('data') or {}
    tx_status = payload.get('status')
    if tx_status != 'success':
        return Response(
            {'error': f'Transaction not successful: {tx_status}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Idempotency: already processed this reference
    if PaymentTransaction.objects.filter(gateway_transaction_id=reference, status='completed').exists():
        return Response({
            'success': True,
            'message': 'Payment already applied',
            'reference': reference,
        }, status=status.HTTP_200_OK)

    # Resolve plan from metadata (frontend sends metadata.plan or custom_fields)
    metadata = payload.get('metadata') or {}
    custom_fields = metadata.get('custom_fields') or []
    plan_name = metadata.get('plan')
    if not plan_name:
        for cf in custom_fields:
            if cf.get('display_name') == 'Plan' or cf.get('variable_name') == 'plan':
                plan_name = cf.get('value')
                break

    if not plan_name:
        return Response({'error': 'Plan not found in payment metadata'}, status=status.HTTP_400_BAD_REQUEST)

    is_yearly = (metadata.get('interval') or '').lower() == 'yearly'

    try:
        plan = SubscriptionPlan.objects.get(name=plan_name)
    except SubscriptionPlan.DoesNotExist:
        tier_map = {'starter_3': 'starter', 'professional_7': 'premium', 'free': 'free'}
        plan = SubscriptionPlan.objects.filter(tier=tier_map.get(plan_name, plan_name)).first()
        if not plan:
            return Response({'error': f'Plan "{plan_name}" not found'}, status=status.HTTP_400_BAD_REQUEST)

    user = request.user
    try:
        _apply_paystack_payment(user=user, plan=plan, payload=payload, reference=reference, is_yearly=is_yearly)
    except Exception as e:
        logger.exception('Paystack verify DB error')
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    logger.info(f'[paystack_verify] {user.email} → {plan.name} ref={reference}')
    return Response({
        'success': True,
        'message': 'Payment verified and subscription activated',
        'plan': plan.name,
        'tier': plan.tier,
        'reference': reference,
    }, status=status.HTTP_200_OK)


def _apply_paystack_payment(user, plan, payload, reference, is_yearly=False):
    """Apply a successful Paystack payment: create/update subscription and transaction. Idempotent by reference."""
    amount = float(payload.get('amount', 0)) / 100.0  # amount in KES from Paystack
    currency = payload.get('currency', 'KES')
    auth = payload.get('authorization') or {}
    authorization_code = (auth.get('authorization_code') or '').strip() or None
    period_days = 365 if is_yearly else 30
    # For Kenya we store the actual KSh amount that was charged.
    stored_amount = amount

    with transaction.atomic():
        existing = UserSubscription.objects.filter(user=user).first()
        enhanced_until = None
        if plan.tier == 'starter':
            if existing and existing.enhanced_access_expires_at:
                enhanced_until = existing.enhanced_access_expires_at
            else:
                enhanced_until = timezone.now() + timezone.timedelta(days=180)

        subscription, _ = UserSubscription.objects.update_or_create(
            user=user,
            defaults={
                'plan': plan,
                'status': 'active',
                'current_period_start': timezone.now(),
                'current_period_end': timezone.now() + timezone.timedelta(days=period_days),
                'enhanced_access_expires_at': enhanced_until,
                # Store Paystack authorization for future off-session charges
                'payment_gateway': 'paystack' if authorization_code else None,
                'payment_method_ref': authorization_code,
                'payment_method_added_at': timezone.now() if authorization_code else None,
            }
        )

        # If the enhanced billing engine subscription exists for this user, store the same Paystack
        # authorization_code so renewals/dunning/reactivation can charge via Paystack consistently.
        if authorization_code:
            try:
                # Use a savepoint so missing-table errors (or other DB issues) don't poison the
                # surrounding atomic() transaction.
                with transaction.atomic():
                    from .billing_engine import EnhancedSubscription as EngineSubscription
                    EngineSubscription.objects.filter(user=user).update(
                        payment_gateway='paystack',
                        payment_method_ref=authorization_code,
                        payment_method_added_at=timezone.now(),
                        updated_at=timezone.now(),
                    )
            except Exception:
                # Don't block payment application on enhanced-engine sync.
                pass

        gateway = PaymentGateway.objects.filter(name='paystack').first()
        PaymentTransaction.objects.create(
            user=user,
            gateway=gateway,
            subscription=subscription,
            amount=stored_amount,
            currency=currency or 'KES',
            status='completed',
            gateway_transaction_id=reference,
            gateway_response=payload,
            processed_at=timezone.now(),
        )

        mp_map = {'free': 'free', 'starter': 'starter', 'premium': 'professional'}
        mp_tier = mp_map.get(plan.tier, 'free')
        try:
            mp = user.marketplace_profile
            mp.tier = mp_tier
            mp.last_updated_at = timezone.now()
            mp.save(update_fields=['tier', 'last_updated_at'])
        except Exception:
            pass


def _paystack_webhook_signature_valid(raw_body: bytes, signature: str, secret: str) -> bool:
    """HMAC SHA512 hex of raw body must match X-Paystack-Signature (Paystack docs)."""
    if not secret:
        return True
    sig = (signature or '').strip()
    if not sig:
        return False
    computed = hmac.new(secret.encode('utf-8'), raw_body, hashlib.sha512).hexdigest()
    if len(sig) != len(computed):
        return False
    return hmac.compare_digest(computed, sig)


@csrf_exempt
@require_POST
def paystack_webhook(request):
    """
    POST /paystack/webhook/ or /api/v1/subscription/webhooks/paystack/
    Paystack sends events (charge.success). No auth; verify X-Paystack-Signature over raw body.

    Implemented as a plain Django view (not DRF) so the raw body is untouched, JSON errors
    return small JSON (not DRF browsable HTML), and HMAC length mismatches cannot 500.

    Dashboard: https://dashboard.paystack.com/#/settings/developers
    """
    raw_body = request.body or b''
    signature = request.META.get('HTTP_X_PAYSTACK_SIGNATURE', '') or ''
    secret = os.environ.get('PAYSTACK_SECRET_KEY') or os.environ.get('PAYSTACK_SECRET')

    if not secret:
        logger.warning('Paystack webhook: PAYSTACK_SECRET_KEY not set, accepting without verification')
    elif not _paystack_webhook_signature_valid(raw_body, signature, secret):
        logger.warning('Paystack webhook: invalid signature')
        return JsonResponse({'received': True, 'ignored': 'invalid_signature'}, status=200)

    try:
        text = raw_body.decode('utf-8')
    except UnicodeDecodeError as e:
        logger.warning('Paystack webhook: body not utf-8: %s', e)
        return JsonResponse({'error': 'Invalid encoding'}, status=400)

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        logger.warning('Paystack webhook: invalid JSON %s body_prefix=%r', e, raw_body[:500])
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    event = data.get('event')
    if event != 'charge.success':
        return JsonResponse({'received': True}, status=200)

    payload = data.get('data') or {}
    reference = (payload.get('reference') or '').strip()
    if not reference:
        return JsonResponse({'received': True}, status=200)

    # Cohort payments use references like "OCH-...". Route these to cohorts payment verification.
    # This allows a single whitelisted webhook URL (/paystack/webhook/) to cover both subscriptions and cohorts.
    if reference.startswith('OCH-'):
        try:
            from cohorts.services.payment_service import paystack_service as cohort_paystack_service

            cohort_paystack_service.verify_payment(reference)
            logger.info('[paystack_webhook] cohort charge.success ref=%s', reference)
        except Exception as e:
            logger.exception('Paystack webhook cohort apply failed: %s', e)
            return JsonResponse({'received': False, 'error': 'cohort_apply_failed'}, status=500)

        return JsonResponse({'received': True}, status=200)

    if PaymentTransaction.objects.filter(gateway_transaction_id=reference, status='completed').exists():
        return JsonResponse({'received': True, 'duplicate': True}, status=200)

    metadata = payload.get('metadata') or {}
    plan_name = metadata.get('plan')
    if not plan_name:
        for cf in metadata.get('custom_fields') or []:
            if cf.get('display_name') == 'Plan' or cf.get('variable_name') == 'plan':
                plan_name = (cf.get('value') or '').strip()
                break
    if not plan_name:
        return JsonResponse({'received': True, 'ignored': 'no_plan_in_metadata'}, status=200)

    is_yearly = (metadata.get('interval') or '').lower() == 'yearly'

    try:
        plan = SubscriptionPlan.objects.get(name=plan_name)
    except SubscriptionPlan.DoesNotExist:
        tier_map = {'starter_3': 'starter', 'professional_7': 'premium', 'Monthly Plan': 'starter', 'Yearly Plan': 'premium'}
        plan = SubscriptionPlan.objects.filter(tier=tier_map.get(plan_name, plan_name)).first()
        if not plan:
            logger.warning('Paystack webhook: plan not found %s', plan_name)
            return JsonResponse({'received': True, 'ignored': 'plan_not_found'}, status=200)

    user = None
    match = re.match(r'^och_(\d+)_(\d+)_([a-z0-9]+)$', reference)
    if match:
        try:
            user_id = int(match.group(2))
            user = User.objects.get(id=user_id)
        except (ValueError, User.DoesNotExist):
            pass
    if not user and payload.get('customer'):
        customer = payload.get('customer') or {}
        email = (customer.get('email') or '').strip()
        if email:
            user = User.objects.filter(email__iexact=email).first()

    if not user:
        logger.warning('Paystack webhook: could not resolve user for reference=%s', reference)
        return JsonResponse({'received': True, 'ignored': 'user_not_found'}, status=200)

    try:
        _apply_paystack_payment(user=user, plan=plan, payload=payload, reference=reference, is_yearly=is_yearly)
        logger.info('[paystack_webhook] charge.success ref=%s user=%s plan=%s', reference, user.email, plan.name)
    except Exception as e:
        logger.exception('Paystack webhook apply payment failed: %s', e)
        return JsonResponse({'received': False, 'error': 'apply_failed'}, status=500)

    return JsonResponse({'received': True}, status=200)

# ── PROMOTIONAL CODES ────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_promo_code(request):
    """
    POST /api/v1/subscription/promo-code/validate
    Validate promotional code without applying it.
    Body: {"code": "CYBER2026", "plan": "starter_3"}
    """
    from .models import SubscriptionPlan
    from .utils import apply_promo_code

    code = request.data.get('code', '').strip()
    plan_name = request.data.get('plan', '').strip()

    if not code:
        return Response({'error': 'Code is required'}, status=status.HTTP_400_BAD_REQUEST)

    if not plan_name:
        return Response({'error': 'Plan is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        plan = SubscriptionPlan.objects.get(name=plan_name)
    except SubscriptionPlan.DoesNotExist:
        return Response({'error': 'Invalid plan'}, status=status.HTTP_400_BAD_REQUEST)

    success, discount_amount, error = apply_promo_code(code, request.user, plan)

    if success:
        base_amount = float(plan.price_monthly or 0)
        final_amount = base_amount - float(discount_amount)

        return Response({
            'valid': True,
            'code': code.upper(),
            'discount_amount': float(discount_amount),
            'base_amount': base_amount,
            'final_amount': max(0, final_amount),
            'discount_type': 'percentage' if discount_amount < base_amount else 'fixed',
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'valid': False,
            'error': error,
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def promo_code_history(request):
    """
    GET /api/v1/subscription/promo-code/history
    Get user's promo code redemption history.
    """
    from .models import PromoCodeRedemption

    redemptions = PromoCodeRedemption.objects.filter(
        user=request.user
    ).select_related('code').order_by('-redeemed_at')[:10]

    data = []
    for redemption in redemptions:
        data.append({
            'id': str(redemption.id),
            'code': redemption.code.code,
            'discount_applied': float(redemption.discount_applied),
            'original_amount': float(redemption.original_amount),
            'final_amount': float(redemption.final_amount),
            'redeemed_at': redemption.redeemed_at.isoformat(),
        })

    return Response(data, status=status.HTTP_200_OK)


# ── ACADEMIC DISCOUNTS ───────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def apply_academic_discount(request):
    """
    POST /api/v1/subscription/academic-discount/apply
    Apply for academic discount verification.
    Body: {
        "method": "edu_email" | "document",
        "edu_email": "student@university.edu" (if method=edu_email),
        "institution_name": "University Name",
        "document_url": "https://..." (if method=document)
    }
    """
    from .models import AcademicDiscount

    method = request.data.get('method', '').strip()
    edu_email = request.data.get('edu_email', '').strip()
    institution_name = request.data.get('institution_name', '').strip()
    document_url = request.data.get('document_url', '').strip()

    if method not in ['edu_email', 'document']:
        return Response({'error': 'Invalid verification method'}, status=status.HTTP_400_BAD_REQUEST)

    if method == 'edu_email' and not edu_email.endswith('.edu'):
        return Response({'error': 'Please provide a valid .edu email address'}, status=status.HTTP_400_BAD_REQUEST)

    if method == 'document' and not document_url:
        return Response({'error': 'Document URL is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Check if user already has academic discount
        try:
            existing = request.user.academic_discount
            if existing.verification_status == 'verified':
                return Response({'error': 'You already have a verified academic discount'}, status=status.HTTP_400_BAD_REQUEST)
            elif existing.verification_status == 'pending':
                return Response({'error': 'Your academic discount application is pending review'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Update existing application
                existing.verification_method = method
                existing.verification_status = 'pending'
                existing.edu_email = edu_email if method == 'edu_email' else None
                existing.institution_name = institution_name
                existing.document_url = document_url if method == 'document' else None
                existing.save()
                discount = existing
        except AcademicDiscount.DoesNotExist:
            # Create new application
            discount = AcademicDiscount.objects.create(
                user=request.user,
                verification_method=method,
                verification_status='pending',
                edu_email=edu_email if method == 'edu_email' else None,
                institution_name=institution_name,
                document_url=document_url if method == 'document' else None,
            )

        # Auto-verify .edu emails
        if method == 'edu_email':
            discount.verification_status = 'verified'
            discount.verified_at = timezone.now()
            discount.expires_at = timezone.now() + timezone.timedelta(days=365)  # 1 year
            discount.save()

            return Response({
                'success': True,
                'status': 'verified',
                'discount_percentage': 30,
                'expires_at': discount.expires_at.isoformat(),
                'message': 'Academic discount verified successfully!',
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': True,
                'status': 'pending',
                'message': 'Academic discount application submitted for review. You will be notified within 1-2 business days.',
            }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f'Academic discount application error: {e}')
        return Response({'error': 'Failed to process application'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def academic_discount_status(request):
    """
    GET /api/v1/subscription/academic-discount/status
    Get user's academic discount status.
    """
    try:
        discount = request.user.academic_discount
        return Response({
            'has_discount': True,
            'status': discount.verification_status,
            'method': discount.verification_method,
            'institution_name': discount.institution_name,
            'verified_at': discount.verified_at.isoformat() if discount.verified_at else None,
            'expires_at': discount.expires_at.isoformat() if discount.expires_at else None,
            'is_active': discount.is_active(),
            'discount_percentage': discount.get_discount_percentage(),
            'rejection_reason': discount.rejection_reason if discount.verification_status == 'rejected' else None,
        }, status=status.HTTP_200_OK)
    except:
        return Response({
            'has_discount': False,
            'status': None,
        }, status=status.HTTP_200_OK)


# ── ADVANCED ANALYTICS ───────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def subscription_analytics(request):
    """
    GET /api/v1/subscription/analytics
    Get advanced subscription analytics for finance dashboard.
    """
    from datetime import timedelta

    from django.db.models import Avg, Count, Q, Sum
    from django.db.models.functions import TruncMonth

    # Check if user has finance role
    if not request.user.user_roles.filter(role__name='finance').exists():
        return Response({'error': 'Finance role required'}, status=status.HTTP_403_FORBIDDEN)

    now = timezone.now()
    last_month = now - timedelta(days=30)
    now - timedelta(days=90)

    # Basic metrics
    total_subscriptions = UserSubscription.objects.filter(status='active').count()
    total_revenue = PaymentTransaction.objects.filter(
        status='completed',
        created_at__gte=last_month
    ).aggregate(total=Sum('amount'))['total'] or 0

    # MRR (Monthly Recurring Revenue)
    mrr = UserSubscription.objects.filter(
        status='active'
    ).select_related('plan').aggregate(
        mrr=Sum('plan__price_monthly')
    )['mrr'] or 0

    # Churn rate (canceled in last 30 days / total active 30 days ago)
    canceled_last_month = UserSubscription.objects.filter(
        status='canceled',
        updated_at__gte=last_month
    ).count()

    active_last_month = UserSubscription.objects.filter(
        Q(status='active') | Q(status='canceled', updated_at__gte=last_month)
    ).count()

    churn_rate = (canceled_last_month / max(active_last_month, 1)) * 100

    # Plan breakdown
    plan_breakdown = UserSubscription.objects.filter(
        status='active'
    ).values('plan__name', 'plan__tier').annotate(
        count=Count('id'),
        revenue=Sum('plan__price_monthly')
    ).order_by('-count')

    # Monthly revenue trend (last 6 months)
    revenue_trend = PaymentTransaction.objects.filter(
        status='completed',
        created_at__gte=now - timedelta(days=180)
    ).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        revenue=Sum('amount'),
        transactions=Count('id')
    ).order_by('month')

    # Failed payments
    failed_payments = PaymentRetryAttempt.objects.filter(
        status='failed',
        created_at__gte=last_month
    ).count()

    # Grace period stats
    past_due_count = UserSubscription.objects.filter(status='past_due').count()

    # Promo code usage
    promo_usage = PromoCodeRedemption.objects.filter(
        redeemed_at__gte=last_month
    ).aggregate(
        total_redemptions=Count('id'),
        total_discount=Sum('discount_applied'),
        avg_discount=Avg('discount_applied'),
        total_original=Sum('original_amount'),
    )

    # Academic discounts
    academic_stats = AcademicDiscount.objects.aggregate(
        total_applications=Count('id'),
        verified=Count('id', filter=Q(verification_status='verified')),
        pending=Count('id', filter=Q(verification_status='pending')),
    )

    return Response({
        'overview': {
            'total_subscriptions': total_subscriptions,
            'monthly_revenue': float(total_revenue),
            'mrr': float(mrr),
            'churn_rate': round(churn_rate, 2),
        },
        'plan_breakdown': [
            {
                'plan_name': item['plan__name'],
                'plan_tier': item['plan__tier'],
                'subscribers': item['count'],
                'revenue': float(item['revenue'] or 0),
            }
            for item in plan_breakdown
        ],
        'revenue_trend': [
            {
                'month': item['month'].strftime('%Y-%m'),
                'revenue': float(item['revenue']),
                'transactions': item['transactions'],
            }
            for item in revenue_trend
        ],
        'payment_health': {
            'failed_payments_last_month': failed_payments,
            'past_due_subscriptions': past_due_count,
        },
        'promotions': {
            'redemptions_last_month': promo_usage['total_redemptions'] or 0,
            'discount_given_last_month': float(promo_usage['total_discount'] or 0),
            'average_discount_last_month': float(promo_usage['avg_discount'] or 0),
            'gross_revenue_covered_last_month': float(promo_usage['total_original'] or 0),
            'discount_rate_last_month': (
                float((promo_usage['total_discount'] or 0) / (promo_usage['total_original'] or 1) * 100)
                if (promo_usage['total_original'] or 0) > 0
                else 0.0
            ),
        },
        'academic_discounts': {
            'total_applications': academic_stats['total_applications'],
            'verified': academic_stats['verified'],
            'pending_review': academic_stats['pending'],
        },
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def retry_attempts_status(request):
    """
    GET /api/v1/subscription/retry-attempts
    Get payment retry attempts for finance dashboard.
    """
    if not request.user.user_roles.filter(role__name='finance').exists():
        return Response({'error': 'Finance role required'}, status=status.HTTP_403_FORBIDDEN)

    from .models import PaymentRetryAttempt

    # Get pending and recent retry attempts
    attempts = PaymentRetryAttempt.objects.filter(
        scheduled_at__gte=timezone.now() - timedelta(days=7)
    ).select_related('subscription', 'subscription__user', 'subscription__plan').order_by('-scheduled_at')[:50]

    data = []
    for attempt in attempts:
        data.append({
            'id': str(attempt.id),
            'user_email': attempt.subscription.user.email,
            'plan_name': attempt.subscription.plan.name,
            'attempt_number': attempt.attempt_number,
            'status': attempt.status,
            'amount': float(attempt.amount),
            'currency': attempt.currency,
            'scheduled_at': attempt.scheduled_at.isoformat(),
            'attempted_at': attempt.attempted_at.isoformat() if attempt.attempted_at else None,
            'error_message': attempt.error_message,
        })

    return Response(data, status=status.HTTP_200_OK)
