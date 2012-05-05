import tornado.ioloop
import tornado.web
import tornado.options

from tornado.options import define, options

define('port', default=8000, help='run on the given port', type=int)

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write('bubbledu')

application = tornado.web.Application([
    (r'/', MainHandler),
])

if __name__ == '__main__':
    tornado.options.parse_command_line()
    application.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
