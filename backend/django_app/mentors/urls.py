"""
Mentor Dashboard URLs
Complete mentor command center API routes.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

# Create router for ViewSets
router = DefaultRouter()

# Register ViewSets
router.register(
    r'(?P<mentor_slug>[^/.]+)/students/(?P<student_id>\d+)/notes',
    views.MentorStudentNoteViewSet,
    basename='mentor-student-notes'
)

router.register(
    r'(?P<mentor_slug>[^/.]+)/schedule',
    views.MentorSessionViewSet,
    basename='mentor-sessions'
)

# URL patterns
urlpatterns = [
    # Main dashboard
    path('<str:mentor_slug>/dashboard/', views.MentorDashboardView.as_view(), name='mentor-dashboard'),

    # Student detail view
    path('<str:mentor_slug>/students/<int:student_id>/', views.MentorStudentDetailView.as_view(), name='mentor-student-detail'),

    # Boost/intervention actions
    path('<str:mentor_slug>/boost/', views.MentorBoostView.as_view(), name='mentor-boost'),

    # Student rating (for credits)
    path('<str:mentor_slug>/rate/', views.StudentRateMentorView.as_view(), name='mentor-rate'),

    # Mentor credits
    path('<str:mentor_slug>/credits/', views.MentorCreditsView.as_view(), name='mentor-credits'),
    path('<str:mentor_slug>/credits/redeem/', views.MentorRedeemCreditsView.as_view(), name='mentor-redeem-credits'),
    path('credit-options/', views.MentorCreditOptionsView.as_view(), name='mentor-credit-options'),

    # Include router URLs
    path('', include(router.urls)),
]
