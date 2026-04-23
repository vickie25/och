# Phase 6: Cohort ID alignment (BIGINT vs UUID)

## Current state (confirmed on production DB)

- `cohorts.id` is **BIGINT** (`int8`).
- Several tables store `cohort_id` as **UUID** with **no FK** to `cohorts(id)`:
  - `cohort_progress.cohort_id` (uuid)
  - `mentor_payouts.cohort_id` (uuid)
  - `revenue_share_tracking.cohort_id` (uuid)
  - `sponsor_cohort_dashboard.cohort_id` (uuid)
  - `sponsor_financial_transactions.cohort_id` (uuid)
  - `sponsor_report_requests.cohort_id` (uuid)
  - `sponsor_student_aggregates.cohort_id` (uuid)
  - `student_dashboard_cache.cohort_id` (uuid)
- Some tables already use BIGINT cohort ids:
  - `users.cohort_id` (bigint)
  - `user_roles.cohort_id` (bigint)

This mismatch is why certain Django migrations fail when they try to add FK constraints to `cohorts(id)`.

## Recommended safest strategy (2-step, minimal downtime)

### Step A (compatibility bridge — safe, reversible)

Goal: let UUID-typed `cohort_id` references keep working while we converge.

- Add a **new** UUID column on `cohorts` (do NOT change the PK yet):
  - `cohorts.uuid_id uuid NOT NULL DEFAULT gen_random_uuid() UNIQUE`
- Expose `uuid_id` in the app as the “external identifier” for cohort references where UUIDs are expected.
- Update high-risk tables to reference `cohorts.uuid_id` instead of `cohorts.id` (by data migration + index), and only then add FK constraints.

This avoids breaking existing BIGINT-based joins while allowing UUID-based features (sponsor dashboards, finance, progress caches) to become consistent.

### Step B (full convergence)

Pick one canonical id and migrate everything to it:

- **Option 1 (recommended)**: keep `cohorts.id` as BIGINT PK and treat `uuid_id` as the cross-service stable identifier.
  - Pros: minimal change to existing DB; avoids rewriting PKs; lower operational risk.
  - Cons: Django app code must consistently use `uuid_id` for external-facing references.

- **Option 2**: migrate PK to UUID.
  - Pros: consistency with UUID-based tables/migrations.
  - Cons: high risk; requires rewriting every FK, rebuilding indexes, careful downtime window.

## What I already did to unblock Phase 5 safely

- Created sponsor dashboard tables **without FK to `cohorts(id)`** so schema exists and the app can run without crashing due to missing tables.
- Marked sponsor-dashboard migrations as applied to keep Django migration graph consistent.

## Next execution checklist (when you’re ready to complete Phase 6 fully)

- Back up DB snapshot.
- Add `cohorts.uuid_id` + backfill (fast).
- Update the app models/migrations to use `uuid_id` consistently for the affected tables.
- Add FK constraints to `cohorts.uuid_id` (not `cohorts.id`) for UUID cohort references.
- Re-run migrations without `--fake` for the affected apps.
- Smoke test: sponsor dashboard endpoints, finance flows, cohort progress endpoints.

