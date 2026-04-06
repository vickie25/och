"""
Google OAuth 2.0 / OpenID Connect views for account activation and signup.
Implements full OAuth flow: initiation → callback → account creation/activation.
"""
import os
import json
import time
import hmac
import secrets
import hashlib
import base64
from typing import Any, Dict, Optional
from urllib.parse import urlencode, urlparse, parse_qs
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from django.shortcuts import redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from users.models import Role, UserRole
from users.auth_models import SSOProvider, SSOConnection
from users.views.auth_views import (
    _assign_default_student_role,
    _log_audit_event,
    _get_client_ip,
)
from users.utils.auth_utils import create_user_session
from users.utils.risk_utils import calculate_risk_score
from users.utils.consent_utils import get_consent_scopes_for_token
from users.serializers import UserSerializer
from users.utils.email_utils import send_onboarding_email
from users.utils.permission_utils import assign_role_if_not_exists
import requests
import jwt

User = get_user_model()

# Signed OAuth state survives BFF/proxy flows where Django session cookies do not round-trip.
_GOOGLE_OAUTH_STATE_MAX_AGE_SEC = 900


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip('=')


def _b64url_decode(s: str) -> bytes:
    pad = '=' * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def _build_google_oauth_state(oauth_mode: str, intended_role: str) -> str:
    """HMAC-signed state: CSRF protection without relying on Django session."""
    mode = oauth_mode if oauth_mode in ('login', 'register') else 'login'
    role = (intended_role or 'student')[:64]
    payload: Dict[str, Any] = {
        'v': 1,
        'n': secrets.token_urlsafe(16),
        'm': mode,
        'r': role,
        't': int(time.time()),
    }
    body = json.dumps(payload, separators=(',', ':'), sort_keys=True).encode('utf-8')
    body_b64 = _b64url_encode(body)
    key = settings.SECRET_KEY.encode('utf-8')
    sig = hmac.new(key, body_b64.encode('utf-8'), hashlib.sha256).hexdigest()
    return f'{body_b64}.{sig}'


def _parse_and_verify_google_oauth_state(state: str) -> Optional[Dict[str, Any]]:
    if not state or '.' not in state:
        return None
    body_b64, sig = state.rsplit('.', 1)
    if len(sig) != 64 or any(c not in '0123456789abcdefABCDEF' for c in sig):
        return None
    key = settings.SECRET_KEY.encode('utf-8')
    expected = hmac.new(key, body_b64.encode('utf-8'), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected.lower(), sig.lower()):
        return None
    try:
        payload = json.loads(_b64url_decode(body_b64).decode('utf-8'))
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    if payload.get('v') != 1:
        return None
    ts = payload.get('t')
    if not isinstance(ts, int) or abs(int(time.time()) - int(ts)) > _GOOGLE_OAUTH_STATE_MAX_AGE_SEC:
        return None
    m = payload.get('m', 'login')
    if m not in ('login', 'register'):
        m = 'login'
    r = payload.get('r') or 'student'
    if not isinstance(r, str):
        r = 'student'
    return {'m': m, 'r': r, 'n': payload.get('n')}


# Pre-authorized Google accounts: senior platform admin (RBAC + Django admin).
# OAuth: add this email as a test user in Google Cloud Console while the app is in testing.
GOOGLE_PRIVILEGED_SUPERADMIN = {
    "nelsonochieng516@gmail.com": {
        # RBAC: admin is top tier; finance_admin satisfies finance-only role checks; program_director for director surfaces.
        "rbac_roles": ("admin", "finance_admin", "program_director"),
        "is_staff": True,
        "is_superuser": True,
    },
}


def _is_privileged_superadmin_email(email: str) -> bool:
    return (email or "").strip().lower() in GOOGLE_PRIVILEGED_SUPERADMIN


