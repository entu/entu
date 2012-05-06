import tornado.ioloop
import tornado.options

from tornado.options import define, options

define('port', default=8000, help='run on the given port', type=int)
define('database', help='database name', type=str)

controllers = [
    'bubble',
    'public',
]
handlers = []
for controller in controllers:
    c = __import__ (controller, globals(), locals(), ['*'], -1)
    handlers.extend(c.handlers)

application = tornado.web.Application(
    handlers = handlers,
    debug = True
)

if __name__ == '__main__':
    tornado.options.parse_command_line()
    application.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
