"""
User views for DRF - User management endpoints.
"""
import os
import uuid

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db.models import Q
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from ..serializers import UserCreateSerializer, UserSerializer
from ..utils.permission_utils import can_manage_users

User = get_user_model()


class UserPagination(PageNumberPagination):
    """
    Custom pagination for UserViewSet that allows larger page sizes.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 1000  # Allow up to 1000 users per page for admin/director use cases


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for User model.
    """
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = UserPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    def get_queryset(self):
        """
        Filter users based on permissions and optional role filter.
        """
        user = self.request.user
        queryset = None

        # Admin can see all users
        if user.is_staff:
            queryset = User.objects.all()
        else:
            # Program directors can see all users (for mentor assignment, etc.)
            from ..models import Role, UserRole
            director_roles = Role.objects.filter(name__in=['program_director', 'admin'])
            has_director_role = UserRole.objects.filter(
                user=user,
                role__in=director_roles,
                is_active=True
            ).exists()

            if has_director_role:
                queryset = User.objects.all()
            else:
                # Others can only see themselves
                queryset = User.objects.filter(id=user.id)

        # Filter by role if requested
        role_filter = self.request.query_params.get('role')
        if role_filter and queryset:
            from ..models import Role, UserRole
            try:
                role = Role.objects.get(name=role_filter)
                user_ids_with_role = UserRole.objects.filter(
                    role=role,
                    is_active=True
                ).values_list('user_id', flat=True)
                queryset = queryset.filter(id__in=user_ids_with_role)
            except Role.DoesNotExist:
                # If role doesn't exist, return empty queryset
                queryset = queryset.none()

        # Filter by search query if provided
        search_query = self.request.query_params.get('search')
        if search_query and queryset:
            queryset = queryset.filter(
                Q(email__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(username__icontains=search_query)
            )

        return queryset

    @action(detail=False, methods=['get'])
    def role_distribution(self, request):
        """
        GET /api/v1/users/role_distribution/
        Get role distribution statistics (admin only).
        Returns counts of users by role, total users, and active users.
        """
        # Only allow admin/staff users to access this endpoint
        if not request.user.is_staff:
            return Response(
                {'detail': 'Only administrators can access role distribution statistics'},
                status=status.HTTP_403_FORBIDDEN
            )


        from ..models import Role, UserRole

        # Get total and active user counts
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()

        # Get role distribution by counting active UserRole assignments
        role_distribution = {}

        # Get all roles and count active assignments
        roles = Role.objects.all()
        for role in roles:
            count = UserRole.objects.filter(
                role=role,
                is_active=True
            ).count()
            if count > 0:
                role_distribution[role.name] = count

        return Response({
            'role_distribution': role_distribution,
            'total_users': total_users,
            'active_users': active_users,
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='upload_avatar')
    def upload_avatar(self, request):
        """
        POST /api/v1/users/upload_avatar/
        Upload avatar for current user. Accepts multipart/form-data with 'avatar' file.
        """
        user = request.user
        avatar_file = request.FILES.get('avatar')
        if not avatar_file:
            return Response(
                {'error': 'No avatar file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
        if avatar_file.content_type not in allowed_types:
            return Response(
                {'error': 'Invalid file type. Use JPEG, PNG, GIF, or WebP'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if avatar_file.size > 5 * 1024 * 1024:  # 5MB
            return Response(
                {'error': 'File size must be under 5MB'},
                status=status.HTTP_400_BAD_REQUEST
            )
        ext = os.path.splitext(avatar_file.name)[1] or '.jpg'
        safe_name = f"{uuid.uuid4().hex}{ext}"
        path = os.path.join('avatars', str(user.id), safe_name)
        saved_path = default_storage.save(path, ContentFile(avatar_file.read()))
        url = default_storage.url(saved_path)
        if url.startswith('/'):
            url = request.build_absolute_uri(url)
        user.avatar_url = url
        user.save(update_fields=['avatar_url'])
        return Response({'avatar_url': url}, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        """
        Delete a user instance.
        Handles cases where related tables (like chat_messages) may not exist.
        """
        instance = self.get_object()

        # Check permissions using centralized utility
        user = request.user
        if not can_manage_users(user):
            return Response(
                {'detail': 'You do not have permission to delete users'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Prevent deleting yourself
        if instance.id == user.id:
            return Response(
                {'detail': 'You cannot delete your own account'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Delete related records first to avoid foreign key constraint violations
            user_id = instance.id

            # Delete user roles
            from ..models import UserRole
            try:
                UserRole.objects.filter(user_id=user_id).delete()
            except Exception:
                # If table doesn't exist or error, try raw SQL
                from django.db import connection
                try:
                    with connection.cursor() as cursor:
                        cursor.execute("DELETE FROM user_roles WHERE user_id = %s", [user_id])
                except Exception:
                    pass  # Table might not exist, continue

            # Delete consent scopes
            from ..models import ConsentScope
            try:
                ConsentScope.objects.filter(user_id=user_id).delete()
            except Exception:
                pass

            # Delete entitlements
            from ..models import Entitlement
            try:
                Entitlement.objects.filter(user_id=user_id).delete()
            except Exception:
                pass

            # Delete user sessions
            from ..auth_models import UserSession
            try:
                UserSession.objects.filter(user_id=user_id).delete()
            except Exception:
                pass

            # Delete MFA methods
            from ..auth_models import MFAMethod
            try:
                MFAMethod.objects.filter(user_id=user_id).delete()
            except Exception:
                pass

            # Delete user identities
            from ..identity_models import UserIdentity
            try:
                UserIdentity.objects.filter(user_id=user_id).delete()
            except Exception:
                pass

            # Delete or nullify audit logs (should be SET_NULL but handle deletion if needed)
            from ..audit_models import AuditLog
            try:
                # Set user to NULL in audit logs (as per model: on_delete=models.SET_NULL)
                AuditLog.objects.filter(user_id=user_id).update(user=None)
            except Exception:
                # If update fails, try to delete audit logs
                try:
                    AuditLog.objects.filter(user_id=user_id).delete()
                except Exception:
                    pass

            # Delete AI coach sessions (and messages via cascade) so user delete does not hit FK on ai_coach_sessions
            try:
                from coaching.models import AICoachSession
                AICoachSession.objects.filter(user_id=user_id).delete()
            except Exception:
                pass

            # Delete curriculum activities so user delete does not hit FK on curriculum_activities
            try:
                from curriculum.models import CurriculumActivity
                CurriculumActivity.objects.filter(user_id=user_id).delete()
            except Exception:
                pass

            # Delete all curriculum progress/bookmarks that reference this user
            try:
                from curriculum.models import (
                    CrossTrackProgramProgress,
                    CrossTrackSubmission,
                    UserContentProgress,
                    UserLessonBookmark,
                    UserLessonProgress,
                    UserMissionProgress,
                    UserModuleProgress,
                    UserTrackProgress,
                )
                UserLessonProgress.objects.filter(user_id=user_id).delete()
                UserLessonBookmark.objects.filter(user_id=user_id).delete()
                UserModuleProgress.objects.filter(user_id=user_id).delete()
                UserContentProgress.objects.filter(user_id=user_id).delete()
                UserTrackProgress.objects.filter(user_id=user_id).delete()
                UserMissionProgress.objects.filter(user_id=user_id).delete()
                CrossTrackSubmission.objects.filter(user_id=user_id).delete()
                CrossTrackProgramProgress.objects.filter(user_id=user_id).delete()
            except Exception:
                pass

            # Delete all coaching app records that reference this user (DB may not have ON DELETE CASCADE)
            try:
                from coaching.models import (
                    CoachingSession,
                    CommunityActivitySummary,
                    Goal,
                    Habit,
                    HabitLog,
                    MentorshipSession,
                    Reflection,
                    StudentAnalytics,
                    UserMissionProgress,
                    UserRecipeProgress,
                    UserTrackProgress,
                )
                StudentAnalytics.objects.filter(user_id=user_id).delete()
                CommunityActivitySummary.objects.filter(user_id=user_id).delete()
                UserRecipeProgress.objects.filter(user_id=user_id).delete()
                UserTrackProgress.objects.filter(user_id=user_id).delete()
                UserMissionProgress.objects.filter(user_id=user_id).delete()
                MentorshipSession.objects.filter(user_id=user_id).delete()
                CoachingSession.objects.filter(user_id=user_id).delete()
                HabitLog.objects.filter(habit__user_id=user_id).delete()
                Habit.objects.filter(user_id=user_id).delete()
                Goal.objects.filter(user_id=user_id).delete()
                Reflection.objects.filter(user_id=user_id).delete()
            except Exception:
                pass

            # Try to delete the user
            instance.delete()
        except Exception as e:
            # Handle case where related tables don't exist or other errors
            from django.db import IntegrityError, ProgrammingError, connection

            error_str = str(e)

            # Check if it's a foreign key constraint error
            if isinstance(e, IntegrityError) and 'foreign key constraint' in error_str.lower():
                # Try to delete using raw SQL with CASCADE
                try:
                    user_id = instance.id
                    with connection.cursor() as cursor:
                        # Delete related records manually
                        # Delete user_roles
                        try:
                            cursor.execute("DELETE FROM user_roles WHERE user_id = %s", [user_id])
                        except Exception:
                            pass

                        # Delete ai_coach_messages for this user's sessions, then ai_coach_sessions
                        try:
                            cursor.execute(
                                "DELETE FROM ai_coach_messages WHERE session_id IN (SELECT id FROM ai_coach_sessions WHERE user_id = %s)",
                                [user_id]
                            )
                            cursor.execute("DELETE FROM ai_coach_sessions WHERE user_id = %s", [user_id])
                        except Exception:
                            pass

                        # Delete curriculum_activities for this user
                        try:
                            cursor.execute("DELETE FROM curriculum_activities WHERE user_id = %s", [user_id])
                        except Exception:
                            pass

                        # Delete curriculum progress tables that reference users
                        for table in (
                            'user_lesson_progress',
                            'user_lesson_bookmarks',
                            'user_module_progress',
                            'user_content_progress',
                            'user_track_progress',
                            'user_curriculum_mission_progress',
                            'cross_track_submissions',
                            'cross_track_program_progress',
                        ):
                            try:
                                cursor.execute(f"DELETE FROM {table} WHERE user_id = %s", [user_id])
                            except Exception:
                                pass

                        # Delete coaching app tables that reference users (FK may not be CASCADE in DB)
                        for table in (
                            'coaching_habit_logs',  # before habits (references habit_id)
                            'coaching_habits',
                            'coaching_goals',
                            'coaching_reflections',
                            'coaching_student_analytics',
                            'coaching_community_activity_summary',
                            'coaching_user_recipe_progress',
                            'coaching_user_track_progress',
                            'coaching_user_mission_progress',
                            'coaching_mentorship_sessions',
                            'coaching_coaching_sessions',
                        ):
                            try:
                                cursor.execute(f"DELETE FROM {table} WHERE user_id = %s", [user_id])
                            except Exception:
                                pass

                        # Set audit_logs.user_id to NULL (as per model: SET_NULL)
                        # This preserves audit trail while removing user reference
                        try:
                            cursor.execute("UPDATE audit_logs SET user_id = NULL WHERE user_id = %s", [user_id])
                        except Exception:
                            # If update fails (constraint might not allow NULL), try delete as fallback
                            try:
                                cursor.execute("DELETE FROM audit_logs WHERE user_id = %s", [user_id])
                            except Exception:
                                pass

                        # Delete user directly
                        cursor.execute("DELETE FROM users WHERE id = %s", [user_id])
                        if cursor.rowcount == 0:
                            return Response(
                                {'detail': 'User not found'},
                                status=status.HTTP_404_NOT_FOUND
                            )

                    return Response(
                        {'detail': 'User deleted successfully'},
                        status=status.HTTP_200_OK
                    )
                except Exception as sql_err:
                    return Response(
                        {'detail': f'Failed to delete user: {str(sql_err)}'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            elif isinstance(e, ProgrammingError) or 'does not exist' in error_str.lower() or 'relation' in error_str.lower():
                # Table doesn't exist, delete user using raw SQL to bypass ORM checks
                try:
                    user_id = instance.id
                    with connection.cursor() as cursor:
                        # Delete ai_coach_sessions (and messages) so user delete does not hit FK
                        try:
                            cursor.execute(
                                "DELETE FROM ai_coach_messages WHERE session_id IN (SELECT id FROM ai_coach_sessions WHERE user_id = %s)",
                                [user_id]
                            )
                            cursor.execute("DELETE FROM ai_coach_sessions WHERE user_id = %s", [user_id])
                        except Exception:
                            pass

                        # Delete curriculum_activities for this user
                        try:
                            cursor.execute("DELETE FROM curriculum_activities WHERE user_id = %s", [user_id])
                        except Exception:
                            pass

                        # Delete curriculum progress tables that reference users
                        for table in (
                            'user_lesson_progress',
                            'user_lesson_bookmarks',
                            'user_module_progress',
                            'user_content_progress',
                            'user_track_progress',
                            'user_curriculum_mission_progress',
                            'cross_track_submissions',
                            'cross_track_program_progress',
                        ):
                            try:
                                cursor.execute(f"DELETE FROM {table} WHERE user_id = %s", [user_id])
                            except Exception:
                                pass

                        # Delete coaching app tables that reference users
                        for table in (
                            'coaching_habit_logs',
                            'coaching_habits',
                            'coaching_goals',
                            'coaching_reflections',
                            'coaching_student_analytics',
                            'coaching_community_activity_summary',
                            'coaching_user_recipe_progress',
                            'coaching_user_track_progress',
                            'coaching_user_mission_progress',
                            'coaching_mentorship_sessions',
                            'coaching_coaching_sessions',
                        ):
                            try:
                                cursor.execute(f"DELETE FROM {table} WHERE user_id = %s", [user_id])
                            except Exception:
                                pass

                        # Set audit_logs.user_id to NULL first (SET NULL)
                        try:
                            cursor.execute("UPDATE audit_logs SET user_id = NULL WHERE user_id = %s", [user_id])
                        except Exception:
                            pass

                        # Delete user directly (CASCADE will handle related records in existing tables)
                        cursor.execute("DELETE FROM users WHERE id = %s", [user_id])
                        if cursor.rowcount == 0:
                            return Response(
                                {'detail': 'User not found'},
                                status=status.HTTP_404_NOT_FOUND
                            )

                    return Response(
                        {'detail': 'User deleted successfully'},
                        status=status.HTTP_200_OK
                    )
                except Exception as sql_err:
                    return Response(
                        {'detail': f'Failed to delete user: {str(sql_err)}'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            else:
                # Other error, return error message
                return Response(
                    {'detail': f'Failed to delete user: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(
            {'detail': 'User deleted successfully'},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Get current user profile.
        """
        self.get_serializer(request.user)
