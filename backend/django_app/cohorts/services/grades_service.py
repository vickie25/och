"""
Grades Service - Calculate and manage cohort grades.
"""
from django.db.models import Avg, Count, Q
from decimal import Decimal
from cohorts.models import CohortGrade, CohortExamSubmission
from programs.models import Enrollment
from missions.models_mxp import MissionProgress


class GradesService:
    """Service for managing cohort grades."""
    
    @staticmethod
    def get_or_create_grade(enrollment_id):
        """
        Get or create grade record for enrollment.
        
        Args:
            enrollment_id: Enrollment UUID
        
        Returns:
            CohortGrade instance
        """
        grade, created = CohortGrade.objects.get_or_create(
            enrollment_id=enrollment_id,
            defaults={
                'missions_score': 0,
                'capstones_score': 0,
                'labs_score': 0,
                'exams_score': 0,
                'participation_score': 0,
                'overall_score': 0
            }
        )
        return grade
    
    @staticmethod
    def calculate_missions_score(enrollment):
        """
        Calculate missions score for student.
        
        Args:
            enrollment: Enrollment instance
        
        Returns:
            Decimal score (0-100)
        """
        # Get all mission progress for student
        missions = MissionProgress.objects.filter(
            user=enrollment.user,
            status__in=['completed', 'approved']
        )
        
        if not missions.exists():
            return Decimal('0.00')
        
        # Calculate average score
        total_score = 0
        count = 0
        
        for mission in missions:
            if mission.mentor_score:
                total_score += float(mission.mentor_score)
                count += 1
        
        if count == 0:
            return Decimal('0.00')
        
        avg_score = total_score / count
        return Decimal(str(round(avg_score, 2)))
    
    @staticmethod
    def calculate_capstones_score(enrollment):
        """
        Calculate capstones score for student.
        
        Args:
            enrollment: Enrollment instance
        
        Returns:
            Decimal score (0-100)
        """
        # Get capstone missions (missions with mission_type='capstone')
        capstones = MissionProgress.objects.filter(
            user=enrollment.user,
            mission__mission_type='capstone',
            status__in=['completed', 'approved']
        )
        
        if not capstones.exists():
            return Decimal('0.00')
        
        total_score = 0
        count = 0
        
        for capstone in capstones:
            if capstone.mentor_score:
                total_score += float(capstone.mentor_score)
                count += 1
        
        if count == 0:
            return Decimal('0.00')
        
        avg_score = total_score / count
        return Decimal(str(round(avg_score, 2)))
    
    @staticmethod
    def calculate_labs_score(enrollment):
        """
        Calculate practice labs score for student.
        
        Args:
            enrollment: Enrollment instance
        
        Returns:
            Decimal score (0-100)
        """
        # Get lab missions (missions with mission_type='lab')
        labs = MissionProgress.objects.filter(
            user=enrollment.user,
            mission__mission_type='lab',
            status__in=['completed', 'approved']
        )
        
        if not labs.exists():
            return Decimal('0.00')
        
        total_score = 0
        count = 0
        
        for lab in labs:
            if lab.mentor_score:
                total_score += float(lab.mentor_score)
                count += 1
        
        if count == 0:
            return Decimal('0.00')
        
        avg_score = total_score / count
        return Decimal(str(round(avg_score, 2)))
    
    @staticmethod
    def calculate_exams_score(enrollment):
        """
        Calculate exams score for student.
        
        Args:
            enrollment: Enrollment instance
        
        Returns:
            Decimal score (0-100)
        """
        exams = CohortExamSubmission.objects.filter(
            enrollment=enrollment,
            status='graded'
        )
        
        if not exams.exists():
            return Decimal('0.00')
        
        avg_score = exams.aggregate(avg=Avg('score'))['avg']
        return Decimal(str(round(avg_score, 2))) if avg_score else Decimal('0.00')
    
    @staticmethod
    def calculate_participation_score(enrollment):
        """
        Calculate participation score based on attendance and engagement.
        
        Args:
            enrollment: Enrollment instance
        
        Returns:
            Decimal score (0-100)
        """
        # This is a placeholder - implement based on your attendance tracking
        # For now, return a default score
        return Decimal('80.00')
    
    @staticmethod
    def recalculate_grade(enrollment_id):
        """
        Recalculate all grade components for a student.
        
        Args:
            enrollment_id: Enrollment UUID
        
        Returns:
            CohortGrade instance with updated scores
        """
        enrollment = Enrollment.objects.get(id=enrollment_id)
        grade = GradesService.get_or_create_grade(enrollment_id)
        
        # Calculate each component
        grade.missions_score = GradesService.calculate_missions_score(enrollment)
        grade.capstones_score = GradesService.calculate_capstones_score(enrollment)
        grade.labs_score = GradesService.calculate_labs_score(enrollment)
        grade.exams_score = GradesService.calculate_exams_score(enrollment)
        grade.participation_score = GradesService.calculate_participation_score(enrollment)
        
        # Calculate overall score
        grade.calculate_overall()
        
        return grade
    
    @staticmethod
    def get_cohort_rankings(cohort_id):
        """
        Get rankings for all students in a cohort.
        
        Args:
            cohort_id: Cohort UUID
        
        Returns:
            list of dicts with student rankings
        """
        enrollments = Enrollment.objects.filter(
            cohort_id=cohort_id,
            status='active'
        ).select_related('user')
        
        rankings = []
        
        for enrollment in enrollments:
            grade = GradesService.get_or_create_grade(enrollment.id)
            rankings.append({
                'enrollment_id': str(enrollment.id),
                'user_id': str(enrollment.user.id),
                'user_email': enrollment.user.email,
                'user_name': f"{enrollment.user.first_name} {enrollment.user.last_name}",
                'overall_score': float(grade.overall_score),
                'letter_grade': grade.letter_grade,
                'missions_score': float(grade.missions_score),
                'capstones_score': float(grade.capstones_score),
                'labs_score': float(grade.labs_score),
                'exams_score': float(grade.exams_score),
                'participation_score': float(grade.participation_score),
            })
        
        # Sort by overall score descending
        rankings.sort(key=lambda x: x['overall_score'], reverse=True)
        
        # Assign ranks
        for i, ranking in enumerate(rankings, 1):
            ranking['rank'] = i
            # Update rank in database
            grade = CohortGrade.objects.get(enrollment_id=ranking['enrollment_id'])
            grade.rank = i
            grade.save(update_fields=['rank'])
        
        return rankings
    
    @staticmethod
    def get_grade_breakdown(enrollment_id):
        """
        Get detailed grade breakdown for a student.
        
        Args:
            enrollment_id: Enrollment UUID
        
        Returns:
            dict with detailed breakdown
        """
        grade = GradesService.get_or_create_grade(enrollment_id)
        enrollment = Enrollment.objects.get(id=enrollment_id)
        
        # Get component details
        missions_count = MissionProgress.objects.filter(
            user=enrollment.user,
            status__in=['completed', 'approved']
        ).count()
        
        capstones_count = MissionProgress.objects.filter(
            user=enrollment.user,
            mission__mission_type='capstone',
            status__in=['completed', 'approved']
        ).count()
        
        labs_count = MissionProgress.objects.filter(
            user=enrollment.user,
            mission__mission_type='lab',
            status__in=['completed', 'approved']
        ).count()
        
        exams_count = CohortExamSubmission.objects.filter(
            enrollment=enrollment,
            status='graded'
        ).count()
        
        return {
            'overall_score': float(grade.overall_score),
            'letter_grade': grade.letter_grade,
            'rank': grade.rank,
            'components': {
                'missions': {
                    'score': float(grade.missions_score),
                    'weight': 25,
                    'count': missions_count
                },
                'capstones': {
                    'score': float(grade.capstones_score),
                    'weight': 30,
                    'count': capstones_count
                },
                'labs': {
                    'score': float(grade.labs_score),
                    'weight': 15,
                    'count': labs_count
                },
                'exams': {
                    'score': float(grade.exams_score),
                    'weight': 25,
                    'count': exams_count
                },
                'participation': {
                    'score': float(grade.participation_score),
                    'weight': 5,
                    'count': 1
                }
            },
            'last_calculated': grade.last_calculated.isoformat()
        }


# Singleton instance
grades_service = GradesService()
