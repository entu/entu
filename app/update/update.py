from tornado import auth, web
from tornado import httpclient

import logging

from main.helper import *
from main.db import *


class UpdateFormulasWeb(myRequestHandler):
    @web.authenticated
    def get(self, entity_id):
        if self.current_user.get('email') != 'mihkel.putrinsh@gmail.com':
            return

        updateFormulas(entity_id=entity_id, user_locale=self.get_user_locale(), user_id=self.current_user.get('id'))


class UpdateFormulasByDefinitionWeb(myRequestHandler, Entity):
    @web.authenticated
    def get(self, entity_definition_keyname, dataproperty):
        if self.current_user.get('email') != 'mihkel.putrinsh@gmail.com':
            return

        # for row in db.Entity(user_locale=self.get_user_locale(), user_id=self.current_user.get('id')).get(entity_definition_keyname=entity_definition_keyname, dataproperty=dataproperty):
        for row in self.get_entities(entity_definition_keyname=entity_definition_keyname, dataproperty=dataproperty):
            logging.debug('ID: %s', str(row['id']))
            logging.debug('properties: %s', row['properties'])
            for p in row['properties'][dataproperty]['values']:
                logging.debug(p)
                self.set_property(entity_id=row['id'], old_property_id = p['id'], property_definition_keyname = row['properties'][dataproperty]['keyname'], value = p['db_value'])


class UpdateFormulasRecursiveWeb(myRequestHandler):
    @web.authenticated
    def get(self, entity_id):
        if self.current_user.get('email') != 'mihkel.putrinsh@gmail.com':
            return

        updateFormulasRecursive(entity_id=entity_id, user_locale=self.get_user_locale(), user_id=self.current_user.get('id'))


def updateFormulas(entity_id, user_locale, user_id):
    logging.debug('e:%s' % str(entity_id))
    for row in entity.formula_properties(entity_id = entity_id):
        # logging.debug('p:%s, f:%s' % (str(row.entity_id), row.value_formula))
        self.set_property(entity_id=entity_id, old_property_id = row.id, property_definition_keyname = row.property_definition_keyname, value = row.value_formula)


class updateValueReferenceDisplayField(myRequestHandler, Entity):
    @web.authenticated
    def get(self):
        if self.current_user.get('email') not in ['argoroots@gmail.com', 'mihkel.putrinsh@gmail.com']:
            return

        entities = self.get_entities(entity_id = [x.get('value_reference') for x in self.db.query('SELECT DISTINCT value_reference FROM property WHERE value_reference IS NOT NULL AND value_string IS NULL;') if x.get('value_reference')])

        if entities:
            for e in entities:
                # logging.debug(e.get('displayname',''))
                # logging.debug(e.get('id'))
                self.db.execute('UPDATE property SET value_string = %s WHERE value_reference = %s', e.get('displayname',''), e.get('id'))



def updateFormulasRecursive(entity_id, user_locale, user_id):
    updateFormulas(entity_id, user_locale, user_id)
    for e_id in self.get_relatives(ids_only=True, entity_id=entity_id, relationship_definition_keyname='child'):
        updateFormulasRecursive(e_id, user_locale, user_id)


handlers = [
    (r'/update/display-refence', updateValueReferenceDisplayField),
    (r'/update/formula/(.*)', UpdateFormulasWeb),
    (r'/update/formulas/(.*)/(.*)', UpdateFormulasByDefinitionWeb),
    (r'/update/formulas-rec/(.*)', UpdateFormulasRecursiveWeb),
]
