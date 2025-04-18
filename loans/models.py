# loans/models.py

import uuid
import decimal
from datetime import timedelta
from django.db import models
from django.utils import timezone
from authentication.models import SaccoUser
from sacco_core.models import Loan, LoanRepayment, Transaction


class LoanApplication(models.Model):
    """Loan applications by members"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled by Member'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    member = models.ForeignKey(SaccoUser, on_delete=models.CASCADE, related_name='loan_applications')
    
    # Loan details
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    purpose = models.TextField()
    term_months = models.PositiveIntegerField(default=12)
    application_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    
    # Supporting documents
    has_guarantor = models.BooleanField(default=False)
    guarantor_name = models.CharField(max_length=255, blank=True)
    guarantor_contact = models.CharField(max_length=50, blank=True)
    guarantor_relationship = models.CharField(max_length=50, blank=True)
    
    # Supporting documents
    application_document = models.FileField(upload_to='loan_applications/', null=True, blank=True)
    
    # Approval/Rejection
    reviewed_date = models.DateField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        SaccoUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='reviewed_applications'
    )
    rejection_reason = models.TextField(blank=True)
    
    # Created loan reference
    loan = models.OneToOneField(
        Loan, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='originating_application'
    )
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-application_date', '-created_at']
    
    def __str__(self):
        return f"Loan Application - {self.member.full_name} - {self.amount} - {self.get_status_display()}"
    
    def approve_application(self, admin_user, interest_rate=None):
        """Approve the loan application and create a loan"""
        
        if self.status != 'PENDING':
            return False
        
        from sacco_core.models import SaccoSettings, MemberShareSummary
        
        # Get SACCO settings for interest rate if not provided
        if not interest_rate:
            settings = SaccoSettings.get_settings()
            interest_rate = settings.loan_interest_rate
        
        # Create the loan
        loan = Loan.objects.create(
            member=self.member,
            amount=self.amount,
            interest_rate=interest_rate,
            term_months=self.term_months,
            purpose=self.purpose,
            status='APPROVED',
            approved_by=admin_user
        )
        
        # Update application
        self.status = 'APPROVED'
        self.reviewed_date = timezone.now().date()
        self.reviewed_by = admin_user
        self.loan = loan
        self.save()
        
        return loan
    
    def reject_application(self, admin_user, rejection_reason):
        """Reject the loan application"""
        
        if self.status != 'PENDING':
            return False
        
        self.status = 'REJECTED'
        self.reviewed_date = timezone.now().date()
        self.reviewed_by = admin_user
        self.rejection_reason = rejection_reason
        self.save()
        
        return True


class LoanGuarantor(models.Model):
    """Guarantors for loans"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='guarantors')
    
    # Guarantor can be a member or external
    member_guarantor = models.ForeignKey(
        SaccoUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='guaranteed_loans'
    )
    
    # For external guarantors
    name = models.CharField(max_length=255, blank=True)
    id_number = models.CharField(max_length=20, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)
    relationship = models.CharField(max_length=50, blank=True)
    
    # Guarantor contribution
    guarantee_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    guarantee_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['loan', 'member_guarantor']  # One guarantee per loan per member
    
    def __str__(self):
        if self.member_guarantor:
            guarantor_name = self.member_guarantor.full_name
        else:
            guarantor_name = self.name
            
        return f"Guarantor - {guarantor_name} for {self.loan.member.full_name}'s loan"


