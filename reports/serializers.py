# reports/serializers.py

from rest_framework import serializers
from .models import (
    Report,
    FinancialStatement,
    MemberStatement,
    AuditLog,
    SystemBackup,
    SavedReport
)


class ReportSerializer(serializers.ModelSerializer):
    """Serializer for reports"""
    
    report_type_display = serializers.SerializerMethodField()
    format_display = serializers.SerializerMethodField()
    generated_by_name = serializers.SerializerMethodField()
    member_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Report
        fields = [
            'id', 'name', 'report_type', 'report_type_display', 'description',
            'start_date', 'end_date', 'format', 'format_display', 'report_file',
            'member', 'member_name', 'generated_by', 'generated_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'generated_by', 'generated_by_name', 'created_at']
    
    def get_report_type_display(self, obj):
        return obj.get_report_type_display()
    
    def get_format_display(self, obj):
        return obj.get_format_display()
    
    def get_generated_by_name(self, obj):
        if obj.generated_by:
            return obj.generated_by.full_name
        return None
    
    def get_member_name(self, obj):
        if obj.member:
            return obj.member.full_name
        return None


class FinancialStatementSerializer(serializers.ModelSerializer):
    """Serializer for financial statements"""
    
    statement_type_display = serializers.SerializerMethodField()
    period_type_display = serializers.SerializerMethodField()
    period_description = serializers.SerializerMethodField()
    generated_by_name = serializers.SerializerMethodField()
    approved_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = FinancialStatement
        fields = [
            'id', 'statement_type', 'statement_type_display', 'period_type',
            'period_type_display', 'year', 'month', 'quarter', 'period_description',
            'start_date', 'end_date', 'statement_data', 'report', 'approved',
            'approved_by', 'approved_by_name', 'approved_at', 'generated_by',
            'generated_by_name', 'created_at'
        ]
        read_only_fields = [
            'id', 'period_description', 'approved', 'approved_by',
            'approved_by_name', 'approved_at', 'generated_by',
            'generated_by_name', 'created_at'
        ]
    
    def get_statement_type_display(self, obj):
        return obj.get_statement_type_display()
    
    def get_period_type_display(self, obj):
        return obj.get_period_type_display()
    
    def get_period_description(self, obj):
        if obj.period_type == 'MONTHLY' and obj.month:
            return f"{obj.get_month_name()} {obj.year}"
        elif obj.period_type == 'QUARTERLY' and obj.quarter:
            return f"Q{obj.quarter} {obj.year}"
        elif obj.period_type == 'ANNUAL':
            return f"{obj.year}"
        elif obj.period_type == 'CUSTOM':
            return f"{obj.start_date} to {obj.end_date}"
        return ""
    
    def get_generated_by_name(self, obj):
        if obj.generated_by:
            return obj.generated_by.full_name
        return None
    
    def get_approved_by_name(self, obj):
        if obj.approved_by:
            return obj.approved_by.full_name
        return None


class MemberStatementSerializer(serializers.ModelSerializer):
    """Serializer for member statements"""
    
    statement_type_display = serializers.SerializerMethodField()
    member_name = serializers.SerializerMethodField()
    generated_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = MemberStatement
        fields = [
            'id', 'member', 'member_name', 'statement_type', 'statement_type_display',
            'start_date', 'end_date', 'statement_data', 'report', 'generated_by',
            'generated_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'generated_by', 'generated_by_name', 'created_at']
    
    def get_statement_type_display(self, obj):
        return obj.get_statement_type_display()
    
    def get_member_name(self, obj):
        return obj.member.full_name
    
    def get_generated_by_name(self, obj):
        if obj.generated_by:
            return obj.generated_by.full_name
        return None


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for audit logs"""
    
    action_type_display = serializers.SerializerMethodField()
    user_details = serializers.SerializerMethodField()
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'action_type', 'action_type_display', 'action_description',
            'entity_type', 'entity_id', 'changes', 'user', 'user_details',
            'ip_address', 'user_agent', 'created_at'
        ]
        read_only_fields = fields
    
    def get_action_type_display(self, obj):
        return obj.get_action_type_display()
    
    def get_user_details(self, obj):
        if obj.user:
            return {
                'id': str(obj.user.id),
                'email': obj.user.email,
                'full_name': obj.user.full_name,
                'role': obj.user.role
            }
        return None


class SystemBackupSerializer(serializers.ModelSerializer):
    """Serializer for system backups"""
    
    backup_type_display = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    initiated_by_name = serializers.SerializerMethodField()
    file_size_display = serializers.SerializerMethodField()
    
    class Meta:
        model = SystemBackup
        fields = [
            'id', 'backup_type', 'backup_type_display', 'name', 'description',
            'status', 'status_display', 'backup_file', 'file_size', 'file_size_display',
            'included_modules', 'backup_date', 'completion_date', 'error_message',
            'initiated_by', 'initiated_by_name', 'created_at'
        ]
        read_only_fields = fields
    
    def get_backup_type_display(self, obj):
        return obj.get_backup_type_display()
    
    def get_status_display(self, obj):
        return obj.get_status_display()
    
    def get_initiated_by_name(self, obj):
        if obj.initiated_by:
            return obj.initiated_by.full_name
        return None
    
    def get_file_size_display(self, obj):
        # Convert bytes to human-readable format
        if obj.file_size < 1024:
            return f"{obj.file_size} bytes"
        elif obj.file_size < 1024 * 1024:
            return f"{obj.file_size / 1024:.2f} KB"
        elif obj.file_size < 1024 * 1024 * 1024:
            return f"{obj.file_size / (1024 * 1024):.2f} MB"
        else:
            return f"{obj.file_size / (1024 * 1024 * 1024):.2f} GB"


class SavedReportSerializer(serializers.ModelSerializer):
    """Serializer for saved report templates"""
    
    created_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = SavedReport
        fields = [
            'id', 'name', 'description', 'report_type', 'format', 'parameters',
            'is_scheduled', 'schedule_frequency', 'last_run', 'next_run',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_by', 'created_by_name', 'created_at', 'updated_at',
            'last_run', 'next_run'
        ]
    
    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.full_name
        return None