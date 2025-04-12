# members/views.py

from django.db.models import Q, Sum
from django.utils import timezone
from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.models import SaccoUser, ActivityLog, UserDocument
from authentication.serializers import UserListSerializer, UserProfileSerializer
from sacco_core.models import MemberShareSummary, MonthlyContribution, ShareCapital
from sacco_core.models import Loan, DividendDistribution, MemberDividend
from .serializers import (
    MemberDetailSerializer,
    MemberShareSummarySerializer,
    MemberContributionSerializer,
    MemberLoanSerializer
)


class AdminRequiredMixin:
    """Mixin to ensure the user is an admin"""
    
    def check_permissions(self, request):
        super().check_permissions(request)
        if not request.user.role == SaccoUser.ADMIN:
            self.permission_denied(
                request, 
                message="You do not have permission to perform this action."
            )


class MemberViewSet(AdminRequiredMixin, viewsets.ModelViewSet):
    """API endpoint for managing members - Admin only"""
    
    permission_classes = [permissions.IsAuthenticated]
    queryset = SaccoUser.objects.filter(role=SaccoUser.MEMBER)
    serializer_class = UserListSerializer
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return MemberDetailSerializer
        return UserListSerializer
    
    def get_queryset(self):
        queryset = SaccoUser.objects.filter(role=SaccoUser.MEMBER)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active)
        
        # Filter by verification status
        is_verified = self.request.query_params.get('is_verified')
        if is_verified is not None:
            is_verified = is_verified.lower() == 'true'
            queryset = queryset.filter(is_verified=is_verified)
        
        # Filter by on-hold status
        is_on_hold = self.request.query_params.get('is_on_hold')
        if is_on_hold is not None:
            is_on_hold = is_on_hold.lower() == 'true'
            queryset = queryset.filter(is_on_hold=is_on_hold)
        
        # Search by name, email, or membership number
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(full_name__icontains=search) |
                Q(email__icontains=search) |
                Q(membership_number__icontains=search) |
                Q(phone_number__icontains=search)
            )
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Toggle a member's active status"""
        
        member = self.get_object()
        member.is_active = not member.is_active
        member.save()
        
        # Log the activity
        action = 'ACCOUNT_LOCK' if not member.is_active else 'ACCOUNT_UNLOCK'
        ActivityLog.objects.create(
            user=request.user,
            action=action,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            description=f"{'Deactivated' if not member.is_active else 'Activated'} account for {member.email}."
        )
        
        return Response({
            'status': 'success',
            'message': f"Member {'deactivated' if not member.is_active else 'activated'} successfully."
        })
    
    @action(detail=True, methods=['get'])
    def contributions(self, request, pk=None):
        """Get a member's contribution history"""
        
        member = self.get_object()
        
        # Get query parameters for filtering
        year = request.query_params.get('year')
        month = request.query_params.get('month')
        
        contributions = MonthlyContribution.objects.filter(member=member)
        
        if year:
            contributions = contributions.filter(year=year)
        if month:
            contributions = contributions.filter(month=month)
        
        # Order by year and month (newest first)
        contributions = contributions.order_by('-year', '-month')
        
        serializer = MemberContributionSerializer(contributions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def share_capital(self, request, pk=None):
        """Get a member's share capital payments"""
        
        member = self.get_object()
        
        # Get query parameters for filtering
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        shares = ShareCapital.objects.filter(member=member)
        
        if date_from:
            shares = shares.filter(transaction_date__gte=date_from)
        if date_to:
            shares = shares.filter(transaction_date__lte=date_to)
        
        # Order by transaction date (newest first)
        shares = shares.order_by('-transaction_date')
        
        serializer = MemberContributionSerializer(shares, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def share_summary(self, request, pk=None):
        """Get a member's share summary"""
        
        member = self.get_object()
        
        try:
            summary = MemberShareSummary.objects.get(member=member)
        except MemberShareSummary.DoesNotExist:
            # Create a new summary if it doesn't exist
            summary = MemberShareSummary.update_member_summary(member)
        
        serializer = MemberShareSummarySerializer(summary)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def loans(self, request, pk=None):
        """Get a member's loans"""
        
        member = self.get_object()
        
        # Get query parameters for filtering
        status = request.query_params.get('status')
        
        loans = Loan.objects.filter(member=member)
        
        if status:
            loans = loans.filter(status=status.upper())
        
        # Order by application date (newest first)
        loans = loans.order_by('-application_date')
        
        serializer = MemberLoanSerializer(loans, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def dividends(self, request, pk=None):
        """Get a member's dividend history"""
        
        member = self.get_object()
        
        # Get query parameters for filtering
        year = request.query_params.get('year')
        
        dividends = MemberDividend.objects.filter(member=member)
        
        if year:
            dividends = dividends.filter(distribution__distribution_date__year=year)
        
        # Order by distribution date (newest first)
        dividends = dividends.order_by('-distribution__distribution_date')
        
        return Response({
            'dividends': [
                {
                    'id': str(dividend.id),
                    'distribution_date': dividend.distribution.distribution_date,
                    'amount': dividend.amount,
                    'percentage_share': dividend.percentage_share,
                    'distribution_total': dividend.distribution.total_amount,
                    'source': dividend.distribution.source,
                    'description': dividend.distribution.description
                }
                for dividend in dividends
            ]
        })
    
    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None):
        """Get a member's uploaded documents"""
        
        member = self.get_object()
        documents = UserDocument.objects.filter(user=member)
        
        return Response({
            'documents': [
                {
                    'id': str(doc.id),
                    'document_type': doc.document_type,
                    'document_type_display': doc.get_document_type_display(),
                    'is_verified': doc.is_verified,
                    'uploaded_at': doc.uploaded_at,
                    'verified_at': doc.verified_at,
                    'verified_by': doc.verified_by.full_name if doc.verified_by else None,
                    'document_url': request.build_absolute_uri(doc.document.url) if doc.document else None
                }
                for doc in documents
            ]
        })
    
    @action(detail=True, methods=['get'])
    def activity_logs(self, request, pk=None):
        """Get activity logs for a member"""
        
        member = self.get_object()
        logs = ActivityLog.objects.filter(user=member).order_by('-created_at')
        
        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size
        
        paginated_logs = logs[start:end]
        total_logs = logs.count()
        
        return Response({
            'logs': [
                {
                    'id': str(log.id),
                    'action': log.action,
                    'action_display': log.get_action_display(),
                    'description': log.description,
                    'ip_address': log.ip_address,
                    'created_at': log.created_at
                }
                for log in paginated_logs
            ],
            'total': total_logs,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_logs + page_size - 1) // page_size
        })
    
    @action(detail=True, methods=['post'])
    def set_share_capital_term(self, request, pk=None):
        """Set the share capital payment term for a member"""
        
        member = self.get_object()
        term = request.data.get('term')
        
        if not term or term not in [12, 24]:
            return Response({
                'status': 'error',
                'message': "Term must be either 12 or 24 months."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        member.share_capital_term = term
        member.save()
        
        # Log the activity
        ActivityLog.objects.create(
            user=request.user,
            action='ACCOUNT_UPDATE',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            description=f"Updated share capital term to {term} months for {member.email}."
        )
        
        return Response({
            'status': 'success',
            'message': f"Share capital term updated to {term} months."
        })


class MemberDashboardView(APIView):
    """API endpoint for member dashboard data"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get dashboard data for the logged-in member"""
        
        user = request.user
        
        # Ensure the user is a member
        if user.role != SaccoUser.MEMBER:
            return Response({
                'status': 'error',
                'message': "This endpoint is only for members."
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get share summary
        try:
            share_summary = MemberShareSummary.objects.get(member=user)
        except MemberShareSummary.DoesNotExist:
            share_summary = MemberShareSummary.update_member_summary(user)
        
        # Get recent contributions
        recent_contributions = MonthlyContribution.objects.filter(
            member=user
        ).order_by('-year', '-month')[:5]
        
        # Get recent share capital payments
        recent_share_payments = ShareCapital.objects.filter(
            member=user
        ).order_by('-transaction_date')[:5]
        
        # Get active loans
        active_loans = Loan.objects.filter(
            member=user, 
            status__in=['APPROVED', 'DISBURSED']
        ).order_by('-application_date')
        
        # Get latest dividend
        latest_dividend = MemberDividend.objects.filter(
            member=user
        ).order_by('-distribution__distribution_date').first()
        
        # Document verification status
        document_status = {
            'id_front': {
                'uploaded': UserDocument.objects.filter(user=user, document_type='ID_FRONT').exists(),
                'verified': UserDocument.objects.filter(user=user, document_type='ID_FRONT', is_verified=True).exists()
            },
            'id_back': {
                'uploaded': UserDocument.objects.filter(user=user, document_type='ID_BACK').exists(),
                'verified': UserDocument.objects.filter(user=user, document_type='ID_BACK', is_verified=True).exists()
            }
        }
        
        # Get next monthly contribution due
        current_date = timezone.now().date()
        current_year = current_date.year
        current_month = current_date.month
        
        # Check if current month's contribution is made
        current_month_paid = MonthlyContribution.objects.filter(
            member=user,
            year=current_year,
            month=current_month
        ).exists()
        
        next_due_month = current_month
        next_due_year = current_year
        
        if current_month_paid:
            # Move to next month
            if current_month == 12:
                next_due_month = 1
                next_due_year = current_year + 1
            else:
                next_due_month = current_month + 1
        
        # Format month names
        months = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ]
        
        return Response({
            'profile': {
                'full_name': user.full_name,
                'membership_number': user.membership_number,
                'date_joined': user.date_joined,
                'is_verified': user.is_verified,
                'is_on_hold': user.is_on_hold,
                'on_hold_reason': user.on_hold_reason if user.is_on_hold else None,
                'share_capital_term': user.share_capital_term
            },
            'shares_summary': {
                'total_share_capital': share_summary.total_share_capital,
                'share_capital_target': share_summary.share_capital_target,
                'share_capital_completion_percentage': share_summary.share_capital_completion_percentage,
                'total_contributions': share_summary.total_contributions,
                'total_deposits': share_summary.total_deposits,
                'percentage_of_total_pool': share_summary.percentage_of_total_pool,
                'number_of_shares': share_summary.number_of_shares,
                'total_dividends_received': share_summary.total_dividends_received
            },
            'contributions': {
                'recent_contributions': [
                    {
                        'id': str(contrib.id),
                        'year': contrib.year,
                        'month': contrib.month,
                        'month_name': months[contrib.month - 1],
                        'amount': contrib.amount,
                        'transaction_date': contrib.transaction_date
                    }
                    for contrib in recent_contributions
                ],
                'next_due': {
                    'year': next_due_year,
                    'month': next_due_month,
                    'month_name': months[next_due_month - 1],
                    'is_current_month_paid': current_month_paid
                }
            },
            'share_capital': {
                'recent_payments': [
                    {
                        'id': str(payment.id),
                        'amount': payment.amount,
                        'transaction_date': payment.transaction_date,
                        'reference_number': payment.reference_number
                    }
                    for payment in recent_share_payments
                ]
            },
            'loans': {
                'active_loans': [
                    {
                        'id': str(loan.id),
                        'amount': loan.amount,
                        'disbursed_amount': loan.disbursed_amount,
                        'status': loan.status,
                        'application_date': loan.application_date,
                        'disbursement_date': loan.disbursement_date,
                        'total_expected_repayment': loan.total_expected_repayment,
                        'total_repaid': loan.total_repaid,
                        'remaining_balance': loan.remaining_balance
                    }
                    for loan in active_loans
                ]
            },
            'dividends': {
                'latest_dividend': {
                    'amount': latest_dividend.amount if latest_dividend else 0,
                    'date': latest_dividend.distribution.distribution_date if latest_dividend else None,
                    'percentage_share': latest_dividend.percentage_share if latest_dividend else 0
                } if latest_dividend else None
            },
            'documents': document_status
        })


class MemberProfileView(generics.RetrieveUpdateAPIView):
    """API endpoint for member to view and update their profile"""
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserProfileSerializer
    
    def get_object(self):
        return self.request.user