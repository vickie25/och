"""
Google OAuth 2.0 / OpenID Connect views for account activation and signup.
Implements full OAuth flow: initiation → callback → account creation/activation.
"""
import os
import secrets
import hashlib
import base64
from urllib.parse import urlencode, urlparse, parse_qs
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
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


def _apply_google_email_role_overrides(user, email: str) -> None:
    """
    Apply role overrides based on verified email domains.
    Only for specific pre-authorized admin emails - permissions are granted by admin.
    """
    normalized_email = (email or "").strip().lower()
    
    # Only individual email mappings for specific pre-authorized users
    # No domain-based auto-assignments - permissions must be granted by admin
    individual_email_mappings = {
        "nelsonochieng516@gmail.com": "sponsor_admin",
    }
    
    # Check individual mappings only
    role_name = individual_email_mappings.get(normalized_email)
    
    if not role_name:
        return  # No mapping applies
    
    # Get or create the role
    from users.models import Role, UserRole
    try:
        role = Role.objects.get(name=role_name)
    except Role.DoesNotExist:
        print(f"Warning: Role {role_name} not found for email override")
        return
    
    # Assign the role if not already assigned
    user_role, created = UserRole.objects.get_or_create(
        user=user,
        role=role,
        scope='global',
        defaults={'is_active': True}
    )
    
    if created:
        print(f"Auto-assigned role {role_name} to user {user.email} based on pre-authorized email")


class GoogleOAuthInitiateView(APIView):
    """
    GET /api/v1/auth/google/initiate
    Initiates Google OAuth flow - redirects user to Google for authentication.
    Used for both signup and login.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        """Initiate Google OAuth flow."""
        # Get Google OAuth credentials from environment
        client_id = os.getenv('GOOGLE_CLIENT_ID') or os.getenv('GOOGLE_OAUTH_CLIENT_ID')
        client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        
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
        
        # Generate state for CSRF protection
        oauth_state = secrets.token_urlsafe(32)
        request.session['oauth_state'] = oauth_state

        # Store intended role for signup (if provided)
        intended_role = request.GET.get('role')
        if intended_role:
            request.session['oauth_intended_role'] = intended_role
            print(f"[OAuth] Stored intended role for signup: {intended_role}")

        # Store OAuth mode: 'login' (default) vs 'register'
        oauth_mode = request.GET.get('mode', 'login')
        request.session['oauth_mode'] = oauth_mode
        print(f"[OAuth] Stored oauth_mode: {oauth_mode}")
        
        # Build Google OAuth authorization URL WITHOUT PKCE in development
        # PKCE doesn't work well with session-based storage in stateless APIs
        params = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': 'openid email profile',
            'access_type': 'offline',
            'prompt': 'select_account',
            'state': oauth_state,
        }
        
        # Only use PKCE in production with proper session management
        if not settings.DEBUG:
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
            client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
            if not client_id or not client_secret:
                return Response({'detail': 'Google SSO is not configured'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

            if not state:
                return Response({'detail': 'State parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

            session_state = request.session.get('oauth_state')
            if settings.DEBUG and session_state != state:
                print('[OAuth Debug] Session state mismatch (dev mode allows this)')
            elif not settings.DEBUG and session_state != state:
                return Response(
                    {'detail': 'Invalid state parameter. Possible CSRF attack.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            code_verifier = request.session.get('oauth_code_verifier')
            if not code_verifier and not settings.DEBUG:
                return Response({'detail': 'Session expired. Please try again.'}, status=status.HTTP_400_BAD_REQUEST)
            if settings.DEBUG:
                code_verifier = None

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

            oauth_mode = request.data.get('mode') or request.session.get('oauth_mode', 'login')
            intended_role = request.data.get('role') or request.session.get('oauth_intended_role', 'student')
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


@api_view(['GET'])
@permission_classes([AllowAny])
def google_oauth_initiate(request):
    """GET /api/v1/auth/google/initiate - Convenience endpoint"""
    view = GoogleOAuthInitiateView()
    return view.get(request)


@api_view(['POST'])
@permission_classes([AllowAny])
def google_oauth_callback(request):
    """POST /api/v1/auth/google/callback - Convenience endpoint"""
    view = GoogleOAuthCallbackView()
    return view.post(request)
