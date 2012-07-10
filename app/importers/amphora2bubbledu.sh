#! /bin/bash

# This script extracts folders and files from directory structure
# exported from Amphora [http://www.amphora.ee] and generates sql
# for importing meta-information into mysql database.
#
# Also it generates reference document for usein file uploader.
#
# Mihkel Putrinš
# 31.05.2012

if [ ! $1 ]; then
    echo Directory should be passed as an argument
    exit 1
fi
if [ ! -d $1 ]; then
    echo '"'"$1"'"' has to be a directory
    exit 1
fi

cd "${1}/.."

# Remove trailing slash from path
DOC_PATH=`echo ${1%/}`

FOLDERS_LIST=~/folders.lst
FOLDERS_MYSQL=~/folders.sql
FILE_COPY=~/copy_files.sh
FILES_SQL=~/files.sql

BD_FOLDER='agpzfmJ1YmJsZWR1cg8LEgZCdWJibGUY2qTUAgw'
PD_FOLDER_IS_PUBLIC='agpzfmJ1YmJsZWR1cg8LEgZCdWJibGUY2qTUAgw_agpzfmJ1YmJsZWR1cg8LEgZCdWJibGUYg53UAgw'
PD_FOLDER_NAME='agpzfmJ1YmJsZWR1cg8LEgZCdWJibGUY2qTUAgw_agpzfmJ1YmJsZWR1cg8LEgZCdWJibGUYmO7TAgw'
BD_DOCUMENT='agpzfmJ1YmJsZWR1cg8LEgZCdWJibGUYxNXRAgw'
PD_FILE='agpzfmJ1YmJsZWR1cg8LEgZCdWJibGUYxNXRAgw_agpzfmJ1YmJsZWR1cg8LEgZCdWJibGUYsbTUAgw'
PD_DOC_CREATED='agpzfmJ1YmJsZWR1cg8LEgZCdWJibGUYxNXRAgw_agpzfmJ1YmJsZWR1cg8LEgZCdWJibGUYk7vSAgw'

ROOT_B_KEY="amphora_ROOT_"

ARGO_PERSON_KEY='agpzfmJ1YmJsZWR1cg8LEgZCdWJibGUYy_rLAgw'
MIHKEL_PERSON_KEY='agpzfmJ1YmJsZWR1cg8LEgZCdWJibGUY1IfMAgw'


echo "You might want to add rights after import with:
------------------------------
DELETE FROM `relationship`
WHERE `related_entity_id` IN (SELECT id FROM entity WHERE gae_key IN ('${ARGO_PERSON_KEY}','${MIHKEL_PERSON_KEY}'));
INSERT IGNORE INTO relationship (entity_id, related_entity_id, `type`)
SELECT id AS entity_id, (SELECT id FROM entity WHERE gae_key = '${ARGO_PERSON_KEY}') AS related_entity_id, 'viewer' AS `type` FROM entity;
INSERT IGNORE INTO relationship (entity_id, related_entity_id, `type`)
SELECT id AS entity_id, (SELECT id FROM entity WHERE gae_key = '${MIHKEL_PERSON_KEY}') AS related_entity_id, 'viewer' AS `type` FROM entity;
------------------------------
"

# Create folders list
echo === Listing folders from $DOC_PATH to $FOLDERS_LIST ===

if [ -f $FOLDERS_LIST ]; then
    echo "Already listed"
