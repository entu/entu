#!/bin/bash

mkdir -p /data/entu/code /data/entu/ssl /data/entu/files /data/entu/thumbs
cd /data/entu/code

git clone https://github.com/argoroots/Entu.git ./
git checkout master
git pull

version=`date +"%y%m%d.%H%M%S"`

docker build -q -t entu:$version ./ && docker tag -f entu:$version entu:latest
docker stop entu
docker rm entu
docker run -d \
    --name="entu" \
    --restart="always" \
    --memory="512m" \
    --env="PORT=80" \
    --env="MYSQL_HOST=" \
    --env="MYSQL_DATABASE=" \
    --env="MYSQL_USER=" \
    --env="MYSQL_PASSWORD=" \
    --env="CUSTOMERGROUP=" \
    --env="NEW_RELIC_APP_NAME=entu" \
    --env="NEW_RELIC_LICENSE_KEY=" \
    --env="NEW_RELIC_LOG=stdout" \
    --env="NEW_RELIC_LOG_LEVEL=error" \
    --env="NEW_RELIC_NO_CONFIG_FILE=true" \
    --env="SENTRY_DSN=" \
    entu:latest

/data/nginx.sh

docker stop entu-maintenance
docker rm entu-maintenance
docker run -d \
    --name="entu-maintenance" \
    --restart="always" \
    --memory="512m" \
    --env="MYSQL_HOST=" \
    --env="MYSQL_DATABASE=" \
    --env="MYSQL_USER=" \
    --env="MYSQL_PASSWORD=" \
    --env="NEW_RELIC_APP_NAME=entu-maintenance" \
    --env="NEW_RELIC_LICENSE_KEY=" \
    --env="NEW_RELIC_LOG=stdout" \
    --env="NEW_RELIC_LOG_LEVEL=error" \
    --env="NEW_RELIC_NO_CONFIG_FILE=true" \
    --env="CUSTOMERGROUP=" \
    entu:latest newrelic-admin run-program /usr/src/entu/app/maintenance.py
