# sacco_core/models.py

import uuid
import decimal
from django.db import models
from django.utils import timezone
from authentication.models import SaccoUser

class SaccoSettings(models.Model):
    """Global SACCO settings"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, default="SACCO Organization")
    share_value = models.DecimalField(max_digits=10, decimal_places=2, default=5000.00)
    minimum_monthly_contribution = models.DecimalField(max_digits=10, decimal_places=2, default=1000.00)
    loan_interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)  # Annual percentage
    maximum_loan_multiplier = models.DecimalField(max_digits=5, decimal_places=2, default=3.00)  # Multiple of shares
    loan_processing_fee_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    loan_insurance_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    
    # Contact information
    phone_number = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)
    postal_address = models.CharField(max_length=100, blank=True)
    physical_address = models.CharField(max_length=255, blank=True)
    
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        SaccoUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='settings_updates'
    )
    
    class Meta:
        verbose_name = "SACCO Settings"
        verbose_name_plural = "SACCO Settings"
    
    def __str__(self):
        return f"{self.name} Settings"
    
    @classmethod
    def get_settings(cls):
        """Get or create SACCO settings"""
        settings, created = cls.objects.get_or_create(pk=uuid.UUID('00000000-0000-0000-0000-000000000001'))
        return settings


class ShareCapital(models.Model):
    """Member share capital contributions"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    member = models.ForeignKey(SaccoUser, on_delete=models.CASCADE, related_name='share_capital')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_date = models.DateField()
    reference_number = models.CharField(max_length=50)
    transaction_code = models.CharField(max_length=50)
    transaction_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        SaccoUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='recorded_share_capital'
    )
    
    class Meta:
        ordering = ['-transaction_date', '-created_at']
    
    def __str__(self):
        return f"Share Capital - {self.member.full_name} - {self.amount}"
    
    def save(self, *args, **kwargs):
        # Update member's share capital total
        super().save(*args, **kwargs)
        
        # Recalculate and update member share totals
        MemberShareSummary.update_member_summary(self.member)
        

