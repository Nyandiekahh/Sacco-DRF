# Create this migration file: authentication/migrations/0002_fix_membership_number.py

from django.db import migrations, models

def fix_admin_membership_numbers(apps, schema_editor):
    """Set admin users' membership_number to None"""
    SaccoUser = apps.get_model('authentication', 'SaccoUser')
    
    # Set all admin users' membership_number to None
    SaccoUser.objects.filter(role='ADMIN').update(membership_number=None)

def reverse_fix_admin_membership_numbers(apps, schema_editor):
    """Reverse operation - not needed"""
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0001_initial'),
    ]

    operations = [
        # Allow null values for membership_number
        migrations.AlterField(
            model_name='saccouser',
            name='membership_number',
            field=models.CharField(blank=True, max_length=20, null=True, unique=True),
        ),
        
        # Run data migration to fix existing admin users
        migrations.RunPython(
            fix_admin_membership_numbers,
            reverse_fix_admin_membership_numbers
        ),
    ]