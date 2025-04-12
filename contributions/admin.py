# contributions/admin.py

from django.contrib import admin
from .models import ContributionReminder, ContributionReport, MemberContributionSchedule

@admin.register(ContributionReminder)
class ContributionReminderAdmin(admin.ModelAdmin):
    list_display = ('year', 'month', 'reminder_date', 'status', 'recipients_count', 'successful_count', 'failed_count')
    list_filter = ('status', 'year', 'month', 'reminder_date')
    search_fields = ('message', 'scheduled_by__email')
    readonly_fields = ('id', 'created_at', 'updated_at')

@admin.register(ContributionReport)
class ContributionReportAdmin(admin.ModelAdmin):
    list_display = ('year', 'month', 'quarter', 'report_date', 'total_members', 'contributing_members', 'total_amount')
    list_filter = ('year', 'month', 'quarter', 'report_date')
    search_fields = ('generated_by__email',)
    readonly_fields = ('id', 'created_at')

@admin.register(MemberContributionSchedule)
class MemberContributionScheduleAdmin(admin.ModelAdmin):
    list_display = ('member', 'frequency', 'amount', 'next_due_date')
    list_filter = ('frequency', 'created_at', 'updated_at')
    search_fields = ('member__email', 'member__full_name')
    readonly_fields = ('id', 'created_at', 'updated_at')
