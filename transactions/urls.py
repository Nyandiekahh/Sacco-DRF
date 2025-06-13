# transactions/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SaccoExpenseViewSet,
    SaccoIncomeViewSet,
    TransactionBatchViewSet,
    BankAccountViewSet,
    BankTransactionViewSet
)
# Import the financial summary view from members app
from members.views import MemberFinancialSummaryView

# Create a router for viewsets
router = DefaultRouter()
router.register(r'expenses', SaccoExpenseViewSet, basename='expense')
router.register(r'income', SaccoIncomeViewSet, basename='income')
router.register(r'batches', TransactionBatchViewSet, basename='transaction-batch')
router.register(r'bank-accounts', BankAccountViewSet, basename='bank-account')
router.register(r'bank-transactions', BankTransactionViewSet, basename='bank-transaction')

urlpatterns = [
    # Include the router URLs
    path('', include(router.urls)),
    
    # Add the total investments endpoint that transactionService.calculateTotalInvestments() expects
    path('total-investments/', MemberFinancialSummaryView.as_view(), name='total-investments'),
]