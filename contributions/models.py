# contributions/models.py

import uuid
from django.db import models
from django.utils import timezone
from authentication.models import SaccoUser
from sacco_core.models import Transaction, MonthlyContribution, ShareCapital, MemberShareSummary


class ContributionReminder(models.Model):
    """Reminders for monthly contributions"""
    
    REMINDER_STATUS = [
        ('SCHEDULED', 'Scheduled'),
        ('SENT', 'Sent'),
        ('FAILED', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField()  # 1-12 for January-December
    reminder_date = models.DateField()
    status = models.CharField(max_length=10, choices=REMINDER_STATUS, default='SCHEDULED')
    message = models.TextField()
    
    sent_at = models.DateTimeField(null=True, blank=True)
    scheduled_by = models.ForeignKey(
        SaccoUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='scheduled_reminders'
    )
    
    recipients_count = models.PositiveIntegerField(default=0)
    successful_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-year', '-month', '-reminder_date']
    
    def __str__(self):
        return f"Contribution Reminder - {self.year}/{self.month}"
    
    def send_reminders(self):
        """Send the contribution reminders to members"""
        
        if self.status == 'SENT':
            return False
            
        # Get all active members who haven't contributed for this month
        active_members = SaccoUser.objects.filter(
            role='MEMBER',
            is_active=True,
            is_on_hold=False
        )
        
        # Find members who haven't contributed for this month/year
        members_to_remind = []
        for member in active_members:
            # Check if member has contributed for this month
            contributed = MonthlyContribution.objects.filter(
                member=member,
                year=self.year,
                month=self.month
            ).exists()
            
            if not contributed:
                members_to_remind.append(member)
        
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.conf import settings
        
        self.recipients_count = len(members_to_remind)
        self.successful_count = 0
        self.failed_count = 0
        
        # Send emails
        for member in members_to_remind:
            try:
                # Prepare customized message
                context = {
                    'member_name': member.full_name or member.email,
                    'month': self.get_month_name(),
                    'year': self.year,
                    'message': self.message,
                }
                
                html_message = render_to_string('emails/contribution_reminder.html', context)
                
                # Send the email
                send_mail(
                    f'Contribution Reminder for {self.get_month_name()} {self.year}',
                    self.message,
                    settings.DEFAULT_FROM_EMAIL,
                    [member.email],
                    html_message=html_message,
                    fail_silently=True,
                )
                
                self.successful_count += 1
                
            except Exception as e:
                self.failed_count += 1
                # Log the error
                print(f"Failed to send reminder to {member.email}: {str(e)}")
        
        # Update status
        self.status = 'SENT'
        self.sent_at = timezone.now()
        self.save()
        
        return True
    
    def get_month_name(self):
        """Get the month name from the month number"""
        months = [
            'January', 'February', 'March', 'April', 'May', 'June', 
            'July', 'August', 'September', 'October', 'November', 'December'
        ]
        return months[self.month - 1]


class ContributionReport(models.Model):
    """Monthly contribution reports"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField(null=True, blank=True)  # For monthly reports
    quarter = models.PositiveIntegerField(null=True, blank=True)  # For quarterly reports
    report_date = models.DateField()
    
    total_members = models.PositiveIntegerField(default=0)
    contributing_members = models.PositiveIntegerField(default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # For tracking contribution growth
    previous_period_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    growth_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Report file
    report_file = models.FileField(upload_to='contribution_reports/', null=True, blank=True)
    
    generated_by = models.ForeignKey(
        SaccoUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='generated_contribution_reports'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-year', '-month', '-quarter']
        unique_together = [['year', 'month'], ['year', 'quarter']]
    
    def __str__(self):
        if self.month:
            return f"Monthly Contribution Report - {self.get_month_name()} {self.year}"
        else:
            return f"Quarterly Contribution Report - Q{self.quarter} {self.year}"
    
    def get_month_name(self):
        """Get the month name from the month number"""
        if not self.month:
            return None
            
        months = [
            'January', 'February', 'March', 'April', 'May', 'June', 
            'July', 'August', 'September', 'October', 'November', 'December'
        ]
        return months[self.month - 1]
    
    @classmethod
    def generate_monthly_report(cls, year, month, admin_user):
        """Generate a monthly contribution report"""
        
        # Check if report already exists
        existing_report = cls.objects.filter(year=year, month=month).first()
        if existing_report:
            report = existing_report
        else:
            report = cls(
                year=year,
                month=month,
                report_date=timezone.now().date(),
                generated_by=admin_user
            )
        
        # Get all contributions for the month
        contributions = MonthlyContribution.objects.filter(year=year, month=month)
        
        # Calculate totals
        total_amount = contributions.aggregate(total=models.Sum('amount'))['total'] or 0
        contributing_members = contributions.values('member').distinct().count()
        total_members = SaccoUser.objects.filter(role='MEMBER', is_active=True).count()
        
        # Calculate growth (compared to previous month)
        previous_month = month - 1
        previous_year = year
        if previous_month < 1:
            previous_month = 12
            previous_year = year - 1
            
        previous_contributions = MonthlyContribution.objects.filter(
            year=previous_year, 
            month=previous_month
        )
        previous_amount = previous_contributions.aggregate(total=models.Sum('amount'))['total'] or 0
        
        # Calculate growth percentage
        if previous_amount > 0:
            growth_percentage = ((total_amount - previous_amount) / previous_amount) * 100
        else:
            growth_percentage = 100 if total_amount > 0 else 0
        
        # Update report
        report.total_members = total_members
        report.contributing_members = contributing_members
        report.total_amount = total_amount
        report.previous_period_amount = previous_amount
        report.growth_percentage = growth_percentage
        
        report.save()
        return report


class MemberContributionSchedule(models.Model):
    """Schedule for member contributions"""
    
    SCHEDULE_FREQUENCY = [
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
        ('BIANNUAL', 'Bi-Annual'),
        ('ANNUAL', 'Annual'),
        ('CUSTOM', 'Custom'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    member = models.OneToOneField(
        SaccoUser, 
        on_delete=models.CASCADE, 
        related_name='contribution_schedule'
    )
    frequency = models.CharField(max_length=10, choices=SCHEDULE_FREQUENCY, default='MONTHLY')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    # For custom frequency
    custom_months = models.CharField(max_length=50, blank=True)  # Comma-separated month numbers
    next_due_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Member Contribution Schedule"
        verbose_name_plural = "Member Contribution Schedules"
    
    def __str__(self):
        return f"Contribution Schedule - {self.member.full_name}"
    
    def calculate_next_due_date(self):
        """Calculate the next due date based on frequency"""
        
        today = timezone.now().date()
        current_month = today.month
        current_year = today.year
        
        if self.frequency == 'MONTHLY':
            # Next month
            if current_month == 12:
                next_due_month = 1
                next_due_year = current_year + 1
            else:
                next_due_month = current_month + 1
                next_due_year = current_year
            
            self.next_due_date = timezone.datetime(
                next_due_year, next_due_month, 5  # Due on 5th of each month
            ).date()
            
        elif self.frequency == 'QUARTERLY':
            # Next quarter
            current_quarter = (current_month - 1) // 3 + 1
            if current_quarter == 4:
                next_quarter = 1
                next_due_year = current_year + 1
            else:
                next_quarter = current_quarter + 1
                next_due_year = current_year
                
            next_due_month = (next_quarter - 1) * 3 + 1
            self.next_due_date = timezone.datetime(
                next_due_year, next_due_month, 5
            ).date()
            
        elif self.frequency == 'BIANNUAL':
            # Twice a year (January and July)
            if current_month < 7:
                next_due_month = 7
                next_due_year = current_year
            else:
                next_due_month = 1
                next_due_year = current_year + 1
                
            self.next_due_date = timezone.datetime(
                next_due_year, next_due_month, 5
            ).date()
            
        elif self.frequency == 'ANNUAL':
            # Once a year (January)
            next_due_year = current_year + 1
            self.next_due_date = timezone.datetime(
                next_due_year, 1, 5
            ).date()
            
        elif self.frequency == 'CUSTOM' and self.custom_months:
            # Custom months
            months = sorted([int(m.strip()) for m in self.custom_months.split(',') if m.strip().isdigit()])
            
            # Find the next month in the list
            next_month = None
            for month in months:
                if month > current_month:
                    next_month = month
                    break
                    
            if next_month:
                # Next month is in current year
                self.next_due_date = timezone.datetime(
                    current_year, next_month, 5
                ).date()
            else:
                # Next month is in next year
                self.next_due_date = timezone.datetime(
                    current_year + 1, months[0], 5
                ).date()
                
        self.save()
        return self.next_due_date