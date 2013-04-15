from tornado import auth, web
from tornado import httpclient

import logging

from main.helper import *
from main.db import *


class SyncConfig(myRequestHandler, Entity):
    @web.authenticated
    def get(self):
        if self.current_user.email != 'mihkel.putrinsh@gmail.com':
            return

        self.db.execute('UPDATE entity_definition SET is_deleted = 0')
        # logging.debug(self.db)

        for conf_e in self.get_entities(entity_definition_keyname = 'conf-entity'):

            eprops = {}

            eprops['keyname']        = conf_e.get('properties', {}).get('keyname'        , {}).get('values', [{}])[0].get('db_value', None)
            eprops['ordinal']        = conf_e.get('properties', {}).get('ordinal'        , {}).get('values', [{}])[0].get('db_value', None)
            eprops['open_after_add'] = conf_e.get('properties', {}).get('open-after-add' , {}).get('values', [{}])[0].get('db_value', None)
            eprops['public_path']    = conf_e.get('properties', {}).get('public_path'    , {}).get('values', [{}])[0].get('db_value', None)
            eprops['label']          = conf_e.get('properties', {}).get('label'          , {}).get('values', [{}])[0].get('db_value', None)
            eprops['label_plural']   = conf_e.get('properties', {}).get('label-plural'   , {}).get('values', [{}])[0].get('db_value', None)
            eprops['description']    = conf_e.get('properties', {}).get('description'    , {}).get('values', [{}])[0].get('db_value', None)
            eprops['menu']           = conf_e.get('properties', {}).get('menu-group'     , {}).get('values', [{}])[0].get('db_value', None)
            eprops['public']         = conf_e.get('properties', {}).get('public'         , {}).get('values', [{}])[0].get('db_value', None)
            eprops['displayname']    = conf_e.get('properties', {}).get('displayname'    , {}).get('values', [{}])[0].get('db_value', None)
            eprops['displayinfo']    = conf_e.get('properties', {}).get('displayinfo'    , {}).get('values', [{}])[0].get('db_value', None)
            eprops['displaytable']   = conf_e.get('properties', {}).get('displaytable'   , {}).get('values', [{}])[0].get('db_value', None)
            eprops['sort']           = conf_e.get('properties', {}).get('sort'           , {}).get('values', [{}])[0].get('db_value', None)
            eprops['actions_add']    = conf_e.get('properties', {}).get('actions-add'    , {}).get('values', [{}])[0].get('db_value', None)
            eprops['is_deleted']     = conf_e.get('properties', {}).get('is-deleted'     , {}).get('values', [{}])[0].get('db_value', None)
            eprops['old_id']         = conf_e.get('properties', {}).get('old-id'         , {}).get('values', [{}])[0].get('db_value', None)

            # logging.debug(conf_e.get('properties', {}))

            if eprops['menu']:
                eprops['menu'] = self.get_entities(entity_id = eprops['menu'], limit = 1)['displayname']

            if eprops['keyname']:
                self.db.execute("""
                    UPDATE `entity_definition`
                    SET ordinal=%s, open_after_add=%s, public_path=%s,
                        estonian_label=%s, estonian_label_plural=%s, estonian_description=%s, estonian_menu=%s, estonian_public=%s, estonian_displayname=%s,
                        estonian_displayinfo=%s, estonian_displaytable=%s, estonian_sort=%s,
                        english_label=%s, english_label_plural=%s, english_description=%s, english_menu=%s, english_public=%s, english_displayname=%s,
                        english_displayinfo=%s, english_displaytable=%s, english_sort=%s,
                        actions_add=%s, `is_deleted`=0
                    WHERE keyname = %s
                    ;
                    """
                    , eprops['ordinal'], eprops['open_after_add'], eprops['public_path']
                    , eprops['label'], eprops['label_plural'], eprops['description'], eprops['menu'], eprops['public'], eprops['displayname']
                    , eprops['displayinfo'], eprops['displaytable'], eprops['sort']
                    , eprops['label'], eprops['label_plural'], eprops['description'], eprops['menu'], eprops['public'], eprops['displayname']
                    , eprops['displayinfo'], eprops['displaytable'], eprops['sort']
                    , eprops['actions_add']
                    , eprops['keyname']
                    )

            else:
                self.db.execute("""
                    INSERT INTO `entity_definition` (
                        `keyname`,
                        `ordinal`, `open_after_add`, `public_path`,
                        `estonian_label`, `estonian_label_plural`, `estonian_description`, `estonian_menu`, `estonian_public`, `estonian_displayname`,
                        `estonian_displayinfo`, `estonian_displaytable`, `estonian_sort`,
                        `english_label`, `english_label_plural`, `english_description`, `english_menu`, `english_public`, `english_displayname`,
                        `english_displayinfo`, `english_displaytable`, `english_sort`,
                        `actions_add`, `is_deleted`, `old_id`)
                    VALUES (
                        %s,
                        %s, %s, %s,
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, 0, NULL)
                    ;
                    """
                    , 'conf-entity-%i' % conf_e['id']
                    , eprops['ordinal'], eprops['open_after_add'], eprops['public_path']
                    , eprops['label'], eprops['label_plural'], eprops['description'], eprops['menu'], eprops['public'], eprops['displayname']
                    , eprops['displayinfo'], eprops['displaytable'], eprops['sort']
                    , eprops['label'], eprops['label_plural'], eprops['description'], eprops['menu'], eprops['public'], eprops['displayname']
                    , eprops['displayinfo'], eprops['displaytable'], eprops['sort']
                    , eprops['actions_add']
                    )


class UpdateFormulasByDefinitionWeb(myRequestHandler):
    @web.authenticated
    def get(self, entity_definition_keyname, dataproperty):
        if self.current_user.email != 'mihkel.putrinsh@gmail.com':
            return

        for row in db.Entity(user_locale=self.get_user_locale(), user_id=self.current_user.id).get(entity_definition_keyname=entity_definition_keyname, dataproperty=dataproperty):
            logging.debug('ID: %s', str(row['id']))
            logging.debug('properties: %s', row['properties'])
            for p in row['properties'][dataproperty]['values']:
                logging.debug(p)
                db.Entity(user_locale=self.get_user_locale(), user_id=self.current_user.id).set_property(entity_id=row['id'], old_property_id = p['id'], property_definition_keyname = row['properties'][dataproperty]['keyname'], value = p['db_value'])


class UpdateFormulasRecursiveWeb(myRequestHandler):
    @web.authenticated
    def get(self, entity_id):
        if self.current_user.email != 'mihkel.putrinsh@gmail.com':
            return

        updateFormulasRecursive(entity_id=entity_id, user_locale=self.get_user_locale(), user_id=self.current_user.id)


def updateFormulas(entity_id, user_locale, user_id):
    logging.debug('e:%s' % str(entity_id))
    for row in entity.formula_properties(entity_id = entity_id):
        # logging.debug('p:%s, f:%s' % (str(row.entity_id), row.value_formula))
        self.set_property(entity_id=entity_id, old_property_id = row.id, property_definition_keyname = row.property_definition_keyname, value = row.value_formula)


def updateFormulasRecursive(entity_id, user_locale, user_id):
    updateFormulas(entity_id, user_locale, user_id)
    for e_id in self.get_relatives(ids_only=True, entity_id=entity_id, relationship_definition_keyname='child'):
        updateFormulasRecursive(e_id, user_locale, user_id)


handlers = [
    (r'/config/sync', SyncConfig),
]
