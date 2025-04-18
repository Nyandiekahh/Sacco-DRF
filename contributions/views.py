# contributions/views.py

from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.models import SaccoUser, ActivityLog
from sacco_core.models import MonthlyContribution, ShareCapital, MemberShareSummary, Transaction
from members.views import AdminRequiredMixin
from .serializers import (
    MonthlyContributionSerializer,
    ShareCapitalSerializer,
    ContributionReminderSerializer
)
from .models import ContributionReminder, ContributionReport


class MemberContributionViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for members to view their own contributions"""
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MonthlyContributionSerializer
    
    def get_queryset(self):
        # Only return contributions for the current user
        return MonthlyContribution.objects.filter(
            member=self.request.user
        ).order_by('-year', '-month', '-created_at')


class MemberShareCapitalViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for members to view their own share capital payments"""
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ShareCapitalSerializer
    
    def get_queryset(self):
        # Only return share capital payments for the current user
        return ShareCapital.objects.filter(
            member=self.request.user
        ).order_by('-transaction_date', '-created_at')


class MonthlyContributionViewSet(AdminRequiredMixin, viewsets.ModelViewSet):
    """API endpoint for managing monthly contributions - Admin only"""
    
    permission_classes = [permissions.IsAuthenticated]
    queryset = MonthlyContribution.objects.all().order_by('-year', '-month', '-created_at')
    serializer_class = MonthlyContributionSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by member
        member_id = self.request.query_params.get('member_id')
        if member_id:
            queryset = queryset.filter(member_id=member_id)
        
        # Filter by year
        year = self.request.query_params.get('year')
        if year:
            queryset = queryset.filter(year=year)
        
        # Filter by month
        month = self.request.query_params.get('month')
        if month:
            queryset = queryset.filter(month=month)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(transaction_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(transaction_date__lte=date_to)
        
        return queryset
    
    def perform_create(self, serializer):
        # Add the admin who recorded the contribution
        contribution = serializer.save(created_by=self.request.user)
        
        # Create a transaction record
        Transaction.objects.create(
            transaction_type='MONTHLY_CONTRIBUTION',
            member=contribution.member,
            amount=contribution.amount,
            transaction_date=contribution.transaction_date,
            description=f"Monthly contribution for {contribution.get_month_name()} {contribution.year}",
            reference_number=contribution.reference_number,
            created_by=self.request.user
        )
        
        # Log the activity
        ActivityLog.objects.create(
            user=self.request.user,
            action='CONTRIBUTION_RECORD',
            ip_address=self.request.META.get('REMOTE_ADDR'),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            description=f"Recorded monthly contribution of {contribution.amount} for {contribution.member.full_name} ({contribution.get_month_name()} {contribution.year})."
        )
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Create multiple contributions at once"""
        
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            contributions = []
            for contribution_data in serializer.validated_data:
                # Create contribution
                contribution = MonthlyContribution.objects.create(
                    member=contribution_data['member'],
                    year=contribution_data['year'],
                    month=contribution_data['month'],
                    amount=contribution_data['amount'],
                    transaction_date=contribution_data['transaction_date'],
                    reference_number=contribution_data['reference_number'],
                    transaction_code=contribution_data['transaction_code'],
                    transaction_message=contribution_data.get('transaction_message', ''),
                    created_by=request.user
                )
                contributions.append(contribution)
                
                # Create transaction record
                Transaction.objects.create(
                    transaction_type='MONTHLY_CONTRIBUTION',
                    member=contribution.member,
                    amount=contribution.amount,
                    transaction_date=contribution.transaction_date,
                    description=f"Monthly contribution for {contribution.get_month_name()} {contribution.year}",
                    reference_number=contribution.reference_number,
                    created_by=request.user
                )
                
                # Log the activity
                ActivityLog.objects.create(
                    user=request.user,
                    action='CONTRIBUTION_RECORD',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    description=f"Recorded monthly contribution of {contribution.amount} for {contribution.member.full_name} ({contribution.get_month_name()} {contribution.year})."
                )
        
        return Response({
            'status': 'success',
            'message': f'Successfully created {len(contributions)} contributions',
            'contributions': self.get_serializer(contributions, many=True).data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def missing_contributions(self, request):
        """Get members who haven't contributed for a specific month"""
        
        year = request.query_params.get('year')
        month = request.query_params.get('month')
        
        if not year or not month:
            return Response({
                'status': 'error',
                'message': 'Year and month parameters are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get all active members
        active_members = SaccoUser.objects.filter(
            role='MEMBER',
            is_active=True,
            is_on_hold=False
        )
        
        # Find members who haven't contributed
        missing_members = []
        for member in active_members:
            # Check if member has contributed for this month
            contributed = MonthlyContribution.objects.filter(
                member=member,
                year=year,
                month=month
            ).exists()
            
            if not contributed:
                missing_members.append({
                    'id': str(member.id),
                    'full_name': member.full_name,
                    'membership_number': member.membership_number,
                    'email': member.email,
                    'phone_number': member.phone_number
                })
        
        return Response({
            'year': year,
            'month': month,
            'total_active_members': active_members.count(),
            'missing_members_count': len(missing_members),
            'missing_members': missing_members
        })
    
    @action(detail=False, methods=['post'])
    def send_reminders(self, request):
        """Send contribution reminders to members who haven't contributed"""
        
        serializer = ContributionReminderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        year = serializer.validated_data['year']
        month = serializer.validated_data['month']
        message = serializer.validated_data['message']
        
        # Get current date for the reminder
        reminder_date = timezone.now().date()
        
        # Create reminder record
        reminder = ContributionReminder.objects.create(
            year=year,
            month=month,
            reminder_date=reminder_date,
            message=message,
            scheduled_by=request.user
        )
        
        # Send the reminders
        reminder.send_reminders()
        
        # Log the activity
        ActivityLog.objects.create(
            user=request.user,
            action='REMINDER_SENT',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            description=f"Sent contribution reminders for {reminder.get_month_name()} {year} to {reminder.recipients_count} members."
        )
        
        return Response({
            'status': 'success',
            'message': f'Reminders sent to {reminder.successful_count} members. Failed: {reminder.failed_count}',
            'reminder_id': str(reminder.id),
            'year': year,
            'month': month,
            'recipients_count': reminder.recipients_count,
            'successful_count': reminder.successful_count,
            'failed_count': reminder.failed_count
        })
    
    @action(detail=False, methods=['get'])
    def generate_report(self, request):
        """Generate a report of contributions for a specific month"""
        
        year = request.query_params.get('year')
        month = request.query_params.get('month')
        
        if not year or not month:
            return Response({
                'status': 'error',
                'message': 'Year and month parameters are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate the report
        report = ContributionReport.generate_monthly_report(
            int(year), 
            int(month), 
            request.user
        )
        
        # Get contributions for the month
        contributions = MonthlyContribution.objects.filter(
            year=year,
            month=month
        ).order_by('member__full_name')
        
        # Get members who contributed
        contributors = []
        for contribution in contributions:
            contributors.append({
                'id': str(contribution.member.id),
                'full_name': contribution.member.full_name,
                'membership_number': contribution.member.membership_number,
                'email': contribution.member.email,
                'amount': contribution.amount,
                'transaction_date': contribution.transaction_date,
                'reference_number': contribution.reference_number
            })
        
        # Get month name
        months = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ]
        month_name = months[int(month) - 1]
        
        return Response({
            'report_id': str(report.id),
            'year': year,
            'month': month,
            'month_name': month_name,
            'report_date': report.report_date,
            'total_members': report.total_members,
            'contributing_members': report.contributing_members,
            'total_amount': report.total_amount,
            'growth_percentage': report.growth_percentage,
            'contributors': contributors
        })


class ShareCapitalViewSet(AdminRequiredMixin, viewsets.ModelViewSet):
    """API endpoint for managing share capital payments - Admin only"""
    
    permission_classes = [permissions.IsAuthenticated]
    queryset = ShareCapital.objects.all().order_by('-transaction_date', '-created_at')
    serializer_class = ShareCapitalSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by member
        member_id = self.request.query_params.get('member_id')
        if member_id:
            queryset = queryset.filter(member_id=member_id)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(transaction_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(transaction_date__lte=date_to)
        
        return queryset
    
    def perform_create(self, serializer):
        # Add the admin who recorded the payment
        payment = serializer.save(created_by=self.request.user)
        
        # Create a transaction record
        Transaction.objects.create(
            transaction_type='SHARE_CAPITAL',
            member=payment.member,
            amount=payment.amount,
            transaction_date=payment.transaction_date,
            description=f"Share capital payment",
            reference_number=payment.reference_number,
            created_by=self.request.user
        )
        
        # Log the activity
        ActivityLog.objects.create(
            user=self.request.user,
            action='SHARE_CAPITAL_RECORD',
            ip_address=self.request.META.get('REMOTE_ADDR'),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            description=f"Recorded share capital payment of {payment.amount} for {payment.member.full_name}."
        )
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Create multiple share capital payments at once"""
        
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            payments = []
            for payment_data in serializer.validated_data:
                # Create share capital payment
                payment = ShareCapital.objects.create(
                    member=payment_data['member'],
                    amount=payment_data['amount'],
                    transaction_date=payment_data['transaction_date'],
                    reference_number=payment_data['reference_number'],
                    transaction_code=payment_data['transaction_code'],
                    transaction_message=payment_data.get('transaction_message', ''),
                    created_by=request.user
                )
                payments.append(payment)
                
                # Create transaction record
                Transaction.objects.create(
                    transaction_type='SHARE_CAPITAL',
                    member=payment.member,
                    amount=payment.amount,
                    transaction_date=payment.transaction_date,
                    description=f"Share capital payment",
                    reference_number=payment.reference_number,
                    created_by=request.user
                )
                
                # Log the activity
                ActivityLog.objects.create(
                    user=request.user,
                    action='SHARE_CAPITAL_RECORD',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    description=f"Recorded share capital payment of {payment.amount} for {payment.member.full_name}."
                )
        
        return Response({
            'status': 'success',
            'message': f'Successfully created {len(payments)} share capital payments',
            'payments': self.get_serializer(payments, many=True).data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def incomplete_share_capital(self, request):
        """Get members who haven't completed their share capital payments"""
        
        # Get all active members
        active_members = SaccoUser.objects.filter(
            role='MEMBER',
            is_active=True
        )
        
        # Find members with incomplete share capital
        incomplete_members = []
        for member in active_members:
            # Get member share summary
            try:
                summary = MemberShareSummary.objects.get(member=member)
                if summary.share_capital_completion_percentage < 100:
                    incomplete_members.append({
                        'id': str(member.id),
                        'full_name': member.full_name,
                        'membership_number': member.membership_number,
                        'email': member.email,
                        'phone_number': member.phone_number,
                        'total_share_capital': summary.total_share_capital,
                        'share_capital_target': summary.share_capital_target,
                        'completion_percentage': summary.share_capital_completion_percentage,
                        'remaining_amount': summary.share_capital_target - summary.total_share_capital
                    })
            except MemberShareSummary.DoesNotExist:
                # Create a new summary
                summary = MemberShareSummary.update_member_summary(member)
                if summary.share_capital_completion_percentage < 100:
                    incomplete_members.append({
                        'id': str(member.id),
                        'full_name': member.full_name,
                        'membership_number': member.membership_number,
                        'email': member.email,
                        'phone_number': member.phone_number,
                        'total_share_capital': summary.total_share_capital,
                        'share_capital_target': summary.share_capital_target,
                        'completion_percentage': summary.share_capital_completion_percentage,
                        'remaining_amount': summary.share_capital_target - summary.total_share_capital
                    })
        
        return Response({
            'total_active_members': active_members.count(),
            'incomplete_members_count': len(incomplete_members),
            'incomplete_members': incomplete_members
        })


class RecalculateSharesView(AdminRequiredMixin, APIView):
    """API endpoint to recalculate share percentages for all members"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        # Recalculate shares for all members
        MemberShareSummary.recalculate_percentages()
        
        # Log the activity
        ActivityLog.objects.create(
            user=request.user,
            action='SHARE_RECALCULATION',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            description="Recalculated share percentages for all members."
        )
        
        return Response({
            'status': 'success',
            'message': 'Successfully recalculated share percentages for all members'
        })