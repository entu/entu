from google.appengine.ext import db
from google.appengine.ext import blobstore
from datetime import *
from operator import attrgetter

import hashlib

from bo import *
from database.dictionary import *
from database.person import *


class Counter(ChangeLogModel):
    name            = db.ReferenceProperty(Dictionary, collection_name='counter_name')
    value           = db.IntegerProperty(default=0)
    increment       = db.IntegerProperty(default=1)

    @property
    def displayname(self):
        return self.name.value

    @property
    def next_value(self):
        self.value += self.increment
        self.put()
        return self.value


class RatingScale(ChangeLogModel):
    name                = db.ReferenceProperty(Dictionary, collection_name='ratingscale_name')

    @property
    def displayname(self):
        return self.name.value

    @property
    def PositiveGradeDefinitions(self):
        return db.Query(GradeDefinition).filter('rating_scale', self).filter('is_positive', True).order('equivalent').fetch(1000)

    @property
    def NegativeGradeDefinitions(self):
        return db.Query(GradeDefinition).filter('rating_scale', self).filter('is_positive', False).order('equivalent').fetch(1000)

    @property
    def GradeDefinitions(self):
        return self.gradedefinitions

    @property
    def gradedefinitions(self):                 # TODO: refactor to GradeDefinitions
        return db.Query(GradeDefinition).filter('rating_scale', self).order('equivalent').fetch(1000)


class BubbleProperty(ChangeLogModel):
    name                    = db.ReferenceProperty(Dictionary, collection_name='bubbleproperty_name')
    name_plural             = db.ReferenceProperty(Dictionary, collection_name='bubbleproperty_name_plural')
    data_type               = db.StringProperty()
    data_property           = db.StringProperty()
    format_string           = db.StringProperty()
    target_property         = db.StringProperty()
    default                 = db.StringProperty()
    choices                 = db.StringListProperty()
    count                   = db.IntegerProperty()
    ordinal                 = db.IntegerProperty()
    is_unique               = db.BooleanProperty(default=False)
    is_read_only            = db.BooleanProperty(default=False)
    is_auto_complete        = db.BooleanProperty(default=False)

    @property
    def displayname(self):
        return self.name.value

    @property
    def dictionary_name(self):
        if getattr(self, 'choices', None):
            if len(self.choices) > 0:
                return self.choices[0]
        if getattr(self, 'data_property', None):
            return 'bubble_%s' % self.data_property.lower()

    @property
    def reference_entitykind(self):
        if getattr(self, 'choices', None):
            if len(self.choices) > 0:
                return eval(self.choices[0])


class BubbleType(ChangeLogModel):
    type                    = db.StringProperty()
    name                    = db.ReferenceProperty(Dictionary, collection_name='bubbletype_name')
    name_plural             = db.ReferenceProperty(Dictionary, collection_name='bubbletype_name_plural')
    description             = db.ReferenceProperty(Dictionary, collection_name='bubbletype_description')
    allowed_subtypes        = db.StringListProperty()
    maximum_leecher_count   = db.IntegerProperty()
    is_exclusive            = db.BooleanProperty(default=False) # no two exclusive events should happen to same person at same time
    grade_display_method    = db.StringProperty()
    property_displayname    = db.StringProperty()
    property_displayinfo    = db.StringProperty()
    bubble_properties       = db.ListProperty(db.Key)
    mandatory_properties    = db.ListProperty(db.Key)
    public_properties       = db.ListProperty(db.Key)
    propagated_properties   = db.ListProperty(db.Key)
    escalated_properties    = db.ListProperty(db.Key)
    inherited_properties    = db.ListProperty(db.Key)

    @property
    def displayname(self):
        if not self.name:
            return '-'

        cache_key = 'bubbletype_dname_' + UserPreferences().current.language + '_' + str(self.key())
        name = Cache().get(cache_key)
        if not name:
            name = StripTags(self.name.value)
            Cache().set(cache_key, name)
        return name

    @property
    def color(self):
        return RandomColor(100,255,100,255,100,255)

    @property
    def allowed_subtypes2(self): #TODO refactor to AllowedSubtypes
        return self.AllowedSubtypes

    @property
    def AllowedSubtypes(self):
        if not self.allowed_subtypes:
            return
        if len(self.allowed_subtypes) == 0:
            return
        CandidateSubtypes = db.Query(BubbleType).fetch(1000)
        AllowedSubtypes = []
        for type in self.allowed_subtypes:
            type_is_valid = False
            for bt in CandidateSubtypes:
                if bt.type == type:
                    AllowedSubtypes.append(bt)
                    type_is_valid = True
                    break
            # If there are non-existing subtypes, remove them and recursively try again
            if not type_is_valid:
                self.allowed_subtypes = RemoveFromList(type, self.allowed_subtypes)
                self.put()
                return self.AllowedSubtypes

        return AllowedSubtypes

    @property
    def AvailableSubtypes(self):
        AvailableSubtypes = db.Query(BubbleType).fetch(1000)
        for type in self.allowed_subtypes:
            for bt in AvailableSubtypes:
                if bt.type == type:
                    AvailableSubtypes.remove(bt)
                    break
        return AvailableSubtypes


    def add_allowed_subtype(self, child_key):
        subtype_to_add = BubbleType.get(child_key)
        self.allowed_subtypes = AddToList(subtype_to_add.type, self.allowed_subtypes)
        self.put()


    def remove_allowed_subtype(self, child_key):
        subtype_to_remove = BubbleType.get(child_key)
        self.allowed_subtypes = RemoveFromList(subtype_to_remove.type, self.allowed_subtypes)
        self.put()


