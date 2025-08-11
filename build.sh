#!/usr/bin/env bash
set -o errexit

# 1. Install dependencies
pip install -r requirements/production.txt

# 2. Run database migrations
python manage.py migrate --settings=config.settings.production

# 3. Collect static files
python manage.py collectstatic --noinput --settings=config.settings.production
