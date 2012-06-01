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
FILE_UPLOAD=~/files.lst
FILES_SQL=~/files.sql

BD_FOLDER='agpzfmJ1YmJsZWR1cg8LEgZCdWJibGUY2qTUAgw'
PD_FOLDER_IS_PUBLIC='agpzfmJ1YmJsZWR1cg8LEgZCdWJibGUY2qTUAgw_agpzfmJ1YmJsZWR1cg8LEgZCdWJibGUYg53UAgw'
PD_FOLDER_NAME='agpzfmJ1YmJsZWR1cg8LEgZCdWJibGUY2qTUAgw_agpzfmJ1YmJsZWR1cg8LEgZCdWJibGUYmO7TAgw'
BD_DOCUMENT='agpzfmJ1YmJsZWR1cg8LEgZCdWJibGUYxNXRAgw'
PD_FILE='agpzfmJ1YmJsZWR1cg8LEgZCdWJibGUYxNXRAgw_agpzfmJ1YmJsZWR1cg8LEgZCdWJibGUYsbTUAgw'
ROOT_B_KEY="amphora_ROOT"

ARGO_PERSON_KEY='agpzfmJ1YmJsZWR1cg8LEgZCdWJibGUYy_rLAgw'
MIHKEL_PERSON_KEY='agpzfmJ1YmJsZWR1cg8LEgZCdWJibGUY1IfMAgw'