class Bubble(ChangeLogModel):
    type                    = db.StringProperty()
    mandatory_bubbles       = db.ListProperty(db.Key)
    optional_bubbles        = db.ListProperty(db.Key)
    prerequisite_bubbles    = db.ListProperty(db.Key)
    next_in_line            = db.ListProperty(db.Key)
    sort_estonian           = db.StringProperty(default='')
    sort_english            = db.StringProperty(default='')
    search_estonian         = db.StringListProperty()
    search_english          = db.StringListProperty()

    def AutoFix(self):
        if getattr(self, 'name', None):
            name = Dictionary().get(self.name)
            self.sort_estonian = StringToSortable(name.estonian)
            self.sort_english = StringToSortable(name.english)

            self.search_estonian = StringToSearchIndex(name.estonian)
            self.search_english = StringToSearchIndex(name.english)

        # seeders = db.Query(Person, keys_only=True).filter('_is_deleted', False).filter('seeder', self.key()).fetch(1000)
        # self.seeders = seeders if seeders else []

        # leechers = db.Query(Person, keys_only=True).filter('_is_deleted', False).filter('leecher', self.key()).fetch(1000)
        # self.leechers = leechers if leechers else []

        for k in self.mandatory_bubbles:
            if not Bubble().get(k):
                self.mandatory_bubbles.remove(k)

        for k in self.optional_bubbles:
            if not Bubble().get(k):
                self.optional_bubbles.remove(k)


        # if getattr(self, 'description', None):
        #     d = Dictionary().get(self.description)
        #     if d:
        #         if not d.english and not d.estonian:
        #             delattr(self, 'description')

        # if getattr(self, 'badge', None):
        #     d = Dictionary().get(self.badge)
        #     if d:
        #         if not d.english and not d.estonian:
        #             delattr(self, 'badge')

        # try:
        #     if not self.state:
        #         delattr(self, 'state')
        # except:
        #     pass
        # try:
        #     if not self.bubble_type:
        #         delattr(self, 'bubble_type')
        # except:
        #     pass
        # try:
        #     if not self.url:
        #         delattr(self, 'url')
        # except:
        #     pass
        # try:
        #     if not self.start_datetime:
        #         delattr(self, 'start_datetime')
        # except:
        #     pass
        # try:
        #     if not self.end_datetime:
        #         delattr(self, 'end_datetime')
        # except:
        #     pass
        # try:
        #     if not self.maximum_leecher_count:
        #         delattr(self, 'maximum_leecher_count')
        # except:
        #     pass
        # try:
        #     if not self.minimum_bubble_count:
        #         delattr(self, 'minimum_bubble_count')
        # except:
        #     pass
        # try:
        #     if not self.minimum_points:
        #         delattr(self, 'minimum_points')
        # except:
        #     pass
        # try:
        #     if not self.points:
        #         delattr(self, 'points')
        # except:
        #     pass

        self.put('autofix')

    @property
    def tags(self):
        bt = db.Query(BubbleType).filter('type', self.type).get()
        result = []
        for bp in sorted(BubbleProperty().get(bt.bubble_properties), key=attrgetter('ordinal')):
            data_value = getattr(self, bp.data_property, None)
            value = []
            if data_value:
                if type(data_value) is not list:
                    data_value = [data_value]
                for v in data_value:
                    if v != None:
                        if bp.data_type in ['dictionary_string', 'dictionary_text', 'dictionary_select']:
                            d = Dictionary().get(v)
                            v = d.value
                        if bp.data_type == 'datetime':
                            v = v.strftime('%d.%m.%Y %H:%M')
                        if bp.data_type == 'date':
                            v = v.strftime('%d.%m.%Y')
                        if bp.data_type == 'reference':
                            e = bp.reference_entitykind().get(v)
                            v = e.displayname
                        if bp.data_type == 'counter':
                            c = Counter().get(v)
                            v = c.displayname
                        if bp.data_type == 'blobstore':
                            b = blobstore.BlobInfo.get(v)
                            v = '<a href="/bubble/file/%s" title="%s">%s</a>' % (b.key(), GetFileSize(b.size), b.filename)
                        if bp.data_type == 'boolean':
                            v = Translate('true') if v == True else Translate('false')
                        if v:
                            value.append(v)
            result.append({
                'data_type': bp.data_type,
                'data_property': bp.data_property,
                'name': bp.name_plural.value if len(value) > 1 else bp.name.value,
                'value': value
            })
        return result

    @property
    def displayname(self):
        bt = self.GetType()

        if not bt.property_displayname:
            return ''

        dname = bt.property_displayname
        for t in self.tags:
            dname = dname.replace('@%s@' % t['data_property'], ', '.join(t['value']))

        return dname

        # if not getattr(self, 'name', None):
        #     return ''

        # d = Dictionary().get(self.name)
        # if not d:
        #     return ''

        # cache_key = 'bubble_dname_' + UserPreferences().current.language + '_' + str(self.key())
        # name = Cache().get(cache_key)
        # if not name:
        #     name = StripTags(d.value)
        #     Cache().set(cache_key, name)
        # return name

    def displayname_cache_reset(self):
        cache_key = 'bubble_dname_' + UserPreferences().current.language + '_' + str(self.key())
        Cache().set(cache_key)

    @property
    def displayinfo(self):
        bt = self.GetType()

        if not bt.property_displayinfo:
            return ''

        dname = bt.property_displayinfo
        for t in self.tags:
            dname = dname.replace('@%s@' % t['data_property'], ', '.join(t['value']))

        return dname

    @property
    def subbubbles(self):
        return GetUniqueList(self.mandatory_bubbles + self.optional_bubbles)

    @property
    def allowed_subbubble_types(self):
        if getattr(self, 'allowed_subtypes', None):
            return db.Query(BubbleType).filter('type IN', self.allowed_subtypes).fetch(1000)
        else:
            return db.Query(BubbleType).filter('type IN', self.GetType().allowed_subtypes).fetch(1000)

    def Authorize(self, type):
        if not getattr(self, 'viewers', None):
            return False
        if Person().current.key() not in getattr(self, 'viewers', None):
            return False
        return True

    def GetPhotoUrl(self, size = ''):
        return 'http://www.gravatar.com/avatar/%s?s=%s&d=identicon' % (hashlib.md5(str(self.key()).strip().lower()).hexdigest(), size)

    def AddSubbubble(self, type):
        newbubble = Bubble()
        newbubble.type = type
        newbubble.viewers = self.viewers
        newbubble.put()

        self.optional_bubbles = AddToList(newbubble.key(), self.optional_bubbles)
        self.put()

        br = db.Query(BubbleRelation).filter('_is_deleted', False).filter('bubble', self.key()).filter('related_bubble', newbubble.key()).get()
        if not br:
            br = BubbleRelation()
            br.bubble = self.key()
            br.related_bubble = newbubble.key()
            br.type = 'subbuble'
            br.put()

        tags = self.tags
        for bp in db.Query(BubbleProperty).filter('data_type', 'counter').filter('__key__ IN ', self.GetType().bubble_properties).fetch(1000):
            data_value = getattr(self, bp.data_property, None)
            if data_value:
                c = Counter().get(data_value)

                dname = bp.format_string.replace('@_counter_value@', str(c.next_value))
                for t in tags:
                    dname = dname.replace('@%s@' % t['data_property'], ', '.join(t['value']))
                setattr(newbubble, bp.target_property, dname)
                newbubble.put()

        return newbubble


    def GetProperties(self):
        bt = db.Query(BubbleType).filter('type', self.type).get()
        result = []
        mandatory_properties = self.GetType().mandatory_properties

        # for bp in db.Query(BubbleProperty).order('ordinal').fetch(1000):
        for bp in sorted(BubbleProperty().get(bt.bubble_properties), key=attrgetter('ordinal')):
            data_value = getattr(self, bp.data_property, None)
            value = []
            choices = []

            if data_value:
                if type(data_value) is not list:
                    data_value = [data_value]

                for v in data_value:
                    if v != None:
                        if bp.data_type in ['dictionary_string', 'dictionary_text']:
                            d = Dictionary().get(v)
                            v = d.value
                        if bp.data_type == 'datetime':
                            v = v.strftime('%d.%m.%Y %H:%M')
                        if bp.data_type == 'date':
                            v = v.strftime('%d.%m.%Y')
                        if bp.data_type in ['reference', 'counter', 'dictionary_select']:
                            v = v
                        if bp.data_type == 'blobstore':
                            b = blobstore.BlobInfo.get(v)
                            v = {'key': b.key(), 'filename': b.filename, 'size': GetFileSize(b.size)}
                        if v:
                            value.append(v)

            if bp.data_type == 'dictionary_select':
                for d in sorted(db.Query(Dictionary).filter('name', bp.dictionary_name), key=attrgetter('value')):
                    choices.append({'key': d.key(), 'value': d.value})

            if bp.data_type == 'reference':
                for e in sorted(db.Query(bp.reference_entitykind).filter('_is_deleted', False), key=attrgetter('displayname')):
                    choices.append({'key': e.key(), 'value': e.displayname})

            if bp.data_type == 'counter':
                for c in sorted(db.Query(Counter).filter('_is_deleted', False), key=attrgetter('displayname')):
                    choices.append({'key': c.key(), 'value': c.displayname})

            if (bp.count == 0 or bp.count > len(value)) and bp.is_read_only == False:
                value.append('')

            result.append({
                'key': bp.key(),
                'data_type': bp.data_type,
                'data_property': bp.data_property,
                'name': bp.name_plural.value if len(value) > 1 else bp.name.value,
                'choices': choices,
                'value': value,
                'is_mandatory': True if bp.key() in mandatory_properties else False,
                'is_read_only': bp.is_read_only,
                'can_add_new': (bp.count == 0 or bp.count > len(value))
            })
        return result

    def SetProperty(self, propertykey, oldvalue = '', newvalue = ''):
        bp = BubbleProperty().get(propertykey)

        data_value = getattr(self, bp.data_property, [])
        if type(data_value) is not list:
            data_value = [data_value]

        if bp.data_type in ['dictionary_string', 'dictionary_text']:
            if len(data_value) > 0:
                for d in Dictionary().get(data_value):
                    if getattr(d, UserPreferences().current.language, None) == oldvalue:
                        if newvalue:
                            setattr(d, UserPreferences().current.language, newvalue)
                            d.put()
                        else:
                            data_value = RemoveFromList(d.key(), data_value)
                newvalue = None
            else:
                d = Dictionary()
                d.name = bp.dictionary_name
                setattr(d, UserPreferences().current.language, newvalue)
                d.put()
                newvalue = d.key()
            oldvalue = None
        if bp.data_type in ['dictionary_select', 'reference', 'counter']:
            oldvalue = db.Key(oldvalue) if oldvalue else None
            newvalue = db.Key(newvalue) if newvalue else None
        if bp.data_type == 'datetime':
            oldvalue = datetime.strptime(oldvalue, '%d.%m.%Y %H:%M') if oldvalue else None
            newvalue = datetime.strptime(newvalue, '%d.%m.%Y %H:%M') if newvalue else None
        if bp.data_type == 'date':
            oldvalue = datetime.strptime('%s 00:00' % oldvalue, '%d.%m.%Y %H:%M') if oldvalue else None
            newvalue = datetime.strptime('%s 00:00' % newvalue, '%d.%m.%Y %H:%M') if newvalue else None
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
            data_value = AddToList(newvalue, data_value)

        if len(data_value) > 0:
            if len(data_value) == 1:
                data_value = data_value[0]
            setattr(self, bp.data_property, data_value)
        else:
            if hasattr(self, bp.data_property):
                delattr(self, bp.data_property)

        self.put()

        return newvalue

    def GetType(self):
        return db.Query(BubbleType).filter('type', self.type).get()

    def GetAllowedTypes(self):
        return sorted(db.Query(BubbleType).filter('type IN', self.GetType().allowed_subtypes).fetch(1000), key=attrgetter('displayname'))

    # @property
    # def displaydate(self):
    #     if self.start_datetime and self.end_datetime:
    #         if self.start_datetime.strftime('%H:%M') == '00:00' and self.end_datetime.strftime('%H:%M') == '00:00':
    #             if self.start_datetime.strftime('%d.%m.%Y') == self.end_datetime.strftime('%d.%m.%Y'):
    #                 return self.start_datetime.strftime('%d.%m.%Y')
    #             else:
    #                 return self.start_datetime.strftime('%d.%m.%Y') + ' - ' + self.end_datetime.strftime('%d.%m.%Y')
    #         else:
    #             if self.start_datetime.strftime('%d.%m.%Y') == self.end_datetime.strftime('%d.%m.%Y'):
    #                 return self.start_datetime.strftime('%d.%m.%Y %H:%M') + ' - ' + self.end_datetime.strftime('%H:%M')
    #             else:
    #                 return self.start_datetime.strftime('%d.%m.%y %H:%M') + ' - ' + self.end_datetime.strftime('%d.%m.%y %H:%M')
    #     else:
    #         if self.start_datetime:
    #             return self.start_datetime.strftime('%d.%m.%Y %H:%M') + ' - ...'
    #         else:
    #             if self.end_datetime:
    #                 return '... - ' + self.end_datetime.strftime('%d.%m.%Y %H:%M')
    #     return ''

    # def GetTypedTags(self):
    #     result = {}
    #     for tag in self.typed_tags:
    #         result[tag.split(':')[0]] = tag.split(':')[1]
    #     return result

    # def GetSeeders(self):
    #     return Person().get(self.seeders)

    # def GetLeechers(self):
    #     return Person().get(self.leechers)

    # def GetNextInLines(self):
    #     return Bubble().get(self.next_in_line)

    # def GetPrerequisiteBubbles(self):
    #     return Bubble.get(self.prerequisite_bubbles)

    # def WaitinglistToLeecher(self):
    #     for bp in db.Query(BubblePerson).filter('bubble', self).filter('status', 'waiting').order('start_datetime'):
    #         if self.maximum_leecher_count:
    #             if self.maximum_leecher_count <= len(self.leechers):
    #                 break
    #         self.leechers = AddToList(bp.person.key(), self.leechers)
    #         self.put()

    #         person = bp.person
    #         person.leecher = AddToList(bp.bubble.key(), person.leecher)
    #         person.put()

    #         bp.end_datetime = datetime.now()
    #         bp.status = 'waiting_end'
    #         bp.put()

    # @property
    # def PrevInLines(self):
    #     return db.Query(Bubble).filter('next_in_line', self.key()).fetch(1000)

    # @property
    # def MandatoryInBubbles(self):
    #     return db.Query(Bubble).filter('mandatory_bubbles', self.key()).fetch(1000)

    # @property
    # def OptionalInBubbles(self):
    #     return db.Query(Bubble).filter('optional_bubbles', self.key()).fetch(1000)

    # @property
    # def InBubblesD(self):
    #     in_bubbles = {}
    #     for b in self.InBubbles:
    #         in_bubbles[b.key()] = b
    #     return in_bubbles

    # @property
    # def InBubbles(self):
    #     in_bubbles = self.in_bubbles
    #     if in_bubbles:
    #         return in_bubbles
    #     else:
    #         return []

    # @property
    # def in_bubbles(self):                       # TODO refactor to InBubbles
    #     return self.MandatoryInBubbles + self.OptionalInBubbles

    # @property
    # def PrerequisiteForBubbles(self):
    #     return db.Query(Bubble).filter('prerequisite_bubbles', self.key()).fetch(1000)

    # @property
    # def PrerequisiteBubbles(self):
    #     bubbles = []
    #     if self.prerequisite_bubbles:
    #         for b in Bubble.get(self.prerequisite_bubbles):
    #             if not b:
    #                 continue
    #             if b.is_deleted:
    #                 continue
    #             bubbles.append(b)
    #     return bubbles

    # @property
    # def SubBubblesD(self):
    #     sub_bubbles = {}
    #     for b in self.SubBubbles:
    #         sub_bubbles[b.key()] = b
    #     return sub_bubbles

    # @property
    # def SubBubbles(self):
    #     sub_bubbles = self.bubbles
    #     if sub_bubbles:
    #         return sub_bubbles
    #     else:
    #         return []

    # @property
    # def bubbles(self):                         # TODO refactor to SubBubbles
    #     keys = []
    #     if self.mandatory_bubbles:
    #         keys += self.mandatory_bubbles
    #     if self.optional_bubbles:
    #         keys += self.optional_bubbles
    #     keys = GetUniqueList(keys)
    #     if len(keys) == 0:
    #         return

    #     bubbles = []
    #     for b in Bubble.get(keys):
    #         if not b:
    #             continue
    #         if b.is_deleted:
    #             continue
    #         if b.key() in self.mandatory_bubbles:
    #             b.is_mandatory = True
    #         else:
    #             b.is_mandatory = False
    #         bubbles.append(b)
    #     if len(bubbles) > 0:
    #         return bubbles

    # @property
    # def RateableSubBubbles(self):
    #     keys = []
    #     if self.mandatory_bubbles:
    #         keys += self.mandatory_bubbles
    #     if self.optional_bubbles:
    #         keys += self.optional_bubbles
    #     keys = GetUniqueList(keys)
    #     if len(keys) == 0:
    #         return

    #     bubbles = []
    #     for b in Bubble.get(keys):
    #         if not b:
    #             continue
    #         if b.is_deleted:
    #             continue
    #         if b.rating_scale is None:
    #             continue
    #         if b.key() in self.mandatory_bubbles:
    #             b.is_mandatory = True
    #         else:
    #             b.is_mandatory = False
    #         bubbles.append(b)
    #     if len(bubbles) > 0:
    #         return bubbles

    # @property
    # def MandatoryBubbles(self):
    #     if self.mandatory_bubbles is None:
    #         return
    #     bubbles = []
    #     for b in Bubble.get(self.mandatory_bubbles):
    #         if not b:
    #             continue
    #         if b.is_deleted:
    #             continue
    #         b.is_mandatory = True
    #         bubbles.append(b)
    #     if len(bubbles) > 0:
    #         return bubbles

    # @property
    # def OptionalBubbles(self):
    #     if self.optional_bubbles:
    #         bubbles = []
    #         for b in Bubble.get(self.optional_bubbles):
    #             if not b:
    #                 continue
    #             if b.is_deleted:
    #                 continue
    #             b.is_mandatory = False
    #             bubbles.append(b)
    #         if len(bubbles) > 0:
    #             return bubbles

    # @property
    # def PersonGrades(self, person_key):
    #     return db.Query(Grade).filter('person', person_key).filter('bubble',self.key()).fetch(1000)

    # # i.e. Pre-requisite bubbles must notify post-requisites when marked green so
    # # that they can check, if they are next in line for at least one green bubble
    # def propose_leecher(self, person_key):
    #     for bubble in self.PrevInLines:
    #         if bubble.is_green(person_key):
    #             return self.add_leecher(person_key)

    #     return False

    # # Could we add person to bubble.leechers?
    # def is_valid_leecher(self, person_key):
    #     if leecher in self.leechers:
    #         return False
    #     return self.are_prerequisites_satisfied(person_key)

    # @property
    # def Grades(self):
    #     return db.Query(Grade).filter('bubble', self.key()).filter('is_deleted', False).fetch(1000)

    # @property
    # def SubGrades(self):
    #     subgrades = []
    #     for bubble_key in self.sub_bubbles:
    #         subgrades.extend(db.Query(Grade).filter('bubble', bubble_key).filter('is_deleted', False).fetch(1000))
    #     return subgrades

    # @property
    # def is_started(self):
    #     return self.start_datetime < datetime.now()

    # @property
    # def is_finished(self):
    #     return self.end_datetime < datetime.now()

    # @property
    # def is_currently_on(self):
    #     return self.is_started() and not self.is_finished()

    # def add_leecher(self, person_key):
    #     #if not self.is_valid_leecher(person_key):
    #     #    return False

    #     self.leechers = AddToList(person_key, self.leechers)
    #     self.put()

    #     if self.type == 'exam':
    #         person = Person().get(person_key)
    #         if not list(set(person.leecher) & set(self.optional_bubbles)):
    #             bubbles = sorted(Bubble().get(self.optional_bubbles), key=attrgetter('start_datetime'))
    #             for b in bubbles:
    #                 if b.type == 'personal_time_slot' and b.is_deleted == False:
    #                     if not db.Query(Person).filter('leecher', b.key()).get():
    #                         person.add_leecher(b.key())
    #                         break

    #     if self.type == 'personal_time_slot':
    #         person = Person().get(person_key)
    #         bubble = db.Query(Bubble).filter('type', 'exam').filter('optional_bubbles', self.key()).get()

    #         if bubble.description:
    #             description = bubble.description.value
    #         else:
    #             description = ''

    #         con = db.Query(Conversation).filter('entities', person.key()).filter('types', 'application').get()
    #         if not con:
    #             con = Conversation()
    #             con.types = ['application']
    #             con.entities = [person.key()]
    #         con.participants = AddToList(person.key(), con.participants)
    #         con.put()
    #         """con.add_message(
    #             message = Translate('email_log_timeslot') % {
    #                 'bubble': bubble.displayname,
    #                 'description': description,
    #                 'time': self.displaydate,
    #                 'link': bubble.url,
    #             }
    #         )

    #         SendMail(
    #             to = person.emails,
    #             reply_to = 'sisseastumine@artun.ee',
    #             subject = Translate('email_subject_timeslot') % bubble.displayname,
    #             message = Translate('email_message_timeslot') % {
    #                 'name': person.displayname,
    #                 'bubble': bubble.displayname,
    #                 'description': description,
    #                 'time': self.displaydate,
    #                 'link': bubble.url,
    #             }
    #         )"""

    # def remove_leecher(self, person_key):
    #     self.leechers.remove(person_key)
    #     self.put()

    # def remove_optional_bubble(self, bubble_key):
    #     self.optional_bubbles.remove(bubble_key)
    #     self.put()

    # def get_subgrades_bubbles(self):
    #     grades_bubbles = []
    #     if self.bubbles:
    #         for b in self.bubbles:
    #             if b.type != 'personal_time_slot':
    #                 if b.type2.grade_display_method == 'all':
    #                     grades_bubbles = grades_bubbles + b.grades(person_key)
    #                 else:
    #                     grades_bubbles.append(b)
    #         grades_bubbles = sorted(grades_bubbles, key=lambda k: k.key())
    #     return grades_bubbles

    # def subgrades(self, person_key):
    #     bubbles = self.get_subgrades_bubbles()
    #     for b in bubbles:
    #         b.grade = db.Query(Grade).filter('bubble', b.key()).filter('is_deleted', False).filter('person', person_key).get()

    #     return bubbles

    # def has_positive_grade(self, person_key):
    #     grades = self.PersonGrades(person_key)
    #     if len(grades) == 0:
    #         return False

    #     for grade in sorted(grades, attrgetter('datetime', reverse=True)):
    #         if grade.is_positive:
    #             return True
    #         if self.type2.grade_display_method == 'latest':
    #             return False

    #     return False

    # def mark_green(person_key):
    #     self.green_persons = AddToList(person_key, self.green_persons)
    #     self.put()
    #     for bubble in self.PrerequisiteForBubbles:
    #         bubble.propose_leecher(person_key)

    # def is_green(person_key):
    #     if person_key in self.green_persons:
    #         return True

    #     if self.rating_scale:
    #         if not self.has_positive_grade(person_key):
    #             return False

    #     if not self.are_mandatories_satisfied(person_key):
    #         return False

    #     if self.minimum_bubble_count > 0:
    #         counter = self.minimum_bubble_count
    #         for sub_bubble in self.SubBubbles:
    #             if sub_bubble.is_green(person_key):
    #                 counter = counter - 1
    #                 if counter == 0:
    #                     return True
    #             return False

    #     self.mark_green(person_key)
    #     return True

    # def recheck_green(person_key):
    #     RemoveFromList(person_key, self.green_persons)
    #     return self.is_green(person_key)

    # def are_mandatories_satisfied(person_key):
    #     for sub_bubble in self.MandatoryBubbles:
    #         if not sub_bubble.is_green(person_key):
    #             return False
    #     return True

    # def are_prerequisites_satisfied(person_key):
    #     for pre_bubble in self.PrerequisiteBubbles:
    #         if not pre_bubble.is_green(person_key):
    #             return False
    #     return True

    # # Positive grades are only available, if mandatories are green.
    # # Negative grades could be issued at any time.
    # def grades_available(person_key):
    #     if not self.rating_scale:
    #         return

    #     if self.are_mandatories_satisfied(person_key):
    #         return self.rating_scale.GradeDefinitions

    #     return self.rating_scale.NegativeGradeDefinitions

    # # When rating a bubble with rated sub-bubbles, sub-bubble grades could be listed.
    # def sub_bubble_grades(person_key):
    #     for sub_bubble in self.SubBubbles:
    #         grades = grades + sub_bubble.PersonGrades(person_key)

    #     return grades


