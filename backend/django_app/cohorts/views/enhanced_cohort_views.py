"""
Enhanced Cohort Management Views - Complete cohort lifecycle management.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from programs.models import Cohort, Enrollment, Track
from cohorts.services.enhanced_cohort_service import enhanced_cohort_service
from cohorts.services.materials_service import materials_service
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_cohort_status(request):
    """
    GET /api/v1/cohorts/my-status/
    
    Get user's cohort enrollment status and subscription benefits.
    """
    try:
        status_data = enhanced_cohort_service.get_user_cohort_status(request.user)
        return Response(status_data)
    
    except Exception as e:
        logger.error(f"Get user cohort status error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_cohort_eligibility(request):
    """
    POST /api/v1/cohorts/check-eligibility/
    
    Check if user can enroll in a specific cohort.
    
    Request body:
    {
        "cohort_id": "uuid",
        "seat_type": "paid"  // optional
    }
    """
    try:
        cohort_id = request.data.get('cohort_id')
        seat_type = request.data.get('seat_type', 'paid')
        
        if not cohort_id:
            return Response(
                {'error': 'cohort_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        cohort = get_object_or_404(Cohort, id=cohort_id)
        
        # Check subscription eligibility
        subscription_eligibility = enhanced_cohort_service.check_subscription_cohort_eligibility(
            request.user, cohort
        )
        
        # Check seat availability
        seat_availability = enhanced_cohort_service.get_available_seats(cohort)
        
        # Calculate pricing
        pricing = enhanced_cohort_service.calculate_cohort_pricing(
            cohort, request.user, seat_type
        )
        
        # Check if already enrolled
        existing_enrollment = Enrollment.objects.filter(
            user=request.user,
            cohort=cohort
        ).first()
        
        return Response({
            'eligible': not existing_enrollment and seat_availability['seat_breakdown'][seat_type]['available'] > 0,
            'existing_enrollment': str(existing_enrollment.id) if existing_enrollment else None,
            'subscription_benefits': subscription_eligibility,
            'seat_availability': seat_availability,
            'pricing': pricing,
            'cohort_info': {
                'id': str(cohort.id),
                'name': cohort.name,
                'start_date': cohort.start_date.isoformat(),
                'end_date': cohort.end_date.isoformat(),
                'mode': cohort.mode,
                'status': cohort.status
            }
        })
    
    except Exception as e:
        logger.error(f"Check cohort eligibility error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def enroll_in_cohort(request):
    """
    POST /api/v1/cohorts/enroll/
    
    Enroll user in a cohort.
    
    Request body:
    {
        "cohort_id": "uuid",
        "seat_type": "paid",
        "enrollment_type": "self"
    }
    """
    try:
        cohort_id = request.data.get('cohort_id')
        seat_type = request.data.get('seat_type', 'paid')
        enrollment_type = request.data.get('enrollment_type', 'self')
        
        if not cohort_id:
            return Response(
                {'error': 'cohort_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        cohort = get_object_or_404(Cohort, id=cohort_id)
        
        # Enroll user
        result = enhanced_cohort_service.enroll_user_in_cohort(
            user=request.user,
            cohort=cohort,
            seat_type=seat_type,
            enrollment_type=enrollment_type
        )
        
        if result['success']:
            return Response(result, status=status.HTTP_201_CREATED)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"Enroll in cohort error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_cohort_analytics(request, cohort_id):
    """
    GET /api/v1/cohorts/{cohort_id}/analytics/
    
    Get comprehensive analytics for a cohort.
    """
    try:
        cohort = get_object_or_404(Cohort, id=cohort_id)
        
        # Check permissions
        if not (request.user == cohort.coordinator or 
                request.user in [ma.mentor for ma in cohort.mentor_assignments.filter(active=True)] or
                request.user.role in ['admin', 'director']):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        analytics = enhanced_cohort_service.get_cohort_analytics(cohort)
        
        return Response({
            'cohort_id': str(cohort.id),
            'cohort_name': cohort.name,
            'analytics': analytics,
            'generated_at': timezone.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Get cohort analytics error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_cohort_dashboard(request, enrollment_id):
    """
    GET /api/v1/cohorts/dashboard/{enrollment_id}/
    
    Get student's cohort learning dashboard.
    """
    try:
        enrollment = get_object_or_404(
            Enrollment,
            id=enrollment_id,
            user=request.user
        )
        
        cohort = enrollment.cohort
        
        # Get materials grouped by day
        materials_by_day = materials_service.get_materials_by_day(cohort.id)
        
        # Get student progress
        progress_summary = materials_service.get_cohort_progress_summary(enrollment_id)
        
        # Get upcoming events
        upcoming_events = cohort.calendar_events.filter(
            start_ts__gte=timezone.now(),
            status='scheduled'
        ).order_by('start_ts')[:5]
        
        # Get mentor assignments
        mentors = cohort.mentor_assignments.filter(active=True).select_related('mentor')
        
        return Response({
            'enrollment_info': {
                'id': str(enrollment.id),
                'status': enrollment.status,
                'seat_type': enrollment.seat_type,
                'joined_at': enrollment.joined_at.isoformat()
            },
            'cohort_info': {
                'id': str(cohort.id),
                'name': cohort.name,
                'start_date': cohort.start_date.isoformat(),
                'end_date': cohort.end_date.isoformat(),
                'mode': cohort.mode,
                'track_name': cohort.track.name if cohort.track else None
            },
            'progress_summary': progress_summary,
            'materials_by_day': materials_by_day,
            'upcoming_events': [
                {
                    'id': str(event.id),
                    'title': event.title,
                    'type': event.type,
                    'start_ts': event.start_ts.isoformat(),
                    'location': event.location,
                    'link': event.link
                }
                for event in upcoming_events
            ],
            'mentors': [
                {
                    'id': str(mentor.mentor.id),
                    'name': f"{mentor.mentor.first_name} {mentor.mentor.last_name}",
                    'email': mentor.mentor.email,
                    'role': mentor.role
                }
                for mentor in mentors
            ]
        })
    
    except Exception as e:
        logger.error(f"Get cohort dashboard error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_available_cohorts(request):
    """
    GET /api/v1/cohorts/available/
    
    Get cohorts available for enrollment with user-specific pricing.
    """
    try:
        # Get published cohorts that are accepting enrollment
        cohorts = Cohort.objects.filter(
            published_to_homepage=True,
            status__in=['active', 'draft'],
            start_date__gt=timezone.now().date()
        ).select_related('track', 'track__program').order_by('start_date')
        
        cohorts_data = []
        for cohort in cohorts:
            # Check seat availability
            seat_availability = enhanced_cohort_service.get_available_seats(cohort)
            
            # Calculate pricing for user
            pricing = enhanced_cohort_service.calculate_cohort_pricing(cohort, request.user)
            
            # Check if user already enrolled
            user_enrolled = Enrollment.objects.filter(
                user=request.user,
                cohort=cohort
            ).exists()
            
            cohorts_data.append({
                'id': str(cohort.id),
                'name': cohort.name,
                'description': cohort.track.description if cohort.track else '',
                'track_name': cohort.track.name if cohort.track else None,
                'program_name': cohort.track.program.name if cohort.track and cohort.track.program else None,
                'start_date': cohort.start_date.isoformat(),
                'end_date': cohort.end_date.isoformat(),
                'mode': cohort.mode,
                'duration_weeks': (cohort.end_date - cohort.start_date).days // 7,
                'seat_availability': seat_availability,
                'pricing': pricing,
                'user_enrolled': user_enrolled,
                'profile_image': cohort.profile_image.url if cohort.profile_image else None
            })
        
        return Response({
            'cohorts': cohorts_data,
            'total_available': len(cohorts_data)
        })
    
    except Exception as e:
        logger.error(f"Get available cohorts error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_cohort_pricing(request, cohort_id):
    """
    POST /api/v1/cohorts/{cohort_id}/pricing/
    
    Update cohort-specific pricing (admin/director only).
    
    Request body:
    {
        "base_price": 150.00,
        "seat_pool": {
            "paid": 40,
            "scholarship": 5,
            "sponsored": 5
        },
        "subscription_discounts": {
            "basic": 0.10,
            "premium": 0.20,
            "enterprise": 0.30
        }
    }
    """
    try:
        cohort = get_object_or_404(Cohort, id=cohort_id)
        
        # Check permissions
        if not (request.user == cohort.coordinator or 
                request.user.role in ['admin', 'director']):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        data = request.data
        
        # Update base price in track/program
        if 'base_price' in data and cohort.track:
            cohort.track.program.default_price = data['base_price']
            cohort.track.program.save()
        
        # Update seat pool
        if 'seat_pool' in data:
            cohort.seat_pool = data['seat_pool']
            cohort.save()
        
        return Response({
            'message': 'Cohort pricing updated successfully',
            'updated_pricing': enhanced_cohort_service.calculate_cohort_pricing(cohort)
        })
    
    except Exception as e:
        logger.error(f"Update cohort pricing error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )