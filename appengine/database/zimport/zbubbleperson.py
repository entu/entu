from google.appengine.ext import db

from bo import *
from database.zimport.zoin import *
from database.bubble import *
from database.person import *


class zBubblePerson(db.Expando):
    def zimport(self):
        p = Person().get(self.person)
        bubble_key = GetZoinKey('Bubble', self.bubble_old_id)

        if p and bubble_key:
            p.leecher = AddToList(bubble_key, p.leecher)
            p.put('zimport')

            b = Bubble().get(bubble_key)
            if b:
                b.leechers = AddToList(db.Key(self.person), b.leechers)
                b.put('zimport')

            self.delete()
