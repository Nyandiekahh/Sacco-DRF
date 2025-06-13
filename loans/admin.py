# loans/admin.py - Add missing models from loans app

from django.contrib import admin
from .models import (
    LoanApplication, LoanGuarantor, RepaymentSchedule, LoanStatement,
    LoanNotification, PaymentMethod, LoanDisbursement, GuarantorRequest, GuarantorLimit
)

@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    list_display = ('member', 'amount', 'status', 'application_date', 'reviewed_date', 'reviewed_by')
    list_filter = ('status', 'application_date', 'reviewed_date')
    search_fields = ('member__email', 'member__full_name', 'purpose')
    readonly_fields = ('id', 'application_date', 'created_at', 'updated_at')

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

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'payment_type', 'status', 'is_default', 'allowed_for_disbursement', 'allowed_for_repayment')
    list_filter = ('payment_type', 'status', 'is_default')
    search_fields = ('name', 'bank_name', 'provider')
    readonly_fields = ('id', 'created_at', 'updated_at')

@admin.register(LoanDisbursement)
class LoanDisbursementAdmin(admin.ModelAdmin):
    list_display = ('loan', 'amount', 'payment_method', 'disbursement_date', 'processed_by')
    list_filter = ('disbursement_date', 'created_at')
    search_fields = ('loan__member__full_name', 'reference_number')
    readonly_fields = ('id', 'created_at')

@admin.register(GuarantorRequest)
class GuarantorRequestAdmin(admin.ModelAdmin):
    list_display = ('loan_application', 'guarantor', 'requester', 'status', 'requested_at')
    list_filter = ('status', 'requested_at')
    search_fields = ('guarantor__full_name', 'requester__full_name')
    readonly_fields = ('id', 'requested_at', 'responded_at')

@admin.register(GuarantorLimit)
class GuarantorLimitAdmin(admin.ModelAdmin):
    list_display = ('member', 'total_guaranteed_amount', 'active_guarantees_count', 'maximum_guarantee_amount', 'available_guarantee_amount')
    search_fields = ('member__full_name', 'member__email')
    readonly_fields = ('id', 'updated_at')