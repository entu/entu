from google.appengine.api import taskqueue

from bo import *
from database.bubble import *
from database.person import *

# how to add task:
# taskqueue.Task(url='/taskqueue/...', params={...}).add(queue_name='my-custom-queue')


class BubblePassLeechers(boRequestHandler):
    def post(self):
        bubble_key = self.request.get('bubble_key')
        person_key = self.request.get('person_key')

        if bubble_key and person_key:
            bubble = Bubble().get(bubble_key)
            person = Person().get(person_key)

            if bubble.next_in_line:
                for nextbubble_key in bubble.next_in_line:
                    person.add_leecher(nextbubble_key)


class BubbleChangeLeecher(boRequestHandler):
    def post(self):
        action = self.request.get('action')
        bubble_key = self.request.get('bubble_key')
        person_key = self.request.get('person_key')

        if action in ['add', 'remove'] and bubble_key and person_key:
            bubble = Bubble().get(bubble_key)
            if action == 'add':
                bubble.add_leecher(db.Key(person_key))
            if action == 'remove':
                bubble.remove_leecher(db.Key(person_key))


def main():
    Route([
            ('/taskqueue/bubble_pass_leechers', BubblePassLeechers),
            ('/taskqueue/bubble_change_leecher', BubbleChangeLeecher),
        ])


if __name__ == '__main__':
    main()