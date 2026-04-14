"""
Mentor Credit Service - Handles credit awards and redemptions for mentors.
"""
from django.db import transaction

from .models import CreditRedemption, CreditTransaction, MentorCredit


class MentorCreditService:
    """Service for managing mentor credits."""

    @staticmethod
    @transaction.atomic
    def award_credits_for_rating(rating, override_amount=None):
        """
        Award credits to mentor based on student rating.
        Credits: 5 stars = 10, 4 stars = 8, 3 stars = 6, 2 stars = 4, 1 star = 2
        """
        mentor = rating.mentor
        credits_to_award = override_amount if override_amount is not None else rating.credits_awarded

        if credits_to_award <= 0:
            return

        # Get or create credit balance
        credit_balance, created = MentorCredit.objects.get_or_create(
            mentor=mentor,
            defaults={
                'total_earned': 0,
                'total_redeemed': 0,
                'current_balance': 0
            }
        )

        # Update balance
        credit_balance.add_credits(credits_to_award, source='rating')

        # Create transaction record
        CreditTransaction.objects.create(
            mentor=mentor,
            transaction_type='earned',
            amount=credits_to_award,
            description=f"Rating from {rating.student}: {rating.rating} stars",
            source='rating',
            related_rating=rating,
            balance_after=credit_balance.current_balance
        )

        return credit_balance

    @staticmethod
    @transaction.atomic
    def redeem_credits(mentor, redemption_type, description=None, **kwargs):
        """
        Redeem credits for a reward (course, certificate, badge, priority matching).
        Returns the CreditRedemption object or raises ValueError if insufficient credits.
        """
        # Get credit balance
        try:
            credit_balance = mentor.credit_balance
        except MentorCredit.DoesNotExist:
            raise ValueError("No credit balance found for this mentor")

        # Check cost
        cost = CreditRedemption.get_cost(redemption_type)
        if not credit_balance.has_sufficient_credits(cost):
            raise ValueError(f"Insufficient credits. Required: {cost}, Available: {credit_balance.current_balance}")

        # Deduct credits
        credit_balance.redeem_credits(cost)

        # Create redemption record
        redemption = CreditRedemption.objects.create(
            mentor=mentor,
            redemption_type=redemption_type,
            credits_used=cost,
            description=description or f"Redeemed for {redemption_type}",
            status='pending',
            **kwargs
        )

        # Create transaction record
        CreditTransaction.objects.create(
            mentor=mentor,
            transaction_type='redeemed',
            amount=-cost,
            description=f"Redeemed for {redemption_type}",
            balance_after=credit_balance.current_balance
        )

        return redemption

    @staticmethod
    def get_credit_summary(mentor):
        """Get comprehensive credit summary for a mentor."""
        try:
            credit_balance = mentor.credit_balance
            return {
                'current_balance': credit_balance.current_balance,
                'total_earned': credit_balance.total_earned,
                'total_redeemed': credit_balance.total_redeemed,
                'last_earned_at': credit_balance.last_earned_at,
                'last_redeemed_at': credit_balance.last_redeemed_at,
            }
        except MentorCredit.DoesNotExist:
            return {
                'current_balance': 0,
                'total_earned': 0,
                'total_redeemed': 0,
                'last_earned_at': None,
                'last_redeemed_at': None,
            }

    @staticmethod
    def get_transaction_history(mentor, limit=20):
        """Get recent credit transactions for a mentor."""
        transactions = mentor.credit_transactions.all()[:limit]
        return [
            {
                'id': str(t.id),
                'type': t.transaction_type,
                'amount': t.amount,
                'description': t.description,
                'source': t.source,
                'balance_after': t.balance_after,
                'created_at': t.created_at
            }
            for t in transactions
        ]

    @staticmethod
    def get_redemption_options():
        """Get available redemption options with costs."""
        return [
            {'type': 'course', 'name': 'Course Purchase', 'cost': 50},
            {'type': 'certificate', 'name': 'Certificate Generation', 'cost': 30},
            {'type': 'badge', 'name': 'Profile Badge', 'cost': 20},
            {'type': 'priority_matching', 'name': 'Priority Student Matching', 'cost': 40},
            {'type': 'featured_profile', 'name': 'Featured Profile', 'cost': 100},
        ]
