from wtforms import *
from boFunctions import *


class PersonForm(Form):
	forename	= TextField(boTranslate('forename'), [validators.Required()])
	surname		= TextField(boTranslate('surname'), [validators.Required()])
	language	= SelectField(boTranslate('language'), choices=[
																#('estonian', boTranslate('estonian')),
																('english', boTranslate('english'))
																])


class ClassifiersForm(Form):
	name = TextField(boTranslate('name'), [validators.Required()])
	values = TextAreaField(boTranslate('values'))