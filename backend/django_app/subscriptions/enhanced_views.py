"""
Enhanced Billing API Views - Complete Implementation
Includes academic discounts, promotional codes, enhanced trial management, and grace periods
"""

import logging

from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from .enhanced_models import (
    AcademicDiscount,
    EnhancedSubscription,
    EnhancedSubscriptionPlan,
    PromoCodeRedemption,
    PromotionalCode,
)
from .enhanced_services import (
    AcademicDiscountService,
    EnhancedBillingService,
    EnhancedTrialService,
    PromotionalCodeService,
)

logger = logging.getLogger(__name__)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def academic_discount_view(request, user_id=None):
    """Handle academic discount requests"""

    if request.method == 'GET':
        # Check academic discount status
        user = request.user if not user_id else get_object_or_404(User, id=user_id)

        try:
            discount = user.academic_discount
            return Response({
                'eligible': True,
                'verified': discount.is_valid(),
                'status': discount.status,
                'discount_rate': float(discount.discount_rate),
                'verification_method': discount.verification_method,
                'expires_at': discount.expires_at,
                'institution_name': discount.institution_name
            })
        except AcademicDiscount.DoesNotExist:
            # Check if user has academic email
            is_academic_email = AcademicDiscountService.is_academic_email(user.email)
            return Response({
                'eligible': is_academic_email,
                'verified': False,
                'auto_eligible': is_academic_email,
                'message': 'Academic discount available for .edu emails' if is_academic_email else 'Not eligible for academic discount'
            })

    elif request.method == 'POST':
        # Apply for academic discount
        user = request.user
        verification_method = request.data.get('verification_method', 'edu_email')
        institution_name = request.data.get('institution_name', '')
        student_id = request.data.get('student_id', '')

        try:
            discount = AcademicDiscountService.create_academic_discount(
                user=user,
                verification_method=verification_method,
                institution_name=institution_name,
                student_id=student_id
            )

            return Response({
                'success': True,
                'discount_id': str(discount.id),
                'status': discount.status,
                'message': 'Academic discount created successfully',
                'auto_verified': discount.status == 'verified'
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAdminUser])
def verify_academic_discount(request, discount_id):
    """Admin endpoint to verify academic discounts"""

    approved = request.data.get('approved', True)
    rejection_reason = request.data.get('rejection_reason', '')

    try:
        discount = AcademicDiscountService.verify_academic_discount(
            discount_id=discount_id,
            verified_by_user=request.user,
            approved=approved,
            rejection_reason=rejection_reason
        )

        return Response({
            'success': True,
            'discount_id': str(discount.id),
            'status': discount.status,
            'message': f'Academic discount {"approved" if approved else "rejected"}'
        })

    except ValidationError as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_promo_code(request):
    """Validate promotional code"""

    code = request.data.get('code', '').strip().upper()
    plan_id = request.data.get('plan_id')

    if not code:
        return Response({
            'valid': False,
            'error': 'Promotional code is required'
        }, status=status.HTTP_400_BAD_REQUEST)

    result = PromotionalCodeService.validate_promo_code(
        code=code,
        user=request.user,
        plan_id=plan_id
    )

    return Response(result)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def subscription_status(request, user_id=None):
    """Get comprehensive subscription status"""

    user = request.user if not user_id else get_object_or_404(User, id=user_id)

    try:
        subscription = user.enhanced_subscriptions.filter(
            status__in=['trial', 'active', 'past_due', 'suspended']
        ).first()

        if not subscription:
            return Response({
                'has_subscription': False,
                'message': 'No active subscription found'
            })

        # Get trial information
        trial_info = {}
        if subscription.is_in_trial():
            trial_info = {
                'is_trial': True,
                'trial_start': subscription.trial_start,
                'trial_end': subscription.trial_end,
                'days_remaining': subscription.days_until_trial_end(),
                'requires_credit_card': subscription.plan.requires_credit_card
            }

        # Get grace period information
        grace_info = {}
        if subscription.is_in_grace_period():
            grace_info = {
                'in_grace_period': True,
                'grace_period_start': subscription.grace_period_start,
                'grace_period_end': subscription.grace_period_end,
                'days_remaining': subscription.days_until_grace_period_end()
            }

        # Get discount information
        discount_info = {
            'academic_discount_applied': subscription.academic_discount_applied,
            'promo_code_applied': subscription.promo_code_applied.code if subscription.promo_code_applied else None,
            'base_amount': float(subscription.base_amount),
            'discount_amount': float(subscription.discount_amount),
            'final_amount': float(subscription.final_amount)
        }

        return Response({
            'has_subscription': True,
            'subscription': {
                'id': str(subscription.id),
                'plan': {
                    'id': str(subscription.plan.id),
                    'name': subscription.plan.name,
                    'plan_type': subscription.plan.plan_type,
                    'price': float(subscription.plan.price),
                    'billing_cycle': subscription.plan.billing_cycle,
                    'features': subscription.plan.features
                },
                'status': subscription.status,
                'dunning_status': subscription.dunning_status,
                'current_period_start': subscription.current_period_start,
                'current_period_end': subscription.current_period_end,
                'next_billing_date': subscription.next_billing_date,
                'amount_due': float(subscription.amount_due),
                **trial_info,
                **grace_info,
                **discount_info
            }
        })

    except Exception as e:
        logger.error(f"Error getting subscription status for user {user.id}: {str(e)}")
        return Response({
            'error': 'Failed to get subscription status'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def available_plans(request):
    """Get available subscription plans with pricing"""

    plans = EnhancedSubscriptionPlan.objects.filter(is_active=True).order_by('sort_order', 'price')
    user = request.user

    plans_data = []
    for plan in plans:
        # Calculate pricing with user's discounts
        pricing = plan.calculate_price_with_discounts(user=user)

        # Get trial configuration
        trial_config = plan.get_trial_config()

        plans_data.append({
            'id': str(plan.id),
            'name': plan.name,
            'plan_type': plan.plan_type,
            'description': plan.description,
            'original_price': float(plan.price),
            'final_price': float(pricing['final_price']),
            'total_savings': float(pricing['total_savings']),
            'discounts_applied': pricing['discounts_applied'],
            'currency': plan.currency,
            'billing_cycle': plan.billing_cycle,
            'features': plan.features,
            'trial_days': trial_config['days'],
            'requires_credit_card': trial_config['requires_card'],
            'grace_period_days': plan.get_grace_period_days(),
            'is_featured': plan.is_featured
        })

    return Response(plans_data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def create_subscription(request):
    """Create new subscription"""

    plan_id = request.data.get('plan_id')
    promo_code = request.data.get('promo_code')
    start_trial = request.data.get('start_trial', True)
    payment_method = request.data.get('payment_method')

    if not plan_id:
        return Response({
            'error': 'Plan ID is required'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        subscription = EnhancedBillingService.create_subscription(
            user=request.user,
            plan_id=plan_id,
            payment_method=payment_method,
            promo_code=promo_code,
            start_trial=start_trial
        )

        return Response({
            'success': True,
            'subscription_id': str(subscription.id),
            'status': subscription.status,
            'message': 'Subscription created successfully'
        }, status=status.HTTP_201_CREATED)

    except ValidationError as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error creating subscription: {str(e)}")
        return Response({
            'error': 'Failed to create subscription'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def change_plan(request):
    """Change subscription plan"""

    user_id = request.data.get('user_id', request.user.id)
    new_plan_id = request.data.get('new_plan_id')
    promo_code = request.data.get('promo_code')
    prorate = request.data.get('prorate', True)

    if not new_plan_id:
        return Response({
            'error': 'New plan ID is required'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Get user's active subscription
        user = request.user if user_id == request.user.id else get_object_or_404(User, id=user_id)
        subscription = user.enhanced_subscriptions.filter(
            status__in=['trial', 'active']
        ).first()

        if not subscription:
            return Response({
                'error': 'No active subscription found'
            }, status=status.HTTP_404_NOT_FOUND)

        updated_subscription = EnhancedBillingService.change_plan(
            subscription=subscription,
            new_plan_id=new_plan_id,
            promo_code=promo_code,
            prorate=prorate
        )

        return Response({
            'success': True,
            'subscription_id': str(updated_subscription.id),
            'new_plan': updated_subscription.plan.name,
            'final_amount': float(updated_subscription.final_amount),
            'message': 'Plan changed successfully'
        })

    except ValidationError as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error changing plan: {str(e)}")
        return Response({
            'error': 'Failed to change plan'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def convert_trial(request):
    """Convert trial to paid subscription"""

    subscription_id = request.data.get('subscription_id')
    promo_code = request.data.get('promo_code')
    payment_method = request.data.get('payment_method')

    if not subscription_id:
        return Response({
            'error': 'Subscription ID is required'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        subscription = get_object_or_404(
            EnhancedSubscription,
            id=subscription_id,
            user=request.user,
            status='trial'
        )

        # Validate promo code if provided
        validated_promo = None
        if promo_code:
            validation_result = PromotionalCodeService.validate_promo_code(
                promo_code, request.user, subscription.plan.id
            )
            if not validation_result['valid']:
                return Response({
                    'error': validation_result['error']
                }, status=status.HTTP_400_BAD_REQUEST)
            validated_promo = PromotionalCode.objects.get(code=promo_code.upper())

        converted_subscription = EnhancedTrialService.convert_trial(
            subscription=subscription,
            payment_method=payment_method,
            promo_code=validated_promo
        )

        return Response({
            'success': True,
            'subscription_id': str(converted_subscription.id),
            'status': converted_subscription.status,
            'final_amount': float(converted_subscription.final_amount),
            'next_billing_date': converted_subscription.next_billing_date,
            'message': 'Trial converted successfully'
        })

    except ValidationError as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error converting trial: {str(e)}")
        return Response({
            'error': 'Failed to convert trial'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def billing_history(request, user_id=None):
    """Get billing history with discount details"""

    user = request.user if not user_id else get_object_or_404(User, id=user_id)

    # Get subscription history
    subscriptions = user.enhanced_subscriptions.all().order_by('-created_at')

    # Get promo code redemptions
    redemptions = user.promo_redemptions.all().order_by('-redeemed_at')

    history = []

    # Add subscription events
    for sub in subscriptions:
        history.append({
            'type': 'subscription',
            'date': sub.created_at,
            'description': f"Subscription created - {sub.plan.name}",
            'amount': float(sub.final_amount),
            'discount_amount': float(sub.discount_amount),
            'academic_discount': sub.academic_discount_applied,
            'promo_code': sub.promo_code_applied.code if sub.promo_code_applied else None,
            'status': sub.status
        })

        if sub.trial_converted_at:
            history.append({
                'type': 'trial_conversion',
                'date': sub.trial_converted_at,
                'description': f"Trial converted - {sub.plan.name}",
                'amount': float(sub.final_amount),
                'discount_amount': float(sub.discount_amount)
            })

    # Add promo code redemptions
    for redemption in redemptions:
        history.append({
            'type': 'promo_redemption',
            'date': redemption.redeemed_at,
            'description': f"Promo code applied - {redemption.promo_code.code}",
            'original_amount': float(redemption.original_amount),
            'discount_amount': float(redemption.discount_applied),
            'final_amount': float(redemption.final_amount)
        })

    # Sort by date
    history.sort(key=lambda x: x['date'], reverse=True)

    return Response({
        'billing_history': history,
        'total_items': len(history)
    })

@api_view(['GET'])
@permission_classes([IsAdminUser])
def billing_analytics(request):
    """Get comprehensive billing analytics"""

    user_id = request.query_params.get('user_id')
    analytics = EnhancedBillingService.get_subscription_analytics(user_id=user_id)

    # Add promotional code analytics
    promo_analytics = {
        'total_promo_codes': PromotionalCode.objects.count(),
        'active_promo_codes': PromotionalCode.objects.filter(status='active').count(),
        'total_redemptions': PromoCodeRedemption.objects.count(),
        'total_promo_savings': sum(
            r.discount_applied for r in PromoCodeRedemption.objects.all()
        )
    }

    # Add academic discount analytics
    academic_analytics = {
        'total_academic_discounts': AcademicDiscount.objects.count(),
        'verified_academic_discounts': AcademicDiscount.objects.filter(status='verified').count(),
        'pending_academic_discounts': AcademicDiscount.objects.filter(status='pending').count(),
        'total_academic_savings': sum(
            s.discount_amount for s in EnhancedSubscription.objects.filter(academic_discount_applied=True)
        )
    }

    return Response({
        'subscription_analytics': analytics,
        'promotional_analytics': promo_analytics,
        'academic_analytics': academic_analytics,
        'generated_at': timezone.now()
    })

# ViewSet for promotional codes management (Admin only)
class PromotionalCodeViewSet(viewsets.ModelViewSet):
    queryset = PromotionalCode.objects.all()
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = super().get_queryset()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset.order_by('-created_at')

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate promotional code"""
        promo_code = self.get_object()
        promo_code.status = 'inactive'
        promo_code.save()
        return Response({'message': 'Promotional code deactivated'})

    @action(detail=True, methods=['get'])
    def usage_stats(self, request, pk=None):
        """Get usage statistics for promotional code"""
        promo_code = self.get_object()
        redemptions = promo_code.redemptions.all()

        stats = {
            'total_redemptions': redemptions.count(),
            'total_savings': sum(r.discount_applied for r in redemptions),
            'unique_users': redemptions.values('user').distinct().count(),
            'recent_redemptions': redemptions.order_by('-redeemed_at')[:10].values(
                'user__email', 'discount_applied', 'redeemed_at'
            )
        }

        return Response(stats)