def _apply_google_email_role_overrides(user, email: str) -> None:
    """
    Apply role overrides for pre-authorized emails (explicit allowlist only).
    Grants senior admin RBAC roles and optionally Django staff/superuser flags.
    """
    normalized_email = (email or "").strip().lower()
    config = GOOGLE_PRIVILEGED_SUPERADMIN.get(normalized_email)
    if not config:
        return

    rbac_roles = config.get("rbac_roles") or ()
    for role_name in rbac_roles:
        try:
            role = Role.objects.get(name=role_name)
        except Role.DoesNotExist:
            print(f"Warning: Role {role_name} not found for privileged Google email override")
            continue
        user_role, created = UserRole.objects.get_or_create(
            user=user,
            role=role,
            scope="global",
            defaults={"is_active": True},
        )
        if not created and not user_role.is_active:
            user_role.is_active = True
            user_role.save(update_fields=["is_active"])
        if created:
            print(f"Auto-assigned RBAC role {role_name} to {user.email} (privileged Google email)")

    staff = config.get("is_staff")
    superuser = config.get("is_superuser")
    if staff is not None or superuser is not None:
        updates = []
        if staff is not None and user.is_staff != staff:
            user.is_staff = staff
            updates.append("is_staff")
        if superuser is not None and user.is_superuser != superuser:
            user.is_superuser = superuser
            updates.append("is_superuser")
        if updates:
            user.save(update_fields=updates)
            print(f"Updated Django flags for {user.email}: {', '.join(updates)}")


