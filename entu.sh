#!/bin/bash

mkdir -p /data/entu/code /data/entu/ssl /data/entu/files /data/entu/thumbs
cd /data/entu/code

git clone https://github.com/argoroots/Entu.git ./
git checkout master
git pull

version=`date +"%y%m%d.%H%M%S"`

docker build -q -t entu:$version ./ && docker tag -f entu:$version entu:latest
docker kill entu
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
    entu:latest

/data/nginx.sh

docker kill entu-maintenance
docker rm entu-maintenance
docker run -d \
    --name="entu-maintenance" \
    --restart="always" \
    --memory="512m" \
    --env="MYSQL_HOST=" \
    --env="MYSQL_DATABASE=" \
    --env="MYSQL_USER=" \
    --env="MYSQL_PASSWORD=" \
    --env="CUSTOMERGROUP=" \
    entu:latest /usr/src/entu/app/maintenance.py
