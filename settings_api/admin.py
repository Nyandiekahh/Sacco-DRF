from django.contrib import admin
from .models import SaccoSettings

@admin.register(SaccoSettings)
class SaccoSettingsAdmin(admin.ModelAdmin):
    """Admin interface for SACCO settings"""
    list_display = ('id', 'share_value', 'minimum_monthly_contribution', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Share Capital Settings', {
            'fields': ('share_value', 'minimum_monthly_contribution')
        }),
        ('Loan Settings', {
            'fields': (
                'loan_interest_rate', 'maximum_loan_multiplier',
                'loan_processing_fee_percentage', 'loan_insurance_percentage'
            )
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'email', 'postal_address', 'physical_address')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one settings object
        return SaccoSettings.objects.count() == 0
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of the settings object
        return False