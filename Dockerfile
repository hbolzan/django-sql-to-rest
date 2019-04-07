# dockerfile inspired on the following sources 
# - https://medium.com/@theparadoxer02/dockerizing-a-django-project-part-1-a0d3bebd738f
# - https://www.toptal.com/python/introduction-python-microservices-nameko

# parent image is an official Python runtime
FROM python:3.5-alpine
ENV PYTHONUNBUFFERED 1

# project root directory
RUN mkdir -p /app/sql-to-rest
COPY . /app/sql-to-rest

# setup
RUN apk update
RUN apk upgrade
RUN apk add git
RUN apk add postgresql-dev gcc python3 python3-dev musl-dev
RUN apk add libffi-dev zlib-dev
ENV LIBRARY_PATH=/lib:/usr/lib

WORKDIR /app/sql-to-rest
RUN pip3 install -U pip
RUN pip install -r requirements.txt
RUN pip install gunicorn

COPY ./docker-entrypoint.sh /
# entrypoint config moved to docker compose file
# to allow debugging when needed
# ENTRYPOINT ["/docker-entrypoint.sh"]
