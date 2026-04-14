"""
Materials Views - Handle cohort learning materials.
"""
import logging

from programs.models import Enrollment
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from cohorts.models import CohortMaterialProgress
from cohorts.services.materials_service import materials_service

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_cohort_materials(request):
    """
    GET /api/v1/cohorts/materials?enrollment_id=uuid&day=1

    Get learning materials for cohort, optionally filtered by day.

    Response:
    {
        "materials": [
            {
                "id": "uuid",
                "day_number": 1,
                "title": "Introduction to Cybersecurity",
                "description": "...",
                "material_type": "video",
                "content_url": "https://...",
                "estimated_minutes": 30,
                "is_required": true,
                "is_unlocked": true,
                "progress": {
                    "status": "completed",
                    "completed_at": "2024-01-01T00:00:00Z"
                }
            }
        ]
    }
    """
    try:
        enrollment_id = request.query_params.get('enrollment_id')
        day_number = request.query_params.get('day')

        if not enrollment_id:
            return Response(
                {'error': 'enrollment_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get enrollment
        try:
            enrollment = Enrollment.objects.select_related('cohort').get(
                id=enrollment_id,
                user=request.user
            )
        except Enrollment.DoesNotExist:
            return Response(
                {'error': 'Enrollment not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get materials
        materials = materials_service.get_cohort_materials(
            enrollment.cohort.id,
            day_number=int(day_number) if day_number else None
        )

        # Get student progress
        progress_map = {}
        for prog in CohortMaterialProgress.objects.filter(enrollment=enrollment):
            progress_map[str(prog.material_id)] = prog

        # Build response
        materials_data = []
        for material in materials:
            progress = progress_map.get(str(material.id))
            is_unlocked = materials_service.is_material_unlocked(material, enrollment)

            materials_data.append({
                'id': str(material.id),
                'day_number': material.day_number,
                'title': material.title,
                'description': material.description,
                'material_type': material.material_type,
                'content_url': material.content_url if is_unlocked else None,
                'content_text': material.content_text if is_unlocked else None,
                'estimated_minutes': material.estimated_minutes,
                'is_required': material.is_required,
                'is_unlocked': is_unlocked,
                'unlock_date': material.unlock_date.isoformat() if material.unlock_date else None,
                'progress': {
                    'status': progress.status if progress else 'not_started',
                    'started_at': progress.started_at.isoformat() if progress and progress.started_at else None,
                    'completed_at': progress.completed_at.isoformat() if progress and progress.completed_at else None,
                    'time_spent_minutes': progress.time_spent_minutes if progress else 0
                } if progress else None
            })

        return Response({'materials': materials_data})

    except Exception as e:
        logger.error(f"Get materials error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_materials_by_day(request):
    """
    GET /api/v1/cohorts/materials/by-day?enrollment_id=uuid

    Get materials grouped by day.

    Response:
    {
        "days": {
            "1": [...materials...],
            "2": [...materials...]
        },
        "total_days": 60
    }
    """
    try:
        enrollment_id = request.query_params.get('enrollment_id')

        if not enrollment_id:
            return Response(
                {'error': 'enrollment_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get enrollment
        try:
            enrollment = Enrollment.objects.select_related('cohort').get(
                id=enrollment_id,
                user=request.user
            )
        except Enrollment.DoesNotExist:
            return Response(
                {'error': 'Enrollment not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get materials grouped by day
        grouped_materials = materials_service.get_materials_by_day(enrollment.cohort.id)

        # Get student progress
        progress_map = {}
        for prog in CohortMaterialProgress.objects.filter(enrollment=enrollment):
            progress_map[str(prog.material_id)] = prog

        # Build response
        days_data = {}
        for day_num, materials in grouped_materials.items():
            day_materials = []
            for material in materials:
                progress = progress_map.get(str(material.id))
                is_unlocked = materials_service.is_material_unlocked(material, enrollment)

                day_materials.append({
                    'id': str(material.id),
                    'title': material.title,
                    'material_type': material.material_type,
                    'estimated_minutes': material.estimated_minutes,
                    'is_required': material.is_required,
                    'is_unlocked': is_unlocked,
                    'progress_status': progress.status if progress else 'not_started'
                })

            days_data[str(day_num)] = day_materials

        return Response({
            'days': days_data,
            'total_days': len(grouped_materials)
        })

    except Exception as e:
        logger.error(f"Get materials by day error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_material(request):
    """
    POST /api/v1/cohorts/materials/start

    Mark material as started.

    Request body:
    {
        "enrollment_id": "uuid",
        "material_id": "uuid"
    }
    """
    try:
        enrollment_id = request.data.get('enrollment_id')
        material_id = request.data.get('material_id')

        if not enrollment_id or not material_id:
            return Response(
                {'error': 'enrollment_id and material_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify enrollment
        try:
            Enrollment.objects.get(id=enrollment_id, user=request.user)
        except Enrollment.DoesNotExist:
            return Response(
                {'error': 'Enrollment not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Start material
        progress = materials_service.start_material(enrollment_id, material_id)

        return Response({
            'status': progress.status,
            'started_at': progress.started_at.isoformat() if progress.started_at else None
        })

    except Exception as e:
        logger.error(f"Start material error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_material(request):
    """
    POST /api/v1/cohorts/materials/complete

    Mark material as completed.

    Request body:
    {
        "enrollment_id": "uuid",
        "material_id": "uuid",
        "time_spent_minutes": 30,
        "notes": "optional notes"
    }
    """
    try:
        enrollment_id = request.data.get('enrollment_id')
        material_id = request.data.get('material_id')
        time_spent = request.data.get('time_spent_minutes', 0)
        notes = request.data.get('notes', '')

        if not enrollment_id or not material_id:
            return Response(
                {'error': 'enrollment_id and material_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify enrollment
        try:
            Enrollment.objects.get(id=enrollment_id, user=request.user)
        except Enrollment.DoesNotExist:
            return Response(
                {'error': 'Enrollment not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Complete material
        progress = materials_service.complete_material(
            enrollment_id,
            material_id,
            time_spent_minutes=time_spent,
            notes=notes
        )

        return Response({
            'status': progress.status,
            'completed_at': progress.completed_at.isoformat() if progress.completed_at else None,
            'time_spent_minutes': progress.time_spent_minutes
        })

    except Exception as e:
        logger.error(f"Complete material error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_progress_summary(request):
    """
    GET /api/v1/cohorts/materials/progress?enrollment_id=uuid

    Get overall progress summary.

    Response:
    {
        "total_materials": 100,
        "completed": 45,
        "in_progress": 10,
        "not_started": 45,
        "completion_percentage": 45.0,
        "total_time_hours": 22.5
    }
    """
    try:
        enrollment_id = request.query_params.get('enrollment_id')

        if not enrollment_id:
            return Response(
                {'error': 'enrollment_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify enrollment
        try:
            Enrollment.objects.get(id=enrollment_id, user=request.user)
        except Enrollment.DoesNotExist:
            return Response(
                {'error': 'Enrollment not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get summary
        summary = materials_service.get_cohort_progress_summary(enrollment_id)

        return Response(summary)

    except Exception as e:
        logger.error(f"Get progress summary error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
