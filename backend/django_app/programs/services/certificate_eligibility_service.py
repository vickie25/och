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
        cohort = enrollment.cohort
        
        # Check for pending invoices
        try:
            from billing.models import Invoice
            pending_invoices = Invoice.objects.filter(
                user=user,
                status__in=['pending', 'overdue', 'partial'],
                items__cohort=cohort
            ).distinct()
            
            pending_amount = pending_invoices.aggregate(
                total=Sum('balance_due')
            )['total'] or 0
            
            passed = pending_amount == 0
            
            return {
                'name': 'Payment Status',
                'passed': passed,
                'required': True,
                'pending_amount': float(pending_amount),
                'pending_invoices_count': pending_invoices.count(),
                'message': 'All payments completed' if passed else f'Pending amount: {pending_amount}',
            }
        except ImportError:
            # If billing module not available, assume payments are OK
            return {
                'name': 'Payment Status',
                'passed': True,
                'required': False,
                'message': 'Payment check skipped - billing module not available',
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
            from missions.models import Mission, MissionSubmission
            
            cohort = enrollment.cohort
            track = cohort.track
            
            # Get required missions for this track/cohort
            required_missions = Mission.objects.filter(
                Q(track=track) | Q(cohort=cohort),
                is_required=True
            )
            
            total_required = required_missions.count()
            
            if total_required == 0:
                return {
                    'name': 'Mission Completion',
                    'passed': True,
                    'required': False,
                    'message': 'No required missions for this track',
                }
            
            # Get completed missions
            completed_missions = MissionSubmission.objects.filter(
                user=enrollment.user,
                mission__in=required_missions,
                status='completed'
            ).values('mission').distinct().count()
            
            passed = completed_missions >= total_required
            
            return {
                'name': 'Mission Completion',
                'passed': passed,
                'required': True,
                'completed': completed_missions,
                'total_required': total_required,
                'message': f'{completed_missions}/{total_required} missions completed',
            }
        except ImportError:
            return {
                'name': 'Mission Completion',
                'passed': True,
                'required': False,
                'message': 'Mission check skipped - module not available',
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
