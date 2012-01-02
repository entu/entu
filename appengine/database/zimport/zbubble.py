from google.appengine.ext import db

from bo import *
from database.zimport.zoin import *
from database.bubble import *


class zBubble(db.Expando):
    def zimport(self):
        b = GetZoin('Bubble', self.key().name())
        if not b:
            b = Bubble()

        if self.name_estonian or self.name_english:
            b.name = Dictionary(
                    name = 'bubble_name',
                    estonian = self.name_estonian,
                    english = self.name_english
                ).put('zimport')

        if self.description_estonian or self.description_english:
            b.description = Dictionary(
                    name = 'bubble_description',
                    estonian = self.description_estonian,
                    english = self.description_english
                ).put('zimport')

        if self.start_datetime:
            b.start_datetime = self.start_datetime

        if self.end_datetime:
            b.end_datetime = self.end_datetime

        if self.type:
            b.type = self.type

        if GetZoinKey('RatingScale', self.rating_scale):
            b.rating_scale = GetZoinKey('RatingScale', self.rating_scale)

        if self.badge_estonian or self.badge_english:
            b.badge = Dictionary(
                name = 'bubble_badge',
                estonian = self.badge_estonian,
                english = self.badge_english
            ).put('zimport')

        if self.points:
            b.points = self.points

        if self.minimum_points:
            b.minimum_points = self.minimum_points

        if self.minimum_bubble_count:
            b.minimum_bubble_count = self.minimum_bubble_count

        if GetZoinKeyList('Bubble', self.mandatory_bubbles):
            b.mandatory_bubbles = MergeLists(b.mandatory_bubbles, GetZoinKeyList('Bubble', self.mandatory_bubbles))

        if GetZoinKeyList('Bubble', self.optional_bubbles):
            b.optional_bubbles = MergeLists(b.optional_bubbles, GetZoinKeyList('Bubble', self.optional_bubbles))

        if GetZoinKeyList('Bubble', self.prerequisite_bubbles):
            b.prerequisite_bubbles = MergeLists(b.prerequisite_bubbles, GetZoinKeyList('Bubble', self.prerequisite_bubbles))

        if self.state:
            b.state = self.state

        if self.series:
            b.series = self.series

        if self.prefix:
            b.prefix = self.prefix

        if GetZoinKey('Counter', self.registry_number_counter):
            b.registry_number_counter = GetZoinKey('Counter', self.registry_number_counter)

        if self.registry_number:
            b.registry_number = self.registry_number

        if self.notes:
            b.notes = self.notes

        if GetZoinKeyList('Person', self.viewers):
            b.viewers = GetZoinKeyList('Person', self.viewers)

        b.put('zimport')

        AddZoin(
            entity_kind = 'Bubble',
            old_key = self.key().name(),
            new_key = b.key(),
        )
        self.delete()


class zBubbleProperty(db.Expando):
    def zimport(self):
        bp = GetZoin('BubbleProperty', self.key().name())
        if not bp:
            bp = BubbleProperty()

        bp.name                 = Dictionary(
                name = 'bubbleproperty_name',
                estonian = self.name_estonian,
                english = self.name_english
            ).put('zimport')
        bp.name_plural                 = Dictionary(
                name = 'bubbleproperty_name_plural',
                estonian = self.name_plural_estonian,
                english = self.name_plural_english
            ).put('zimport')
        bp.data_type            = self.data_type.lower()
        bp.data_property        = self.data_property.lower()
        bp.format_string        = self.format_string
        bp.target_property      = self.target_property
        bp.default              = self.default
        bp.choices              = StrToList(self.choices)
        bp.ordinal              = int(self.ordinal)
        bp.count                = int(self.count)
        bp.is_unique            = self.is_unique
        bp.is_read_only         = self.is_read_only
        bp.is_auto_complete     = self.is_auto_complete
        bp.put('zimport')

        AddZoin(
            entity_kind = 'BubbleProperty',
            old_key = self.key().name(),
            new_key = bp.key(),
        )
        self.delete()


