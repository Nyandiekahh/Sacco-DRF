# reports/models.py

import uuid
from django.db import models
from django.utils import timezone
from authentication.models import SaccoUser


class Report(models.Model):
    """Base model for all reports"""
    
    REPORT_TYPES = [
        ('FINANCIAL_STATEMENT', 'Financial Statement'),
        ('MEMBER_STATEMENT', 'Member Statement'),
        ('LOAN_STATEMENT', 'Loan Statement'),
        ('CONTRIBUTION_REPORT', 'Contribution Report'),
        ('DIVIDEND_REPORT', 'Dividend Report'),
        ('AUDIT_REPORT', 'Audit Report'),
    ]
    
    FORMAT_CHOICES = [
        ('PDF', 'PDF Document'),
        ('EXCEL', 'Excel Spreadsheet'),
        ('CSV', 'CSV File'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    description = models.TextField(blank=True)
    
    # Date range
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    
    # Report format and file
    format = models.CharField(max_length=5, choices=FORMAT_CHOICES, default='PDF')
    report_file = models.FileField(upload_to='reports/', null=True, blank=True)
    
    # For member-specific reports
    member = models.ForeignKey(
        SaccoUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='member_reports'
    )
    
    # Tracking
    generated_by = models.ForeignKey(
        SaccoUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='generated_reports'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.created_at.date()}"


class FinancialStatement(models.Model):
    """Financial statements (Balance Sheet, Income Statement, etc.)"""
    
    STATEMENT_TYPES = [
        ('BALANCE_SHEET', 'Balance Sheet'),
        ('INCOME_STATEMENT', 'Income Statement'),
        ('CASH_FLOW', 'Cash Flow Statement'),
        ('EQUITY_CHANGES', 'Statement of Changes in Equity'),
    ]
    
    PERIOD_TYPES = [
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
        ('SEMI_ANNUAL', 'Semi-Annual'),
        ('ANNUAL', 'Annual'),
        ('CUSTOM', 'Custom Period'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    statement_type = models.CharField(max_length=20, choices=STATEMENT_TYPES)
    period_type = models.CharField(max_length=12, choices=PERIOD_TYPES)
    
    # For standard periods
    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField(null=True, blank=True)  # For monthly/quarterly
    quarter = models.PositiveIntegerField(null=True, blank=True)  # For quarterly
    
    # Date range
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Statement data (stored as JSON)
    statement_data = models.JSONField(null=True, blank=True)
    
    # References
    report = models.OneToOneField(
        Report, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='financial_statement'
    )
    
    # Approval
    approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        SaccoUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='approved_statements'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Tracking
    generated_by = models.ForeignKey(
        SaccoUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='generated_statements'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-year', '-month', '-quarter', '-created_at']
        unique_together = [
            ['statement_type', 'year', 'month'],
            ['statement_type', 'year', 'quarter'],
        ]
    
    def __str__(self):
        period = ''
        if self.period_type == 'MONTHLY' and self.month:
            period = f"{self.get_month_name()} {self.year}"
        elif self.period_type == 'QUARTERLY' and self.quarter:
            period = f"Q{self.quarter} {self.year}"
        elif self.period_type == 'ANNUAL':
            period = f"{self.year}"
        elif self.period_type == 'CUSTOM':
            period = f"{self.start_date} to {self.end_date}"
            
        return f"{self.get_statement_type_display()} - {period}"
    
    def get_month_name(self):
        """Get the month name from the month number"""
        if not self.month:
            return None
            
        months = [
            'January', 'February', 'March', 'April', 'May', 'June', 
            'July', 'August', 'September', 'October', 'November', 'December'
        ]
        return months[self.month - 1]


class MemberStatement(models.Model):
    """Statements for individual members"""
    
    STATEMENT_TYPES = [
        ('CONTRIBUTIONS', 'Contributions Statement'),
        ('SHARES', 'Shares Statement'),
        ('DIVIDENDS', 'Dividends Statement'),
        ('LOANS', 'Loans Statement'),
        ('COMPREHENSIVE', 'Comprehensive Statement'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    member = models.ForeignKey(SaccoUser, on_delete=models.CASCADE, related_name='statements')
    statement_type = models.CharField(max_length=20, choices=STATEMENT_TYPES)
    
    # Date range
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Statement data
    statement_data = models.JSONField(null=True, blank=True)
    
    # References
    report = models.OneToOneField(
        Report, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='member_statement'
    )
    
    # Tracking
    generated_by = models.ForeignKey(
        SaccoUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='generated_member_statements'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_statement_type_display()} - {self.member.full_name} - {self.start_date} to {self.end_date}"


class AuditLog(models.Model):
    """Audit logs for regulatory compliance"""
    
    ACTION_TYPES = [
        ('FINANCIAL', 'Financial Transaction'),
        ('MEMBER', 'Member Record Change'),
        ('LOAN', 'Loan Action'),
        ('SETTING', 'System Setting Change'),
        ('ADMIN', 'Administrative Action'),
        ('SECURITY', 'Security Event'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    action_type = models.CharField(max_length=10, choices=ACTION_TYPES)
    action_description = models.TextField()
    
    # Details
    entity_type = models.CharField(max_length=50)  # e.g., "Loan", "Member", "Transaction"
    entity_id = models.CharField(max_length=50)  # ID of the affected entity
    changes = models.JSONField(null=True, blank=True)  # Before/after data
    
    # User information
    user = models.ForeignKey(
        SaccoUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='audit_logs'
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Audit - {self.get_action_type_display()} - {self.entity_type} - {self.created_at}"


class SystemBackup(models.Model):
    """System backups"""
    
    BACKUP_TYPES = [
        ('SCHEDULED', 'Scheduled Backup'),
        ('MANUAL', 'Manual Backup'),
        ('PRE_UPDATE', 'Pre-Update Backup'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    backup_type = models.CharField(max_length=10, choices=BACKUP_TYPES)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='PENDING')
    backup_file = models.FileField(upload_to='system_backups/', null=True, blank=True)
    file_size = models.PositiveBigIntegerField(default=0)  # Size in bytes
    
    # Backup details
    included_modules = models.JSONField(default=list)  # List of modules included
    backup_date = models.DateTimeField()
    completion_date = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    # User information
    initiated_by = models.ForeignKey(
        SaccoUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='initiated_backups'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-backup_date']
    
    def __str__(self):
        return f"Backup - {self.name} - {self.backup_date}"


class SavedReport(models.Model):
    """Saved report templates"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Report type and format
    report_type = models.CharField(max_length=50)
    format = models.CharField(max_length=10)
    
    # Template parameters
    parameters = models.JSONField(default=dict)
    
    # Scheduling
    is_scheduled = models.BooleanField(default=False)
    schedule_frequency = models.CharField(max_length=20, blank=True)  # daily, weekly, monthly
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    
    # Owner
    created_by = models.ForeignKey(
        SaccoUser, 
        on_delete=models.CASCADE, 
        related_name='saved_reports'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"Saved Report - {self.name}"