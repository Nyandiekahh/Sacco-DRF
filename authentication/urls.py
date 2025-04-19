from django.urls import path
from .views import (
    InviteMemberView,
    OTPLoginView,
    CompleteRegistrationView,
    DocumentUploadView,
    UserProfileView,
    RequestPasswordResetView,
    VerifyOTPView,
    ResetPasswordView,
    AdminResetUserOTPView,
    ToggleUserStatusView,
    VerifyDocumentView,
    SendMassEmailView,
    ListInvitationsView,
    ResendInvitationView
)

urlpatterns = [
    # Invitation and registration
    path('invite/', InviteMemberView.as_view(), name='invite-member'),
    path('invitations/', ListInvitationsView.as_view(), name='list-invitations'),
    path('invitations/<uuid:invitation_id>/resend/', ResendInvitationView.as_view(), name='resend-invitation'),
    path('otp-login/', OTPLoginView.as_view(), name='otp-login'),
    path('complete-registration/', CompleteRegistrationView.as_view(), name='complete-registration'),
    
    # User profile and documents
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('upload-document/', DocumentUploadView.as_view(), name='upload-document'),
    
    # Password management
    path('reset-password-request/', RequestPasswordResetView.as_view(), name='reset-password-request'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    
    # Admin actions
    path('admin/reset-user-otp/<uuid:user_id>/', AdminResetUserOTPView.as_view(), name='admin-reset-user-otp'),
    path('admin/toggle-user-status/<uuid:user_id>/', ToggleUserStatusView.as_view(), name='toggle-user-status'),
    path('admin/verify-document/<uuid:document_id>/', VerifyDocumentView.as_view(), name='verify-document'),
    path('admin/send-mass-email/', SendMassEmailView.as_view(), name='send-mass-email'),
    path('admin/verify-document/type/<str:document_type>/', VerifyDocumentView.as_view(), name='verify-document-by-type'),
]