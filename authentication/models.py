# authentication/models.py

import uuid
import random
import string
from datetime import datetime, timedelta
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.conf import settings

class SaccoUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'ADMIN')
        
        return self.create_user(email, password, **extra_fields)

class SaccoUser(AbstractBaseUser, PermissionsMixin):
    ADMIN = 'ADMIN'
    MEMBER = 'MEMBER'
    
    ROLE_CHOICES = [
        (ADMIN, 'Admin'),
        (MEMBER, 'Member'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=MEMBER)
    
    # Additional profile fields
    id_number = models.CharField(max_length=20, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    whatsapp_number = models.CharField(max_length=15, blank=True)
    mpesa_number = models.CharField(max_length=15, blank=True)
    
    # Bank details
    bank_name = models.CharField(max_length=100, blank=True)
    bank_account_number = models.CharField(max_length=50, blank=True)
    bank_account_name = models.CharField(max_length=100, blank=True)
    
    # Membership details
    membership_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)  # For KYC verification
    
    # Account status
    is_on_hold = models.BooleanField(default=False)
    on_hold_reason = models.TextField(blank=True)
    
    # Security fields
    failed_login_attempts = models.PositiveIntegerField(default=0)
    last_failed_login = models.DateTimeField(null=True, blank=True)
    account_locked_until = models.DateTimeField(null=True, blank=True)
    
    # Admin fields
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    
    # Share capital payment terms (in months)
    share_capital_term = models.PositiveIntegerField(default=12)  # Default to 12 months
    
    objects = SaccoUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    def __str__(self):
        return self.email
    
    def save(self, *args, **kwargs):
        # Generate membership number if not provided
        if not self.membership_number and self.role == self.MEMBER:
            year = timezone.now().year
            count = SaccoUser.objects.filter(role=self.MEMBER).count() + 1
            self.membership_number = f"SACCO-{year}-{count:04d}"
        
        super().save(*args, **kwargs)
    
    @property
    def is_locked(self):
        if self.account_locked_until and timezone.now() < self.account_locked_until:
            return True
        return False
    
    def increment_failed_login(self):
        self.failed_login_attempts += 1
        self.last_failed_login = timezone.now()
        
        # Lock account after X failed attempts
        if self.failed_login_attempts >= settings.ACCOUNT_LOCKOUT_ATTEMPTS:
            self.account_locked_until = timezone.now() + timedelta(minutes=settings.ACCOUNT_LOCKOUT_TIME)
        
        self.save()
    
    def reset_failed_login(self):
        self.failed_login_attempts = 0
        self.last_failed_login = None
        self.account_locked_until = None
        self.save()


class UserDocument(models.Model):
    DOCUMENT_TYPES = [
        ('ID_FRONT', 'ID Front'),
        ('ID_BACK', 'ID Back'),
        ('PASSPORT', 'Passport Photo'),
        ('OTHER', 'Other Document'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(SaccoUser, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    document = models.FileField(upload_to='user_documents/')
    is_verified = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        SaccoUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='verified_documents'
    )
    
    def __str__(self):
        return f"{self.user.email} - {self.get_document_type_display()}"


class Invitation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    invited_by = models.ForeignKey(
        SaccoUser, 
        on_delete=models.CASCADE, 
        related_name='sent_invitations'
    )
    share_capital_term = models.PositiveIntegerField(default=12)  # 12 or 24 months
    
    def __str__(self):
        return f"Invitation for {self.email}"
    
    def save(self, *args, **kwargs):
        # Generate OTP if not provided
        if not self.otp:
            self.otp = ''.join(random.choices(string.digits, k=6))
        
        # Set expiration if not provided (default 48 hours)
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=48)
        
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        return not self.is_used and not self.is_expired


class OTPRequest(models.Model):
    OTP_TYPE_CHOICES = [
        ('RESET', 'Password Reset'),
        ('LOGIN', 'Login Verification'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(SaccoUser, on_delete=models.CASCADE, related_name='otp_requests')
    otp = models.CharField(max_length=6)
    otp_type = models.CharField(max_length=10, choices=OTP_TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    def __str__(self):
        return f"OTP for {self.user.email} - {self.otp_type}"
    
    def save(self, *args, **kwargs):
        # Generate OTP if not provided
        if not self.otp:
            self.otp = ''.join(random.choices(string.digits, k=6))
        
        # Set expiration if not provided (default 15 minutes)
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=15)
        
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        return not self.is_used and not self.is_expired


class ActivityLog(models.Model):
    ACTION_TYPES = [
        ('LOGIN', 'User Login'),
        ('INVITE', 'User Invitation'),
        ('ACCOUNT_CREATE', 'Account Creation'),
        ('PASSWORD_RESET', 'Password Reset'),
        ('DOCUMENT_UPLOAD', 'Document Upload'),
        ('DOCUMENT_VERIFY', 'Document Verification'),
        ('ACCOUNT_UPDATE', 'Account Update'),
        ('ACCOUNT_LOCK', 'Account Lock'),
        ('ACCOUNT_UNLOCK', 'Account Unlock'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(SaccoUser, on_delete=models.SET_NULL, null=True, related_name='activity_logs')
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        if self.user:
            return f"{self.user.email} - {self.get_action_display()} at {self.created_at}"
        return f"System - {self.get_action_display()} at {self.created_at}"