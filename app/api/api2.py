import hmac
import json
import datetime
import logging
import mimetypes
from hashlib import sha1
from operator import itemgetter

from PIL import Image
from StringIO import StringIO

from boto.s3.connection import S3Connection
from boto.s3.key import Key


from main.helper import *
from main.db import *
from main.db2 import *




class API2EntityList(myRequestHandler, Entity2):
    @web.removeslash
    def get(self):
        #
        # Get entity list
        #
        db_result = self.get_entities_info(
            definition = self.get_argument('definition', default=None, strip=True),
            query      = self.get_argument('query', default=None, strip=True),
            limit      = self.get_argument('limit', default=None, strip=True),
            page       = self.get_argument('page', default=None, strip=True)
        )

        result = {}
        for e in db_result.get('entities', []):
            result.setdefault(e.get('id'), {}).setdefault('definition', {})['keyname'] = e.get('definition') if e.get('definition') else None
            result.setdefault(e.get('id'), {}).setdefault('definition', {})['label'] = e.get('label') if e.get('label') else None
            result.setdefault(e.get('id'), {}).setdefault('definition', {})['label_plural'] = e.get('label_plural') if e.get('label_plural') else None
            result.setdefault(e.get('id'), {}).setdefault('definition', {})['table_header'] = e.get('displaytableheader').split('|') if e.get('displaytableheader') else None
            result.setdefault(e.get('id'), {})['id'] = e.get('id') if e.get('id') else None
            result.setdefault(e.get('id'), {})['sort'] = e.get('sort') if e.get('sort') else None
            result.setdefault(e.get('id'), {}).setdefault('changed', {})['dt'] = e.get('changed') if e.get('changed') else None
            result.setdefault(e.get('id'), {}).setdefault('changed', {})['ts'] = e.get('changed_ts') if e.get('changed_ts') else None
            result.setdefault(e.get('id'), {})['name'] = e.get('displayname') if e.get('displayname') else None
            result.setdefault(e.get('id'), {})['info'] = e.get('displayinfo') if e.get('displayinfo') else None
            result.setdefault(e.get('id'), {})['table'] = e.get('displaytable').split('|') if e.get('displaytable') else None

        self.json({
            'result': sorted(result.values(), key=itemgetter('sort')),
            'time': round(self.request.request_time(), 3),
            'count': db_result.get('count', 0),
        })




class API2CmdiXml(myRequestHandler, Entity):
    @web.removeslash
    def get(self, entity_id=None):
        if not entity_id:
            return self.json({
                'error': 'No entity ID!',
                'time': round(self.request.request_time(), 3),
            }, 400)

        entity = self.get_entities(entity_id=entity_id, limit=1)
        if not entity:
            return self.json({
                'error': 'Entity with given ID is not found!',
                'time': round(self.request.request_time(), 3),
            }, 404)
        entity['definition'] = {'keyname': entity['definition_keyname']}

        xml = """<?xml version="1.0" encoding="UTF-8"?>
            <CMD xmlns="http://www.clarin.eu/cmd/"
                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                 CMDVersion="1.1"
                 xsi:schemaLocation="%(XSD)s">
                <Header></Header>
                <Resources>
                    <ResourceProxyList></ResourceProxyList>
                    <JournalFileProxyList></JournalFileProxyList>
                    <ResourceRelationList></ResourceRelationList>
                </Resources>
                <Components>
                    <%(Component)s>
                        <GeneralInfo>
                            <ResourceName xml:lang="en">%(ResourceName)s</ResourceName>
                            <Version xml:lang="en">%(Version)s</Version>
                            <LastUpdate>%(LastUpdate)s</LastUpdate>
                            <LegalOwner xml:lang="en">%(LegalOwner)s</LegalOwner>
                        </GeneralInfo>
                    </%(Component)s>
                </Components>
            </CMD>""" % {
                'XSD'          : entity['properties']['XSD'].get('values',[{'value':''}])[0]['value'],
                'Component'    : entity['properties']['Component'].get('values',[{'value':''}])[0]['value'],
                'ResourceName' : entity['properties']['ResourceName'].get('values',[{'value':''}])[0]['value'],
                'Version'      : entity['properties']['Version'].get('values',[{'value':''}])[0]['value'],
                'LastUpdate'   : entity['properties']['LastUpdate'].get('values',[{'value':''}])[0]['value'],
                'LegalOwner'   : entity['properties']['LegalOwner'].get('values',[{'value':''}])[0]['value'],
            }

        mimetypes.init()
        mime = mimetypes.types_map.get('.xml', 'application/octet-stream')
        filename = 'entu-cmd-%s.xml' % entity_id
        self.add_header('Content-Type', mime)
        # self.add_header('Content-Disposition', 'attachment; filename="%s"' % filename)
        self.write(xml)




