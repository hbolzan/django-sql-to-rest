# django-sql-to-rest
# parent image contains all dependencies necessary to run a Django application

ARG VERSION
FROM hbolzan/base-for-django:${VERSION}

# project root directory
RUN mkdir -p /app/sql-to-rest
RUN mkdir /pg_dumps
COPY . /app/sql-to-rest
COPY ./deploy/pg_dumps/. /pg_dumps/
WORKDIR /app/sql-to-rest
RUN pip install -r requirements.txt
COPY ./docker-entrypoint.sh /
