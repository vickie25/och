import os

import pytest
from rest_framework import status

from subscriptions.models import PaymentTransaction, SubscriptionPlan, UserSubscription


@pytest.mark.django_db
class TestStudentUpgradePaystackFlow:
    def test_paystack_initialize_paid_plan_returns_authorization_url(self, student_client, monkeypatch):
        SubscriptionPlan.objects.create(
            name='starter_3',
            tier='starter',
            price_monthly=300,
            stream='student',
            billing_interval='monthly',
            is_listed=True,
        )

        os.environ['PAYSTACK_SECRET_KEY'] = 'test_secret'

        class _FakeResp:
            def json(self):
                return {
                    'status': True,
                    'message': 'Authorization URL created',
                    'data': {
                        'authorization_url': 'https://paystack.test/checkout/abc',
                        'reference': 'och_123_1_deadbeef',
                    },
                }

        def fake_post(_url, headers=None, json=None, timeout=None):
            assert 'Authorization' in (headers or {})
            assert (json or {}).get('amount', 0) > 0
            assert (json or {}).get('currency') in ('KES', 'NGN', 'GHS', 'ZAR')
            return _FakeResp()

        monkeypatch.setattr('subscriptions.views.requests.post', fake_post)

        res = student_client.post(
            '/api/v1/subscription/paystack/initialize',
            {'plan': 'starter_3', 'callback_url': 'https://example.test/return'},
            format='json',
        )
        assert res.status_code == status.HTTP_200_OK
        assert 'authorization_url' in res.data
        assert 'reference' in res.data

    def test_paystack_verify_success_activates_subscription_and_records_paystack_txn(
        self, student_user, student_client, monkeypatch
    ):
        plan = SubscriptionPlan.objects.create(
            name='starter_3',
            tier='starter',
            price_monthly=300,
            stream='student',
            billing_interval='monthly',
            is_listed=True,
        )
        os.environ['PAYSTACK_SECRET_KEY'] = 'test_secret'

        reference = 'och_123_{}_deadbeef'.format(student_user.id)

        class _FakeResp:
            def json(self):
                return {
                    'status': True,
                    'message': 'Verification successful',
                    'data': {
                        'status': 'success',
                        'reference': reference,
                        'amount': 30000,  # in "cents" (kobo-like)
                        'currency': 'KES',
                        'metadata': {'plan': 'starter_3'},
                        'authorization': {'authorization_code': 'AUTH_test_123'},
                    },
                }

        def fake_get(_url, headers=None, timeout=None):
            assert 'Authorization' in (headers or {})
            return _FakeResp()

        monkeypatch.setattr('subscriptions.views.requests.get', fake_get)

        res = student_client.post(
            '/api/v1/subscription/paystack/verify',
            {'reference': reference},
            format='json',
        )
        assert res.status_code == status.HTTP_200_OK
        assert res.data['success'] is True
        assert res.data['plan'] == plan.name

        sub = UserSubscription.objects.get(user=student_user)
        assert sub.status == 'active'
        assert sub.plan_id == plan.id
        # Payment method must be stored for Paystack off-session charges.
        assert sub.payment_gateway == 'paystack'
        assert sub.payment_method_ref == 'AUTH_test_123'

        txn = PaymentTransaction.objects.get(gateway_transaction_id=reference)
        assert txn.status == 'completed'
        assert float(txn.amount) == pytest.approx(300.0)
        assert txn.currency == 'KES'

