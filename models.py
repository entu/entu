from google.appengine.ext import db
from google.appengine.ext import search
from google.appengine.api import users


class Person(search.SearchableModel):
	create_date 	= db.DateTimeProperty(auto_now_add=True)
	forename   		= db.StringProperty()
	surname   		= db.StringProperty()
	idcode  		= db.StringProperty()
	gender     		= db.StringProperty()
	birth_date 		= db.DateProperty()
	identities		= db.StringListProperty()


class PersonPreferences(db.Model):
	person 			= db.ReferenceProperty(Person, collection_name='preferences')
	language		= db.StringProperty()
	avatar			= db.BlobProperty()


class Contact(db.Model):
	create_date 	= db.DateTimeProperty(auto_now_add=True)
	person 			= db.ReferenceProperty(Person, collection_name='contacts')
	type   			= db.StringProperty()
	value  			= db.StringProperty()
	activation_key	= db.StringProperty()


class Role(db.Model):
	create_date 	= db.DateTimeProperty(auto_now_add=True)
	person 			= db.ReferenceProperty(Person, collection_name='roles')
	value  			= db.StringProperty()


class Classifier(db.Model):
	create_date 	= db.DateTimeProperty(auto_now_add=True)
	name			= db.StringProperty()
	values			= db.StringListProperty()


class Curriculum(search.SearchableModel):
	name				= db.StringProperty()
	code				= db.StringProperty()
	tags				= db.StringListProperty()
	level_of_education	= db.StringProperty()
	form_of_training	= db.StringProperty()
	nominal_years		= db.IntegerProperty()
	nominal_credit_points	= db.IntegerProperty()
	degree				= db.StringProperty()
	manager				= db.ReferenceProperty(Person, collection_name='managed_curriculums')


class RatingScale(db.Model):
	name			= db.StringProperty()


class Subject(search.SearchableModel):
	create_date 	= db.DateTimeProperty(auto_now_add=True)
	code			= db.StringProperty()
	name			= db.StringProperty()
	tags			= db.StringListProperty()
	credit_points	= db.FloatProperty()
	rating_scale	= db.ReferenceProperty(RatingScale, collection_name='subjects')

