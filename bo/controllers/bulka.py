from google.appengine.ext.remote_api import handler
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

class ApiCallHandler(handler.ApiCallHandler):
    def CheckIsAdmin(self):

        return True


application = webapp.WSGIApplication([('.*', ApiCallHandler)])


def main():
    run_wsgi_app(application)


if __name__ == '__main__':
    main()