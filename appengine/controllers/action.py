from datetime import *

from bo import *
from database.bubble import *
from database.dictionary import *


class TimeSlot(boRequestHandler):
    def get(self, bubble_id):
        bubble = Bubble().get_by_id(int(bubble_id))
        if not bubble.Authorize('viewer'):
            self.error(404)
            return

        self.view(
            main_template = '',
            template_file = 'action/timeslot.html',
            values = {
                'bubble': bubble,
            }
        )

    def post(self, bubble_id):
        AddTask('/taskqueue/action_timeslot/%s' % bubble_id, {
            'start': self.request.get('start').strip(),
            'end': self.request.get('end').strip(),
            'interval': self.request.get('interval').strip(),
            'user': CurrentUser()._googleuser
        }, 'one-by-one')


def main():
    Route([
            (r'/action/timeslot/(.*)', TimeSlot),
        ])


if __name__ == '__main__':
    main()
