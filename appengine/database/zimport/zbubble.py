from google.appengine.ext import db

from bo import *
from database.zimport.zoin import *
from database.bubble import *


class zRatingScale(db.Expando):
    def zimport(self):
        rs = GetZoin('RatingScale', self.key().name())
        if not rs:
            rs = RatingScale()

        name = Dictionary(
            name = 'ratingscale_name',
            estonian = self.name_estonian,
            english = self.name_english
        ).put('zimport')

        rs.name = name
        rs.put('zimport')

        AddZoin(
            entity_kind = 'RatingScale',
            old_key = self.key().name(),
            new_key = rs.key(),
        )
        self.delete()


class zGradeDefinition(db.Expando):
    def zimport(self):
        gd = GetZoin('GradeDefinition', self.key().name())
        if not gd:
            gd = GradeDefinition()

        name = Dictionary(
            name = 'gradedefinition_name',
            estonian = self.name_estonian,
            english = self.name_english
        ).put('zimport')

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


class zGrade(db.Expando):
    def zimport(self):
        g = GetZoin('Grade', self.key().name())
        if not g:
            g = Grade()

        name = Dictionary(
            name = 'grade_name',
            estonian = self.name_estonian,
            english = self.name_english
        ).put('zimport')

        school = Dictionary(
            name = 'grade_school',
            estonian = self.school_name_estonian,
            english = self.school_name_english
        ).put('zimport')

        suject_name = Dictionary(
            name = 'grade_suject_name',
            estonian = self.subject_name_est,
            english = self.subject_name_eng
        ).put('zimport')

        g.person            = db.Key(self.person_key) if self.person_key else GetZoinKey('Person', self.person)
        g.bubble            = GetZoinKey('Bubble', self.bubble)
        g.subject_name      = suject_name
        g.datetime          = self.datetime
        g.name              = name
        g.is_positive       = self.is_positive
        g.equivalent        = self.equivalent
        g.points            = self.credit_points
        g.school            = school
        g.teacher           = GetZoinKey('Person', self.teacher)
        g.teacher_name      = self.teacher_name
        g.bubble_type       = self.bubbletype
        g.typed_tags        = StrToList(self.typed_tags)
        g.put('zimport')

        AddZoin(
            entity_kind = 'Grade',
            old_key = self.key().name(),
            new_key = g.key(),
        )
        self.delete()


class zBubbleType(db.Expando):
    def zimport(self):
        bt = GetZoin('BubbleType', self.key().name())
        if not bt:
            bt = BubbleType()

        name = Dictionary(
            name = 'bubbletype_name',
            estonian = self.name_estonian,
            english = self.name_english
        ).put('zimport')
        description = Dictionary(
            name = 'bubbletype_description',
            estonian = self.description_estonian,
            english = self.description_english
        ).put('zimport')

        bt.type                 = self.type
        bt.name                 = name
        bt.description          = description
        bt.allowed_subtypes     = StrToList(self.allowed_subtypes)
        bt.grade_display_method = self.grade_display_method
        bt.property_displayname = self.property_displayname
        bt.property_displayinfo = self.property_displayinfo
        bt.optional_properties  = GetZoinKeyList('BubbleProperty', self.optional_properties)
        bt.mandatory_properties = GetZoinKeyList('BubbleProperty', self.mandatory_properties)
        bt.public_properties    = GetZoinKeyList('BubbleProperty', self.public_properties)
        bt.propagated_properties = GetZoinKeyList('BubbleProperty', self.propagated_properties)
        bt.escalated_properties = GetZoinKeyList('BubbleProperty', self.escalated_properties)
        bt.inherited_properties = GetZoinKeyList('BubbleProperty', self.inherited_properties)
        bt.put('zimport')

        AddZoin(
            entity_kind = 'BubbleType',
            old_key = self.key().name(),
            new_key = bt.key(),
        )
        self.delete()


class zBubbleProperty(db.Expando):
    def zimport(self):
        bp = GetZoin('BubbleProperty', self.key().name())
        if not bp:
            bp = BubbleProperty()

        name = Dictionary(
            name = 'tagtype_name',
            estonian = self.name_estonian,
            english = self.name_english
        ).put('zimport')

        bp.name                 = name
        bp.count                = int(self.count)
        bp.ordinal              = int(self.ordinal)
        bp.data_property        = self.data_property.lower()
        bp.data_type            = self.data_type.lower()
        bp.default              = self.default
        bp.choices              = StrToList(self.choices)
        bp.is_unique            = True if self.is_unique.lower() == 'true' else False
        bp.put('zimport')

        AddZoin(
            entity_kind = 'BubbleProperty',
            old_key = self.key().name(),
            new_key = bp.key(),
        )
        self.delete()


class zBubble(db.Expando):
    def zimport(self):
        b = GetZoin('Bubble', self.key().name())
        if not b:
            b = Bubble()

        name = Dictionary(
            name = 'bubble_name',
            estonian = self.name_estonian,
            english = self.name_english
        ).put('zimport')
        description = Dictionary(
            name = 'bubble_description',
            estonian = self.description_estonian,
            english = self.description_english
        ).put('zimport')
        badge = Dictionary(
            name = 'bubble_badge',
            estonian = self.badge_estonian,
            english = self.badge_english
        ).put('zimport')

        b.name                  = name
        b.description           = description
        b.start_datetime        = self.start_datetime
        b.end_datetime          = self.end_datetime
        #b.owners                = GetZoinKey('Person', self.owners)
        #b.editors               = GetZoinKeyList('Person', self.editors)
        #b.viewers               = GetZoinKeyList('Person', self.viewers)
        b.type                  = self.type
        b.typed_tags            = StrToList(self.typed_tags)
        b.rating_scale          = GetZoinKey('RatingScale', self.rating_scale)
        b.badge                 = badge
        b.points                = self.points
        b.minimum_points        = self.minimum_points
        b.minimum_bubble_count  = self.minimum_bubble_count
        b.mandatory_bubbles     = MergeLists(b.mandatory_bubbles, GetZoinKeyList('Bubble', self.mandatory_bubbles))
        b.optional_bubbles      = MergeLists(b.optional_bubbles, GetZoinKeyList('Bubble', self.optional_bubbles))
        b.prerequisite_bubbles  = MergeLists(b.prerequisite_bubbles, GetZoinKeyList('Bubble', self.prerequisite_bubbles))
        b.state                 = self.state
        b.put('zimport')

        AddZoin(
            entity_kind = 'Bubble',
            old_key = self.key().name(),
            new_key = b.key(),
        )
        self.delete()


