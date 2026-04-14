"""
Certificate Verification Views
Public verification endpoint for certificate validation per OCH Certificate Renewal Model v1.0
"""
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from ..models import Certificate


@api_view(['GET'])
@permission_classes([AllowAny])
def verify_certificate(request, certificate_id):
    """
    Public verification endpoint for certificates.

    GET /api/v1/certificates/{certificate_id}/verify/

    Returns certificate details including:
    - Student name, track, level
    - Issue date, expiry date
    - Current status with visual badge
    - Renewal count and last renewal date
    - QR code for sharing

    Per OCH Certificate Renewal Model v1.0 Section 7.
    """
    try:
        certificate = get_object_or_404(Certificate, id=certificate_id)
        enrollment = certificate.enrollment
        user = enrollment.user
        cohort = enrollment.cohort
        track = cohort.track
        program = track.program

        # Build response per spec
        response_data = {
            'verified': True,
            'certificate': {
                'id': str(certificate.id),
                'certificate_id': certificate.certificate_id_formatted,
                'status': certificate.status,
                'status_display': certificate.get_status_display(),
                'status_badge': _get_status_badge(certificate.status),

                # Student info
                'student_name': f"{user.first_name} {user.last_name}".strip() or user.email,
                'track': track.name,
                'program': program.name,
                'level': 'L1',  # Could be dynamic based on track

                # Dates
                'issue_date': certificate.issue_date.isoformat() if certificate.issue_date else None,
                'expiry_date': certificate.expiry_date.isoformat() if certificate.expiry_date else None,
                'grace_period_end': certificate.grace_period_end.isoformat() if certificate.grace_period_end else None,

                # Renewal info
                'renewal_count': certificate.renewal_count,
                'last_renewal_date': certificate.last_renewal_date.isoformat() if certificate.last_renewal_date else None,
                'last_renewal_method': certificate.last_renewal_method,

                # Additional metrics
                'total_hours': certificate.total_hours,
                'missions_completed': certificate.missions_completed,
                'grade': certificate.grade or enrollment.grade or 'Pass',

                # Verification
                'verification_url': f"https://ongozacyberhub.com/verify/{certificate.id}",
                'qr_code_url': f"/api/v1/certificates/{certificate.id}/qr-code/",
                'download_url': f"/api/v1/certificates/{certificate.id}/download/",
            }
        }

        return Response(response_data)

    except Certificate.DoesNotExist:
        return Response(
            {
                'verified': False,
                'error': 'Certificate not found',
                'message': 'The certificate ID provided could not be verified.'
            },
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {
                'verified': False,
                'error': 'Verification failed',
                'message': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def _get_status_badge(status: str) -> dict:
    """
    Get visual badge configuration for certificate status.

    Per spec: Visual badge showing ACTIVE (green), GRACE_PERIOD (amber),
    EXPIRED (red), or SUSPENDED (grey)
    """
    badges = {
        'active': {
            'color': 'green',
            'bg_color': '#22c55e',
            'text_color': '#ffffff',
            'label': 'ACTIVE',
            'icon': 'check-circle'
        },
        'renewal_pending': {
            'color': 'blue',
            'bg_color': '#3b82f6',
            'text_color': '#ffffff',
            'label': 'RENEWAL PENDING',
            'icon': 'clock'
        },
        'grace_period': {
            'color': 'amber',
            'bg_color': '#f59e0b',
            'text_color': '#ffffff',
            'label': 'GRACE PERIOD',
            'icon': 'alert-triangle'
        },
        'expired': {
            'color': 'red',
            'bg_color': '#ef4444',
            'text_color': '#ffffff',
            'label': 'EXPIRED',
            'icon': 'x-circle'
        },
        'renewed': {
            'color': 'purple',
            'bg_color': '#8b5cf6',
            'text_color': '#ffffff',
            'label': 'RENEWED',
            'icon': 'refresh-cw'
        },
        'suspended': {
            'color': 'grey',
            'bg_color': '#6b7280',
            'text_color': '#ffffff',
            'label': 'SUSPENDED',
            'icon': 'pause-circle'
        },
    }

    return badges.get(status, badges['suspended'])


@api_view(['GET'])
@permission_classes([AllowAny])
def verify_certificate_by_formatted_id(request, formatted_id):
    """
    Verify certificate using formatted ID (OCH-{TRACK}-{LEVEL}-{YYYYMMDD}-{RANDOM}).

    GET /api/v1/certificates/verify/formatted/{formatted_id}/
    """
    try:
        # Parse formatted ID to extract certificate info
        # Format: OCH-{TRACK}-{LEVEL}-{YYYYMMDD}-{RANDOM}
        parts = formatted_id.split('-')
        if len(parts) >= 4 and parts[0] == 'OCH':
            # Try to find by formatted ID pattern
            # The random suffix is the first 8 chars of the UUID
            parts[-1]

            # Query all certificates and match by formatted ID
            from ..models import Certificate
            for cert in Certificate.objects.all():
                if cert.certificate_id_formatted == formatted_id:
                    # Redirect to main verify function
                    return verify_certificate(request, str(cert.id))

        return Response(
            {
                'verified': False,
                'error': 'Invalid certificate ID format'
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    except Exception as e:
        return Response(
            {
                'verified': False,
                'error': 'Verification failed',
                'message': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
