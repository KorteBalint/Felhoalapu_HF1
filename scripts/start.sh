#!/bin/sh
set -eu

python manage.py migrate --noinput

exec gunicorn \
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers "${GUNICORN_WORKERS:-2}" \
  config.wsgi:application
