# transactions/serializers.py

from rest_framework import serializers
from .models import (
    SaccoExpense, 
    SaccoIncome, 
    TransactionBatch, 
    BatchItem, 
    TransactionLog,
    BankAccount, 
    BankTransaction
)


class SaccoExpenseSerializer(serializers.ModelSerializer):
    """Serializer for SACCO expenses"""
    
    category_display = serializers.SerializerMethodField()
    recorder_name = serializers.SerializerMethodField()
    
    class Meta:
        model = SaccoExpense
        fields = [
            'id', 'expense_date', 'amount', 'description', 'category', 
            'category_display', 'payment_method', 'reference_number', 
            'receipt_image', 'transaction_cost', 'recorded_by', 
            'recorder_name', 'created_at', 'transaction'
        ]
        read_only_fields = ['id', 'recorded_by', 'recorder_name', 'created_at', 'transaction']
    
    def get_category_display(self, obj):
        return obj.get_category_display()
    
    def get_recorder_name(self, obj):
        if obj.recorded_by:
            return obj.recorded_by.full_name
        return None


class SaccoIncomeSerializer(serializers.ModelSerializer):
    """Serializer for SACCO income"""
    
    category_display = serializers.SerializerMethodField()
    recorder_name = serializers.SerializerMethodField()
    
    class Meta:
        model = SaccoIncome
        fields = [
            'id', 'income_date', 'amount', 'description', 'category', 
            'category_display', 'payment_method', 'reference_number', 
            'receipt_image', 'recorded_by', 'recorder_name', 
            'created_at', 'transaction'
        ]
        read_only_fields = ['id', 'recorded_by', 'recorder_name', 'created_at', 'transaction']
    
    def get_category_display(self, obj):
        return obj.get_category_display()
    
    def get_recorder_name(self, obj):
        if obj.recorded_by:
            return obj.recorded_by.full_name
        return None


class BatchItemSerializer(serializers.ModelSerializer):
    """Serializer for batch items"""
    
    member_name = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    
    class Meta:
        model = BatchItem
        fields = [
            'id', 'batch', 'member', 'member_name', 'amount', 
            'reference_number', 'transaction_code', 'description',
            'status', 'status_display', 'error_message', 'transaction',
            'created_at', 'processed_at'
        ]
        read_only_fields = ['id', 'status', 'error_message', 'transaction', 'created_at', 'processed_at']
    
    def get_member_name(self, obj):
        return obj.member.full_name
    
    def get_status_display(self, obj):
        return obj.get_status_display()


class TransactionBatchSerializer(serializers.ModelSerializer):
    """Serializer for transaction batches"""
    
    items = BatchItemSerializer(many=True, read_only=True)
    batch_type_display = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = TransactionBatch
        fields = [
            'id', 'batch_type', 'batch_type_display', 'description', 
            'transaction_date', 'status', 'status_display', 
            'total_amount', 'transaction_count', 'batch_file',
            'processed_count', 'failed_count', 'processing_notes',
            'created_by', 'created_by_name', 'created_at', 'processed_at',
            'items'
        ]
        read_only_fields = [
            'id', 'processed_count', 'failed_count', 'created_by',
            'created_by_name', 'created_at', 'processed_at'
        ]
    
    def get_batch_type_display(self, obj):
        return obj.get_batch_type_display()
    
    def get_status_display(self, obj):
        return obj.get_status_display()
    
    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.full_name
        return None


class TransactionLogSerializer(serializers.ModelSerializer):
    """Serializer for transaction logs"""
    
    class Meta:
        model = TransactionLog
        fields = [
            'id', 'transaction', 'ip_address', 'user_agent',
            'previous_state', 'new_state', 'notes', 'created_at'
        ]
        read_only_fields = fields


class BankAccountSerializer(serializers.ModelSerializer):
    """Serializer for bank accounts"""
    
    class Meta:
        model = BankAccount
        fields = [
            'id', 'account_name', 'bank_name', 'account_number', 'branch',
            'account_type', 'is_primary', 'is_active', 'current_balance',
            'last_reconciled', 'contact_person', 'contact_email', 'contact_phone',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'current_balance', 'created_at', 'updated_at']


class BankTransactionSerializer(serializers.ModelSerializer):
    """Serializer for bank transactions"""
    
    transaction_type_display = serializers.SerializerMethodField()
    account_details = serializers.SerializerMethodField()
    recorder_name = serializers.SerializerMethodField()
    reconciled_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = BankTransaction
        fields = [
            'id', 'account', 'account_details', 'transaction_date', 'value_date',
            'transaction_type', 'transaction_type_display', 'amount', 'description',
            'reference_number', 'destination_account', 'is_reconciled',
            'reconciliation_date', 'reconciled_by', 'reconciled_by_name',
            'related_transaction', 'created_at', 'recorded_by', 'recorder_name'
        ]
        read_only_fields = [
            'id', 'reconciliation_date', 'reconciled_by', 'reconciled_by_name',
            'created_at', 'recorded_by', 'recorder_name'
        ]
    
    def get_transaction_type_display(self, obj):
        return obj.get_transaction_type_display()
    
    def get_account_details(self, obj):
        return {
            'id': str(obj.account.id),
            'bank_name': obj.account.bank_name,
            'account_name': obj.account.account_name,
            'account_number': obj.account.account_number
        }
    
    def get_recorder_name(self, obj):
        if obj.recorded_by:
            return obj.recorded_by.full_name
        return None
    
    def get_reconciled_by_name(self, obj):
        if obj.reconciled_by:
            return obj.reconciled_by.full_name
        return None