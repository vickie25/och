# OCH (Ongoza CyberHub) — Super Understanding Guide
## 🚀 Master Onboarding Edition — Full Product, Tech & Financial Audit

> **Purpose:** This is the definitive "Ground Truth" for OCH. It maps the **High-Detail Product Spec** and the **Financial Module Spec** against the actual codebase.

---

## 🏗️ Part 1: Delivery Roadmap (Phase 0-3)

| Phase | Focus | Status |
|:---|:---|:---|
| **Phase 0** | **Platform Foundation**: Identity (SSO/JWT), PCM (Programs/Cohorts), API Gateway, Notifications, Consent/Privacy MVP. | ✅ **90% Built** |
| **Phase 1** | **Core Experience**: Profiling (T0), Foundations (T1), Tracks (T2-T6), Mentorship, Portfolio. | ✅ **85% Built** |
| **Phase 2** | **Commercial (Billing)**: Paystack Integration, Stream A/B/C/D billing, Wallets, Credits, Entitlements. | ✅ **80% Built** |
| **Phase 3** | **Analytics & Intelligence**: Data Warehouse, National Heatmaps, SRE Hardening, SAR/Erasure flows. | 🔶 **40% Built** |

---

## 📐 Part 2: System Landscape & Integration

### 1. The Financial Core
- **Revenue Stream A**: Student Subscriptions (Free, Pro Monthly/Annual, Premium).
- **Revenue Stream B**: Institutional/University Billing (Per-student licensing, 12-month min).
- **Revenue Stream C**: Employer Talent Contracts (Monthly retainer + placement fees).
- **Revenue Stream D**: Cohort-Based Programs (Fixed-price, time-bound bootcamps).
- **The "Brain" (PCM)**: Manages tracks, intakes, and capacity; gates access via **Entitlements**.

### 2. Technical Stack
- **Backend**: Django (API) + FastAPI (AI Profiler).
- **Frontend**: Next.js (App Router).
- **Payments**: Paystack (Card, Mobile Money, Bank Transfer).
- **Async Logic**: Celery (Dunning retries, renewal checks, reporting).

---

## 🏗️ Part 3: The 10-Tier High-Detail Audit

### TIER 0 — Cyber Talent Profiler
**Logic**: 7 modules (Identity, Aptitude, Tech, Scenarios, Style, Difficulty, Reflection).
**Code Status**: ✅ **134KB Backend Views**. Handles complex weighted track recommendation.

### TIER 1 — Foundations
**Logic**: Mandatory 10-module orientation. Acts as a strict gate for T2.
**Code Status**: ✅ **53KB Frontend UI**. Includes assessment quizes and reflection logs.

### TIER 2-5 — Tracks (Beginner → Mastery)
**Logic**: ~20 videos per track level + missions. T5 includes **Capstone Projects**.
**Code Status**: ✅ Massive curriculum engine. Mastery includes `models_capstone.py` and `views_capstone.py`.

### TIER 7 — Engines (Missions & Recipes)
**Logic**: Missions (multi-stage simulations) + Recipes (micro-skill "boosters").
**Code Status**: ✅ **100KB+ Logic**. Supports subtask dependencies and evidence uploads.

---

## 💰 Part 4: Financial Data Model (Master Schema)

When working on the `finance`, `subscriptions`, or `marketplace` apps, refer to these entities:

| Entity | Primary Fields | Purpose |
|:---|:---|:---|
| **Subscription** | `status`, `current_period_end`, `cancel_at_period_end`, `paystack_id` | Tracks lifecycle (Active, Past_Due, etc.) |
| **Invoice** | `amount`, `tax`, `status`, `invoice_number`, `pdf_url` | Generated for all 4 revenue streams. |
| **Payment** | `paystack_reference`, `status`, `payment_method` | Immutable record of transaction. |
| **Contract** | `organization_id`, `start_date`, `end_date`, `total_value` | B2B agreements for Inst/Employers. |
| **Wallet** | `balance`, `currency`, `last_transaction_at` | Learner's internal credit balance. |
| **MentorPayout** | `mentor_id`, `amount`, `status` (pending/paid) | Tracks 1-on-1 and cohort compensation. |

---

## 🔄 Part 5: Core Financial Logic

### 1. Subscription State Machine
`TRIAL` → `ACTIVE` → `PAST_DUE` (retries on Day 1, 3, 7) → `SUSPENDED` (Day 14).

### 2. Proration (Upgrades)
When a student moves **Pro Monthly ($29) → Premium ($49)** mid-cycle:
- **Credit**: (Remaining Days / Total Days) * $29.
- **Charge**: (Remaining Days / Total Days) * $49 - Credit.
- **Effect**: Upgrade is immediate; Downgrades only at period end.

### 3. Cohort Enrollment (Stream D)
- **Fixed Price**: One-time or installments (not monthly recurring).
- **Seat Caps**: Max 50 students per cohort.
- **Entitlements**: Grants access to specific tiers/tracks for a fixed duration (e.g., 12 weeks).

---

## 🛡️ Part 6: Developer Standards

1.  **Security**: PCI-DSS compliance (No card data in DB!). Use Paystack tokens.
2.  **Privacy**: Every data access check is gated by a `purpose_key` in the **CPPC**.
3.  **Audit**: Every write on `Account`, `Portfolio`, or `Billing` is audited in the **A&O** layer.
4.  **Idempotency**: All webhook handlers (Paystack) must be idempotent to prevent double-billing.

---

**Master Implementation Score: ~80%**
The platform is exceptionally high-fidelity. The "Heavy Lifting" (Identity, PCM, Missions, Profiler, and Core Billing) is done. 
**Current focus**: Finalizing Analytics (T9) and advanced Marketplace automation.
