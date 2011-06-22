from bo import *
from database.bubble import *
from database.person import *

class SendToBubbleLeechers(boRequestHandler):
    def get(self, key):
        bubble = Bubble().get(key)
        if bubble:

            leechers = [p.displayname for p in Person().get(bubble.leechers)]
            leechers.sort()

            self.view('', 'spam/bubble.html', {
                'bubble': bubble,
                'leechers': leechers,
            })

    def post(self, key):
        subject = self.request.get('subject').strip()
        message = self.request.get('message').strip()

        bubble = Bubble().get(key)
        if bubble:

            for leecher in Person().get(bubble.leechers):
                self.echo(','.join(leecher.emails) + ' ' + subject + ' ' + message)

                SendMail(
                    to = leecher.emails,
                    reply_to = 'sisseastumine@artun.ee',
                    subject = subject,
                    message = message,
                    html = False,
                )


def main():
    Route([
            ('/spam/bubble/(.*)', SendToBubbleLeechers)
        ])


if __name__ == '__main__':
    main()