echo "You might want to add rights after import with:
------------------------------
DELETE FROM `relationship`
WHERE `related_bubble_id` IN (SELECT id FROM bubble WHERE gae_key IN ('${ARGO_PERSON_KEY}','${MIHKEL_PERSON_KEY}'));
INSERT IGNORE INTO relationship (bubble_id, related_bubble_id, `type`)
SELECT id AS bubble_id, (SELECT id FROM bubble WHERE gae_key = '${ARGO_PERSON_KEY}') AS related_bubble_id, 'viewer' AS `type` FROM bubble;
INSERT IGNORE INTO relationship (bubble_id, related_bubble_id, `type`)
SELECT id AS bubble_id, (SELECT id FROM bubble WHERE gae_key = '${MIHKEL_PERSON_KEY}') AS related_bubble_id, 'viewer' AS `type` FROM bubble;
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
                echo "${ROOT_B_KEY}/$fn"
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
    B_KEY="${ROOT_B_KEY}"
    echo "-- Root element" > $FOLDERS_MYSQL
    echo "INSERT INTO bubble SET bubble_definition_id = (SELECT id FROM bubble_definition WHERE gae_key = '${BD_FOLDER}'), gae_key = '${B_KEY}' ON DUPLICATE KEY UPDATE bubble_definition_id = (SELECT id FROM bubble_definition WHERE gae_key = '${BD_FOLDER}'), gae_key = '${B_KEY}';" >> $FOLDERS_MYSQL

    echo "DELETE FROM property WHERE bubble_id = (SELECT id FROM bubble WHERE gae_key = '${B_KEY}');" >> $FOLDERS_MYSQL
    echo "INSERT INTO property SET property_definition_id = (SELECT id FROM property_definition WHERE gae_key = '${PD_FOLDER_NAME}'), bubble_id = (SELECT id FROM bubble WHERE gae_key = '${B_KEY}'), language = 'estonian', value_string = 'Amphora dokumendid';" >> $FOLDERS_MYSQL
    echo "INSERT INTO property SET property_definition_id = (SELECT id FROM property_definition WHERE gae_key = '${PD_FOLDER_NAME}'), bubble_id = (SELECT id FROM bubble WHERE gae_key = '${B_KEY}'), language = 'english', value_string = 'Amphora Root';" >> $FOLDERS_MYSQL

    # Create Amphora folders
    while read fn
    do
        echo "-- ${fn}"
        B_KEY="${fn}"
        PARENT_B_KEY=`echo $B_KEY | rev | cut -d'/' -f2- | rev`
        echo "INSERT INTO bubble SET bubble_definition_id = (SELECT id FROM bubble_definition WHERE gae_key = '${BD_FOLDER}'), gae_key = '${B_KEY}' ON DUPLICATE KEY UPDATE bubble_definition_id = (SELECT id FROM bubble_definition WHERE gae_key = '${BD_FOLDER}'), gae_key = '${B_KEY}';"

        echo "DELETE FROM relationship WHERE related_bubble_id = (SELECT id FROM bubble WHERE gae_key = '${B_KEY}');"
        echo "INSERT INTO relationship SET bubble_id = (SELECT id FROM bubble WHERE gae_key = '${PARENT_B_KEY}'), related_bubble_id = (SELECT id FROM bubble WHERE gae_key = '${B_KEY}'), type='subbubble', gae_key='${PARENT_B_KEY}_${B_KEY}';"

        echo "DELETE FROM property WHERE bubble_id = (SELECT id FROM bubble WHERE gae_key = '${B_KEY}');"
        echo "INSERT INTO property SET property_definition_id = (SELECT id FROM property_definition WHERE gae_key = '${PD_FOLDER_NAME}'), bubble_id = (SELECT id FROM bubble WHERE gae_key = '${B_KEY}'), language = 'estonian', value_string = '${fn}';"
        echo "INSERT INTO property SET property_definition_id = (SELECT id FROM property_definition WHERE gae_key = '${PD_FOLDER_NAME}'), bubble_id = (SELECT id FROM bubble WHERE gae_key = '${B_KEY}'), language = 'english', value_string = '${fn}';"

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
            fname=`basename "${fn}"`

            file_orig_name=`grep file_orig_name "${fn}" | sed -e 's/<[a-zA-Z\/][^>]*>//g' | sed 's/^ *//;s/ *$//' | tr -d '[ \r]'`
            file_orig_guid=`grep file_orig_guid "${fn}" | sed -e 's/<[a-zA-Z\/][^>]*>//g' | sed 's/^ *//;s/ *$//' | tr -d '[ \r]'`
            # document_date=`grep document_date "${fn}" | sed -e 's/<[a-zA-Z\/][^>]*>//g' | sed 's/^ *//;s/ *$//' | tr -d '[ \r]'`
            # author=`grep author "${fn}" | sed -e 's/<[a-zA-Z\/][^>]*>//g' | sed 's/^ *//;s/ *$//' | tr -d '[ \r]'`

            FILE_KEY="amphora_${file_orig_guid}"
            DOCUMENT_KEY="${FILE_KEY}"
            DIRECTORY_KEY="${ROOT_B_KEY}/${dname}"
            # Create document bubble
            echo "INSERT INTO bubble SET bubble_definition_id = (SELECT id FROM bubble_definition WHERE gae_key = '${BD_DOCUMENT}'), gae_key = '${DOCUMENT_KEY}' ON DUPLICATE KEY UPDATE bubble_definition_id = (SELECT id FROM bubble_definition WHERE gae_key = '${BD_DOCUMENT}'), gae_key = '${DOCUMENT_KEY}';"
            echo "DELETE FROM relationship WHERE related_bubble_id = (SELECT id FROM bubble WHERE gae_key = '${DOCUMENT_KEY}');"
            echo "INSERT INTO relationship SET bubble_id = (SELECT id FROM bubble WHERE gae_key = '${DIRECTORY_KEY}'), related_bubble_id = (SELECT id FROM bubble WHERE gae_key = '${DOCUMENT_KEY}'), type='subbubble', gae_key='${DIRECTORY_KEY}_${DOCUMENT_KEY}';"

            # Insert file metadata
            echo "INSERT IGNORE INTO file SET gae_key='${FILE_KEY}', filename='${file_orig_name}';"

            # Add file property to document
            echo "DELETE FROM property WHERE bubble_id = (SELECT id FROM bubble WHERE gae_key = '${DOCUMENT_KEY}');"
            echo "INSERT INTO property SET property_definition_id = (SELECT id FROM property_definition WHERE gae_key = '${PD_FILE}'), bubble_id = (SELECT id FROM bubble WHERE gae_key = '${DOCUMENT_KEY}'), value_file = (SELECT id FROM file WHERE gae_key = '${FILE_KEY}');"

            # Prepare for file upload
            echo "${FILE_KEY}    `dirname "${fn}"`/${file_orig_guid}" >> $FILE_UPLOAD

        done >> $FILES_SQL
    echo "Parsed"
fi

exit 0
