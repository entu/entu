from google.appengine.ext import db
from google.appengine.ext import blobstore
from google.appengine.api import images
from datetime import *
from operator import attrgetter

import hashlib

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
    type                    = db.StringProperty()
    mandatory_bubbles       = db.ListProperty(db.Key)
    optional_bubbles        = db.ListProperty(db.Key)
    prerequisite_bubbles    = db.ListProperty(db.Key)
    next_in_line            = db.ListProperty(db.Key)

    @property
    def displayname(self):
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

    @property
    def displayinfo(self):
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

    def AutoFix(self):
        bt = self.GetType()

        setattr(self, 'x_type', bt.key())

        if hasattr(self, '_version'):
            setattr(self, 'x_version', self._version)
            delattr(self, '_version')
        if hasattr(self, '_created'):
            setattr(self, 'x_created', self._created)
            delattr(self, '_created')
        if hasattr(self, '_created_by'):
            setattr(self, 'x_created_by', self._created_by)
            delattr(self, '_created_by')
        if hasattr(self, '_changed'):
            setattr(self, 'x_changed', self._changed)
            delattr(self, '_changed')
        if hasattr(self, '_changed_by'):
            setattr(self, 'x_changed_by', self._changed_by)
            delattr(self, '_changed_by')
        if hasattr(self, '_is_deleted'):
            setattr(self, 'x_is_deleted', self._is_deleted)
            delattr(self, '_is_deleted')
        if hasattr(self, 'viewers'):
            setattr(self, 'x_br_viewer', self.viewers)
            delattr(self, 'viewers')

        if hasattr(self, 'seeders'):
            if len(self.seeders) > 0:
                setattr(self, 'x_br_seeder', self.seeders)

        if hasattr(self, 'leechers'):
            if len(self.leechers) > 0:
                setattr(self, 'x_br_leecher', self.leechers)

        subbubbleslist = MergeLists(self.GetValueAsList('optional_bubbles'), self.GetValueAsList('x_br_subbubble'))
        if len(subbubbleslist) > 0:
            setattr(self, 'x_br_subbubble', subbubbleslist)
            setattr(self, 'optional_bubbles', subbubbleslist)

        for language in SystemPreferences().get('languages'):
            sorts = getattr(bt, 'sort_string', '')
            for data_property in FindTags(sorts, '@', '@'):
                t = self.GetProperty(bubbletype = bt, data_property = data_property, language = language)
                sorts = sorts.replace('@%s@' % data_property, ', '.join(['%s' % n['value'] for n in t['values'] if n['value']]))
            sorts = StringToSortable(sorts)
            setattr(self, 'x_sort_%s' % language, sorts)

            searchl = []
            for bp in Bubble().get(bt.GetValueAsList('search_properties')):
                if hasattr(bp, 'data_property'):
                    t = self.GetProperty(bubbletype = bt, data_property = bp.data_property, language = language)
                    for s in ['%s' % n['value'] for n in t['values'] if n['value']]:
                        searchl = MergeLists(searchl, StringToSearchIndex(s))
            if len(searchl) > 0:
                setattr(self, 'x_search_%s' % language, searchl)
            else:
                if hasattr(self, 'x_search_%s'% language):
                    delattr(self, 'x_search_%s'% language)

            if hasattr(self, '_sort_%s'% language):
                delattr(self, '_sort_%s'% language)
            if hasattr(self, '_search_%s'% language):
                delattr(self, '_search_%s'% language)
            if hasattr(self, 'sort_%s'% language):
                delattr(self, 'sort_%s'% language)
            if hasattr(self, 'search_%s'% language):
                delattr(self, 'search_%s'% language)

        for key in self.dynamic_properties():
            value = getattr(self, key)
            if type(value) is list:
                if len(value) == 1:
                    setattr(self, key, value[0])

        self.put('autofix')

    def Authorize(self, type):
        if Person().current.key() in getattr(self, 'x_br_viewer', []):
            return True
        else:
            return False

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

        gravatar_type = 'monsterid' if getattr(self, 'type', '') in ['person', 'applicant'] else 'identicon'

        return 'http://www.gravatar.com/avatar/%s?s=%s&d=%s' % (hashlib.md5(str(self.key()).strip().lower()).hexdigest(), size, gravatar_type)

    def AddSubbubble(self, type):
        bt = self.GetType()
        bt_new = Bubble.get(type)

        # Create new bubble
        newbubble = Bubble()
        newbubble.x_type = bt_new.key()
        newbubble.type = bt_new.path
        newbubble.x_br_viewer = self.x_br_viewer

        # Propagate properties
        for pp_key in getattr(bt, 'propagated_properties', []):
            pp = Bubble().get(pp_key)
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
                        self.put()
                    else:
                        counter_value = GetCounterNextValue(data_value)
                    dname = bp.format_string.replace('@_counter_value@', str(counter_value))
                    for data_property in FindTags(dname, '@', '@'):
                        t = self.GetProperty(bubbletype = bt, data_property = data_property)
                        dname = dname.replace('@%s@' % data_property, ', '.join(['%s' % n['value'] for n in t['values'] if n['value']]))

                    setattr(newbubble, bp.target_property, dname)

        # Save new bubble
        newbubble.put()

        # Create BubbleRelation's
        # br = db.Query(BubbleRelation).filter('_is_deleted', False).filter('bubble', self.key()).filter('related_bubble', newbubble.key()).get()
        # if not br:
        #     br = BubbleRelation()
        #     br.bubble = self.key()
        #     br.related_bubble = newbubble.key()
        #     br.type = 'subbuble'
        #     br.put()

        # Add new bubble to optional_bubbles list
        self.x_br_subbubble = AddToList(newbubble.key(), self.GetValueAsList('x_br_subbubble'))
        self.optional_bubbles = AddToList(newbubble.key(), self.GetValueAsList('optional_bubbles'))
        self.put()

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
                    if bp.data_type in ['dictionary_string', 'dictionary_text', 'dictionary_select']:
                        d = Dictionary().get(v)
                        v = {'value': getattr(d, language), 'key': str(d.key())}
                    if bp.data_type == 'datetime':
                        v = {'value': UtcToLocalDateTime(v).strftime('%d.%m.%Y %H:%M')}
                    if bp.data_type == 'date':
                        v = {'value': v.strftime('%d.%m.%Y')}
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
        if bp.data_type in ['dictionary_select', 'reference', 'counter']:
            oldvalue = db.Key(oldvalue) if oldvalue else None
            newvalue = db.Key(newvalue) if newvalue else None
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
            data_value = AddToList(newvalue, data_value)
            data_value = RemoveFromList(oldvalue, data_value)

        if oldvalue:
            data_value = RemoveFromList(oldvalue, data_value)
        if newvalue:
            if bp.GetValue('count', 0) == 1:
                data_value = [newvalue]
            else:
                data_value = AddToList(newvalue, data_value)

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

    def GetRelatives(self, relation):
        if hasattr(self, 'x_br_%s' % relation):
            # return Bubble().get(self.GetValueAsList('x_br_%s' % relation))
            return db.get(self.GetValueAsList('x_br_%s' % relation))

    def GetParents(self):
        return db.Query(Bubble).filter('x_is_deleted', False).filter('x_br_subbubble', self.key()).fetch(100)

    def GetSubtypes(self):
        bt = self.GetType()
        return Bubble().get(MergeLists(self.GetValueAsList('allowed_subtypes'), bt.GetValueAsList('allowed_subtypes')))

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


class BubbleRelation(ChangeLogModel):
    bubble                  = db.ReferenceProperty(Bubble, collection_name='bubblerelation_bubble')
    related_bubble          = db.ReferenceProperty(Bubble, collection_name='bubblerelation_related_bubble')
    type                    = db.StringProperty(choices=['subbuble', 'seeder','leecher','editor','owner','viewer','add_sub_bubbles'])
    start_datetime          = db.DateTimeProperty()
    end_datetime            = db.DateTimeProperty()
