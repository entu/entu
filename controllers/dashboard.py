from google.appengine.api import users

from boFunctions import *

class Dashboard(webapp.RequestHandler):
	def get(self):
		
		page_meta = '<link rel="stylesheet" type="text/css" media="screen" href="/css/slickmap.css" />'
		
		boView(self, 'dashboard', 'dashboard.html', { 'page_meta': page_meta })


def main():
	boWSGIApp([
			 ('/dashboard', Dashboard),
			])


if __name__ == '__main__':
	main()