from google.appengine.api import taskqueue

import csv
import cStringIO

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


class ApplicationStats(boRequestHandler):
    def post(self):
        email = self.request.get('email')

        bubbles = {}
        genders = {}
        ages = {}
        bubbles_list = []
        persons_list = []

        for g in db.Query(Grade).filter('bubble_type', 'submission').filter('is_deleted', False).filter('is_locked', True).filter('is_positive', True).fetch(limit=3000):

            bubble = g.bubble
            person = g.person

            bubble_key = str(bubble.key())
            person_key = str(person.key())

            bubbles_list.append(g.key())
            persons_list.append(g.person.key())


            if bubble_key not in bubbles:
                bubbles[bubble_key] = {'name': bubble.displayname, 'value': 1}
            else:
                bubbles[bubble_key]['value'] += 1

            if person.gender:
                g_key = str(person.gender)
            else:
                g_key = 'NONE'
            if g_key not in genders:
                genders[g_key] = {'name': Translate('gender_' + str(person.gender)), 'value': 1, 'list': [person_key]}
            else:
                genders[g_key]['list'] = AddToList(person_key, genders[g_key]['list'])
                genders[g_key]['value'] = len(genders[g_key]['list'])

            if person.age:
                a_key = person.age
            else:
                a_key = 'NONE'
            if a_key not in ages:
                ages[a_key] = {'name': a_key, 'value': 1, 'list': [person_key]}
            else:
                ages[a_key]['list'] = AddToList(person_key, ages[a_key]['list'])
                ages[a_key]['value'] = len(ages[a_key]['list'])

        attachments = []

        csvfile = cStringIO.StringIO()
        csvWriter = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
        for b in sorted(list(bubbles.values()), key=lambda k: k['value'], reverse=True):
            csvWriter.writerow([
                b['name'].encode("utf-8"),
                b['value'],
            ])
        attachments.append(('Bubble.csv', csvfile.getvalue()))
        csvfile.close()

        csvfile = cStringIO.StringIO()
        csvWriter = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
        for g in sorted(list(genders.values()), key=lambda k: k['value'], reverse=True):
            csvWriter.writerow([
                g['name'].encode("utf-8"),
                g['value'],
            ])
        attachments.append(('Gender.csv', csvfile.getvalue()))
        csvfile.close()

        csvfile = cStringIO.StringIO()
        csvWriter = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
        for a in sorted(list(ages.values()), key=lambda k: k['value'], reverse=True):
            csvWriter.writerow([
                a['name'],
                a['value'],
            ])
        attachments.append(('Age.csv', csvfile.getvalue()))
        csvfile.close()

        SendMail(
            to = email,
            subject = 'Application statistics',
            message = 'Bubbles: ' + str(len(list(set(bubbles_list)))) + '\n' + 'Persons: ' + str(len(list(set(persons_list)))),
            html = False,
            attachments = attachments,
        )



def main():
    Route([
            ('/taskqueue/bubble_pass_leechers', BubblePassLeechers),
            ('/taskqueue/bubble_change_leecher', BubbleChangeLeecher),
            ('/taskqueue/application_stats', ApplicationStats),
        ])


if __name__ == '__main__':
    main()