class zBubbleType(db.Expando):
    def zimport(self):
        bt = GetZoin('BubbleType', self.key().name())
        if not bt:
            bt = BubbleType()

        bt.type                 = self.type
        bt.name                 = Dictionary(
                name = 'bubbletype_name',
                estonian = self.name_estonian,
                english = self.name_english
            ).put('zimport')
        bt.name_plural          = Dictionary(
                name = 'bubbletype_name_plural',
                estonian = self.name_plural_estonian,
                english = self.name_plural_english
            ).put('zimport')
        bt.description          = Dictionary(
                name = 'bubbletype_description',
                estonian = self.description_estonian,
                english = self.description_english
            ).put('zimport')
        bt.allowed_subtypes     = StrToList(self.allowed_subtypes)
        bt.grade_display_method = self.grade_display_method
        bt.property_displayname = self.property_displayname
        bt.property_displayinfo = self.property_displayinfo
        bt.bubble_properties    = GetZoinKeyList('BubbleProperty', self.bubble_properties)
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


class zCounter(db.Expando):
    def zimport(self):
        c = GetZoin('Counter', self.key().name())
        if not c:
            c = Counter()

        c.name      = Dictionary(
                name = 'counter_name',
                estonian = self.name_estonian,
                english = self.name_english
            ).put('zimport')
        c.value     = self.value
        c.increment = self.increment
        c.put('zimport')

        AddZoin(
            entity_kind = 'Counter',
            old_key = self.key().name(),
            new_key = c.key(),
        )
        self.delete()


class zDictionary(db.Expando):
    def zimport(self):
        d = GetZoin('Dictionary', self.key().name())
        if not d:
            d = Dictionary()

        d.name      = self.name
        d.estonian  = self.estonian
        d.english   = self.english
        d.put('zimport')

        AddZoin(
            entity_kind = 'Dictionary',
            old_key = self.key().name(),
            new_key = d.key(),
        )
        self.delete()


class zGrade(db.Expando):
    def zimport(self):
        g = GetZoin('Grade', self.key().name())
        if not g:
            g = Grade()

        g.person            = db.Key(self.person_key) if self.person_key else GetZoinKey('Person', self.person)
        g.bubble            = GetZoinKey('Bubble', self.bubble)
        g.subject_name      = Dictionary(
                name = 'grade_suject_name',
                estonian = self.subject_name_est,
                english = self.subject_name_eng
            ).put('zimport')
        g.datetime          = self.datetime
        g.name              = Dictionary(
                name = 'grade_name',
                estonian = self.name_estonian,
                english = self.name_english
            ).put('zimport')
        g.is_positive       = self.is_positive
        g.equivalent        = self.equivalent
        g.points            = self.credit_points
        g.school            = Dictionary(
                name = 'grade_school',
                estonian = self.school_name_estonian,
                english = self.school_name_english
            ).put('zimport')
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


class zGradeDefinition(db.Expando):
    def zimport(self):
        gd = GetZoin('GradeDefinition', self.key().name())
        if not gd:
            gd = GradeDefinition()

        gd.rating_scale     = GetZoinKey('RatingScale', self.rating_scale)
        gd.name             = Dictionary(
                name = 'gradedefinition_name',
                estonian = self.name_estonian,
                english = self.name_english
            ).put('zimport')
        gd.is_positive      = self.is_positive
        gd.equivalent       = self.equivalent
        gd.put('zimport')

        AddZoin(
            entity_kind = 'GradeDefinition',
            old_key = self.key().name(),
            new_key = gd.key(),
        )
        self.delete()


class zRatingScale(db.Expando):
    def zimport(self):
        rs = GetZoin('RatingScale', self.key().name())
        if not rs:
            rs = RatingScale()

        rs.name = Dictionary(
                name = 'ratingscale_name',
                estonian = self.name_estonian,
                english = self.name_english
            ).put('zimport')
        rs.put('zimport')

        AddZoin(
            entity_kind = 'RatingScale',
            old_key = self.key().name(),
            new_key = rs.key(),
        )
        self.delete()
