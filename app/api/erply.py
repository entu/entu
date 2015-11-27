import urllib
import json

from tornado import gen
from tornado import httpclient

from main.helper import *




class API2Erply(myRequestHandler):
    @web.removeslash
    @gen.coroutine
    def post(self, erply_request):
        try:
            ERPLY_CUSTOMER = self.app_settings('auth-erply', '\n', True).split('\n')[0]
            ERPLY_USER     = self.app_settings('auth-erply', '\n', True).split('\n')[1]
            ERPLY_PASSWORD = self.app_settings('auth-erply', '\n', True).split('\n')[2]
        except Exception, e:
            self.json({
                'error': 'Erply customer, user or password not set!',
                'time': round(self.request.request_time(), 3),
            }, 400)
            return

        erply_url = 'https://%s.erply.com/api/' % ERPLY_CUSTOMER

        if not self.current_user:
            self.json({
                'error': 'Forbidden!',
                'time': round(self.request.request_time(), 3),
            }, 403)
            return

        http_client = httpclient.AsyncHTTPClient()
        erply_user_request = yield http_client.fetch(httpclient.HTTPRequest(
            url=erply_url,
            method='POST',
            body=urllib.urlencode({
                'clientCode':   ERPLY_CUSTOMER,
                'username':     ERPLY_USER,
                'password':     ERPLY_PASSWORD,
                'responseType': 'JSON',
                'request':      'verifyUser',
            })
        ))

        try:
            erply_user = json.loads(erply_user_request.body)
        except Exception:
            self.json({
                'error': 'Erply user auth failed!',
                'time': round(self.request.request_time(), 3),
            }, 500)
            return

        if not erply_user.get('records'):
            self.json(erply_user)
            return

        erply_session = erply_user.get('records')[0].get('sessionKey', None)
        if not erply_session:
            self.json(erply_user)
            return

        arguments = {
            'clientCode':     ERPLY_CUSTOMER,
            'sessionKey':     erply_session,
            'request':        erply_request,
            'responseType':   'JSON',
        }

        if self.request.arguments:
            for x, y in self.request.arguments.iteritems():
                arguments[x] = y[0]

        page = 0
        result = []

        while True:
            page = page + 1
            arguments['recordsOnPage'] = 100
            arguments['pageNo'] = page

            erply_api_request = yield http_client.fetch(httpclient.HTTPRequest(
                url=erply_url,
                method='POST',
                body=urllib.urlencode(arguments)
            ))

            try:
                erply_api = json.loads(erply_api_request.body)
            except Exception:
                self.json({
                    'error': 'Erply request failed!',
                    'time': round(self.request.request_time(), 3),
                }, 500)
                return

            result = result + erply_api.get('records', [])

            if int(erply_api.get('status', {}).get('recordsTotal', 0)) <= len(result):
                break

        self.json({
            'result': result,
            'time': round(self.request.request_time(), 3),
        })




handlers = [
    (r'/erply/(.*)', API2Erply),
]
