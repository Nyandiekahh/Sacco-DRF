# members/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MemberViewSet, MemberDashboardView, MemberProfileView

# Create a router for viewsets
router = DefaultRouter()
router.register(r'members', MemberViewSet)

urlpatterns = [
    # Include the router URLs
    path('', include(router.urls)),
    
    # Member dashboard
    path('dashboard/', MemberDashboardView.as_view(), name='member-dashboard'),
    
    # Member profile
    path('profile/', MemberProfileView.as_view(), name='member-profile'),
]