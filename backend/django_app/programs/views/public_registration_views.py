"""
Public Registration Views - Handle public cohort browsing and applications.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from programs.models import Cohort
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def list_published_cohorts(request):
    """
    GET /api/v1/programs/public/cohorts/
    
    List all published cohorts available for public enrollment.
    No authentication required.
    
    Response:
    [
        {
            "id": "uuid",
            "name": "Cybersecurity Bootcamp 2024",
            "start_date": "2024-02-01",
            "end_date": "2024-05-01",
            "mode": "virtual",
            "seat_cap": 50,
            "enrolled_count": 25,
            "enrollment_fee": 100.00,
            "currency": "USD",
            "track_name": "Defender",
            "description": "...",
            "profile_image": "https://..."
        }
    ]
    """
    try:
        # Debug: Check all cohorts first
        all_cohorts = Cohort.objects.all()
        logger.info(f"Total cohorts in database: {all_cohorts.count()}")
        
        published_cohorts = Cohort.objects.filter(published_to_homepage=True)
        logger.info(f"Published cohorts: {published_cohorts.count()}")
        
        # Get all published cohorts that are accepting applications
        cohorts = Cohort.objects.filter(
            published_to_homepage=True,
            status__in=['draft', 'active', 'running']
        ).select_related('track').order_by('start_date')
        
        logger.info(f"Filtered cohorts: {cohorts.count()}")
        
        cohorts_data = []
        for cohort in cohorts:
            # Count enrolled students
            enrolled_count = cohort.enrollments.filter(
                status__in=['active', 'pending_payment']
            ).count()
            
            logger.info(f"Processing cohort: {cohort.name}, track: {cohort.track.name if cohort.track else 'No Track'}")
            
            cohorts_data.append({
                'id': str(cohort.id),
                'name': cohort.name,
                'start_date': cohort.start_date.isoformat(),
                'end_date': cohort.end_date.isoformat(),
                'mode': cohort.mode,
                'seat_cap': cohort.seat_cap,
                'enrolled_count': enrolled_count,
                'enrollment_fee': float(getattr(cohort, 'enrollment_fee', 100.00)),
                'currency': getattr(cohort, 'currency', 'USD'),
                'track_name': cohort.track.name if cohort.track else 'No Track',
                'description': getattr(cohort, 'description', ''),
                'profile_image': cohort.profile_image.url if cohort.profile_image else None,
            })
        
        logger.info(f"Returning {len(cohorts_data)} cohorts")
        return Response(cohorts_data)
    
    except Exception as e:
        logger.error(f"Error listing published cohorts: {str(e)}")
        return Response(
            {'error': 'Failed to load cohorts'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def apply_as_student(request, cohort_id):
    """
    POST /api/v1/programs/public/cohorts/<uuid:cohort_id>/apply/student/
    
    Submit student application for a cohort.
    No authentication required.
    
    Request body:
    {
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "+1234567890",
        "background": "Software developer with 3 years experience",
        "motivation": "Want to learn cybersecurity..."
    }
    """
    try:
        # Get cohort
        try:
            cohort = Cohort.objects.get(id=cohort_id, published_to_homepage=True)
        except Cohort.DoesNotExist:
            return Response(
                {'error': 'Cohort not found or not available for applications'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validate required fields
        required_fields = ['name', 'email']
        for field in required_fields:
            if not request.data.get(field):
                return Response(
                    {'error': f'{field} is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Create application (you'll need to import CohortPublicApplication)
        from programs.models import CohortPublicApplication
        
        application = CohortPublicApplication.objects.create(
            cohort=cohort,
            applicant_type='student',
            form_data=request.data,
            status='pending'
        )
        
        return Response({
            'application_id': str(application.id),
            'message': 'Application submitted successfully',
            'next_steps': 'You will receive an email with further instructions'
        }, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        logger.error(f"Error submitting student application: {str(e)}")
        return Response(
            {'error': 'Failed to submit application'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def join_as_sponsor(request, cohort_id):
    """
    POST /api/v1/programs/public/cohorts/<uuid:cohort_id>/apply/sponsor/
    
    Submit sponsor application for a cohort.
    """
    try:
        # Get cohort
        try:
            cohort = Cohort.objects.get(id=cohort_id, published_to_homepage=True)
        except Cohort.DoesNotExist:
            return Response(
                {'error': 'Cohort not found or not available for applications'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validate required fields
        required_fields = ['organization_name', 'contact_email', 'contact_name']
        for field in required_fields:
            if not request.data.get(field):
                return Response(
                    {'error': f'{field} is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Create sponsor application
        from programs.models import CohortPublicApplication
        
        application = CohortPublicApplication.objects.create(
            cohort=cohort,
            applicant_type='sponsor',
            form_data=request.data,
            status='pending'
        )
        
        return Response({
            'application_id': str(application.id),
            'message': 'Sponsor application submitted successfully',
            'next_steps': 'Our team will contact you within 2 business days'
        }, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        logger.error(f"Error submitting sponsor application: {str(e)}")
        return Response(
            {'error': 'Failed to submit application'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Placeholder functions for other endpoints referenced in urls.py
@api_view(['GET'])
def list_public_applications(request):
    return Response({'message': 'Not implemented'})

@api_view(['POST'])
def assign_applications_to_mentor(request):
    return Response({'message': 'Not implemented'})

@api_view(['POST'])
def set_review_cutoff(request):
    return Response({'message': 'Not implemented'})

@api_view(['POST'])
def set_interview_cutoff(request):
    return Response({'message': 'Not implemented'})

@api_view(['POST'])
def enroll_applications(request):
    return Response({'message': 'Not implemented'})

@api_view(['POST'])
def reject_application(request):
    return Response({'message': 'Not implemented'})

@api_view(['POST'])
def delete_applications(request):
    return Response({'message': 'Not implemented'})

@api_view(['POST'])
def send_application_credentials_email_view(request):
    return Response({'message': 'Not implemented'})

@api_view(['GET'])
def list_mentor_applications(request):
    return Response({'message': 'Not implemented'})

@api_view(['POST'])
def grade_application(request, application_id):
    return Response({'message': 'Not implemented'})

@api_view(['POST'])
def grade_interview(request, application_id):
    return Response({'message': 'Not implemented'})

@api_view(['POST'])
def send_application_tests(request):
    return Response({'message': 'Not implemented'})

@api_view(['POST'])
def grade_application_test(request):
    return Response({'message': 'Not implemented'})