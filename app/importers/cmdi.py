# -*- coding: utf-8 -*-

from tornado import auth, web
from operator import itemgetter

import sys
import datetime
import logging
import json

import xmltodict

from main.helper import *
from main.db import *


class CmdiImport(myRequestHandler, Entity):
    """
    """
    @web.authenticated
    def post(self):
        cmdi = {}
        cmdi_xml            = self.get_argument('cmdi_xml', default=None, strip=True)
        parent_entity_id    = self.get_argument('parent_entity_id', default=None, strip=True)
        try:
            cmdi_dict = xmltodict.parse(cmdi_xml)
        except:
            self.write(str(sys.exc_info()[0]))
            raise
            return

        cmdi_CMD = cmdi_dict.get('CMD')
        if cmdi_CMD:
            cmdi['XSD'] = cmdi_CMD.get('@xsi:schemaLocation')
            # logging.debug(cmdi)
            cmdi_Components = cmdi_CMD.get('Components')
            if cmdi_Components:
                cmdi_Component = cmdi_Components.itervalues().next()
                cmdi['Component'] = cmdi_Components.keys()[0]
                cmdi_GeneralInfo = cmdi_Component.get('GeneralInfo')
                if cmdi_GeneralInfo:
                    if self.getXmlText(cmdi_GeneralInfo.get('ResourceName')):
                        cmdi['ResourceName'] = self.getXmlText(cmdi_GeneralInfo.get('ResourceName'))
                    if self.getXmlText(cmdi_GeneralInfo.get('LegalOwner')):
                        cmdi['LegalOwner'] = self.getXmlText(cmdi_GeneralInfo.get('LegalOwner'))
                    if self.getXmlText(cmdi_GeneralInfo.get('Version')):
                        cmdi['Version'] = self.getXmlText(cmdi_GeneralInfo.get('Version'))
                    if self.getXmlText(cmdi_GeneralInfo.get('LastUpdate')):
                        cmdi['LastUpdate'] = self.getXmlText(cmdi_GeneralInfo.get('LastUpdate'))

        entity_id = self.create_entity(entity_definition_keyname='cmdi', parent_entity_id=parent_entity_id)
        for k,v in cmdi.items():
            self.set_property(entity_id=entity_id, property_definition_keyname='cmdi-%s' % k, value=v)
        self.write(str(cmdi))
        return

    def getXmlText(self, node):
        if node:
            try:
                return node.get('#text')
            except Exception, e:
                return node
        return None


handlers = [
    ('/import/cmdi', CmdiImport),
]

