#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate

# Create superuser if it doesn't exist
python manage.py shell << EOF
from authentication.models import SaccoUser
import os

if not SaccoUser.objects.filter(email='admin@sacco.com').exists():
    SaccoUser.objects.create_superuser(
        email='admin@sacco.com',
        password=os.environ.get('ADMIN_PASSWORD', 'admin123456'),
        full_name='System Administrator',
        role='ADMIN'
    )
    print("Superuser created successfully")
else:
    print("Superuser already exists")
EOF