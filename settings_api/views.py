from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import SaccoSettings
from .serializers import SaccoSettingsSerializer
from .permissions import IsAdminUser

class SaccoSettingsViewSet(viewsets.ModelViewSet):
    """ViewSet for viewing and editing SACCO settings"""
    serializer_class = SaccoSettingsSerializer
    
    def get_queryset(self):
        """Return the SACCO settings (usually just one record)"""
        return SaccoSettings.objects.all()
    
    def get_permissions(self):
        """
        Ensure only admin users can modify settings.
        Anyone authenticated can view them.
        """
        if self.action in ['update', 'partial_update', 'create', 'destroy']:
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated()]
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get the current settings (convenience endpoint)"""
        settings = SaccoSettings.get_settings()
        serializer = self.get_serializer(settings)
        return Response(serializer.data)    


class UserSettingsViewSet(viewsets.ViewSet):
    """
    ViewSet for user-specific settings
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get', 'put', 'patch'])
    def profile(self, request):
        """Get or update the user's profile"""
        user = request.user
        if request.method == 'GET':
            serializer = UserProfileSerializer(user)
            return Response(serializer.data)
        
        serializer = UserProfileSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            
            # Log the activiy
            from authentication.models import ActivityLog
            ActivityLog.objects.create(
                user=user,
                action='PROFILE_UPDATE',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                description=f"User profile updated through settings.",
            )
            
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Change user password"""
        from authentication.serializers import PasswordResetSerializer
        
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            # Log the activity
            from authentication.models import ActivityLog
            ActivityLog.objects.create(
                user=user,
                action='PASSWORD_RESET',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                description=f"Password change through settings.",
            )
            
            return Response({"message": "Password changed successfully"})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def upload_document(self, request):
        """Upload KYC documents"""
        from authentication.serializers import DocumentUploadSerializer
        
        serializer = DocumentUploadSerializer(data=request.data)
        if serializer.is_valid():
            document = serializer.save(user=request.user)
            
            # Log the activity
            from authentication.models import ActivityLog
            ActivityLog.objects.create(
                user=request.user,
                action='DOCUMENT_UPLOAD',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                description=f"Uploaded {document.get_document_type_display()} document through settings.",
            )
            
            return Response({
                'message': 'Document uploaded successfully.',
                'document_id': str(document.id)
            }, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def documents(self, request):
        """Get user documents"""
        from authentication.models import UserDocument
        from authentication.serializers import UserProfileSerializer
        
        profile_serializer = UserProfileSerializer(request.user)
        return Response({
            'documents': profile_serializer.data['documents']
        })
    
    @action(detail=False, methods=['get'])
    def notification_preferences(self, request):
        """Get or update notification preferences (placeholder for future)"""
        return Response({
            "email_notifications": True,
            "sms_notifications": True
        })
    
# settings_api/views.py
class AdminSettingsViewSet(viewsets.ViewSet):
    """
    ViewSet for admin-specific settings and actions
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    @action(detail=False, methods=['get'])
    def users(self, request):
        """List all users (admin only)"""
        from authentication.models import SaccoUser
        from authentication.serializers import UserListSerializer
        
        users = SaccoUser.objects.all()
        serializer = UserListSerializer(users, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='reset-password')
    def reset_user_password(self, request, pk=None):
        """Admin sending password reset OTP to a user"""
        from authentication.models import SaccoUser, OTPRequest, ActivityLog
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.conf import settings as django_settings
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            target_user = SaccoUser.objects.get(id=pk)
            
            # Create OTP
            otp_request = OTPRequest.objects.create(
                user=target_user,
                otp_type='RESET'
            )
            
            # Send OTP email
            subject = 'Password Reset OTP'
            message = f"""
            Your administrator has requested a password reset for your account.
            Your OTP code is: {otp_request.otp}
            This code will expire in 15 minutes.
            """
            
            # For HTML email (preferred)
            html_message = render_to_string('emails/admin_password_reset.html', {
                'otp': otp_request.otp,
                'expiry_minutes': 15,
                'admin_name': request.user.full_name or request.user.email,
            })
            
            try:
                send_mail(
                    subject,
                    message,
                    django_settings.DEFAULT_FROM_EMAIL,
                    [target_user.email],
                    html_message=html_message,
                    fail_silently=False,
                )
                
                # Log the activity
                ActivityLog.objects.create(
                    user=request.user,
                    action='PASSWORD_RESET',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    description=f"Admin initiated password reset for {target_user.email}.",
                )
                
                return Response({
                    'message': f'Password reset OTP sent to {target_user.email}.'
                }, status=status.HTTP_200_OK)
                
            except Exception as e:
                logger.error(f"Failed to send admin reset email: {str(e)}")
                return Response(
                    {"error": "Failed to send reset email."}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except SaccoUser.DoesNotExist:
            return Response(
                {"error": "User not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'], url_path='toggle-status')
    def toggle_user_status(self, request, pk=None):
        """Toggle a user's active status (put on hold/activate)"""
        from authentication.models import SaccoUser, ActivityLog
        
        try:
            target_user = SaccoUser.objects.get(id=pk)
            
            # Toggle status
            target_user.is_on_hold = not target_user.is_on_hold
            
            # Get reason if putting on hold
            if target_user.is_on_hold:
                reason = request.data.get('reason', '')
                target_user.on_hold_reason = reason
                action_type = 'ACCOUNT_LOCK'
                action_msg = f"Member account put on hold. Reason: {reason}"
            else:
                target_user.on_hold_reason = ''
                action_type = 'ACCOUNT_UNLOCK'
                action_msg = "Member account activated from hold status"
            
            target_user.save()
            
            # Log the activity
            ActivityLog.objects.create(
                user=request.user,
                action=action_type,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                description=f"{action_msg} for {target_user.email}.",
            )
            
            status_msg = "put on hold" if target_user.is_on_hold else "activated"
            return Response({
                'message': f'User has been {status_msg} successfully.'
            }, status=status.HTTP_200_OK)
            
        except SaccoUser.DoesNotExist:
            return Response(
                {"error": "User not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'], url_path='verify-document/(?P<document_id>[^/.]+)')
    def verify_document(self, request, pk=None, document_id=None):
        """Verify a user document"""
        from authentication.models import UserDocument, ActivityLog
        from django.utils import timezone
        
        try:
            document = UserDocument.objects.get(id=document_id, user_id=pk)
            
            # Update verification status
            document.is_verified = True
            document.verified_at = timezone.now()
            document.verified_by = request.user
            document.save()
            
            # Log the activity
            ActivityLog.objects.create(
                user=request.user,
                action='DOCUMENT_VERIFY',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                description=f"Verified {document.get_document_type_display()} for {document.user.email}.",
            )
            
            return Response({
                'message': 'Document verified successfully.'
            }, status=status.HTTP_200_OK)
            
        except UserDocument.DoesNotExist:
            return Response(
                {"error": "Document not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get the current settings (convenience endpoint)"""
        settings = SaccoSettings.get_settings()
        serializer = self.get_serializer(settings)
    
        # Optional: Add dividend calculation methods
        response_data = serializer.data
        response_data['dividend_calculation_methods'] = [
            method[0] for method in SaccoSettings._meta.get_field('dividend_calculation_method').choices
        ]
    
        return Response(response_data)