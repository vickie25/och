
import secrets
import time

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.mail import send_mail
from django.db.models import Q
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from users.permissions import IsSupportOrDirectorOrAdmin
from users.utils.auth_utils import create_user_session

from .models import ProblemCode, SupportTicket, SupportTicketResponse
from .serializers import (
    ProblemCodeSerializer,
    SupportTicketCreateUpdateSerializer,
    SupportTicketDetailSerializer,
    SupportTicketListSerializer,
    SupportTicketResponseCreateSerializer,
    SupportTicketResponseSerializer,
)


class ProblemCodeViewSet(viewsets.ModelViewSet):
    """
    CRUD for problem tracking codes. List is available to support/director/admin.
    Create/update/delete typically for director/admin only; support can list and use.
    """
    queryset = ProblemCode.objects.all()
    serializer_class = ProblemCodeSerializer
    permission_classes = [IsSupportOrDirectorOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['code', 'name', 'description']
    ordering_fields = ['code', 'category', 'created_at']
    ordering = ['category', 'code']


class SupportTicketViewSet(viewsets.ModelViewSet):
    """
    Support tickets with problem code tracking.
    Staff (support/director/admin): full list, CRUD, assign, stats.
    Students: my-tickets (own only), create, retrieve (own only).
    """
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'priority', 'assigned_to', 'problem_code']
    search_fields = ['subject', 'description', 'reporter_email', 'reporter_name']
    ordering_fields = ['created_at', 'updated_at', 'priority', 'status']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action in ('my_tickets', 'create', 'retrieve', 'destroy'):
            return [IsAuthenticated()]
        return [IsSupportOrDirectorOrAdmin()]

    def _is_staff_for_tickets(self, user):
        if not user or not user.is_authenticated:
            return False
        if getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False):
            return True
        user_roles = getattr(user, 'user_roles', None)
        if not user_roles:
            return False
        return user_roles.filter(
            role__name__in=['support', 'program_director', 'admin'],
            is_active=True
        ).exists()

    def get_queryset(self):
        qs = SupportTicket.objects.select_related(
            'problem_code', 'assigned_to', 'created_by'
        ).prefetch_related('responses', 'attachments').all()
        if not self.request.user or not self.request.user.is_authenticated:
            return qs.none()
        if self._is_staff_for_tickets(self.request.user):
            return qs
        return qs.filter(
            Q(reporter_id=self.request.user.id) |
            Q(reporter_email__iexact=self.request.user.email)
        )

    def get_serializer_class(self):
        if self.action == 'list':
            return SupportTicketListSerializer
        if self.action in ('retrieve',):
            return SupportTicketDetailSerializer
        return SupportTicketCreateUpdateSerializer

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(
            created_by=user,
            reporter_id=user.id,
            reporter_email=user.email or '',
            reporter_name=getattr(user, 'get_full_name', lambda: '')().strip() or user.email or '',
        )

    @action(detail=False, methods=['get'], url_path='my-tickets')
    def my_tickets(self, request):
        """List tickets for the current user (students see own; staff see all)."""
        qs = self.filter_queryset(self.get_queryset())
        serializer = SupportTicketListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assign ticket to a user (support agent)."""
        ticket = self.get_object()
        user_id = request.data.get('assigned_to_id')
        if user_id is not None:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                user = User.objects.get(id=user_id)
                ticket.assigned_to = user
                ticket.save(update_fields=['assigned_to', 'updated_at'])
                return Response(SupportTicketDetailSerializer(ticket).data)
            except User.DoesNotExist:
                return Response({'detail': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        ticket.assigned_to = None
        ticket.save(update_fields=['assigned_to', 'updated_at'])
        return Response(SupportTicketDetailSerializer(ticket).data)

    @action(detail=True, methods=['get', 'post'], url_path='responses')
    def responses(self, request, pk=None):
        """List or create ticket replies. POST body: { message, send_copy_to_email?: boolean }."""
        ticket = self.get_object()
        if request.method == 'GET':
            qs = ticket.responses.all().order_by('created_at')
            serializer = SupportTicketResponseSerializer(qs, many=True)
            return Response(serializer.data)
        # POST
        ser = SupportTicketResponseCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = request.user
        is_staff = self._is_staff_for_tickets(user)
        created_by_name = (getattr(user, 'get_full_name', lambda: '')() or user.email or '').strip()
        resp = SupportTicketResponse.objects.create(
            ticket=ticket,
            message=ser.validated_data['message'],
            is_staff=is_staff,
            created_by=user,
            created_by_name=created_by_name,
        )
        send_copy = ser.validated_data.get('send_copy_to_email', False)
        if send_copy and ticket.reporter_email:
            try:
                subject = f'Re: [{ticket.subject}] – Support ticket #{ticket.id}'
                html_message = render_to_string('emails/support_ticket_reply.html', {
                    'ticket_id': ticket.id,
                    'ticket_subject': ticket.subject,
                    'reply_message': resp.message,
                    'created_by_name': created_by_name or 'Support',
                })
                plain_message = strip_tags(html_message).replace('\n\n', '\n').strip()
                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[ticket.reporter_email],
                    fail_silently=True,
                    html_message=html_message,
                )
            except Exception:
                pass
        return Response(SupportTicketResponseSerializer(resp).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Dashboard stats: counts by status and priority."""
        qs = SupportTicket.objects.all()
        by_status = {}
        for s in SupportTicket.STATUS_CHOICES:
            by_status[s[0]] = qs.filter(status=s[0]).count()
        by_priority = {}
        for p in SupportTicket.PRIORITY_CHOICES:
            by_priority[p[0]] = qs.filter(priority=p[0]).count()
        open_count = qs.filter(status__in=['open', 'in_progress', 'pending_customer']).count()
        return Response({
            'by_status': by_status,
            'by_priority': by_priority,
            'open_count': open_count,
            'total': qs.count(),
        })


