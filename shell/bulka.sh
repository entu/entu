echo ""
echo ""
echo ""
echo ""
echo ""
echo ""
echo ""
echo "           ${1}"
echo "--------------------------------------------------------------------------------"

iconv --from-code UTF-16 --to-code UTF-8 ${2} > ${2}.utf8.csv

cat secure.txt | python2.5 /usr/local/bin/bulkloader.py --url=https://bongapp.appspot.com/bulka --kind=${1} --filename="${2}.utf8.csv" --config_file=~/Dropbox/Work/EKA/OIS/SVN/trunk/loaders.py --passin --email=bonga.bulka@artun.ee