#!/bin/bash

mkdir -p /data/entu/code /data/entu/ssl /data/entu/files /data/entu/thumbs
cd /data/entu/code

git clone -q https://github.com/argoroots/Entu.git ./
git checkout -q master
git pull

printf "\n\n"
version=`date +"%y%m%d.%H%M%S"`
docker build --quiet --pull --tag=entu:$version ./ && docker tag entu:$version entu:latest

printf "\n\n"
docker stop entu
docker rm entu
docker run -d \
    --net="entu" \
    --name="entu" \
    --restart="always" \
    --cpu-shares=1024 \
    --env="VERSION=$version" \
    --env="PORT=80" \
    --env="DEBUG=false" \
    --env="AUTH_URL=https://auth.entu.ee" \
    --env="MONGODB=" \
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
    --env="INTERCOM_KEY=" \
    --volume="/data/entu/files:/entu/files" \
    --volume="/data/entu/thumbs:/entu/thumbs" \
    entu:latest python -u /usr/src/entu/app/main.py --logging=error

printf "\n\n"
docker exec nginx /etc/init.d/nginx reload

printf "\n\n"
docker stop entu_maintenance
docker rm entu_maintenance
docker run -d \
    --net="entu" \
    --name="entu_maintenance" \
    --restart="always" \
    --cpu-shares=512 \
    --memory="1g" \
    --env="VERSION=$version" \
    --env="MYSQL_HOST=" \
    --env="MYSQL_DATABASE=" \
    --env="MYSQL_USER=" \
    --env="MYSQL_PASSWORD=" \
    --env="CUSTOMERGROUP=" \
    --env="VERBOSE=0" \
    --env="NEW_RELIC_APP_NAME=entu-maintenance" \
    --env="NEW_RELIC_LICENSE_KEY=" \
    --env="NEW_RELIC_LOG=stdout" \
    --env="NEW_RELIC_LOG_LEVEL=error" \
    --env="NEW_RELIC_NO_CONFIG_FILE=true" \
    entu:latest python -u /usr/src/entu/app/maintenance.py

printf "\n\n"
docker exec entu pip list --outdated
