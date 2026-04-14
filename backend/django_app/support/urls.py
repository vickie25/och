from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ProblemCodeViewSet, SupportTicketViewSet, impersonate_user, redeem_impersonation

router = DefaultRouter()
router.register(r'problem-codes', ProblemCodeViewSet, basename='problemcode')
router.register(r'tickets', SupportTicketViewSet, basename='supportticket')

urlpatterns = [
    path('impersonate/<int:user_id>/', impersonate_user, name='support-impersonate'),
    path('impersonate/redeem/', redeem_impersonation, name='support-impersonate-redeem'),
    path('', include(router.urls)),
]