else
    find "${DOC_PATH}" -type d | uniq -u |
        while read fn
        do
            # echo -n $fn
            if find "$fn"/* -type d -maxdepth 0 | read; then
                echo "$fn"
            fi
        done >> $FOLDERS_LIST
    echo "Listed"
fi


# Parse folders to sql
echo === Parsing folders to $FOLDERS_MYSQL ===

if [ -f $FOLDERS_MYSQL ]; then
    echo "Already parsed"
else
    # Create root folder
    B_KEY=`echo ${ROOT_B_KEY} | md5 | cut -d" " -f1`
    echo "-- Root element" > $FOLDERS_MYSQL
    echo "INSERT INTO entity SET entity_definition_id = (SELECT id FROM entity_definition WHERE gae_key = '${BD_FOLDER}'), gae_key = '${ROOT_B_KEY}${B_KEY}' ON DUPLICATE KEY UPDATE entity_definition_id = (SELECT id FROM entity_definition WHERE gae_key = '${BD_FOLDER}'), gae_key = '${ROOT_B_KEY}${B_KEY}';" >> $FOLDERS_MYSQL

    echo "DELETE FROM property WHERE entity_id = (SELECT id FROM entity WHERE gae_key = '${ROOT_B_KEY}${B_KEY}');" >> $FOLDERS_MYSQL
    echo "INSERT INTO property SET property_definition_id = (SELECT id FROM property_definition WHERE gae_key = '${PD_FOLDER_NAME}'), entity_id = (SELECT id FROM entity WHERE gae_key = '${ROOT_B_KEY}${B_KEY}'), language = 'estonian', value_string = 'Amphora dokumendid';" >> $FOLDERS_MYSQL
    echo "INSERT INTO property SET property_definition_id = (SELECT id FROM property_definition WHERE gae_key = '${PD_FOLDER_NAME}'), entity_id = (SELECT id FROM entity WHERE gae_key = '${ROOT_B_KEY}${B_KEY}'), language = 'english', value_string = 'Amphora Root';" >> $FOLDERS_MYSQL

    # Create Amphora folders
    while read fn
    do
        echo "-- ${fn}"
        B_KEY=`echo ${fn} | md5 | cut -d" " -f1`
        PARENT_B_KEY=`echo $fn | rev | cut -d'/' -f2- | rev | md5 | cut -d" " -f1`

        fn=`echo ${fn} | sed -e "s/'/\\\'/g"`
        echo "INSERT INTO entity SET entity_definition_id = (SELECT id FROM entity_definition WHERE gae_key = '${BD_FOLDER}'), gae_key = '${ROOT_B_KEY}${B_KEY}' ON DUPLICATE KEY UPDATE entity_definition_id = (SELECT id FROM entity_definition WHERE gae_key = '${BD_FOLDER}'), gae_key = '${ROOT_B_KEY}${B_KEY}';"

        echo "DELETE FROM relationship WHERE related_entity_id = (SELECT id FROM entity WHERE gae_key = '${ROOT_B_KEY}${B_KEY}');"
        echo "INSERT INTO relationship SET entity_id = (SELECT id FROM entity WHERE gae_key = '${ROOT_B_KEY}${PARENT_B_KEY}'), related_entity_id = (SELECT id FROM entity WHERE gae_key = '${ROOT_B_KEY}${B_KEY}'), type='child', gae_key='${ROOT_B_KEY}${PARENT_B_KEY}_${B_KEY}';"

        echo "DELETE FROM property WHERE entity_id = (SELECT id FROM entity WHERE gae_key = '${ROOT_B_KEY}${B_KEY}');"
        echo "INSERT INTO property SET property_definition_id = (SELECT id FROM property_definition WHERE gae_key = '${PD_FOLDER_NAME}'), entity_id = (SELECT id FROM entity WHERE gae_key = '${ROOT_B_KEY}${B_KEY}'), language = 'estonian', value_string = '${fn}';"
        echo "INSERT INTO property SET property_definition_id = (SELECT id FROM property_definition WHERE gae_key = '${PD_FOLDER_NAME}'), entity_id = (SELECT id FROM entity WHERE gae_key = '${ROOT_B_KEY}${B_KEY}'), language = 'english', value_string = '${fn}';"

    done < $FOLDERS_LIST >> $FOLDERS_MYSQL
    echo "Parsed"
fi


echo === Parsing files ===

if [ -f $FILES_SQL ]; then
    echo "Already parsed"
else
    find "${DOC_PATH}" -type f -name '*.xml' |
        while read fn
        do
            echo "-- ${fn}"
            dname="`dirname "${fn}" | rev | cut -d'/' -f2- | rev`"

            file_orig_name=`grep file_orig_name "${fn}" | sed -e 's/<[a-zA-Z\/][^>]*>//g' | sed 's/^ *//;s/ *$//' | tr -d '[ \r]' | sed -e "s/'/\\\'/g"`
            file_orig_guid=`grep file_orig_guid "${fn}" | sed -e 's/<[a-zA-Z\/][^>]*>//g' | sed 's/^ *//;s/ *$//' | tr -d '[ \r]'`
            document_date=`grep document_date "${fn}" | sed -e 's/<[a-zA-Z\/][^>]*>//g' | sed 's/^ *//;s/ *$//' | tr -d '[ \r]'`
            author=`grep author "${fn}" | sed -e 's/<[a-zA-Z\/][^>]*>//g' | sed 's/^ *//;s/ *$//' | tr -d '[ \r]' | sed -e "s/'/\\\'/g"`

            FILE_KEY=`echo ${file_orig_guid} | md5 | cut -d" " -f1`
            DIRECTORY_KEY=`echo ${dname} | md5 | cut -d" " -f1`

            # Create document bubble
            echo "INSERT INTO entity SET
                entity_definition_id = (SELECT id FROM entity_definition WHERE gae_key = '${BD_DOCUMENT}'),
                gae_key = '${ROOT_B_KEY}${FILE_KEY}',
                created = STR_TO_DATE('${document_date}','%d.%m.%Y %H:%i:%s'),
                created_by = '$author'
                ON DUPLICATE KEY UPDATE entity_definition_id = (SELECT id FROM entity_definition WHERE gae_key = '${BD_DOCUMENT}'), gae_key = '${ROOT_B_KEY}${FILE_KEY}';"
            echo "DELETE FROM relationship WHERE related_entity_id = (SELECT id FROM entity WHERE gae_key = '${ROOT_B_KEY}${FILE_KEY}');"
            echo "INSERT INTO relationship SET
                entity_id = (SELECT id FROM entity WHERE gae_key = '${ROOT_B_KEY}${DIRECTORY_KEY}'),
                related_entity_id = (SELECT id FROM entity WHERE gae_key = '${ROOT_B_KEY}${FILE_KEY}'),
                type='child',
                gae_key='${ROOT_B_KEY}${DIRECTORY_KEY}_${FILE_KEY}';"

            # Insert file metadata
            echo "INSERT IGNORE INTO file SET gae_key='${ROOT_B_KEY}${FILE_KEY}', filename='${file_orig_name}';"

            echo "DELETE FROM property WHERE entity_id = (SELECT id FROM entity WHERE gae_key = '${ROOT_B_KEY}${FILE_KEY}');"
            # Add file property to document
            echo "INSERT INTO property SET
                property_definition_id = (SELECT id FROM property_definition WHERE gae_key = '${PD_FILE}'),
                entity_id = (SELECT id FROM entity WHERE gae_key = '${ROOT_B_KEY}${FILE_KEY}'),
                value_file = (SELECT id FROM file WHERE gae_key = '${ROOT_B_KEY}${FILE_KEY}');"
            # Add document_created_on property to document
            echo "INSERT INTO property SET
                property_definition_id = (SELECT id FROM property_definition WHERE gae_key = '${PD_DOC_CREATED}'),
                entity_id = (SELECT id FROM entity WHERE gae_key = '${ROOT_B_KEY}${FILE_KEY}'),
                value_datetime = STR_TO_DATE('${document_date}','%d.%m.%Y %H:%i:%s');"

        done >> $FILES_SQL
    echo "Parsed"
fi


echo === Listing files ===

if [ -f $FILE_COPY ]; then
    echo "Already listed"
else
    find "${DOC_PATH}" -type f -name '*.xml' |
        while read fn
        do
            dname="`dirname "${fn}"`"
            fname=`grep file_orig_guid "${fn}" | sed -e 's/<[a-zA-Z\/][^>]*>//g' | sed 's/^ *//;s/ *$//' | tr -d '[ \r]'`
            echo "cp \"${dname}/${fname}\" ./filestore/"

        done >> $FILE_COPY
    echo "Listed"
fi

exit 0
