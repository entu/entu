from tornado import auth, web
from tornado import httpclient

import logging

from main.helper import *
from main.db import *


class SyncConfig(myRequestHandler, Entity):
    @web.authenticated
    def get(self):
        if self.current_user.get('email') not in ('mihkel.putrinsh@gmail.com', 'argo@roots.ee'):
            return


        #
        # conf-entity
        #

        # TODO:
        # only alter definitions of configurations, where user has at least editing rights
        self.db.execute('UPDATE entity_definition SET is_deleted = 1')
        self.db.execute('UPDATE property_definition SET is_deleted = 1')

        # TODO:
        # only alter definitions of configurations, where user has at least editing rights
        for conf_e in self.get_entities(entity_definition_keyname = 'conf-entity'):
            # logging.debug(conf_e)

            e_props = {}

            e_props['actions_add']    = conf_e.get('properties', {}).get('actions-add'    , {}).get('values', [{}])[0].get('db_value', None)
            e_props['description']    = conf_e.get('properties', {}).get('description'    , {}).get('values', [{}])[0].get('db_value', None)
            e_props['displayinfo']    = conf_e.get('properties', {}).get('displayinfo'    , {}).get('values', [{}])[0].get('db_value', None)
            e_props['displayname']    = conf_e.get('properties', {}).get('displayname'    , {}).get('values', [{}])[0].get('db_value', None)
            e_props['displaytable']   = conf_e.get('properties', {}).get('displaytable'   , {}).get('values', [{}])[0].get('db_value', None)
            e_props['is_deleted']     = conf_e.get('properties', {}).get('is-deleted'     , {}).get('values', [{}])[0].get('db_value', None)
            e_props['keyname']        = conf_e.get('properties', {}).get('keyname'        , {}).get('values', [{}])[0].get('db_value', None)
            e_props['label']          = conf_e.get('properties', {}).get('label'          , {}).get('values', [{}])[0].get('db_value', None)
            e_props['label_plural']   = conf_e.get('properties', {}).get('label-plural'   , {}).get('values', [{}])[0].get('db_value', None)
            e_props['menu']           = conf_e.get('properties', {}).get('menu-group'     , {}).get('values', [{}])[0].get('db_value', None)
            e_props['old_id']         = conf_e.get('properties', {}).get('old-id'         , {}).get('values', [{}])[0].get('db_value', None)
            e_props['open_after_add'] = conf_e.get('properties', {}).get('open-after-add' , {}).get('values', [{}])[0].get('db_value', None)
            e_props['ordinal']        = conf_e.get('properties', {}).get('ordinal'        , {}).get('values', [{}])[0].get('db_value', None)
            e_props['public']         = conf_e.get('properties', {}).get('public'         , {}).get('values', [{}])[0].get('db_value', None)
            e_props['public_path']    = conf_e.get('properties', {}).get('public_path'    , {}).get('values', [{}])[0].get('db_value', None)
            e_props['sort']           = conf_e.get('properties', {}).get('sort'           , {}).get('values', [{}])[0].get('db_value', None)

            # logging.debug(conf_e.get('properties', {}))

            if e_props['menu']:
                e_props['menu'] = self.get_entities(entity_id = e_props['menu'], limit = 1)['displayname']

            if e_props['keyname']:
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
                    , e_props['ordinal'], e_props['open_after_add'], e_props['public_path']
                    , e_props['label'], e_props['label_plural'], e_props['description'], e_props['menu'], e_props['public'], e_props['displayname']
                    , e_props['displayinfo'], e_props['displaytable'], e_props['sort']
                    , e_props['label'], e_props['label_plural'], e_props['description'], e_props['menu'], e_props['public'], e_props['displayname']
                    , e_props['displayinfo'], e_props['displaytable'], e_props['sort']
                    , e_props['actions_add']
                    , e_props['keyname']
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
                    , e_props['ordinal'], e_props['open_after_add'], e_props['public_path']
                    , e_props['label'], e_props['label_plural'], e_props['description'], e_props['menu'], e_props['public'], e_props['displayname']
                    , e_props['displayinfo'], e_props['displaytable'], e_props['sort']
                    , e_props['label'], e_props['label_plural'], e_props['description'], e_props['menu'], e_props['public'], e_props['displayname']
                    , e_props['displayinfo'], e_props['displaytable'], e_props['sort']
                    , e_props['actions_add']
                    )

            #
            # conf-property
            #

            childs = self.get_relatives(entity_id = conf_e['id'], relationship_definition_keyname = 'child', entity_definition_keyname = 'conf-property').values()
            if childs:
                for conf_p in childs[0]:
                # for conf_p in self.get_childs(entity_id = conf_e['id'], entity_definition_keyname = 'conf-property'):
                    # logging.debug(conf_p)
                    p_props = {}

                    p_props['autocomplete'] = conf_p.get('properties', {}).get('autocomplete' , {}).get('values', [{}])[0].get('db_value', None)
                    p_props['classifier']   = conf_p.get('properties', {}).get('classifier'   , {}).get('values', [{}])[0].get('db_value', None)
                    p_props['createonly']   = conf_p.get('properties', {}).get('createonly'   , {}).get('values', [{}])[0].get('db_value', None)
                    p_props['dataproperty'] = conf_p.get('properties', {}).get('dataproperty' , {}).get('values', [{}])[0].get('db_value', None)
                    p_props['datatype']     = conf_p.get('properties', {}).get('datatype'     , {}).get('values', [{}])[0].get('db_value', None)
                    p_props['defaultvalue'] = conf_p.get('properties', {}).get('defaultvalue' , {}).get('values', [{}])[0].get('db_value', None)
                    p_props['description']  = conf_p.get('properties', {}).get('description'  , {}).get('values', [{}])[0].get('db_value', None)
                    p_props['executable']   = conf_p.get('properties', {}).get('executable'   , {}).get('values', [{}])[0].get('db_value', None)
                    p_props['fieldset']     = conf_p.get('properties', {}).get('fieldset'     , {}).get('values', [{}])[0].get('db_value', None)
                    p_props['formatstring'] = conf_p.get('properties', {}).get('formatstring' , {}).get('values', [{}])[0].get('db_value', None)
                    p_props['formula']      = conf_p.get('properties', {}).get('formula'      , {}).get('values', [{}])[0].get('db_value', None)
                    p_props['label']        = conf_p.get('properties', {}).get('label'        , {}).get('values', [{}])[0].get('db_value', None)
                    p_props['label_plural'] = conf_p.get('properties', {}).get('label-plural' , {}).get('values', [{}])[0].get('db_value', None)
                    p_props['mandatory']    = conf_p.get('properties', {}).get('mandatory'    , {}).get('values', [{}])[0].get('db_value', None)
                    p_props['multilingual'] = conf_p.get('properties', {}).get('multilingual' , {}).get('values', [{}])[0].get('db_value', None)
                    p_props['multiplicity'] = conf_p.get('properties', {}).get('multiplicity' , {}).get('values', [{}])[0].get('db_value', None)
                    p_props['ordinal']      = conf_p.get('properties', {}).get('ordinal'      , {}).get('values', [{}])[0].get('db_value', None)
                    p_props['propagates']   = conf_p.get('properties', {}).get('propagates'   , {}).get('values', [{}])[0].get('db_value', None)
                    p_props['public']       = conf_p.get('properties', {}).get('public'       , {}).get('values', [{}])[0].get('db_value', None)
                    p_props['readonly']     = conf_p.get('properties', {}).get('readonly'     , {}).get('values', [{}])[0].get('db_value', None)
                    p_props['search']       = conf_p.get('properties', {}).get('search'       , {}).get('values', [{}])[0].get('db_value', None)
                    p_props['visible']      = conf_p.get('properties', {}).get('visible'      , {}).get('values', [{}])[0].get('db_value', None)

                    p_props['datatype']     = self.db.get('SELECT value_string FROM property WHERE is_deleted = 0 AND property_definition_keyname = \'conf-datatype-name\' AND entity_id = %s;' % p_props['datatype'])['value_string']
                    if not p_props['formula']:
                        p_props['formula']            = 0
                    if not p_props['executable']:
                        p_props['executable']         = 0
                    if not p_props['multilingual']:
                        p_props['multilingual']       = 0
                    if not p_props['readonly']:
                        p_props['readonly']           = 0
                    if not p_props['createonly']:
                        p_props['createonly']         = 0
                    if not p_props['propagates']:
                        p_props['propagates']         = 0
                    if not p_props['autocomplete']:
                        p_props['autocomplete']       = 0
                    if not p_props['mandatory']:
                        p_props['mandatory']          = 0
                    if not p_props['search']:
                        p_props['search']             = 0
                    if not p_props['public']:
                        p_props['public']             = 0

                    p_props['keyname']   = '%s-%s' % (e_props['keyname'], p_props['dataproperty'])
                    p_props['old_id']    = 'try01-%s' % p_props['keyname']

                    # logging.debug(p_props)

                    if p_props['classifier']:
                        p_props['classifier'] = self.get_entities(entity_id = p_props['classifier'], limit = 1)['displayname']

                    if p_props['keyname']:
                        self.db.execute("""
                            UPDATE `property_definition`
                            SET `entity_definition_keyname`=%s,
                                `dataproperty`=%s, `datatype`=%s, `defaultvalue`=%s,
                                `estonian_fieldset`=%s, `estonian_label`=%s, `estonian_label_plural`=%s, `estonian_description`=%s, `estonian_formatstring`=%s,
                                `english_fieldset`=%s, `english_label`=%s, `english_label_plural`=%s, `english_description`=%s, `english_formatstring`=%s,
                                `formula`=%s, `executable`=%s, `visible`=%s, `ordinal`=%s,
                                `multilingual`=%s, `multiplicity`=%s, `readonly`=%s, `createonly`=%s,
                                `public`=%s, `mandatory`=%s, `search`=%s, `propagates`=%s, `autocomplete`=%s,
                                `classifying_entity_definition_keyname`=%s, `is_deleted`=0,
                                `old_id`=%s
                            WHERE keyname = %s
                            ;
                            """
                            , e_props['keyname']
                            , p_props['dataproperty'], p_props['datatype'], p_props['defaultvalue']
                            , p_props['fieldset'], p_props['label'], p_props['label_plural'], p_props['description'], p_props['formatstring']
                            , p_props['fieldset'], p_props['label'], p_props['label_plural'], p_props['description'], p_props['formatstring']
                            , p_props['formula'], p_props['executable'], p_props['visible'], p_props['ordinal']
                            , p_props['multilingual'], p_props['multiplicity'], p_props['readonly'], p_props['createonly']
                            , p_props['public'], p_props['mandatory'], p_props['search'], p_props['propagates'], p_props['autocomplete']
                            , p_props['classifier']
                            , p_props['old_id']
                            , p_props['keyname']
                            )

                    else:
                        self.db.execute("""
                            INSERT INTO `property_definition` (
                                `keyname`, `entity_definition_keyname`,
                                `dataproperty`, `datatype`, `defaultvalue`,
                                `estonian_fieldset`, `estonian_label`, `estonian_label_plural`, `estonian_description`, `estonian_formatstring`,
                                `english_fieldset`, `english_label`, `english_label_plural`, `english_description`, `english_formatstring`,
                                `formula`, `executable`, `visible`, `ordinal`,
                                `multilingual`, `multiplicity`, `readonly`, `createonly`,
                                `public`, `mandatory`, `search`, `propagates`, `autocomplete`,
                                `classifying_entity_definition_keyname`, `is_deleted`, `old_id`)
                            VALUES (
                                %s, %s,
                                %s, %s, %s,
                                %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s,
                                %s, %s, %s, %s,
                                %s, %s, %s, %s,
                                %s, %s, %s, %s, %s,
                                %s, 0, NULL);
                            """
                            , 'conf-property-%i-%i' % (parent['id'], conf_p['id']), p_props['ed_keyname']
                            , p_props['dataproperty'], p_props['datatype'], p_props['defaultvalue']
                            , p_props['fieldset'], p_props['label'], p_props['label_plural'], p_props['description'], p_props['formatstring']
                            , p_props['fieldset'], p_props['label'], p_props['label_plural'], p_props['description'], p_props['formatstring']
                            , p_props['formula'], p_props['executable'], p_props['visible'], p_props['ordinal']
                            , p_props['multilingual'], p_props['multiplicity'], p_props['readonly'], p_props['createonly']
                            , p_props['public'], p_props['mandatory'], p_props['search'], p_props['propagates'], p_props['autocomplete']
                            , p_props['keyname']
                            )


handlers = [
    (r'/config/sync', SyncConfig),
]
