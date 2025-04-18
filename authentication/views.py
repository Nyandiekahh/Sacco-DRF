# authentication/views.py

import logging
import random
import string
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.auth import authenticate, login, logout
from rest_framework import status, generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .models import SaccoUser, Invitation, OTPRequest, UserDocument, ActivityLog
from .serializers import (
    InvitationSerializer, 
    OTPLoginSerializer, 
    UserRegistrationSerializer,
    UserProfileSerializer,
    OTPVerificationSerializer,
    PasswordResetRequestSerializer,
    PasswordResetSerializer,
    DocumentUploadSerializer,
    InvitationListSerializer
)

logger = logging.getLogger(__name__)

class InviteMemberView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Send an invitation with OTP to a new member."""
        
        # Check if user has admin privileges
        if request.user.role != SaccoUser.ADMIN:
            return Response(
                {"error": "You do not have permission to invite users."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = InvitationSerializer(data=request.data)
        if serializer.is_valid():
            # Check if the email already exists
            email = serializer.validated_data['email']
            if SaccoUser.objects.filter(email=email).exists():
                return Response(
                    {"error": "User with this email already exists."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create invitation
            invitation = serializer.save(invited_by=request.user)
            
            # Send invitation email with OTP
            subject = 'Invitation to join SACCO'
            message = f"""
            You have been invited to join our SACCO system.
            Your OTP code is: {invitation.otp}
            This code will expire in 48 hours.
            
            Please use this code to complete your registration.
            """
            
            # For HTML email (preferred)
            html_message = render_to_string('emails/invitation.html', {
                'otp': invitation.otp,
                'expiry_hours': 48,
                'inviter_name': request.user.full_name or request.user.email,
            })
            
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    html_message=html_message,
                    fail_silently=False,
                )
                
                # Log the activity
                ActivityLog.objects.create(
                    user=request.user,
                    action='INVITE',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    description=f"Invited {email} to join the SACCO.",
                )
                
                return Response({"message": "Invitation sent successfully."}, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                logger.error(f"Failed to send invitation email: {str(e)}")
                return Response(
                    {"error": "Failed to send invitation email."}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OTPLoginView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Login using OTP from an invitation."""
        
        serializer = OTPLoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']
            
            # Verify OTP from invitation
            invitation = Invitation.objects.filter(
                email=email,
                otp=otp,
                is_used=False
            ).first()
            
            if not invitation:
                return Response(
                    {"error": "Invalid OTP or email."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if invitation.is_expired:
                return Response(
                    {"error": "OTP has expired."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if user exists
            user = SaccoUser.objects.filter(email=email).first()
            
            # Set invitation as used
            invitation.is_used = True
            invitation.save()
            
            if user:
                # Existing user - generate token
                refresh = RefreshToken.for_user(user)
                
                # Log the activity
                ActivityLog.objects.create(
                    user=user,
                    action='LOGIN',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    description=f"Logged in using OTP.",
                )
                
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user_exists': True,
                    'user_id': str(user.id)
                }, status=status.HTTP_200_OK)
            else:
                # New user - return flag to complete registration
                return Response({
                    'message': 'OTP verified. Please complete registration.',
                    'user_exists': False,
                    'invitation_id': str(invitation.id)
                }, status=status.HTTP_200_OK)
                
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CompleteRegistrationView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Complete registration after OTP verification."""
        
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            # Check if the email was invited
            invitation = Invitation.objects.filter(
                email=email,
                is_used=True
            ).order_by('-created_at').first()
            
            if not invitation:
                return Response(
                    {"error": "No valid invitation found for this email."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create the user
            user = SaccoUser.objects.create_user(
                email=email,
                password=serializer.validated_data['password'],
                full_name=serializer.validated_data.get('full_name', ''),
                id_number=serializer.validated_data.get('id_number', ''),
                phone_number=serializer.validated_data.get('phone_number', ''),
                whatsapp_number=serializer.validated_data.get('whatsapp_number', ''),
                mpesa_number=serializer.validated_data.get('mpesa_number', ''),
                bank_name=serializer.validated_data.get('bank_name', ''),
                bank_account_number=serializer.validated_data.get('bank_account_number', ''),
                bank_account_name=serializer.validated_data.get('bank_account_name', ''),
                role=SaccoUser.MEMBER,
                share_capital_term=invitation.share_capital_term
            )
            
            # Generate token
            refresh = RefreshToken.for_user(user)
            
            # Log the activity
            ActivityLog.objects.create(
                user=user,
                action='ACCOUNT_CREATE',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                description=f"Completed registration and created account.",
            )
            
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user_id': str(user.id),
                'message': 'Registration completed successfully.'
            }, status=status.HTTP_201_CREATED)
                
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DocumentUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Upload KYC documents."""
        
        serializer = DocumentUploadSerializer(data=request.data)
        if serializer.is_valid():
            document = serializer.save(user=request.user)
            
            # Log the activity
            ActivityLog.objects.create(
                user=request.user,
                action='DOCUMENT_UPLOAD',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                description=f"Uploaded {document.get_document_type_display()} document.",
            )
            
            return Response({
                'message': 'Document uploaded successfully.',
                'document_id': str(document.id)
            }, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserProfileSerializer
    
    def get_object(self):
        return self.request.user
    
    def perform_update(self, serializer):
        serializer.save()
        
        # Log the activity
        ActivityLog.objects.create(
            user=self.request.user,
            action='ACCOUNT_UPDATE',
            ip_address=self.request.META.get('REMOTE_ADDR'),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            description=f"Updated profile information.",
        )


class RequestPasswordResetView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Request a password reset."""
        
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            # Check if user exists
            user = SaccoUser.objects.filter(email=email).first()
            if not user:
                # Don't reveal that user doesn't exist for security
                return Response({
                    'message': 'If a user with this email exists, an OTP has been sent.'
                }, status=status.HTTP_200_OK)
            
            # Create OTP
            otp_request = OTPRequest.objects.create(
                user=user,
                otp_type='RESET'
            )
            
            # Send OTP email
            subject = 'Password Reset OTP'
            message = f"""
            You have requested to reset your password.
            Your OTP code is: {otp_request.otp}
            This code will expire in 15 minutes.
            
            If you did not request this reset, please ignore this email.
            """
            
            # For HTML email (preferred)
            html_message = render_to_string('emails/password_reset.html', {
                'otp': otp_request.otp,
                'expiry_minutes': 15,
            })
            
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    html_message=html_message,
                    fail_silently=False,
                )
                
                # Log the activity
                ActivityLog.objects.create(
                    user=user,
                    action='PASSWORD_RESET',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    description=f"Requested password reset.",
                )
                
                return Response({
                    'message': 'If a user with this email exists, an OTP has been sent.'
                }, status=status.HTTP_200_OK)
                
            except Exception as e:
                logger.error(f"Failed to send password reset email: {str(e)}")
                return Response(
                    {"error": "Failed to send reset email."}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Verify OTP for password reset."""
        
        serializer = OTPVerificationSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']
            
            # Find user
            user = SaccoUser.objects.filter(email=email).first()
            if not user:
                return Response(
                    {"error": "Invalid email."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verify OTP
            otp_request = OTPRequest.objects.filter(
                user=user,
                otp=otp,
                otp_type='RESET',
                is_used=False
            ).order_by('-created_at').first()
            
            if not otp_request:
                return Response(
                    {"error": "Invalid OTP."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if otp_request.is_expired:
                return Response(
                    {"error": "OTP has expired."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Mark OTP as used
            otp_request.is_used = True
            otp_request.save()
            
            # Generate reset token
            reset_token = RefreshToken.for_user(user)
            
            return Response({
                'reset_token': str(reset_token.access_token),
                'message': 'OTP verified successfully.'
            }, status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Reset password after OTP verification."""
        
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            
            # Set new password
            user.set_password(serializer.validated_data['new_password'])
            
            # Reset any account lockouts
            user.reset_failed_login()
            user.save()
            
            # Log the activity
            ActivityLog.objects.create(
                user=user,
                action='PASSWORD_RESET',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                description=f"Password reset completed.",
            )
            
            return Response({
                'message': 'Password has been reset successfully.'
            }, status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminResetUserOTPView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, user_id):
        """Admin sending password reset OTP to a locked user."""
        
        # Check if user has admin privileges
        if request.user.role != SaccoUser.ADMIN:
            return Response(
                {"error": "You do not have permission to reset user passwords."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            target_user = SaccoUser.objects.get(id=user_id)
            
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
                    settings.DEFAULT_FROM_EMAIL,
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


class ToggleUserStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, user_id):
        """Toggle a user's active status (put on hold/activate)."""
        
        # Check if user has admin privileges
        if request.user.role != SaccoUser.ADMIN:
            return Response(
                {"error": "You do not have permission to change user status."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            target_user = SaccoUser.objects.get(id=user_id)
            
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


class VerifyDocumentView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, document_id):
        """Verify a user's document."""
        
        # Check if user has admin privileges
        if request.user.role != SaccoUser.ADMIN:
            return Response(
                {"error": "You do not have permission to verify documents."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            document = UserDocument.objects.get(id=document_id)
            
            # Update verification status
            document.is_verified = True
            document.verified_at = timezone.now()
            document.verified_by = request.user
            document.save()
            
            # Check if all required documents are verified
            user = document.user
            all_verified = True
            
            # Check if user has uploaded and verified both ID sides
            id_front = UserDocument.objects.filter(
                user=user, 
                document_type='ID_FRONT', 
                is_verified=True
            ).exists()
            
            id_back = UserDocument.objects.filter(
                user=user, 
                document_type='ID_BACK', 
                is_verified=True
            ).exists()
            
            if not (id_front and id_back):
                all_verified = False
            
            # Update user verification status if all documents are verified
            if all_verified and not user.is_verified:
                user.is_verified = True
                user.save()
            
            # Log the activity
            ActivityLog.objects.create(
                user=request.user,
                action='DOCUMENT_VERIFY',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                description=f"Verified {document.get_document_type_display()} for {document.user.email}.",
            )
            
            return Response({
                'message': 'Document verified successfully.',
                'user_verified': user.is_verified
            }, status=status.HTTP_200_OK)
            
        except UserDocument.DoesNotExist:
            return Response(
                {"error": "Document not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )


class SendMassEmailView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Send a mass email to all members."""
        
        # Check if user has admin privileges
        if request.user.role != SaccoUser.ADMIN:
            return Response(
                {"error": "You do not have permission to send mass emails."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        subject = request.data.get('subject')
        message = request.data.get('message')
        email_type = request.data.get('type', 'general')  # e.g., contribution_reminder, general
        
        if not subject or not message:
            return Response(
                {"error": "Subject and message are required."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get all active members
        members = SaccoUser.objects.filter(
            role=SaccoUser.MEMBER,
            is_active=True,
            is_on_hold=False
        )
        
        # For HTML email (preferred)
        html_message = render_to_string('emails/mass_email.html', {
            'message': message,
            'admin_name': request.user.full_name or request.user.email,
        })
        
        # Send emails in batches to avoid timeout
        batch_size = 50
        sent_count = 0
        error_count = 0
        
        for i in range(0, len(members), batch_size):
            batch = members[i:i+batch_size]
            recipient_list = [member.email for member in batch]
            
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    recipient_list,
                    html_message=html_message,
                    fail_silently=True,  # Continue on individual failures
                )
                sent_count += len(recipient_list)
            except Exception as e:
                logger.error(f"Failed to send batch email: {str(e)}")
                error_count += len(recipient_list)
        
        # Log the activity
        ActivityLog.objects.create(
            user=request.user,
            action='MASS_EMAIL',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            description=f"Sent mass email ({email_type}) to {sent_count} members.",
        )
        
        return Response({
            'message': f'Emails sent to {sent_count} members. Failed: {error_count}.'
        }, status=status.HTTP_200_OK)

class ListInvitationsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """List all invitations sent by the admin."""
        
        # Check if user has admin privileges
        if request.user.role != SaccoUser.ADMIN:
            return Response(
                {"error": "You do not have permission to view invitations."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get all invitations
        invitations = Invitation.objects.all().order_by('-created_at')
        
        # Optional filtering by email
        email_filter = request.query_params.get('email')
        if email_filter:
            invitations = invitations.filter(email__icontains=email_filter)
        
        # Optional filtering by status
        status_filter = request.query_params.get('status')
        if status_filter:
            if status_filter == 'used':
                invitations = invitations.filter(is_used=True)
            elif status_filter == 'pending':
                now = timezone.now()
                invitations = invitations.filter(is_used=False, expires_at__gt=now)
            elif status_filter == 'expired':
                now = timezone.now()
                invitations = invitations.filter(is_used=False, expires_at__lte=now)
        
        # Serialize and return data
        serializer = InvitationListSerializer(invitations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ResendInvitationView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, invitation_id):
        """Resend an invitation."""
        
        # Check if user has admin privileges
        if request.user.role != SaccoUser.ADMIN:
            return Response(
                {"error": "You do not have permission to resend invitations."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # Get the invitation
            invitation = Invitation.objects.get(id=invitation_id)
            
            # Check if invitation is already used
            if invitation.is_used:
                return Response(
                    {"error": "This invitation has already been used."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Generate new OTP and expiration time
            invitation.otp = ''.join(random.choices(string.digits, k=6))
            invitation.expires_at = timezone.now() + timedelta(hours=48)
            invitation.save()
            
            # Send the invitation email
            subject = 'Invitation to join SACCO (Resent)'
            message = f"""
            You have been invited to join our SACCO system.
            Your OTP code is: {invitation.otp}
            This code will expire in 48 hours.
            
            Please use this code to complete your registration.
            """
            
            # For HTML email (preferred)
            html_message = render_to_string('emails/invitation.html', {
                'otp': invitation.otp,
                'expiry_hours': 48,
                'inviter_name': request.user.full_name or request.user.email,
                'is_resend': True
            })
            
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [invitation.email],
                    html_message=html_message,
                    fail_silently=False,
                )
                
                # Log the activity
                ActivityLog.objects.create(
                    user=request.user,
                    action='INVITE',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    description=f"Resent invitation to {invitation.email}.",
                )
                
                return Response({"message": "Invitation resent successfully."}, status=status.HTTP_200_OK)
                
            except Exception as e:
                logger.error(f"Failed to resend invitation email: {str(e)}")
                return Response(
                    {"error": "Failed to send invitation email."}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Invitation.DoesNotExist:
            return Response(
                {"error": "Invitation not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )