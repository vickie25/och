"""
Employer Contract Services
Business logic for contract lifecycle, SLA management, and performance tracking
"""
import uuid
from decimal import Decimal
from datetime import datetime, timedelta, date
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Avg, Count, Sum
from django.core.exceptions import ValidationError
from .employer_contracts import (
    EmployerContract, EmployerContractTier, CandidateRequirement,
    CandidatePresentation, SuccessfulPlacement, ContractPerformanceMetrics,
    ReplacementGuarantee
)
from users.models import User


class ContractLifecycleService:
    """Manages employer contract lifecycle stages."""
    
    @staticmethod
    def create_contract_proposal(organization, tier_name, start_date, end_date, 
                               created_by, **custom_terms):
        """Create new contract proposal."""
        tier = EmployerContractTier.objects.get(tier_name=tier_name, is_active=True)
        
        contract = EmployerContract.objects.create(
            organization=organization,
            tier=tier,
            contract_number=EmployerContract.generate_contract_number(),
            status='proposal',
            start_date=start_date,
            end_date=end_date,
            monthly_retainer=tier.monthly_retainer,
            placement_fee=tier.placement_fee,
            candidates_per_quarter=tier.candidates_per_quarter,
            replacement_guarantee_days=90 if tier_name == 'enterprise' else 60,
            created_by=created_by,
            special_terms=custom_terms
        )
        
        # Assign account manager for Growth/Enterprise tiers
        if tier_name in ['growth', 'enterprise']:
            # Logic to assign available account manager
            pass
        
        return contract
    
    @staticmethod
    def transition_contract_status(contract, new_status, user=None, notes=None):
        """Safely transition contract to new status."""
        valid_transitions = {
            'proposal': ['negotiation', 'terminated'],
            'negotiation': ['proposal', 'signed', 'terminated'],
            'signed': ['active', 'terminated'],
            'active': ['renewal', 'terminated', 'suspended'],
            'renewal': ['active', 'terminated'],
            'suspended': ['active', 'terminated'],
            'terminated': []  # Terminal state
        }
        
        if new_status not in valid_transitions.get(contract.status, []):
            raise ValidationError(f"Cannot transition from {contract.status} to {new_status}")
        
        old_status = contract.status
        contract.status = new_status
        
        # Set status-specific timestamps
        if new_status == 'signed':
            contract.signed_at = timezone.now()
        elif new_status == 'active':
            contract.activated_at = timezone.now()
            # Set performance review date
            contract.performance_review_due = contract.end_date
        elif new_status == 'terminated':
            contract.terminated_at = timezone.now()
        
        contract.save()
        
        # Log status change
        if notes:
            contract.internal_notes += f"\n{timezone.now()}: {old_status} -> {new_status} by {user}: {notes}"
            contract.save()
        
        return contract
    
    @staticmethod
    def check_renewal_eligibility(contract):
        """Check if contract is eligible for renewal."""
        if contract.status != 'active':
            return False, "Contract must be active for renewal"
        
        days_to_end = (contract.end_date - timezone.now().date()).days
        if days_to_end > contract.renewal_notice_days:
            return False, f"Renewal notice period not reached ({days_to_end} days remaining)"
        
        return True, "Contract eligible for renewal"
    
    @staticmethod
    def calculate_renewal_pricing(contract):
        """Calculate renewal pricing based on performance."""
        # Get latest performance metrics
        latest_metrics = ContractPerformanceMetrics.objects.filter(
            contract=contract
        ).order_by('-period_end').first()
        
        base_retainer = contract.tier.monthly_retainer
        base_placement_fee = contract.tier.placement_fee
        
        if not latest_metrics:
            return {
                'monthly_retainer': base_retainer,
                'placement_fee': base_placement_fee,
                'discount_applied': False,
                'discount_reason': None
            }
        
        # Apply performance-based discount
        if latest_metrics.placement_success_rate >= 90:
            discount_rate = Decimal('0.10')  # 10% discount
            discounted_retainer = base_retainer * (1 - discount_rate)
            return {
                'monthly_retainer': discounted_retainer,
                'placement_fee': base_placement_fee,
                'discount_applied': True,
                'discount_reason': f'High performance discount ({latest_metrics.placement_success_rate}% success rate)',
                'discount_amount': base_retainer - discounted_retainer
            }
        
        return {
            'monthly_retainer': base_retainer,
            'placement_fee': base_placement_fee,
            'discount_applied': False,
            'discount_reason': None
        }


