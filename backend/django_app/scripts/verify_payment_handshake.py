import os
import django
import sys
from decimal import Decimal

# Set up Django environment
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

from django.contrib.auth import get_user_model
from subscriptions.models import UserSubscription, SubscriptionPlan, PaymentTransaction
from subscriptions.views import _apply_paystack_payment
from django.utils import timezone

User = get_user_model()

def verify_payment_handshake():
    print("--- 💸 Payment Handshake Verification ---")
    
    # 1. Selection of Verification Subject
    user = User.objects.filter(is_active=True).first()
    if not user:
        print("❌ FAIL: No active user found for verification.")
        return

    print(f"Testing for user: {user.email}")

    # 2. Resolve a test plan (Starter/Premium)
    plan = SubscriptionPlan.objects.filter(tier='starter').first()
    if not plan:
        print("❌ FAIL: No 'starter' plan found in database.")
        return
        
    print(f"Target Plan: {plan.name}")

    # 3. Simulate Paystack Success Payload
    # This mirrors the data structure from Paystack API
    mock_reference = f"verify_ref_{timezone.now().timestamp()}"
    mock_payload = {
        "amount": 300, # 300 cents = 3 KES (or whatever the starter price is)
        "currency": "KES",
        "status": "success",
        "authorization": {
            "authorization_code": "AUTH_demo_123",
            "last4": "4242",
            "exp_month": "12",
            "exp_year": "2030",
            "channel": "card",
            "card_type": "visa"
        }
    }

    print(f"Simulating payment confirmation for reference: {mock_reference}...")

    # 4. Trigger Internal Application Logic
    try:
        # We call the core helper that the API view uses
        _apply_paystack_payment(
            user=user,
            plan=plan,
            payload=mock_payload,
            reference=mock_reference,
            is_yearly=False
        )
        
        # 5. Verify Database Side-Effects
        subscription = UserSubscription.objects.get(user=user)
        transaction = PaymentTransaction.objects.get(gateway_transaction_id=mock_reference)
        
        print(f"✅ DB Update: Subscription status is '{subscription.status}'")
        print(f"✅ DB Update: Plan is '{subscription.plan.name}'")
        print(f"✅ DB Update: Transaction recorded for {transaction.amount} {transaction.currency}")
        
        # Check dates
        if subscription.current_period_end > timezone.now():
            print(f"✅ Success: Subscription period correctly extended to {subscription.current_period_end}")
        else:
            print("⚠️ WARNING: Subscription period not extended.")

        # Cleanup verification data to keep DB clean
        transaction.delete()
        print("🧹 Verification artifacts cleaned up.")

    except Exception as e:
        print(f"❌ FAIL: Payment application error: {e}")

    print("\n--- ✅ PAYMENT HANDSHAKE VERIFICATION COMPLETE ---")

if __name__ == "__main__":
    verify_payment_handshake()
