# loans/serializers.py

from rest_framework import serializers
from authentication.models import SaccoUser
from sacco_core.models import Loan, LoanRepayment
from .models import LoanApplication, RepaymentSchedule, LoanStatement, LoanNotification, PaymentMethod, LoanDisbursement, GuarantorRequest, GuarantorLimit


class LoanApplicationSerializer(serializers.ModelSerializer):
    """Serializer for loan applications"""
    
    member_name = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    
    class Meta:
        model = LoanApplication
        fields = [
            'id', 'member', 'member_name', 'amount', 'purpose',
            'term_months', 'application_date', 'status', 'status_display',
            'has_guarantor', 'guarantor_name', 'guarantor_contact',
            'guarantor_relationship', 'application_document',
            'reviewed_date', 'reviewed_by', 'rejection_reason',
            'loan', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'application_date', 'status', 'reviewed_date',
            'reviewed_by', 'rejection_reason', 'loan', 'created_at',
            'updated_at', 'member_name', 'status_display'
        ]
    
    def get_member_name(self, obj):
        return obj.member.full_name
    
    def get_status_display(self, obj):
        return obj.get_status_display()
    
    def validate_amount(self, value):
        """Validate loan amount"""
        if value <= 0:
            raise serializers.ValidationError("Loan amount must be greater than zero.")
        return value
    
    def validate_term_months(self, value):
        """Validate loan term"""
        if value <= 0:
            raise serializers.ValidationError("Loan term must be greater than zero.")
        return value


class LoanSerializer(serializers.ModelSerializer):
    """Serializer for loans"""
    
    member_name = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    approver_name = serializers.SerializerMethodField()
    disburser_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Loan
        fields = [
            'id', 'member', 'member_name', 'amount', 'interest_rate',
            'application_date', 'status', 'status_display', 'purpose',
            'term_months', 'approval_date', 'disbursement_date',
            'expected_completion_date', 'processing_fee', 'insurance_fee',
            'disbursed_amount', 'total_expected_repayment', 'total_repaid',
            'remaining_balance', 'approved_by', 'approver_name',
            'disbursed_by', 'disburser_name', 'rejection_reason',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'application_date', 'status', 'approval_date',
            'disbursement_date', 'expected_completion_date',
            'processing_fee', 'insurance_fee', 'disbursed_amount',
            'total_expected_repayment', 'total_repaid', 'remaining_balance',
            'approved_by', 'disbursed_by', 'rejection_reason',
            'created_at', 'updated_at', 'member_name', 'status_display',
            'approver_name', 'disburser_name'
        ]
    
    def get_member_name(self, obj):
        return obj.member.full_name
    
    def get_status_display(self, obj):
        return obj.get_status_display()
    
    def get_approver_name(self, obj):
        if obj.approved_by:
            return obj.approved_by.full_name
        return None
    
    def get_disburser_name(self, obj):
        if obj.disbursed_by:
            return obj.disbursed_by.full_name
        return None


class LoanRepaymentSerializer(serializers.ModelSerializer):
    """Serializer for loan repayments"""
    
    recorded_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = LoanRepayment
        fields = [
            'id', 'loan', 'amount', 'transaction_date', 'reference_number',
            'transaction_code', 'transaction_message', 'created_at',
            'created_by', 'recorded_by_name'
        ]
        read_only_fields = [
            'id', 'loan', 'created_at', 'created_by', 'recorded_by_name'
        ]
    
    def get_recorded_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.full_name
        return None
    
    def validate_amount(self, value):
        """Validate repayment amount"""
        if value <= 0:
            raise serializers.ValidationError("Repayment amount must be greater than zero.")
        return value


