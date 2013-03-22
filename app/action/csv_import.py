from tornado import auth
from tornado import web

import csv
import StringIO
import logging

from main.helper import *
from main.db import *


class UploadFile(myRequestHandler):
    """
    """
    @web.authenticated
    def post(self):
        if not self.request.files.get('file', None):
            return

        uploaded_file = self.request.files.get('file', [])[0] if self.request.files.get('file', None) else None
        if not uploaded_file:
            return

        file_id = self.db.execute_lastrowid('INSERT INTO tmp_file SET filename = %s, file = %s, created_by = %s, created = NOW();', uploaded_file['filename'], uploaded_file['body'], self.current_user.id)

        # csv.reader(zf.read('0010711996.txt').split('\n'), delimiter='\t')

        self.write(str(file_id))


class ReadFile(myRequestHandler):
    """
    """
    @web.authenticated
    def post(self):
        file_id = self.get_argument('file_id', None)
        delimiter = self.get_argument('delimiter', ',')
        first_row = self.get_argument('first_row', 1)
        parent_entity_id = self.get_argument('parent_entity_id', None)
        entity_definition_keyname = self.get_argument('entity_definition_keyname', None)

        if not file_id or not delimiter or not parent_entity_id or not entity_definition_keyname:
            return

        first_row = int(first_row)

        tmp_file = self.db.get('SELECT * FROM tmp_file WHERE id = %s AND created_by = %s LIMIT 1;', file_id, self.current_user.id)

        if not tmp_file:
            return

        csv_headers = None
        row_count = 0
        for row in csv.reader(StringIO.StringIO(tmp_file.file), delimiter=str(delimiter)):
            if not csv_headers:
                csv_headers = row
            row_count += 1


        item = self.get_entities(entity_id=0, entity_definition_keyname=entity_definition_keyname, limit=1, full_definition=True)

        self.render('action/csv_read.html',
            file_id = file_id,
            file_name = tmp_file.filename,
            delimiter = delimiter,
            first_row = first_row,
            row_count = row_count,
            csv_headers = csv_headers,
            properties = item.get('properties', {}).values(),
            parent_entity_id = parent_entity_id,
            entity_definition_keyname = entity_definition_keyname,
        )


class ImportFile(myRequestHandler):
    """
    """
    @web.authenticated
    def post(self):
        file_id = self.get_argument('file_id', None)
        delimiter = self.get_argument('delimiter', ',')
        first_row = self.get_argument('first_row', 1)
        parent_entity_id = self.get_argument('parent_entity_id', None)
        entity_definition_keyname = self.get_argument('entity_definition_keyname', None)

        first_row = int(first_row)

        tmp_file = self.db.get('SELECT * FROM tmp_file WHERE id = %s AND created_by = %s LIMIT 1;', file_id, self.current_user.id)

        if not tmp_file:
            return

        item = self.get_entities(entity_id=0, entity_definition_keyname=entity_definition_keyname, limit=1, full_definition=True)
        properties = item.get('properties', {}).values()

        row_num = 0
        for row in csv.reader(StringIO.StringIO(tmp_file.file), delimiter=str(delimiter)):
            row_num += 1
            if row_num < first_row:
                continue
            entity_id = self.create(entity_definition_keyname=entity_definition_keyname, parent_entity_id=parent_entity_id)
            for p in properties:
                field = self.get_argument('field_%s' % p.get('dataproperty'), None)
                if not field:
                    continue
                value = row[int(field)]
                if not value:
                    continue

                property_id = self.set_property(entity_id=entity_id, property_definition_keyname=p.get('keyname'), value=value)


handlers = [
    ('/action/csv/upload', UploadFile),
    ('/action/csv/read', ReadFile),
    ('/action/csv/import', ImportFile),
]
