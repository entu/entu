from tornado import gen
from tornado import httpclient

from main.helper import *




class API2MetNo(myRequestHandler):
    @web.removeslash
    @gen.coroutine
    def get(self, metno_request):
        metno_url = 'https://api.met.no/weatherapi/' + metno_request

        http_client = httpclient.AsyncHTTPClient()
        erply_user_request = yield http_client.fetch(httpclient.HTTPRequest(
            url=metno_url,
            method='GET'
        ))

        self.write(erply_user_request.body)




handlers = [
    (r'/metno/(.*)', API2MetNo),
]
