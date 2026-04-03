"""
Certificate Eligibility Service
Checks all requirements before certificate generation:
- Course/cohort completion
- No pending payments
- Full competency/eligibility
"""
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from django.db.models import Sum, Q
import logging

logger = logging.getLogger(__name__)


class CertificateEligibilityService:
    """
    Service to check certificate eligibility requirements.
    
    Requirements for certificate generation:
    1. Course/cohort completion - enrollment status must be 'completed'
    2. No pending payments - all invoices must be paid
    3. Full competency - all required competencies assessed and passed
    4. Minimum attendance/participation requirements met
    """
    
    @classmethod
    def check_eligibility(cls, enrollment) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if an enrollment is eligible for certificate generation.
        
        Returns:
            Tuple of (is_eligible, details_dict)
        """
        checks = {
            'completion': cls._check_completion(enrollment),
            'payments': cls._check_payments(enrollment),
            'competency': cls._check_competency(enrollment),
            'attendance': cls._check_attendance(enrollment),
            'missions': cls._check_missions(enrollment),
        }
        
        # All checks must pass
        is_eligible = all(check['passed'] for check in checks.values())
        
        details = {
            'is_eligible': is_eligible,
            'checks': checks,
            'summary': cls._generate_summary(checks),
        }
        
        return is_eligible, details
    
    @classmethod
    def _check_completion(cls, enrollment) -> Dict[str, Any]:
        """Check if course/cohort is completed."""
        status = enrollment.status
        completed_at = enrollment.completed_at
        
        passed = status == 'completed' and completed_at is not None
        
        return {
            'name': 'Course/Cohort Completion',
            'passed': passed,
            'required': True,
            'status': status,
            'completed_at': completed_at.isoformat() if completed_at else None,
            'message': 'Course completed successfully' if passed else f'Course not completed (status: {status})',
        }
    
    @classmethod
    def _check_payments(cls, enrollment) -> Dict[str, Any]:
        """Check if all payments are completed - no pending amounts."""
        user = enrollment.user
        track_key = getattr(enrollment, "track_key", None) or getattr(getattr(getattr(enrollment, "cohort", None), "track", None), "key", None)

        # Foundations (Tier 1 / L0) is free by design: do not block certificates on payments/invoices.
        if str(track_key or "").upper() in {"L0", "FOUNDATION", "FOUNDATIONS"}:
            return {
                "name": "Payment Status",
                "passed": True,
                "required": False,
                "message": "Foundations is free (payment not required)",
            }

        # Fast-path: enrollment-level payment status (kept for backwards compatibility)
        enrollment_paid = getattr(enrollment, "payment_status", None) in {"paid", "waived"}

        # Finance invoice check (authoritative in this codebase)
        try:
            from finance.models import Invoice as FinanceInvoice

            unpaid = FinanceInvoice.objects.filter(
                user=user,
                status__in=["draft", "sent", "overdue"],
            )
            unpaid_count = unpaid.count()
            passed = unpaid_count == 0 and enrollment_paid

            return {
                "name": "Payment Status",
                "passed": passed,
                "required": True,
                "unpaid_invoices_count": unpaid_count,
                "enrollment_payment_status": getattr(enrollment, "payment_status", None),
                "message": "All payments completed" if passed else "Pending payments detected",
            }
        except Exception as e:
            logger.warning("Payment check failed; falling back to enrollment.payment_status: %s", e)
            return {
                "name": "Payment Status",
                "passed": bool(enrollment_paid),
                "required": True,
                "enrollment_payment_status": getattr(enrollment, "payment_status", None),
                "message": "Payment status derived from enrollment.payment_status only",
            }
    
    @classmethod
    def _check_competency(cls, enrollment) -> Dict[str, Any]:
        """Check if all required competencies are assessed and passed."""
        track = enrollment.cohort.track
        
        # Get required competencies for the track
        try:
            from competency.models import CompetencyAssessment, Competency
            
            required_competencies = Competency.objects.filter(
                track=track,
                is_required=True
            )
            
            total_required = required_competencies.count()
            
            if total_required == 0:
                return {
                    'name': 'Competency Assessment',
                    'passed': True,
                    'required': False,
                    'message': 'No competency requirements for this track',
                }
            
            # Get user's assessments
            assessments = CompetencyAssessment.objects.filter(
                user=enrollment.user,
                competency__in=required_competencies
            )
            
            passed_assessments = assessments.filter(status='passed').count()
            failed_assessments = assessments.filter(status='failed').count()
            missing_assessments = total_required - assessments.count()
            
            passed = passed_assessments >= total_required
            
            return {
                'name': 'Competency Assessment',
                'passed': passed,
                'required': True,
                'total_required': total_required,
                'passed_count': passed_assessments,
                'failed_count': failed_assessments,
                'missing_count': missing_assessments,
                'message': f'{passed_assessments}/{total_required} competencies passed' if passed else f'Missing {missing_assessments} assessments, {failed_assessments} failed',
            }
        except ImportError:
            # If competency module not available, check grade
            grade = enrollment.grade
            passed = grade is not None and grade in ['A', 'B', 'C', 'Pass', 'pass']
            
            return {
                'name': 'Competency/Grade Check',
                'passed': passed,
                'required': True,
                'grade': grade,
                'message': f'Grade: {grade}' if grade else 'No grade recorded',
            }
    
    @classmethod
    def _check_attendance(cls, enrollment) -> Dict[str, Any]:
        """Check minimum attendance requirements."""
        try:
            from attendance.models import AttendanceRecord
            
            # Get attendance records for this enrollment
            attendance_records = AttendanceRecord.objects.filter(
                enrollment=enrollment
            )
            
            total_sessions = attendance_records.count()
            attended_sessions = attendance_records.filter(status='present').count()
            
            if total_sessions == 0:
                return {
                    'name': 'Attendance',
                    'passed': True,
                    'required': False,
                    'message': 'No attendance records required',
                }
            
            attendance_rate = (attended_sessions / total_sessions * 100) if total_sessions > 0 else 0
            min_required_rate = 75  # 75% attendance required
            
            passed = attendance_rate >= min_required_rate
            
            return {
                'name': 'Attendance',
                'passed': passed,
                'required': True,
                'attendance_rate': round(attendance_rate, 2),
                'attended_sessions': attended_sessions,
                'total_sessions': total_sessions,
                'min_required': min_required_rate,
                'message': f'{attendance_rate:.1f}% attendance (min: {min_required_rate}%)',
            }
        except ImportError:
            return {
                'name': 'Attendance',
                'passed': True,
                'required': False,
                'message': 'Attendance check skipped - module not available',
            }
    
    @classmethod
    def _check_missions(cls, enrollment) -> Dict[str, Any]:
        """Check if required missions are completed."""
        try:
            from missions.models_mxp import MissionProgress
        except Exception as e:
            logger.warning("MissionProgress unavailable; cannot enforce mission completion: %s", e)
            return {
                "name": "Mission Completion",
                "passed": False,
                "required": True,
                "message": "Mission progress system not available",
            }

        track = getattr(getattr(enrollment, "cohort", None), "track", None)
        mission_ids = getattr(track, "missions", None) if track else None
        mission_ids = mission_ids if isinstance(mission_ids, list) else []

        total_required = len(mission_ids)
        if total_required == 0:
            return {
                "name": "Mission Completion",
                "passed": True,
                "required": False,
                "message": "No required missions configured for this track",
            }

        # MissionProgress.user FK targets users.uuid_id in this codebase; filter by uuid_id explicitly.
        user_uuid = getattr(enrollment.user, "uuid_id", None)
        if not user_uuid:
            return {
                "name": "Mission Completion",
                "passed": False,
                "required": True,
                "message": "User uuid_id missing; cannot check mission progress",
            }

        completed_count = (
            MissionProgress.objects.filter(
                user_id=user_uuid,
                mission_id__in=mission_ids,
            )
            .filter(Q(status="approved") | Q(final_status="pass"))
            .values("mission_id")
            .distinct()
            .count()
        )

        passed = completed_count >= total_required
        return {
            "name": "Mission Completion",
            "passed": passed,
            "required": True,
            "completed": completed_count,
            "total_required": total_required,
            "message": f"{completed_count}/{total_required} missions completed",
        }
    
    @classmethod
    def _generate_summary(cls, checks: Dict[str, Any]) -> str:
        """Generate human-readable summary of eligibility checks."""
        passed = [name for name, check in checks.items() if check['passed']]
        failed = [name for name, check in checks.items() if not check['passed']]
        
        if not failed:
            return "All eligibility requirements met. Certificate can be generated."
        
        failed_names = [checks[name]['name'] for name in failed]
        return f"Cannot generate certificate. Failed requirements: {', '.join(failed_names)}"


# Convenience function
def check_certificate_eligibility(enrollment) -> Tuple[bool, Dict[str, Any]]:
    """Check if enrollment is eligible for certificate generation."""
    return CertificateEligibilityService.check_eligibility(enrollment)
