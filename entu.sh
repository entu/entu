#!/bin/bash

# /data/entu-mysql.sh

mkdir -p /data/entu/code /data/entu/ssl /data/entu/files /data/entu/thumbs
cd /data/entu/code

git clone -q https://github.com/argoroots/Entu.git ./
git checkout -q master
git pull
printf "\n\n"

version=`date +"%y%m%d.%H%M%S"`
docker build -q -t entu:$version ./ && docker tag -f entu:$version entu:latest
printf "\n\n"

docker stop entu-maintenance
docker rm entu-maintenance
docker run -d \
    --name="entu-maintenance" \
    --restart="always" \
    --memory="512m" \
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
    --link="entu-mysql:entumysql" \
    entu:latest python /usr/src/entu/app/maintenance.py

docker inspect -f "{{ .NetworkSettings.IPAddress }}" entu-maintenance
printf "\n\n"

docker stop entu
docker rm entu
docker run -d \
    --name="entu" \
    --restart="always" \
    --memory="512m" \
    --env="PORT=80" \
    --env="DEBUG=false" \
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
    --link="entu-mysql:entumysql" \
    --volume="/data/entu/files:/entu/files" \
    --volume="/data/entu/thumbs:/entu/thumbs" \
    entu:latest python /usr/src/entu/app/main.py --logging=error

docker inspect -f "{{ .NetworkSettings.IPAddress }}" entu
printf "\n\n"

/data/nginx.sh
