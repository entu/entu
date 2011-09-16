from google.appengine.ext import db

from bo import *
from database.zimport.zoin import *
from database.bubble import *


class zRatingScale(db.Model):
    name_estonian = db.StringProperty()
    name_english  = db.StringProperty()

    def zimport(self):
        rs = GetZoin('RatingScale', self.key().name())
        if not rs:
            rs = RatingScale()

        name = Dictionary(
            name = 'ratingscale_name',
            estonian = self.name_estonian,
            english = self.name_english
        ).put()

        rs.name = name
        rs.put('zimport')

        AddZoin(
            entity_kind = 'RatingScale',
            old_key = self.key().name(),
            new_key = rs.key(),
        )

        self.delete()


class zGradeDefinition(db.Model):
    rating_scale    = db.StringProperty()
    name_estonian   = db.StringProperty()
    name_english    = db.StringProperty()
    is_positive     = db.BooleanProperty()
    equivalent      = db.IntegerProperty()

    def zimport(self):
        gd = GetZoin('GradeDefinition', self.key().name())
        if not gd:
            gd = GradeDefinition()

        name = Dictionary(
            name = 'gradedefinition_name',
            estonian = self.name_estonian,
            english = self.name_english
        ).put()

        gd.rating_scale     = GetZoinKey('RatingScale', self.rating_scale)
        gd.name             = name
        gd.is_positive      = self.is_positive
        gd.equivalent       = self.equivalent
        gd.put('zimport')

        AddZoin(
            entity_kind = 'GradeDefinition',
            old_key = self.key().name(),
            new_key = gd.key(),
        )

        self.delete()


class zGrade(db.Model):
    person                  = db.StringProperty()
    bubble                  = db.StringProperty()
    datetime                = db.DateTimeProperty()
    name_estonian           = db.StringProperty()
    name_english            = db.StringProperty()
    is_positive             = db.BooleanProperty()
    equivalent              = db.IntegerProperty()
    credit_points           = db.FloatProperty()
    school_name_estonian    = db.StringProperty()
    school_name_english     = db.StringProperty()
    teacher                 = db.StringProperty()
    teacher_name            = db.StringProperty()
    bubbletype              = db.StringProperty()

    def zimport(self):
        g = GetZoin('Grade', self.key().name())
        if not g:
            g = Grade()

        name = Dictionary(
            name = 'grade_name',
            estonian = self.name_estonian,
            english = self.name_english
        ).put()

        school = Dictionary(
            name = 'grade_school_name',
            estonian = self.school_name_estonian,
            english = self.school_name_english
        ).put()

        g.person            = GetZoinKey('Person', self.person)
        g.bubble            = GetZoinKey('Bubble', self.bubble)
        g.datetime          = self.datetime
        g.name              = name
        g.is_positive       = self.is_positive
        g.equivalent        = self.equivalent
        g.points            = self.credit_points
        g.school            = school
        g.teacher           = GetZoinKey('Person', self.teacher)
        g.teacher_name      = self.teacher_name
        g.bubble_type       = self.bubbletype
        g.put('zimport')

        AddZoin(
            entity_kind = 'Grade',
            old_key = self.key().name(),
            new_key = g.key(),
        )

        self.delete()


class zBubbleType(db.Model):
    type                    = db.StringProperty()
    name_estonian           = db.StringProperty()
    name_english            = db.StringProperty()
    description_estonian    = db.StringProperty()
    description_english     = db.StringProperty()
    allowed_subtypes        = db.StringProperty()
    grade_display_method    = db.StringProperty()

    def zimport(self):
        bt = GetZoin('BubbleType', self.key().name())
        if not bt:
            bt = BubbleType()

        name = Dictionary(
            name = 'bubbletype_name',
            estonian = self.name_estonian,
            english = self.name_english
        ).put()
        description = Dictionary(
            name = 'bubble_description',
            estonian = self.description_estonian,
            english = self.description_english
        ).put()

        bt.type                 = self.type
        bt.name                 = name
        bt.description          = description
        bt.allowed_subtypes     = StrToList(self.allowed_subtypes)
        bt.grade_display_method = StrToList(self.grade_display_method)
        bt.put('zimport')

        AddZoin(
            entity_kind = 'BubbleType',
            old_key = self.key().name(),
            new_key = bt.key(),
        )

        self.delete()


class zBubble(db.Model):
    order                   = db.IntegerProperty()
    name_estonian           = db.StringProperty()
    name_english            = db.StringProperty()
    description_estonian    = db.TextProperty()
    description_english     = db.TextProperty()
    start_datetime          = db.DateTimeProperty()
    end_datetime            = db.DateTimeProperty()
    location                = db.StringProperty()   #not imported
    owner                   = db.StringProperty()
    editors                 = db.TextProperty()
    viewers                 = db.TextProperty()
    type                    = db.StringProperty()
    typed_tags              = db.TextProperty()
    rating_scale            = db.StringProperty()
    badge_estonian          = db.StringProperty()
    badge_english           = db.StringProperty()
    points                  = db.FloatProperty()
    minimum_points          = db.FloatProperty()
    minimum_bubble_count    = db.IntegerProperty()
    mandatory_bubbles       = db.TextProperty()
    optional_bubbles        = db.TextProperty()
    prerequisite_bubbles    = db.TextProperty()
    entities                = db.TextProperty()
    state                   = db.StringProperty()

    def zimport(self):
        b = GetZoin('Bubble', self.key().name())
        if not b:
            b = Bubble()

        name = Dictionary(
            name = 'bubble_name',
            estonian = self.name_estonian,
            english = self.name_english
        ).put()
        description = Dictionary(
            name = 'bubble_description',
            estonian = self.description_estonian,
            english = self.description_english
        ).put()
        badge = Dictionary(
            name = 'bubble_badge',
            estonian = self.badge_estonian,
            english = self.badge_english
        ).put()

        b.name                  = name
        b.description           = description
        b.start_datetime        = self.start_datetime
        b.end_datetime          = self.end_datetime
        b.owner                 = GetZoinKey('Person', self.owner)
        b.editors               = GetZoinKeyList('Person', self.editors)
        b.viewers               = GetZoinKeyList('Person', self.viewers)
        b.type                  = self.type
        b.typed_tags            = StrToList(self.typed_tags)
        b.rating_scale          = GetZoinKey('RatingScale', self.rating_scale)
        b.badge                 = badge
        b.points                = self.points
        b.minimum_points        = self.minimum_points
        b.minimum_bubble_count  = self.minimum_bubble_count
        b.mandatory_bubbles     = GetZoinKeyList('Bubble', self.mandatory_bubbles)
        b.optional_bubbles      = GetZoinKeyList('Bubble', self.optional_bubbles)
        b.prerequisite_bubbles  = GetZoinKeyList('Bubble', self.prerequisite_bubbles)
        b.entities              = GetZoinKeyList('Bubble', self.entities)
        b.state                 = self.state
        b.put('zimport')

        AddZoin(
            entity_kind = 'Bubble',
            old_key = self.key().name(),
            new_key = b.key(),
        )

        self.delete()