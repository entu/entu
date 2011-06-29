from google.appengine.ext import db
from datetime import *

from bo import *
from database.general import *
from database.dictionary import *
from database.person import *


class RatingScale(ChangeLogModel):
    name            = db.ReferenceProperty(Dictionary, collection_name='ratingscale_name')
    model_version   = db.StringProperty(default='A')

    @property
    def displayname(self):
        return self.name.translate()

    @property
    def gradedefinitions(self):
        return db.Query(GradeDefinition).filter('rating_scale', self).order('equivalent').fetch(1000)


class BubbleType(ChangeLogModel):
    type            = db.StringProperty()
    name            = db.ReferenceProperty(Dictionary, collection_name='bubbletype_name')
    description     = db.ReferenceProperty(Dictionary, collection_name='bubbletype_description')
    allowed_subtypes = db.StringListProperty()
    model_version   = db.StringProperty(default='A')

    @property
    def displayname(self):
        cache_key = 'bubbletype_dname_' + UserPreferences().current.language + '_' + str(self.key())
        name = Cache().get(cache_key)
        if not name:
            name = self.name.translate()
            Cache().set(cache_key, name)
        return name

    @property
    def color(self):
        return RandomColor(100,255,100,255,100,255)

    @property
    def allowed_subtypes2(self):
        if self.allowed_subtypes:
            if len(self.allowed_subtypes) > 0:
                types = []
                for t in self.allowed_subtypes:
                    types.append(db.Query(BubbleType).filter('type', t).get())
                return types



