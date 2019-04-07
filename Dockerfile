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
RUN apk add --update python3 python3-dev
RUN apk add libffi-dev zlib-dev
RUN apk add netcat
ENV LIBRARY_PATH=/lib:/usr/lib

WORKDIR /app/sql-to-rest
RUN pip3 install -r requirements.txt
RUN pip3 install gunicorn

COPY ./docker-entrypoint.sh /
ENTRYPOINT ["/docker-entrypoint.sh"]
