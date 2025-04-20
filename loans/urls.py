from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LoanApplicationViewSet, 
    LoanViewSet, 
    LoanEligibilityView,
    PaymentMethodViewSet,
    LoanDisbursementView,
    LoanRepaymentView,
    EligibleGuarantorsView,
    GuarantorRequestViewSet
)

# Create a router for viewsets
router = DefaultRouter()
router.register(r'applications', LoanApplicationViewSet, basename='loan-application')
router.register(r'loans', LoanViewSet, basename='loan')
router.register(r'payment-methods', PaymentMethodViewSet, basename='payment-method')

urlpatterns = [
    # Include the router URLs
    path('', include(router.urls)),
    
    # Loan eligibility
    path('eligibility/', LoanEligibilityView.as_view(), name='loan-eligibility'),
    
    # Enhanced loan disbursement
    path('loans/<uuid:loan_id>/disburse/', LoanDisbursementView.as_view(), name='loan-disburse'),
    
    # Enhanced loan repayment
    path('loans/<uuid:loan_id>/repay/', LoanRepaymentView.as_view(), name='loan-repay'),
    
    # Payment method endpoints
    path('payment-methods/verify/<str:method>/', 
         PaymentMethodViewSet.as_view({'post': 'verify_payment_method'}), 
         name='verify-payment-method'),
    
    # Loan statistics
    path('stats/', LoanViewSet.as_view({'get': 'stats'}), name='loan-stats'),
    
    # Due payments (already implemented, including for clarity)
    path('due-payments/', LoanViewSet.as_view({'get': 'due_payments'}), name='due-payments'),
    
    # Bank accounts (for disbursement)
    path('bank-accounts/', LoanViewSet.as_view({'get': 'bank_accounts'}), name='bank-accounts'),
    
    # Guarantor endpoints
    path('eligible-guarantors/', EligibleGuarantorsView.as_view(), name='eligible-guarantors'),
    path('guarantor-requests/', GuarantorRequestViewSet.as_view({'get': 'list', 'post': 'create'}), name='guarantor-requests'),
    path('guarantor-requests/pending/', GuarantorRequestViewSet.as_view({'get': 'pending'}), name='pending-guarantor-requests'),
    path('guarantor-requests/<uuid:pk>/', GuarantorRequestViewSet.as_view({'get': 'retrieve'}), name='guarantor-request-detail'),
    path('guarantor-requests/<uuid:pk>/accept/', GuarantorRequestViewSet.as_view({'post': 'accept'}), name='accept-guarantor-request'),
    path('guarantor-requests/<uuid:pk>/reject/', GuarantorRequestViewSet.as_view({'post': 'reject'}), name='reject-guarantor-request'),
]