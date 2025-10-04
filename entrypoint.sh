#!/bin/sh
python manage.py migrate --noinput
gunicorn --bind :8000 --workers 2 exizt.wsgi