from tornado.web import RequestHandler
from tornado.options import options
from tornado import locale

from helper import *


class PublicHandler(myRequestHandler):
    def get(self, search):
        items = []
        # for i in self.getresults(search):
        #     items.append(i)

        self.render('public/list.html',
            page_title = self.locale.translate('search_results'),
            items = items,
        )

    def getresults(self, search):
        for item in myDb().query('SELECT * FROM items WHERE search LIKE %s LIMIT 1000;', ('%'+search+'%')):
            yield item


handlers = [
    (r'/public(.*)', PublicHandler),
]
