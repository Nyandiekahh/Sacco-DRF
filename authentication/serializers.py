# authentication/serializers.py

import re
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import SaccoUser, Invitation, UserDocument


class InvitationSerializer(serializers.ModelSerializer):
    """Serializer for creating member invitations"""
    
    class Meta:
        model = Invitation
        fields = ['email', 'share_capital_term']
        
    def validate_share_capital_term(self, value):
        if value not in [12, 24]:
            raise serializers.ValidationError("Share capital term must be either 12 or 24 months.")
        return value


class OTPLoginSerializer(serializers.Serializer):
    """Serializer for OTP-based login"""
    
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for completing user registration"""
    
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = SaccoUser
        fields = [
            'email', 'password', 'confirm_password', 'full_name', 'id_number', 
            'phone_number', 'whatsapp_number', 'mpesa_number', 
            'bank_name', 'bank_account_number', 'bank_account_name'
        ]
        
    def validate(self, attrs):
        # Check if passwords match
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        # Validate ID number
        id_number = attrs.get('id_number')
        if id_number and not re.match(r'^\d{8,10}$', id_number):
            raise serializers.ValidationError({"id_number": "ID number must be between 8-10 digits."})
        
        # Validate phone numbers
        phone_number = attrs.get('phone_number')
        if phone_number and not re.match(r'^\+?\d{10,15}$', phone_number):
            raise serializers.ValidationError({"phone_number": "Invalid phone number format."})
        
        whatsapp_number = attrs.get('whatsapp_number')
        if whatsapp_number and not re.match(r'^\+?\d{10,15}$', whatsapp_number):
            raise serializers.ValidationError({"whatsapp_number": "Invalid WhatsApp number format."})
        
        mpesa_number = attrs.get('mpesa_number')
        if mpesa_number and not re.match(r'^\+?\d{10,15}$', mpesa_number):
            raise serializers.ValidationError({"mpesa_number": "Invalid M-Pesa number format."})
        
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile"""
    
    documents = serializers.SerializerMethodField()
    is_admin = serializers.SerializerMethodField()
    
    class Meta:
        model = SaccoUser
        fields = [
            'id', 'email', 'full_name', 'id_number', 'phone_number', 
            'whatsapp_number', 'mpesa_number', 'bank_name', 
            'bank_account_number', 'bank_account_name', 'membership_number',
            'date_joined', 'is_active', 'is_verified', 'is_on_hold',
            'on_hold_reason', 'documents', 'is_admin', 'share_capital_term'
        ]
        read_only_fields = [
            'id', 'email', 'membership_number', 'date_joined', 
            'is_active', 'is_verified', 'is_on_hold', 'on_hold_reason',
            'is_admin', 'share_capital_term'
        ]
    
    def get_documents(self, obj):
        """Get document verification status"""
        document_status = {
            'id_front': {
                'uploaded': False,
                'verified': False
            },
            'id_back': {
                'uploaded': False,
                'verified': False
            },
            'passport': {
                'uploaded': False,
                'verified': False
            }
        }
        
        documents = obj.documents.all()
        for doc in documents:
            if doc.document_type == 'ID_FRONT':
                document_status['id_front']['uploaded'] = True
                document_status['id_front']['verified'] = doc.is_verified
            elif doc.document_type == 'ID_BACK':
                document_status['id_back']['uploaded'] = True
                document_status['id_back']['verified'] = doc.is_verified
            elif doc.document_type == 'PASSPORT':
                document_status['passport']['uploaded'] = True
                document_status['passport']['verified'] = doc.is_verified
        
        return document_status
    
    def get_is_admin(self, obj):
        """Check if user is an admin"""
        return obj.role == SaccoUser.ADMIN
    
    def validate(self, attrs):
        # Validate ID number
        id_number = attrs.get('id_number')
        if id_number and not re.match(r'^\d{8,10}$', id_number):
            raise serializers.ValidationError({"id_number": "ID number must be between 8-10 digits."})
        
        # Validate phone numbers
        phone_number = attrs.get('phone_number')
        if phone_number and not re.match(r'^\+?\d{10,15}$', phone_number):
            raise serializers.ValidationError({"phone_number": "Invalid phone number format."})
        
        whatsapp_number = attrs.get('whatsapp_number')
        if whatsapp_number and not re.match(r'^\+?\d{10,15}$', whatsapp_number):
            raise serializers.ValidationError({"whatsapp_number": "Invalid WhatsApp number format."})
        
        mpesa_number = attrs.get('mpesa_number')
        if mpesa_number and not re.match(r'^\+?\d{10,15}$', mpesa_number):
            raise serializers.ValidationError({"mpesa_number": "Invalid M-Pesa number format."})
        
        return attrs


