from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import blobstore
from google.appengine.api import images
from datetime import *
from operator import attrgetter
from operator import itemgetter

import hashlib
import time

from bo import *
from database.dictionary import *
from database.person import *


class Counter(ChangeLogModel):
    name            = db.ReferenceProperty(Dictionary, collection_name='counter_name')
    value           = db.IntegerProperty(default=0)
    value_property  = db.StringProperty()
    increment       = db.IntegerProperty(default=1)

    @property
    def displayname(self):
        return self.name.value


def GetCounterNextValue(counter_key):
    c = Counter().get(counter_key)
    c.value += c.increment
    c.put()
    return c.value


class Bubble(ChangeLogModel):
    x_search                = db.StringListProperty()
    x_sort_estonian         = db.StringProperty(default='')
    x_sort_english          = db.StringProperty(default='')
    # x_type                  = db.ReferenceProperty()
    type                    = db.StringProperty()
    # optional_bubbles        = db.ListProperty(db.Key)

    @property
    def y_type(self):
        return self.type

    @property
    def displayname(self):
        try:
            bt = self.GetType()

            if not hasattr(bt, 'property_displayname'):
                return ''

            cache_key = 'bubble_dname_' + UserPreferences().current.language + '_' + str(self.key())
            dname = Cache().get(cache_key)
            if dname:
                return dname

            dname = getattr(bt, 'property_displayname', '')
            for data_property in FindTags(dname, '@', '@'):
                t = self.GetProperty(bubbletype = bt, data_property = data_property)
                dname = dname.replace('@%s@' % data_property, ', '.join(['%s' % n['value'] for n in t['values'] if n['value']]))

            Cache().set(cache_key, dname)
            return dname
        except Exception, e:
            logging.error('Bubble().displayname: %s' % e)

    @property
    def displayinfo(self):
        try:
            bt = self.GetType()

            if not hasattr(bt, 'property_displayinfo'):
                return ''

            cache_key = 'bubble_dinfo_' + UserPreferences().current.language + '_' + str(self.key())
            dinfo = Cache().get(cache_key)
            if dinfo:
                return dinfo

            dinfo = getattr(bt, 'property_displayinfo', '')
            for data_property in FindTags(dinfo, '@', '@'):
                t = self.GetProperty(bubbletype = bt, data_property = data_property)
                dinfo = dinfo.replace('@%s@' % data_property, ', '.join(['%s' % n['value'] for n in t['values'] if n['value']]))

            Cache().set(cache_key, dinfo)
            return dinfo
        except Exception, e:
            logging.error('Bubble().displayinfo: %s' % e)

    @property
    def displaycount(self):
        try:
            bt = self.GetType()

            if not hasattr(bt, 'property_displaycount'):
                return

            return len(self.GetValueAsList(getattr(bt, 'property_displaycount')))
        except Exception, e:
            logging.error('Bubble().displaycount: %s' % e)

    @property
    def public_key(self):
        if not getattr(self, 'x_public_key', None):
            self.x_public_key = hashlib.md5(str(self.key()) + str(time.time())).hexdigest()
            self.put()
        return self.x_public_key

    def AutoFix(self):
        bt = self.GetType()
        do_put = False

        # Set x_sort_... and x_search_...
        try:
            search = []
            for language in SystemPreferences().get('languages'):
                sorts = getattr(bt, 'sort_string', '')
                for data_property in FindTags(sorts, '@', '@'):
                    t = self.GetProperty(bubbletype = bt, data_property = data_property, language = language)
                    if t['data_type'] in ['date', 'datetime']:
                        sorts = sorts.replace('@%s@' % data_property, ', '.join(['%s' % n['forsort'] for n in t['values'] if n['forsort']]))
                    elif t['data_type'] in ['integer', 'float']:
                        sorts = sorts.replace('@%s@' % data_property, ', '.join(['%09d' % n['value'] for n in t['values'] if n['value']]))
                    else:
                        sorts = sorts.replace('@%s@' % data_property, ', '.join(['%s' % n['value'] for n in t['values'] if n['value']]))
                sorts = StringToSortable(sorts)
                if sorts != getattr(self, 'x_sort_%s' % language, ''):
                    setattr(self, 'x_sort_%s' % language, sorts)
                    do_put = True

                searchl = []
                for bp in Bubble().get(bt.GetValueAsList('search_properties')):
                    if hasattr(bp, 'data_property'):
                        t = self.GetProperty(bubbletype = bt, data_property = bp.data_property, language = language)
                        for s in ['%s' % n['value'] for n in t['values'] if n['value']]:
                            searchl = ListMerge(searchl, StringToSearchIndex(s))

                search = ListMerge(search, ['%s:%s' % (language, l) for l in searchl if l])

                if hasattr(self, 'x_search_%s' % language):
                    delattr(self, 'x_search_%s' % language)

            if len(search) > 0:
                if search != getattr(self, 'x_search', []):
                    setattr(self, 'x_search', search)
                    do_put = True
            else:
                if hasattr(self, 'x_search'):
                    delattr(self, 'x_search')
                    do_put = True

            for key in self.dynamic_properties():
                value = getattr(self, key)
                if type(value) is list:
                    if len(value) == 1:
                        setattr(self, key, value[0])
                        do_put = True

            if do_put == True:
                self.put('autofix')
        except Exception, e:
            logging.error('AutoFix ERROR (%s): %s' % (str(self.key()), e))
            pass

    def Authorize(self, type):
        if users.is_current_user_admin():
            return True
        if type == 'owner':
            allowed = ['owner']
        if type == 'editor':
            allowed = ['owner', 'editor']
        if type == 'subbubbler':
            allowed = ['owner', 'editor', 'subbubbler']
        if type == 'viewer':
            allowed = ['owner', 'editor', 'subbubbler', 'viewer']
        if self.GetMyRole() in allowed:
            return True
        else:
            return False

    def GetMyRole(self):
        if users.is_current_user_admin():
            return 'owner'
        if CurrentUser().key() in self.GetValueAsList('x_br_owner'):
            return 'owner'
        if CurrentUser().key() in self.GetValueAsList('x_br_editor'):
            return 'editor'
        if CurrentUser().key() in self.GetValueAsList('x_br_subbubbler'):
            return 'subbubbler'
        if CurrentUser().key() in self.GetValueAsList('x_br_viewer'):
            return 'viewer'

    def CanEdit(self):
        # return True if self.GetMyRole() in ['owner', 'editor'] else False
        return True if self.GetMyRole() in ['owner', 'editor', 'subbubbler', 'viewer'] else False

    def CanAddSubbubble(self):
        # return True if self.GetMyRole() in ['owner', 'editor', 'subbubbler'] else False
        return True if self.GetMyRole() in ['owner', 'editor', 'subbubbler', 'viewer'] else False

    def AddRight(self, person_keys, right=None, user=None):
        rights = ['viewer', 'subbubbler', 'editor', 'owner']

        if type(person_keys) is not list:
            person_keys = [person_keys]

        # Remove rights
        for r in rights:
            if ListMatch(self.GetValueAsList('x_br_%s' % r), person_keys):
                self.RemoveValue('x_br_%s' % r, person_keys)
                self.put(user)

        # Add rights
        if right:
            self.AddValue('x_br_%s' % right, person_keys)
            self.put(user)

        # Remove BubbleRelation
        for pk in person_keys:
            for br in db.Query(BubbleRelation).filter('bubble', self.key()).filter('related_bubble', pk).filter('type IN', rights).filter('x_is_deleted', False).fetch(100):
                br.x_is_deleted = True
                br.put(user)

        # Set BubbleRelation
        if right:
            for pk in person_keys:
                br = db.Query(BubbleRelation).filter('bubble', self.key()).filter('related_bubble', pk).filter('type', right).get()
                if not br:
                    br = BubbleRelation()
                    br.bubble = self.key()
                    br.related_bubble = pk
                br.type = right
                br.x_is_deleted = False
                br.put(user)

    def GetPhotoUrl(self, size = 150, square = False):
        blob_key = getattr(self, 'photo', None)
        if blob_key:
            b = blobstore.BlobInfo.get(blob_key)
            if b:
                if b.content_type in ['image/bmp', 'image/jpeg', 'image/pjpeg', 'image/png', 'image/gif', 'image/tiff', 'image/x-icon']:
                    url = images.get_serving_url(b.key())
                    sq = '-c' if square else ''
                    if size:
                        url += '=s%s%s' % (size, sq)
                    return url

        if getattr(self, 'type', '') in ['pre_applicant', 'applicant']:
            return '/images/avatar.png'

        gravatar_type = 'monsterid' if getattr(self, 'type', '') == 'person' else 'identicon'

        return 'http://www.gravatar.com/avatar/%s?s=%s&d=%s' % (hashlib.md5(str(self.key()).strip().lower()).hexdigest(), size, gravatar_type)

    def AddSubbubble(self, type, properties = None, user = None):
        bt = self.GetType()
        bt_new = Bubble.get(type)

        # Create new bubble
        newbubble = Bubble()
        newbubble.x_type = bt_new.key()
        newbubble.type = bt_new.path

        # Set properties
        if properties:
            for p, v in properties.iteritems():
                newbubble.AddValue(p, v)

        # Propagate properties
        for pp in Bubble().get(bt.GetValueAsList('propagated_properties')):
            if hasattr(self, pp.data_property):
                setattr(newbubble, pp.data_property, getattr(self, pp.data_property))

        # Set Counters
        for bp in db.Query(Bubble).filter('type', 'bubble_property').filter('data_type', 'counter').filter('__key__ IN ', bt.bubble_properties).fetch(1000):
            if bp.key() not in getattr(bt, 'propagated_properties', []):
                data_value = getattr(self, bp.data_property, None)
                if data_value:
                    c = Counter().get(data_value)
                    if getattr(c, 'value_property', None):
                        counter_value = getattr(self, c.value_property, c.value) + c.increment
                        setattr(self, c.value_property, counter_value)
                        self.put(user)
                    else:
                        counter_value = GetCounterNextValue(data_value)
                    dname = bp.format_string.replace('@_counter_value@', str(counter_value))
                    for data_property in FindTags(dname, '@', '@'):
                        t = self.GetProperty(bubbletype = bt, data_property = data_property)
                        dname = dname.replace('@%s@' % data_property, ', '.join(['%s' % n['value'] for n in t['values'] if n['value']]))

                    setattr(newbubble, bp.target_property, dname)

        # Save new bubble
        newbubble.put(user)

        # Propagate rights
        for r in ['viewer', 'subbubbler', 'editor', 'owner']:
            if hasattr(self, 'x_br_%s' % r):
                newbubble.AddRight(
                    person_keys = getattr(self, 'x_br_%s' % r),
                    right = r
                )

        # Create BubbleRelation's
        br = db.Query(BubbleRelation).filter('bubble', self.key()).filter('related_bubble', newbubble.key()).filter('type', 'subbubble').get()
        if not br:
            br = BubbleRelation()
            br.bubble = self.key()
            br.related_bubble = newbubble.key()
            br.type = 'subbubble'
            br.put(user)
        else:
            if br.x_is_deleted != False:
                br.x_is_deleted = False
                br.put(user)

        # Add new bubble to optional_bubbles list
        self.x_br_subbubble = ListMerge(newbubble.key(), self.GetValueAsList('x_br_subbubble'))
        self.put(user)

        #AutoFix new bubble
        newbubble.AutoFix()

        return newbubble

    def GetValueAsList(self, data_property):
        result = getattr(self, data_property, [])
        if type(result) is list:
            return result
        else:
            return [result]

    def GetValue(self, data_property, default=None):
        result = getattr(self, data_property, None)
        if not result:
            return default
        if type(result) is list:
            return result[0]
        else:
            return result

    def AddValue(self, data_property, values):
        newvalue = ListMerge(getattr(self, data_property, []), values)
        if len(newvalue) == 1:
            setattr(self, data_property, newvalue[0])
        if len(newvalue) > 1:
            setattr(self, data_property, newvalue)

    def RemoveValue(self, data_property, value):
        oldvalue = getattr(self, data_property, [])
        if type(oldvalue) is not list:
            oldvalue = [oldvalue]
        newvalue = ListSubtract(oldvalue, value)

        if  not newvalue:
            if hasattr(self, data_property):
                delattr(self, data_property)
            return
        if len(newvalue) == 0 and hasattr(self, data_property):
            delattr(self, data_property)
            return
        if len(newvalue) == 1:
            setattr(self, data_property, newvalue[0])
            return
        if len(newvalue) > 1:
            setattr(self, data_property, newvalue)
            return

    def GetProperties(self, language = None):
        if not language:
            language = UserPreferences().current.language

        if self.is_saved():
            cache_key = 'bubble_properties_' + language + '_' + str(self.key())
            result = Cache().get(cache_key)
            if result:
                return result

        bt = self.GetType()

        result = []
        for bp in sorted(Bubble().get(bt.GetValueAsList('bubble_properties')), key=attrgetter('ordinal')):
            if hasattr(bp, 'data_property'):
                result.append(self.GetProperty(
                    bubbletype = bt,
                    data_property = bp.data_property,
                    language = language,
                ))

        if self.is_saved():
            Cache().set(cache_key, result)
        return result

    def GetProperty(self, bubbletype, data_property, language = None):
        if not language:
            language = UserPreferences().current.language

        if self.is_saved():
            cache_key = 'bubble_property_' + data_property + '_' + language + '_' + str(self.key())
            result = Cache().get(cache_key)
            if result:
                return result

        bp = db.Query(Bubble).filter('__key__ IN', bubbletype.GetValueAsList('bubble_properties')).filter('data_property', data_property).get()
        if not bp:
            return

        data_value = getattr(self, bp.data_property, None)
        values = []
        has_values = False
        choices = False

        if data_value:
            if type(data_value) is not list:
                data_value = [data_value]

            for v in data_value:
                if v != None:
                    if bp.data_type in ['string', 'text', 'integer', 'float', 'boolean']:
                        v = {'value': v}
                    if bp.data_type == 'select':
                        v = {'value': v, 'key': v}
                    if bp.data_type in ['dictionary_string', 'dictionary_text', 'dictionary_select']:
                        d = Dictionary().get(v)
                        v = {'value': getattr(d, language), 'key': str(d.key())}
                    if bp.data_type == 'datetime':
                        v = {'value': UtcToLocalDateTime(v).strftime('%d.%m.%Y %H:%M'), 'forsort': UtcToLocalDateTime(v).strftime('%Y%m%d%H%M')}
                    if bp.data_type == 'date':
                        v = {'value': v.strftime('%d.%m.%Y'), 'forsort': UtcToLocalDateTime(v).strftime('%Y%m%d%H%M')}
                    if bp.data_type == 'reference':
                        try:
                            d = Bubble().get(v)
                            v = {'value': d.displayname, 'key': str(d.key())}
                        except:
                            v = {'value': 'BT'}
                    if bp.data_type == 'counter':
                        d = Counter().get(v)
                        v = {'value': d.displayname, 'key': str(d.key())}
                    if bp.data_type == 'blobstore':
                        b = blobstore.BlobInfo.get(v)
                        v = {
                            'value': b.filename,
                            'key': str(b.key()),
                            'size': GetFileSize(b.size),
                            'image_url': images.get_serving_url(b.key()) if bp.data_property == 'photo' and b.content_type in ['image/bmp', 'image/jpeg', 'image/pjpeg', 'image/png', 'image/gif', 'image/tiff', 'image/x-icon'] else None
                        }

                    if v:
                        values.append(v)
                        has_values = True

        if (bp.GetValue('count', 0) == 0 or bp.GetValue('count', 0) > len(values)) and bp.GetValue('is_read_only', False) == False:
            values.append({'value': None})

        result = {
            'key': str(bp.key()),
            'data_type': bp.GetValue('data_type', ''),
            'data_property': bp.GetValue('data_property', ''),
            'name': GetDictionaryValue(bp.GetValue('name_plural', ''), language) if len(values) > 1 else GetDictionaryValue(bp.GetValue('name', ''), language),
            'has_values': has_values,
            'values': values,
            'is_public': bp.key() in bubbletype.GetValueAsList('public_properties'),
            'is_read_only': bp.key() in bubbletype.GetValueAsList('read_only_properties'),
            'is_mandatory': bp.key() in bubbletype.GetValueAsList('mandatory_properties'),
            'is_create_only': bp.key() in bubbletype.GetValueAsList('create_only_properties'),
            'can_add_new': (bp.GetValue('count', 0) == 0 or bp.GetValue('count', 0) > len(values)),
            'choices': bp.data_type in ['select', 'dictionary_select', 'reference', 'counter'],
        }

        if self.is_saved():
            Cache().set(cache_key, result)
        return result

    def SetProperty(self, propertykey, oldvalue = '', newvalue = '', user = None):
        bp = Bubble().get(propertykey)

        result = newvalue
        data_value = getattr(self, bp.data_property, [])
        if type(data_value) is not list:
            data_value = [data_value]

        if bp.data_type in ['dictionary_string', 'dictionary_text']:
            if oldvalue:
                d = Dictionary().get(oldvalue)
            else:
                d = Dictionary()
                if bp.GetValue('choices', None):
                    d.name = bp.GetValue('choices', None)
                else:
                    d.name = 'bubble_%s' % bp.data_property
            setattr(d, UserPreferences().current.language, newvalue)
            d.put()
            oldvalue = None
            newvalue = d.key()
            result = str(d.key())
        if bp.data_type == 'select':
            data_value = [v for v in newvalue.split(' : ')] if newvalue else []
            oldvalue = None
            newvalue = None
        if bp.data_type in ['dictionary_select', 'reference', 'counter']:
            data_value = [db.Key(v) for v in newvalue.split(' : ')] if newvalue else []
            oldvalue = None
            newvalue = None
        if bp.data_type == 'datetime':
            oldvalue = UtcFromLocalDateTime(datetime.strptime('%s:00' % oldvalue, '%d.%m.%Y %H:%M:%S')) if oldvalue else None
            newvalue = UtcFromLocalDateTime(datetime.strptime('%s:00' % newvalue, '%d.%m.%Y %H:%M:%S')) if newvalue else None
        if bp.data_type == 'date':
            oldvalue = datetime.strptime('%s 00:00:00' % oldvalue, '%d.%m.%Y %H:%M:%S') if oldvalue else None
            newvalue = datetime.strptime('%s 00:00:00' % newvalue, '%d.%m.%Y %H:%M:%S') if newvalue else None
        if bp.data_type == 'float':
            oldvalue = float(oldvalue) if oldvalue else None
            newvalue = float(newvalue) if newvalue else None
        if bp.data_type == 'integer':
            oldvalue = int(oldvalue) if oldvalue else None
            newvalue = int(newvalue) if newvalue else None
        if bp.data_type == 'boolean':
            newvalue = True if newvalue.lower() == 'true' else False
            oldvalue = True if oldvalue.lower() == 'true' else False
            # data_value = ListMerge(newvalue, data_value)
            # data_value = ListSubtract(data_value, oldvalue)

        if oldvalue:
            data_value = ListSubtract(data_value, oldvalue)
        if newvalue:
            if bp.GetValue('count', 0) == 1:
                data_value = [newvalue]
            else:
                data_value = ListMerge(newvalue, data_value)

        if len(data_value) > 0:
            if len(data_value) == 1:
                data_value = data_value[0]
            setattr(self, bp.data_property, data_value)
        else:
            if hasattr(self, bp.data_property):
                delattr(self, bp.data_property)

        self.put(user)

        self.ResetCache()
        for language in SystemPreferences().get('languages'):
            Cache().set('bubble_property_' + bp.data_property + '_' + language + '_' + str(self.key()))

        return result

    def GetType(self):
        if self.is_saved():
            cache_key = 'bubble_typekey_' + str(self.key())
            result = Cache().get(cache_key)
            if result:
                return Bubble().get(result)
        if hasattr(self, 'x_type'):
            result = Bubble().get(self.x_type)
        else:
            if not hasattr(self, 'type'):
                return None
            result = db.Query(Bubble).filter('type', 'bubble_type').filter('path', self.type).get()

        if self.is_saved():
            Cache().set(cache_key, result.key())
        return result

    def GetRelatives(self, relation, type=None):
        if hasattr(self, 'x_br_%s' % relation):
            result = []
            for b in db.get(self.GetValueAsList('x_br_%s' % relation)):
                if not b:
                    continue
                if b.x_is_deleted == True:
                    continue
                if b.kind() != 'Bubble':
                    continue
                if type and b.type != type:
                    continue
                result.append(b)
            return result
        return []

    def GetParents(self):
        return db.Query(Bubble).filter('x_is_deleted', False).filter('x_br_subbubble', self.key()).fetch(100)

    def GetSubtypes(self):
        bt = self.GetType()
        return Bubble().get(ListMerge(self.GetValueAsList('allowed_subtypes'), bt.GetValueAsList('allowed_subtypes')))

    def GetAllowedSubtypes(self):
        if getattr(self, 'allowed_subtypes', None):
            return Bubble().get(self.GetValueAsList('allowed_subtypes'))
        bt = self.GetType()
        if getattr(bt, 'allowed_subtypes', None):
            return Bubble().get(bt.GetValueAsList('allowed_subtypes'))

    def ResetCache(self):
        for language in SystemPreferences().get('languages'):
            Cache().set('bubble_typekey_' + str(self.key()))
            Cache().set('bubble_properties_' + language + '_' + str(self.key()))
            Cache().set('bubble_dname_' + language + '_' + str(self.key()))
            Cache().set('bubble_dinfo_' + language + '_' + str(self.key()))


def CurrentUser():
    user = users.get_current_user()
    if user:
        # if user.email() == 'argoroots@gmail.com':
        #     return Bubble().get_by_id(5013376)
        current_user = db.Query(Bubble).filter('type', 'person').filter('user', user.email()).filter('x_is_deleted', False).get()
        if not current_user:
            current_user = Bubble()
            current_user.user = user.email()
            current_user.is_guest = True
            current_user.type = 'person'
            current_user.put()
        current_user._googleuser = user.email()
        return current_user


class BubbleRelation(ChangeLogModel):
    bubble                  = db.ReferenceProperty(Bubble, collection_name='bubblerelation_bubble')
    related_bubble          = db.ReferenceProperty(Bubble, collection_name='bubblerelation_related_bubble')
    type                    = db.StringProperty(choices=['nextinline','subbubble','seeder','leecher','editor','owner','subbubbler','viewer'])
    start_datetime          = db.DateTimeProperty()
    end_datetime            = db.DateTimeProperty()
