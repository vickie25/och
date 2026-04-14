"""
Admin views for student management - onboarding emails and tracking.
"""
import logging

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsAdminOrDirector
from users.utils.email_utils import send_onboarding_email

logger = logging.getLogger(__name__)
User = get_user_model()


class SendOnboardingEmailView(APIView):
    """
    Send onboarding email to a student.
    POST /api/v1/admin/students/send-onboarding-email/
    Body: { "user_id": "123" }
    """
    permission_classes = [IsAuthenticated, IsAdminOrDirector]

    def post(self, request):
        user_id = request.data.get('user_id')
        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Reuse shared onboarding email implementation so director enrollment
        # matches self-registration onboarding behavior.
        success = send_onboarding_email(user)

        if success:
            return Response(
                {
                    "success": True,
                    "message": f"Onboarding email sent to {user.email}",
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "error": "Failed to send email",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class TrackOnboardingEmailView(APIView):
    """
    Track when onboarding email is opened.
    GET /api/track-onboarding-email?token=xxx&user_id=xxx
    Returns a 1x1 transparent pixel image.
    """
    permission_classes = []  # Public endpoint for email tracking

    def get(self, request):
        token = request.query_params.get('token')
        user_id = request.query_params.get('user_id')

        if not token or not user_id:
            # Return transparent pixel even if params are missing
            from django.http import HttpResponse
            pixel = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
            return HttpResponse(pixel, content_type='image/png')

        try:
            user = User.objects.get(id=user_id)

            # Verify token matches
            if user.metadata and user.metadata.get('onboarding_email_token') == token:
                # Update status to 'sent_and_seen'
                if user.onboarded_email_status == 'sent':
                    user.onboarded_email_status = 'sent_and_seen'
                    user.save(update_fields=['onboarded_email_status'])
                    logger.info(f"Onboarding email opened for user {user_id}")

        except User.DoesNotExist:
            pass
        except Exception as e:
            logger.error(f"Error tracking onboarding email: {str(e)}")

        # Return transparent 1x1 pixel
        from django.http import HttpResponse
        pixel = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
        return HttpResponse(pixel, content_type='image/png')