class DocumentUploadSerializer(serializers.ModelSerializer):
    """Serializer for document uploads"""
    
    class Meta:
        model = UserDocument
        fields = ['document_type', 'document']
    
    def validate_document(self, value):
        # Validate file size (max 5MB)
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Maximum file size is 5MB.")
        
        # Validate file extension
        valid_extensions = ['jpg', 'jpeg', 'png', 'pdf']
        extension = value.name.split('.')[-1].lower()
        if extension not in valid_extensions:
            raise serializers.ValidationError(
                f"Unsupported file extension. Supported formats: {', '.join(valid_extensions)}"
            )
        
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for password reset requests"""
    
    email = serializers.EmailField()


class OTPVerificationSerializer(serializers.Serializer):
    """Serializer for OTP verification"""
    
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)


class PasswordResetSerializer(serializers.Serializer):
    """Serializer for password reset"""
    
    new_password = serializers.CharField(required=True, validators=[validate_password])
    confirm_password = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs


class UserListSerializer(serializers.ModelSerializer):
    """Serializer for listing users (admin view)"""
    
    verification_status = serializers.SerializerMethodField()
    
    class Meta:
        model = SaccoUser
        fields = [
            'id', 'email', 'full_name', 'membership_number', 'date_joined',
            'is_active', 'is_verified', 'is_on_hold', 'verification_status',
            'phone_number', 'failed_login_attempts', 'account_locked_until',
            'share_capital_term'
        ]
    
    def get_verification_status(self, obj):
        """Get document verification status"""
        id_front = UserDocument.objects.filter(
            user=obj, document_type='ID_FRONT', is_verified=True
        ).exists()
        
        id_back = UserDocument.objects.filter(
            user=obj, document_type='ID_BACK', is_verified=True
        ).exists()
        
        passport = UserDocument.objects.filter(
            user=obj, document_type='PASSPORT', is_verified=True
        ).exists()
        
        return {
            'id_front': id_front,
            'id_back': id_back,
            'passport': passport,
            'complete': id_front and id_back
        }


class ActivityLogSerializer(serializers.Serializer):
    """Serializer for activity logs"""
    
    id = serializers.UUIDField(read_only=True)
    user = serializers.SerializerMethodField()
    action = serializers.CharField(read_only=True)
    action_display = serializers.SerializerMethodField()
    ip_address = serializers.IPAddressField(read_only=True)
    description = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    
    def get_user(self, obj):
        if obj.user:
            return {
                'id': obj.user.id,
                'email': obj.user.email,
                'full_name': obj.user.full_name,
                'membership_number': obj.user.membership_number
            }
        return None
    
    def get_action_display(self, obj):
        return obj.get_action_display()

class InvitationListSerializer(serializers.ModelSerializer):
    invited_by_email = serializers.EmailField(source='invited_by.email', read_only=True)
    invited_by_name = serializers.CharField(source='invited_by.full_name', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Invitation
        fields = [
            'id', 'email', 'created_at', 'expires_at', 'is_used', 
            'invited_by_email', 'invited_by_name', 'share_capital_term',
            'is_expired'
        ]
        read_only_fields = fields