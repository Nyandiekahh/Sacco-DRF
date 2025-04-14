# settings_api/utils.py
from .models import SaccoSettings

def get_sacco_settings():
    """
    Get current SACCO settings.
    This function should be used by other apps to access SACCO settings.
    """
    return SaccoSettings.get_settings()

def get_loan_interest_rate():
    """Get current loan interest rate"""
    settings = get_sacco_settings()
    return settings.loan_interest_rate / 100  # Convert to decimal

def get_loan_processing_fees(loan_amount):
    """Calculate loan processing fees for a given loan amount"""
    settings = get_sacco_settings()
    return (settings.loan_processing_fee_percentage / 100) * loan_amount

def get_max_loan_amount(user_shares):
    """Calculate max loan amount based on user's shares"""
    settings = get_sacco_settings()
    return user_shares * settings.maximum_loan_multiplier

def is_loan_eligible(user):
    """Check if user is eligible for a loan based on membership duration"""
    from django.utils import timezone
    from datetime import timedelta
    
    settings = get_sacco_settings()
    min_period = settings.minimum_membership_period_months
    
    eligible_date = user.date_joined + timedelta(days=30 * min_period)
    return timezone.now() >= eligible_date and user.is_verified