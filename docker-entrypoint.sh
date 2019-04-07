#!/bin/bash

until nc -z ${POSTGRES_HOST} ${POSTGRES_PORT}; do
    echo "$(date) - waiting for postgres..."
    sleep 1
done

until nc -z ${RABBIT_HOST} ${RABBIT_PORT}; do
    echo "$(date) - waiting for rabbitmq..."
    sleep 1
done

python manage.py migrate — noinput
python manage.py collectstatic — noinput
gunicorn config.wsgi:application -w 3 -b 0.0.0.0:${PORT:-}${DJANGO_APP_PORT}
