from google.appengine.api import users

from boFunctions import *

class Frontpage(webapp.RequestHandler):
	def get(self):
		if boUser():
			self.redirect('/dashboard')

		boView(self, '', 'frontpage.html')


def main():
	boWSGIApp([
			 ('/', Frontpage),
			])


if __name__ == '__main__':
	main()