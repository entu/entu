from tornado import auth, web, httpclient
from bs4 import BeautifulSoup

import hashlib
import logging

from main.helper import *
from main.db import *

class ShowPhoto(myRequestHandler, Entity):
    """
    """
    entity_id = None
    photo_property = None
    isbn = None

    @web.asynchronous
    def get(self):

        entity_id = self.get_argument('entity', default=None, strip=True)
        ester_file_id = self.get_argument('ester_file', default=None, strip=True)

        if not entity_id and not ester_file_id:
            return self.missing()

        if entity_id:
            item = self.get_entities(entity_id=entity_id, full_definition=True, limit=1)
            if not item:
                return self.missing()
            self.photo_file = [x.get('db_value', '') for x in item.get('properties', {}).get('photo', {}).get('values', [])][0]
            if self.photo_file:
                return self.redirect('/api2/file-%s' % self.photo_file)
            self.entity_id = entity_id
            self.photo_property = [x.get('keyname') for x in item.get('properties', {}).values() if x.get('dataproperty') == 'photo'][0]
            self.isbn = [x.get('value', '').split(' ')[0] for x in item.get('properties', {}).get('isn', {}).get('values', [])][0]
            if not self.isbn:
                return self.redirect('https://secure.gravatar.com/avatar/%s?d=identicon&s=150' % (hashlib.md5('%s' % self.entity_id).hexdigest()))

        if ester_file_id:
            tmp_file = self.db_get('SELECT file FROM tmp_file WHERE id = %s LIMIT 1;', ester_file_id)
            if not tmp_file:
                return self.missing()
            if not tmp_file.get('file'):
                return self.missing()
            item = json.loads(tmp_file.get('file'))
            self.isbn = item.get('isn', '').split(' ')[0] if type(item.get('isn', '')) is not list else [x.split(' ')[0] for x in item.get('isn', [''])][0]
            if not self.isbn:
                return self.redirect('/static/images/blank.png')

        url = 'https://www.raamatukoi.ee/cgi-bin/index?valik=isbn&paring=%s' % self.isbn
        httpclient.AsyncHTTPClient().fetch(url, callback=self._got_raamatukoi_item, request_timeout=60)

    @web.asynchronous
    def _got_raamatukoi_item(self, response):
        if not response.body:
            self.finish()
            return

        soup = BeautifulSoup(response.body.decode('utf-8', 'ignore'))
        url = None

        table = soup.find('table', {'width' : '450'})
        if table:
            img = table.find('img')
            if img:
                url = img.get('src')
                httpclient.AsyncHTTPClient().fetch(url, callback=self._got_photo, request_timeout=60)

        if not url:
            if self.entity_id:
                return self.redirect('https://secure.gravatar.com/avatar/%s?d=identicon&s=150' % (hashlib.md5('%s' % self.entity_id).hexdigest()))
            else:
                return self.redirect('/static/images/blank.png')

    @web.asynchronous
    def _got_photo(self, response):
        if not response.body:
            self.finish()
            return

        if self.photo_property:
            self.set_property(entity_id=self.entity_id, property_definition_keyname=self.photo_property, value={'filename': response.effective_url.split('/')[-1], 'body': response.body})

        self.add_header('Content-Type', response.headers.get('Content-Type'))
        self.write(response.body)
        self.finish()


handlers = [
    ('/photo-by-isbn', ShowPhoto),
]
