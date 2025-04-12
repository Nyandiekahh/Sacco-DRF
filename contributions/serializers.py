# contributions/serializers.py

from rest_framework import serializers
from sacco_core.models import MonthlyContribution, ShareCapital
from .models import ContributionReminder, ContributionReport


class MonthlyContributionSerializer(serializers.ModelSerializer):
    """Serializer for monthly contributions"""
    
    member_name = serializers.SerializerMethodField()
    month_name = serializers.SerializerMethodField()
    recorder_name = serializers.SerializerMethodField()
    
    class Meta:
        model = MonthlyContribution
        fields = [
            'id', 'member', 'member_name', 'year', 'month', 'month_name',
            'amount', 'transaction_date', 'reference_number', 'transaction_code',
            'transaction_message', 'created_at', 'created_by', 'recorder_name'
        ]
        read_only_fields = ['id', 'created_at', 'created_by', 'recorder_name']
    
    def get_member_name(self, obj):
        return obj.member.full_name
    
    def get_month_name(self, obj):
        months = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ]
        return months[obj.month - 1]
    
    def get_recorder_name(self, obj):
        if obj.created_by:
            return obj.created_by.full_name
        return None


class ShareCapitalSerializer(serializers.ModelSerializer):
    """Serializer for share capital payments"""
    
    member_name = serializers.SerializerMethodField()
    recorder_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ShareCapital
        fields = [
            'id', 'member', 'member_name', 'amount', 'transaction_date',
            'reference_number', 'transaction_code', 'transaction_message',
            'created_at', 'created_by', 'recorder_name'
        ]
        read_only_fields = ['id', 'created_at', 'created_by', 'recorder_name']
    
    def get_member_name(self, obj):
        return obj.member.full_name
    
    def get_recorder_name(self, obj):
        if obj.created_by:
            return obj.created_by.full_name
        return None


class ContributionReminderSerializer(serializers.ModelSerializer):
    """Serializer for contribution reminders"""
    
    month_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ContributionReminder
        fields = [
            'id', 'year', 'month', 'month_name', 'reminder_date', 'status',
            'message', 'sent_at', 'scheduled_by', 'recipients_count',
            'successful_count', 'failed_count', 'created_at'
        ]
        read_only_fields = [
            'id', 'reminder_date', 'status', 'sent_at', 'scheduled_by',
            'recipients_count', 'successful_count', 'failed_count', 'created_at',
            'month_name'
        ]
    
    def get_month_name(self, obj):
        months = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ]
        return months[obj.month - 1]


class ContributionReportSerializer(serializers.ModelSerializer):
    """Serializer for contribution reports"""
    
    month_name = serializers.SerializerMethodField()
    quarter_name = serializers.SerializerMethodField()
    generated_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ContributionReport
        fields = [
            'id', 'year', 'month', 'month_name', 'quarter', 'quarter_name',
            'report_date', 'total_members', 'contributing_members',
            'total_amount', 'previous_period_amount', 'growth_percentage',
            'report_file', 'generated_by', 'generated_by_name', 'created_at'
        ]
        read_only_fields = [
            'id', 'report_date', 'total_members', 'contributing_members',
            'total_amount', 'previous_period_amount', 'growth_percentage',
            'report_file', 'generated_by', 'generated_by_name', 'created_at',
            'month_name', 'quarter_name'
        ]
    
    def get_month_name(self, obj):
        if obj.month:
            months = [
                'January', 'February', 'March', 'April', 'May', 'June',
                'July', 'August', 'September', 'October', 'November', 'December'
            ]
            return months[obj.month - 1]
        return None
    
    def get_quarter_name(self, obj):
        if obj.quarter:
            return f"Q{obj.quarter}"
        return None
    
    def get_generated_by_name(self, obj):
        if obj.generated_by:
            return obj.generated_by.full_name
        return None