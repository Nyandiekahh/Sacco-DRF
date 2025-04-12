# Generated by Django 5.2 on 2025-04-12 07:20

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('action_type', models.CharField(choices=[('FINANCIAL', 'Financial Transaction'), ('MEMBER', 'Member Record Change'), ('LOAN', 'Loan Action'), ('SETTING', 'System Setting Change'), ('ADMIN', 'Administrative Action'), ('SECURITY', 'Security Event')], max_length=10)),
                ('action_description', models.TextField()),
                ('entity_type', models.CharField(max_length=50)),
                ('entity_id', models.CharField(max_length=50)),
                ('changes', models.JSONField(blank=True, null=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='audit_logs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('report_type', models.CharField(choices=[('FINANCIAL_STATEMENT', 'Financial Statement'), ('MEMBER_STATEMENT', 'Member Statement'), ('LOAN_STATEMENT', 'Loan Statement'), ('CONTRIBUTION_REPORT', 'Contribution Report'), ('DIVIDEND_REPORT', 'Dividend Report'), ('AUDIT_REPORT', 'Audit Report')], max_length=20)),
                ('description', models.TextField(blank=True)),
                ('start_date', models.DateField(blank=True, null=True)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('format', models.CharField(choices=[('PDF', 'PDF Document'), ('EXCEL', 'Excel Spreadsheet'), ('CSV', 'CSV File')], default='PDF', max_length=5)),
                ('report_file', models.FileField(blank=True, null=True, upload_to='reports/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('generated_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='generated_reports', to=settings.AUTH_USER_MODEL)),
                ('member', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='member_reports', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='MemberStatement',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('statement_type', models.CharField(choices=[('CONTRIBUTIONS', 'Contributions Statement'), ('SHARES', 'Shares Statement'), ('DIVIDENDS', 'Dividends Statement'), ('LOANS', 'Loans Statement'), ('COMPREHENSIVE', 'Comprehensive Statement')], max_length=20)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('statement_data', models.JSONField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('generated_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='generated_member_statements', to=settings.AUTH_USER_MODEL)),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='statements', to=settings.AUTH_USER_MODEL)),
                ('report', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='member_statement', to='reports.report')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='SavedReport',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('report_type', models.CharField(max_length=50)),
                ('format', models.CharField(max_length=10)),
                ('parameters', models.JSONField(default=dict)),
                ('is_scheduled', models.BooleanField(default=False)),
                ('schedule_frequency', models.CharField(blank=True, max_length=20)),
                ('last_run', models.DateTimeField(blank=True, null=True)),
                ('next_run', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='saved_reports', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='SystemBackup',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('backup_type', models.CharField(choices=[('SCHEDULED', 'Scheduled Backup'), ('MANUAL', 'Manual Backup'), ('PRE_UPDATE', 'Pre-Update Backup')], max_length=10)),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('IN_PROGRESS', 'In Progress'), ('COMPLETED', 'Completed'), ('FAILED', 'Failed')], default='PENDING', max_length=12)),
                ('backup_file', models.FileField(blank=True, null=True, upload_to='system_backups/')),
                ('file_size', models.PositiveBigIntegerField(default=0)),
                ('included_modules', models.JSONField(default=list)),
                ('backup_date', models.DateTimeField()),
                ('completion_date', models.DateTimeField(blank=True, null=True)),
                ('error_message', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('initiated_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='initiated_backups', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-backup_date'],
            },
        ),
        migrations.CreateModel(
            name='FinancialStatement',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('statement_type', models.CharField(choices=[('BALANCE_SHEET', 'Balance Sheet'), ('INCOME_STATEMENT', 'Income Statement'), ('CASH_FLOW', 'Cash Flow Statement'), ('EQUITY_CHANGES', 'Statement of Changes in Equity')], max_length=20)),
                ('period_type', models.CharField(choices=[('MONTHLY', 'Monthly'), ('QUARTERLY', 'Quarterly'), ('SEMI_ANNUAL', 'Semi-Annual'), ('ANNUAL', 'Annual'), ('CUSTOM', 'Custom Period')], max_length=12)),
                ('year', models.PositiveIntegerField()),
                ('month', models.PositiveIntegerField(blank=True, null=True)),
                ('quarter', models.PositiveIntegerField(blank=True, null=True)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('statement_data', models.JSONField(blank=True, null=True)),
                ('approved', models.BooleanField(default=False)),
                ('approved_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_statements', to=settings.AUTH_USER_MODEL)),
                ('generated_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='generated_statements', to=settings.AUTH_USER_MODEL)),
                ('report', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='financial_statement', to='reports.report')),
            ],
            options={
                'ordering': ['-year', '-month', '-quarter', '-created_at'],
                'unique_together': {('statement_type', 'year', 'month'), ('statement_type', 'year', 'quarter')},
            },
        ),
    ]
