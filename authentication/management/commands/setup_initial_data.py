from django.core.management.base import BaseCommand
from django.conf import settings
from sacco_core.models import SaccoSettings
from settings_api.models import SaccoSettings as ApiSettings

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
            
            # Create core settings
            self.stdout.write('📋 Setting up core SACCO settings...')
            core_settings = SaccoSettings.get_settings()
            core_settings.name = sacco_config['NAME']
            core_settings.share_value = sacco_config['SHARE_VALUE']
            core_settings.minimum_monthly_contribution = sacco_config['MIN_CONTRIBUTION']
            core_settings.loan_interest_rate = sacco_config['LOAN_INTEREST_RATE']
            core_settings.maximum_loan_multiplier = sacco_config['MAX_LOAN_MULTIPLIER']
            core_settings.phone_number = sacco_config['PHONE']
            core_settings.email = sacco_config['EMAIL']
            core_settings.postal_address = sacco_config['POSTAL_ADDRESS']
            core_settings.physical_address = sacco_config['PHYSICAL_ADDRESS']
            core_settings.save()
            self.stdout.write(self.style.SUCCESS('✅ Core settings configured'))
            
            # Create API settings
            self.stdout.write('⚙️  Setting up API settings...')
            api_settings = ApiSettings.get_settings()
            api_settings.sacco_name = sacco_config['NAME']
            api_settings.share_value = sacco_config['SHARE_VALUE']
            api_settings.minimum_monthly_contribution = sacco_config['MIN_CONTRIBUTION']
            api_settings.loan_interest_rate = sacco_config['LOAN_INTEREST_RATE']
            api_settings.maximum_loan_multiplier = sacco_config['MAX_LOAN_MULTIPLIER']
            api_settings.phone_number = sacco_config['PHONE']
            api_settings.email = sacco_config['EMAIL']
            api_settings.postal_address = sacco_config['POSTAL_ADDRESS']
            api_settings.physical_address = sacco_config['PHYSICAL_ADDRESS']
            api_settings.save()
            self.stdout.write(self.style.SUCCESS('✅ API settings configured'))
            
            self.stdout.write(self.style.SUCCESS('\n🎉 Initial SACCO data setup completed successfully!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error during setup: {str(e)}'))
            raise e