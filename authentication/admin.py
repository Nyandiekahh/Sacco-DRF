# authentication/admin.py

from django.contrib import admin
from .models import SaccoUser, UserDocument, Invitation, OTPRequest, ActivityLog

@admin.register(SaccoUser)
class SaccoUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'full_name', 'membership_number', 'role', 'is_active', 'is_verified', 'is_on_hold', 'date_joined')
    list_filter = ('role', 'is_active', 'is_verified', 'is_on_hold', 'date_joined')
    search_fields = ('email', 'full_name', 'membership_number', 'phone_number')
    readonly_fields = ('id', 'date_joined', 'last_login')
    fieldsets = (
        ('Personal Information', {
            'fields': ('id', 'email', 'full_name', 'role', 'membership_number', 'date_joined')
        }),
        ('Contact Details', {
            'fields': ('id_number', 'phone_number', 'whatsapp_number', 'mpesa_number')
        }),
        ('Bank Details', {
            'fields': ('bank_name', 'bank_account_number', 'bank_account_name')
        }),
        ('Account Status', {
            'fields': ('is_active', 'is_verified', 'is_on_hold', 'on_hold_reason', 'share_capital_term')
        }),
        ('Security', {
            'fields': ('failed_login_attempts', 'last_failed_login', 'account_locked_until')
        }),
        ('Administrative', {
            'fields': ('is_staff', 'is_superuser', 'last_login')
        }),
    )

@admin.register(UserDocument)
class UserDocumentAdmin(admin.ModelAdmin):
    list_display = ('user', 'document_type', 'is_verified', 'uploaded_at', 'verified_at')
    list_filter = ('document_type', 'is_verified', 'uploaded_at')
    search_fields = ('user__email', 'user__full_name')
    readonly_fields = ('id', 'uploaded_at')

@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ('email', 'created_at', 'expires_at', 'is_used', 'invited_by')
    list_filter = ('is_used', 'created_at', 'expires_at')
    search_fields = ('email', 'invited_by__email')
    readonly_fields = ('id', 'created_at')

@admin.register(OTPRequest)
class OTPRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'otp_type', 'created_at', 'expires_at', 'is_used')
    list_filter = ('otp_type', 'is_used', 'created_at')
    search_fields = ('user__email', 'user__full_name')
    readonly_fields = ('id', 'created_at')

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'ip_address', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('user__email', 'user__full_name', 'description')
    readonly_fields = ('id', 'created_at')