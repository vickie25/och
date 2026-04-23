"""
Cohort financial policy: one-time fees, enrollment windows, and capacity checks.

Single place for payment initiation and public pricing so we never silently fall
back to hard-coded defaults.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from decimal import Decimal
from typing import TYPE_CHECKING, Optional, Tuple

from django.utils import timezone

if TYPE_CHECKING:
    from programs.models import Cohort


@dataclass(frozen=True)
class CohortFeeBreakdown:
    list_price: Decimal
    source: str  # cohort_enrollment_fee | program_default


def get_effective_cohort_enrollment_fee(cohort: "Cohort") -> CohortFeeBreakdown:
    """
    Canonical one-time list price for paid cohort seats.
    Prefers `cohort.enrollment_fee` when set > 0; otherwise uses the program's default_price.
    """
    fee = getattr(cohort, "enrollment_fee", None)
    if fee is not None and fee > 0:
        return CohortFeeBreakdown(list_price=Decimal(fee), source="cohort_enrollment_fee")
    if cohort.track and cohort.track.program:
        default_p = cohort.track.program.default_price or Decimal("0")
        if default_p > 0:
            return CohortFeeBreakdown(list_price=Decimal(default_p), source="program_default")
    return CohortFeeBreakdown(list_price=Decimal("0"), source="cohort_enrollment_fee")


def enrollment_window_status(
    cohort: "Cohort", now: Optional[datetime] = None
) -> Tuple[bool, str]:
    """
    Returns (allowed, message). When window fields are null, enrollment is open from
    "ever" until the cohort start date (date boundary, end-inclusive through day before start).
    """
    now = now or timezone.now()
    opens = getattr(cohort, "enrollment_opens_at", None)
    closes = getattr(cohort, "enrollment_closes_at", None)

    if opens and now < opens:
        return False, "Enrollment has not opened yet for this cohort."

    if closes and now > closes:
        return False, "The enrollment period for this cohort has closed."

    # Block new enrollments after cohort has started (same calendar day still allowed)
    start = cohort.start_date
    if start:
        today = timezone.localdate()
        if today > start:
            return False, "This cohort has already started; enrollment is closed."

    return True, "ok"


def assert_seat_available_for_enrollment(cohort: "Cohort") -> Tuple[bool, str]:
    """Enforce capacity (aligned with `EnhancedCohortService.get_available_seats`)."""
    count = cohort.enrollments.filter(status__in=["active", "pending_payment"]).count()
    if count >= cohort.seat_cap:
        return False, "This cohort is full; no seats available."
    return True, "ok"
