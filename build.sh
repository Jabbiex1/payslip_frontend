#!/usr/bin/env bash
set -o errexit

echo "DATABASE_URL is: $DATABASE_URL"
echo "DJANGO_SETTINGS_MODULE is: $DJANGO_SETTINGS_MODULE"

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate