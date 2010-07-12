from wtforms import *
from boFunctions import *


class UserPreferencesForm(Form):
	forename	= TextField(boTranslate('forename'), [validators.Length(max=35)])
	surname		= TextField(boTranslate('surname'), [validators.Length(max=35)])
	language	= SelectField(boTranslate('language'), choices=[
																#('estonian', boTranslate('estonian')),
																('english', boTranslate('english'))
																])
	avatar		= FileField(boTranslate('avatar'))
