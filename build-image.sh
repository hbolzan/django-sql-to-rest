#!/bin/bash

VERSION=$1
docker build --build-arg VERSION=$VERSION -t "hbolzan/django-sql-to-rest:${VERSION}" .
