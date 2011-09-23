#!/bin/sh

url=https://dev.bongapp.appspot.com/bulka
email=bubbledu@artun.ee

script_path=`echo "$(dirname $0)"`
data_path=`pwd`

file_config=${script_path}/upload.yaml
file_csv=${data_path}/${1}.csv

kind=${1}

appcfg.py upload_data --config_file=${file_config} --filename=${file_csv} --kind=$kind --url=${url} --email=${email}