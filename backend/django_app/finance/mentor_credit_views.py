"""
Finance-facing mentor credit wallet endpoints.

These endpoints are intended for finance/admin users to view mentor credit balances
and transaction history (credits are earned via mentee ratings).
"""

from mentors.models import CreditTransaction, Mentor, MentorCredit
from programs.permissions import IsFinanceUser
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView


class MentorCreditWalletsView(APIView):
    """
    GET /api/v1/finance/mentor-credit-wallets/
    List mentor credit wallet balances for finance/admin.
    """

    permission_classes = [permissions.IsAuthenticated, IsFinanceUser]

    def get(self, request):
        mentors = (
            Mentor.objects.select_related("user")
            .prefetch_related("credit_balance")
            .all()
            .order_by("user__first_name", "user__last_name", "mentor_slug")
        )

        out = []
        for m in mentors:
            try:
                bal: MentorCredit = m.credit_balance
                current_balance = bal.current_balance
                total_earned = bal.total_earned
                total_redeemed = bal.total_redeemed
                last_earned_at = bal.last_earned_at
                last_redeemed_at = bal.last_redeemed_at
            except MentorCredit.DoesNotExist:
                current_balance = 0
                total_earned = 0
                total_redeemed = 0
                last_earned_at = None
                last_redeemed_at = None

            out.append(
                {
                    "mentor_id": str(m.id),
                    "mentor_slug": m.mentor_slug,
                    "mentor_name": m.user.get_full_name() or m.user.email,
                    "mentor_email": m.user.email,
                    "average_rating": float(m.average_rating) if m.average_rating is not None else None,
                    "credits": {
                        "current_balance": current_balance,
                        "total_earned": total_earned,
                        "total_redeemed": total_redeemed,
                        "last_earned_at": last_earned_at,
                        "last_redeemed_at": last_redeemed_at,
                    },
                }
            )

        return Response(out, status=status.HTTP_200_OK)


class MentorCreditWalletTransactionsView(APIView):
    """
    GET /api/v1/finance/mentor-credit-wallets/<mentor_slug>/transactions/
    List recent credit transactions for a mentor.
    """

    permission_classes = [permissions.IsAuthenticated, IsFinanceUser]

    def get(self, request, mentor_slug: str):
        mentor = Mentor.objects.select_related("user").filter(mentor_slug=mentor_slug).first()
        if not mentor:
            return Response({"detail": "Mentor not found"}, status=status.HTTP_404_NOT_FOUND)

        tx = (
            CreditTransaction.objects.filter(mentor=mentor)
            .order_by("-created_at")[:100]
        )

        out = [
            {
                "id": str(t.id),
                "type": t.transaction_type,
                "amount": t.amount,
                "description": t.description,
                "source": t.source,
                "balance_after": t.balance_after,
                "created_at": t.created_at,
            }
            for t in tx
        ]
        return Response(
            {
                "mentor_slug": mentor.mentor_slug,
                "mentor_email": mentor.user.email,
                "transactions": out,
            },
            status=status.HTTP_200_OK,
        )