class API2Entity(myRequestHandler, Entity):
    @web.removeslash
    def get(self, entity_id=None):
        #
        # Get entity (with given ID)
        #
        if not entity_id:
            return self.json({
                'error': 'No entity ID!',
                'time': round(self.request.request_time(), 3),
            }, 400)

        try:
            entity = self.get_entities(entity_id=entity_id, limit=1)
        except Exception, e:
            return self.json({
                'error': 'Something is wrong here!',
                'time': round(self.request.request_time(), 3),
            }, 500)

        if not entity:
            return self.json({
                'error': 'Entity with given ID is not found!',
                'time': round(self.request.request_time(), 3),
            }, 404)
        entity['definition'] = {'keyname': entity['definition_keyname']}

        self.json({
            'result': entity,
            'time': round(self.request.request_time(), 3),
        })


    @web.removeslash
    def put(self, entity_id=None):
        #
        # Change entity (with given ID) properties
        #
        if not self.current_user:
            return self.json({
                'error': 'Forbidden!',
                'time': round(self.request.request_time(), 3),
            }, 403)

        if not entity_id:
            return self.json({
                'error': 'No entity ID!',
                'time': round(self.request.request_time(), 3),
            }, 400)

        # entity = self.get_entities(entity_id=entity_id, limit=1)
        # if not entity:
        #     return self.json({
        #         'error': 'Entity with given ID is not found!',
        #         'time': round(self.request.request_time(), 3),
        #     }, 404)

        for dataproperty, value in self.request.arguments.iteritems():
            if dataproperty in ['user', 'policy', 'signature']:
                continue

            if '.' in dataproperty:
                property_definition_keyname = dataproperty.split('.')[0]
                old_property_id = dataproperty.split('.')[1]
            else:
                property_definition_keyname = dataproperty
                old_property_id = None

            if type(value) is not list:
                value = [value]

            new_properties = {}
            for v in value:
                new_property_id = self.set_property(entity_id=entity_id, old_property_id=old_property_id, property_definition_keyname=property_definition_keyname, value=v)
                if new_property_id:
                    new_properties.setdefault(property_definition_keyname, []).append({'id': new_property_id, 'value': v})

        self.json({
            'result': {
                'id': entity_id,
                'properties': new_properties
            },
            'time': round(self.request.request_time(), 3),
        }, 201)


    @web.removeslash
    def post(self, entity_id=None):
        #
        # Create new child entity (under entity with given ID)
        #
        if not self.current_user:
            return self.json({
                'error': 'Forbidden!',
                'time': round(self.request.request_time(), 3),
            }, 403)

        if not entity_id:
            return self.json({
                'error': 'No entity ID!',
                'time': round(self.request.request_time(), 3),
            }, 400)

        entity = self.get_entities(entity_id=entity_id, limit=1)
        if not entity:
            return self.json({
                'error': 'Entity with given ID is not found!',
                'time': round(self.request.request_time(), 3),
            }, 404)

        definition = self.get_argument('definition', default=None, strip=True)
        if not definition:
            return self.json({
                'error': 'No definition!',
                'time': round(self.request.request_time(), 3),
            }, 400)

        entity_id = self.create_entity(entity_definition_keyname=definition, parent_entity_id=entity_id)

        for dataproperty, value in self.request.arguments.iteritems():
            if dataproperty in ['user', 'policy', 'signature', 'definition']:
                continue
            if type(value) is not list:
                value = [value]
            for v in value:
                new_property_id = self.set_property(entity_id=entity_id, property_definition_keyname=dataproperty, value=v)

        self.json({
            'result': {
                'id': entity_id,
            },
            'time': round(self.request.request_time(), 3),
        }, 201)


    @web.removeslash
    def delete(self, entity_id=None):
        #
        # Delete entity (with given ID)
        #
        if not entity_id:
            return self.json({
                'error': 'No entity ID!',
                'time': round(self.request.request_time(), 3),
            }, 400)

        result = self.delete_entity(entity_id=entity_id)
        if not result:
            return self.json({
                'error': 'Forbidden!',
                'time': round(self.request.request_time(), 3),
            }, 403)

        self.json({
            'result': {
                'id': entity_id,
            },
            'time': round(self.request.request_time(), 3),
        })




