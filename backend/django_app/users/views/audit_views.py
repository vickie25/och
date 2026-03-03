"""
Audit log views for compliance and security monitoring.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.utils import timezone
from django.db.models import Q
from users.audit_models import AuditLog
from users.serializers import AuditLogSerializer
from users.models import Role, UserRole


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/v1/audit-logs
    List audit logs (admin and program directors).
    """
    queryset = AuditLog.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AuditLogSerializer
    
    def get_queryset(self):
        """Filter audit logs based on user permissions and query params."""
        user = self.request.user

        # Admins can see all logs. Program directors can see director-relevant logs.
        # Support can see logs for a specific user only (when user_id is provided).
        is_admin = user.is_staff or user.is_superuser
        director_role = Role.objects.filter(name='program_director').first()
        is_director = False
        if director_role:
            is_director = UserRole.objects.filter(user=user, role=director_role, is_active=True).exists()
        support_role = Role.objects.filter(name='support').first()
        is_support = False
        if support_role:
            is_support = UserRole.objects.filter(user=user, role=support_role, is_active=True).exists()

        if is_admin:
            queryset = AuditLog.objects.all()
        elif is_director:
            queryset = AuditLog.objects.filter(
                resource_type__in=[
                    'program', 'cohort', 'track', 'milestone', 'module',
                    'enrollment', 'mentor_assignment', 'mission',
                ]
            )
        elif is_support:
            # Support may only view logs for a specific user (user_id query param required)
            user_id_param = self.request.query_params.get('user_id')
            if not user_id_param:
                raise PermissionDenied('Support must filter by user_id to view audit logs.')
            try:
                uid = int(user_id_param)
                queryset = AuditLog.objects.filter(user_id=uid)
            except (ValueError, TypeError):
                raise PermissionDenied('Invalid user_id.')
        else:
            # Users may view their own audit log only (user_id must be their own)
            user_id_param = self.request.query_params.get('user_id')
            try:
                uid = int(user_id_param) if user_id_param else None
                if uid is not None and uid == user.id:
                    queryset = AuditLog.objects.filter(user_id=uid)
                else:
                    raise PermissionDenied('You do not have permission to view these audit logs.')
            except (ValueError, TypeError):
                raise PermissionDenied('Invalid user_id.')
        
        # Filter by actor (actor_identifier or user ID)
        actor = self.request.query_params.get('actor')
        user_id = self.request.query_params.get('user_id')
        if user_id:
            try:
                queryset = queryset.filter(user_id=int(user_id))
            except (ValueError, TypeError):
                pass
        elif actor:
            queryset = queryset.filter(actor_identifier__icontains=actor)
        
        # Filter by entity (resource_type or resource_id)
        entity = self.request.query_params.get('entity')
        if entity:
            queryset = queryset.filter(
                Q(resource_type__icontains=entity) | 
                Q(resource_id__icontains=entity)
            )
        
        # Filter by date range (support 'range' parameter for common ranges)
        range_param = self.request.query_params.get('range')
        if range_param:
            from datetime import timedelta
            now = timezone.now()
            if range_param == 'today':
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                queryset = queryset.filter(timestamp__gte=start_date)
            elif range_param == 'week':
                start_date = now - timedelta(days=7)
                queryset = queryset.filter(timestamp__gte=start_date)
            elif range_param == 'month':
                start_date = now - timedelta(days=30)
                queryset = queryset.filter(timestamp__gte=start_date)
            elif range_param == 'year':
                start_date = now - timedelta(days=365)
                queryset = queryset.filter(timestamp__gte=start_date)
        
        # Also support explicit date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        
        # Filter by action
        action_filter = self.request.query_params.get('action')
        if action_filter:
            queryset = queryset.filter(action=action_filter)
        
        # Filter by resource type
        resource_type = self.request.query_params.get('resource_type')
        if resource_type:
            queryset = queryset.filter(resource_type=resource_type)

        # Support multiple resource types: ?resource_types=program,cohort,track
        resource_types = self.request.query_params.get('resource_types')
        if resource_types:
            types = [t.strip() for t in resource_types.split(',') if t.strip()]
            if types:
                queryset = queryset.filter(resource_type__in=types)
        
        # Filter by result
        result = self.request.query_params.get('result')
        if result:
            queryset = queryset.filter(result=result)
        
        return queryset.order_by('-timestamp')
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get audit log statistics."""
        queryset = self.get_queryset()
        
        total = queryset.count()
        success = queryset.filter(result='success').count()
        failure = queryset.filter(result='failure').count()
        
        # Group by action
        action_counts = {}
        for log in queryset.values('action').distinct():
            action = log['action']
            action_counts[action] = queryset.filter(action=action).count()
        
        return Response({
            'total': total,
            'success': success,
            'failure': failure,
            'action_counts': action_counts,
        })

