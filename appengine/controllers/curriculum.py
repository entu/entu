from helpers import *
from database import *

from urllib import unquote


class ShowCurriculum(webapp.RequestHandler):
    def get(self, key = None):

        key = unquote(key).decode('utf8').strip('/')

        if key == '':
            tree = db.Query(Curriculum).filter('__key__', db.Key(key.strip('/'))).get()
        else:
            pass


        View(self, c.name.value, 'curriculum_tree.html', {
            'tree': tree,
        })


def main():
    Route([
            (r'/curriculum(.*)', ShowCurriculum)
        ])


if __name__ == '__main__':
    main()