class API2EntityChilds(myRequestHandler, Entity2):
    @web.removeslash
    def get(self, entity_id=None):
        if not entity_id:
            return self.json({
                'error': 'No entity ID!',
                'time': round(self.request.request_time(), 3),
            }, 400)

        db_result = self.get_entities_info(
            parent_entity_id = entity_id,
            definition = self.get_argument('definition', default=None, strip=True),
            query      = self.get_argument('query', default=None, strip=True),
            limit      = self.get_argument('limit', default=None, strip=True),
            page       = self.get_argument('page', default=None, strip=True)
        )

        result = {}
        for e in db_result.get('entities', []):
            result.setdefault(e.get('definition'), {})['definition'] = e.get('definition') if e.get('definition') else None
            result.setdefault(e.get('definition'), {})['label'] = e.get('label') if e.get('label') else None
            result.setdefault(e.get('definition'), {})['label_plural'] = e.get('label_plural') if e.get('label_plural') else None
            result.setdefault(e.get('definition'), {})['table_header'] = e.get('displaytableheader').split('|') if e.get('displaytableheader') else None
            result.setdefault(e.get('definition'), {}).setdefault('entities', {}).setdefault(e.get('id'), {})['id'] = e.get('id') if e.get('id') else None
            result.setdefault(e.get('definition'), {}).setdefault('entities', {}).setdefault(e.get('id'), {})['sort'] = e.get('sort') if e.get('sort') else None
            result.setdefault(e.get('definition'), {}).setdefault('entities', {}).setdefault(e.get('id'), {})['name'] = e.get('displayname') if e.get('displayname') else None
            result.setdefault(e.get('definition'), {}).setdefault('entities', {}).setdefault(e.get('id'), {})['info'] = e.get('displayinfo') if e.get('displayinfo') else None
            result.setdefault(e.get('definition'), {}).setdefault('entities', {}).setdefault(e.get('id'), {})['table'] = e.get('displaytable').split('|') if e.get('displaytable') else None
        for r in result.values():
            r['entities'] = sorted(r.get('entities', {}).values(), key=itemgetter('sort'))

        self.json({
            'result': result,
            'time': round(self.request.request_time(), 3),
            'count': db_result.get('count', 0),
        })




