# loans/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LoanApplicationViewSet, LoanViewSet, LoanEligibilityView

# Create a router for viewsets
router = DefaultRouter()
router.register(r'applications', LoanApplicationViewSet, basename='loan-application')
router.register(r'loans', LoanViewSet, basename='loan')

urlpatterns = [
    # Include the router URLs
    path('', include(router.urls)),
    
    # Loan eligibility
    path('eligibility/', LoanEligibilityView.as_view(), name='loan-eligibility'),
]