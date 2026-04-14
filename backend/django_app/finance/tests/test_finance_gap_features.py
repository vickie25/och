"""Smoke tests for reconciliation, revenue recognition, cohort finance helpers."""
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from finance.models import ReconciliationRun
from finance.reconciliation_service import compute_book_total_for_period, run_reconciliation
from finance.revenue_recognition import recognize_revenue_for_period

User = get_user_model()


class ReconciliationServiceTests(TestCase):
    def test_compute_book_empty_period(self):
        t0 = date.today() - timedelta(days=400)
        t1 = date.today() - timedelta(days=300)
        total, n = compute_book_total_for_period(t0, t1, currency='USD')
        self.assertEqual(total, Decimal('0'))
        self.assertEqual(n, 0)

    def test_reconciliation_run_persisted(self):
        u = User.objects.create_user(email='admin@test.dev', password='x', is_staff=True)
        p0 = date.today().replace(day=1)
        p1 = p0 + timedelta(days=27)
        run = run_reconciliation(
            period_start=p0,
            period_end=p1,
            bank_total=Decimal('0.00'),
            currency='USD',
            user=u,
            notes='test',
        )
        self.assertIsInstance(run, ReconciliationRun)
        self.assertEqual(ReconciliationRun.objects.filter(id=run.id).count(), 1)


class RevenueRecognitionTests(TestCase):
    def test_recognize_empty(self):
        p0 = date.today() - timedelta(days=30)
        p1 = date.today()
        r = recognize_revenue_for_period(p0, p1, currency='USD')
        self.assertEqual(r['created'], 0)