class API2EntityReferrals(myRequestHandler, Entity2):
    @web.removeslash
    def get(self, entity_id=None):
        if not entity_id:
            return self.json({
                'error': 'No entity ID!',
                'time': round(self.request.request_time(), 3),
            }, 400)

        db_result = self.get_entities_info(
            referred_to_entity_id = entity_id,
            definition = self.get_argument('definition', default=None, strip=True),
            query      = self.get_argument('query', default=None, strip=True),
            limit      = self.get_argument('limit', default=None, strip=True),
            page       = self.get_argument('page', default=None, strip=True)
        )

        result = {}
        for e in db_result.get('entities', []):
            result.setdefault(e.get('definition'), {})['definition'] = e.get('definition') if e.get('definition') else None
            result.setdefault(e.get('definition'), {})['label'] = e.get('label') if e.get('label') else None
            result.setdefault(e.get('definition'), {})['label_plural'] = e.get('label_plural') if e.get('label_plural') else None
            result.setdefault(e.get('definition'), {})['table_header'] = e.get('displaytableheader').split('|') if e.get('displaytableheader') else None
            result.setdefault(e.get('definition'), {}).setdefault('entities', {}).setdefault(e.get('id'), {})['id'] = e.get('id') if e.get('id') else None
            result.setdefault(e.get('definition'), {}).setdefault('entities', {}).setdefault(e.get('id'), {})['sort'] = e.get('sort') if e.get('sort') else None
            result.setdefault(e.get('definition'), {}).setdefault('entities', {}).setdefault(e.get('id'), {})['name'] = e.get('displayname') if e.get('displayname') else None
            result.setdefault(e.get('definition'), {}).setdefault('entities', {}).setdefault(e.get('id'), {})['info'] = e.get('displayinfo') if e.get('displayinfo') else None
            result.setdefault(e.get('definition'), {}).setdefault('entities', {}).setdefault(e.get('id'), {})['table'] = e.get('displaytable').split('|') if e.get('displaytable') else None
        for r in result.values():
            r['entities'] = sorted(r.get('entities', {}).values(), key=itemgetter('sort'))

        self.json({
            'result': result,
            'time': round(self.request.request_time(), 3),
            'count': db_result.get('count', 0),
        })




class API2File(myRequestHandler, Entity):
    @web.removeslash
    def get(self, file_id=None):
        #
        # Get file (with given ID)
        #
        if not file_id:
            return self.json({
                'error': 'No file ID!',
                'time': round(self.request.request_time(), 3),
            }, 400)

        files = self.get_file(file_id)
        if not files:
            return self.json({
                'error': 'File with given ID is not found!',
                'time': round(self.request.request_time(), 3),
            }, 404)

        if not files[0].get('file'):
            return self.json({
                'error': 'No file!',
                'time': round(self.request.request_time(), 3),
            }, 400)

        if files[0].get('url'):
            return self.redirect(files[0].get('file'))

        mimetypes.init()
        mime = mimetypes.types_map.get('.%s' % files[0].get('filename').lower().split('.')[-1], 'application/octet-stream')

        filename = files[0].get('filename')

        self.add_header('Content-Type', mime)
        self.add_header('Content-Disposition', 'inline; filename="%s"' % filename)
        self.write(files[0].get('file'))

    @web.removeslash
    def delete(self, file_id=None):
        #
        # Delete file (with given ID)
        #
        pass




