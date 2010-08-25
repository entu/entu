import os

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp import util

from bo import *
from database import *
from translations import *

def view(self, page_title, templatefile, values={}):
    values['str'] = Translations()
    if page_title:
        values['site_name'] = SYSTEM_TITLE + ' - ' + Translations(page_title)
        values['page_title'] = Translations(page_title)
    else:
        values['site_name'] = SYSTEM_TITLE
        values['page_title'] = '&nbsp;'
    values['site_url'] = self.request.headers.get('host')
    values['user'] = Person().current()
    values['logouturl'] = users.create_logout_url('/')
    path = os.path.join(os.path.dirname(__file__), '..', 'templates', templatefile)
    self.response.out.write(template.render(path, values))


def app(url_mapping):
    application = webapp.WSGIApplication(url_mapping, debug=True)
    util.run_wsgi_app(application)