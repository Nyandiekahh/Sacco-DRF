# Generated by Django 5.2 on 2025-04-12 07:20

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('sacco_core', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BankAccount',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('account_name', models.CharField(max_length=100)),
                ('bank_name', models.CharField(max_length=100)),
                ('account_number', models.CharField(max_length=50)),
                ('branch', models.CharField(blank=True, max_length=100)),
                ('account_type', models.CharField(max_length=50)),
                ('is_primary', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('current_balance', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('last_reconciled', models.DateField(blank=True, null=True)),
                ('contact_person', models.CharField(blank=True, max_length=100)),
                ('contact_email', models.EmailField(blank=True, max_length=254)),
                ('contact_phone', models.CharField(blank=True, max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-is_primary', 'bank_name', 'account_name'],
            },
        ),
        migrations.CreateModel(
            name='BankTransaction',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('transaction_date', models.DateField()),
                ('value_date', models.DateField(blank=True, null=True)),
                ('transaction_type', models.CharField(choices=[('DEPOSIT', 'Deposit'), ('WITHDRAWAL', 'Withdrawal'), ('TRANSFER', 'Transfer'), ('INTEREST', 'Interest Credit'), ('FEE', 'Bank Fee/Charge'), ('OTHER', 'Other Transaction')], max_length=10)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('description', models.TextField(blank=True)),
                ('reference_number', models.CharField(blank=True, max_length=50)),
                ('is_reconciled', models.BooleanField(default=False)),
                ('reconciliation_date', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='transactions.bankaccount')),
                ('destination_account', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='incoming_transfers', to='transactions.bankaccount')),
                ('reconciled_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reconciled_transactions', to=settings.AUTH_USER_MODEL)),
                ('recorded_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='recorded_bank_transactions', to=settings.AUTH_USER_MODEL)),
                ('related_transaction', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='bank_transaction', to='sacco_core.transaction')),
            ],
            options={
                'ordering': ['-transaction_date', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='SaccoExpense',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('expense_date', models.DateField()),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('description', models.TextField()),
                ('category', models.CharField(choices=[('ADMINISTRATIVE', 'Administrative Expenses'), ('OPERATION', 'Operational Expenses'), ('RENTAL', 'Rent and Utilities'), ('BANKING', 'Banking Charges'), ('MARKETING', 'Marketing and Advertising'), ('TECHNOLOGY', 'Technology and Systems'), ('PROFESSIONAL', 'Professional Services'), ('OTHER', 'Other Expenses')], max_length=15)),
                ('payment_method', models.CharField(max_length=50)),
                ('reference_number', models.CharField(blank=True, max_length=50)),
                ('receipt_image', models.FileField(blank=True, null=True, upload_to='expense_receipts/')),
                ('transaction_cost', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('recorded_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='recorded_expenses', to=settings.AUTH_USER_MODEL)),
                ('transaction', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='expense', to='sacco_core.transaction')),
            ],
            options={
                'ordering': ['-expense_date', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='SaccoIncome',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('income_date', models.DateField()),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('description', models.TextField()),
                ('category', models.CharField(choices=[('INVESTMENT', 'Investment Returns'), ('MEMBERSHIP', 'Membership Fees'), ('PENALTIES', 'Penalties and Fines'), ('DONATIONS', 'Donations'), ('GRANTS', 'Grants'), ('OTHER', 'Other Income')], max_length=15)),
                ('payment_method', models.CharField(max_length=50)),
                ('reference_number', models.CharField(blank=True, max_length=50)),
                ('receipt_image', models.FileField(blank=True, null=True, upload_to='income_receipts/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('recorded_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='recorded_income', to=settings.AUTH_USER_MODEL)),
                ('transaction', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='income', to='sacco_core.transaction')),
            ],
            options={
                'ordering': ['-income_date', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='TransactionBatch',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('batch_type', models.CharField(choices=[('CONTRIBUTION', 'Monthly Contributions'), ('SHARE_CAPITAL', 'Share Capital Payments'), ('LOAN_DISBURSEMENT', 'Loan Disbursements'), ('LOAN_REPAYMENT', 'Loan Repayments')], max_length=20)),
                ('description', models.TextField(blank=True)),
                ('transaction_date', models.DateField()),
                ('status', models.CharField(choices=[('PENDING', 'Pending Processing'), ('PROCESSING', 'Processing'), ('COMPLETED', 'Completed'), ('FAILED', 'Failed')], default='PENDING', max_length=10)),
                ('total_amount', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('transaction_count', models.PositiveIntegerField(default=0)),
                ('batch_file', models.FileField(blank=True, null=True, upload_to='transaction_batches/')),
                ('processed_count', models.PositiveIntegerField(default=0)),
                ('failed_count', models.PositiveIntegerField(default=0)),
                ('processing_notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('processed_at', models.DateTimeField(blank=True, null=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_transaction_batches', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='BatchItem',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('reference_number', models.CharField(blank=True, max_length=50)),
                ('transaction_code', models.CharField(blank=True, max_length=50)),
                ('description', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('PROCESSED', 'Processed'), ('FAILED', 'Failed')], default='PENDING', max_length=10)),
                ('error_message', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('processed_at', models.DateTimeField(blank=True, null=True)),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='batch_items', to=settings.AUTH_USER_MODEL)),
                ('transaction', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='batch_item', to='sacco_core.transaction')),
                ('batch', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='transactions.transactionbatch')),
            ],
            options={
                'ordering': ['batch', 'created_at'],
            },
        ),
        migrations.CreateModel(
            name='TransactionLog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('previous_state', models.JSONField(blank=True, null=True)),
                ('new_state', models.JSONField(blank=True, null=True)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('transaction', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='log', to='sacco_core.transaction')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
