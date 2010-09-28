from wtforms import *

from helpers import *


class PersonForm(Form):
    forename    = TextField(Translate('forename'), [validators.Required()])
    surname     = TextField(Translate('surname'), [validators.Required()])
    language    = SelectField(Translate('language'), choices=[
                                                                #('estonian', Translate('estonian')),
                                                                ('english', Translate('english'))
                                                               ])


class DictionariesForm(Form):
    name = TextField(Translate('name'), [validators.Required()])
    value = TextField(Translate('value'), [validators.Required()])
    translations = FieldList(TextField('Name', [validators.required()]), min_entries=3)
