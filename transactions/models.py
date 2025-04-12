# transactions/models.py

import uuid
import decimal
from django.db import models
from django.utils import timezone
from authentication.models import SaccoUser
from sacco_core.models import Transaction


class SaccoExpense(models.Model):
    """SACCO expenses"""
    
    EXPENSE_CATEGORIES = [
        ('ADMINISTRATIVE', 'Administrative Expenses'),
        ('OPERATION', 'Operational Expenses'),
        ('RENTAL', 'Rent and Utilities'),
        ('BANKING', 'Banking Charges'),
        ('MARKETING', 'Marketing and Advertising'),
        ('TECHNOLOGY', 'Technology and Systems'),
        ('PROFESSIONAL', 'Professional Services'),
        ('OTHER', 'Other Expenses'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    expense_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField()
    category = models.CharField(max_length=15, choices=EXPENSE_CATEGORIES)
    
    # Payment details
    payment_method = models.CharField(max_length=50)
    reference_number = models.CharField(max_length=50, blank=True)
    receipt_image = models.FileField(upload_to='expense_receipts/', null=True, blank=True)
    
    # Transaction costs
    transaction_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Record keeping
    recorded_by = models.ForeignKey(
        SaccoUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='recorded_expenses'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Related transaction
    transaction = models.OneToOneField(
        Transaction, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='expense'
    )
    
    class Meta:
        ordering = ['-expense_date', '-created_at']
    
    def __str__(self):
        return f"Expense - {self.get_category_display()} - {self.amount}"
    
    def save(self, *args, **kwargs):
        # Create a corresponding transaction record if not already exists
        super().save(*args, **kwargs)
        
        if not self.transaction:
            transaction = Transaction.objects.create(
                transaction_type='EXPENSE',
                amount=self.amount,
                transaction_date=self.expense_date,
                transaction_cost=self.transaction_cost,
                description=f"{self.get_category_display()}: {self.description}",
                reference_number=self.reference_number,
                created_by=self.recorded_by
            )
            
            self.transaction = transaction
            self.save(update_fields=['transaction'])


class SaccoIncome(models.Model):
    """SACCO income other than loan interest and fees"""
    
    INCOME_CATEGORIES = [
        ('INVESTMENT', 'Investment Returns'),
        ('MEMBERSHIP', 'Membership Fees'),
        ('PENALTIES', 'Penalties and Fines'),
        ('DONATIONS', 'Donations'),
        ('GRANTS', 'Grants'),
        ('OTHER', 'Other Income'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    income_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField()
    category = models.CharField(max_length=15, choices=INCOME_CATEGORIES)
    
    # Payment details
    payment_method = models.CharField(max_length=50)
    reference_number = models.CharField(max_length=50, blank=True)
    receipt_image = models.FileField(upload_to='income_receipts/', null=True, blank=True)
    
    # Record keeping
    recorded_by = models.ForeignKey(
        SaccoUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='recorded_income'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Related transaction
    transaction = models.OneToOneField(
        Transaction, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='income'
    )
    
    class Meta:
        ordering = ['-income_date', '-created_at']
    
    def __str__(self):
        return f"Income - {self.get_category_display()} - {self.amount}"
    
    def save(self, *args, **kwargs):
        # Create a corresponding transaction record if not already exists
        super().save(*args, **kwargs)
        
        if not self.transaction:
            transaction = Transaction.objects.create(
                transaction_type='INCOME',
                amount=self.amount,
                transaction_date=self.income_date,
                description=f"{self.get_category_display()}: {self.description}",
                reference_number=self.reference_number,
                created_by=self.recorded_by
            )
            
            self.transaction = transaction
            self.save(update_fields=['transaction'])


class TransactionBatch(models.Model):
    """Batch of transactions for bulk processing"""
    
    BATCH_TYPES = [
        ('CONTRIBUTION', 'Monthly Contributions'),
        ('SHARE_CAPITAL', 'Share Capital Payments'),
        ('LOAN_DISBURSEMENT', 'Loan Disbursements'),
        ('LOAN_REPAYMENT', 'Loan Repayments'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending Processing'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch_type = models.CharField(max_length=20, choices=BATCH_TYPES)
    description = models.TextField(blank=True)
    transaction_date = models.DateField()
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    transaction_count = models.PositiveIntegerField(default=0)
    
    # Batch file (e.g., CSV upload)
    batch_file = models.FileField(upload_to='transaction_batches/', null=True, blank=True)
    
    # Processing details
    processed_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)
    processing_notes = models.TextField(blank=True)
    
    # Tracking
    created_by = models.ForeignKey(
        SaccoUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_transaction_batches'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Transaction Batch - {self.get_batch_type_display()} - {self.transaction_date}"


class BatchItem(models.Model):
    """Individual item in a transaction batch"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSED', 'Processed'),
        ('FAILED', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(TransactionBatch, on_delete=models.CASCADE, related_name='items')
    
    # Transaction details
    member = models.ForeignKey(
        SaccoUser, 
        on_delete=models.CASCADE, 
        related_name='batch_items'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reference_number = models.CharField(max_length=50, blank=True)
    transaction_code = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    
    # Processing status
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    error_message = models.TextField(blank=True)
    
    # Related transaction
    transaction = models.OneToOneField(
        Transaction, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='batch_item'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['batch', 'created_at']
    
    def __str__(self):
        return f"Batch Item - {self.member.full_name} - {self.amount}"


class TransactionLog(models.Model):
    """Log of all financial transactions for audit purposes"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='log')
    
    # IP and device information
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Additional audit information
    previous_state = models.JSONField(null=True, blank=True)
    new_state = models.JSONField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Transaction Log - {self.transaction}"


class BankAccount(models.Model):
    """SACCO bank accounts"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account_name = models.CharField(max_length=100)
    bank_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=50)
    branch = models.CharField(max_length=100, blank=True)
    
    # Account type and purpose
    account_type = models.CharField(max_length=50)
    is_primary = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Balance tracking
    current_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    last_reconciled = models.DateField(null=True, blank=True)
    
    # Contact details
    contact_person = models.CharField(max_length=100, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_primary', 'bank_name', 'account_name']
    
    def __str__(self):
        return f"{self.bank_name} - {self.account_name} ({self.account_number})"
    
    def save(self, *args, **kwargs):
        # Ensure only one primary account
        if self.is_primary:
            BankAccount.objects.filter(is_primary=True).exclude(pk=self.pk).update(is_primary=False)
        
        super().save(*args, **kwargs)


class BankTransaction(models.Model):
    """Transactions in SACCO bank accounts"""
    
    TRANSACTION_TYPES = [
        ('DEPOSIT', 'Deposit'),
        ('WITHDRAWAL', 'Withdrawal'),
        ('TRANSFER', 'Transfer'),
        ('INTEREST', 'Interest Credit'),
        ('FEE', 'Bank Fee/Charge'),
        ('OTHER', 'Other Transaction'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='transactions')
    
    transaction_date = models.DateField()
    value_date = models.DateField(null=True, blank=True)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)
    reference_number = models.CharField(max_length=50, blank=True)
    
    # For transfers between accounts
    destination_account = models.ForeignKey(
        BankAccount, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='incoming_transfers'
    )
    
    # Reconciliation
    is_reconciled = models.BooleanField(default=False)
    reconciliation_date = models.DateField(null=True, blank=True)
    reconciled_by = models.ForeignKey(
        SaccoUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='reconciled_transactions'
    )
    
    # Related transaction
    related_transaction = models.OneToOneField(
        Transaction, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='bank_transaction'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey(
        SaccoUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='recorded_bank_transactions'
    )
    
    class Meta:
        ordering = ['-transaction_date', '-created_at']
    
    def __str__(self):
        return f"{self.account.bank_name} - {self.get_transaction_type_display()} - {self.amount}"
    
    def save(self, *args, **kwargs):
        is_new = not self.pk
        super().save(*args, **kwargs)
        
        # Update account balance
        if is_new:
            account = self.account
            
            if self.transaction_type in ['DEPOSIT', 'INTEREST']:
                account.current_balance += self.amount
            elif self.transaction_type in ['WITHDRAWAL', 'FEE']:
                account.current_balance -= self.amount
            elif self.transaction_type == 'TRANSFER':
                if self.destination_account:
                    account.current_balance -= self.amount
                    self.destination_account.current_balance += self.amount
                    self.destination_account.save()
            
            account.save()