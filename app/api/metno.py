import urllib

from tornado import gen
from tornado import httpclient

from main.helper import *




class API2MetNo(myRequestHandler):
    @web.removeslash
    @gen.coroutine
    def get(self, metno_request):
        arguments = {}
        if self.request.arguments:
            for x, y in self.request.arguments.iteritems():
                arguments[x] = y[0]

        http_client = httpclient.AsyncHTTPClient()
        metno_request = yield http_client.fetch(httpclient.HTTPRequest(
            url='https://api.met.no/weatherapi/' + metno_request + '?' + urllib.urlencode(arguments),
            method='GET'
        ))

        self.set_header('Content-Type', metno_request.headers['Content-Type'])
        self.write(metno_request.body)




handlers = [
    (r'/metno/(.*)', API2MetNo),
]
