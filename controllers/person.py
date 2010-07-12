from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from wtforms import *
from wtforms.ext.django import *

import urllib

from functions import *
from models import *


class List(webapp.RequestHandler):
    def get(self, a = None):
		b = a.split('/')
		print b[-2:]


class Search(webapp.RequestHandler):
   	
    def get(self, searchstr = None):
    
		searchstr = urllib.unquote(searchstr).decode('utf8')[1:]
		
		if searchstr:
			persons = Person.all().search(searchstr).fetch(100)
			
			view(self, 'search.html', {'persons': persons,  'search': searchstr,  'form': UserForm()})
		else:
			view(self, 'search_error.html')





class UserForm(Form): 
    title =			TextField(u'Title', [validators.required(), validators.length(max=150)]) 
    description = 	TextAreaField(u'Content', [validators.required()]) 
    genre = 		SelectField(u'Genre', [validators.required()]) 
    subgenre = 		TextField(u'Subgenres', [validators.length(max=250)]) 
    url = 			TextField(u'URL', [validators.required()])
    
    #form = 			forms.UserForm(req.form) 
    #errors = [] 
    #Add the choices to the genre list. 
    #form.genre.choices = [(genre.key().name().lower(), genre.name) for genre in Genre.all().fetch(1000)] 
    #form.genre.data = 'Psy'.lower() 














application = webapp.WSGIApplication([
									  (r'/person/search(.*)', Search),
									  (r'/person/(.*)', List)
									 ], debug=True)


def main():
    run_wsgi_app(application)


if __name__ == '__main__':
    main()