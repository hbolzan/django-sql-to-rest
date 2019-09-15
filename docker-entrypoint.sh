#!/bin/sh

# VERSION=$1
# echo "# Version: ${VERSION}" > version.txt

until nc -z ${POSTGRES_HOST} ${POSTGRES_PORT}; do
    echo "$(date) - waiting for postgres..."
    sleep 1
done

/check-db.sh sql_to_rest /app/sql-to-rest/deploy/pg_dumps/sql_to_rest.dump
/check-db.sh minipcp /app/sql-to-rest/deploy/pg_dumps/minipcp_zero.dump

until nc -z ${RABBIT_HOST} ${RABBIT_PORT}; do
    echo "$(date) - waiting for rabbitmq..."
    sleep 1
done

python3 manage.py migrate --noinput
python3 manage.py collectstatic --noinput
gunicorn --reload django_sql_to_rest.wsgi:application -w 3 -b 0.0.0.0:${PORT:-}${DJANGO_APP_PORT}
