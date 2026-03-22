# Student Stream A: catalog JSON, billing SKUs, policy defaults, user subscription lifecycle fields.
# Database ops use ADD COLUMN IF NOT EXISTS so partial / manual DB changes do not break migrate.

from decimal import Decimal

from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


def seed_policy_and_student_plans(apps, schema_editor):
    PaymentSettings = apps.get_model('subscriptions', 'PaymentSettings')
    SubscriptionPlan = apps.get_model('subscriptions', 'SubscriptionPlan')

    PaymentSettings.objects.get_or_create(
        setting_key='student_subscription_policy',
        defaults={
            'setting_value': {
                'grace_period_days_monthly': 3,
                'grace_period_days_annual': 7,
                'renewal_attempt_days_before': 1,
                'academic_discount_percent': 30,
                'promo_single_code_per_checkout': True,
                'auto_renewal_default': True,
                'downgrade_effective': 'end_of_period',
                'upgrade_effective': 'immediate',
                'usd_to_kes_rate': 130,
                'notes': 'Editable via Admin → Payment Settings or DB; drives student UI copy.',
            },
            'description': 'Stream A (student) subscription billing policy knobs',
        },
    )

    USD_KES = Decimal('130')
    usd = lambda n: (Decimal(n) * USD_KES).quantize(Decimal('0.01'))

    defaults = [
        {
            'name': 'och_free',
            'tier': 'free',
            'stream': 'student',
            'billing_interval': 'none',
            'sort_order': 0,
            'is_listed': True,
            'price_monthly': Decimal('0'),
            'price_annual': None,
            'missions_access_type': 'ai_only',
            'mentorship_access': False,
            'talentscope_access': 'preview',
            'marketplace_contact': False,
            'ai_coach_daily_limit': 1,
            'portfolio_item_limit': 0,
            'catalog': {
                'display_name': 'Free Tier (Tier 0–1)',
                'tier_rank': 0,
                'usd_monthly': 0,
                'usd_annual': None,
                'tier_range': {'min': 0, 'max': 1},
                'mentorship_credits_per_month': 0,
                'trial_days': 0,
                'trial_requires_payment_method': False,
                'features': {
                    'tier_2_6_access': False,
                    'tier_7_9_access': False,
                    'priority_support': False,
                    'certification_prep': False,
                    'enterprise_dashboard_trial': False,
                },
                'annual_savings_percent': None,
            },
        },
        {
            'name': 'och_pro_monthly',
            'tier': 'starter',
            'stream': 'student',
            'billing_interval': 'monthly',
            'sort_order': 10,
            'is_listed': True,
            'price_monthly': usd(29),
            'price_annual': None,
            'missions_access_type': 'full',
            'mentorship_access': True,
            'talentscope_access': 'full',
            'marketplace_contact': True,
            'ai_coach_daily_limit': None,
            'portfolio_item_limit': None,
            'catalog': {
                'display_name': 'Pro Monthly',
                'tier_rank': 2,
                'usd_monthly': 29,
                'usd_annual': None,
                'tier_range': {'min': 2, 'max': 6},
                'mentorship_credits_per_month': 2,
                'trial_days': 14,
                'trial_requires_payment_method': False,
                'features': {
                    'tier_2_6_access': True,
                    'tier_7_9_access': False,
                    'priority_support': False,
                    'certification_prep': False,
                    'enterprise_dashboard_trial': False,
                },
                'annual_savings_percent': None,
            },
        },
        {
            'name': 'och_pro_annual',
            'tier': 'starter',
            'stream': 'student',
            'billing_interval': 'annual',
            'sort_order': 20,
            'is_listed': True,
            'price_monthly': Decimal('0'),
            'price_annual': usd(290),
            'missions_access_type': 'full',
            'mentorship_access': True,
            'talentscope_access': 'full',
            'marketplace_contact': True,
            'ai_coach_daily_limit': None,
            'portfolio_item_limit': None,
            'catalog': {
                'display_name': 'Pro Annual',
                'tier_rank': 2,
                'usd_monthly': None,
                'usd_annual': 290,
                'tier_range': {'min': 2, 'max': 6},
                'mentorship_credits_per_month': 5,
                'trial_days': 14,
                'trial_requires_payment_method': False,
                'features': {
                    'tier_2_6_access': True,
                    'tier_7_9_access': False,
                    'priority_support': False,
                    'certification_prep': False,
                    'enterprise_dashboard_trial': False,
                },
                'annual_savings_percent': 17,
            },
        },
        {
            'name': 'och_premium',
            'tier': 'premium',
            'stream': 'student',
            'billing_interval': 'monthly',
            'sort_order': 30,
            'is_listed': True,
            'price_monthly': usd(49),
            'price_annual': usd(490),
            'missions_access_type': 'full',
            'mentorship_access': True,
            'talentscope_access': 'full',
            'marketplace_contact': True,
            'ai_coach_daily_limit': None,
            'portfolio_item_limit': None,
            'catalog': {
                'display_name': 'Premium',
                'tier_rank': 3,
                'usd_monthly': 49,
                'usd_annual': 490,
                'tier_range': {'min': 2, 'max': 9},
                'mentorship_credits_per_month': None,
                'trial_days': 7,
                'trial_requires_payment_method': True,
                'features': {
                    'tier_2_6_access': True,
                    'tier_7_9_access': True,
                    'priority_support': True,
                    'certification_prep': True,
                    'enterprise_dashboard_trial': True,
                },
                'annual_savings_percent': 17,
            },
        },
    ]

    for row in defaults:
        SubscriptionPlan.objects.update_or_create(
            name=row['name'],
            defaults={k: v for k, v in row.items() if k != 'name'},
        )


