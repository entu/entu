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
    def get(self, entity_id=None):

        if not entity_id:
            return self.missing()

        item = self.get_entities(entity_id=entity_id, full_definition=True, limit=1)

        if not item:
            return self.missing()

        self.entity_id = entity_id

        self.photo_property = [x.get('keyname') for x in item.get('properties', {}).values() if x.get('dataproperty') == 'photo'][0]

        self.isbn = [x.get('value', '').split(' ')[0] for x in item.get('properties', {}).get('isn', {}).get('values', [])][0]
        if not self.isbn:
            return self.redirect('https://secure.gravatar.com/avatar/%s?d=identicon&s=150' % (hashlib.md5(self.entity_id).hexdigest()))

        url = 'http://pood.rahvaraamat.ee/otsing?frst=1&page=1&q=%s&t=1' % self.isbn
        httpclient.AsyncHTTPClient().fetch(url, callback=self._got_rahvaraamat_list, request_timeout=60)

    @web.asynchronous
    def _got_rahvaraamat_list(self, response):
        if not response.body:
            self.finish()
            return

        soup = BeautifulSoup(response.body.decode('utf-8', 'ignore'))
        url = None

        div = soup.find(id='product_thumbnail')
        if div:
            a = div.find('a')
            if a:
                url = a.get('href')
                httpclient.AsyncHTTPClient().fetch(url, callback=self._got_photo, request_timeout=60)
        else:
            div = soup.find('div', class_='list_product_title')
            if div:
                a = div.find('a')
                if a:
                    url = 'http://pood.rahvaraamat.ee%s' % a.get('href')
                    httpclient.AsyncHTTPClient().fetch(url, callback=self._got_rahvaraamat_item, request_timeout=60)

        if not url:
            url = 'https://www.raamatukoi.ee/cgi-bin/index?valik=isbn&paring=%s' % self.isbn
            httpclient.AsyncHTTPClient().fetch(url, callback=self._got_raamatukoi_item, request_timeout=60)

    @web.asynchronous
    def _got_rahvaraamat_item(self, response):
        if not response.body:
            self.finish()
            return

        soup = BeautifulSoup(response.body.decode('utf-8', 'ignore'))
        url = None

        div = soup.find(id='product_thumbnail')
        if div:
            a = div.find('a')
            if a:
                url = a.get('href')
                httpclient.AsyncHTTPClient().fetch(url, callback=self._got_photo, request_timeout=60)

        if not url:
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
            return self.redirect('https://secure.gravatar.com/avatar/%s?d=identicon&s=150' % (hashlib.md5(self.entity_id).hexdigest()))

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
    (r'/photo-by-isbn-(.*)', ShowPhoto),
]
