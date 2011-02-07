url=https://bongapp.appspot.com/bulka
email=bonga.bulka@artun.ee

dir_log=~/Dropbox/Work/EKA/OIS/SVN/trunk/shell/log
file_config=~/Dropbox/Work/EKA/OIS/SVN/trunk/shell/upload.yaml
file_password=~/Dropbox/Work/EKA/OIS/SVN/trunk/shell/secure.txt
file_log=${dir_log}/log-${1}.txt
file_csv=~/Dropbox/Work/EKA/zExport/${1}.csv

kind=${1}

echo ${1}
cd ${dir_log}
cat ${file_password} | appcfg.py upload_data --config_file=${file_config} --filename=${file_csv} --kind=$kind --url=${url} --email=${email} --passin > ${file_log} 2>&1