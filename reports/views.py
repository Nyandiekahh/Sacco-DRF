# reports/views.py

from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from authentication.models import SaccoUser, ActivityLog
from members.views import AdminRequiredMixin
from .models import (
    Report,
    FinancialStatement,
    MemberStatement,
    AuditLog,
    SystemBackup,
    SavedReport
)
from .serializers import (
    ReportSerializer,
    FinancialStatementSerializer,
    MemberStatementSerializer,
    AuditLogSerializer
)


class ReportViewSet(AdminRequiredMixin, viewsets.ModelViewSet):
    """API endpoint for reports - Admin only"""
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ReportSerializer
    
    def get_queryset(self):
        queryset = Report.objects.all()
        
        # Filter by report type
        report_type = self.request.query_params.get('report_type')
        if report_type:
            queryset = queryset.filter(report_type=report_type)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(start_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(end_date__lte=date_to)
        
        # Filter by member
        member_id = self.request.query_params.get('member_id')
        if member_id:
            queryset = queryset.filter(member_id=member_id)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        report = serializer.save(generated_by=self.request.user)
        
        # Log the activity
        ActivityLog.objects.create(
            user=self.request.user,
            action='REPORT_GENERATE',
            ip_address=self.request.META.get('REMOTE_ADDR'),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            description=f"Generated {report.get_report_type_display()} report: {report.name}.",
        )


class FinancialStatementViewSet(AdminRequiredMixin, viewsets.ModelViewSet):
    """API endpoint for financial statements - Admin only"""
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FinancialStatementSerializer
    
    def get_queryset(self):
        queryset = FinancialStatement.objects.all()
        
        # Filter by statement type
        statement_type = self.request.query_params.get('statement_type')
        if statement_type:
            queryset = queryset.filter(statement_type=statement_type)
        
        # Filter by period type
        period_type = self.request.query_params.get('period_type')
        if period_type:
            queryset = queryset.filter(period_type=period_type)
        
        # Filter by year
        year = self.request.query_params.get('year')
        if year:
            queryset = queryset.filter(year=year)
        
        # Filter by month/quarter
        month = self.request.query_params.get('month')
        quarter = self.request.query_params.get('quarter')
        
        if month:
            queryset = queryset.filter(month=month)
        if quarter:
            queryset = queryset.filter(quarter=quarter)
        
        # Filter by approval status
        approved = self.request.query_params.get('approved')
        if approved is not None:
            approved = approved.lower() == 'true'
            queryset = queryset.filter(approved=approved)
        
        return queryset.order_by('-year', '-month', '-quarter')
    
    def perform_create(self, serializer):
        statement = serializer.save(generated_by=self.request.user)
        
        # Log the activity
        ActivityLog.objects.create(
            user=self.request.user,
            action='STATEMENT_GENERATE',
            ip_address=self.request.META.get('REMOTE_ADDR'),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            description=f"Generated {statement.get_statement_type_display()} for {statement.get_period_description()}.",
        )
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a financial statement"""
        
        statement = self.get_object()
        
        # Check if already approved
        if statement.approved:
            return Response({
                'status': 'info',
                'message': 'This statement is already approved'
            })
        
        # Approve the statement
        statement.approved = True
        statement.approved_by = request.user
        statement.approved_at = timezone.now()
        statement.save()
        
        # Log the activity
        ActivityLog.objects.create(
            user=request.user,
            action='STATEMENT_APPROVE',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            description=f"Approved {statement.get_statement_type_display()} for {statement.get_period_description()}.",
        )
        
        return Response({
            'status': 'success',
            'message': 'Statement approved successfully'
        })


class MemberStatementViewSet(viewsets.ModelViewSet):
    """API endpoint for member statements"""
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MemberStatementSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        # Determine queryset based on user role
        if user.role == SaccoUser.ADMIN:
            # Admins can see all statements
            queryset = MemberStatement.objects.all()
            
            # Filter by member if specified
            member_id = self.request.query_params.get('member_id')
            if member_id:
                queryset = queryset.filter(member_id=member_id)
        else:
            # Members can only see their own statements
            queryset = MemberStatement.objects.filter(member=user)
        
        # Filter by statement type
        statement_type = self.request.query_params.get('statement_type')
        if statement_type:
            queryset = queryset.filter(statement_type=statement_type)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(start_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(end_date__lte=date_to)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        # Only admins can create statements for other members
        user = self.request.user
        
        # For non-admins, ensure the statement is for themselves
        if user.role != SaccoUser.ADMIN:
            serializer.validated_data['member'] = user
        
        statement = serializer.save(generated_by=user)
        
        # Log the activity
        ActivityLog.objects.create(
            user=user,
            action='MEMBER_STATEMENT_GENERATE',
            ip_address=self.request.META.get('REMOTE_ADDR'),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            description=f"Generated {statement.get_statement_type_display()} statement for {statement.member.full_name}.",
        )


class AuditLogViewSet(AdminRequiredMixin, viewsets.ReadOnlyModelViewSet):
    """API endpoint for audit logs - Admin only"""
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AuditLogSerializer
    
    def get_queryset(self):
        queryset = AuditLog.objects.all()
        
        # Filter by action type
        action_type = self.request.query_params.get('action_type')
        if action_type:
            queryset = queryset.filter(action_type=action_type)
        
        # Filter by entity type
        entity_type = self.request.query_params.get('entity_type')
        if entity_type:
            queryset = queryset.filter(entity_type=entity_type)
        
        # Filter by user
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        
        return queryset.order_by('-created_at')


class SystemBackupViewSet(AdminRequiredMixin, viewsets.ModelViewSet):
    """API endpoint for system backups - Admin only"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return SystemBackup.objects.all().order_by('-backup_date')
    
    @action(detail=False, methods=['post'])
    def create_backup(self, request):
        """Create a system backup"""
        
        # Extract backup details
        backup_type = request.data.get('backup_type', 'MANUAL')
        name = request.data.get('name', f"Backup {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
        description = request.data.get('description', '')
        
        # Create backup record
        backup = SystemBackup.objects.create(
            backup_type=backup_type,
            name=name,
            description=description,
            status='IN_PROGRESS',
            backup_date=timezone.now(),
            initiated_by=request.user
        )
        
        # In a real system, you would initiate an actual backup process here
        # This is a simplified example
        
        # Update backup status (in a real system this would be done asynchronously)
        backup.status = 'COMPLETED'
        backup.completion_date = timezone.now()
        backup.file_size = 1024 * 1024  # 1MB placeholder
        backup.included_modules = ['authentication', 'members', 'contributions', 'loans', 'transactions']
        backup.save()
        
        # Log the activity
        ActivityLog.objects.create(
            user=request.user,
            action='SYSTEM_BACKUP',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            description=f"Created system backup: {name}.",
        )
        
        return Response({
            'status': 'success',
            'message': 'Backup created successfully',
            'backup_id': str(backup.id),
            'name': backup.name,
            'status': backup.status,
            'backup_date': backup.backup_date,
            'completion_date': backup.completion_date
        })


class SavedReportViewSet(AdminRequiredMixin, viewsets.ModelViewSet):
    """API endpoint for saved report templates - Admin only"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return SavedReport.objects.filter(created_by=self.request.user).order_by('name')
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def run_report(self, request, pk=None):
        """Run a saved report"""
        
        saved_report = self.get_object()
        
        # Extract parameters
        # In a real system, these would be validated against the saved report's expected parameters
        parameters = request.data.get('parameters', {})
        
        # Create a new report based on the saved template
        # This is simplified - in a real system you would have more complex logic
        report = Report.objects.create(
            name=f"{saved_report.name} - {timezone.now().strftime('%Y-%m-%d')}",
            report_type=saved_report.report_type,
            description=saved_report.description,
            format=saved_report.format,
            generated_by=request.user
        )
        
        # Log the activity
        ActivityLog.objects.create(
            user=request.user,
            action='REPORT_GENERATE',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            description=f"Generated report from saved template: {saved_report.name}.",
        )
        
        return Response({
            'status': 'success',
            'message': 'Report generated successfully',
            'report_id': str(report.id),
            'name': report.name
        })
    
    @action(detail=True, methods=['post'])
    def schedule(self, request, pk=None):
        """Schedule a report to run periodically"""
        
        saved_report = self.get_object()
        
        # Extract scheduling parameters
        frequency = request.data.get('frequency')
        if not frequency:
            return Response({
                'status': 'error',
                'message': 'Frequency is required for scheduling'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update the saved report
        saved_report.is_scheduled = True
        saved_report.schedule_frequency = frequency
        saved_report.next_run = self.calculate_next_run(frequency)
        saved_report.save()
        
        # Log the activity
        ActivityLog.objects.create(
            user=request.user,
            action='REPORT_SCHEDULE',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            description=f"Scheduled report to run {frequency}: {saved_report.name}.",
        )
        
        return Response({
            'status': 'success',
            'message': f'Report scheduled to run {frequency}',
            'next_run': saved_report.next_run
        })
    
    def calculate_next_run(self, frequency):
        """Calculate the next run date based on frequency"""
        
        now = timezone.now()
        
        if frequency == 'daily':
            return now.replace(hour=0, minute=0, second=0, microsecond=0) + timezone.timedelta(days=1)
        elif frequency == 'weekly':
            # Next Monday
            days_ahead = 7 - now.weekday()
            return now.replace(hour=0, minute=0, second=0, microsecond=0) + timezone.timedelta(days=days_ahead)
        elif frequency == 'monthly':
            # First day of next month
            if now.month == 12:
                return now.replace(year=now.year+1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            else:
                return now.replace(month=now.month+1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            # Default to tomorrow
            return now.replace(hour=0, minute=0, second=0, microsecond=0) + timezone.timedelta(days=1)