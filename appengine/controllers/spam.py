from bo import *
from database.bubble import *
from database.person import *


class ShowNewSpam(boRequestHandler):
    def get(self):
        redirect = self.request.get('r').strip()
        bubble_id = self.request.get('b').strip()
        persons_ids = self.request.get('p').strip().strip('.').split('.')
        if persons_ids:
            persons_ids = [int(i) for i in persons_ids]

        bubble = Bubble().get_by_id(int(bubble_id))
        persons = Person().get_by_id(persons_ids)

        self.view('', 'spam/new_message.html', {
            'bubble': bubble,
            'persons': persons,
            'redirect': redirect,
        })

    def post(self):
        redirect = self.request.get('redirect').strip()
        bubble_id = self.request.get('bubble').strip()
        persons_ids = self.request.get('persons').strip().strip('.').split('.')
        subject = self.request.get('subject').strip()
        message = self.request.get('message').strip()

        if persons_ids:
            persons_ids = [int(i) for i in persons_ids]

        bubble = Bubble().get_by_id(int(bubble_id))
        if bubble:
            subject = subject.replace('{bubble_name}', bubble.displayname)
            message = message.replace('{bubble_name}', bubble.displayname)
            subject = subject.replace('{bubble_url}', bubble.url if bubble.url else '')
            message = message.replace('{bubble_url}',  bubble.url if bubble.url else '')
            subject = subject.replace('{bubble_date}', bubble.displaydate)
            message = message.replace('{bubble_date}', bubble.displaydate)


        for person in Person().get_by_id(persons_ids):
            self.echo(', '.join(person.emails))
            SendMail(
                to = person.emails,
                reply_to = 'sisseastumine@artun.ee',
                subject = subject.replace('{person_name}', person.displayname),
                message = message.replace('{person_name}', person.displayname),
                html = False
            )


def main():
    Route([
            ('/spam', ShowNewSpam),
        ])


if __name__ == '__main__':
    main()