class RepaymentSchedule(models.Model):
    """Loan repayment schedule"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PARTIAL', 'Partially Paid'),
        ('PAID', 'Paid'),
        ('OVERDUE', 'Overdue'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='repayment_schedule')
    
    installment_number = models.PositiveIntegerField()
    due_date = models.DateField()
    amount_due = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Breakdown
    principal_amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Tracking
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    remaining_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['loan', 'installment_number']
        unique_together = ['loan', 'installment_number']
    
    def __str__(self):
        return f"Installment {self.installment_number} - {self.loan.member.full_name} - {self.due_date}"
    
    def save(self, *args, **kwargs):
        # Calculate remaining amount if not set
        if self.remaining_amount == 0:
            self.remaining_amount = self.amount_due
            
        # Update status based on payment
        if self.amount_paid >= self.amount_due:
            self.status = 'PAID'
            self.remaining_amount = 0
        elif self.amount_paid > 0:
            self.status = 'PARTIAL'
            self.remaining_amount = self.amount_due - self.amount_paid
        elif self.due_date < timezone.now().date() and self.status == 'PENDING':
            self.status = 'OVERDUE'
            
        super().save(*args, **kwargs)
    
    @classmethod
    def generate_schedule(cls, loan):
        """Generate a repayment schedule for a loan"""
        
        if not loan.disbursement_date:
            return False
            
        # Delete any existing schedule
        cls.objects.filter(loan=loan).delete()
        
        # Calculate monthly payment (principal + interest)
        principal = loan.amount
        monthly_interest_rate = loan.interest_rate / 100 / 12
        term_months = loan.term_months
        
        # For simple interest loans
        # Monthly payment = (Principal + Total Interest) / Term
        total_interest = principal * monthly_interest_rate * term_months
        monthly_payment = (principal + total_interest) / term_months
        
        # Create schedule
        start_date = loan.disbursement_date
        
        schedules = []
        remaining_principal = principal
        
        for i in range(1, term_months + 1):
            # Calculate due date
            due_date = start_date + timedelta(days=30 * i)
            
            # Calculate interest for this period
            interest_payment = remaining_principal * monthly_interest_rate
            
            # Calculate principal for this period
            if i == term_months:
                # Last payment - ensure we pay exactly the remaining principal
                principal_payment = remaining_principal
                # Adjust monthly payment for last installment
                monthly_payment = principal_payment + interest_payment
            else:
                # Regular payment
                principal_payment = min(monthly_payment - interest_payment, remaining_principal)
            
            # Create schedule item
            schedule = cls(
                loan=loan,
                installment_number=i,
                due_date=due_date,
                amount_due=principal_payment + interest_payment,
                principal_amount=principal_payment,
                interest_amount=interest_payment,
                remaining_amount=principal_payment + interest_payment
            )
            schedules.append(schedule)
            
            # Update remaining principal
            remaining_principal -= principal_payment
            
        # Bulk create all schedules
        cls.objects.bulk_create(schedules)
        return True


class LoanStatement(models.Model):
    """Loan statements for members"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='statements')
    statement_date = models.DateField()
    
    # Summary information
    principal_amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    remaining_balance = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Statement details
    payoff_amount = models.DecimalField(max_digits=12, decimal_places=2)
    overdue_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    next_payment_date = models.DateField(null=True, blank=True)
    next_payment_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Statement files
    statement_file = models.FileField(upload_to='loan_statements/', null=True, blank=True)
    
    generated_by = models.ForeignKey(
        SaccoUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='generated_loan_statements'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-statement_date', '-created_at']
    
    def __str__(self):
        return f"Loan Statement - {self.loan.member.full_name} - {self.statement_date}"
    
    @classmethod
    def generate_statement(cls, loan, admin_user):
        """Generate a loan statement"""
        
        statement = cls(
            loan=loan,
            statement_date=timezone.now().date(),
            principal_amount=loan.amount,
            interest_rate=loan.interest_rate,
            total_amount=loan.total_expected_repayment,
            amount_paid=loan.total_repaid,
            remaining_balance=loan.remaining_balance,
            payoff_amount=loan.remaining_balance,
            generated_by=admin_user
        )
        
        # Get next payment schedule
        next_schedule = RepaymentSchedule.objects.filter(
            loan=loan, 
            status__in=['PENDING', 'PARTIAL']
        ).order_by('due_date').first()
        
        if next_schedule:
            statement.next_payment_date = next_schedule.due_date
            statement.next_payment_amount = next_schedule.remaining_amount
            
            # Check if overdue
            if next_schedule.status == 'OVERDUE':
                statement.overdue_amount = next_schedule.remaining_amount
        
        statement.save()
        return statement


class LoanNotification(models.Model):
    """Notifications for loan-related activities"""
    
    NOTIFICATION_TYPES = [
        ('APPROVAL', 'Loan Approved'),
        ('REJECTION', 'Loan Rejected'),
        ('DISBURSEMENT', 'Loan Disbursed'),
        ('PAYMENT_DUE', 'Payment Due Reminder'),
        ('PAYMENT_RECEIVED', 'Payment Received'),
        ('PAYMENT_OVERDUE', 'Payment Overdue'),
        ('LOAN_PAID', 'Loan Fully Paid'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    
    sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.loan.member.full_name}"
    
    def send_notification(self):
        """Send the notification to the member"""
        
        if self.sent:
            return False
            
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.conf import settings
        
        member = self.loan.member
        
        context = {
            'member_name': member.full_name or member.email,
            'loan_amount': self.loan.amount,
            'message': self.message,
            'notification_type': self.get_notification_type_display(),
        }
        
        if self.notification_type == 'PAYMENT_DUE':
            # Add payment details
            next_schedule = RepaymentSchedule.objects.filter(
                loan=self.loan, 
                status__in=['PENDING', 'PARTIAL']
            ).order_by('due_date').first()
            
            if next_schedule:
                context.update({
                    'payment_date': next_schedule.due_date,
                    'payment_amount': next_schedule.remaining_amount,
                })
        
        # Prepare HTML email
        html_message = render_to_string('emails/loan_notification.html', context)
        
        try:
            # Send the email
            send_mail(
                f"SACCO Loan Notification: {self.get_notification_type_display()}",
                self.message,
                settings.DEFAULT_FROM_EMAIL,
                [member.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            self.sent = True
            self.sent_at = timezone.now()
            self.save()
            
            return True
            
        except Exception as e:
            # Log the error
            print(f"Failed to send loan notification: {str(e)}")
            return False
        
# Add this to your existing loans/models.py

class PaymentMethod(models.Model):
    """Payment methods for loan disbursements and repayments"""
    
    PAYMENT_TYPE_CHOICES = [
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('MOBILE_MONEY', 'Mobile Money'),
        ('CHEQUE', 'Cheque'),
        ('CASH', 'Cash'),
        ('CARD', 'Debit/Credit Card'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('PENDING', 'Pending Verification'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)
    description = models.TextField(blank=True)
    
    # For bank transfers
    bank_name = models.CharField(max_length=100, blank=True)
    account_name = models.CharField(max_length=100, blank=True)
    account_number = models.CharField(max_length=50, blank=True)
    
    # For mobile money
    provider = models.CharField(max_length=50, blank=True)  # e.g., M-Pesa, Airtel Money
    phone_number = models.CharField(max_length=20, blank=True)
    
    # For internal identification
    internal_code = models.CharField(max_length=50, blank=True)
    
    # Status
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ACTIVE')
    transaction_fee_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    transaction_fee_fixed = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # For admin use
    is_default = models.BooleanField(default=False)
    allowed_for_disbursement = models.BooleanField(default=True)
    allowed_for_repayment = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_payment_type_display()})"
    
    def calculate_transaction_fee(self, amount):
        """Calculate transaction fee for a given amount"""
        percentage_fee = amount * (self.transaction_fee_percentage / 100)
        total_fee = percentage_fee + self.transaction_fee_fixed
        return total_fee
    
    def save(self, *args, **kwargs):
        # If this payment method is set as default, unset others
        if self.is_default:
            PaymentMethod.objects.filter(is_default=True).exclude(id=self.id).update(is_default=False)
        super().save(*args, **kwargs)


class LoanDisbursement(models.Model):
    """Records loan disbursement details"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='disbursements')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Payment method details
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT, related_name='loan_disbursements')
    reference_number = models.CharField(max_length=100)
    transaction_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=12, decimal_places=2)  # Amount after fees
    
    # Recipient details
    recipient_account = models.CharField(max_length=100, blank=True)
    recipient_name = models.CharField(max_length=255, blank=True)
    
    description = models.TextField(blank=True)
    disbursement_date = models.DateField()
    
    # Admin who processed the disbursement
    processed_by = models.ForeignKey(
        SaccoUser, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='processed_disbursements'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-disbursement_date', '-created_at']
    
    def __str__(self):
        return f"Disbursement for {self.loan.member.full_name}'s loan - {self.amount}"
    
    def save(self, *args, **kwargs):
        # Calculate net amount if not set
        if not self.net_amount:
            self.net_amount = self.amount - self.transaction_cost
        
        super().save(*args, **kwargs)