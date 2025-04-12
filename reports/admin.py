# reports/admin.py

from django.contrib import admin
from .models import (
    Report, FinancialStatement, MemberStatement, AuditLog, SystemBackup,
    SavedReport
)

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('name', 'report_type', 'format', 'start_date', 'end_date', 'generated_by')
    list_filter = ('report_type', 'format', 'created_at')
    search_fields = ('name', 'description', 'member__full_name', 'generated_by__email')
    readonly_fields = ('id', 'created_at')

@admin.register(FinancialStatement)
class FinancialStatementAdmin(admin.ModelAdmin):
    list_display = ('statement_type', 'period_type', 'year', 'month', 'quarter', 'approved', 'generated_by')
    list_filter = ('statement_type', 'period_type', 'year', 'month', 'quarter', 'approved')
    search_fields = ('generated_by__email', 'approved_by__email')
    readonly_fields = ('id', 'created_at')

@admin.register(MemberStatement)
class MemberStatementAdmin(admin.ModelAdmin):
    list_display = ('member', 'statement_type', 'start_date', 'end_date', 'generated_by')
    list_filter = ('statement_type', 'start_date', 'end_date')
    search_fields = ('member__full_name', 'member__email', 'generated_by__email')
    readonly_fields = ('id', 'created_at')

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action_type', 'entity_type', 'entity_id', 'user', 'created_at')
    list_filter = ('action_type', 'entity_type', 'created_at')
    search_fields = ('action_description', 'user__email', 'entity_id')
    readonly_fields = ('id', 'created_at')

@admin.register(SystemBackup)
class SystemBackupAdmin(admin.ModelAdmin):
    list_display = ('name', 'backup_type', 'status', 'backup_date', 'file_size', 'initiated_by')
    list_filter = ('backup_type', 'status', 'backup_date')
    search_fields = ('name', 'description', 'initiated_by__email')
    readonly_fields = ('id', 'created_at')

@admin.register(SavedReport)
class SavedReportAdmin(admin.ModelAdmin):
    list_display = ('name', 'report_type', 'format', 'is_scheduled', 'created_by')
    list_filter = ('report_type', 'format', 'is_scheduled')
    search_fields = ('name', 'description', 'created_by__email')
    readonly_fields = ('id', 'created_at', 'updated_at')