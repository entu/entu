from bo import *

class Show(webapp.RequestHandler):
    def get(self):

        page_meta = '<link rel="stylesheet" type="text/css" media="screen" href="/css/slickmap.css" />'

        View(self, 'dashboard', 'dashboard.html', { 'page_meta': page_meta })


def main():
    Route([
            ('/dashboard', Show)
        ])


if __name__ == '__main__':
    main()