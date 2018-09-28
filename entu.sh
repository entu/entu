#!/bin/bash

mkdir -p /data/entu/code /data/entu/files /data/entu/thumbs /data/entu/uploads
cd /data/entu/code

git clone -q https://github.com/entu/entu.git ./
git checkout -q master
git pull

printf "\n\n"
docker build --quiet --pull --tag=entu ./

printf "\n\n"
docker stop entu
docker rm entu
docker run -d \
    --net="entu" \
    --name="entu" \
    --restart="always" \
    --env="PORT=80" \
    --env="DEBUG=false" \
    --env="AUTH_URL=" \
    --env="MONGODB=" \
    --env="UPLOADS_PATH=/entu/uploads/" \
    --env="MYSQL_HOST=" \
    --env="MYSQL_PORT=3306" \
    --env="MYSQL_DATABASE=" \
    --env="MYSQL_USER=" \
    --env="MYSQL_PASSWORD=" \
    --env="MYSQL_SSL_CA=" \
    --env="FILES_PATH=/entu" \
    --env="CUSTOMERGROUP=" \
    --env="INTERCOM_KEY=" \
    --volume="/data/entu/files:/entu/files" \
    --volume="/data/entu/thumbs:/entu/thumbs" \
    --volume="/data/entu/uploads:/entu/uploads" \
    entu:latest python -u /usr/src/entu/app/main.py --logging=error
