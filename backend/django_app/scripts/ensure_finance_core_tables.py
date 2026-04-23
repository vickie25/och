import os
import sys


DDL = [
    # wallets
    """
    CREATE TABLE IF NOT EXISTS "wallets" (
      "id" uuid NOT NULL PRIMARY KEY,
      "user_id" bigint NOT NULL,
      "balance" numeric(12,2) NOT NULL DEFAULT 0,
      "currency" varchar(3) NOT NULL DEFAULT 'USD',
      "last_transaction_at" timestamp with time zone NULL,
      "created_at" timestamp with time zone NOT NULL DEFAULT now(),
      "updated_at" timestamp with time zone NOT NULL DEFAULT now()
    );
    """,
    "CREATE INDEX IF NOT EXISTS wallets_user_id_idx ON wallets(user_id);",
    # transactions
    """
    CREATE TABLE IF NOT EXISTS "transactions" (
      "id" uuid NOT NULL PRIMARY KEY,
      "wallet_id" uuid NOT NULL,
      "type" varchar(20) NOT NULL,
      "amount" numeric(12,2) NOT NULL,
      "description" text NOT NULL DEFAULT '',
      "reference_type" varchar(50) NULL,
      "reference_id" uuid NULL,
      "created_at" timestamp with time zone NOT NULL DEFAULT now()
    );
    """,
    "CREATE INDEX IF NOT EXISTS transactions_wallet_id_idx ON transactions(wallet_id);",
    # credits
    """
    CREATE TABLE IF NOT EXISTS "credits" (
      "id" uuid NOT NULL PRIMARY KEY,
      "user_id" bigint NOT NULL,
      "type" varchar(20) NOT NULL,
      "amount" numeric(12,2) NOT NULL,
      "remaining" numeric(12,2) NOT NULL,
      "expires_at" timestamp with time zone NULL,
      "created_at" timestamp with time zone NOT NULL DEFAULT now(),
      "updated_at" timestamp with time zone NOT NULL DEFAULT now()
    );
    """,
    "CREATE INDEX IF NOT EXISTS credits_user_id_idx ON credits(user_id);",
    # contracts (org id is bigint)
    """
    CREATE TABLE IF NOT EXISTS "contracts" (
      "id" uuid NOT NULL PRIMARY KEY,
      "organization_id" bigint NOT NULL,
      "type" varchar(20) NOT NULL,
      "status" varchar(20) NOT NULL,
      "start_date" date NOT NULL,
      "end_date" date NOT NULL,
      "employer_plan" varchar(20) NULL,
      "institution_pricing_tier" varchar(30) NULL,
      "billing_cycle" varchar(20) NULL,
      "seat_cap" integer NULL,
      "total_value" numeric(15,2) NOT NULL,
      "created_at" timestamp with time zone NOT NULL DEFAULT now(),
      "updated_at" timestamp with time zone NOT NULL DEFAULT now()
    );
    """,
    "CREATE INDEX IF NOT EXISTS contracts_org_id_idx ON contracts(organization_id);",
    # tax rates
    """
    CREATE TABLE IF NOT EXISTS "tax_rates" (
      "id" uuid NOT NULL PRIMARY KEY,
      "country" varchar(2) NOT NULL,
      "region" varchar(100) NOT NULL DEFAULT '',
      "type" varchar(20) NOT NULL,
      "rate" numeric(7,4) NOT NULL,
      "is_active" boolean NOT NULL DEFAULT true,
      "effective_date" timestamp with time zone NOT NULL,
      "created_at" timestamp with time zone NOT NULL DEFAULT now(),
      "updated_at" timestamp with time zone NOT NULL DEFAULT now()
    );
    """,
    "CREATE INDEX IF NOT EXISTS tax_rates_country_idx ON tax_rates(country);",
    # mentor payouts (workaround: cohort_id exists but no FK due to cohort id type mismatch)
    """
    CREATE TABLE IF NOT EXISTS "mentor_payouts" (
      "id" uuid NOT NULL PRIMARY KEY,
      "mentor_id" bigint NOT NULL,
      "cohort_id" uuid NULL,
      "compensation_mode" varchar(20) NOT NULL,
      "amount" numeric(10,2) NOT NULL,
      "status" varchar(20) NOT NULL,
      "period_start" date NOT NULL,
      "period_end" date NOT NULL,
      "payout_method" varchar(50) NOT NULL DEFAULT '',
      "created_at" timestamp with time zone NOT NULL DEFAULT now(),
      "updated_at" timestamp with time zone NOT NULL DEFAULT now()
    );
    """,
    "CREATE INDEX IF NOT EXISTS mentor_payouts_mentor_id_idx ON mentor_payouts(mentor_id);",
    # invoices
    """
    CREATE TABLE IF NOT EXISTS "invoices" (
      "id" uuid NOT NULL PRIMARY KEY,
      "user_id" bigint NULL,
      "organization_id" bigint NULL,
      "contract_id" uuid NULL,
      "type" varchar(20) NOT NULL,
      "invoice_number" varchar(50) NOT NULL,
      "total" numeric(10,2) NOT NULL,
      "due_date" date NOT NULL,
      "status" varchar(20) NOT NULL,
      "created_at" timestamp with time zone NOT NULL DEFAULT now(),
      "updated_at" timestamp with time zone NOT NULL DEFAULT now()
    );
    """,
    "CREATE INDEX IF NOT EXISTS invoices_user_id_idx ON invoices(user_id);",
    "CREATE INDEX IF NOT EXISTS invoices_org_id_idx ON invoices(organization_id);",
    # payments
    """
    CREATE TABLE IF NOT EXISTS "payments" (
      "id" uuid NOT NULL PRIMARY KEY,
      "invoice_id" uuid NULL,
      "amount" numeric(10,2) NOT NULL,
      "currency" varchar(3) NOT NULL,
      "status" varchar(20) NOT NULL,
      "payment_method" varchar(20) NOT NULL,
      "paystack_reference" varchar(100) NOT NULL DEFAULT '',
      "stripe_payment_intent_id" varchar(100) NOT NULL DEFAULT '',
      "created_at" timestamp with time zone NOT NULL DEFAULT now(),
      "updated_at" timestamp with time zone NOT NULL DEFAULT now()
    );
    """,
    "CREATE INDEX IF NOT EXISTS payments_invoice_id_idx ON payments(invoice_id);",
    # reconciliation runs
    """
    CREATE TABLE IF NOT EXISTS "reconciliation_runs" (
      "id" uuid NOT NULL PRIMARY KEY,
      "period_start" date NOT NULL,
      "period_end" date NOT NULL,
      "book_total" numeric(12,2) NOT NULL,
      "bank_total" numeric(12,2) NOT NULL,
      "difference" numeric(12,2) NOT NULL,
      "currency" varchar(3) NOT NULL,
      "status" varchar(20) NOT NULL,
      "notes" text NOT NULL DEFAULT '',
      "created_at" timestamp with time zone NOT NULL DEFAULT now(),
      "updated_at" timestamp with time zone NOT NULL DEFAULT now()
    );
    """,
]


def main() -> int:
    sys.path.insert(0, "/app")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.production")
    import django

    django.setup()
    from django.db import connection

    with connection.cursor() as cur:
        # Ensure uuid generator exists (for id defaults in app code)
        cur.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')
        for stmt in DDL:
            cur.execute(stmt)
            print("OK", stmt.splitlines()[0].strip()[:90])

        # Quick existence check
        for t in [
            "wallets",
            "transactions",
            "credits",
            "contracts",
            "tax_rates",
            "mentor_payouts",
            "invoices",
            "payments",
            "reconciliation_runs",
        ]:
            cur.execute("select to_regclass(%s)", [f"public.{t}"])
            print("TABLE", t, cur.fetchone()[0])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

