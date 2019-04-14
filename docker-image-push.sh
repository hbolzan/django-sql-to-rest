#!/bin/bash

VERSION=$1
docker push "${DOCKER_USER_ID}/django-sql-to-rest:${VERSION}"
docker push "${DOCKER_USER_ID}/django-sql-to-rest:latest"
