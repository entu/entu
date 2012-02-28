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
        right = self.request.get('right').strip()
        user = self.request.get('user').strip()

        rights = ['viewer', 'subbubbler', 'editor', 'owner']

        if not bubble or not person:
            return

        # Remove rights
        for r in rights:
            bubble.RemoveValue('x_br_%s' % r, person.key())
            bubble.put(user)

        # Add rights
        if right:
            bubble.SetValue('x_br_%s' % right, person.key())
            bubble.put(user)

        # Remove BubbleRelation
        for br in db.Query(BubbleRelation).filter('bubble', bubble.key()).filter('related_bubble', person.key()).filter('type IN', rights).fetch(100):
            br.x_is_deleted = True
            br.put(user)

        # Set BubbleRelation
        if right:
            br = db.Query(BubbleRelation).filter('bubble', bubble.key()).filter('related_bubble', person.key()).filter('type', right).get()
            if not br:
                br = BubbleRelation()
                br.bubble = bubble.key()
                br.related_bubble = person.key()
            br.type = right
            br.x_is_deleted = False
            br.put(user)

        logging.debug('right:%s user:%s' % (right, user))


def main():
    Route([
            ('/taskqueue/rights', AddBubbleRights),
        ])


if __name__ == '__main__':
    main()
