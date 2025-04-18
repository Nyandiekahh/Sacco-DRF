# Generated by Django 5.2 on 2025-04-14 16:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('settings_api', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='saccosettings',
            name='dividend_calculation_method',
            field=models.CharField(choices=[('SHARES', 'Based on Shares'), ('DEPOSITS', 'Based on Deposits'), ('BOTH', 'Based on Both')], default='BOTH', help_text='Method for calculating dividends', max_length=20),
        ),
        migrations.AddField(
            model_name='saccosettings',
            name='enable_email_notifications',
            field=models.BooleanField(default=True, help_text='Enable email notifications for transactions'),
        ),
        migrations.AddField(
            model_name='saccosettings',
            name='enable_sms_notifications',
            field=models.BooleanField(default=True, help_text='Enable SMS notifications for transactions'),
        ),
        migrations.AddField(
            model_name='saccosettings',
            name='maximum_loan_term_months',
            field=models.PositiveIntegerField(default=36, help_text='Maximum loan repayment period in months'),
        ),
        migrations.AddField(
            model_name='saccosettings',
            name='minimum_guarantors',
            field=models.PositiveIntegerField(default=2, help_text='Minimum number of guarantors required for a loan'),
        ),
        migrations.AddField(
            model_name='saccosettings',
            name='minimum_membership_period_months',
            field=models.PositiveIntegerField(default=3, help_text='Minimum period of membership before loan eligibility (months)'),
        ),
        migrations.AddField(
            model_name='saccosettings',
            name='sacco_name',
            field=models.CharField(default='Sample SACCO', help_text='Official SACCO name', max_length=100),
        ),
    ]
