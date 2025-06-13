# settings_api/models.py
from django.db import models

class SaccoSettings(models.Model):
    """Model for storing SACCO global settings"""
    
    # Share Capital Settings
    share_value = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=100.00, 
        help_text="Value of a single share"
    )
    minimum_monthly_contribution = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=1000.00, 
        help_text="Minimum required monthly contribution"
    )
    
    # Loan Settings
    loan_interest_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=10.00, 
        help_text="Annual interest rate for loans (%)"
    )
    maximum_loan_multiplier = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=3.00, 
        help_text="Maximum loan amount as a multiple of shares"
    )
    loan_processing_fee_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=1.00, 
        help_text="Loan processing fee as percentage of loan amount"
    )
    loan_insurance_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=1.00, 
        help_text="Loan insurance fee as percentage of loan amount"
    )
    maximum_loan_term_months = models.PositiveIntegerField(
        default=36,
        help_text="Maximum loan repayment period in months"
    )
    minimum_guarantors = models.PositiveIntegerField(
        default=2,
        help_text="Minimum number of guarantors required for a loan"
    )
    
    # Member Settings
    minimum_membership_period_months = models.PositiveIntegerField(
        default=3,
        help_text="Minimum period of membership before loan eligibility (months)"
    )
    
    # Dividend Settings
    dividend_calculation_method = models.CharField(
        max_length=20,
        choices=[
            ('SHARES', 'Based on Shares'),
            ('DEPOSITS', 'Based on Deposits'),
            ('BOTH', 'Based on Both')
        ],
        default='BOTH',
        help_text="Method for calculating dividends"
    )
    
    # System Settings
    enable_sms_notifications = models.BooleanField(
        default=True,
        help_text="Enable SMS notifications for transactions"
    )
    enable_email_notifications = models.BooleanField(
        default=True,
        help_text="Enable email notifications for transactions"
    )
    
    # Contact Information
    sacco_name = models.CharField(
        max_length=100, 
        default="Sample SACCO", 
        help_text="Official SACCO name"
    )
    phone_number = models.CharField(
        max_length=20, 
        default="+254700000000", 
        help_text="SACCO contact phone number"
    )
    email = models.EmailField(
        default="info@sacco.com", 
        help_text="SACCO contact email"
    )
    postal_address = models.CharField(
        max_length=100, 
        default="P.O. Box 12345, Nairobi", 
        help_text="SACCO postal address"
    )
    physical_address = models.CharField(
        max_length=200, 
        default="Nairobi, Kenya", 
        help_text="SACCO physical address"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "SACCO Setting"
        verbose_name_plural = "SACCO Settings"
        
    def __str__(self):
        return f"SACCO Settings (Last updated: {self.updated_at.strftime('%Y-%m-%d')})"
    
    @classmethod
    def get_settings(cls):
        """Get or create SACCO settings"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings