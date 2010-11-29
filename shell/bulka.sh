email=bonga.bulka@artun.ee
url=https://bongapp.appspot.com/bulka

dir_log=~/Dropbox/Work/EKA/OIS/SVN/trunk/shell/log
file_csv=~/Dropbox/Work/EKA_Export/${1}.csv
file_utf8=~/Dropbox/Work/EKA_Export/${1}.utf8.csv
file_loader=~/Dropbox/Work/EKA/OIS/SVN/trunk/loaders.py
file_password=~/Dropbox/Work/EKA/OIS/SVN/trunk/shell/secure.txt
file_log=${dir_log}/log-${1}.txt

echo ${1}

cd ${dir_log}

iconv --from-code UTF-16 --to-code UTF-8 ${file_csv} > ${file_utf8}

cat ${file_password} | python2.5 /usr/local/bin/bulkloader.py --url=${url} --kind=${1} --filename="${file_utf8}" --config_file=${file_loader} --passin --email=${email} > ${file_log} 2>&1