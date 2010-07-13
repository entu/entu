from google.appengine.api import users

from boFunctions import *

class Dashboard(webapp.RequestHandler):
	def get(self):
		
		boView(self, 'dashboard', 'dashboard.html')


def main():
	boWSGIApp([
			 ('/dashboard', Dashboard),
			])


if __name__ == '__main__':
	main()