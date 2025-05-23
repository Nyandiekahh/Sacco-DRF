# loans/views.py

from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.models import SaccoUser, ActivityLog
from sacco_core.models import Loan, LoanRepayment, Transaction, MemberShareSummary
from members.views import AdminRequiredMixin
from .models import LoanApplication, RepaymentSchedule, LoanStatement, LoanNotification, PaymentMethod, LoanDisbursement
from .serializers import (
    LoanApplicationSerializer,
    LoanSerializer,
    LoanRepaymentSerializer,
    LoanStatementSerializer,
    RepaymentScheduleSerializer, 
    PaymentMethodSerializer,
    LoanDisbursementSerializer,
    GuarantorRequestSerializer,
    GuarantorLimitSerializer,
    EligibleGuarantorSerializer
)

class LoanApplicationViewSet(viewsets.ModelViewSet):
    """API endpoint for loan applications"""
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LoanApplicationSerializer
    
    def get_queryset(self):
        """Return appropriate applications based on user role"""
        user = self.request.user
        
        if user.role == SaccoUser.ADMIN:
            # Admins see all applications
            queryset = LoanApplication.objects.all()
        else:
            # Members see only their own applications
            queryset = LoanApplication.objects.filter(member=user)
        
        # Filter by status
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param.upper())
        
        return queryset.order_by('-application_date')
    
    def perform_create(self, serializer):
        # Set member to current user if not admin
        user = self.request.user
        if user.role != SaccoUser.ADMIN:
            serializer.save(member=user)
        else:
            serializer.save()
        
        # Log the activity
        ActivityLog.objects.create(
            user=self.request.user,
            action='LOAN_APPLICATION',
            ip_address=self.request.META.get('REMOTE_ADDR'),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            description=f"Created loan application for {serializer.instance.amount}."
        )
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a loan application"""
        
        # Only admins can approve
        if request.user.role != SaccoUser.ADMIN:
            return Response({
                'status': 'error',
                'message': 'Only administrators can approve loan applications'
            }, status=status.HTTP_403_FORBIDDEN)
        
        application = self.get_object()
        
        # Check if already processed
        if application.status != 'PENDING':
            return Response({
                'status': 'error',
                'message': f'Application is already {application.get_status_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get interest rate from request or use default
        interest_rate = request.data.get('interest_rate')
        
        # Approve the application
        loan = application.approve_application(request.user, interest_rate)
        
        # Create loan notification
        notification = LoanNotification.objects.create(
            loan=loan,
            notification_type='APPROVAL',
            message=f"Your loan application for {loan.amount} has been approved."
        )
        
        # Send the notification
        notification.send_notification()
        
        # Log the activity
        ActivityLog.objects.create(
            user=request.user,
            action='LOAN_APPROVAL',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            description=f"Approved loan application for {application.member.full_name} - {loan.amount}."
        )
        
        return Response({
            'status': 'success',
            'message': 'Loan application approved successfully',
            'loan_id': str(loan.id)
        })
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a loan application"""
        
        # Only admins can reject
        if request.user.role != SaccoUser.ADMIN:
            return Response({
                'status': 'error',
                'message': 'Only administrators can reject loan applications'
            }, status=status.HTTP_403_FORBIDDEN)
        
        application = self.get_object()
        
        # Check if already processed
        if application.status != 'PENDING':
            return Response({
                'status': 'error',
                'message': f'Application is already {application.get_status_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get rejection reason
        rejection_reason = request.data.get('rejection_reason')
        if not rejection_reason:
            return Response({
                'status': 'error',
                'message': 'Rejection reason is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Reject the application
        application.reject_application(request.user, rejection_reason)
        
        # Create loan notification if there's a related loan
        if application.loan:
            notification = LoanNotification.objects.create(
                loan=application.loan,
                notification_type='REJECTION',
                message=f"Your loan application has been rejected. Reason: {rejection_reason}"
            )
            
            # Send the notification
            notification.send_notification()
        
        # Log the activity
        ActivityLog.objects.create(
            user=request.user,
            action='LOAN_REJECTION',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            description=f"Rejected loan application for {application.member.full_name}. Reason: {rejection_reason}"
        )
        
        return Response({
            'status': 'success',
            'message': 'Loan application rejected successfully'
        })


class LoanViewSet(viewsets.ModelViewSet):
    """API endpoint for loans"""
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LoanSerializer
    
    def get_queryset(self):
        """Return appropriate loans based on user role"""
        user = self.request.user
        
        if user.role == SaccoUser.ADMIN:
            # Admins see all loans
            queryset = Loan.objects.all()
        else:
            # Members see only their own loans
            queryset = Loan.objects.filter(member=user)
        
        # Filter by status
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param.upper())
        
        return queryset.order_by('-application_date')
    
    @action(detail=True, methods=['post'])
    def disburse(self, request, pk=None):
        """Disburse an approved loan"""
        
        # Only admins can disburse
        if request.user.role != SaccoUser.ADMIN:
            return Response({
                'status': 'error',
                'message': 'Only administrators can disburse loans'
            }, status=status.HTTP_403_FORBIDDEN)
        
        loan = self.get_object()
        
        # Check if loan is in correct status
        if loan.status != 'APPROVED':
            return Response({
                'status': 'error',
                'message': f'Loan is {loan.get_status_display()}, not Approved'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update loan status
        loan.status = 'DISBURSED'
        loan.disbursement_date = timezone.now().date()
        loan.disbursed_by = request.user
        loan.save()
        
        # Generate repayment schedule
        RepaymentSchedule.generate_schedule(loan)
        
        # Create transaction record for disbursement
        transaction = Transaction.objects.create(
            transaction_type='LOAN_DISBURSEMENT',
            member=loan.member,
            amount=loan.disbursed_amount,
            transaction_date=loan.disbursement_date,
            transaction_cost=loan.processing_fee + loan.insurance_fee,
            description=f"Loan disbursement",
            related_loan=loan,
            created_by=request.user
        )
        
        # Create loan notification
        notification = LoanNotification.objects.create(
            loan=loan,
            notification_type='DISBURSEMENT',
            message=f"Your loan of {loan.amount} has been disbursed. Amount credited: {loan.disbursed_amount}"
        )
        
        # Send the notification
        notification.send_notification()
        
        # Log the activity
        ActivityLog.objects.create(
            user=request.user,
            action='LOAN_DISBURSEMENT',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            description=f"Disbursed loan of {loan.amount} to {loan.member.full_name}."
        )
        
        return Response({
            'status': 'success',
            'message': 'Loan disbursed successfully',
            'loan': {
                'id': str(loan.id),
                'amount': loan.amount,
                'disbursed_amount': loan.disbursed_amount,
                'disbursement_date': loan.disbursement_date,
                'processing_fee': loan.processing_fee,
                'insurance_fee': loan.insurance_fee,
                'total_expected_repayment': loan.total_expected_repayment,
                'transaction_id': str(transaction.id)
            }
        })
    
    @action(detail=True, methods=['post'])
    def add_repayment(self, request, pk=None):
        """Add a repayment to a loan"""
        
        # Only admins can add repayments
        if request.user.role != SaccoUser.ADMIN:
            return Response({
                'status': 'error',
                'message': 'Only administrators can add loan repayments'
            }, status=status.HTTP_403_FORBIDDEN)
        
        loan = self.get_object()
        
        # Check if loan is in correct status
        if loan.status != 'DISBURSED':
            return Response({
                'status': 'error',
                'message': f'Loan is {loan.get_status_display()}, not Disbursed'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate input
        serializer = LoanRepaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        amount = serializer.validated_data['amount']
        transaction_details = {
            'reference_number': serializer.validated_data.get('reference_number', ''),
            'transaction_code': serializer.validated_data.get('transaction_code', ''),
            'transaction_message': serializer.validated_data.get('transaction_message', '')
        }
        
        # Add repayment
        repayment = loan.add_repayment(amount, transaction_details, request.user)
        
        # Create transaction record
        transaction = Transaction.objects.create(
            transaction_type='LOAN_REPAYMENT',
            member=loan.member,
            amount=amount,
            transaction_date=repayment.transaction_date,
            description=f"Loan repayment",
            reference_number=repayment.reference_number,
            related_loan=loan,
            created_by=request.user
        )
        
        # Update repayment schedule
        schedules = RepaymentSchedule.objects.filter(
            loan=loan,
            status__in=['PENDING', 'PARTIAL', 'OVERDUE']
        ).order_by('due_date')
        
        remaining_amount = amount
        for schedule in schedules:
            if remaining_amount <= 0:
                break
                
            if schedule.remaining_amount <= remaining_amount:
                # This installment can be fully paid
                paid_amount = schedule.remaining_amount
                schedule.amount_paid += paid_amount
                schedule.remaining_amount = 0
                schedule.status = 'PAID'
                schedule.save()
                
                remaining_amount -= paid_amount
            else:
                # Partial payment for this installment
                schedule.amount_paid += remaining_amount
                schedule.remaining_amount -= remaining_amount
                schedule.status = 'PARTIAL'
                schedule.save()
                
                remaining_amount = 0
        
        # Create loan notification if loan is fully paid
        if loan.status == 'SETTLED':
            notification = LoanNotification.objects.create(
                loan=loan,
                notification_type='LOAN_PAID',
                message=f"Your loan has been fully repaid. Thank you!"
            )
            
            # Send the notification
            notification.send_notification()
        else:
            # Create payment received notification
            notification = LoanNotification.objects.create(
                loan=loan,
                notification_type='PAYMENT_RECEIVED',
                message=f"We have received your loan payment of {amount}. Remaining balance: {loan.remaining_balance}"
            )
            
            # Send the notification
            notification.send_notification()
        
        # Log the activity
        ActivityLog.objects.create(
            user=request.user,
            action='LOAN_REPAYMENT',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            description=f"Recorded loan repayment of {amount} for {loan.member.full_name}."
        )
        
        return Response({
            'status': 'success',
            'message': 'Loan repayment added successfully',
            'loan_status': loan.status,
            'repayment': {
                'id': str(repayment.id),
                'amount': repayment.amount,
                'transaction_date': repayment.transaction_date,
                'reference_number': repayment.reference_number,
                'transaction_id': str(transaction.id)
            },
            'loan': {
                'id': str(loan.id),
                'total_repaid': loan.total_repaid,
                'remaining_balance': loan.remaining_balance,
                'is_settled': loan.status == 'SETTLED'
            }
        })
    
    @action(detail=True, methods=['get'])
    def repayment_schedule(self, request, pk=None):
        """Get repayment schedule for a loan"""
        
        loan = self.get_object()
        
        # Check if schedule exists
        schedules = RepaymentSchedule.objects.filter(loan=loan).order_by('installment_number')
        
        if not schedules.exists():
            # Generate schedule if loan is disbursed
            if loan.status == 'DISBURSED' and loan.disbursement_date:
                RepaymentSchedule.generate_schedule(loan)
                schedules = RepaymentSchedule.objects.filter(loan=loan).order_by('installment_number')
            else:
                return Response({
                    'status': 'error',
                    'message': 'Repayment schedule not available. Loan must be disbursed.'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = RepaymentScheduleSerializer(schedules, many=True)
        
        return Response({
            'loan_id': str(loan.id),
            'member': loan.member.full_name,
            'amount': loan.amount,
            'interest_rate': loan.interest_rate,
            'term_months': loan.term_months,
            'disbursement_date': loan.disbursement_date,
            'total_expected_repayment': loan.total_expected_repayment,
            'total_repaid': loan.total_repaid,
            'remaining_balance': loan.remaining_balance,
            'schedule': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def generate_statement(self, request, pk=None):
        """Generate a loan statement"""
        
        loan = self.get_object()
        
        # Generate statement
        statement = LoanStatement.generate_statement(loan, request.user)
        
        serializer = LoanStatementSerializer(statement)
        
        # Log the activity
        ActivityLog.objects.create(
            user=request.user,
            action='LOAN_STATEMENT',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            description=f"Generated loan statement for {loan.member.full_name}'s loan."
        )
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def due_payments(self, request):
        """Get loans with upcoming or overdue payments"""
        
        # Only admins can access this endpoint
        if request.user.role != SaccoUser.ADMIN:
            return Response({
                'status': 'error',
                'message': 'Only administrators can access due payments'
            }, status=status.HTTP_403_FORBIDDEN)
        
        today = timezone.now().date()
        
        # Get loans with upcoming payments (within next 7 days)
        upcoming_due_date = today + timezone.timedelta(days=7)
        
        # Get schedules with upcoming or overdue payments
        schedules = RepaymentSchedule.objects.filter(
            loan__status='DISBURSED',
            status__in=['PENDING', 'PARTIAL', 'OVERDUE'],
            due_date__lte=upcoming_due_date
        ).select_related('loan', 'loan__member').order_by('due_date')
        
        # Group by loan
        loans_with_payments = {}
        for schedule in schedules:
            loan_id = str(schedule.loan.id)
            
            if loan_id not in loans_with_payments:
                loans_with_payments[loan_id] = {
                    'loan_id': loan_id,
                    'member': {
                        'id': str(schedule.loan.member.id),
                        'full_name': schedule.loan.member.full_name,
                        'membership_number': schedule.loan.member.membership_number,
                        'email': schedule.loan.member.email,
                        'phone_number': schedule.loan.member.phone_number
                    },
                    'amount': schedule.loan.amount,
                    'disbursement_date': schedule.loan.disbursement_date,
                    'total_expected_repayment': schedule.loan.total_expected_repayment,
                    'total_repaid': schedule.loan.total_repaid,
                    'remaining_balance': schedule.loan.remaining_balance,
                    'upcoming_payments': [],
                    'overdue_payments': []
                }
            
            payment_info = {
                'installment_number': schedule.installment_number,
                'due_date': schedule.due_date,
                'amount_due': schedule.amount_due,
                'amount_paid': schedule.amount_paid,
                'remaining_amount': schedule.remaining_amount,
                'days_overdue': (today - schedule.due_date).days if schedule.due_date < today else 0
            }
            
            if schedule.due_date < today:
                loans_with_payments[loan_id]['overdue_payments'].append(payment_info)
            else:
                loans_with_payments[loan_id]['upcoming_payments'].append(payment_info)
        
        return Response({
            'due_payments': list(loans_with_payments.values())
        })
    
    @action(detail=False, methods=['post'])
    def send_payment_reminders(self, request):
        """Send reminders for upcoming or overdue payments"""
        
        # Only admins can send reminders
        if request.user.role != SaccoUser.ADMIN:
            return Response({
                'status': 'error',
                'message': 'Only administrators can send payment reminders'
            }, status=status.HTTP_403_FORBIDDEN)
        
        today = timezone.now().date()
        
        # Get reminder type
        reminder_type = request.data.get('type', 'all')
        reminder_message = request.data.get('message', '')
        
        # Get schedules based on type
        if reminder_type == 'overdue':
            # Only overdue payments
            schedules = RepaymentSchedule.objects.filter(
                loan__status='DISBURSED',
                status__in=['PENDING', 'PARTIAL', 'OVERDUE'],
                due_date__lt=today
            ).select_related('loan', 'loan__member')
        elif reminder_type == 'upcoming':
            # Only upcoming payments (within next 7 days)
            upcoming_due_date = today + timezone.timedelta(days=7)
            schedules = RepaymentSchedule.objects.filter(
                loan__status='DISBURSED',
                status__in=['PENDING', 'PARTIAL'],
                due_date__gte=today,
                due_date__lte=upcoming_due_date
            ).select_related('loan', 'loan__member')
        else:
            # Both overdue and upcoming
            upcoming_due_date = today + timezone.timedelta(days=7)
            schedules = RepaymentSchedule.objects.filter(
                loan__status='DISBURSED',
                status__in=['PENDING', 'PARTIAL', 'OVERDUE'],
                due_date__lte=upcoming_due_date
            ).select_related('loan', 'loan__member')
        
        # Group by loan (to avoid multiple reminders to same member)
        loans_with_payments = {}
        for schedule in schedules:
            loan_id = str(schedule.loan.id)
            
            if loan_id not in loans_with_payments:
                loans_with_payments[loan_id] = {
                    'loan': schedule.loan,
                    'schedules': []
                }
            
            loans_with_payments[loan_id]['schedules'].append(schedule)
        
        # Send reminders
        sent_count = 0
        failed_count = 0
        
        for loan_info in loans_with_payments.values():
            loan = loan_info['loan']
            
            # Determine notification type
            has_overdue = any(s.due_date < today for s in loan_info['schedules'])
            notification_type = 'PAYMENT_OVERDUE' if has_overdue else 'PAYMENT_DUE'
            
            # Get earliest schedule
            earliest_schedule = min(loan_info['schedules'], key=lambda s: s.due_date)
            
            # Create notification message
            if not reminder_message:
                if notification_type == 'PAYMENT_OVERDUE':
                    message = f"You have an overdue loan payment of {earliest_schedule.remaining_amount} that was due on {earliest_schedule.due_date}. Please make your payment as soon as possible."
                else:
                    message = f"You have an upcoming loan payment of {earliest_schedule.remaining_amount} due on {earliest_schedule.due_date}. Please ensure your payment is made on time."
            else:
                message = reminder_message
            
            # Create and send notification
            notification = LoanNotification.objects.create(
                loan=loan,
                notification_type=notification_type,
                message=message
            )
            
            if notification.send_notification():
                sent_count += 1
            else:
                failed_count += 1
        
        # Log the activity
        ActivityLog.objects.create(
            user=request.user,
            action='PAYMENT_REMINDER',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            description=f"Sent payment reminders to {sent_count} members. Failed: {failed_count}"
        )
        
        return Response({
            'status': 'success',
            'message': f'Payment reminders sent successfully',
            'sent_count': sent_count,
            'failed_count': failed_count
        })


class LoanEligibilityView(APIView):
    """API endpoint to check loan eligibility"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Check loan eligibility for the current member"""
        
        user = request.user
        
        # Get member share summary
        try:
            summary = MemberShareSummary.objects.get(member=user)
        except MemberShareSummary.DoesNotExist:
            summary = MemberShareSummary.update_member_summary(user)
        
        # Get active loans
        active_loans = Loan.objects.filter(
            member=user,
            status__in=['APPROVED', 'DISBURSED']
        )
        
        from sacco_core.models import SaccoSettings
        settings = SaccoSettings.get_settings()
        
        # Calculate maximum loan amount
        max_multiplier = settings.maximum_loan_multiplier
        max_loan_amount = summary.total_deposits * max_multiplier
        
        # Check if member has active loans
        has_active_loans = active_loans.exists()
        outstanding_loans = sum([loan.remaining_balance for loan in active_loans])
        
        # Check eligibility based on active loans
        eligible = True
        reason = None
        
        if has_active_loans:
            if outstanding_loans >= max_loan_amount:
                eligible = False
                reason = "You already have active loans that exceed your eligibility."
            else:
                max_loan_amount -= outstanding_loans
        
        # Check eligibility based on share capital completion
        if summary.share_capital_completion_percentage < 100:
            eligible = False
            reason = "You must complete your share capital contribution before applying for a loan."
        
        # Check eligibility based on KYC verification
        if not user.is_verified:
            eligible = False
            reason = "Your account must be fully verified before applying for a loan."
        
        # Check if account is on hold
        if user.is_on_hold:
            eligible = False
            reason = f"Your account is currently on hold. Reason: {user.on_hold_reason}"
        
        return Response({
            'eligible': eligible,
            'reason': reason if not eligible else None,
            'max_loan_amount': max_loan_amount if eligible else 0,
            'deposits': summary.total_deposits,
            'multiplier': max_multiplier,
            'has_active_loans': has_active_loans,
            'outstanding_loans': outstanding_loans if has_active_loans else 0,
            'share_capital_complete': summary.share_capital_completion_percentage >= 100,
            'is_verified': user.is_verified,
            'is_on_hold': user.is_on_hold
        })
    
# Add these new views to your existing loans/views.py


class PaymentMethodViewSet(viewsets.ModelViewSet):
    """API endpoint for payment methods"""
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PaymentMethodSerializer
    
    def get_queryset(self):
        """Return appropriate payment methods based on usage"""
        queryset = PaymentMethod.objects.filter(status='ACTIVE')
        
        # Filter by usage
        usage = self.request.query_params.get('usage')
        if usage == 'disbursement':
            queryset = queryset.filter(allowed_for_disbursement=True)
        elif usage == 'repayment':
            queryset = queryset.filter(allowed_for_repayment=True)
        
        # Filter by type
        payment_type = self.request.query_params.get('type')
        if payment_type:
            queryset = queryset.filter(payment_type=payment_type.upper())
        
        return queryset.order_by('name')
    
    def perform_create(self, serializer):
        # Only admins can create payment methods
        if self.request.user.role != SaccoUser.ADMIN:
            return Response(
                {"error": "Only administrators can create payment methods"},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer.save()
    
    def perform_update(self, serializer):
        # Only admins can update payment methods
        if self.request.user.role != SaccoUser.ADMIN:
            return Response(
                {"error": "Only administrators can update payment methods"},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def verify_payment_method(self, request, pk=None):
        """Verify a payment method"""
        
        # Only admins can verify payment methods
        if request.user.role != SaccoUser.ADMIN:
            return Response(
                {"error": "Only administrators can verify payment methods"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        payment_method = self.get_object()
        
        # Update status to ACTIVE
        payment_method.status = 'ACTIVE'
        payment_method.save()
        
        # Log the activity
        ActivityLog.objects.create(
            user=request.user,
            action='PAYMENT_METHOD_VERIFICATION',
            description=f"Verified payment method: {payment_method.name}"
        )
        
        return Response({"status": "success", "message": "Payment method verified successfully"})


class LoanDisbursementView(APIView):
    """Enhanced API endpoint for loan disbursement"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, loan_id):
        """Get payment method options for a specific loan"""

    def post(self, request, loan_id):
        """Process loan disbursement with enhanced payment methods"""
        return self.get(request, loan_id)
        
        # Only admins can view disbursement options
        if request.user.role != SaccoUser.ADMIN:
            return Response(
                {"error": "Only administrators can disburse loans"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            loan = Loan.objects.get(id=loan_id)
        except Loan.DoesNotExist:
            return Response(
                {"error": "Loan not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get member payment methods from their profile
        member = loan.member
        payment_methods = []
        
        # Add M-Pesa if available
        if member.mpesa_number:
            payment_methods.append({
                'type': 'MOBILE_MONEY',
                'name': 'M-Pesa',
                'account_number': member.mpesa_number,
                'account_name': member.full_name
            })
        
        # Add bank account if available
        if member.bank_account_number and member.bank_name:
            payment_methods.append({
                'type': 'BANK_TRANSFER',
                'name': f'{member.bank_name} Account',
                'account_number': member.bank_account_number,
                'account_name': member.bank_account_name or member.full_name
            })
        
        # Get available system payment methods
        system_payment_methods = PaymentMethod.objects.filter(
            status='ACTIVE',
            allowed_for_disbursement=True
        )
        
        system_payment_serializer = PaymentMethodSerializer(system_payment_methods, many=True)
        
        return Response({
            'loan_id': str(loan.id),
            'member': {
                'id': str(member.id),
                'name': member.full_name,
                'email': member.email
            },
            'member_payment_methods': payment_methods,
            'system_payment_methods': system_payment_serializer.data
        })
    
    @transaction.atomic
    def post(self, request, loan_id):
        """Process loan disbursement with enhanced payment methods"""
        
        # Only admins can disburse loans
        if request.user.role != SaccoUser.ADMIN:
            return Response(
                {"error": "Only administrators can disburse loans"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            loan = Loan.objects.get(id=loan_id)
        except Loan.DoesNotExist:
            return Response(
                {"error": "Loan not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if loan is in correct status
        if loan.status != 'APPROVED':
            return Response(
                {"error": f"Loan is {loan.get_status_display()}, not Approved"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate input
        serializer = LoanDisbursementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get payment method
        try:
            payment_method = PaymentMethod.objects.get(
                id=serializer.validated_data['payment_method'],
                allowed_for_disbursement=True,
                status='ACTIVE'
            )
        except PaymentMethod.DoesNotExist:
            return Response(
                {"error": "Invalid or inactive payment method for disbursement"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculate transaction cost
        amount = loan.amount
        transaction_cost = serializer.validated_data.get('transaction_cost', 0)
        
        # Calculate default transaction cost if not provided
        if transaction_cost == 0:
            transaction_cost = payment_method.calculate_transaction_fee(amount)
        
        # Calculate net amount (after fees)
        net_amount = amount - transaction_cost
        
        # Create disbursement record
        disbursement = LoanDisbursement.objects.create(
            loan=loan,
            amount=amount,
            payment_method=payment_method,
            reference_number=serializer.validated_data['reference_number'],
            transaction_cost=transaction_cost,
            net_amount=net_amount,
            recipient_account=serializer.validated_data.get('recipient_account', ''),
            recipient_name=loan.member.full_name,
            description=serializer.validated_data.get('description', ''),
            disbursement_date=serializer.validated_data.get('disbursement_date', timezone.now().date()),
            processed_by=request.user
        )
        
        # Update loan status
        loan.status = 'DISBURSED'
        loan.disbursement_date = disbursement.disbursement_date
        loan.disbursed_by = request.user
        loan.disbursed_amount = net_amount
        loan.processing_fee = transaction_cost
        loan.save()
        
        # Generate repayment schedule
        RepaymentSchedule.generate_schedule(loan)
        
        # Create transaction record for disbursement
        transaction = Transaction.objects.create(
            transaction_type='LOAN_DISBURSEMENT',
            member=loan.member,
            amount=net_amount,
            transaction_date=disbursement.disbursement_date,
            transaction_cost=transaction_cost,
            description=f"Loan disbursement via {payment_method.name}",
            reference_number=disbursement.reference_number,
            related_loan=loan,
            created_by=request.user
        )
        
        # Create loan notification
        notification = LoanNotification.objects.create(
            loan=loan,
            notification_type='DISBURSEMENT',
            message=f"Your loan of {amount} has been disbursed. Amount credited: {net_amount} via {payment_method.name}"
        )
        
        # Send the notification
        notification.send_notification()
        
        # Log the activity
        ActivityLog.objects.create(
            user=request.user,
            action='LOAN_DISBURSEMENT',
            description=f"Disbursed loan of {amount} to {loan.member.full_name} via {payment_method.name}"
        )
        
        disbursement_serializer = LoanDisbursementSerializer(disbursement)
        
        return Response({
            "status": "success",
            "message": "Loan disbursed successfully",
            "disbursement": disbursement_serializer.data,
            "loan": {
                "id": str(loan.id),
                "status": loan.status,
                "disbursed_amount": loan.disbursed_amount,
                "disbursement_date": loan.disbursement_date
            },
            "transaction_id": str(transaction.id)
        })


class LoanRepaymentView(APIView):
    """Enhanced API endpoint for loan repayment"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @transaction.atomic
    def post(self, request, loan_id):
        """Process loan repayment with enhanced payment methods"""
        
        # Allow members to make repayments for their own loans
        try:
            loan = Loan.objects.get(id=loan_id)
        except Loan.DoesNotExist:
            return Response(
                {"error": "Loan not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check permissions - admin or loan owner
        if request.user.role != SaccoUser.ADMIN and request.user != loan.member:
            return Response(
                {"error": "You don't have permission to make repayments for this loan"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if loan is in correct status
        if loan.status != 'DISBURSED':
            return Response(
                {"error": f"Loan is {loan.get_status_display()}, not Disbursed"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate input
        serializer = LoanRepaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get payment method if provided
        payment_method = None
        if 'payment_method' in serializer.validated_data:
            try:
                payment_method = PaymentMethod.objects.get(
                    id=serializer.validated_data['payment_method'],
                    allowed_for_repayment=True,
                    status='ACTIVE'
                )
            except PaymentMethod.DoesNotExist:
                return Response(
                    {"error": "Invalid or inactive payment method for repayment"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Process the repayment
        amount = serializer.validated_data['amount']
        transaction_details = {
            'reference_number': serializer.validated_data.get('reference_number', ''),
            'transaction_code': serializer.validated_data.get('transaction_code', ''),
            'transaction_message': serializer.validated_data.get('transaction_message', '')
        }
        
        # Add payment method details if available
        if payment_method:
            transaction_details['payment_method'] = payment_method.name
        
        # Add repayment
        repayment = loan.add_repayment(amount, transaction_details, request.user)
        
        # Create transaction record
        transaction_description = f"Loan repayment"
        if payment_method:
            transaction_description += f" via {payment_method.name}"
        
        transaction = Transaction.objects.create(
            transaction_type='LOAN_REPAYMENT',
            member=loan.member,
            amount=amount,
            transaction_date=repayment.transaction_date,
            description=transaction_description,
            reference_number=repayment.reference_number,
            related_loan=loan,
            created_by=request.user
        )
        
        # Update repayment schedule
        schedules = RepaymentSchedule.objects.filter(
            loan=loan,
            status__in=['PENDING', 'PARTIAL', 'OVERDUE']
        ).order_by('due_date')
        
        remaining_amount = amount
        for schedule in schedules:
            if remaining_amount <= 0:
                break
                
            if schedule.remaining_amount <= remaining_amount:
                # This installment can be fully paid
                paid_amount = schedule.remaining_amount
                schedule.amount_paid += paid_amount
                schedule.remaining_amount = 0
                schedule.status = 'PAID'
                schedule.save()
                
                remaining_amount -= paid_amount
            else:
                # Partial payment for this installment
                schedule.amount_paid += remaining_amount
                schedule.remaining_amount -= remaining_amount
                schedule.status = 'PARTIAL'
                schedule.save()
                
                remaining_amount = 0
        
        # Create loan notification
        notification_type = 'LOAN_PAID' if loan.status == 'SETTLED' else 'PAYMENT_RECEIVED'
        notification_message = (
            "Your loan has been fully repaid. Thank you!" 
            if loan.status == 'SETTLED' 
            else f"We have received your loan payment of {amount}. Remaining balance: {loan.remaining_balance}"
        )
        
        notification = LoanNotification.objects.create(
            loan=loan,
            notification_type=notification_type,
            message=notification_message
        )
        
        # Send the notification
        notification.send_notification()
        
        # Log the activity
        ActivityLog.objects.create(
            user=request.user,
            action='LOAN_REPAYMENT',
            description=f"Recorded loan repayment of {amount} for {loan.member.full_name}"
        )
        
        return Response({
            "status": "success",
            "message": "Loan repayment processed successfully",
            "repayment": {
                "id": str(repayment.id),
                "amount": repayment.amount,
                "transaction_date": repayment.transaction_date,
                "reference_number": repayment.reference_number
            },
            "loan": {
                "id": str(loan.id),
                "status": loan.status,
                "total_repaid": loan.total_repaid,
                "remaining_balance": loan.remaining_balance,
                "is_settled": loan.status == 'SETTLED'
            },
            "transaction_id": str(transaction.id)
        })

# Add these classes to loans/views.py

class EligibleGuarantorsView(APIView):
    """API endpoint to get eligible guarantors for a loan"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get eligible guarantors for a loan amount"""
        
        # Get loan amount from query params
        loan_amount = request.query_params.get('loan_amount')
        if not loan_amount:
            return Response({"error": "Loan amount is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            loan_amount = decimal.Decimal(loan_amount)
        except:
            return Response({"error": "Invalid loan amount"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get all members except the current user
        members = SaccoUser.objects.filter(
            role='MEMBER', 
            is_active=True, 
            is_on_hold=False
        ).exclude(id=request.user.id)
        
        eligible_guarantors = []
        
        for member in members:
            # Get or update guarantor limit
            limit = GuarantorLimit.update_guarantor_limit(member)
            
            if limit and limit.available_guarantee_amount > 0:
                # Calculate maximum percentage they can guarantee
                max_percentage = min(100, (limit.available_guarantee_amount / loan_amount) * 100)
                
                if max_percentage >= 1:  # Only include if they can guarantee at least 1%
                    eligible_guarantors.append({
                        'id': member.id,
                        'full_name': member.full_name,
                        'email': member.email,
                        'phone_number': member.phone_number,
                        'available_guarantee_amount': limit.available_guarantee_amount,
                        'maximum_percentage': max_percentage
                    })
        
        # Sort by available guarantee amount (descending)
        eligible_guarantors.sort(key=lambda x: x['available_guarantee_amount'], reverse=True)
        
        serializer = EligibleGuarantorSerializer(eligible_guarantors, many=True)
        return Response(serializer.data)


class GuarantorRequestViewSet(viewsets.ModelViewSet):
    """API endpoint for guarantor requests"""
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GuarantorRequestSerializer
    
    def get_queryset(self):
        """Return guarantor requests based on user role"""
        user = self.request.user
        
        # Filter by status
        status_param = self.request.query_params.get('status')
        
        if user.role == 'ADMIN':
            # Admins see all requests
            queryset = GuarantorRequest.objects.all()
        else:
            # Members see requests they're involved in
            queryset = GuarantorRequest.objects.filter(
                models.Q(requester=user) | models.Q(guarantor=user)
            )
        
        # Apply status filter if provided
        if status_param:
            queryset = queryset.filter(status=status_param.upper())
            
        return queryset.order_by('-requested_at')
    
    def perform_create(self, serializer):
        # Set requester to current user
        serializer.save(requester=self.request.user)
        
        # Log the activity
        ActivityLog.objects.create(
            user=self.request.user,
            action='GUARANTOR_REQUEST',
            description=f"Requested {serializer.instance.guarantor.full_name} to guarantee {serializer.instance.guarantee_percentage}% of loan"
        )
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Accept a guarantor request"""
        
        guarantor_request = self.get_object()
        
        # Only the guarantor can accept
        if request.user != guarantor_request.guarantor:
            return Response(
                {"error": "Only the requested guarantor can accept this request"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if request is still pending
        if guarantor_request.status != 'PENDING':
            return Response(
                {"error": f"Request is already {guarantor_request.get_status_display()}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get response message
        response_message = request.data.get('response_message', '')
        
        # Accept the request
        guarantor_request.accept(response_message)
        
        # Log the activity
        ActivityLog.objects.create(
            user=request.user,
            action='GUARANTOR_ACCEPT',
            description=f"Accepted guarantor request for {guarantor_request.loan_application.member.full_name}'s loan"
        )
        
        return Response({
            "status": "success",
            "message": "Guarantor request accepted"
        })
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a guarantor request"""
        
        guarantor_request = self.get_object()
        
        # Only the guarantor can reject
        if request.user != guarantor_request.guarantor:
            return Response(
                {"error": "Only the requested guarantor can reject this request"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if request is still pending
        if guarantor_request.status != 'PENDING':
            return Response(
                {"error": f"Request is already {guarantor_request.get_status_display()}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get response message
        response_message = request.data.get('response_message', '')
        
        # Reject the request
        guarantor_request.reject(response_message)
        
        # Log the activity
        ActivityLog.objects.create(
            user=request.user,
            action='GUARANTOR_REJECT',
            description=f"Rejected guarantor request for {guarantor_request.loan_application.member.full_name}'s loan"
        )
        
        return Response({
            "status": "success",
            "message": "Guarantor request rejected"
        })
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending guarantor requests for the current user"""
        
        pending_requests = GuarantorRequest.objects.filter(
            guarantor=request.user,
            status='PENDING'
        ).order_by('-requested_at')
        
        serializer = self.get_serializer(pending_requests, many=True)
        return Response(serializer.data)