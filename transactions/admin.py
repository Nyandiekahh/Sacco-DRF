# transactions/admin.py

from django.contrib import admin
from .models import (
    SaccoExpense, SaccoIncome, TransactionBatch, BatchItem, TransactionLog,
    BankAccount, BankTransaction
)

@admin.register(SaccoExpense)
class SaccoExpenseAdmin(admin.ModelAdmin):
    list_display = ('expense_date', 'category', 'amount', 'description', 'recorded_by')
    list_filter = ('category', 'expense_date', 'created_at')
    search_fields = ('description', 'reference_number', 'recorded_by__email')
    readonly_fields = ('id', 'created_at')

@admin.register(SaccoIncome)
class SaccoIncomeAdmin(admin.ModelAdmin):
    list_display = ('income_date', 'category', 'amount', 'description', 'recorded_by')
    list_filter = ('category', 'income_date', 'created_at')
    search_fields = ('description', 'reference_number', 'recorded_by__email')
    readonly_fields = ('id', 'created_at')

@admin.register(TransactionBatch)
class TransactionBatchAdmin(admin.ModelAdmin):
    list_display = ('batch_type', 'transaction_date', 'status', 'total_amount', 'transaction_count', 'created_by')
    list_filter = ('batch_type', 'status', 'transaction_date', 'created_at')
    search_fields = ('description', 'created_by__email')
    readonly_fields = ('id', 'created_at')

@admin.register(BatchItem)
class BatchItemAdmin(admin.ModelAdmin):
    list_display = ('batch', 'member', 'amount', 'status', 'processed_at')
    list_filter = ('status', 'created_at', 'processed_at')
    search_fields = ('member__full_name', 'reference_number', 'transaction_code')
    readonly_fields = ('id', 'created_at')

@admin.register(TransactionLog)
class TransactionLogAdmin(admin.ModelAdmin):
    list_display = ('transaction', 'ip_address', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('transaction__member__full_name', 'notes')
    readonly_fields = ('id', 'created_at')

@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ('bank_name', 'account_name', 'account_number', 'account_type', 'is_primary', 'is_active', 'current_balance')
    list_filter = ('is_primary', 'is_active', 'last_reconciled')
    search_fields = ('bank_name', 'account_name', 'account_number')
    readonly_fields = ('id', 'created_at', 'updated_at')

@admin.register(BankTransaction)
class BankTransactionAdmin(admin.ModelAdmin):
    list_display = ('account', 'transaction_type', 'amount', 'transaction_date', 'is_reconciled', 'recorded_by')
    list_filter = ('transaction_type', 'transaction_date', 'is_reconciled')
    search_fields = ('description', 'reference_number', 'account__bank_name')
    readonly_fields = ('id', 'created_at')