def noop_reverse(apps, schema_editor):
    pass


def apply_pg_schema_0005(apps, schema_editor):
    """Idempotent column adds (PostgreSQL: IF NOT EXISTS; SQLite 3.35+: IF NOT EXISTS)."""
    vendor = schema_editor.connection.vendor
    if vendor == 'sqlite':
        stmts = [
            "ALTER TABLE subscription_plans ADD COLUMN IF NOT EXISTS billing_interval varchar(16) NOT NULL DEFAULT 'monthly'",
            "ALTER TABLE subscription_plans ADD COLUMN IF NOT EXISTS catalog TEXT NOT NULL DEFAULT '{}'",
            "ALTER TABLE subscription_plans ADD COLUMN IF NOT EXISTS is_listed integer NOT NULL DEFAULT 1",
            "ALTER TABLE subscription_plans ADD COLUMN IF NOT EXISTS price_annual decimal(12, 2) NULL",
            "ALTER TABLE subscription_plans ADD COLUMN IF NOT EXISTS sort_order smallint NOT NULL DEFAULT 0",
            "ALTER TABLE subscription_plans ADD COLUMN IF NOT EXISTS stream varchar(32) NOT NULL DEFAULT 'student'",
            "CREATE INDEX IF NOT EXISTS subscription_plans_stream_idx ON subscription_plans (stream)",
            "CREATE INDEX IF NOT EXISTS subscription_plans_is_listed_idx ON subscription_plans (is_listed)",
            "CREATE INDEX IF NOT EXISTS subscription_plans_billing_interval_idx ON subscription_plans (billing_interval)",
            "ALTER TABLE user_subscriptions ADD COLUMN IF NOT EXISTS billing_interval varchar(16) NOT NULL DEFAULT 'monthly'",
            "ALTER TABLE user_subscriptions ADD COLUMN IF NOT EXISTS trial_end datetime NULL",
            "ALTER TABLE user_subscriptions ADD COLUMN IF NOT EXISTS cancel_at_period_end integer NOT NULL DEFAULT 0",
            "ALTER TABLE user_subscriptions ADD COLUMN IF NOT EXISTS grace_period_end datetime NULL",
            "ALTER TABLE user_subscriptions ADD COLUMN IF NOT EXISTS pending_downgrade_plan_id char(32) NULL REFERENCES subscription_plans (id)",
            "CREATE INDEX IF NOT EXISTS user_subscriptions_billing_interval_idx ON user_subscriptions (billing_interval)",
            "CREATE INDEX IF NOT EXISTS user_subscriptions_trial_end_idx ON user_subscriptions (trial_end)",
            "CREATE INDEX IF NOT EXISTS user_subscriptions_grace_period_end_idx ON user_subscriptions (grace_period_end)",
        ]
        with schema_editor.connection.cursor() as cursor:
            for sql in stmts:
                cursor.execute(sql)
        return
    if vendor != 'postgresql':
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
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
        """)
        cursor.execute("""
            DO $fk$
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
            END $fk$;
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS user_subscriptions_billing_interval_idx ON user_subscriptions (billing_interval);
            CREATE INDEX IF NOT EXISTS user_subscriptions_trial_end_idx ON user_subscriptions (trial_end);
            CREATE INDEX IF NOT EXISTS user_subscriptions_grace_period_end_idx ON user_subscriptions (grace_period_end);
        """)


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0004_add_promo_academic_invoice_retry'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(apply_pg_schema_0005, noop_reverse),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='subscriptionplan',
                    name='billing_interval',
                    field=models.CharField(
                        choices=[('none', 'No billing (free)'), ('monthly', 'Monthly'), ('annual', 'Annual')],
                        db_index=True,
                        default='monthly',
                        help_text='How this SKU is billed (free tier = none)',
                        max_length=16,
                    ),
                ),
                migrations.AddField(
                    model_name='subscriptionplan',
                    name='catalog',
                    field=models.JSONField(
                        blank=True,
                        default=dict,
                        help_text='Stream A metadata: tier_rank, usd_monthly, usd_annual, tier_range {min,max}, mentorship_credits_per_month (null = unlimited), trial_days, trial_requires_payment_method, features {tier_2_6_access, tier_7_9_access, priority_support, certification_prep}, annual_savings_percent, display_name, marketing_notes',
                    ),
                ),
                migrations.AddField(
                    model_name='subscriptionplan',
                    name='is_listed',
                    field=models.BooleanField(db_index=True, default=True, help_text='Show on student pricing pages; admin can hide SKUs without deleting'),
                ),
                migrations.AddField(
                    model_name='subscriptionplan',
                    name='price_annual',
                    field=models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        help_text='Annual price in primary ledger currency (KES) when billing_interval is annual',
                        max_digits=12,
                        null=True,
                        validators=[django.core.validators.MinValueValidator(0)],
                    ),
                ),
                migrations.AddField(
                    model_name='subscriptionplan',
                    name='sort_order',
                    field=models.PositiveSmallIntegerField(default=0, help_text='Display order (lower first)'),
                ),
                migrations.AddField(
                    model_name='subscriptionplan',
                    name='stream',
                    field=models.CharField(
                        choices=[('student', 'Student (Stream A)')],
                        db_index=True,
                        default='student',
                        help_text='Revenue stream (e.g. student vs future B2B)',
                        max_length=32,
                    ),
                ),
                migrations.AddField(
                    model_name='usersubscription',
                    name='billing_interval',
                    field=models.CharField(
                        choices=[('none', 'No billing (free)'), ('monthly', 'Monthly'), ('annual', 'Annual')],
                        db_index=True,
                        default='monthly',
                        help_text='Active cycle for this subscription (monthly vs annual)',
                        max_length=16,
                    ),
                ),
                migrations.AddField(
                    model_name='usersubscription',
                    name='cancel_at_period_end',
                    field=models.BooleanField(default=False, help_text='Cancellation scheduled for end of current period'),
                ),
                migrations.AddField(
                    model_name='usersubscription',
                    name='grace_period_end',
                    field=models.DateTimeField(blank=True, db_index=True, help_text='Access continues until this time after a failed renewal', null=True),
                ),
                migrations.AddField(
                    model_name='usersubscription',
                    name='pending_downgrade_plan',
                    field=models.ForeignKey(
                        blank=True,
                        help_text='If set, user moves to this plan at current_period_end',
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='pending_downgrades',
                        to='subscriptions.subscriptionplan',
                    ),
                ),
                migrations.AddField(
                    model_name='usersubscription',
                    name='trial_end',
                    field=models.DateTimeField(blank=True, db_index=True, help_text='When trial ends (if applicable)', null=True),
                ),
            ],
        ),
        migrations.RunPython(seed_policy_and_student_plans, noop_reverse),
    ]
