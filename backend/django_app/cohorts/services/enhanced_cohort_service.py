"""
Enhanced Cohort Service - Advanced cohort management with subscription integration.
"""
import logging
from decimal import Decimal

from django.db import transaction
from django.db.models import Count, Sum
from django.utils import timezone
from programs.cohort_finance import (
    assert_seat_available_for_enrollment,
    enrollment_window_status,
    get_effective_cohort_enrollment_fee,
)
from programs.models import Enrollment
from subscriptions.models import TIER_PREMIUM, TIER_STARTER, SubscriptionPlan, UserSubscription

from cohorts.models import CohortDayMaterial, CohortPayment

logger = logging.getLogger(__name__)


class EnhancedCohortService:
    """Enhanced service for cohort management with subscription integration."""

    @staticmethod
    def check_subscription_cohort_eligibility(user, cohort):
        """
        Check if user can enroll in cohort based on subscription status.

        Args:
            user: User instance
            cohort: Cohort instance

        Returns:
            dict: {eligible: bool, reason: str, discount: float}
        """
        try:
            # Check active user subscription (subscription engine)
            active_subscription = (
                UserSubscription.objects
                .select_related('plan')
                .filter(
                    user=user,
                    status='active',
                    current_period_end__gte=timezone.now()
                )
                .first()
            )

            if not active_subscription:
                return {
                    'eligible': True,
                    'reason': 'No active subscription - full payment required',
                    'discount': 0.0,
                    'subscription_benefit': None
                }

            # Subscription holders get benefits based on tier
            # Map our plan.tier values to benefit profiles
            subscription_benefits = {
                SubscriptionPlan.TIER_FREE if hasattr(SubscriptionPlan, 'TIER_FREE') else 'free': {
                    'label': 'free',
                    'discount': 0.0,
                    'priority_enrollment': False,
                },
                TIER_STARTER: {
                    'label': 'starter',
                    'discount': 0.10,
                    'priority_enrollment': False,
                },
                TIER_PREMIUM: {
                    'label': 'premium',
                    'discount': 0.20,
                    'priority_enrollment': True,
                },
            }

            plan_tier = getattr(active_subscription.plan, 'tier', None) or 'free'
            benefits = subscription_benefits.get(
                plan_tier,
                {'label': str(plan_tier), 'discount': 0.0, 'priority_enrollment': False},
            )

            return {
                'eligible': True,
                'reason': f'Active {benefits["label"]} subscription - {int(benefits["discount"]*100)}% discount',
                'discount': benefits['discount'],
                'subscription_benefit': {
                    'plan_type': benefits['label'],
                    'priority_enrollment': benefits['priority_enrollment'],
                    'subscription_id': str(active_subscription.id)
                }
            }

        except Exception as e:
            logger.error(f"Subscription eligibility check error: {str(e)}")
            return {
                'eligible': True,
                'reason': 'Error checking subscription - full payment required',
                'discount': 0.0,
                'subscription_benefit': None
            }

    @staticmethod
    def calculate_cohort_pricing(cohort, user=None, seat_type='paid'):
        """
        Calculate cohort pricing with discounts and seat type considerations.

        Args:
            cohort: Cohort instance
            user: Optional user for subscription discounts
            seat_type: 'paid', 'scholarship', 'sponsored'

        Returns:
            dict: Pricing breakdown
        """
        eff = get_effective_cohort_enrollment_fee(cohort)
        base_price = eff.list_price
        if base_price <= 0 and seat_type == "paid":
            # Paid seat requires a positive list price (cohort fee or program default)
            return {
                "base_price": Decimal("0.00"),
                "final_price": Decimal("0.00"),
                "discount_amount": Decimal("0.00"),
                "discount_reason": "No list price: set cohort.enrollment_fee or program.default_price",
                "seat_type": seat_type,
                "price_source": eff.source,
            }

        # Seat type adjustments
        if seat_type == 'scholarship':
            return {
                'base_price': base_price,
                'final_price': Decimal('0.00'),
                'discount_amount': base_price,
                'discount_reason': 'Scholarship seat',
                'seat_type': seat_type,
                'price_source': eff.source,
            }
        elif seat_type == 'sponsored':
            return {
                'base_price': base_price,
                'final_price': Decimal('0.00'),
                'discount_amount': base_price,
                'discount_reason': 'Sponsored seat',
                'seat_type': seat_type,
                'price_source': eff.source,
            }

        # Check subscription discounts for paid seats
        discount_amount = Decimal('0.00')
        discount_reason = 'No discount'

        if user:
            eligibility = EnhancedCohortService.check_subscription_cohort_eligibility(user, cohort)
            if eligibility['discount'] > 0:
                discount_amount = base_price * Decimal(str(eligibility['discount']))
                discount_reason = eligibility['reason']

        final_price = base_price - discount_amount

        return {
            'base_price': base_price,
            'final_price': final_price,
            'discount_amount': discount_amount,
            'discount_reason': discount_reason,
            'seat_type': seat_type,
            'price_source': eff.source,
        }

    @staticmethod
    def get_available_seats(cohort):
        """
        Get detailed seat availability for a cohort.

        Args:
            cohort: Cohort instance

        Returns:
            dict: Seat availability breakdown
        """
        total_enrolled = cohort.enrollments.filter(
            status__in=['active', 'pending_payment']
        ).count()

        # Get seat pool configuration
        seat_pool = cohort.seat_pool or {}
        paid_seats = seat_pool.get('paid', cohort.seat_cap)
        scholarship_seats = seat_pool.get('scholarship', 0)
        sponsored_seats = seat_pool.get('sponsored', 0)

        # Count by seat type
        enrolled_by_type = cohort.enrollments.filter(
            status__in=['active', 'pending_payment']
        ).values('seat_type').annotate(count=Count('id'))

        enrolled_counts = {item['seat_type']: item['count'] for item in enrolled_by_type}

        return {
            'total_capacity': cohort.seat_cap,
            'total_enrolled': total_enrolled,
            'available_seats': cohort.seat_cap - total_enrolled,
            'seat_breakdown': {
                'paid': {
                    'capacity': paid_seats,
                    'enrolled': enrolled_counts.get('paid', 0),
                    'available': paid_seats - enrolled_counts.get('paid', 0)
                },
                'scholarship': {
                    'capacity': scholarship_seats,
                    'enrolled': enrolled_counts.get('scholarship', 0),
                    'available': scholarship_seats - enrolled_counts.get('scholarship', 0)
                },
                'sponsored': {
                    'capacity': sponsored_seats,
                    'enrolled': enrolled_counts.get('sponsored', 0),
                    'available': sponsored_seats - enrolled_counts.get('sponsored', 0)
                }
            },
            'is_full': total_enrolled >= cohort.seat_cap,
            'waitlist_count': cohort.waitlist_entries.filter(active=True).count()
        }

    @staticmethod
    @transaction.atomic
    def enroll_user_in_cohort(user, cohort, seat_type='paid', enrollment_type='self', org=None):
        """
        Enroll user in cohort with comprehensive checks and payment setup.

        Args:
            user: User instance
            cohort: Cohort instance
            seat_type: 'paid', 'scholarship', 'sponsored'
            enrollment_type: 'self', 'invite', 'director'
            org: Optional organization for sponsored seats

        Returns:
            dict: Enrollment result with payment info
        """
        try:
            # Check if already enrolled
            existing_enrollment = Enrollment.objects.filter(
                user=user,
                cohort=cohort
            ).first()

            if existing_enrollment:
                return {
                    'success': False,
                    'error': 'User already enrolled in this cohort',
                    'enrollment_id': str(existing_enrollment.id)
                }

            open_ok, open_msg = enrollment_window_status(cohort)
            if not open_ok:
                return {"success": False, "error": open_msg}
            cap_ok, cap_msg = assert_seat_available_for_enrollment(cohort)
            if not cap_ok:
                return {"success": False, "error": cap_msg}

            # Check seat availability
            seat_availability = EnhancedCohortService.get_available_seats(cohort)
            seat_info = seat_availability['seat_breakdown'][seat_type]

            if seat_info['available'] <= 0:
                return {
                    'success': False,
                    'error': f'No {seat_type} seats available',
                    'available_seats': seat_availability
                }

            # Calculate pricing
            pricing = EnhancedCohortService.calculate_cohort_pricing(cohort, user, seat_type)
            if (
                seat_type == 'paid'
                and (pricing.get('final_price') or Decimal('0')) <= 0
            ):
                return {
                    'success': False,
                    'error': 'Paid enrollment requires a positive one-time fee: set cohort.enrollment_fee '
                    'or program.default_price.',
                    'pricing': pricing,
                }

            # Determine payment status
            payment_status = 'waived' if seat_type in ['scholarship', 'sponsored'] else 'pending'
            enrollment_status = 'active' if payment_status == 'waived' else 'pending_payment'

            # Create enrollment
            enrollment = Enrollment.objects.create(
                cohort=cohort,
                user=user,
                org=org,
                enrollment_type=enrollment_type,
                seat_type=seat_type,
                payment_status=payment_status,
                status=enrollment_status
            )

            # Create payment record if needed
            payment_info = None
            if payment_status == 'pending' and pricing['final_price'] > 0:
                payment = CohortPayment.objects.create(
                    enrollment=enrollment,
                    amount=pricing['final_price'],
                    currency='USD',
                    paystack_reference=f"cohort_{enrollment.id}_{timezone.now().timestamp()}"
                )
                payment_info = {
                    'payment_id': str(payment.id),
                    'amount': float(payment.amount),
                    'currency': payment.currency,
                    'payment_deadline': (timezone.now() + timezone.timedelta(days=7)).isoformat()
                }

            return {
                'success': True,
                'enrollment_id': str(enrollment.id),
                'enrollment_status': enrollment_status,
                'seat_type': seat_type,
                'pricing': pricing,
                'payment_info': payment_info,
                'message': 'Enrollment successful'
            }

        except Exception as e:
            logger.error(f"Cohort enrollment error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @staticmethod
    def get_cohort_analytics(cohort):
        """
        Get comprehensive analytics for a cohort.

        Args:
            cohort: Cohort instance

        Returns:
            dict: Analytics data
        """
        enrollments = cohort.enrollments.all()
        active_enrollments = enrollments.filter(status='active')

        # Basic metrics
        total_enrolled = enrollments.count()
        completion_rate = 0
        if total_enrolled > 0:
            completed = enrollments.filter(status='completed').count()
            completion_rate = (completed / total_enrolled) * 100

        # Revenue metrics
        payments = CohortPayment.objects.filter(
            enrollment__cohort=cohort,
            status='completed'
        )
        total_revenue = payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        # Progress metrics
        total_materials = CohortDayMaterial.objects.filter(cohort=cohort).count()

        # Engagement metrics
        avg_progress = 0
        if active_enrollments.exists():
            # This would need to be calculated based on material progress
            # Placeholder calculation
            avg_progress = 65.0  # Would calculate from actual progress data

        return {
            'enrollment_metrics': {
                'total_enrolled': total_enrolled,
                'active_students': active_enrollments.count(),
                'completion_rate': round(completion_rate, 2),
                'seat_utilization': round((total_enrolled / cohort.seat_cap) * 100, 2)
            },
            'revenue_metrics': {
                'total_revenue': float(total_revenue),
                'average_fee': float(total_revenue / total_enrolled) if total_enrolled > 0 else 0,
                'payment_completion_rate': round((payments.count() / total_enrolled) * 100, 2) if total_enrolled > 0 else 0
            },
            'content_metrics': {
                'total_materials': total_materials,
                'average_progress': avg_progress,
                'materials_per_day': round(total_materials / ((cohort.end_date - cohort.start_date).days + 1), 2)
            },
            'timeline_metrics': {
                'days_total': (cohort.end_date - cohort.start_date).days + 1,
                'days_elapsed': max(0, (timezone.now().date() - cohort.start_date).days),
                'days_remaining': max(0, (cohort.end_date - timezone.now().date()).days)
            }
        }

    @staticmethod
    def get_user_cohort_status(user):
        """
        Get user's current cohort enrollments and eligibility.

        Args:
            user: User instance

        Returns:
            dict: User cohort status
        """
        # Current enrollments
        current_enrollments = Enrollment.objects.filter(
            user=user,
            status__in=['active', 'pending_payment']
        ).select_related('cohort', 'cohort__track')

        # Completed cohorts
        completed_enrollments = Enrollment.objects.filter(
            user=user,
            status='completed'
        ).select_related('cohort', 'cohort__track')

        # Check subscription status
        subscription_status = EnhancedCohortService.check_subscription_cohort_eligibility(user, None)

        return {
            'current_cohorts': [
                {
                    'enrollment_id': str(e.id),
                    'cohort_id': str(e.cohort.id),
                    'cohort_name': e.cohort.name,
                    'track_name': e.cohort.track.name if e.cohort.track else None,
                    'status': e.status,
                    'seat_type': e.seat_type,
                    'start_date': e.cohort.start_date.isoformat(),
                    'end_date': e.cohort.end_date.isoformat()
                }
                for e in current_enrollments
            ],
            'completed_cohorts': [
                {
                    'cohort_name': e.cohort.name,
                    'track_name': e.cohort.track.name if e.cohort.track else None,
                    'completed_at': e.completed_at.isoformat() if e.completed_at else None
                }
                for e in completed_enrollments
            ],
            'subscription_benefits': subscription_status,
            'total_cohorts_completed': completed_enrollments.count(),
            'can_enroll_multiple': True  # Users can have both subscription and cohort
        }


# Singleton instance
enhanced_cohort_service = EnhancedCohortService()
