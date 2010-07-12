import os

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp import util
from google.appengine.api import users

from models import *

from translations.estonian import *


def boView(self, page_title, templatefile, values={}):
	values['str'] = TRANSLATION
	values['page_title'] = self.request.headers.get('host') #boTranslate(page_title)
	values['user'] = boUser()
	values['logouturl'] = users.create_logout_url('/')
	path = os.path.join(os.path.dirname(__file__), 'templates', templatefile)
	self.response.out.write(template.render(path, values))


def boWSGIApp(url_mapping):
	application = webapp.WSGIApplication(url_mapping, debug=True)
	util.run_wsgi_app(application)


def boStrToList(string):
	return [x.strip() for x in string.strip().replace('\n', ' ').replace(',', ' ').replace(';', ' ').split(' ') if len(x.strip()) > 0]


def boTranslate(key):
	return TRANSLATION[key].decode('utf8')


def boUser():
	user = users.get_current_user()
	if user:
		if user.federated_identity():
			return db.Query(Person).filter('identities =', user.federated_identity()).get()


def boRescale(img_data, width, height, halign='middle', valign='middle'):
	from google.appengine.api import images
	image = images.Image(img_data)

	desired_wh_ratio = float(width) / float(height)
	wh_ratio = float(image.width) / float(image.height)

	if desired_wh_ratio > wh_ratio:
		image.resize(width=width)
		image.execute_transforms()
		trim_y = (float(image.height - height) / 2) / image.height
		if valign == 'top':
			image.crop(0.0, 0.0, 1.0, 1 - (2 * trim_y))
		elif valign == 'bottom':
			image.crop(0.0, (2 * trim_y), 1.0, 1.0)
		else:
			image.crop(0.0, trim_y, 1.0, 1 - trim_y)
	else:
		image.resize(height=height)
		image.execute_transforms()
		trim_x = (float(image.width - width) / 2) / image.width
		if halign == 'left':
			image.crop(0.0, 0.0, 1 - (2 * trim_x), 1.0)
		elif halign == 'right':
			image.crop((2 * trim_x), 0.0, 1.0, 1.0)
		else:
			image.crop(trim_x, 0.0, 1 - trim_x, 1.0)

	return image.execute_transforms()
