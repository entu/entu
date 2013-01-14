from tornado import auth, web
from tornado import httpclient

import logging

from helper import *
from db import *


class UpdateFormulasWeb(myRequestHandler):
    @web.authenticated
    def get(self, entity_id):
        if self.current_user.email != 'mihkel.putrinsh@gmail.com':
            return

        updateFormulas(entity_id=entity_id, user_locale=self.get_user_locale(), user_id=self.current_user.id)


class UpdateFormulasRecursiveWeb(myRequestHandler):
    @web.authenticated
    def get(self, entity_id):
        if self.current_user.email != 'mihkel.putrinsh@gmail.com':
            return

        updateFormulasRecursive(entity_id=entity_id, user_locale=self.get_user_locale(), user_id=self.current_user.id)


def updateFormulas(entity_id, user_locale, user_id):
    entity = db.Entity(user_locale, user_id)

    logging.debug('e:%s' % str(entity_id))
    for row in entity.formula_properties(entity_id = entity_id):
        logging.debug('p:%s, f:%s' % (str(row.entity_id), row.value_formula))
        entity.set_property(entity_id=entity_id, old_property_id = row.id, property_definition_keyname = row.property_definition_keyname, value = row.value_formula)

def updateFormulasRecursive(entity_id, user_locale, user_id):
    updateFormulas(entity_id, user_locale, user_id)
    entity = db.Entity(user_locale, user_id)
    for e_id in entity.get_relatives(ids_only=True, entity_id=entity_id, relationship_definition_keyname='child'):
        updateFormulasRecursive(e_id, user_locale, user_id)


handlers = [
    (r'/update/formulas/(.*)', UpdateFormulasWeb),
    (r'/update/formulas-rec/(.*)', UpdateFormulasRecursiveWeb),
]
