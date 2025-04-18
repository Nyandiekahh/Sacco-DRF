# settings_api/admin.py
from django.contrib import admin
from .models import SaccoSettings

@admin.register(SaccoSettings)
class SaccoSettingsAdmin(admin.ModelAdmin):
    """Customized admin interface for SACCO Settings"""
    
    # Fieldsets to organize settings into logical groups
    fieldsets = [
        ('Share Capital', {
            'fields': ['share_value', 'minimum_monthly_contribution']
        }),
        ('Loan Settings', {
            'fields': [
                'loan_interest_rate', 
                'maximum_loan_multiplier', 
                'loan_processing_fee_percentage', 
                'loan_insurance_percentage',
                'maximum_loan_term_months',
                'minimum_guarantors'
            ]
        }),
        ('Member Settings', {
            'fields': ['minimum_membership_period_months']
        }),
        ('Dividend Settings', {
            'fields': ['dividend_calculation_method']
        }),
        ('System Notifications', {
            'fields': ['enable_sms_notifications', 'enable_email_notifications']
        }),
        ('Contact Information', {
            'fields': [
                'sacco_name', 
                'phone_number', 
                'email', 
                'postal_address', 
                'physical_address'
            ]
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    # Read-only fields for timestamps and system-generated values
    readonly_fields = ['created_at', 'updated_at']
    
    # Customize list display in admin overview
    list_display = [
        'sacco_name', 
        'share_value', 
        'minimum_monthly_contribution', 
        'loan_interest_rate', 
        'updated_at'
    ]
    
    # Add search capabilities
    search_fields = ['sacco_name', 'email', 'phone_number']
    
    # Prevent adding multiple settings instances
    def has_add_permission(self, request):
        return not SaccoSettings.objects.exists()
    
    # Prevent deleting the settings
    def has_delete_permission(self, request, obj=None):
        return False
    
    # Customize the title
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.title = "SACCO Global Configuration Settings"
        return form