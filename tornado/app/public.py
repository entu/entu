from tornado.web import RequestHandler
from tornado.options import options


class PublicHandler(RequestHandler):
    def get(self):
        self.write('public arx:' + str(options.port))


class PublicHandler1(RequestHandler):
    def get(self, jama):
        self.write(jama + ' public arx:' + str(options.port))

handlers = [
    (r'/public', PublicHandler),
    (r'/public(.*)', PublicHandler1),
]
