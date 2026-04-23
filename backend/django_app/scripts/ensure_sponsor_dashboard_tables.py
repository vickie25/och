import os
import sys


DDL = [
    # Ensure uuid generator exists (used by app defaults)
    'CREATE EXTENSION IF NOT EXISTS "pgcrypto";',
    # sponsor_dashboard_cache (org_id is PK)
    """
    CREATE TABLE IF NOT EXISTS "sponsor_dashboard_cache" (
      "org_id" bigint NOT NULL PRIMARY KEY,
      "seats_total" integer NOT NULL DEFAULT 0,
      "seats_used" integer NOT NULL DEFAULT 0,
      "seats_at_risk" integer NOT NULL DEFAULT 0,
      "budget_total" numeric(12,2) NOT NULL DEFAULT 0,
      "budget_used" numeric(12,2) NOT NULL DEFAULT 0,
      "budget_used_pct" numeric(5,2) NOT NULL DEFAULT 0,
      "avg_readiness" numeric(5,2) NOT NULL DEFAULT 0,
      "avg_completion_pct" numeric(5,2) NOT NULL DEFAULT 0,
      "graduates_count" integer NOT NULL DEFAULT 0,
      "active_cohorts_count" integer NOT NULL DEFAULT 0,
      "overdue_invoices_count" integer NOT NULL DEFAULT 0,
      "low_utilization_cohorts" integer NOT NULL DEFAULT 0,
      "cache_updated_at" timestamp with time zone NOT NULL DEFAULT now()
    );
    """,
    "CREATE INDEX IF NOT EXISTS sponsor_dashboard_cache_org_id_idx ON sponsor_dashboard_cache(org_id);",
    # FK org_id -> organizations(id)
    """
    DO $$
    BEGIN
      IF EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relname='organizations') THEN
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='sponsor_dashboard_cache_org_id_fkey') THEN
          ALTER TABLE sponsor_dashboard_cache
            ADD CONSTRAINT sponsor_dashboard_cache_org_id_fkey
            FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE CASCADE;
        END IF;
      END IF;
    END
    $$;
    """,
    # sponsor_cohort_dashboard
    """
    CREATE TABLE IF NOT EXISTS "sponsor_cohort_dashboard" (
      "id" uuid NOT NULL PRIMARY KEY,
      "org_id" bigint NOT NULL,
      "cohort_id" uuid NOT NULL,
      "cohort_name" varchar(200) NOT NULL,
      "track_name" varchar(200) NOT NULL DEFAULT '',
      "start_date" date NULL,
      "end_date" date NULL,
      "mode" varchar(20) NOT NULL DEFAULT '',
      "seats_total" integer NOT NULL DEFAULT 0,
      "seats_used" integer NOT NULL DEFAULT 0,
      "seats_sponsored" integer NOT NULL DEFAULT 0,
      "seats_remaining" integer NOT NULL DEFAULT 0,
      "avg_readiness" numeric(5,2) NULL,
      "completion_pct" numeric(5,2) NULL,
      "portfolio_health_avg" numeric(5,2) NULL,
      "graduates_count" integer NOT NULL DEFAULT 0,
      "at_risk_count" integer NOT NULL DEFAULT 0,
      "next_milestone" jsonb NOT NULL DEFAULT '{}'::jsonb,
      "upcoming_events" jsonb NOT NULL DEFAULT '[]'::jsonb,
      "flags" jsonb NOT NULL DEFAULT '[]'::jsonb,
      "updated_at" timestamp with time zone NOT NULL DEFAULT now()
    );
    """,
    "CREATE INDEX IF NOT EXISTS sponsor_cohort_dashboard_org_updated_idx ON sponsor_cohort_dashboard(org_id, updated_at);",
    "CREATE INDEX IF NOT EXISTS sponsor_cohort_dashboard_cohort_idx ON sponsor_cohort_dashboard(cohort_id);",
    """
    DO $$
    BEGIN
      IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='sponsor_cohort_dashboard_org_id_fkey') THEN
        ALTER TABLE sponsor_cohort_dashboard
          ADD CONSTRAINT sponsor_cohort_dashboard_org_id_fkey
          FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE CASCADE;
      END IF;
    END
    $$;
    """,
    # NOTE: cohort FK intentionally omitted due to known cohorts.id type drift (uuid vs bigint)
    """
    DO $$
    BEGIN
      IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='sponsor_cohort_dashboard_org_id_cohort_id_uniq') THEN
        ALTER TABLE sponsor_cohort_dashboard
          ADD CONSTRAINT sponsor_cohort_dashboard_org_id_cohort_id_uniq
          UNIQUE (org_id, cohort_id);
      END IF;
    END
    $$;
    """,
    # sponsor_student_aggregates
    """
    CREATE TABLE IF NOT EXISTS "sponsor_student_aggregates" (
      "id" uuid NOT NULL PRIMARY KEY,
      "org_id" bigint NOT NULL,
      "cohort_id" uuid NOT NULL,
      "student_id" bigint NOT NULL,
      "name_anonymized" varchar(100) NOT NULL,
      "readiness_score" numeric(5,2) NULL,
      "completion_pct" numeric(5,2) NULL,
      "portfolio_items" integer NOT NULL DEFAULT 0,
      "consent_employer_share" boolean NOT NULL DEFAULT false,
      "updated_at" timestamp with time zone NOT NULL DEFAULT now()
    );
    """,
    "CREATE INDEX IF NOT EXISTS sponsor_student_aggregates_org_cohort_idx ON sponsor_student_aggregates(org_id, cohort_id);",
    "CREATE INDEX IF NOT EXISTS sponsor_student_aggregates_org_consent_idx ON sponsor_student_aggregates(org_id, consent_employer_share);",
    """
    DO $$
    BEGIN
      IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='sponsor_student_aggregates_org_id_fkey') THEN
        ALTER TABLE sponsor_student_aggregates
          ADD CONSTRAINT sponsor_student_aggregates_org_id_fkey
          FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE CASCADE;
      END IF;
    END
    $$;
    """,
    """
    DO $$
    BEGIN
      IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='sponsor_student_aggregates_student_id_fkey') THEN
        ALTER TABLE sponsor_student_aggregates
          ADD CONSTRAINT sponsor_student_aggregates_student_id_fkey
          FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE;
      END IF;
    END
    $$;
    """,
    # NOTE: cohort FK intentionally omitted due to known cohorts.id type drift
    """
    DO $$
    BEGIN
      IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='sponsor_student_aggregates_org_id_cohort_id_student_id_uniq') THEN
        ALTER TABLE sponsor_student_aggregates
          ADD CONSTRAINT sponsor_student_aggregates_org_id_cohort_id_student_id_uniq
          UNIQUE (org_id, cohort_id, student_id);
      END IF;
    END
    $$;
    """,
    # sponsor_codes
    """
    CREATE TABLE IF NOT EXISTS "sponsor_codes" (
      "id" uuid NOT NULL PRIMARY KEY,
      "org_id" bigint NOT NULL,
      "code" varchar(50) NOT NULL UNIQUE,
      "seats" integer NOT NULL,
      "value_per_seat" numeric(8,2) NULL,
      "valid_from" date NULL,
      "valid_until" date NULL,
      "usage_count" integer NOT NULL DEFAULT 0,
      "max_usage" integer NULL,
      "status" varchar(20) NOT NULL DEFAULT 'active',
      "created_at" timestamp with time zone NOT NULL DEFAULT now(),
      "updated_at" timestamp with time zone NOT NULL DEFAULT now()
    );
    """,
    "CREATE INDEX IF NOT EXISTS sponsor_codes_org_status_idx ON sponsor_codes(org_id, status);",
    "CREATE INDEX IF NOT EXISTS sponsor_codes_code_idx ON sponsor_codes(code);",
    """
    DO $$
    BEGIN
      IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='sponsor_codes_org_id_fkey') THEN
        ALTER TABLE sponsor_codes
          ADD CONSTRAINT sponsor_codes_org_id_fkey
          FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE CASCADE;
      END IF;
    END
    $$;
    """,
    # sponsor_report_requests
    """
    CREATE TABLE IF NOT EXISTS "sponsor_report_requests" (
      "id" uuid NOT NULL PRIMARY KEY,
      "org_id" bigint NOT NULL,
      "request_type" varchar(32) NOT NULL DEFAULT 'graduate_breakdown',
      "cohort_id" uuid NULL,
      "details" text NOT NULL DEFAULT '',
      "status" varchar(20) NOT NULL DEFAULT 'pending',
      "created_at" timestamp with time zone NOT NULL DEFAULT now(),
      "delivered_at" timestamp with time zone NULL,
      "delivered_by_id" bigint NULL,
      "attachment_url" varchar(500) NOT NULL DEFAULT ''
    );
    """,
    "CREATE INDEX IF NOT EXISTS sponsor_report_requests_org_status_idx ON sponsor_report_requests(org_id, status);",
    "CREATE INDEX IF NOT EXISTS sponsor_report_requests_status_idx ON sponsor_report_requests(status);",
    """
    DO $$
    BEGIN
      IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='sponsor_report_requests_org_id_fkey') THEN
        ALTER TABLE sponsor_report_requests
          ADD CONSTRAINT sponsor_report_requests_org_id_fkey
          FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE CASCADE;
      END IF;
    END
    $$;
    """,
    """
    DO $$
    BEGIN
      IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='sponsor_report_requests_delivered_by_id_fkey') THEN
        ALTER TABLE sponsor_report_requests
          ADD CONSTRAINT sponsor_report_requests_delivered_by_id_fkey
          FOREIGN KEY (delivered_by_id) REFERENCES users(id) ON DELETE SET NULL;
      END IF;
    END
    $$;
    """,
]


def main() -> int:
    sys.path.insert(0, "/app")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.production")
    import django

    django.setup()
    from django.db import connection

    with connection.cursor() as cur:
        for stmt in DDL:
            cur.execute(stmt)
            first = (stmt.strip().splitlines() or [""])[0][:100]
            print("OK", first)

        for t in [
            "sponsor_dashboard_cache",
            "sponsor_cohort_dashboard",
            "sponsor_student_aggregates",
            "sponsor_codes",
            "sponsor_report_requests",
        ]:
            cur.execute("select to_regclass(%s)", [f"public.{t}"])
            print("TABLE", t, cur.fetchone()[0])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

