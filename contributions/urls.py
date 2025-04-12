# contributions/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MonthlyContributionViewSet, ShareCapitalViewSet, RecalculateSharesView

# Create a router for viewsets
router = DefaultRouter()
router.register(r'monthly', MonthlyContributionViewSet)
router.register(r'share-capital', ShareCapitalViewSet)

urlpatterns = [
    # Include the router URLs
    path('', include(router.urls)),
    
    # Recalculate shares
    path('recalculate-shares/', RecalculateSharesView.as_view(), name='recalculate-shares'),
]