class API2FileUpload(myRequestHandler, Entity):
    @web.removeslash
    def post(self):
        #
        # Upload/create file
        #
        if not self.current_user:
            return self.json({
                'error': 'Forbidden!',
                'time': round(self.request.request_time(), 3),
            }, 403)

        if self.request.headers.get('Content-Type', '').startswith('multipart/form-data'):
            uploaded_file = self.request.files.get('file', [{}])[0].body
        else:
            uploaded_file = self.request.body

        if not uploaded_file:
            return self.json({
                'error': 'No file!',
                'time': round(self.request.request_time(), 3),
            }, 400)

        if not self.request.headers.get('Content-Type', '').startswith('multipart/form-data'):
            try:
                file_size = int(self.request.headers.get('Content-Length', 0))
            except Exception:
                return self.json({
                    'error': 'Content-Length header not set!',
                    'time': round(self.request.request_time(), 3),
                }, 403)

            if file_size != len(uploaded_file):
                return self.json({
                    'error': 'File not complete!',
                    'time': round(self.request.request_time(), 3),
                }, 400)

        entity_id = self.get_argument('entity', default=None, strip=True)
        if not entity_id:
            return self.json({
                'error': 'No entity ID!',
                'time': round(self.request.request_time(), 3),
            }, 400)

        # entity = self.get_entities(entity_id=entity_id, limit=1)
        # if not entity:
        #     return self.json({
        #         'error': 'Entity with given ID is not found!',
        #         'time': round(self.request.request_time(), 3),
        #     }, 404)

        property_definition_keyname = self.get_argument('property', default=None, strip=True)
        if not property_definition_keyname:
            return self.json({
                'error': 'No property!',
                'time': round(self.request.request_time(), 3),
            }, 400)

        filename = self.get_argument('filename', default=None, strip=True)
        if not filename:
            return self.json({
                'error': 'No filename!',
                'time': round(self.request.request_time(), 3),
            }, 400)

        new_property_id = self.set_property(entity_id=entity_id, property_definition_keyname=property_definition_keyname, value={'filename': filename, 'body': uploaded_file})
        if new_property_id:
            properties = {property_definition_keyname: [{'id': new_property_id, 'value': filename}]}
        else:
            properties = None

        self.json({
            'result': {
                'id': entity_id,
                'properties': properties
            },
            'time': round(self.request.request_time(), 3),
        })




class API2EntityPicture(myRequestHandler, Entity2):
    @web.removeslash
    def get(self, entity_id=None):
        # im = Image.open(StringIO(data))
        picture = self.get_entity_picture(entity_id)

        if not picture:
            return self.redirect('https://secure.gravatar.com/avatar/%s?d=identicon&s=150' % (hashlib.md5(str(entity_id)).hexdigest()))

        if picture.get('thumbnail'):
            self.add_header('Content-Type', 'image/jpeg')
            return self.write(picture.get('thumbnail'))

        elif picture.get('file'):
            thumbnail = None
            # try:

            size = (300, 300)
            im = Image.open(StringIO(picture.get('file')))

            if im.size[0] < size[0] and im.size[1] < size[1]:
                aspect = float(im.size[0])/float(im.size[1])
                c = (aspect, 1) if aspect > 0 else (1, aspect)
                im = im.resize((int(im.size[0]*size[0]/im.size[0]*c[0]), int(im.size[1]*size[1]/im.size[1]*c[1])), Image.ANTIALIAS)
            else:
                im.thumbnail(size, Image.ANTIALIAS)

            im_bg = Image.new('RGB', size, (255, 255, 255))
            try:
                im_bg.paste(im, ((size[0] - im.size[0]) / 2, (size[1] - im.size[1]) / 2), im)
            except Exception:
                im_bg.paste(im, ((size[0] - im.size[0]) / 2, (size[1] - im.size[1]) / 2))


            im_new = StringIO()
            im_bg.save(im_new, 'JPEG', quality=75)

            thumbnail = im_new.getvalue()

            # except Exception:
            #     return

            if thumbnail:
                self.set_file_thumbnail(picture.get('id'), thumbnail)

                self.add_header('Content-Type', 'image/jpeg')
                return self.write(thumbnail)

        elif picture.get('definition', '') == 'person':
            return self.redirect('https://secure.gravatar.com/avatar/%s?d=wavatar&s=150' % (hashlib.md5(str(entity_id)).hexdigest()))

        elif picture.get('definition', '') in ['audiovideo', 'book', 'methodical', 'periodical', 'textbook', 'workbook']:
            return self.redirect('/photo-by-isbn?entity=%s' % entity_id)

        else:
            return self.redirect('https://secure.gravatar.com/avatar/%s?d=identicon&s=150' % (hashlib.md5(str(entity_id)).hexdigest()))