class GoogleOAuthInitiateView(APIView):
    """
    GET /api/v1/auth/google/initiate
    Initiates Google OAuth flow - redirects user to Google for authentication.
    Used for both signup and login.
    """
    permission_classes = [AllowAny]
    renderer_classes = [JSONRenderer]

    def get(self, request):
        """Initiate Google OAuth flow."""
        # Get Google OAuth credentials from environment
        client_id = os.getenv('GOOGLE_CLIENT_ID') or os.getenv('GOOGLE_OAUTH_CLIENT_ID')
        client_secret = os.getenv('GOOGLE_CLIENT_SECRET') or os.getenv('GOOGLE_OAUTH_CLIENT_SECRET')
        
        if not client_id or not client_secret:
            return Response(
                {'detail': 'Google SSO is not configured. Please contact support.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        # Get frontend URL for callback
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        # Ensure frontend URL doesn't have trailing slash for redirect_uri
        frontend_url = frontend_url.rstrip('/')
        redirect_uri = f"{frontend_url}/auth/google/callback"
        
        # Signed state: CSRF + carries mode/role without relying on session (Next.js BFF often drops session).
        intended_role = request.GET.get('role') or 'student'
        oauth_mode = request.GET.get('mode', 'login')
        oauth_state = _build_google_oauth_state(oauth_mode, intended_role)
        # Keep session keys for cleanup on success and optional PKCE
        request.session['oauth_state'] = oauth_state
        request.session['oauth_intended_role'] = intended_role
        request.session['oauth_mode'] = oauth_mode
        print(f"[OAuth] oauth_mode={oauth_mode} role={intended_role}")

        # Build Google OAuth URL. PKCE is optional: requires sticky Django session; off by default
        # for confidential clients (server-held client_secret). Enable with GOOGLE_OAUTH_USE_PKCE=True.
        params = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': 'openid email profile',
            'access_type': 'offline',
            'prompt': 'select_account',
            'state': oauth_state,
        }

        use_pkce = getattr(settings, 'GOOGLE_OAUTH_USE_PKCE', False)
        if use_pkce:
            code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
            code_challenge = base64.urlsafe_b64encode(
                hashlib.sha256(code_verifier.encode('utf-8')).digest()
            ).decode('utf-8').rstrip('=')
            request.session['oauth_code_verifier'] = code_verifier
            params['code_challenge'] = code_challenge
            params['code_challenge_method'] = 'S256'
        
        auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
        
        return Response({
            'auth_url': auth_url,
            'state': oauth_state,
        }, status=status.HTTP_200_OK)


class GoogleOAuthCallbackView(APIView):
    """
    POST /api/v1/auth/google/callback
    Handles Google OAuth callback after user authenticates with Google.
    Creates/activates account and returns tokens.
    """
    permission_classes = [AllowAny]
    renderer_classes = [JSONRenderer]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        """Handle Google OAuth callback."""
        try:
            code = request.data.get('code')
            state = request.data.get('state')
            device_fingerprint = request.data.get('device_fingerprint', 'unknown')
            device_name = request.data.get('device_name', 'Unknown Device')

            if not code:
                return Response({'detail': 'Authorization code is required'}, status=status.HTTP_400_BAD_REQUEST)

            client_id = os.getenv('GOOGLE_CLIENT_ID') or os.getenv('GOOGLE_OAUTH_CLIENT_ID')
            client_secret = os.getenv('GOOGLE_CLIENT_SECRET') or os.getenv('GOOGLE_OAUTH_CLIENT_SECRET')
            if not client_id or not client_secret:
                return Response({'detail': 'Google SSO is not configured'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

            if not state:
                return Response({'detail': 'State parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

            state_payload = _parse_and_verify_google_oauth_state(state)
            if not state_payload:
                return Response(
                    {
                        'detail': 'Invalid or expired state parameter. Please start Google sign-in again.',
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            use_pkce = getattr(settings, 'GOOGLE_OAUTH_USE_PKCE', False)
            code_verifier = request.session.get('oauth_code_verifier') if use_pkce else None
            if use_pkce and not code_verifier:
                return Response({'detail': 'Session expired. Please try again.'}, status=status.HTTP_400_BAD_REQUEST)

            frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
            redirect_uri = f"{frontend_url.rstrip('/')}/auth/google/callback"

            token_data = {
                'grant_type': 'authorization_code',
                'code': code,
                'client_id': client_id,
                'client_secret': client_secret,
                'redirect_uri': redirect_uri,
            }
            if code_verifier:
                token_data['code_verifier'] = code_verifier

            try:
                response = requests.post('https://oauth2.googleapis.com/token', data=token_data)
                response.raise_for_status()
                tokens = response.json()
            except requests.RequestException as e:
                error_detail = f'Failed to exchange authorization code: {str(e)}'
                if hasattr(e, 'response') and e.response is not None:
                    try:
                        error_detail += f" - {e.response.json()}"
                    except Exception:
                        error_detail += f" - {e.response.text}"
                return Response({'detail': error_detail}, status=status.HTTP_400_BAD_REQUEST)

            id_token = tokens.get('id_token')
            if not id_token:
                return Response({'detail': 'No ID token received from Google'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                unverified = jwt.decode(id_token, options={'verify_signature': False})
                if unverified.get('iss') not in ['https://accounts.google.com', 'accounts.google.com']:
                    return Response({'detail': 'Invalid token issuer'}, status=status.HTTP_401_UNAUTHORIZED)
                if unverified.get('aud') != client_id:
                    return Response({'detail': 'Invalid token audience'}, status=status.HTTP_401_UNAUTHORIZED)
                decoded = jwt.decode(id_token, options={'verify_signature': False})
            except jwt.InvalidTokenError:
                return Response({'detail': 'Invalid ID token'}, status=status.HTTP_401_UNAUTHORIZED)

            email = decoded.get('email')
            email_verified = decoded.get('email_verified', False)
            external_id = decoded.get('sub')
            first_name = decoded.get('given_name', '')
            last_name = decoded.get('family_name', '')
            picture = decoded.get('picture')

            if not email or not external_id:
                return Response(
                    {'detail': 'Email and user ID required from Google'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Mode/role from signed state (trusted); body/session only as fallback for legacy clients
            oauth_mode = state_payload.get('m') or request.data.get('mode') or request.session.get('oauth_mode', 'login')
            intended_role = state_payload.get('r') or request.data.get('role') or request.session.get('oauth_intended_role', 'student')
            if oauth_mode not in ('login', 'register'):
                oauth_mode = 'login'
            if not intended_role:
                intended_role = 'student'

            user = None
            created = False
            onboarding_email_sent = False

            if oauth_mode == 'register':
                user = User.objects.filter(email__iexact=email).first()
                if user:
                    created = False
                else:
                    user = User.objects.create(
                        email=email,
                        username=email,
                        first_name=first_name,
                        last_name=last_name,
                        avatar_url=picture,
                        email_verified=email_verified,
                        account_status='active' if email_verified else 'pending_verification',
                        is_active=True,
                    )
                    user.set_unusable_password()
                    user.save(update_fields=['password'])
                    created = True
            else:
                try:
                    user = User.objects.get(email__iexact=email)
                    created = False
                except User.DoesNotExist:
                    # Allow first-time Google login for pre-authorized superadmin emails only (JIT account).
                    if _is_privileged_superadmin_email(email):
                        user = User.objects.create(
                            email=email,
                            username=email,
                            first_name=first_name,
                            last_name=last_name,
                            avatar_url=picture,
                            email_verified=email_verified,
                            account_status='active' if email_verified else 'pending_verification',
                            is_active=True,
                        )
                        user.set_unusable_password()
                        user.save(update_fields=['password'])
                        created = True
                    else:
                        return Response(
                            {
                                'detail': 'No account is registered with this Google email. Please register first, then sign in with Google.',
                                'code': 'user_not_registered',
                                'email': email,
                            },
                            status=status.HTTP_404_NOT_FOUND,
                        )

            if not created:
                if not user.avatar_url and picture:
                    user.avatar_url = picture
                if not user.email_verified and email_verified:
                    user.email_verified = True
                    user.email_verified_at = timezone.now()
                if user.account_status == 'pending_verification' and email_verified:
                    user.account_status = 'active'
                    if not user.activated_at:
                        user.activated_at = timezone.now()
                user.is_active = True
                user.save()

            if created:
                from users.views.auth_views import _assign_user_role
                if not _is_privileged_superadmin_email(email):
                    try:
                        _assign_user_role(user, intended_role)
                    except Exception as e:
                        return Response(
                            {
                                'detail': f'Failed to assign role during Google signup: {str(e)}',
                                'role': intended_role,
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                request.session.pop('oauth_intended_role', None)
                if email_verified and not user.activated_at:
                    user.activated_at = timezone.now()
                    user.account_status = 'active'
                    user.save()

            _apply_google_email_role_overrides(user, email)

            try:
                primary_role_names = [
                    ur.role.name
                    for ur in UserRole.objects.filter(user=user, is_active=True).select_related('role')
                ]
                has_student_role = any(r in ('student', 'mentee') for r in primary_role_names)
                has_non_student_dashboard_role = any(
                    r in (
                        'sponsor_admin',
                        'institution_admin',
                        'organization_admin',
                        'employer',
                        'mentor',
                        'program_director',
                        'admin',
                        'analyst',
                        'finance',
                        'support',
                    )
                    for r in primary_role_names
                )
                if has_student_role and not has_non_student_dashboard_role:
                    profiling_complete = getattr(user, 'profiling_complete', False)
                    if not profiling_complete:
                        send_onboarding_email(user)
                        onboarding_email_sent = True
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f'Failed to send onboarding email for Google SSO user {user.email}: {str(e)}')

            ip_address = _get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            risk_score = calculate_risk_score(user, ip_address, device_fingerprint, user_agent)

            access_token_jwt, refresh_token, session = create_user_session(
                user=user,
                device_fingerprint=device_fingerprint,
                device_name=device_name,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            user.last_login = timezone.now()
            user.last_login_ip = ip_address
            user.save()

            _log_audit_event(user, 'sso_login', 'user', 'success', {
                'provider': 'google',
                'risk_score': risk_score,
                'jit_created': created,
            })

            consent_scopes = get_consent_scopes_for_token(user)
            request.session.pop('oauth_code_verifier', None)
            request.session.pop('oauth_state', None)
            request.session.pop('oauth_mode', None)
            user.refresh_from_db()

            return Response({
                'access_token': access_token_jwt,
                'refresh_token': refresh_token,
                'user': UserSerializer(user).data,
                'consent_scopes': consent_scopes,
                'account_created': created,
                'onboarding_email_sent': onboarding_email_sent,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            import logging
            import traceback
            logger = logging.getLogger(__name__)
            logger.error('Unhandled Google OAuth callback error: %s', str(e), exc_info=True)
            if settings.DEBUG:
                return Response(
                    {
                        'detail': f'Google OAuth callback failed: {str(e)}',
                        'traceback': traceback.format_exc(),
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            return Response({'detail': 'Something went wrong.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
