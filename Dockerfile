# django-sql-to-rest
# parent image contains all dependencies necessary to run a Django application

# ARG VERSION
# ARG USER
FROM hbolzan/base-for-django:latest

# project root directory
RUN mkdir -p /app/sql-to-rest
COPY . /app/sql-to-rest
WORKDIR /app/sql-to-rest
RUN pip install -r requirements.txt
COPY ./check-db.sh /
COPY ./docker-entrypoint.sh /
ENTRYPOINT ["/docker-entrypoint.sh"]
