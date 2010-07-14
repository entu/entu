from google.appengine.tools import bulkloader
from google.appengine.ext import db
from google.appengine.ext import search
import datetime
import sys
import os.path


sys.path.append(
	os.path.abspath(
		os.path.dirname(
			os.path.realpath(__file__))))


from models import *


def get_date_from_str(s):
	if s:
		return datetime.datetime.strptime(s, '%Y-%m-%d').date()
	else:
		return None

def get_utf8_str(s):
	if s:
		return s.decode('utf-8')
	else:
		return None

def get_person_key(s):
	if s:
		return db.Key.from_path('Person', s.decode('utf-8'))
	else:
		return None

def get_ratingscale_key(s):
	if s:
		return db.Key.from_path('RatingScale', s.decode('utf-8'))
	else:
		return None

def get_list(s):
	if s:
		return [s.decode('utf-8')]
	else:
		return None


#PERSONS DATA

class PersonLoader(bulkloader.Loader):
	def __init__(self):
		bulkloader.Loader.__init__(self, 'Person',
			[('key_name', get_utf8_str),			# old_id
			 ('forename', get_utf8_str),
			 ('surname', get_utf8_str),
			 ('idcode', get_utf8_str),
			 ('gender', get_utf8_str),				# Classifier
			 ('birth_date', get_date_from_str),
			])

	def handle_entity(self, entity):
		entity.save()


class ContactLoader(bulkloader.Loader):
	def __init__(self):
		bulkloader.Loader.__init__(self, 'Contact',
			[('person', get_person_key),
			 ('type', get_utf8_str),
			 ('value', get_utf8_str),
			])

	def handle_entity(self, entity):
		entity.save()


class RoleLoader(bulkloader.Loader):
	def __init__(self):
		bulkloader.Loader.__init__(self, 'Role',
			[('person', get_person_key),
			 ('value', get_utf8_str),
			])

	def handle_entity(self, entity):
		entity.save()


#CURRICULUM

class CurriculumLoader(bulkloader.Loader):
	def __init__(self):
		bulkloader.Loader.__init__(self, 'Curriculum',
			[('key_name', get_utf8_str),			# old_id
			 ('name', get_utf8_str),
			 ('code', get_utf8_str),
			 ('tags', get_list),
			 ('level_of_education', get_utf8_str),	# Classifier
			 ('form_of_training', get_utf8_str),	# Classifier
			 ('nominal_years', int),
			 ('nominal_credit_points', int),
			 ('degree', get_utf8_str),				# Classifier
			])

	def handle_entity(self, entity):
		entity.save()


class RatingScaleLoader(bulkloader.Loader):
	def __init__(self):
		bulkloader.Loader.__init__(self, 'RatingScale',
			[('key_name', get_utf8_str),
			 ('name', get_utf8_str),
			])

	def handle_entity(self, entity):
		entity.save()


class SubjectLoader(bulkloader.Loader):
	def __init__(self):
		bulkloader.Loader.__init__(self, 'Subject',
			[('key_name', get_utf8_str),
			 ('name', get_utf8_str),
			 ('code', get_utf8_str),
			 ('tags', get_list),
			 ('credit_points', float),
			 ('rating_scale', get_ratingscale_key),
			])

	def handle_entity(self, entity):
		entity.save()


loaders = [PersonLoader, ContactLoader, RoleLoader, CurriculumLoader, RatingScaleLoader, SubjectLoader]