# loans/admin.py

from django.contrib import admin
from .models import (
    LoanApplication, LoanGuarantor, RepaymentSchedule, LoanStatement,
    LoanNotification
)

@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    list_display = ('member', 'amount', 'status', 'application_date', 'reviewed_date', 'reviewed_by')
    list_filter = ('status', 'application_date', 'reviewed_date')
    search_fields = ('member__email', 'member__full_name', 'purpose')
    readonly_fields = ('id', 'application_date', 'created_at', 'updated_at')
    fieldsets = (
        ('Application Details', {
            'fields': ('id', 'member', 'amount', 'purpose', 'term_months', 'application_date', 'status')
        }),
        ('Guarantor Information', {
            'fields': ('has_guarantor', 'guarantor_name', 'guarantor_contact', 'guarantor_relationship')
        }),
        ('Review', {
            'fields': ('reviewed_date', 'reviewed_by', 'rejection_reason')
        }),
        ('Documents', {
            'fields': ('application_document',)
        }),
        ('Loan Reference', {
            'fields': ('loan',)
        }),
        ('Meta', {
            'fields': ('created_at', 'updated_at')
        }),
    )

@admin.register(LoanGuarantor)
class LoanGuarantorAdmin(admin.ModelAdmin):
    list_display = ('loan', 'member_guarantor', 'name', 'guarantee_amount', 'guarantee_percentage')
    list_filter = ('created_at',)
    search_fields = ('loan__member__full_name', 'member_guarantor__full_name', 'name', 'id_number')
    readonly_fields = ('id', 'created_at')

@admin.register(RepaymentSchedule)
class RepaymentScheduleAdmin(admin.ModelAdmin):
    list_display = ('loan', 'installment_number', 'due_date', 'amount_due', 'amount_paid', 'remaining_amount', 'status')
    list_filter = ('status', 'due_date')
    search_fields = ('loan__member__full_name',)
    readonly_fields = ('id', 'created_at', 'updated_at')

@admin.register(LoanStatement)
class LoanStatementAdmin(admin.ModelAdmin):
    list_display = ('loan', 'statement_date', 'remaining_balance', 'next_payment_date', 'generated_by')
    list_filter = ('statement_date', 'created_at')
    search_fields = ('loan__member__full_name',)
    readonly_fields = ('id', 'created_at')

@admin.register(LoanNotification)
class LoanNotificationAdmin(admin.ModelAdmin):
    list_display = ('loan', 'notification_type', 'sent', 'sent_at', 'created_at')
    list_filter = ('notification_type', 'sent', 'sent_at', 'created_at')
    search_fields = ('loan__member__full_name', 'message')
    readonly_fields = ('id', 'created_at')
