"""
Enhanced Billing API Views - Academic Discounts and Promotional Codes
"""
import logging
from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from programs.permissions import IsProgramDirector
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .billing_engine import EnhancedSubscription, SubscriptionPlanVersion
from .enhanced_billing_services import (
    AcademicDiscountService,
    EnhancedTrialService,
    PromotionalCodeService,
)
from .promotional_models import (
    AcademicDiscount,
    PromotionalCode,
)

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def verify_academic_email(request):
    """
    POST /api/enhanced-billing/academic/verify-email/
    Verify educational email for academic discount.
    """
    try:
        edu_email = request.data.get('edu_email')
        if not edu_email:
            return Response(
                {'error': 'Educational email is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        discount, message = AcademicDiscountService.verify_edu_email(request.user, edu_email)

        return Response({
            'success': True,
            'message': message,
            'discount': {
                'id': str(discount.id),
                'status': discount.status,
                'discount_rate': float(discount.discount_rate),
                'verification_method': discount.verification_method,
                'expires_at': discount.expires_at.isoformat() if discount.expires_at else None
            }
        })

    except Exception as e:
        logger.error(f"Academic email verification error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def upload_academic_document(request):
    """
    POST /api/enhanced-billing/academic/upload-document/
    Upload verification document for academic discount.
    """
    try:
        document = request.FILES.get('document')
        document_type = request.data.get('document_type')
        institution_name = request.data.get('institution_name')

        if not all([document, document_type, institution_name]):
            return Response(
                {'error': 'Document, document type, and institution name are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        discount, message = AcademicDiscountService.upload_verification_document(
            request.user, document, document_type, institution_name
        )

        return Response({
            'success': True,
            'message': message,
            'discount': {
                'id': str(discount.id),
                'status': discount.status,
                'document_type': discount.document_type,
                'institution_name': discount.institution_name
            }
        })

    except Exception as e:
        logger.error(f"Document upload error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_academic_discount_status(request):
    """
    GET /api/enhanced-billing/academic/status/
    Get current academic discount status.
    """
    try:
        discount = AcademicDiscount.objects.get(user=request.user)

        return Response({
            'has_discount': True,
            'discount': {
                'id': str(discount.id),
                'status': discount.status,
                'discount_rate': float(discount.discount_rate),
                'verification_method': discount.verification_method,
                'institution_name': discount.institution_name,
                'expires_at': discount.expires_at.isoformat() if discount.expires_at else None,
                'days_until_expiry': discount.days_until_expiry,
                'is_valid': discount.is_valid
            }
        })

    except AcademicDiscount.DoesNotExist:
        return Response({
            'has_discount': False,
            'discount': None
        })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def validate_promo_code(request):
    """
    POST /api/enhanced-billing/promo/validate/
    Validate promotional code and calculate discount.
    """
    try:
        code = request.data.get('code')
        plan_id = request.data.get('plan_id')
        billing_cycle = request.data.get('billing_cycle', 'monthly')

        if not code:
            return Response(
                {'error': 'Promotional code is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get plan version if plan_id provided
        original_amount = None
        if plan_id:
            try:
                plan_version = SubscriptionPlanVersion.get_active_plan(plan_id)
                if plan_version:
                    original_amount = (
                        plan_version.price_annual if billing_cycle == 'annual'
                        else plan_version.price_monthly
                    )
            except:
                pass

        promo_result, message = PromotionalCodeService.validate_and_apply_code(
            code, request.user, plan_id, original_amount
        )

        if promo_result:
            return Response({
                'valid': True,
                'message': message,
                'discount': {
                    'code': promo_result['code'].code,
                    'discount_type': promo_result['discount_type'],
                    'discount_value': float(promo_result['discount_value']),
                    'discount_amount': float(promo_result['discount_amount']),
                    'final_amount': float(promo_result['final_amount']) if promo_result['final_amount'] else None,
                    'extended_trial_days': promo_result['extended_trial_days'],
                    'bonus_credits': promo_result['bonus_credits'],
                    'can_stack_academic': promo_result['can_stack_academic']
                }
            })
        else:
            return Response({
                'valid': False,
                'message': message,
                'discount': None
            })

    except Exception as e:
        logger.error(f"Promo code validation error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def calculate_pricing_with_discounts(request):
    """
    POST /api/enhanced-billing/pricing/calculate/
    Calculate final pricing with all applicable discounts.
    """
    try:
        plan_id = request.data.get('plan_id')
        billing_cycle = request.data.get('billing_cycle', 'monthly')
        promo_code = request.data.get('promo_code')

        if not plan_id:
            return Response(
                {'error': 'Plan ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get plan version
        plan_version = SubscriptionPlanVersion.get_active_plan(plan_id)
        if not plan_version:
            return Response(
                {'error': 'Plan not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Calculate combined discounts
        pricing = PromotionalCodeService.calculate_combined_discount(
            request.user, plan_version, billing_cycle, promo_code
        )

        return Response({
            'plan': {
                'id': plan_version.plan_id,
                'name': plan_version.name,
                'version': plan_version.version
            },
            'billing_cycle': billing_cycle,
            'pricing': {
                'original_price': float(pricing['original_price']),
                'academic_discount': float(pricing['academic_discount']),
                'promo_discount': float(pricing['promo_discount']),
                'total_discount': float(pricing['total_discount']),
                'final_price': float(pricing['final_price']),
                'savings_amount': float(pricing['total_discount']),
                'savings_percentage': round((pricing['total_discount'] / pricing['original_price'] * 100), 1) if pricing['original_price'] > 0 else 0
            },
            'discounts_applied': {
                'has_academic': pricing['has_academic'],
                'has_promo': pricing['has_promo'],
                'promo_details': pricing['promo_details']
            }
        })

    except Exception as e:
        logger.error(f"Pricing calculation error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_enhanced_subscription(request):
    """
    POST /api/enhanced-billing/subscription/create-enhanced/
    Create subscription with academic discounts and promotional codes.
    """
    try:
        plan_id = request.data.get('plan_id')
        billing_cycle = request.data.get('billing_cycle', 'monthly')
        promo_code = request.data.get('promo_code')
        payment_method_ref = request.data.get('payment_method')
        payment_gateway = request.data.get('gateway')

        if not plan_id:
            return Response(
                {'error': 'Plan ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check for existing subscription
        existing = EnhancedSubscription.objects.filter(user=request.user).first()
        if existing and existing.status not in ['EXPIRED', 'CANCELED']:
            return Response(
                {'error': 'You already have an active subscription'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get plan version
        plan_version = SubscriptionPlanVersion.get_active_plan(plan_id)
        if not plan_version:
            return Response(
                {'error': 'Plan not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        with transaction.atomic():
            # Create enhanced trial subscription
            subscription = EnhancedTrialService.create_enhanced_trial(
                request.user, plan_version, billing_cycle, promo_code, payment_method_ref=payment_method_ref, payment_gateway=payment_gateway
            )

            # Calculate final pricing for response
            pricing = PromotionalCodeService.calculate_combined_discount(
                request.user, plan_version, billing_cycle, promo_code
            )

            return Response({
                'success': True,
                'message': 'Enhanced subscription created successfully!',
                'subscription': {
                    'id': str(subscription.id),
                    'status': subscription.status,
                    'plan_name': subscription.plan_version.name,
                    'billing_cycle': subscription.billing_cycle,
                    'trial_end': subscription.trial_end.isoformat() if subscription.trial_end else None,
                    'current_period_end': subscription.current_period_end.isoformat()
                },
                'pricing': pricing
            }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Enhanced subscription creation error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def update_trial_payment_method(request):
    """
    POST /api/enhanced-billing/subscription/payment-method/
    Store payment method for an active trial and auto-convert to paid immediately.
    Body: { "payment_method": "pm_...", "gateway": "stripe"|"paystack" }
    """
    from .billing_services import SubscriptionLifecycleManager

    payment_method_ref = (request.data.get('payment_method') or '').strip()
    payment_gateway = (request.data.get('gateway') or 'stripe').strip().lower()
    if not payment_method_ref:
        return Response({'error': 'payment_method is required'}, status=status.HTTP_400_BAD_REQUEST)
    if payment_gateway not in ['stripe', 'paystack']:
        return Response({'error': 'gateway must be stripe or paystack'}, status=status.HTTP_400_BAD_REQUEST)

    subscription = EnhancedSubscription.objects.filter(user=request.user).first()
    if not subscription or subscription.status != 'TRIAL':
        return Response({'error': 'No active trial subscription found'}, status=status.HTTP_404_NOT_FOUND)
    if not subscription.trial_end or timezone.now() > subscription.trial_end:
        return Response({'error': 'Trial has already ended'}, status=status.HTTP_400_BAD_REQUEST)

    # Save payment method and auto-convert
    with transaction.atomic():
        subscription.payment_method_ref = payment_method_ref
        subscription.payment_gateway = payment_gateway
        subscription.payment_method_added_at = timezone.now()
        subscription.save(update_fields=['payment_method_ref', 'payment_gateway', 'payment_method_added_at', 'updated_at'])

        SubscriptionLifecycleManager.convert_trial_to_active(subscription)

    return Response({
        'success': True,
        'message': 'Payment method saved. Trial converted to active subscription.',
        'subscription': {
            'id': str(subscription.id),
            'status': subscription.status,
            'current_period_end': subscription.current_period_end.isoformat() if subscription.current_period_end else None,
        }
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def cancel_enhanced_subscription(request):
    """
    POST /api/enhanced-billing/subscription/cancel/
    Cancel an enhanced subscription.
    Body: { "type": "end_of_period" | "immediate" } (default end_of_period)
    """
    cancel_type = (request.data.get('type') or request.data.get('cancellation_type') or 'end_of_period').strip().lower()
    if cancel_type not in ['end_of_period', 'immediate']:
        return Response({'error': 'type must be end_of_period or immediate'}, status=status.HTTP_400_BAD_REQUEST)

    subscription = EnhancedSubscription.objects.filter(user=request.user).first()
    if not subscription or subscription.status not in ['ACTIVE', 'TRIAL', 'PAST_DUE']:
        return Response({'error': 'No cancellable subscription found'}, status=status.HTTP_404_NOT_FOUND)

    with transaction.atomic():
        if cancel_type == 'immediate':
            subscription.cancellation_type = 'immediate'
            subscription.cancel_at_period_end = False
            subscription.current_period_end = timezone.now()
            subscription.transition_to('CANCELED', 'User canceled immediately')
        else:
            # End-of-period cancellation should preserve access until current_period_end.
            # Keep status ACTIVE and prevent renewal by setting cancel_at_period_end.
            subscription.cancellation_type = 'end_of_period'
            subscription.cancel_at_period_end = True
            subscription.canceled_at = timezone.now()
            subscription.save(update_fields=['cancellation_type', 'cancel_at_period_end', 'canceled_at', 'updated_at'])

    return Response({
        'success': True,
        'message': 'Subscription canceled',
        'cancellation': {
            'type': subscription.cancellation_type,
            'cancel_at_period_end': subscription.cancel_at_period_end,
            'access_until': subscription.current_period_end.isoformat() if subscription.current_period_end else None,
            'status': subscription.status,
        }
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def reactivate_enhanced_subscription(request):
    """
    POST /api/enhanced-billing/subscription/reactivate/
    Reactivate a suspended subscription by paying outstanding balance (within 30 days).
    Body: { "payment_method": "pm_...", "gateway": "stripe"|"paystack" }
    """
    from .billing_services import ReactivationManager

    payment_method_ref = (request.data.get('payment_method') or '').strip()
    payment_gateway = (request.data.get('gateway') or 'stripe').strip().lower()

    subscription = EnhancedSubscription.objects.filter(user=request.user).first()
    if not subscription or subscription.status != 'SUSPENDED':
        return Response({'error': 'No suspended subscription found'}, status=status.HTTP_404_NOT_FOUND)

    try:
        result = ReactivationManager.reactivate(subscription, payment_method_ref=payment_method_ref or None, payment_gateway=payment_gateway)
        inv = result['invoice']
        sub = result['subscription']
        return Response({
            'success': True,
            'message': 'Subscription reactivated',
            'subscription': {
                'id': str(sub.id),
                'status': sub.status,
                'current_period_end': sub.current_period_end.isoformat() if sub.current_period_end else None,
                'reactivation_window_end': sub.reactivation_window_end.isoformat() if sub.reactivation_window_end else None,
            },
            'invoice': {
                'id': str(inv.id),
                'invoice_number': inv.invoice_number,
                'total_amount': float(inv.total_amount),
                'currency': inv.currency,
                'status': inv.status,
            }
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def schedule_enhanced_downgrade(request):
    """
    POST /api/enhanced-billing/subscription/downgrade/
    Schedule a downgrade effective at current_period_end (no refunds).
    Body: { "plan_id": "<stable plan_id>" }
    """
    plan_id = (request.data.get('plan_id') or '').strip()
    if not plan_id:
        return Response({'error': 'plan_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    subscription = EnhancedSubscription.objects.filter(user=request.user).first()
    if not subscription or subscription.status not in ['ACTIVE', 'PAST_DUE', 'TRIAL']:
        return Response({'error': 'No subscription found'}, status=status.HTTP_404_NOT_FOUND)

    new_plan_version = SubscriptionPlanVersion.get_active_plan(plan_id)
    if not new_plan_version:
        return Response({'error': 'Plan not found'}, status=status.HTTP_404_NOT_FOUND)

    if subscription.plan_version_id == new_plan_version.id:
        return Response({'error': 'Already on that plan'}, status=status.HTTP_400_BAD_REQUEST)

    subscription.pending_downgrade_plan_version = new_plan_version
    subscription.pending_downgrade_effective_at = subscription.current_period_end
    subscription.save(update_fields=['pending_downgrade_plan_version', 'pending_downgrade_effective_at', 'updated_at'])

    try:
        from .email_service import SubscriptionEmailService
        SubscriptionEmailService.send_downgrade_scheduled_email(
            user=request.user,
            current_plan_name=subscription.plan_version.name,
            new_plan_name=new_plan_version.name,
            effective_date=subscription.current_period_end or timezone.now(),
        )
    except Exception:
        pass

    return Response({
        'success': True,
        'message': 'Downgrade scheduled',
        'effective_date': subscription.current_period_end.isoformat() if subscription.current_period_end else None,
        'pending_plan': {'plan_id': new_plan_version.plan_id, 'name': new_plan_version.name, 'version': new_plan_version.version},
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def cancel_enhanced_scheduled_downgrade(request):
    """
    POST /api/enhanced-billing/subscription/downgrade/cancel/
    Cancel a scheduled downgrade.
    """
    subscription = EnhancedSubscription.objects.filter(user=request.user).first()
    if not subscription:
        return Response({'error': 'No subscription found'}, status=status.HTTP_404_NOT_FOUND)

    subscription.pending_downgrade_plan_version = None
    subscription.pending_downgrade_effective_at = None
    subscription.save(update_fields=['pending_downgrade_plan_version', 'pending_downgrade_effective_at', 'updated_at'])

    return Response({'success': True, 'message': 'Scheduled downgrade canceled'}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_available_plans_with_pricing(request):
    """
    GET /api/enhanced-billing/plans/with-pricing/
    Get available plans with personalized pricing (academic discounts applied).
    """
    try:
        plans = SubscriptionPlanVersion.objects.filter(status='active').order_by('price_monthly')

        plans_data = []
        for plan in plans:
            # Calculate pricing for both billing cycles
            monthly_pricing = PromotionalCodeService.calculate_combined_discount(
                request.user, plan, 'monthly'
            )
            annual_pricing = PromotionalCodeService.calculate_combined_discount(
                request.user, plan, 'annual'
            )

            # Get trial configuration
            trial_config = EnhancedTrialService.get_trial_configuration(plan)

            plans_data.append({
                'id': plan.plan_id,
                'name': plan.name,
                'version': plan.version,
                'billing_cycles': plan.billing_cycles,
                'tier_access': plan.tier_access,
                'track_access': plan.track_access,
                'feature_flags': plan.feature_flags,
                'mentorship_credits': plan.mentorship_credits,
                'trial_config': {
                    'trial_days': trial_config.trial_days,
                    'requires_payment_method': trial_config.requires_payment_method
                },
                'pricing': {
                    'monthly': {
                        'original_price': float(monthly_pricing['original_price']),
                        'final_price': float(monthly_pricing['final_price']),
                        'total_discount': float(monthly_pricing['total_discount']),
                        'has_academic': monthly_pricing['has_academic'],
                        'savings_percentage': round((monthly_pricing['total_discount'] / monthly_pricing['original_price'] * 100), 1) if monthly_pricing['original_price'] > 0 else 0
                    },
                    'annual': {
                        'original_price': float(annual_pricing['original_price']),
                        'final_price': float(annual_pricing['final_price']),
                        'total_discount': float(annual_pricing['total_discount']),
                        'has_academic': annual_pricing['has_academic'],
                        'savings_percentage': round((annual_pricing['total_discount'] / annual_pricing['original_price'] * 100), 1) if annual_pricing['original_price'] > 0 else 0
                    }
                }
            })

        return Response({
            'plans': plans_data,
            'user_discounts': {
                'has_academic': AcademicDiscount.objects.filter(user=request.user, status='verified').exists()
            }
        })

    except Exception as e:
        logger.error(f"Plans with pricing error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Admin Views
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsProgramDirector])
def admin_academic_discounts(request):
    """
    GET /api/enhanced-billing/admin/academic-discounts/
    Get academic discounts for admin review.
    """
    try:
        status_filter = request.GET.get('status', 'pending')

        discounts = AcademicDiscount.objects.filter(
            status=status_filter
        ).select_related('user').order_by('-created_at')

        discounts_data = []
        for discount in discounts:
            discounts_data.append({
                'id': str(discount.id),
                'user': {
                    'id': str(discount.user.id),
                    'email': discount.user.email,
                    'name': f"{discount.user.first_name} {discount.user.last_name}".strip()
                },
                'verification_method': discount.verification_method,
                'status': discount.status,
                'institution_name': discount.institution_name,
                'student_email': discount.student_email,
                'document_type': discount.document_type,
                'discount_rate': float(discount.discount_rate),
                'created_at': discount.created_at.isoformat(),
                'verified_at': discount.verified_at.isoformat() if discount.verified_at else None,
                'expires_at': discount.expires_at.isoformat() if discount.expires_at else None
            })

        return Response({
            'discounts': discounts_data,
            'total_count': len(discounts_data)
        })

    except Exception as e:
        logger.error(f"Admin academic discounts error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsProgramDirector])
def admin_review_academic_discount(request, discount_id):
    """
    POST /api/enhanced-billing/admin/academic-discounts/{id}/review/
    Admin review of academic discount application.
    """
    try:
        approved = request.data.get('approved', False)
        notes = request.data.get('notes', '')

        discount, message = AcademicDiscountService.admin_review_discount(
            discount_id, approved, request.user, notes
        )

        return Response({
            'success': True,
            'message': message,
            'discount': {
                'id': str(discount.id),
                'status': discount.status,
                'reviewed_by': discount.reviewed_by.email if discount.reviewed_by else None,
                'review_notes': discount.review_notes
            }
        })

    except Exception as e:
        logger.error(f"Admin review error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated, IsProgramDirector])
def admin_promotional_codes(request):
    """
    GET/POST /api/enhanced-billing/admin/promo-codes/
    Manage promotional codes.
    """
    if request.method == 'GET':
        try:
            codes = PromotionalCodeService.get_active_codes_for_admin()

            codes_data = []
            for code in codes:
                codes_data.append({
                    'id': str(code.id),
                    'code': code.code,
                    'name': code.name,
                    'discount_type': code.discount_type,
                    'discount_value': float(code.discount_value),
                    'status': code.status,
                    'valid_from': code.valid_from.isoformat(),
                    'valid_until': code.valid_until.isoformat(),
                    'current_redemptions': code.current_redemptions,
                    'max_redemptions': code.max_redemptions,
                    'usage_percentage': code.usage_percentage,
                    'created_at': code.created_at.isoformat()
                })

            return Response({
                'codes': codes_data,
                'total_count': len(codes_data)
            })

        except Exception as e:
            logger.error(f"Admin promo codes list error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    elif request.method == 'POST':
        try:
            with transaction.atomic():
                code = PromotionalCode.objects.create(
                    code=request.data.get('code'),
                    name=request.data.get('name'),
                    description=request.data.get('description', ''),
                    discount_type=request.data.get('discount_type'),
                    discount_value=Decimal(str(request.data.get('discount_value', 0))),
                    valid_from=timezone.now(),
                    valid_until=request.data.get('valid_until'),
                    max_redemptions=request.data.get('max_redemptions', 1000),
                    max_redemptions_per_user=request.data.get('max_redemptions_per_user', 1),
                    eligible_plans=request.data.get('eligible_plans', []),
                    new_customers_only=request.data.get('new_customers_only', False),
                    stackable_with_academic=request.data.get('stackable_with_academic', False),
                    extended_trial_days=request.data.get('extended_trial_days', 0),
                    bonus_credits=request.data.get('bonus_credits', 0),
                    created_by=request.user
                )

                return Response({
                    'success': True,
                    'message': 'Promotional code created successfully',
                    'code': {
                        'id': str(code.id),
                        'code': code.code,
                        'name': code.name,
                        'status': code.status
                    }
                }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Admin promo code creation error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsProgramDirector])
def admin_promo_code_analytics(request, code_id):
    """
    GET /api/enhanced-billing/admin/promo-codes/{id}/analytics/
    Get promotional code analytics.
    """
    try:
        analytics = PromotionalCodeService.get_code_analytics(code_id)

        return Response({
            'code': {
                'id': str(analytics['code'].id),
                'code': analytics['code'].code,
                'name': analytics['code'].name,
                'discount_type': analytics['code'].discount_type,
                'discount_value': float(analytics['code'].discount_value)
            },
            'analytics': {
                'total_redemptions': analytics['total_redemptions'],
                'redemptions_remaining': analytics['redemptions_remaining'],
                'usage_percentage': analytics['usage_percentage'],
                'total_discount_given': float(analytics['total_discount_given']),
                'average_discount': float(analytics['average_discount']),
                'revenue_impact': {
                    'total_original': float(analytics['revenue_impact']['total_original']),
                    'total_discount': float(analytics['revenue_impact']['total_discount']),
                    'discount_rate': float(analytics['revenue_impact']['discount_rate']),
                    'net_revenue': float(analytics['revenue_impact']['net_revenue']),
                    'redemption_count': analytics['revenue_impact']['redemption_count'],
                },
                'conversion': {
                    'converted_count': analytics['conversion']['converted_count'],
                    'conversion_rate': float(analytics['conversion']['conversion_rate']),
                    'conversions_by_plan': analytics['conversion']['conversions_by_plan'],
                },
                'plan_breakdown': [
                    {
                        'plan_id': row['plan_id'],
                        'plan_name': row['plan_name'],
                        'redemptions': row['redemptions'],
                        'total_discount': float(row['total_discount']),
                    }
                    for row in analytics.get('plan_breakdown', [])
                ],
                'redemption_timeline': analytics['redemption_timeline']
            }
        })

    except Exception as e:
        logger.error(f"Promo code analytics error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
