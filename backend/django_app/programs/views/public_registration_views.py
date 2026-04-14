"""
Public Registration Views - Handle public cohort browsing and applications.
"""
import logging

from curriculum.models import CurriculumTrack
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from programs.models import Cohort, CohortPublicApplication

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

            # Resolve a human-friendly track name
            track_name = None
            if cohort.track:
                track_name = cohort.track.name
            else:
                # Fallback: use first curriculum track based on curriculum_tracks JSON
                raw_curriculum = getattr(cohort, 'curriculum_tracks', []) or []
                curriculum_slugs = []
                if isinstance(raw_curriculum, (list, tuple)):
                    for item in raw_curriculum:
                        if isinstance(item, str):
                            curriculum_slugs.append(item)
                        elif isinstance(item, dict):
                            # Support shapes like {"slug": "...", "code": "..."}
                            slug_val = item.get('slug') or item.get('code')
                            if isinstance(slug_val, str):
                                curriculum_slugs.append(slug_val)
                try:
                    if curriculum_slugs:
                        curriculum_tracks = list(
                            CurriculumTrack.objects.filter(slug__in=curriculum_slugs)
                        )
                        if curriculum_tracks:
                            ct = curriculum_tracks[0]
                            track_name = getattr(ct, 'name', None) or getattr(ct, 'code', None) or curriculum_slugs[0]
                        else:
                            # No track objects found, fall back to first slug string
                            track_name = curriculum_slugs[0]
                except Exception as ct_err:
                    logger.warning(f"Error resolving curriculum tracks for cohort {cohort.id}: {ct_err}")

            if not track_name:
                track_name = 'No Track'

            logger.info(f"Processing cohort: {cohort.name}, track: {track_name}")

            # Build profile image URLs (relative + absolute)
            if cohort.profile_image:
                if request:
                    profile_image_url = request.build_absolute_uri(cohort.profile_image.url)
                else:
                    profile_image_url = cohort.profile_image.url
            else:
                profile_image_url = None

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
                'track_name': track_name,
                'description': getattr(cohort, 'description', ''),
                # Keep backward-compatible key plus explicit URL key
                'profile_image': cohort.profile_image.url if cohort.profile_image else None,
                'profile_image_url': profile_image_url,
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_my_cohort_applications(request):
    """
    GET /api/v1/programs/public/my-applications/

    Return the current user's public cohort applications, matched by email.
    Used by the student dashboard to show "Applied" status on cohorts.
    """
    try:
        email = (request.user.email or '').strip().lower()
        if not email:
            return Response([], status=status.HTTP_200_OK)

        # Match historical and current payload shapes:
        # - {"email": "..."}
        # - {"contact_email": "..."} (sponsors)
        # - {"form_data": {"email": "..."}}
        # - {"form_data": {"contact_email": "..."}}
        email_filter = (
            Q(form_data__email__iexact=email) |
            Q(form_data__contact_email__iexact=email) |
            Q(form_data__form_data__email__iexact=email) |
            Q(form_data__form_data__contact_email__iexact=email)
        )

        applications = (
            CohortPublicApplication.objects
            .filter(email_filter)
            .select_related('cohort')
            .order_by('-created_at')
        )

        data = []
        for app in applications:
            data.append({
                'id': str(app.id),
                'cohort_id': str(app.cohort_id),
                'cohort_name': app.cohort.name if app.cohort else None,
                'applicant_type': app.applicant_type,
                'status': app.status,
                'created_at': app.created_at.isoformat() if app.created_at else None,
            })

        return Response(data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error listing my cohort applications: {str(e)}")
        return Response(
            {'error': 'Failed to load applications'},
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




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_public_applications(request):
    """
    GET /api/v1/programs/director/public-applications/

    Director/mentor view of public cohort applications.
    Supports filtering via query params:
      - cohort_id
      - applicant_type
      - status
      - review_status
      - enrollment_status
      - reviewer_mentor_id

    Response:
      { "applications": [ ...Application ] }
    """
    if not (request.user.is_staff or request.user.is_superuser):
        return Response(
            {'detail': 'You do not have permission to view applications.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        qs = CohortPublicApplication.objects.select_related('cohort', 'reviewer_mentor', 'interview_mentor')

        cohort_id = request.query_params.get('cohort_id')
        applicant_type = request.query_params.get('applicant_type')
        status_param = request.query_params.get('status')
        review_status = request.query_params.get('review_status')
        enrollment_status = request.query_params.get('enrollment_status')
        reviewer_mentor_id = request.query_params.get('reviewer_mentor_id')

        if cohort_id:
            qs = qs.filter(cohort_id=cohort_id)
        if applicant_type:
            qs = qs.filter(applicant_type=applicant_type)
        if status_param:
            qs = qs.filter(status=status_param)
        if review_status:
            qs = qs.filter(review_status=review_status)
        if enrollment_status:
            qs = qs.filter(enrollment_status=enrollment_status)
        if reviewer_mentor_id:
            qs = qs.filter(reviewer_mentor_id=reviewer_mentor_id)

        applications = []
        for app in qs.order_by('-created_at'):
            fd = app.form_data or {}
            email = fd.get('email') or fd.get('contact_email') or ''
            name = fd.get('name') or fd.get('full_name') or fd.get('contact_name') or ''

            applications.append({
                'id': str(app.id),
                'cohort_id': str(app.cohort_id),
                'cohort_name': app.cohort.name if app.cohort else '',
                'applicant_type': app.applicant_type,
                'status': app.status,
                'form_data': fd,
                'email': email,
                'name': name,
                'notes': app.notes or '',
                'created_at': app.created_at.isoformat() if app.created_at else None,
                'reviewer_mentor_id': app.reviewer_mentor_id,
                'reviewer_mentor_name': (
                    f"{app.reviewer_mentor.first_name} {app.reviewer_mentor.last_name}".strip()
                    if app.reviewer_mentor else None
                ),
                'review_score': float(app.review_score) if app.review_score is not None else None,
                'review_status': app.review_status,
                'interview_mentor_name': (
                    f"{app.interview_mentor.first_name} {app.interview_mentor.last_name}".strip()
                    if app.interview_mentor else None
                ),
                'interview_score': float(app.interview_score) if app.interview_score is not None else None,
                'interview_status': app.interview_status,
                'enrollment_status': app.enrollment_status,
            })

        return Response({'applications': applications}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error listing public applications: {str(e)}")
        return Response(
            {'error': 'Failed to load applications'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

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
