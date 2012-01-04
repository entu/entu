from google.appengine.api import taskqueue

import csv
import cStringIO

from bo import *
from database.bubble import *
from database.person import *
from database.feedback import *

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


class BubbleCopyLeechers(boRequestHandler):
    def post(self):
        from_bubble_key = self.request.get('from_bubble_key')
        to_bubble_key = self.request.get('to_bubble_key')

        if from_bubble_key and to_bubble_key:
            from_bubble = Bubble().get(from_bubble_key)

            if from_bubble.leechers:
                for person in Person().get(from_bubble.leechers):
                    person.add_leecher(db.Key(to_bubble_key))


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


class BubbleChangeSeeder(boRequestHandler):
    def post(self):
        action = self.request.get('action')
        bubble_key = self.request.get('bubble_key')
        person_key = self.request.get('person_key')

        if action in ['add', 'remove'] and bubble_key and person_key:
            bubble = Bubble().get(bubble_key)
            if action == 'add':
                bubble.seeders = AddToList(db.Key(person_key), bubble.seeders)
                bubble.put()


class PersonMerge(boRequestHandler):
    def post(self):
        source_ids = StrToList(self.request.get('source_ids'))
        target_key = self.request.get('target_key')

        target_p = Person().get(target_key)
        if target_p:
            target_pk = target_p.key()
            for source_id in source_ids:
                source_p = Person().get_by_id(int(source_id))
                source_pk = source_p.key()

                for m in db.Query(Cv).filter('person', source_pk):
                    m.person = target_pk
                    m.put()

                for m in db.Query(Contact).filter('person', source_pk):
                    m.person = target_pk
                    m.put()

                for m in db.Query(Message).filter('person', source_pk):
                    m.person = target_pk
                    m.put()

                for d in db.Query(Document).filter('uploader', source_pk):
                    d.uploader = target_pk
                    d.put()
                for d in db.Query(Document).filter('owners', source_pk):
                    d.owners = RemoveFromList(source_pk, d.owners)
                    d.owners = AddToList(target_pk, d.owners)
                    d.put()
                for d in db.Query(Document).filter('editors', source_pk):
                    d.editors = RemoveFromList(source_pk, d.editors)
                    d.editors = AddToList(target_pk, d.editors)
                    d.put()
                for d in db.Query(Document).filter('viewers', source_pk):
                    d.viewers = RemoveFromList(source_pk, d.viewers)
                    d.viewers = AddToList(target_pk, d.viewers)
                    d.put()

                for b in db.Query(Bubble).filter('owners', source_pk):
                    b.owners = RemoveFromList(source_pk, d.owners)
                    b.owners = AddToList(target_pk, d.owners)
                    b.put()
                for b in db.Query(Bubble).filter('editors', source_pk):
                    b.editors = RemoveFromList(source_pk, b.editors)
                    b.editors = AddToList(target_pk, b.editors)
                    b.put()
                for b in db.Query(Bubble).filter('viewers', source_pk):
                    b.viewers = RemoveFromList(source_pk, b.viewers)
                    b.viewers = AddToList(target_pk, b.viewers)
                    b.put()
                for b in db.Query(Bubble).filter('seeders', source_pk):
                    b.seeders = RemoveFromList(source_pk, b.seeders)
                    b.seeders = AddToList(target_pk, b.seeders)
                    b.put()
                for b in db.Query(Bubble).filter('leechers', source_pk):
                    b.leechers = RemoveFromList(source_pk, b.leechers)
                    b.leechers = AddToList(target_pk, b.leechers)
                    b.put()

                for bp in db.Query(BubblePerson).filter('person', source_pk):
                    bp.person = target_pk
                    bp.put()

                for g in db.Query(Grade).filter('person', source_pk):
                    g.person = target_pk
                    g.put()
                for g in db.Query(Grade).filter('teacher', source_pk):
                    g.teacher = target_pk
                    g.teacher_name = target_p.displayname
                    g.put()

                for q in db.Query(Questionary).filter('manager', source_pk):
                    q.manager = target_pk
                    q.put()
                for qp in db.Query(QuestionaryPerson).filter('person', source_pk):
                    qp.person = target_pk
                    qp.put()
                for qa in db.Query(QuestionAnswer).filter('person', source_pk):
                    qa.person = target_pk
                    qa.put()
                for qa in db.Query(QuestionAnswer).filter('target_person', source_pk):
                    qa.target_person = target_pk
                    qa.put()











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
                genders[g_key] = {'name': self.translate('gender_' + str(person.gender)), 'value': 1, 'list': [person_key]}
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
            ('/taskqueue/bubble_copy_leechers', BubbleCopyLeechers),
            ('/taskqueue/bubble_change_leecher', BubbleChangeLeecher),
            ('/taskqueue/bubble_change_seeder', BubbleChangeSeeder),
            ('/taskqueue/person_merge', PersonMerge),
            ('/taskqueue/application_stats', ApplicationStats),
        ])


if __name__ == '__main__':
    main()