class MonthlyContribution(models.Model):
    """Member monthly contributions"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    member = models.ForeignKey(SaccoUser, on_delete=models.CASCADE, related_name='monthly_contributions')
    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField()  # 1-12 for January-December
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_date = models.DateField()
    reference_number = models.CharField(max_length=50)
    transaction_code = models.CharField(max_length=50)
    transaction_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        SaccoUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='recorded_contributions'
    )
    
    class Meta:
        ordering = ['-year', '-month', '-created_at']
        unique_together = ['member', 'year', 'month']  # Ensure one contribution per month
    
    def __str__(self):
        return f"Contribution - {self.member.full_name} - {self.year}/{self.month} - {self.amount}"
    
    def save(self, *args, **kwargs):
        # Update member's contribution total
        super().save(*args, **kwargs)
        
        # Recalculate and update member contribution totals
        MemberShareSummary.update_member_summary(self.member)


class MemberShareSummary(models.Model):
    """Summary of member's shares and contributions"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    member = models.OneToOneField(SaccoUser, on_delete=models.CASCADE, related_name='share_summary')
    
    # Share capital
    total_share_capital = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    share_capital_target = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    share_capital_completion_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Monthly contributions
    total_contributions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    current_year_contributions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    previous_year_contributions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Shares
    total_deposits = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # Share capital + contributions
    percentage_of_total_pool = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # % of all deposits
    number_of_shares = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Dividends
    total_dividends_received = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    last_dividend_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    last_dividend_date = models.DateField(null=True, blank=True)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Member Share Summary"
        verbose_name_plural = "Member Share Summaries"
    
    def __str__(self):
        return f"Share Summary - {self.member.full_name}"
    
    @classmethod
    def update_member_summary(cls, member):
        """Update the summary for a specific member"""
        
        # Get or create summary
        summary, created = cls.objects.get_or_create(member=member)
        
        # Calculate share capital
        settings = SaccoSettings.get_settings()
        total_share_capital = ShareCapital.objects.filter(member=member).aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        
        # Set share capital target
        share_capital_target = settings.share_value
        
        # Calculate completion percentage
        if share_capital_target > 0:
            completion_percentage = min(100, (total_share_capital / share_capital_target) * 100)
        else:
            completion_percentage = 0
        
        # Calculate contributions
        current_year = timezone.now().year
        total_contributions = MonthlyContribution.objects.filter(member=member).aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        
        current_year_contributions = MonthlyContribution.objects.filter(
            member=member, year=current_year
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        
        previous_year_contributions = MonthlyContribution.objects.filter(
            member=member, year=current_year-1
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        
        # Total deposits
        total_deposits = total_share_capital + total_contributions
        
        # Number of shares
        number_of_shares = 0
        if settings.share_value > 0:
            number_of_shares = total_share_capital / settings.share_value
        
        # Update the summary
        summary.total_share_capital = total_share_capital
        summary.share_capital_target = share_capital_target
        summary.share_capital_completion_percentage = completion_percentage
        summary.total_contributions = total_contributions
        summary.current_year_contributions = current_year_contributions
        summary.previous_year_contributions = previous_year_contributions
        summary.total_deposits = total_deposits
        summary.number_of_shares = number_of_shares
        summary.save()
        
        # Recalculate percentage shares for all members
        cls.recalculate_percentages()
    
    @classmethod
    def recalculate_percentages(cls):
        """Recalculate percentage shares for all members"""
        
        # Get total deposits across all members
        total_pool = cls.objects.aggregate(
            total=models.Sum('total_deposits')
        )['total'] or 0
        
        if total_pool > 0:
            # Update each member's percentage
            for summary in cls.objects.all():
                percentage = (summary.total_deposits / total_pool) * 100
                summary.percentage_of_total_pool = percentage
                summary.save(update_fields=['percentage_of_total_pool'])


class DividendDistribution(models.Model):
    """Dividend distribution to members"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    distribution_date = models.DateField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    source = models.CharField(max_length=50, default="Interest Income")  # Source of dividends
    description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    distributed_by = models.ForeignKey(
        SaccoUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='distributed_dividends'
    )
    
    class Meta:
        ordering = ['-distribution_date', '-created_at']
    
    def __str__(self):
        return f"Dividend Distribution - {self.distribution_date} - {self.total_amount}"


class MemberDividend(models.Model):
    """Individual member dividend allocation"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    distribution = models.ForeignKey(
        DividendDistribution, 
        on_delete=models.CASCADE, 
        related_name='member_dividends'
    )
    member = models.ForeignKey(
        SaccoUser, 
        on_delete=models.CASCADE, 
        related_name='dividends'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    percentage_share = models.DecimalField(max_digits=5, decimal_places=2)  # % of total distribution
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-distribution__distribution_date', '-created_at']
        unique_together = ['distribution', 'member']  # One dividend per member per distribution
    
    def __str__(self):
        return f"Dividend - {self.member.full_name} - {self.distribution.distribution_date} - {self.amount}"
    
    def save(self, *args, **kwargs):
        # Save the dividend
        super().save(*args, **kwargs)
        
        # Update member's dividend summary
        summary, created = MemberShareSummary.objects.get_or_create(member=self.member)
        summary.total_dividends_received += self.amount
        summary.last_dividend_amount = self.amount
        summary.last_dividend_date = self.distribution.distribution_date
        summary.save()


class Loan(models.Model):
    """Member loans"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('DISBURSED', 'Disbursed'),
        ('REJECTED', 'Rejected'),
        ('SETTLED', 'Settled'),
        ('DEFAULTED', 'Defaulted'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    member = models.ForeignKey(SaccoUser, on_delete=models.CASCADE, related_name='loans')
    
    # Loan details
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)  # Annual percentage
    application_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    purpose = models.TextField()
    
    # Terms
    term_months = models.PositiveIntegerField(default=12)
    approval_date = models.DateField(null=True, blank=True)
    disbursement_date = models.DateField(null=True, blank=True)
    expected_completion_date = models.DateField(null=True, blank=True)
    
    # Processing
    processing_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    insurance_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    disbursed_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Repayment
    total_expected_repayment = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_repaid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    remaining_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Approvals
    approved_by = models.ForeignKey(
        SaccoUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='approved_loans'
    )
    disbursed_by = models.ForeignKey(
        SaccoUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='disbursed_loans'
    )
    rejection_reason = models.TextField(blank=True)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-application_date', '-created_at']
    
    def __str__(self):
        return f"Loan - {self.member.full_name} - {self.amount} - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        if not self.pk:  # New loan
            # Calculate processing and insurance fees
            settings = SaccoSettings.get_settings()
            self.processing_fee = (settings.loan_processing_fee_percentage / 100) * self.amount
            self.insurance_fee = (settings.loan_insurance_percentage / 100) * self.amount
            
            # Calculate disbursed amount
            self.disbursed_amount = self.amount - self.processing_fee - self.insurance_fee
            
            # Calculate total expected repayment (simple interest)
            monthly_interest_rate = self.interest_rate / 100 / 12
            self.total_expected_repayment = self.amount * (1 + (monthly_interest_rate * self.term_months))
            self.remaining_balance = self.total_expected_repayment
        
        elif self.status == 'APPROVED' and not self.approval_date:
            self.approval_date = timezone.now().date()
        
        elif self.status == 'DISBURSED' and not self.disbursement_date:
            self.disbursement_date = timezone.now().date()
            # Set expected completion date
            self.expected_completion_date = self.disbursement_date + timezone.timedelta(days=30 * self.term_months)
        
        super().save(*args, **kwargs)
    
    def add_repayment(self, amount, transaction_details, admin_user):
        """Add a loan repayment"""
        
        # Create repayment record
        repayment = LoanRepayment.objects.create(
            loan=self,
            amount=amount,
            transaction_date=timezone.now().date(),
            reference_number=transaction_details.get('reference_number', ''),
            transaction_code=transaction_details.get('transaction_code', ''),
            transaction_message=transaction_details.get('transaction_message', ''),
            created_by=admin_user
        )
        
        # Update loan status
        self.total_repaid += amount
        self.remaining_balance -= amount
        
        if self.remaining_balance <= 0:
            self.status = 'SETTLED'
            self.remaining_balance = 0
        
        self.save()
        
        return repayment


class LoanRepayment(models.Model):
    """Loan repayments"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='repayments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_date = models.DateField()
    reference_number = models.CharField(max_length=50)
    transaction_code = models.CharField(max_length=50)
    transaction_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        SaccoUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='recorded_repayments'
    )
    
    class Meta:
        ordering = ['-transaction_date', '-created_at']
    
    def __str__(self):
        return f"Repayment - {self.loan.member.full_name} - {self.amount}"


class Transaction(models.Model):
    """Financial transactions in the SACCO"""
    
    TRANSACTION_TYPES = [
        ('SHARE_CAPITAL', 'Share Capital Payment'),
        ('MONTHLY_CONTRIBUTION', 'Monthly Contribution'),
        ('LOAN_DISBURSEMENT', 'Loan Disbursement'),
        ('LOAN_REPAYMENT', 'Loan Repayment'),
        ('DIVIDEND_PAYMENT', 'Dividend Payment'),
        ('EXPENSE', 'SACCO Expense'),
        ('INCOME', 'SACCO Income'),
        ('OTHER', 'Other Transaction')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    member = models.ForeignKey(
        SaccoUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='transactions'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_date = models.DateField()
    transaction_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # References to related records
    related_loan = models.ForeignKey(
        Loan, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='transactions'
    )
    related_dividend = models.ForeignKey(
        DividendDistribution, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='transactions'
    )
    
    description = models.TextField(blank=True)
    reference_number = models.CharField(max_length=50, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        SaccoUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='recorded_transactions'
    )
    
    class Meta:
        ordering = ['-transaction_date', '-created_at']
    
    def __str__(self):
        transaction_party = self.member.full_name if self.member else "SACCO"
        return f"{self.get_transaction_type_display()} - {transaction_party} - {self.amount}"


class FinancialSummary(models.Model):
    """SACCO financial summary"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField(unique=True)
    
    # Assets
    total_share_capital = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_contributions = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    outstanding_loans = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cash_at_hand = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_assets = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Income
    interest_income = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    fees_income = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    other_income = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_income = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Expenses
    operational_expenses = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    dividend_payments = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    other_expenses = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_expenses = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Metrics
    net_income = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    active_members = models.PositiveIntegerField(default=0)
    total_members = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
        verbose_name = "Financial Summary"
        verbose_name_plural = "Financial Summaries"
    
    def __str__(self):
        return f"Financial Summary - {self.date}"
    
    @classmethod
    def generate_current_summary(cls):
        """Generate a financial summary for the current date"""
        
        today = timezone.now().date()
        
        # Check if summary already exists for today
        existing_summary = cls.objects.filter(date=today).first()
        if existing_summary:
            summary = existing_summary
        else:
            summary = cls(date=today)
        
        # Calculate assets
        total_share_capital = ShareCapital.objects.aggregate(total=models.Sum('amount'))['total'] or 0
        total_contributions = MonthlyContribution.objects.aggregate(total=models.Sum('amount'))['total'] or 0
        
        # Outstanding loans (only 'DISBURSED' loans that aren't 'SETTLED' or 'DEFAULTED')
        outstanding_loans = Loan.objects.filter(
            status='DISBURSED'
        ).exclude(
            status__in=['SETTLED', 'DEFAULTED']
        ).aggregate(
            total=models.Sum('remaining_balance')
        )['total'] or 0
        
        # Income calculations
        interest_income = LoanRepayment.objects.aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        
        # Subtract original loan amounts to get interest only
        loan_principal = Loan.objects.filter(
            status='DISBURSED'
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        
        loan_repayments = LoanRepayment.objects.aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        
        if loan_repayments > loan_principal:
            interest_income = loan_repayments - loan_principal
        else:
            interest_income = 0
        
        # Fees income (processing & insurance)
        fees_income = Loan.objects.aggregate(
            processing=models.Sum('processing_fee'),
            insurance=models.Sum('insurance_fee')
        )
        fees_income = (fees_income.get('processing') or 0) + (fees_income.get('insurance') or 0)
        
        # Expenses
        dividend_payments = MemberDividend.objects.aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        
        # Active and total members
        active_members = SaccoUser.objects.filter(
            role='MEMBER',
            is_active=True,
            is_on_hold=False
        ).count()
        
        total_members = SaccoUser.objects.filter(role='MEMBER').count()
        
        # Cash at hand (contributions + share capital - outstanding loans - dividends)
        cash_at_hand = (total_share_capital + total_contributions) - outstanding_loans - dividend_payments
        
        # Total assets
        total_assets = cash_at_hand + outstanding_loans
        
        # Total income
        total_income = interest_income + fees_income
        
        # Total expenses (assuming operational expenses are manually entered)
        total_expenses = dividend_payments + summary.operational_expenses
        
        # Net income
        net_income = total_income - total_expenses
        
        # Update summary
        summary.total_share_capital = total_share_capital
        summary.total_contributions = total_contributions
        summary.outstanding_loans = outstanding_loans
        summary.cash_at_hand = cash_at_hand
        summary.total_assets = total_assets
        summary.interest_income = interest_income
        summary.fees_income = fees_income
        summary.total_income = total_income
        summary.dividend_payments = dividend_payments
        summary.total_expenses = total_expenses
        summary.net_income = net_income
        summary.active_members = active_members
        summary.total_members = total_members
        
        summary.save()
        return summary