class API2EntityRights(myRequestHandler, Entity2):
    def post(self, entity_id):
        if not self.current_user:
            return self.json({
                'error': 'Forbidden!',
                'time': round(self.request.request_time(), 3),
            }, 403)

        if not entity_id:
            return self.json({
                'error': 'No entity ID!',
                'time': round(self.request.request_time(), 3),
            }, 400)

        right = self.get_argument('right', default=None, strip=True)
        if right and right not in ['viewer', 'expander', 'editor', 'owner']:
            return self.json({
                'error': 'Right type must be set!',
                'time': round(self.request.request_time(), 3),
            }, 400)

        related_entity_id = self.get_argument('entity', default=None, strip=True)
        if not related_entity_id:
            return self.json({
                'error': 'Entity ID must be set!',
                'time': round(self.request.request_time(), 3),
            }, 400)

        response = self.set_entity_right(entity_id=entity_id, related_entity_id=related_entity_id, right=right)

        self.json({
            'result': response,
            'time': round(self.request.request_time(), 3),
        })



class API2EntityShare(myRequestHandler, Entity):
    def post(self, entity_id):
        if not self.current_user:
            return self.json({
                'error': 'Forbidden!',
                'time': round(self.request.request_time(), 3),
            }, 403)

        to = StrToList(self.get_argument('to', default=None, strip=True))
        if not to:
            return self.json({
                'error': 'To address must be set!',
                'time': round(self.request.request_time(), 3),
            }, 404)

        if not entity_id:
            return self.json({
                'error': 'No entity ID!',
                'time': round(self.request.request_time(), 3),
            }, 400)

        entity = self.get_entities(entity_id=entity_id, limit=1)
        if not entity:
            return self.json({
                'error': 'Entity with given ID is not found!',
                'time': round(self.request.request_time(), 3),
            }, 404)

        url = 'https://%s/entity/%s/%s' % (self.request.headers.get('Host'), entity.get('definition_keyname', ''), entity.get('id'))

        message = self.get_argument('message', default='', strip=True)

        response = self.mail_send(
            to = to,
            subject = entity.get('displayname', ''),
            message = '%s\n\n%s\n\n%s\n%s' % (message, url, self.current_user.get('name', ''), self.current_user.get('email', '')),
            html = False
        )

        self.json({
            'result': response,
            'time': round(self.request.request_time(), 3),
        })




class API2Email(myRequestHandler, Entity2):
    def get(self):
        pass


    def post(self):
        if not self.current_user:
            return self.json({
                'error': 'Forbidden!',
                'time': round(self.request.request_time(), 3),
            }, 403)

        to = self.get_argument('to', default=None, strip=True)
        if not to:
            return self.json({
                'error': 'To address must be set!',
                'time': round(self.request.request_time(), 3),
            }, 400)

        subject = self.get_argument('subject', default=None, strip=True)
        if not subject:
            return self.json({
                'error': 'Subject must be set!',
                'time': round(self.request.request_time(), 3),
            }, 400)

        message = self.get_argument('message', default=None, strip=True)
        if not message:
            return self.json({
                'error': 'Message must be set!',
                'time': round(self.request.request_time(), 3),
            }, 400)

        campaign = self.get_argument('campaign', default=None, strip=True)

        response = self.mail_send(
            to = to,
            subject = subject,
            message = message,
            html = True,
            campaign = campaign
        )

        self.json({
            'result': response,
            'time': round(self.request.request_time(), 3),
        })




class API2DefinitionList(myRequestHandler, Entity2):
    @web.removeslash
    def get(self):
        menu = self.get_menu()

        self.json({
            'result': menu,
            'time': round(self.request.request_time(), 3),
        })




class API2Definition(myRequestHandler, Entity2):
    @web.removeslash
    def get(self, definition_id=None):
        if not definition_id:
            return self.json({
                'error': 'No definition ID!',
                'time': round(self.request.request_time(), 3),
            }, 400)

        definitions = self.get_entity_definitions(definition_id=definition_id)
        if not definitions:
            return self.json({
                'error': 'Definition with given ID is not found!',
                'time': round(self.request.request_time(), 3),
            }, 404)

        self.json({
            'result': definitions,
            'time': round(self.request.request_time(), 3),
        })




