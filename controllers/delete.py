from boFunctions import *
from models import *


class Delete(webapp.RequestHandler):
    def get(self ,url):
        q = db.GqlQuery('SELECT * FROM ' + url)
        db.delete(q.fetch(300))
        boView(self, '', 'delete.html', { 'count': q.count() })


def main():
    boWSGIApp([
            (r'/delete/(.*)', Delete),
        ])


if __name__ == '__main__':
    main()