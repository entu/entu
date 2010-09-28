from helpers import *
from database import *


class Delete(webapp.RequestHandler):
    def get(self ,url):
        #q = db.GqlQuery('SELECT * FROM ' + url)
        for a in db.Query(Subject):
            a.__searchable_text_index = None
            a.put()
            #try:
            #    a.delete()
            #except:
            #    a.deleted = True
            #    a.save()

        #View(self, '', 'delete.html', { 'count': q.count() })


def main():
    Route([
            (r'/delete/(.*)', Delete),
        ])


if __name__ == '__main__':
    main()