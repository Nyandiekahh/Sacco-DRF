#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Make migrations for authentication app first with automated input
echo -e "1\nTEMP000" | python manage.py makemigrations authentication

# Make migrations for all other apps
python manage.py makemigrations

# Run migrations with syncdb
python manage.py migrate --run-syncdb

# Collect static files
python manage.py collectstatic --noinput

# Create superuser if it doesn't exist
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser(email='admin@sacco.com', password='TempPassword123!') if not User.objects.filter(email='admin@sacco.com').exists() else print('Superuser already exists')" | python manage.py shell