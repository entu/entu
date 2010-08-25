import bo
from database import *


class Delete(bo.webapp.RequestHandler):
    def get(self ,url):
        q = db.GqlQuery('SELECT * FROM ' + url)
        db.delete(q.fetch(300))
        bo.view(self, '', 'delete.html', { 'count': q.count() })


def main():
    bo.app([
            (r'/delete/(.*)', Delete),
        ])


if __name__ == '__main__':
    main()