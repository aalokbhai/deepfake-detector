#!/usr/bin/env bash
# Runs on every deploy: applies DB migrations and collects static files.
set -o errexit
cd "$(dirname "$0")/deepfake_site"
python manage.py migrate --noinput
python manage.py collectstatic --noinput
