# transactions/views.py

from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from authentication.models import SaccoUser, ActivityLog
from members.views import AdminRequiredMixin
from .models import (
    SaccoExpense, 
    SaccoIncome, 
    TransactionBatch, 
    BatchItem, 
    TransactionLog,
    BankAccount, 
    BankTransaction
)
from .serializers import (
    SaccoExpenseSerializer,
    SaccoIncomeSerializer,
    TransactionBatchSerializer,
    BatchItemSerializer,
    BankAccountSerializer,
    BankTransactionSerializer
)


class SaccoExpenseViewSet(AdminRequiredMixin, viewsets.ModelViewSet):
    """API endpoint for SACCO expenses - Admin only"""
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SaccoExpenseSerializer
    
    def get_queryset(self):
        queryset = SaccoExpense.objects.all()
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(expense_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(expense_date__lte=date_to)
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        return queryset.order_by('-expense_date')
    
    def perform_create(self, serializer):
        # Record who created the expense
        expense = serializer.save(recorded_by=self.request.user)
        
        # Log the activity
        ActivityLog.objects.create(
            user=self.request.user,
            action='EXPENSE_RECORD',
            ip_address=self.request.META.get('REMOTE_ADDR'),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            description=f"Recorded expense of {expense.amount} - {expense.get_category_display()}."
        )


class SaccoIncomeViewSet(AdminRequiredMixin, viewsets.ModelViewSet):
    """API endpoint for SACCO income - Admin only"""
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SaccoIncomeSerializer
    
    def get_queryset(self):
        queryset = SaccoIncome.objects.all()
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(income_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(income_date__lte=date_to)
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        return queryset.order_by('-income_date')
    
    def perform_create(self, serializer):
        # Record who created the income
        income = serializer.save(recorded_by=self.request.user)
        
        # Log the activity
        ActivityLog.objects.create(
            user=self.request.user,
            action='INCOME_RECORD',
            ip_address=self.request.META.get('REMOTE_ADDR'),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            description=f"Recorded income of {income.amount} - {income.get_category_display()}."
        )


class TransactionBatchViewSet(AdminRequiredMixin, viewsets.ModelViewSet):
    """API endpoint for transaction batches - Admin only"""
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TransactionBatchSerializer
    
    def get_queryset(self):
        queryset = TransactionBatch.objects.all()
        
        # Filter by batch type
        batch_type = self.request.query_params.get('batch_type')
        if batch_type:
            queryset = queryset.filter(batch_type=batch_type)
        
        # Filter by status
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(transaction_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(transaction_date__lte=date_to)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        # Record who created the batch
        batch = serializer.save(created_by=self.request.user)
        
        # Log the activity
        ActivityLog.objects.create(
            user=self.request.user,
            action='BATCH_CREATE',
            ip_address=self.request.META.get('REMOTE_ADDR'),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            description=f"Created {batch.get_batch_type_display()} batch with {batch.transaction_count} transactions."
        )
    
    @action(detail=True, methods=['post'])
    def process_batch(self, request, pk=None):
        """Process a transaction batch"""
        
        batch = self.get_object()
        
        # Check if batch is already processed
        if batch.status == 'COMPLETED':
            return Response({
                'status': 'error',
                'message': 'Batch is already processed'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update batch status
        batch.status = 'PROCESSING'
        batch.save()
        
        # Process batch items
        with transaction.atomic():
            batch_items = BatchItem.objects.filter(batch=batch, status='PENDING')
            processed_count = 0
            failed_count = 0
            
            for item in batch_items:
                try:
                    # Processing logic based on batch type
                    # This is simplified and would be more complex in a real system
                    item.status = 'PROCESSED'
                    item.processed_at = timezone.now()
                    item.save()
                    processed_count += 1
                except Exception as e:
                    item.status = 'FAILED'
                    item.error_message = str(e)
                    item.save()
                    failed_count += 1
            
            # Update batch
            batch.processed_count = processed_count
            batch.failed_count = failed_count
            batch.status = 'COMPLETED' if failed_count == 0 else 'FAILED'
            batch.processed_at = timezone.now()
            batch.save()
        
        # Log the activity
        ActivityLog.objects.create(
            user=request.user,
            action='BATCH_PROCESS',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            description=f"Processed batch: {processed_count} successful, {failed_count} failed."
        )
        
        return Response({
            'status': 'success',
            'message': f'Batch processed: {processed_count} successful, {failed_count} failed',
            'batch_id': str(batch.id),
            'processed_count': processed_count,
            'failed_count': failed_count
        })


class BankAccountViewSet(AdminRequiredMixin, viewsets.ModelViewSet):
    """API endpoint for bank accounts - Admin only"""
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BankAccountSerializer
    
    def get_queryset(self):
        queryset = BankAccount.objects.all()
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active)
        
        # Filter by primary status
        is_primary = self.request.query_params.get('is_primary')
        if is_primary is not None:
            is_primary = is_primary.lower() == 'true'
            queryset = queryset.filter(is_primary=is_primary)
        
        return queryset.order_by('-is_primary', 'bank_name')
    
    def perform_create(self, serializer):
        account = serializer.save()
        
        # Log the activity
        ActivityLog.objects.create(
            user=self.request.user,
            action='BANK_ACCOUNT_CREATE',
            ip_address=self.request.META.get('REMOTE_ADDR'),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            description=f"Created bank account: {account.bank_name} - {account.account_name}."
        )
    
    @action(detail=True, methods=['post'])
    def set_as_primary(self, request, pk=None):
        """Set this account as the primary account"""
        
        account = self.get_object()
        
        # Already primary
        if account.is_primary:
            return Response({
                'status': 'info',
                'message': 'This account is already the primary account'
            })
        
        # Update to primary
        account.is_primary = True
        account.save()  # This will handle removing primary from other accounts
        
        # Log the activity
        ActivityLog.objects.create(
            user=request.user,
            action='BANK_ACCOUNT_UPDATE',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            description=f"Set {account.bank_name} - {account.account_name} as primary account."
        )
        
        return Response({
            'status': 'success',
            'message': 'Account set as primary successfully'
        })


class BankTransactionViewSet(AdminRequiredMixin, viewsets.ModelViewSet):
    """API endpoint for bank transactions - Admin only"""
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BankTransactionSerializer
    
    def get_queryset(self):
        queryset = BankTransaction.objects.all()
        
        # Filter by account
        account_id = self.request.query_params.get('account_id')
        if account_id:
            queryset = queryset.filter(account_id=account_id)
        
        # Filter by transaction type
        transaction_type = self.request.query_params.get('transaction_type')
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
        
        # Filter by reconciliation status
        is_reconciled = self.request.query_params.get('is_reconciled')
        if is_reconciled is not None:
            is_reconciled = is_reconciled.lower() == 'true'
            queryset = queryset.filter(is_reconciled=is_reconciled)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(transaction_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(transaction_date__lte=date_to)
        
        return queryset.order_by('-transaction_date')
    
    def perform_create(self, serializer):
        transaction = serializer.save(recorded_by=self.request.user)
        
        # Log the activity
        ActivityLog.objects.create(
            user=self.request.user,
            action='BANK_TRANSACTION_RECORD',
            ip_address=self.request.META.get('REMOTE_ADDR'),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            description=f"Recorded bank transaction: {transaction.get_transaction_type_display()} - {transaction.amount}."
        )
    
    @action(detail=True, methods=['post'])
    def reconcile(self, request, pk=None):
        """Mark a bank transaction as reconciled"""
        
        bank_transaction = self.get_object()
        
        # Already reconciled
        if bank_transaction.is_reconciled:
            return Response({
                'status': 'info',
                'message': 'This transaction is already reconciled'
            })
        
        # Update reconciliation status
        bank_transaction.is_reconciled = True
        bank_transaction.reconciliation_date = timezone.now().date()
        bank_transaction.reconciled_by = request.user
        bank_transaction.save()
        
        # Log the activity
        ActivityLog.objects.create(
            user=request.user,
            action='BANK_TRANSACTION_RECONCILE',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            description=f"Reconciled bank transaction: {bank_transaction.amount} - {bank_transaction.reference_number}."
        )
        
        return Response({
            'status': 'success',
            'message': 'Transaction reconciled successfully'
        })