class CandidateMatchingService:
    """Handles candidate matching and presentation logic."""
    
    @staticmethod
    def find_matching_candidates(requirement, limit=10):
        """Find candidates matching requirement criteria."""
        from marketplace.models import MarketplaceProfile
        
        # Base query for eligible candidates
        candidates = MarketplaceProfile.objects.filter(
            is_visible=True,
            employer_share_consent=True,
            profile_status__in=['emerging_talent', 'job_ready']
        ).select_related('mentee')
        
        # Filter by tier access (premium contracts get all tiers)
        if requirement.contract.tier.tier_name != 'enterprise':
            candidates = candidates.filter(
                tier__in=['starter', 'professional']  # Exclude free tier for paid contracts
            )
        
        # Filter by minimum tier level
        if requirement.minimum_tier_level:
            # Add tier level filtering logic based on curriculum progress
            pass
        
        # Filter by required tracks
        if requirement.required_tracks:
            candidates = candidates.filter(
                primary_track_key__in=requirement.required_tracks
            )
        
        # Filter by skills (basic keyword matching)
        if requirement.required_skills:
            for skill in requirement.required_skills:
                candidates = candidates.filter(
                    skills__icontains=skill
                )
        
        # Order by match score (would be calculated by ML algorithm)
        candidates = candidates.order_by('-readiness_score', '-job_fit_score')
        
        return candidates[:limit]
    
    @staticmethod
    def present_candidates_to_employer(requirement, candidates, presented_by):
        """Present candidates to employer with proper tracking."""
        presentations = []
        
        with transaction.atomic():
            for candidate_profile in candidates:
                # Check if candidate already presented for this requirement
                if CandidatePresentation.objects.filter(
                    requirement=requirement,
                    candidate=candidate_profile.mentee
                ).exists():
                    continue
                
                # Calculate match score (simplified)
                match_score = CandidateMatchingService._calculate_match_score(
                    requirement, candidate_profile
                )
                
                # Create presentation record
                presentation = CandidatePresentation.objects.create(
                    contract=requirement.contract,
                    requirement=requirement,
                    candidate=candidate_profile.mentee,
                    match_score=match_score,
                    quality_score=candidate_profile.readiness_score or 75,
                    mission_completion_score=70,  # Would come from missions data
                    is_exclusive=requirement.contract.has_exclusivity,
                    exclusivity_expires_at=(
                        timezone.now() + timedelta(hours=requirement.contract.exclusivity_window_hours)
                        if requirement.contract.has_exclusivity else None
                    )
                )
                presentations.append(presentation)
            
            # Update requirement status and SLA tracking
            if presentations and not requirement.first_shortlist_sent_at:
                requirement.first_shortlist_sent_at = timezone.now()
                requirement.sla_met = timezone.now() <= requirement.shortlist_due_at
                requirement.status = 'shortlisted'
                requirement.save()
        
        return presentations
    
    @staticmethod
    def _calculate_match_score(requirement, candidate_profile):
        """Calculate candidate match score for requirement."""
        score = Decimal('0.0')
        
        # Base score from readiness
        if candidate_profile.readiness_score:
            score += candidate_profile.readiness_score * Decimal('0.4')
        
        # Job fit score
        if candidate_profile.job_fit_score:
            score += candidate_profile.job_fit_score * Decimal('0.3')
        
        # Skills matching (simplified)
        if requirement.required_skills and candidate_profile.skills:
            matched_skills = len(set(requirement.required_skills) & set(candidate_profile.skills))
            total_required = len(requirement.required_skills)
            if total_required > 0:
                skills_score = (matched_skills / total_required) * 30
                score += Decimal(str(skills_score))
        
        return min(score, Decimal('100.0'))


class SLAMonitoringService:
    """Monitors and tracks SLA compliance."""
    
    @staticmethod
    def check_overdue_requirements():
        """Find requirements that are overdue for shortlisting."""
        overdue = CandidateRequirement.objects.filter(
            status='open',
            first_shortlist_sent_at__isnull=True,
            shortlist_due_at__lt=timezone.now()
        ).select_related('contract')
        
        return overdue
    
    @staticmethod
    def calculate_sla_compliance_rate(contract, period_start=None, period_end=None):
        """Calculate SLA compliance rate for contract."""
        if not period_start:
            period_start = contract.start_date
        if not period_end:
            period_end = timezone.now().date()
        
        requirements = CandidateRequirement.objects.filter(
            contract=contract,
            submitted_at__date__range=[period_start, period_end]
        )
        
        total_requirements = requirements.count()
        if total_requirements == 0:
            return None
        
        met_sla = requirements.filter(sla_met=True).count()
        return (met_sla / total_requirements) * 100
    
    @staticmethod
    def send_sla_alerts():
        """Send alerts for SLA violations."""
        overdue = SLAMonitoringService.check_overdue_requirements()
        
        alerts = []
        for requirement in overdue:
            hours_overdue = (timezone.now() - requirement.shortlist_due_at).total_seconds() / 3600
            
            alert = {
                'requirement_id': requirement.id,
                'contract': requirement.contract.contract_number,
                'employer': requirement.contract.organization.name,
                'title': requirement.title,
                'hours_overdue': round(hours_overdue, 1),
                'priority': requirement.priority
            }
            alerts.append(alert)
        
        return alerts


