"""Reconciliation, revenue recognition, cohort-manager finance APIs."""
from datetime import datetime
from decimal import Decimal

from django.shortcuts import get_object_or_404
from programs.models import Cohort
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsStaffOrFinance

from .cohort_finance import get_cohort_financial_summary, user_can_view_cohort_finance
from .models import ReconciliationRun
from .reconciliation_service import compute_book_total_for_period, run_reconciliation
from .revenue_recognition import recognize_revenue_for_period


class ReconciliationPreviewView(APIView):
    """GET book total for a period (finance RBAC or Django staff)."""
    permission_classes = [IsStaffOrFinance]

    def get(self, request):
        start = request.query_params.get('period_start')
        end = request.query_params.get('period_end')
        currency = request.query_params.get('currency', 'USD')
        if not start or not end:
            return Response(
                {'error': 'period_start and period_end (YYYY-MM-DD) required'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        p0 = datetime.strptime(start, '%Y-%m-%d').date()
        p1 = datetime.strptime(end, '%Y-%m-%d').date()
        book_total, payment_count = compute_book_total_for_period(p0, p1, currency=currency)
        return Response({
            'period_start': start,
            'period_end': end,
            'currency': currency,
            'book_total': str(book_total),
            'payment_records_count': payment_count,
        })


class ReconciliationRunCreateView(APIView):
    """POST: compare book total to supplied bank total and persist run."""
    permission_classes = [IsStaffOrFinance]

    def post(self, request):
        start = request.data.get('period_start')
        end = request.data.get('period_end')
        bank_raw = request.data.get('bank_total')
        currency = request.data.get('currency', 'USD')
        notes = request.data.get('notes', '')
        if not start or not end or bank_raw is None:
            return Response(
                {'error': 'period_start, period_end, bank_total required'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        p0 = datetime.strptime(start, '%Y-%m-%d').date()
        p1 = datetime.strptime(end, '%Y-%m-%d').date()
        bank_total = Decimal(str(bank_raw))
        run = run_reconciliation(
            period_start=p0,
            period_end=p1,
            bank_total=bank_total,
            currency=currency,
            user=request.user,
            notes=notes,
        )
        return Response({
            'id': str(run.id),
            'book_total': str(run.book_total),
            'bank_total': str(run.bank_total),
            'difference': str(run.difference),
            'currency': run.currency,
            'payment_count': run.payment_count,
            'created_at': run.created_at.isoformat(),
        }, status=status.HTTP_201_CREATED)


class ReconciliationRunListView(APIView):
    permission_classes = [IsStaffOrFinance]

    def get(self, request):
        qs = ReconciliationRun.objects.all()[:50]
        data = [
            {
                'id': str(r.id),
                'period_start': r.period_start.isoformat(),
                'period_end': r.period_end.isoformat(),
                'book_total': str(r.book_total),
                'bank_total': str(r.bank_total),
                'difference': str(r.difference),
                'currency': r.currency,
                'payment_count': r.payment_count,
                'created_at': r.created_at.isoformat(),
            }
            for r in qs
        ]
        return Response({'results': data})


class RevenueRecognitionRunView(APIView):
    permission_classes = [IsStaffOrFinance]

    def post(self, request):
        start = request.data.get('period_start')
        end = request.data.get('period_end')
        currency = request.data.get('currency', 'USD')
        if not start or not end:
            return Response(
                {'error': 'period_start and period_end required'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        p0 = datetime.strptime(start, '%Y-%m-%d').date()
        p1 = datetime.strptime(end, '%Y-%m-%d').date()
        result = recognize_revenue_for_period(p0, p1, currency=currency)
        return Response(result, status=status.HTTP_200_OK)


class CohortManagerFinanceView(APIView):
    """Financial summary for a cohort (coordinator / track director / staff)."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        cohort_id = request.query_params.get('cohort_id')
        if not cohort_id:
            return Response({'error': 'cohort_id required'}, status=status.HTTP_400_BAD_REQUEST)
        cohort = get_object_or_404(Cohort.objects.select_related('track'), pk=cohort_id)
        if not user_can_view_cohort_finance(request.user, cohort):
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        return Response(get_cohort_financial_summary(cohort.id))
