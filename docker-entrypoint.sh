#!/bin/sh

# until nc -z ${POSTGRES_HOST} ${POSTGRES_PORT}; do
#     echo "$(date) - waiting for postgres..."
#     sleep 1
# done

# until nc -z ${RABBIT_HOST} ${RABBIT_PORT}; do
#     echo "$(date) - waiting for rabbitmq..."
#     sleep 1
# done

python3 manage.py migrate — noinput
python3 manage.py collectstatic — noinput
gunicorn django_sql_to_rest.wsgi:application -w 3 -b 0.0.0.0:${PORT:-}${DJANGO_APP_PORT}
