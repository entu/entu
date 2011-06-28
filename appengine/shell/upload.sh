#!/bin/sh

url=https://bongapp.appspot.com/bulka
email=bonga.bulka@artun.ee

script_path=`echo "$(dirname $0)"`
data_path=`pwd`

dir_log=${script_path}/log
file_config=${script_path}/upload.yaml
file_password=${script_path}/secure.txt
file_log=${dir_log}/log-${1}.txt
file_csv=${data_path}/${1}.csv

kind=${1}

echo ${file_csv}
cd ${dir_log}
cat ${file_password} | appcfg.py upload_data --config_file=${file_config} --filename=${file_csv} --kind=$kind --url=${url} --email=${email} --passin > ${file_log} 2>&1