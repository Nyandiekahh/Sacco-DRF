from rest_framework import serializers
from .models import SaccoSettings

class SaccoSettingsSerializer(serializers.ModelSerializer):
    """Serializer for SACCO settings model"""
    
    class Meta:
        model = SaccoSettings
        fields = [
            'id', 'share_value', 'minimum_monthly_contribution', 
            'loan_interest_rate', 'maximum_loan_multiplier',
            'loan_processing_fee_percentage', 'loan_insurance_percentage',
            'phone_number', 'email', 'postal_address', 'physical_address',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']