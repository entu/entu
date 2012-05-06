from tornado.web import RequestHandler
from tornado.options import options

class MainHandler(RequestHandler):
    def get(self):
        self.write('arx:' + str(options.port))

handlers = [
    (r'/', MainHandler),
]
