# authentication/management/commands/setup_initial_data.py

from django.core.management.base import BaseCommand
from django.conf import settings
from sacco_core.models import SaccoSettings

class Command(BaseCommand):
    help = 'Set up initial SACCO data from environment variables'

    def handle(self, *args, **options):
        self.stdout.write(self.style.HTTP_INFO('🚀 Setting up initial SACCO data...'))
        
        try:
            # Get settings from environment or use defaults
            sacco_config = getattr(settings, 'SACCO_SETTINGS', {
                'NAME': 'KMS SACCO',
                'SHARE_VALUE': 5000.00,
                'MIN_CONTRIBUTION': 1000.00,
                'LOAN_INTEREST_RATE': 12.00,
                'MAX_LOAN_MULTIPLIER': 3.0,
                'PHONE': '+254700000000',
                'EMAIL': 'info@kmssacco.co.ke',
                'POSTAL_ADDRESS': 'P.O. Box 12345, Nairobi',
                'PHYSICAL_ADDRESS': 'Nairobi, Kenya',
            })
            
            # Create or update SACCO settings
            self.stdout.write('📋 Setting up SACCO settings...')
            sacco_settings = SaccoSettings.get_settings()
            sacco_settings.name = sacco_config['NAME']
            sacco_settings.share_value = sacco_config['SHARE_VALUE']
            sacco_settings.minimum_monthly_contribution = sacco_config['MIN_CONTRIBUTION']
            sacco_settings.loan_interest_rate = sacco_config['LOAN_INTEREST_RATE']
            sacco_settings.maximum_loan_multiplier = sacco_config['MAX_LOAN_MULTIPLIER']
            sacco_settings.phone_number = sacco_config['PHONE']
            sacco_settings.email = sacco_config['EMAIL']
            sacco_settings.postal_address = sacco_config['POSTAL_ADDRESS']
            sacco_settings.physical_address = sacco_config['PHYSICAL_ADDRESS']
            sacco_settings.save()
            self.stdout.write(self.style.SUCCESS('✅ SACCO settings configured'))
            
            # Create initial financial summary
            from sacco_core.models import FinancialSummary
            self.stdout.write('💰 Creating initial financial summary...')
            FinancialSummary.generate_current_summary()
            self.stdout.write(self.style.SUCCESS('✅ Financial summary created'))
            
            self.stdout.write(self.style.SUCCESS('\n🎉 Initial SACCO data setup completed successfully!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error during setup: {str(e)}'))
            raise e