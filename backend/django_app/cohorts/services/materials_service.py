"""
Materials Service - Manage cohort learning materials.
"""
from django.utils import timezone
from django.db.models import Q, Count, Avg
from cohorts.models import CohortDayMaterial, CohortMaterialProgress
from programs.models import Enrollment


class MaterialsService:
    """Service for managing cohort learning materials."""
    
    @staticmethod
    def get_cohort_materials(cohort_id, day_number=None):
        """
        Get materials for a cohort, optionally filtered by day.
        
        Args:
            cohort_id: Cohort UUID
            day_number: Optional day number filter
        
        Returns:
            QuerySet of CohortDayMaterial
        """
        queryset = CohortDayMaterial.objects.filter(cohort_id=cohort_id)
        
        if day_number:
            queryset = queryset.filter(day_number=day_number)
        
        return queryset.order_by('day_number', 'order')
    
    @staticmethod
    def get_materials_by_day(cohort_id):
        """
        Get materials grouped by day.
        
        Args:
            cohort_id: Cohort UUID
        
        Returns:
            dict: {day_number: [materials]}
        """
        materials = CohortDayMaterial.objects.filter(
            cohort_id=cohort_id
        ).order_by('day_number', 'order')
        
        grouped = {}
        for material in materials:
            day = material.day_number
            if day not in grouped:
                grouped[day] = []
            grouped[day].append(material)
        
        return grouped
    
    @staticmethod
    def get_student_progress(enrollment_id, material_id=None):
        """
        Get student progress on materials.
        
        Args:
            enrollment_id: Enrollment UUID
            material_id: Optional material UUID filter
        
        Returns:
            QuerySet or single CohortMaterialProgress
        """
        queryset = CohortMaterialProgress.objects.filter(enrollment_id=enrollment_id)
        
        if material_id:
            return queryset.filter(material_id=material_id).first()
        
        return queryset
    
    @staticmethod
    def start_material(enrollment_id, material_id):
        """
        Mark material as started.
        
        Args:
            enrollment_id: Enrollment UUID
            material_id: Material UUID
        
        Returns:
            CohortMaterialProgress instance
        """
        progress, created = CohortMaterialProgress.objects.get_or_create(
            enrollment_id=enrollment_id,
            material_id=material_id,
            defaults={
                'status': 'in_progress',
                'started_at': timezone.now()
            }
        )
        
        if not created and progress.status == 'not_started':
            progress.status = 'in_progress'
            progress.started_at = timezone.now()
            progress.save()
        
        return progress
    
    @staticmethod
    def complete_material(enrollment_id, material_id, time_spent_minutes=0, notes=''):
        """
        Mark material as completed.
        
        Args:
            enrollment_id: Enrollment UUID
            material_id: Material UUID
            time_spent_minutes: Time spent on material
            notes: Student notes
        
        Returns:
            CohortMaterialProgress instance
        """
        progress, created = CohortMaterialProgress.objects.get_or_create(
            enrollment_id=enrollment_id,
            material_id=material_id,
            defaults={
                'status': 'completed',
                'started_at': timezone.now(),
                'completed_at': timezone.now(),
                'time_spent_minutes': time_spent_minutes,
                'notes': notes
            }
        )
        
        if not created:
            progress.status = 'completed'
            progress.completed_at = timezone.now()
            progress.time_spent_minutes += time_spent_minutes
            if notes:
                progress.notes = notes
            progress.save()
        
        return progress
    
    @staticmethod
    def get_cohort_progress_summary(enrollment_id):
        """
        Get overall progress summary for a student in their cohort.
        
        Args:
            enrollment_id: Enrollment UUID
        
        Returns:
            dict with progress statistics
        """
        enrollment = Enrollment.objects.get(id=enrollment_id)
        cohort = enrollment.cohort
        
        # Total materials
        total_materials = CohortDayMaterial.objects.filter(cohort=cohort).count()
        
        # Student progress
        progress = CohortMaterialProgress.objects.filter(enrollment=enrollment)
        completed = progress.filter(status='completed').count()
        in_progress = progress.filter(status='in_progress').count()
        
        # Calculate percentage
        completion_percentage = (completed / total_materials * 100) if total_materials > 0 else 0
        
        # Time spent
        total_time = progress.aggregate(total=models.Sum('time_spent_minutes'))['total'] or 0
        
        return {
            'total_materials': total_materials,
            'completed': completed,
            'in_progress': in_progress,
            'not_started': total_materials - completed - in_progress,
            'completion_percentage': round(completion_percentage, 2),
            'total_time_minutes': total_time,
            'total_time_hours': round(total_time / 60, 2)
        }
    
    @staticmethod
    def is_material_unlocked(material, enrollment):
        """
        Check if material is unlocked for student.
        
        Args:
            material: CohortDayMaterial instance
            enrollment: Enrollment instance
        
        Returns:
            bool
        """
        if not material.unlock_date:
            return True
        
        today = timezone.now().date()
        return today >= material.unlock_date
    
    @staticmethod
    def get_unlocked_materials(cohort_id, enrollment_id):
        """
        Get all unlocked materials for a student.
        
        Args:
            cohort_id: Cohort UUID
            enrollment_id: Enrollment UUID
        
        Returns:
            QuerySet of unlocked materials
        """
        today = timezone.now().date()
        
        return CohortDayMaterial.objects.filter(
            cohort_id=cohort_id
        ).filter(
            Q(unlock_date__isnull=True) | Q(unlock_date__lte=today)
        ).order_by('day_number', 'order')


# Singleton instance
materials_service = MaterialsService()
