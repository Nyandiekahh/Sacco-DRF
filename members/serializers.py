# members/serializers.py

from rest_framework import serializers
from authentication.models import SaccoUser, UserDocument
from sacco_core.models import MemberShareSummary, MonthlyContribution, ShareCapital, Loan


class MemberDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for member information - Admin view"""
    
    documents = serializers.SerializerMethodField()
    share_summary = serializers.SerializerMethodField()
    account_status = serializers.SerializerMethodField()
    
    class Meta:
        model = SaccoUser
        fields = [
            'id', 'email', 'full_name', 'membership_number', 'id_number',
            'phone_number', 'whatsapp_number', 'mpesa_number',
            'bank_name', 'bank_account_number', 'bank_account_name',
            'date_joined', 'is_active', 'is_verified', 'is_on_hold',
            'on_hold_reason', 'share_capital_term', 'documents',
            'share_summary', 'account_status'
        ]
    
    def get_documents(self, obj):
        """Get document verification status"""
        documents = UserDocument.objects.filter(user=obj)
        return [
            {
                'id': str(doc.id),
                'document_type': doc.document_type,
                'document_type_display': doc.get_document_type_display(),
                'is_verified': doc.is_verified,
                'uploaded_at': doc.uploaded_at,
                'verified_at': doc.verified_at,
                'document_url': self.context['request'].build_absolute_uri(doc.document.url) if doc.document else None
            }
            for doc in documents
        ]
    
    def get_share_summary(self, obj):
        """Get member's share summary"""
        try:
            summary = MemberShareSummary.objects.get(member=obj)
            return {
                'total_share_capital': summary.total_share_capital,
                'share_capital_target': summary.share_capital_target,
                'share_capital_completion_percentage': summary.share_capital_completion_percentage,
                'total_contributions': summary.total_contributions,
                'total_deposits': summary.total_deposits,
                'percentage_of_total_pool': summary.percentage_of_total_pool,
                'number_of_shares': summary.number_of_shares,
                'total_dividends_received': summary.total_dividends_received,
                'last_dividend_amount': summary.last_dividend_amount,
                'last_dividend_date': summary.last_dividend_date
            }
        except MemberShareSummary.DoesNotExist:
            return None
    
    def get_account_status(self, obj):
        """Get account status information"""
        return {
            'is_locked': obj.is_locked,
            'failed_login_attempts': obj.failed_login_attempts,
            'last_failed_login': obj.last_failed_login,
            'account_locked_until': obj.account_locked_until
        }


class MemberShareSummarySerializer(serializers.ModelSerializer):
    """Serializer for member share summary"""
    
    member_details = serializers.SerializerMethodField()
    
    class Meta:
        model = MemberShareSummary
        fields = [
            'id', 'member_details', 'total_share_capital', 'share_capital_target',
            'share_capital_completion_percentage', 'total_contributions',
            'current_year_contributions', 'previous_year_contributions',
            'total_deposits', 'percentage_of_total_pool', 'number_of_shares',
            'total_dividends_received', 'last_dividend_amount', 'last_dividend_date',
            'updated_at'
        ]
    
    def get_member_details(self, obj):
        """Get basic member details"""
        return {
            'id': str(obj.member.id),
            'full_name': obj.member.full_name,
            'membership_number': obj.member.membership_number,
            'email': obj.member.email
        }


class MemberContributionSerializer(serializers.ModelSerializer):
    """Serializer for monthly contributions"""
    
    member_details = serializers.SerializerMethodField()
    month_name = serializers.SerializerMethodField()
    recorder = serializers.SerializerMethodField()
    
    class Meta:
        model = MonthlyContribution
        fields = [
            'id', 'member_details', 'year', 'month', 'month_name',
            'amount', 'transaction_date', 'reference_number',
            'transaction_code', 'transaction_message', 'created_at',
            'recorder'
        ]
    
    def get_member_details(self, obj):
        """Get basic member details"""
        return {
            'id': str(obj.member.id),
            'full_name': obj.member.full_name,
            'membership_number': obj.member.membership_number
        }
    
    def get_month_name(self, obj):
        """Get the month name from the month number"""
        months = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ]
        return months[obj.month - 1]
    
    def get_recorder(self, obj):
        """Get the admin who recorded the contribution"""
        if obj.created_by:
            return {
                'id': str(obj.created_by.id),
                'full_name': obj.created_by.full_name,
                'email': obj.created_by.email
            }
        return None


class ShareCapitalSerializer(serializers.ModelSerializer):
    """Serializer for share capital payments"""
    
    member_details = serializers.SerializerMethodField()
    recorder = serializers.SerializerMethodField()
    
    class Meta:
        model = ShareCapital
        fields = [
            'id', 'member_details', 'amount', 'transaction_date',
            'reference_number', 'transaction_code', 'transaction_message',
            'created_at', 'recorder'
        ]
    
    def get_member_details(self, obj):
        """Get basic member details"""
        return {
            'id': str(obj.member.id),
            'full_name': obj.member.full_name,
            'membership_number': obj.member.membership_number
        }
    
    def get_recorder(self, obj):
        """Get the admin who recorded the payment"""
        if obj.created_by:
            return {
                'id': str(obj.created_by.id),
                'full_name': obj.created_by.full_name,
                'email': obj.created_by.email
            }
        return None


class MemberLoanSerializer(serializers.ModelSerializer):
    """Serializer for member loans"""
    
    member_details = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    approver = serializers.SerializerMethodField()
    disburser = serializers.SerializerMethodField()
    repayments = serializers.SerializerMethodField()
    
    class Meta:
        model = Loan
        fields = [
            'id', 'member_details', 'amount', 'interest_rate', 'application_date',
            'status', 'status_display', 'purpose', 'term_months', 'approval_date',
            'disbursement_date', 'expected_completion_date', 'processing_fee',
            'insurance_fee', 'disbursed_amount', 'total_expected_repayment',
            'total_repaid', 'remaining_balance', 'approver', 'disburser',
            'rejection_reason', 'created_at', 'updated_at', 'repayments'
        ]
    
    def get_member_details(self, obj):
        """Get basic member details"""
        return {
            'id': str(obj.member.id),
            'full_name': obj.member.full_name,
            'membership_number': obj.member.membership_number
        }
    
    def get_status_display(self, obj):
        """Get the status display text"""
        return obj.get_status_display()
    
    def get_approver(self, obj):
        """Get the admin who approved the loan"""
        if obj.approved_by:
            return {
                'id': str(obj.approved_by.id),
                'full_name': obj.approved_by.full_name,
                'email': obj.approved_by.email
            }
        return None
    
    def get_disburser(self, obj):
        """Get the admin who disbursed the loan"""
        if obj.disbursed_by:
            return {
                'id': str(obj.disbursed_by.id),
                'full_name': obj.disbursed_by.full_name,
                'email': obj.disbursed_by.email
            }
        return None
    
    def get_repayments(self, obj):
        """Get the loan repayments"""
        repayments = obj.repayments.all().order_by('-transaction_date')
        return [
            {
                'id': str(repayment.id),
                'amount': repayment.amount,
                'transaction_date': repayment.transaction_date,
                'reference_number': repayment.reference_number,
                'transaction_code': repayment.transaction_code,
                'created_at': repayment.created_at,
                'recorded_by': {
                    'id': str(repayment.created_by.id),
                    'full_name': repayment.created_by.full_name,
                    'email': repayment.created_by.email
                } if repayment.created_by else None
            }
            for repayment in repayments
        ]