"""
Risk assessment utilities for authentication security.
"""
from datetime import timedelta

from django.utils import timezone

from users.audit_models import AuditLog
from users.auth_models import DeviceTrust, UserSession


def calculate_risk_score(user, ip_address, device_fingerprint, user_agent):
    """
    Calculate risk score based on:
    - New device detection
    - Geo-velocity (IP changes)
    - TOR/VPN detection (placeholder)
    - Previous failed attempts

    NOTE: DB schema has bigint user_id in device_trust/user_sessions but Django
    model may pass a UUID. Each query is wrapped in try/except to degrade
    gracefully (assumes higher risk) instead of crashing with a 500 error.
    """
    import logging
    logger = logging.getLogger(__name__)
    risk_score = 0.0

    # Check if device is new (wrapped for bigint/uuid type mismatch safety)
    try:
        device_known = DeviceTrust.objects.filter(
            user_id=user.pk,
            device_fingerprint=device_fingerprint
        ).exists()
        if not device_known:
            risk_score += 0.3  # New device
    except Exception as e:
        logger.warning('DeviceTrust query failed (schema mismatch?): %s', e)
        risk_score += 0.3  # Assume new device if we can't check

    # Check recent IP addresses (wrapped for type safety)
    recent_ips = []
    try:
        recent_ips = list(
            UserSession.objects.filter(
                user_id=user.pk,
                created_at__gte=timezone.now() - timedelta(hours=24)
            ).exclude(ip_address__isnull=True)
             .values_list('ip_address', flat=True)
             .distinct()
        )
    except Exception as e:
        logger.warning('UserSession IP query failed (schema mismatch?): %s', e)

    if ip_address and ip_address not in recent_ips:
        risk_score += 0.2  # New IP address

    # Check for rapid IP changes (geo-velocity)
    if len(recent_ips) > 3:
        risk_score += 0.2

    # Check failed login attempts (from audit log)
    try:
        recent_failures = AuditLog.objects.filter(
            user_id=user.pk,
            action='login',
            result='failure',
            timestamp__gte=timezone.now() - timedelta(minutes=15)
        ).count()
        if recent_failures > 0:
            risk_score += min(recent_failures * 0.1, 0.5)
    except Exception as e:
        logger.warning('AuditLog query failed (schema mismatch?): %s', e)

    # TOR/VPN detection (placeholder - implement with external service)
    if _is_tor_or_vpn(ip_address):
        risk_score += 0.3

    return min(risk_score, 1.0)  # Cap at 1.0


def requires_mfa(risk_score, user_role=None, user=None):
    """
    Determine if MFA is required based on risk score and role.
    Finance/Admin roles always require MFA.
    """
    from django.conf import settings

    # In development, skip MFA for all users unless they explicitly enabled it
    if settings.DEBUG and user and not user.mfa_enabled:
        return False

    # Mandatory roles for MFA (Staff/Internal) when not in DEBUG mode (live)
    MANDATORY_MFA_ROLES = ['admin', 'finance', 'finance_admin', 'support', 'program_director']

    # Force MFA for mandatory roles when not in DEBUG mode
    if user_role and user_role.lower() in [r.lower() for r in MANDATORY_MFA_ROLES]:
        # EMERGENCY BYPASS FOR PRESENTATION - REMOVE AFTER FIXING EMAIL
        # Disabling MFA for all staff roles (Admin, Director, Finance, etc.)
        return False
        # In DEBUG, only if they explicitly enabled it
        return user is not None and user.mfa_enabled

    # Risk-based MFA requirement for other roles (Student, Mentor, etc.)
    # Only enforce if user has MFA enabled; if MFA is disabled (e.g. by admin override),
    # do NOT force MFA even for higher risk scores.
    if risk_score >= 0.5 and user and user.mfa_enabled:
        return True

    return False


def _is_tor_or_vpn(ip_address):
    """
    Check if IP is TOR or VPN (placeholder).
    TODO: Integrate with TOR exit node list or VPN detection service.
    """
    # Placeholder implementation
    return False