class Bubble(ChangeLogModel):
    name                    = db.ReferenceProperty(Dictionary, collection_name='bubble_name')
    description             = db.ReferenceProperty(Dictionary, collection_name='bubble_description')
    start_datetime          = db.DateTimeProperty()
    end_datetime            = db.DateTimeProperty()
    url                     = db.StringProperty()
    location                = db.ReferenceProperty(Location, collection_name='bubble_location')
    owner                   = db.ReferenceProperty(Person, collection_name='bubble_owner')
    editors                 = db.ListProperty(db.Key)
    viewers                 = db.ListProperty(db.Key)
    leechers                = db.ListProperty(db.Key)
    seeders                 = db.ListProperty(db.Key)
    type                    = db.StringProperty()
    typed_tags              = db.StringListProperty()
    rating_scale            = db.ReferenceProperty(RatingScale, collection_name='bubble_ratingscale')
    badge                   = db.ReferenceProperty(Dictionary, collection_name='bubble_badge')
    points                  = db.FloatProperty()
    minimum_points          = db.FloatProperty()
    minimum_bubble_count    = db.IntegerProperty()
    mandatory_bubbles       = db.ListProperty(db.Key)
    optional_bubbles        = db.ListProperty(db.Key)
    next_in_line            = db.ListProperty(db.Key)
    entities                = db.ListProperty(db.Key)
    state                   = db.StringProperty()
    is_deleted              = db.BooleanProperty(default=False)
    created_datetime        = db.DateTimeProperty(auto_now_add=True)
    sort_estonian           = db.StringProperty()
    sort_english            = db.StringProperty()
    model_version           = db.StringProperty(default='A')

    @property
    def displayname(self):
        if self.name:
            cache_key = 'bubble_dname_' + UserPreferences().current.language + '_' + str(self.key())
            name = Cache().get(cache_key)
            if not name:
                name = StripTags(self.name.translate())
                Cache().set(cache_key, name)
            return name
        else:
            return ''


    def displayname_cache_reset(self):
        cache_key = 'bubble_dname_' + UserPreferences().current.language + '_' + str(self.key())
        Cache().set(cache_key)


    @property
    def displaydate(self):
        if self.start_datetime and self.end_datetime:
            if self.start_datetime.strftime('%H:%M') == '00:00' and self.end_datetime.strftime('%H:%M') == '00:00':
                if self.start_datetime.strftime('%d.%m.%Y') == self.end_datetime.strftime('%d.%m.%Y'):
                    return self.start_datetime.strftime('%d.%m.%Y')
                else:
                    return self.start_datetime.strftime('%d.%m.%Y') + ' - ' + self.end_datetime.strftime('%d.%m.%Y')
            else:
                if self.start_datetime.strftime('%d.%m.%Y') == self.end_datetime.strftime('%d.%m.%Y'):
                    return self.start_datetime.strftime('%d.%m.%Y %H:%M') + ' - ' + self.end_datetime.strftime('%H:%M')
                else:
                    return self.start_datetime.strftime('%d.%m.%y %H:%M') + ' - ' + self.end_datetime.strftime('%d.%m.%y %H:%M')
        else:
            if self.start_datetime:
                return self.start_datetime.strftime('%d.%m.%Y %H:%M') + ' - ...'
            else:
                return '... - ' + self.end_datetime.strftime('%d.%m.%Y %H:%M')

    @property
    def type2(self):
        return db.Query(BubbleType).filter('type', self.type).get()

    @property
    def seeders2(self):
        return Person.get(self.seeders)

    @property
    def leechers2(self):
        return Person.get(self.leechers)

    @property
    def color(self):
        return RandomColor(200,255,200,255,200,255)

    @property
    def in_bubbles(self):
        mandatory = db.Query(Bubble).filter('mandatory_bubbles', self.key()).fetch(1000)
        optional = db.Query(Bubble).filter('optional_bubbles', self.key()).fetch(1000)
        bubbles = mandatory + optional
        return bubbles

    @property
    def bubbles(self):
        keys = []
        if self.mandatory_bubbles:
            keys += self.mandatory_bubbles
        if self.optional_bubbles:
            keys += self.optional_bubbles
        keys = GetUniqueList(keys)
        if len(keys) > 0:
            bubbles = []
            for b in Bubble.get(keys):
                if b:
                    if b.is_deleted == False:
                        bubbles.append(b)
            if len(bubbles) > 0:
                return bubbles

    @property
    def mandatory_bubbles2(self):
        return Bubble.get(self.mandatory_bubbles)

    @property
    def optional_bubbles2(self):
        return Bubble.get(self.optional_bubbles)

    def add_leecher(self, person_key):
        self.leechers = AddToList(person_key, self.leechers)
        self.put()

        if self.type == 'exam':
            person = Person().get(person_key)
            if not list(set(person.leecher) & set(self.optional_bubbles)):
                bubbles = sorted(Bubble().get(self.optional_bubbles), key=lambda k: k.start_datetime)
                for b in bubbles:
                    if b.type == 'personal_time_slot' and b.is_deleted == False:
                        if not db.Query(Person).filter('leecher', b.key()).get():
                            person.add_leecher(b.key())
                            break

        if self.type == 'personal_time_slot':
            person = Person().get(person_key)
            bubble = db.Query(Bubble).filter('type', 'exam').filter('optional_bubbles', self.key()).get()

            if bubble.description:
                description = bubble.description.translate()
            else:
                description = ''

            con = db.Query(Conversation).filter('entities', person.key()).filter('types', 'application').get()
            if not con:
                con = Conversation()
                con.types = ['application']
                con.entities = [person.key()]
            con.participants = AddToList(person.key(), con.participants)
            con.put()
            con.add_message(
                message = Translate('email_log_timeslot') % {
                    'bubble': bubble.displayname,
                    'description': description,
                    'time': self.displaydate,
                    'link': bubble.url,
                }
            )

            SendMail(
                to = person.emails,
                reply_to = 'sisseastumine@artun.ee',
                subject = Translate('email_subject_timeslot') % bubble.displayname,
                message = Translate('email_message_timeslot') % {
                    'name': person.displayname,
                    'bubble': bubble.displayname,
                    'description': description,
                    'time': self.displaydate,
                    'link': bubble.url,
                }
            )


    def remove_leecher(self, person_key):
        self.leechers.remove(person_key)
        self.put()


    def remove_optional_bubble(self, bubble_key):
        self.optional_bubbles.remove(bubble_key)
        self.put()


class GradeDefinition(ChangeLogModel):
    rating_scale    = db.ReferenceProperty(RatingScale)
    name            = db.ReferenceProperty(Dictionary, collection_name='gradedefinition_name')
    is_positive     = db.BooleanProperty()
    equivalent      = db.IntegerProperty()
    model_version   = db.StringProperty(default='A')

    @property
    def displayname(self):
        return self.name.translate()


class Grade(ChangeLogModel):
    person          = db.ReferenceProperty(Person, collection_name='grades')
    gradedefinition = db.ReferenceProperty(GradeDefinition, collection_name='grades')
    bubble          = db.ReferenceProperty(Bubble, collection_name='grades')
    bubble_type     = db.StringProperty()
    datetime        = db.DateTimeProperty()
    name            = db.ReferenceProperty(Dictionary, collection_name='grade_name')
    equivalent      = db.IntegerProperty()
    is_positive     = db.BooleanProperty()
    points          = db.FloatProperty()
    school          = db.ReferenceProperty(Dictionary, collection_name='grade_school')
    teacher         = db.ReferenceProperty(Person, collection_name='given_grades')
    teacher_name    = db.StringProperty()
    is_locked       = db.BooleanProperty(default=False)
    is_deleted      = db.BooleanProperty(default=False)
    model_version   = db.StringProperty(default='A')