class PlacementFeeService:
    """Handles placement fee calculations and billing."""
    
    @staticmethod
    def record_successful_placement(presentation, start_date, salary_offered=None):
        """Record successful candidate placement."""
        contract = presentation.contract
        
        # Calculate placement fee
        placement_fee = contract.placement_fee
        
        # Calculate guarantee end date
        guarantee_end = start_date + timedelta(days=contract.replacement_guarantee_days)
        
        placement = SuccessfulPlacement.objects.create(
            presentation=presentation,
            start_date=start_date,
            salary_offered=salary_offered,
            placement_fee=placement_fee,
            guarantee_end_date=guarantee_end
        )
        
        # Update presentation status
        presentation.status = 'hired'
        presentation.decision_at = timezone.now()
        presentation.save()
        
        # Update requirement
        requirement = presentation.requirement
        requirement.positions_filled += 1
        if requirement.positions_filled >= requirement.positions_count:
            requirement.status = 'filled'
        requirement.save()
        
        return placement
    
    @staticmethod
    def calculate_monthly_placement_fees(contract, month_start):
        """Calculate placement fees for a given month."""
        month_end = month_start + timedelta(days=32)
        month_end = month_end.replace(day=1) - timedelta(days=1)  # Last day of month
        
        placements = SuccessfulPlacement.objects.filter(
            presentation__contract=contract,
            start_date__range=[month_start, month_end],
            status__in=['placed', 'confirmed', 'fee_billed', 'fee_paid']
        )
        
        total_fees = sum(p.placement_fee for p in placements)
        fee_cap = contract.get_monthly_placement_fee_cap()
        
        return {
            'placements_count': placements.count(),
            'total_fees': total_fees,
            'fee_cap': fee_cap,
            'capped_fees': min(total_fees, fee_cap),
            'cap_applied': total_fees > fee_cap,
            'placements': list(placements)
        }
    
    @staticmethod
    def generate_placement_fee_invoice(contract, month_start):
        """Generate invoice for placement fees."""
        fee_data = PlacementFeeService.calculate_monthly_placement_fees(contract, month_start)
        
        if fee_data['capped_fees'] == 0:
            return None
        
        # Create invoice (would integrate with finance system)
        invoice_data = {
            'contract': contract,
            'month': month_start,
            'placements_count': fee_data['placements_count'],
            'total_amount': fee_data['capped_fees'],
            'line_items': [
                {
                    'description': f'Placement fees for {month_start.strftime("%B %Y")}',
                    'quantity': fee_data['placements_count'],
                    'unit_price': float(fee_data['capped_fees'] / fee_data['placements_count']),
                    'total': float(fee_data['capped_fees'])
                }
            ]
        }
        
        return invoice_data


