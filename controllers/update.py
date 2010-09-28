from helpers import *
from database import *


class Update(webapp.RequestHandler):

    def get(self):
        for c in db.Query(Translation).fetch(1000):
            try:
                c.dictionary_name = c.dictionary.name
                c.save()
            except:
                self.response.out.write(str(c.key()) + '\n')



def main():
    Route([
            (r'/update', Update),
        ])


if __name__ == '__main__':
    main()