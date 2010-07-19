from wtforms import *
from boFunctions import *


class PersonForm(Form):
    forename    = TextField(boTranslate('forename'), [validators.Required()])
    surname     = TextField(boTranslate('surname'), [validators.Required()])
    language    = SelectField(boTranslate('language'), choices=[
                                                                #('estonian', boTranslate('estonian')),
                                                                ('english', boTranslate('english'))
                                                               ])


class DictionariesForm(Form):
    name = TextField(boTranslate('name'), [validators.Required()])
    value = TextField(boTranslate('value'), [validators.Required()])
    translations = FieldList(TextField('Name', [validators.required()]), min_entries=3)