User = get_user_model()

# In-memory fallback for impersonation codes when cache is DummyCache (e.g. local dev)
_impersonation_store = {}
_IMPERSONATION_TTL_SECONDS = 120


def _set_impersonation(code: str, payload: dict) -> None:
    cache.set(f'impersonate:{code}', payload, timeout=_IMPERSONATION_TTL_SECONDS)
    _impersonation_store[code] = (payload, time.monotonic() + _IMPERSONATION_TTL_SECONDS)


def _get_impersonation(code: str) -> dict | None:
    payload = cache.get(f'impersonate:{code}')
    if payload is not None:
        return payload
    if code in _impersonation_store:
        data, expires = _impersonation_store[code]
        if time.monotonic() <= expires:
            return data
        del _impersonation_store[code]
    return None


def _delete_impersonation(code: str) -> None:
    cache.delete(f'impersonate:{code}')
    _impersonation_store.pop(code, None)


@api_view(['POST'])
@permission_classes([IsSupportOrDirectorOrAdmin])
def impersonate_user(request, user_id):
    """
    Support/director/admin can obtain session tokens for a user (e.g. student) to log in as them.
    Opens in a new tab; the action is logged so the target user can see that support accessed their account.
    Returns { access_token, refresh_token } for the frontend to set cookies in the new tab.
    """
    if not request.user or not request.user.is_authenticated:
        return Response({'detail': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
    try:
        target = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return Response({'detail': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    if not target.is_active:
        return Response({'detail': 'User is inactive'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        device_fp = request.META.get('HTTP_USER_AGENT', '')[:200] or 'support-impersonation'
        access_token, refresh_token, session = create_user_session(
            user=target,
            device_fingerprint=device_fp,
            device_name='Support impersonation',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            mfa_verified=True,
            session_expires_minutes=40,
        )
    except ValueError as e:
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    # Log so the *target user* sees it when they view their activity (user=target)
    from django.utils import timezone

    from users.audit_models import AuditLog
    try:
        AuditLog.objects.create(
            user=target,
            actor_type='user',
            actor_identifier=request.user.email or str(request.user.id),
            action='login',
            resource_type='user',
            resource_id=str(target.id),
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            metadata={
                'impersonation': True,
                'by_user_id': request.user.id,
                'by_email': request.user.email or '',
                'by_name': getattr(request.user, 'get_full_name', lambda: '')().strip() or '',
            },
            result='success',
            timestamp=timezone.now(),
        )
    except Exception:
        pass
    # Minimal user for frontend (student identity so dashboard shows student, not support)
    user_payload = {
        'id': target.id,
        'email': target.email,
        'first_name': getattr(target, 'first_name', None) or '',
        'last_name': getattr(target, 'last_name', None) or '',
        'roles': [{'role': {'name': 'student'}}],
    }
    impersonation_expires_at = session.expires_at.isoformat() if session.expires_at else None
    payload = {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user_payload,
        'impersonation_expires_at': impersonation_expires_at,
    }
    code = secrets.token_urlsafe(32)
    _set_impersonation(code, payload)
    return Response({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'expires_in': 40 * 60,
        'user': user_payload,
        'impersonation_expires_at': impersonation_expires_at,
        'impersonation_code': code,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def redeem_impersonation(request):
    """
    One-time redeem of impersonation tokens by code (no auth).
    Popup calls this with ?code=xxx to get student tokens and set session.
    """
    code = (request.query_params.get('code') or '').strip()
    if not code:
        return Response({'detail': 'Missing code'}, status=status.HTTP_400_BAD_REQUEST)
    payload = _get_impersonation(code)
    if not payload:
        return Response({'detail': 'Invalid or expired code'}, status=status.HTTP_404_NOT_FOUND)
    _delete_impersonation(code)
    return Response(payload)