class API2NotFound(myRequestHandler, Entity2):
    #
    # Nice error if API method not found
    #
    def get(self, url):
        self.json({
            'error': '\'%s\' not found' % url,
            'time': round(self.request.request_time(), 3),
        }, 404)

    def put(self, url):
        self.get(url)

    def post(self, url):
        self.get(url)

    def delete(self, url):
        self.get(url)










class S3FileUpload(myRequestHandler):
    def get(self, entity_id=None, property_id=None):
        AWS_BUCKET     = self.app_settings('auth-s3', '\n', True).split('\n')[0]
        AWS_ACCESS_KEY = self.app_settings('auth-s3', '\n', True).split('\n')[1]
        AWS_SECRET_KEY = self.app_settings('auth-s3', '\n', True).split('\n')[2]

        bucket = self.get_argument('bucket', None, True)
        key = self.get_argument('key', None, True)
        etag = self.get_argument('etag', None, True)
        message = self.get_argument('message', None, True)

        if bucket and key and etag:
            s3_conn   = S3Connection(AWS_ACCESS_KEY, AWS_SECRET_KEY)
            s3_bucket = s3_conn.get_bucket(bucket, validate=False)
            s3_key    = s3_bucket.get_key(key)
            s3_url    = s3_key.generate_url(expires_in=10, query_auth=True)

            self.json({
                'bucket': bucket,
                'key': key,
                'etag': etag,
                'message': message,
                'url': s3_url,
            })
        else:
            file_type = self.get_argument('file_type', None, True)
            if not file_type:
                file_type = 'binary/octet-stream'

            key = '%s/%s' % (self.app_settings('database-name'), datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
            policy = {
                'expiration': (datetime.datetime.utcnow()+datetime.timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%SZ'),
                'conditions': [
                    {'bucket': AWS_BUCKET},
                    ['starts-with', '$key', key],
                    {'acl': 'private'},
                    {'success_action_status': '201'},
                    {'x-amz-server-side-encryption': 'AES256'},
                    {'Content-Type': file_type},
                ]
            }
            encoded_policy = json.dumps(policy).encode('utf-8').encode('base64').replace('\n','')
            signature = hmac.new(str(AWS_SECRET_KEY), str(encoded_policy), sha1).digest().encode('base64').replace('\n','')

            self.json({
                'url': 'https://%s.s3.amazonaws.com/' % AWS_BUCKET,
                'data': {
                    'key':                          '%s/${filename}' % key,
                    'acl':                          'private',
                    'success_action_status':        '201',
                    'x-amz-server-side-encryption': 'AES256',
                    'AWSAccessKeyId':               AWS_ACCESS_KEY,
                    'policy':                       encoded_policy,
                    'signature':                    signature,
                    'Content-Type':                 file_type,
                }
            })




handlers = [
    (r'/api2/entity', API2EntityList),
    (r'/api2/entity-(.*)/childs', API2EntityChilds),
    (r'/api2/entity-(.*)/referrals', API2EntityReferrals),
    (r'/api2/entity-(.*)/picture', API2EntityPicture),
    (r'/api2/entity-(.*)/rights', API2EntityRights),
    (r'/api2/entity-(.*)/share', API2EntityShare),
    (r'/api2/entity-(.*)', API2Entity),
    (r'/api2/file', API2FileUpload),
    (r'/api2/file/aws', S3FileUpload),
    (r'/api2/file-(.*)', API2File),
    (r'/api2/definition', API2DefinitionList),
    (r'/api2/definition-(.*)', API2Definition),
    (r'/api2/cmdi-xml/(.*)', API2CmdiXml),
    (r'/api2/email', API2Email),
    (r'/api2(.*)', API2NotFound),
]
