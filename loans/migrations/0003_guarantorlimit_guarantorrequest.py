# Generated by Django 5.2 on 2025-04-19 05:24

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loans', '0002_paymentmethod_loandisbursement'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='GuarantorLimit',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('total_guaranteed_amount', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('active_guarantees_count', models.PositiveIntegerField(default=0)),
                ('maximum_guarantee_amount', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('available_guarantee_amount', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('member', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='guarantor_limit', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='GuarantorRequest',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('guarantee_amount', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('guarantee_percentage', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('ACCEPTED', 'Accepted'), ('REJECTED', 'Rejected'), ('CANCELLED', 'Cancelled')], default='PENDING', max_length=10)),
                ('message', models.TextField(blank=True)),
                ('response_message', models.TextField(blank=True)),
                ('requested_at', models.DateTimeField(auto_now_add=True)),
                ('responded_at', models.DateTimeField(blank=True, null=True)),
                ('guarantor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='guarantor_requests_received', to=settings.AUTH_USER_MODEL)),
                ('loan_application', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='guarantor_requests', to='loans.loanapplication')),
                ('requester', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='guarantor_requests_sent', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-requested_at'],
            },
        ),
    ]
