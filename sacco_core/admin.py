# sacco_core/admin.py

from django.contrib import admin
from .models import (
    SaccoSettings, ShareCapital, MonthlyContribution, MemberShareSummary,
    DividendDistribution, MemberDividend, Loan, LoanRepayment, Transaction,
    FinancialSummary
)

@admin.register(SaccoSettings)
class SaccoSettingsAdmin(admin.ModelAdmin):
    list_display = ('name', 'share_value', 'minimum_monthly_contribution', 'loan_interest_rate', 'updated_at')
    readonly_fields = ('id', 'updated_at')
    fieldsets = (
        ('Basic Settings', {
            'fields': ('id', 'name', 'share_value', 'minimum_monthly_contribution')
        }),
        ('Loan Settings', {
            'fields': ('loan_interest_rate', 'maximum_loan_multiplier', 'loan_processing_fee_percentage', 'loan_insurance_percentage')
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'email', 'postal_address', 'physical_address')
        }),
        ('Meta', {
            'fields': ('updated_at', 'updated_by')
        }),
    )

@admin.register(ShareCapital)
class ShareCapitalAdmin(admin.ModelAdmin):
    list_display = ('member', 'amount', 'transaction_date', 'reference_number', 'created_by')
    list_filter = ('transaction_date', 'created_at')
    search_fields = ('member__email', 'member__full_name', 'reference_number', 'transaction_code')
    readonly_fields = ('id', 'created_at')

@admin.register(MonthlyContribution)
class MonthlyContributionAdmin(admin.ModelAdmin):
    list_display = ('member', 'year', 'month', 'amount', 'transaction_date', 'created_by')
    list_filter = ('year', 'month', 'transaction_date')
    search_fields = ('member__email', 'member__full_name', 'reference_number', 'transaction_code')
    readonly_fields = ('id', 'created_at')

@admin.register(MemberShareSummary)
class MemberShareSummaryAdmin(admin.ModelAdmin):
    list_display = ('member', 'total_share_capital', 'share_capital_completion_percentage', 'total_contributions', 'total_deposits', 'percentage_of_total_pool', 'number_of_shares')
    list_filter = ('updated_at',)
    search_fields = ('member__email', 'member__full_name')
    readonly_fields = ('id', 'updated_at')

@admin.register(DividendDistribution)
class DividendDistributionAdmin(admin.ModelAdmin):
    list_display = ('distribution_date', 'total_amount', 'source', 'distributed_by')
    list_filter = ('distribution_date', 'created_at')
    search_fields = ('source', 'description', 'distributed_by__email')
    readonly_fields = ('id', 'created_at')

@admin.register(MemberDividend)
class MemberDividendAdmin(admin.ModelAdmin):
    list_display = ('member', 'distribution', 'amount', 'percentage_share')
    list_filter = ('distribution__distribution_date', 'created_at')
    search_fields = ('member__email', 'member__full_name')
    readonly_fields = ('id', 'created_at')

@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('member', 'amount', 'status', 'application_date', 'disbursement_date', 'remaining_balance')
    list_filter = ('status', 'application_date', 'disbursement_date')
    search_fields = ('member__email', 'member__full_name', 'purpose')
    readonly_fields = ('id', 'application_date', 'created_at', 'updated_at')
    fieldsets = (
        ('Loan Details', {
            'fields': ('id', 'member', 'amount', 'interest_rate', 'application_date', 'status', 'purpose', 'term_months')
        }),
        ('Approval and Disbursement', {
            'fields': ('approval_date', 'disbursement_date', 'expected_completion_date', 'approved_by', 'disbursed_by')
        }),
        ('Processing', {
            'fields': ('processing_fee', 'insurance_fee', 'disbursed_amount')
        }),
        ('Repayment', {
            'fields': ('total_expected_repayment', 'total_repaid', 'remaining_balance')
        }),
        ('Meta', {
            'fields': ('created_at', 'updated_at', 'rejection_reason')
        }),
    )

@admin.register(LoanRepayment)
class LoanRepaymentAdmin(admin.ModelAdmin):
    list_display = ('loan', 'amount', 'transaction_date', 'reference_number', 'created_by')
    list_filter = ('transaction_date', 'created_at')
    search_fields = ('loan__member__email', 'loan__member__full_name', 'reference_number', 'transaction_code')
    readonly_fields = ('id', 'created_at')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_type', 'member', 'amount', 'transaction_date', 'reference_number', 'created_by')
    list_filter = ('transaction_type', 'transaction_date')
    search_fields = ('member__email', 'member__full_name', 'reference_number', 'description')
    readonly_fields = ('id', 'created_at')

@admin.register(FinancialSummary)
class FinancialSummaryAdmin(admin.ModelAdmin):
    list_display = ('date', 'total_assets', 'total_income', 'total_expenses', 'net_income', 'active_members')
    list_filter = ('date',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    fieldsets = (
        ('Summary Info', {
            'fields': ('id', 'date')
        }),
        ('Assets', {
            'fields': ('total_share_capital', 'total_contributions', 'outstanding_loans', 'cash_at_hand', 'total_assets')
        }),
        ('Income', {
            'fields': ('interest_income', 'fees_income', 'other_income', 'total_income')
        }),
        ('Expenses', {
            'fields': ('operational_expenses', 'dividend_payments', 'other_expenses', 'total_expenses')
        }),
        ('Metrics', {
            'fields': ('net_income', 'active_members', 'total_members')
        }),
        ('Meta', {
            'fields': ('created_at', 'updated_at')
        }),
    )