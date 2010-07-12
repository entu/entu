import os
from google.appengine.ext.webapp import template

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from models import *

class deletePerson(webapp.RequestHandler):
	def get(self):
		q = Person.all()
		db.delete(Person.all().fetch(300))
		path = os.path.join(os.path.dirname(__file__), '../views/delete.html')
		template_values = { 'count': q.count() }
		self.response.out.write(template.render(path, template_values))


class deleteContact(webapp.RequestHandler):
	def get(self):
		q = Contact.all()
		db.delete(q.fetch(300))
		path = os.path.join(os.path.dirname(__file__), '../views/delete.html')
		template_values = { 'count': q.count() }
		self.response.out.write(template.render(path, template_values))


application = webapp.WSGIApplication([
									  (r'/delete/person', deletePerson),
									  (r'/delete/contact', deleteContact)
									 ], debug=True)
def main():
    run_wsgi_app(application)


if __name__ == '__main__':
    main()