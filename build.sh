#!/usr/bin/env bash
# Render runs this script every time you deploy

set -o errexit  # exit immediately if any command fails

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Run migrations on the default database
python manage.py migrate --database=default

# NOTE: mock_payslips database is read-only data — no migrations needed
# You will restore that data manually once via psql (see deployment guide)