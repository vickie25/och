-- =============================================================================
-- Mirrors Django subscriptions.0005_student_stream_catalog_and_policy (schema only).
--
-- WHY: Django models expect user_subscriptions.billing_interval (and plan catalog
-- columns). If these columns are missing, /api/v1/subscription/status returns 500.
--
-- RECOMMENDED (DB already matches migrations 0001–0004 in django_migrations):
--   python manage.py migrate subscriptions
--
-- IF migrate fails on 0004 (e.g. "promotional_codes already exists") your DB was
-- created manually. Align migration history, then apply 0005:
--   python manage.py migrate subscriptions 0004 --fake
--   python manage.py migrate subscriptions 0005
--
-- IF you apply THIS FILE instead of migrate 0005, record it so Django does not
-- try to re-apply 0005:
--   INSERT INTO django_migrations (app, name, applied)
--   VALUES ('subscriptions', '0005_student_stream_catalog_and_policy', NOW());
-- Then run migrate again (it should no-op). RunPython seed in 0005 will NOT run —
-- use migrate 0005 for full seed, or insert PaymentSettings / plans by hand.
-- =============================================================================

BEGIN;

-- subscription_plans
ALTER TABLE subscription_plans
  ADD COLUMN IF NOT EXISTS billing_interval varchar(16) NOT NULL DEFAULT 'monthly';

ALTER TABLE subscription_plans
  ADD COLUMN IF NOT EXISTS catalog jsonb NOT NULL DEFAULT '{}'::jsonb;

ALTER TABLE subscription_plans
  ADD COLUMN IF NOT EXISTS is_listed boolean NOT NULL DEFAULT true;

ALTER TABLE subscription_plans
  ADD COLUMN IF NOT EXISTS price_annual numeric(12, 2) NULL;

ALTER TABLE subscription_plans
  ADD COLUMN IF NOT EXISTS sort_order smallint NOT NULL DEFAULT 0;

ALTER TABLE subscription_plans
  ADD COLUMN IF NOT EXISTS stream varchar(32) NOT NULL DEFAULT 'student';

CREATE INDEX IF NOT EXISTS subscription_plans_stream_idx ON subscription_plans (stream);
CREATE INDEX IF NOT EXISTS subscription_plans_is_listed_idx ON subscription_plans (is_listed);
CREATE INDEX IF NOT EXISTS subscription_plans_billing_interval_idx ON subscription_plans (billing_interval);

-- user_subscriptions
ALTER TABLE user_subscriptions
  ADD COLUMN IF NOT EXISTS billing_interval varchar(16) NOT NULL DEFAULT 'monthly';

ALTER TABLE user_subscriptions
  ADD COLUMN IF NOT EXISTS trial_end timestamptz NULL;

ALTER TABLE user_subscriptions
  ADD COLUMN IF NOT EXISTS cancel_at_period_end boolean NOT NULL DEFAULT false;

ALTER TABLE user_subscriptions
  ADD COLUMN IF NOT EXISTS grace_period_end timestamptz NULL;

ALTER TABLE user_subscriptions
  ADD COLUMN IF NOT EXISTS pending_downgrade_plan_id uuid NULL;

-- FK pending_downgrade_plan → subscription_plans (defer constraint add if orphans)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'user_subscriptions_pending_downgrade_plan_id_fkey'
  ) THEN
    ALTER TABLE user_subscriptions
      ADD CONSTRAINT user_subscriptions_pending_downgrade_plan_id_fkey
      FOREIGN KEY (pending_downgrade_plan_id)
      REFERENCES subscription_plans (id)
      ON DELETE SET NULL;
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS user_subscriptions_billing_interval_idx ON user_subscriptions (billing_interval);
CREATE INDEX IF NOT EXISTS user_subscriptions_trial_end_idx ON user_subscriptions (trial_end);
CREATE INDEX IF NOT EXISTS user_subscriptions_grace_period_end_idx ON user_subscriptions (grace_period_end);

COMMIT;

-- =============================================================================
