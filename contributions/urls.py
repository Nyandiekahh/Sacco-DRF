# contributions/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MonthlyContributionViewSet, 
    ShareCapitalViewSet, 
    RecalculateSharesView,
    MemberContributionViewSet,
    MemberShareCapitalViewSet
)

# Create a router for viewsets
router = DefaultRouter()
router.register(r'monthly', MonthlyContributionViewSet)
router.register(r'share-capital', ShareCapitalViewSet)
router.register(r'member/monthly', MemberContributionViewSet, basename='member-monthly')
router.register(r'member/share-capital', MemberShareCapitalViewSet, basename='member-share-capital')

urlpatterns = [
    # Include the router URLs
    path('', include(router.urls)),
    
    # Recalculate shares
    path('recalculate-shares/', RecalculateSharesView.as_view(), name='recalculate-shares'),
]