from bo import *
from database import *


class Delete(webapp.RequestHandler):
    def get(self ,url):
        q = db.GqlQuery('SELECT * FROM ' + url)
        db.delete(q.fetch(300))
        View(self, '', 'delete.html', { 'count': q.count() })


def main():
    Route([
            (r'/delete/(.*)', Delete),
        ])


if __name__ == '__main__':
    main()