class PerformanceTrackingService:
    """Tracks and analyzes contract performance metrics."""
    
    @staticmethod
    def calculate_performance_metrics(contract, period_start, period_end):
        """Calculate comprehensive performance metrics for contract."""
        
        # Get all presentations in period
        presentations = CandidatePresentation.objects.filter(
            contract=contract,
            presented_at__date__range=[period_start, period_end]
        )
        
        # Get all requirements in period
        requirements = CandidateRequirement.objects.filter(
            contract=contract,
            submitted_at__date__range=[period_start, period_end]
        )
        
        # Calculate basic metrics
        candidates_presented = presentations.count()
        candidates_shortlisted = presentations.filter(status__in=['shortlisted', 'interviewed', 'hired']).count()
        candidates_interviewed = presentations.filter(status__in=['interviewed', 'hired']).count()
        candidates_hired = presentations.filter(status='hired').count()
        
        # Calculate rates
        placement_success_rate = (candidates_hired / candidates_presented * 100) if candidates_presented > 0 else 0
        shortlist_conversion_rate = (candidates_shortlisted / candidates_presented * 100) if candidates_presented > 0 else 0
        interview_conversion_rate = (candidates_interviewed / candidates_shortlisted * 100) if candidates_shortlisted > 0 else 0
        hire_conversion_rate = (candidates_hired / candidates_interviewed * 100) if candidates_interviewed > 0 else 0
        
        # SLA metrics
        sla_compliance_rate = SLAMonitoringService.calculate_sla_compliance_rate(
            contract, period_start, period_end
        ) or 0
        
        # Calculate average time to shortlist
        avg_time_to_shortlist = None
        shortlisted_reqs = requirements.filter(first_shortlist_sent_at__isnull=False)
        if shortlisted_reqs.exists():
            total_days = sum([
                (req.first_shortlist_sent_at.date() - req.submitted_at.date()).days
                for req in shortlisted_reqs
            ])
            avg_time_to_shortlist = total_days / shortlisted_reqs.count()
        
        # Financial metrics
        months_in_period = (period_end - period_start).days / 30.44  # Average days per month
        total_retainer_paid = contract.get_effective_monthly_retainer() * Decimal(str(months_in_period))
        
        placements = SuccessfulPlacement.objects.filter(
            presentation__contract=contract,
            start_date__range=[period_start, period_end]
        )
        total_placement_fees = sum(p.placement_fee for p in placements)
        
        # Quality metrics
        avg_quality_score = presentations.aggregate(avg=Avg('quality_score'))['avg']
        avg_employer_rating = presentations.filter(
            employer_rating__isnull=False
        ).aggregate(avg=Avg('employer_rating'))['avg']
        
        # Guarantee metrics
        placements_within_guarantee = placements.count()
        guarantee_claims = ReplacementGuarantee.objects.filter(
            original_placement__presentation__contract=contract,
            claimed_at__date__range=[period_start, period_end]
        ).count()
        
        # Determine performance grade
        performance_grade = PerformanceTrackingService._calculate_performance_grade(placement_success_rate)
        
        # Create or update metrics record
        metrics, created = ContractPerformanceMetrics.objects.update_or_create(
            contract=contract,
            period_start=period_start,
            period_end=period_end,
            defaults={
                'candidates_presented': candidates_presented,
                'candidates_shortlisted': candidates_shortlisted,
                'candidates_interviewed': candidates_interviewed,
                'candidates_hired': candidates_hired,
                'placement_success_rate': Decimal(str(placement_success_rate)),
                'shortlist_conversion_rate': Decimal(str(shortlist_conversion_rate)),
                'interview_conversion_rate': Decimal(str(interview_conversion_rate)),
                'hire_conversion_rate': Decimal(str(hire_conversion_rate)),
                'avg_time_to_shortlist': Decimal(str(avg_time_to_shortlist)) if avg_time_to_shortlist else None,
                'sla_compliance_rate': Decimal(str(sla_compliance_rate)),
                'total_retainer_paid': total_retainer_paid,
                'total_placement_fees': total_placement_fees,
                'total_contract_value': total_retainer_paid + total_placement_fees,
                'avg_candidate_quality_score': Decimal(str(avg_quality_score)) if avg_quality_score else None,
                'avg_employer_rating': Decimal(str(avg_employer_rating)) if avg_employer_rating else None,
                'placements_within_guarantee': placements_within_guarantee,
                'guarantee_claims': guarantee_claims,
                'performance_grade': performance_grade,
                'discount_eligible': placement_success_rate >= 90,
                'requires_improvement_plan': placement_success_rate < 60
            }
        )
        
        return metrics
    
    @staticmethod
    def _calculate_performance_grade(success_rate):
        """Calculate performance grade based on success rate."""
        if success_rate >= 90:
            return 'A+'
        elif success_rate >= 80:
            return 'A'
        elif success_rate >= 70:
            return 'B'
        elif success_rate >= 60:
            return 'C'
        elif success_rate >= 50:
            return 'D'
        else:
            return 'F'


class ReplacementGuaranteeService:
    """Manages replacement guarantee claims and fulfillment."""
    
    @staticmethod
    def claim_replacement_guarantee(placement, claim_reason, candidate_left_date):
        """Process replacement guarantee claim."""
        if not placement.is_guarantee_active():
            raise ValidationError("Replacement guarantee period has expired")
        
        days_employed = (candidate_left_date - placement.start_date).days
        replacement_due = timezone.now().date() + timedelta(days=10)  # 10 business days
        
        guarantee = ReplacementGuarantee.objects.create(
            original_placement=placement,
            claim_reason=claim_reason,
            candidate_left_date=candidate_left_date,
            days_employed=days_employed,
            replacement_due_date=replacement_due
        )
        
        # Update placement record
        placement.candidate_left_date = candidate_left_date
        placement.left_within_guarantee = True
        placement.guarantee_used = True
        placement.save()
        
        return guarantee
    
    @staticmethod
    def fulfill_replacement_guarantee(guarantee, replacement_candidates):
        """Fulfill replacement guarantee with new candidates."""
        guarantee.replacement_candidates_provided = len(replacement_candidates)
        guarantee.status = 'presented'
        guarantee.save()
        
        # Present replacement candidates
        presentations = CandidateMatchingService.present_candidates_to_employer(
            guarantee.original_placement.presentation.requirement,
            replacement_candidates,
            guarantee.assigned_to
        )
        
        return presentations
    
    @staticmethod
    def check_overdue_guarantees():
        """Find overdue replacement guarantees."""
        return ReplacementGuarantee.objects.filter(
            status__in=['claimed', 'approved', 'sourcing'],
            replacement_due_date__lt=timezone.now().date()
        )