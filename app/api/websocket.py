from tornado import websocket

import logging
import json
import urllib

from main.helper import *
from main.db import *

clients = {}


# class ScanPage(myRequestHandler):
#     @web.authenticated
#     def get(self):
#         if not self.current_user:
#             return

#         code = self.get_argument('code', None, True)

#         if not code:
#             return self.write('Scan a code...')

#         for c in clients.get(self.current_user.get('id'), []):
#             c.write_message(code)

#         self.redirect('http://www.barcodesinc.com/generator/image.php?code=%s&style=452&type=C128B&width=388&height=100&xres=2&font=5' % code)


class PicToShopConfig(myRequestHandler):
    @web.removeslash
    @web.authenticated
    def get(self):
        self.redirect('p2spro://configure?%s' % urllib.urlencode({
            'lookup'      : '%s://%s/ws/scanner-%s?code=CODE&format=FORMAT' % (self.request.protocol, self.request.host, self.current_user.get('id')),
            'home'        : '%s://%s/ws/scanner' % (self.request.protocol, self.request.host),
            'formats'     : 'EAN13,EAN8,UPCE,ITF,CODE39,CODE128,CODABAR,CODE93,STD2OF5',
            'gps'         : True,
            'hidebuttons' : False,
            'autorotate'  : False,
            'highres'     : True,
            'settings'    : False,
        }))


class ScanPage(myRequestHandler):
    @web.removeslash
    def get(self, user_id):
        user_id = user_id.strip('-/ ')
        code = self.get_argument('code', None, True)

        if not code or not user_id:
            return self.write('Scan a code...')

        for c in clients.get(user_id, []):
            c.write_message(code)

        self.redirect('http://www.barcodesinc.com/generator/image.php?code=%s&style=452&type=C128B&width=388&height=100&xres=2&font=5' % code)


class ScanSocket(websocket.WebSocketHandler):
    def check_origin(self, origin):
        logging.debug('WebSocket check origin')
        return True
        # parsed_origin = urllib.parse.urlparse(origin)
        # return parsed_origin.netloc.endswith('.mydomain.com')

    def open(self):
        user_id = self.get_argument('id', None, True)

        if self not in clients.get(user_id, []):
            clients.setdefault(user_id, []).append(self)
            logging.debug('WebSocket opened for #%s' % user_id)

    def on_message(self, message):
        user_id = self.get_argument('id', None, True)

        # for c in clients.get(user_id, []):
        #     c.write_message(message)

    def on_close(self):
        user_id = self.get_argument('id', None, True)

        clients[user_id].remove(self)
        logging.debug('WebSocket closed')


handlers = [
    (r'/p2s', PicToShopConfig),
    (r'/ws/scanner_socket', ScanSocket),
    (r'/ws/scanner(.*)', ScanPage),
]
