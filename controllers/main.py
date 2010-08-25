from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app


class MainHandler(bo.webapp.RequestHandler):

    def get(self, path = None):
        print ''



def main():
    application = webapp.WSGIApplication([(r'/', MainHandler)], debug=True)
    run_wsgi_app(application)


if __name__ == '__main__':
    main()
