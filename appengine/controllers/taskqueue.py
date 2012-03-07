from bo import *
from database.bubble import *

class AddBubbleRights(boRequestHandler):
    def post(self):
        bubble = Bubble().get(self.request.get('bubble').strip())
        #person = Bubble().get(self.request.get('person').strip())
        person = db.get(self.request.get('person').strip())
        if person.kind() != 'Bubble':
            logging.error('Will skip %s %s' % (person.kind(), person.key()))
            return

        bubble.AddRight(
            person_keys = person.key(),
            right = self.request.get('right').strip(),
            user = self.request.get('user').strip()
        )


class AddBubbleRelation(boRequestHandler):
    def post(self):
        bubble = Bubble().get(self.request.get('bubble').strip())
        related_bubble = Bubble().get(self.request.get('related_bubble').strip())
        type = self.request.get('type').strip()
        user = self.request.get('user').strip()

        if not bubble or not related_bubble or not type:
            return

        # Add rights
        bubble.AddValue('x_br_%s' % type, related_bubble.key())
        bubble.put(user)

        # Set BubbleRelation
        br = db.Query(BubbleRelation).filter('bubble', bubble.key()).filter('related_bubble', related_bubble.key()).filter('type', type).get()
        if not br:
            br = BubbleRelation()
            br.bubble = bubble.key()
            br.related_bubble = related_bubble.key()
        br.type = type
        br.x_is_deleted = False
        br.put(user)


class RemoveBubbleRelation(boRequestHandler):
    def post(self):
        bubble = Bubble().get(self.request.get('bubble').strip())
        related_bubble = Bubble().get(self.request.get('related_bubble').strip())
        type = self.request.get('type').strip()
        user = self.request.get('user').strip()

        if not bubble or not related_bubble or not type:
            return

        # Remove rights
        bubble.RemoveValue('x_br_%s' % type, related_bubble.key())
        bubble.put(user)

        # Remove BubbleRelation
        br = db.Query(BubbleRelation).filter('bubble', bubble.key()).filter('related_bubble', related_bubble.key()).filter('type', type).get()
        if br:
            br.x_is_deleted = True
            br.put(user)


def main():
    Route([
            ('/taskqueue/rights', AddBubbleRights),
            ('/taskqueue/add_relation', AddBubbleRelation),
            ('/taskqueue/remove_relation', RemoveBubbleRelation),
        ])


if __name__ == '__main__':
    main()
