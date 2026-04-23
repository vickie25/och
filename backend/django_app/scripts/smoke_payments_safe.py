import os
import sys
import uuid


def main() -> int:
    sys.path.insert(0, "/app")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.production")
    import django

    django.setup()

    from django.contrib.auth import get_user_model
    from django.db import connection
    from django.utils import timezone

    from subscriptions.models import PaymentTransaction, SubscriptionPlan, UserSubscription
    from subscriptions.views import _apply_paystack_payment

    print("SMOKE_PAYMENTS_SAFE")

    # 0) Env sanity (do not print secrets)
    secret = os.environ.get("PAYSTACK_SECRET_KEY") or os.environ.get("PAYSTACK_SECRET") or ""
    public = os.environ.get("PAYSTACK_PUBLIC_KEY") or os.environ.get("NEXT_PUBLIC_PAYSTACK_PUBLIC_KEY") or ""
    currency = (os.environ.get("PAYSTACK_DEFAULT_CURRENCY") or "KES").upper()
    print("ENV_PAYSTACK_SECRET_SET", bool(secret))
    print("ENV_PAYSTACK_PUBLIC_SET", bool(public))
    print("ENV_PAYSTACK_DEFAULT_CURRENCY", currency)

    # 1) Table presence check (use real Django table names to avoid drift/renames)
    must_have_tables = [
        SubscriptionPlan._meta.db_table,
        UserSubscription._meta.db_table,
        PaymentTransaction._meta.db_table,
        "pricing_tiers",
        "invoices",
        "payments",
        "transactions",
    ]
    with connection.cursor() as cur:
        for t in must_have_tables:
            cur.execute("select to_regclass(%s)", [f"public.{t}"])
            ok = cur.fetchone()[0]
            if ok:
                print("TABLE", t, "OK")
                continue
            # If regclass lookup fails, double-check via information_schema (avoids false negatives
            # when schema/name drift exists).
            cur.execute(
                "select table_schema, table_name from information_schema.tables where table_name=%s",
                [t],
            )
            rows = cur.fetchall()
            if rows:
                print("TABLE", t, "FOUND_AS", rows[:3])
            else:
                print("TABLE", t, "MISSING")

    # 2) Plan existence
    plan = SubscriptionPlan.objects.filter(tier="starter").first()
    if not plan:
        print("FAIL_NO_STARTER_PLAN")
        return 2
    print("PLAN_STARTER", plan.id, plan.name)

    # 3) Create temp user (clean up at end)
    User = get_user_model()
    email = f"pay_smoke_{uuid.uuid4().hex[:10]}@example.com"
    # This project requires username/first_name/last_name in create_user.
    username = f"pay_smoke_{uuid.uuid4().hex[:10]}"
    password = uuid.uuid4().hex
    # Some custom managers require positional args (username, email, password).
    user = User.objects.create_user(username, email, password, first_name="Pay", last_name="Smoke")
    user.is_active = True
    user.save(update_fields=["is_active"])
    print("TEMP_USER_CREATED", user.id, user.email)

    mock_reference = f"verify_ref_{timezone.now().timestamp()}"
    mock_payload = {
        "amount": 300,
        "currency": currency,
        "status": "success",
        "authorization": {
            "authorization_code": "AUTH_demo_123",
            "last4": "4242",
            "exp_month": "12",
            "exp_year": "2030",
            "channel": "card",
            "card_type": "visa",
        },
    }

    # 4) Exercise the real internal apply logic
    try:
        _apply_paystack_payment(
            user=user,
            plan=plan,
            payload=mock_payload,
            reference=mock_reference,
            is_yearly=False,
        )

        subscription = UserSubscription.objects.get(user=user)
        tx = PaymentTransaction.objects.get(gateway_transaction_id=mock_reference)
        print("SUB_STATUS", subscription.status)
        print("SUB_PLAN", subscription.plan.name, subscription.plan.tier)
        print("TX", str(tx.amount), tx.currency, tx.status)
        print("SUB_PERIOD_END_GT_NOW", bool(subscription.current_period_end and subscription.current_period_end > timezone.now()))

    except Exception as e:
        print("FAIL_APPLY_PAYMENT", type(e).__name__, str(e))
        return 3
    finally:
        # 5) Cleanup artifacts (keep production clean)
        try:
            PaymentTransaction.objects.filter(gateway_transaction_id=mock_reference).delete()
        except Exception:
            pass
        try:
            UserSubscription.objects.filter(user=user).delete()
        except Exception:
            pass
        try:
            user.delete()
        except Exception:
            pass
        print("CLEANUP_DONE")

    print("OK_SMOKE_PAYMENTS_SAFE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

