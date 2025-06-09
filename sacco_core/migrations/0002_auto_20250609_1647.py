from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('sacco_core', '0001_initial'),  # Replace with your latest migration
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='monthlycontribution',
            unique_together=set(),  # Remove the unique constraint
        ),
    ]