# -*- coding: utf-8 -*-

from bo import *
from database.bubble import *

class AddBubbleRights(boRequestHandler):
    def post(self):
        bubble = Bubble().get(self.request.get('bubble').strip())
        if not bubble:
            return

        #person = Bubble().get(self.request.get('person').strip())
        person = db.get(self.request.get('person').strip())
        if person.kind() != 'Bubble':
            logging.info('Will skip %s %s' % (person.kind(), person.key()))
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



# Actions tasks

class TimeSlot(boRequestHandler):
    def post(self, bubble_id):
        start_str = self.request.get('start').strip()
        end_str = self.request.get('end').strip()
        interval_str = self.request.get('interval', '60').strip()

        if not start_str or not end_str or not interval_str:
            return

        bubble = Bubble().get_by_id(int(bubble_id))
        bt_key = db.Query(Bubble, keys_only=True).filter('type', 'bubble_type').filter('path', 'personal_time_slot').get()

        interval = int(interval_str)
        start = UtcFromLocalDateTime(datetime.strptime('%s:00' % start_str, '%d.%m.%Y %H:%M:%S'))
        end = UtcFromLocalDateTime(datetime.strptime('%s:00' % end_str, '%d.%m.%Y %H:%M:%S'))
        timeslot = start
        times = []
        while timeslot < end:
            start_datetime = timeslot
            timeslot = timeslot + timedelta(minutes=interval)
            end_datetime = timeslot
            newbubble = bubble.AddSubbubble(bt_key, {'start_datetime': start_datetime, 'end_datetime': end_datetime})


class SendPrivateRatingList(boRequestHandler):
    def post(self, bubble_id):
        bubble = Bubble().get_by_id(int(bubble_id))
        message_bt = db.Query(Bubble).filter('path', 'message').get()

        subjecttext = bubble.displayname + u' - pingerida'
        for leecher in bubble.GetRelatives('leecher'):
            logging.info(bubble.displayname + ': ' + leecher.displayname + ': ' + self.request.host_url + '/application/ratings/' + bubble_id + '/' + str(leecher.key()))

            messagetext = leecher.displayname + u'<br><br>Sinu ' + bubble.displayname + u' vastuvõtu pingerida on siin:<br>' + self.request.host_url + '/application/ratings/' + bubble_id + '/' + str(leecher.key()) + u'<br><br>Vastuvõtt<br>6267 305<br>helen.jyrgens@artun.ee'

            email = leecher.email
            # email = 'mihkel.putrinsh@artun.ee'
            SendMail(
                to = email,
                subject = subjecttext,
                message = messagetext,
            )

            message = leecher.AddSubbubble(message_bt.key())
            message.x_created_by = 'helen.jyrgens@artun.ee'
            # continue # for debuggig purposes only
            message.put()

            #
            # HACK alert!
            #
            value = message.SetProperty(
                propertykey = 'agpzfmJ1YmJsZWR1cg8LEgZCdWJibGUYk7zUAgw',
                oldvalue = '',
                newvalue = messagetext if len(messagetext) <= 500 else messagetext[:500]
            )


def main():
    Route([
            ('/taskqueue/rights', AddBubbleRights),
            ('/taskqueue/add_relation', AddBubbleRelation),
            ('/taskqueue/remove_relation', RemoveBubbleRelation),
            (r'/taskqueue/action_timeslot/(.*)', TimeSlot),
            (r'/taskqueue/private_rating_list/(.*)', SendPrivateRatingList),
        ])


if __name__ == '__main__':
    main()