class BubbleRelation(ChangeLogModel):
    bubble                  = db.ReferenceProperty(Bubble, collection_name='bubblerelation_bubble')
    related_bubble          = db.ReferenceProperty(Bubble, collection_name='bubblerelation_related_bubble')
    type                    = db.StringProperty(choices=['subbuble', 'seeder','leecher','editor','owner','viewer','add_sub_bubbles'])
    start_datetime          = db.DateTimeProperty()
    end_datetime            = db.DateTimeProperty()
    name                    = db.ReferenceProperty(Dictionary, collection_name='bubblerelation_name')
    name_plural             = db.ReferenceProperty(Dictionary, collection_name='bubblerelation_name_plural')


class GradeDefinition(ChangeLogModel):
    rating_scale    = db.ReferenceProperty(RatingScale)
    name            = db.ReferenceProperty(Dictionary, collection_name='gradedefinition_name')
    is_positive     = db.BooleanProperty()
    equivalent      = db.IntegerProperty()

    @property
    def displayname(self):
        return self.name.value


class Grade(ChangeLogModel):
    person          = db.ReferenceProperty(Person, collection_name='grades')
    gradedefinition = db.ReferenceProperty(GradeDefinition, collection_name='grades')
    bubble          = db.ReferenceProperty(Bubble)
    bubble_type     = db.StringProperty()
    subject_name    = db.ReferenceProperty(Dictionary, collection_name='grade_subject_name')
    datetime        = db.DateTimeProperty()
    name            = db.ReferenceProperty(Dictionary, collection_name='grade_name')
    equivalent      = db.IntegerProperty()
    is_positive     = db.BooleanProperty()
    points          = db.FloatProperty()
    school          = db.ReferenceProperty(Dictionary, collection_name='grade_school')
    teacher         = db.ReferenceProperty(Person, collection_name='given_grades')
    teacher_name    = db.StringProperty()
    typed_tags      = db.StringListProperty()
    is_locked       = db.BooleanProperty(default=False)

    @property
    def displayname(self):
        if self.name:
            return self.name.value
        else:
            if self.gradedefinition:
                if self.gradedefinition.name:
                    return self.gradedefinition.name.value
        return ''

    @property
    def displaydate(self):
        if self.datetime:
            return self.datetime.strftime('%d.%m.%Y %H:%M')
        else:
            return '...'