class RepaymentScheduleSerializer(serializers.ModelSerializer):
    """Serializer for loan repayment schedules"""
    
    class Meta:
        model = RepaymentSchedule
        fields = [
            'id', 'loan', 'installment_number', 'due_date', 'amount_due',
            'principal_amount', 'interest_amount', 'amount_paid',
            'remaining_amount', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = fields


class LoanStatementSerializer(serializers.ModelSerializer):
    """Serializer for loan statements"""
    
    member_name = serializers.SerializerMethodField()
    generated_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = LoanStatement
        fields = [
            'id', 'loan', 'member_name', 'statement_date', 'principal_amount',
            'interest_rate', 'total_amount', 'amount_paid', 'remaining_balance',
            'payoff_amount', 'overdue_amount', 'next_payment_date',
            'next_payment_amount', 'statement_file', 'generated_by',
            'generated_by_name', 'created_at'
        ]
        read_only_fields = fields
    
    def get_member_name(self, obj):
        return obj.loan.member.full_name
    
    def get_generated_by_name(self, obj):
        if obj.generated_by:
            return obj.generated_by.full_name
        return None


class LoanNotificationSerializer(serializers.ModelSerializer):
    """Serializer for loan notifications"""
    
    class Meta:
        model = LoanNotification
        fields = [
            'id', 'loan', 'notification_type', 'message', 'sent',
            'sent_at', 'created_at'
        ]
        read_only_fields = fields


class LoanGuarantorSerializer(serializers.Serializer):
    """Serializer for loan guarantors"""
    
    member_id = serializers.UUIDField(required=False)
    name = serializers.CharField(required=False)
    id_number = serializers.CharField(required=False)
    phone_number = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    relationship = serializers.CharField(required=False)
    guarantee_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    guarantee_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    
    def validate(self, data):
        """Validate guarantor data"""
        # Either member_id or external guarantor details must be provided
        if not data.get('member_id') and not data.get('name'):
            raise serializers.ValidationError("Either member ID or guarantor name must be provided.")
        
        # Validate member if provided
        if data.get('member_id'):
            try:
                member = SaccoUser.objects.get(id=data['member_id'], role='MEMBER')
            except SaccoUser.DoesNotExist:
                raise serializers.ValidationError("Member not found.")
        
        # For external guarantors, validate required fields
        if data.get('name'):
            if not data.get('id_number'):
                raise serializers.ValidationError("ID number is required for external guarantors.")
            if not data.get('phone_number'):
                raise serializers.ValidationError("Phone number is required for external guarantors.")
        
        return data
    
# Add these new serializers to your existing loans/serializers.py

class PaymentMethodSerializer(serializers.ModelSerializer):
    """Serializer for payment methods"""
    
    payment_type_display = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    
    class Meta:
        model = PaymentMethod
        fields = [
            'id', 'name', 'payment_type', 'payment_type_display', 
            'description', 'bank_name', 'account_name', 'account_number',
            'provider', 'phone_number', 'internal_code', 'status',
            'status_display', 'transaction_fee_percentage', 'transaction_fee_fixed',
            'is_default', 'allowed_for_disbursement', 'allowed_for_repayment',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at',
            'payment_type_display', 'status_display'
        ]
    
    def get_payment_type_display(self, obj):
        return obj.get_payment_type_display()
    
    def get_status_display(self, obj):
        return obj.get_status_display()


class LoanDisbursementSerializer(serializers.ModelSerializer):
    """Serializer for loan disbursements"""
    
    # Add a field for direct member payment method selection
    member_payment_method = serializers.ChoiceField(
        choices=['mpesa', 'bank'], 
        required=False,
        write_only=True
    )
    
    class Meta:
        model = LoanDisbursement
        fields = [
            'id', 'loan', 'amount', 'payment_method', 'payment_method_name',
            'reference_number', 'transaction_cost', 'net_amount', 
            'recipient_account', 'recipient_name', 'description',
            'disbursement_date', 'processed_by', 'processed_by_name',
            'created_at', 'member_payment_method'  # Added member_payment_method
        ]
        read_only_fields = [
            'id', 'loan', 'amount', 'net_amount',
            'recipient_name', 'processed_by', 'processed_by_name',
            'created_at', 'payment_method_name'
        ]
    
    def get_payment_method_name(self, obj):
        return obj.payment_method.name if obj.payment_method else None
    
    def get_processed_by_name(self, obj):
        return obj.processed_by.full_name if obj.processed_by else None
    
    def validate_reference_number(self, value):
        """Validate reference number"""
        if not value:
            raise serializers.ValidationError("Reference number is required.")
        
        # Check for duplicate reference number
        if LoanDisbursement.objects.filter(reference_number=value).exists():
            raise serializers.ValidationError("This reference number has already been used.")
        
        return value
    
    def validate(self, data):
        """Validate disbursement data"""
        
        # Ensure payment method is provided
        if 'payment_method' not in data:
            raise serializers.ValidationError({"payment_method": "Payment method is required"})
        
        # Validate recipient account based on payment method
        if 'payment_method' in data and 'recipient_account' in data:
            try:
                payment_method = PaymentMethod.objects.get(id=data['payment_method'])
                
                # For bank transfers, validate account format
                if payment_method.payment_type == 'BANK_TRANSFER' and not data['recipient_account']:
                    raise serializers.ValidationError({"recipient_account": "Bank account number is required"})
                
                # For mobile money, validate phone format
                if payment_method.payment_type == 'MOBILE_MONEY':
                    # Simple validation for phone number format
                    if not data['recipient_account'] or not re.match(r'^\+?[0-9]{10,15}$', data['recipient_account']):
                        raise serializers.ValidationError({"recipient_account": "Valid phone number is required"})
            except PaymentMethod.DoesNotExist:
                raise serializers.ValidationError({"payment_method": "Invalid payment method"})
        
        return data


# Update the existing LoanRepaymentSerializer to include payment method
class LoanRepaymentSerializer(serializers.ModelSerializer):
    """Serializer for loan repayments"""
    
    recorded_by_name = serializers.SerializerMethodField()
    payment_method_name = serializers.SerializerMethodField()
    
    class Meta:
        model = LoanRepayment
        fields = [
            'id', 'loan', 'amount', 'transaction_date', 'reference_number',
            'transaction_code', 'transaction_message', 'created_at',
            'created_by', 'recorded_by_name', 'payment_method', 'payment_method_name'
        ]
        read_only_fields = [
            'id', 'loan', 'created_at', 'created_by', 'recorded_by_name',
            'payment_method_name'
        ]
    
    def get_recorded_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.full_name
        return None
    
    def get_payment_method_name(self, obj):
        # This assumes you'll add a payment_method field to LoanRepayment model
        if hasattr(obj, 'payment_method') and obj.payment_method:
            return obj.payment_method.name
        return None
    
    def validate_amount(self, value):
        """Validate repayment amount"""
        if value <= 0:
            raise serializers.ValidationError("Repayment amount must be greater than zero.")
        return value
    
    def validate_reference_number(self, value):
        """Validate reference number"""
        if not value:
            raise serializers.ValidationError("Reference number is required.")
        
        # Check for duplicate reference number
        if LoanRepayment.objects.filter(reference_number=value).exists():
            raise serializers.ValidationError("This reference number has already been used.")
        
        return value

# Add these serializers to loans/serializers.py

class GuarantorLimitSerializer(serializers.ModelSerializer):
    """Serializer for guarantor limits"""
    
    member_name = serializers.SerializerMethodField()
    
    class Meta:
        model = GuarantorLimit
        fields = [
            'id', 'member', 'member_name', 'total_guaranteed_amount',
            'active_guarantees_count', 'maximum_guarantee_amount',
            'available_guarantee_amount', 'updated_at'
        ]
        read_only_fields = fields
    
    def get_member_name(self, obj):
        return obj.member.full_name


class EligibleGuarantorSerializer(serializers.ModelSerializer):
    """Serializer for eligible guarantors"""
    
    available_guarantee_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    maximum_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    
    class Meta:
        model = SaccoUser
        fields = [
            'id', 'full_name', 'email', 'phone_number', 
            'available_guarantee_amount', 'maximum_percentage'
        ]


class GuarantorRequestSerializer(serializers.ModelSerializer):
    """Serializer for guarantor requests"""
    
    guarantor_name = serializers.SerializerMethodField()
    requester_name = serializers.SerializerMethodField()
    loan_amount = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    
    class Meta:
        model = GuarantorRequest
        fields = [
            'id', 'loan_application', 'guarantor', 'guarantor_name',
            'requester', 'requester_name', 'loan_amount',
            'guarantee_amount', 'guarantee_percentage', 'status',
            'status_display', 'message', 'response_message',
            'requested_at', 'responded_at'
        ]
        read_only_fields = [
            'id', 'status_display', 'requester_name',
            'guarantor_name', 'loan_amount', 'requested_at', 'responded_at'
        ]
    
    def get_guarantor_name(self, obj):
        return obj.guarantor.full_name
    
    def get_requester_name(self, obj):
        return obj.requester.full_name
    
    def get_loan_amount(self, obj):
        return obj.loan_application.amount
    
    def get_status_display(self, obj):
        return obj.get_status_display()
    
    def validate(self, data):
        # Validate guarantee percentage
        if data.get('guarantee_percentage', 0) <= 0 or data.get('guarantee_percentage', 0) > 100:
            raise serializers.ValidationError("Guarantee percentage must be between 1% and 100%")
        
        # Calculate guarantee amount based on percentage
        loan_application = data.get('loan_application')
        if loan_application:
            loan_amount = loan_application.amount
            percentage = data.get('guarantee_percentage', 0)
            guarantee_amount = (percentage / 100) * loan_amount
            data['guarantee_amount'] = guarantee_amount
        
        # Check if guarantor has sufficient limit
        guarantor = data.get('guarantor')
        if guarantor:
            try:
                limit = GuarantorLimit.objects.get(member=guarantor)
                if data.get('guarantee_amount', 0) > limit.available_guarantee_amount:
                    raise serializers.ValidationError(
                        f"Guarantee amount exceeds guarantor's available limit of {limit.available_guarantee_amount}"
                    )
            except GuarantorLimit.DoesNotExist:
                # If no limit exists, create one
                GuarantorLimit.update_guarantor_limit(guarantor)
        
        return data