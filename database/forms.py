from wtforms import *

from translations import *


class PersonForm(Form):
    forename    = TextField(Translations('forename'), [validators.Required()])
    surname     = TextField(Translations('surname'), [validators.Required()])
    language    = SelectField(Translations('language'), choices=[
                                                                #('estonian', Translations('estonian')),
                                                                ('english', Translations('english'))
                                                               ])


class DictionariesForm(Form):
    name = TextField(Translations('name'), [validators.Required()])
    value = TextField(Translations('value'), [validators.Required()])
    translations = FieldList(TextField('Name', [validators.required()]), min_entries=3)
