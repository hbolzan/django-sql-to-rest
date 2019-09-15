#!/bin/bash

VERSION=$1
echo "# Version: ${VERSION}" > version.txt

docker build --build-arg VERSION=$VERSION --build-arg USER=$DOCKER_USER_ID \
       -t "${DOCKER_USER_ID}/django-sql-to-rest:latest" \
       -t "${DOCKER_USER_ID}/django-sql-to-rest:${VERSION}" .

docker push "${DOCKER_USER_ID}/django-sql-to-rest:${VERSION}"
docker push "${DOCKER_USER_ID}/django-sql-to-rest:latest"
