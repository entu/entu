url=https://bongapp.appspot.com/bulka
email=bonga.bulka@artun.ee

file_config=upload.yaml
file_csv=${1}.csv
file_password=secure.txt

kind=${1}

cat ${file_password} | appcfg.py upload_data --config_file=${file_config} --filename=${file_csv} --kind=$kind --url=${url} --email=${email} --passin