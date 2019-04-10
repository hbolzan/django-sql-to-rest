# parent image contains all needed dependencies for Django
FROM hbolzan/base-for-django

# project root directory
RUN mkdir -p /app/sql-to-rest
COPY . /app/sql-to-rest
WORKDIR /app/sql-to-rest
RUN pip install -r requirements.txt
COPY ./docker-entrypoint.sh /
