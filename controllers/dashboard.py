import bo

class Dashboard(bo.webapp.RequestHandler):
    def get(self):

        page_meta = '<link rel="stylesheet" type="text/css" media="screen" href="/css/slickmap.css" />'

        bo.view(self, 'dashboard', 'dashboard.html', { 'page_meta': page_meta })


def main():
    bo.app([
             ('/dashboard', Dashboard),
            ])


if __name__ == '__main__':
    main()