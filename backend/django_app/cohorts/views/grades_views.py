"""
Grades Views - Handle cohort grades and performance.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from programs.models import Enrollment
from cohorts.services.grades_service import grades_service
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_student_grades(request):
    """
    GET /api/v1/cohorts/grades?enrollment_id=uuid
    
    Get comprehensive grades for a student.
    
    Response:
    {
        "overall_score": 85.5,
        "letter_grade": "B",
        "rank": 5,
        "components": {
            "missions": {"score": 88.0, "weight": 25, "count": 10},
            "capstones": {"score": 90.0, "weight": 30, "count": 3},
            "labs": {"score": 85.0, "weight": 15, "count": 8},
            "exams": {"score": 82.0, "weight": 25, "count": 4},
            "participation": {"score": 80.0, "weight": 5, "count": 1}
        }
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
            enrollment = Enrollment.objects.get(id=enrollment_id, user=request.user)
        except Enrollment.DoesNotExist:
            return Response(
                {'error': 'Enrollment not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get grade breakdown
        breakdown = grades_service.get_grade_breakdown(enrollment_id)
        
        return Response(breakdown)
    
    except Exception as e:
        logger.error(f"Get grades error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def recalculate_grades(request):
    """
    POST /api/v1/cohorts/grades/recalculate
    
    Recalculate grades for a student.
    
    Request body:
    {
        "enrollment_id": "uuid"
    }
    """
    try:
        enrollment_id = request.data.get('enrollment_id')
        
        if not enrollment_id:
            return Response(
                {'error': 'enrollment_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify enrollment
        try:
            enrollment = Enrollment.objects.get(id=enrollment_id, user=request.user)
        except Enrollment.DoesNotExist:
            return Response(
                {'error': 'Enrollment not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Recalculate
        grade = grades_service.recalculate_grade(enrollment_id)
        
        return Response({
            'overall_score': float(grade.overall_score),
            'letter_grade': grade.letter_grade,
            'message': 'Grades recalculated successfully'
        })
    
    except Exception as e:
        logger.error(f"Recalculate grades error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_cohort_rankings(request):
    """
    GET /api/v1/cohorts/grades/rankings?cohort_id=uuid
    
    Get rankings for all students in cohort (only if student is in that cohort).
    
    Response:
    {
        "rankings": [
            {
                "rank": 1,
                "user_name": "John Doe",
                "overall_score": 95.5,
                "letter_grade": "A"
            }
        ]
    }
    """
    try:
        cohort_id = request.query_params.get('cohort_id')
        
        if not cohort_id:
            return Response(
                {'error': 'cohort_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify user is in this cohort
        try:
            enrollment = Enrollment.objects.get(
                cohort_id=cohort_id,
                user=request.user
            )
        except Enrollment.DoesNotExist:
            return Response(
                {'error': 'You are not enrolled in this cohort'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get rankings
        rankings = grades_service.get_cohort_rankings(cohort_id)
        
        # Anonymize other students (optional - remove if you want to show names)
        current_user_id = str(request.user.id)
        for ranking in rankings:
            if ranking['user_id'] != current_user_id:
                ranking['user_name'] = f"Student {ranking['rank']}"
                ranking.pop('user_email', None)
        
        return Response({'rankings': rankings})
    
    except Exception as e:
        logger.error(f"Get rankings error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
