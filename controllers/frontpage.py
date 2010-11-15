from bo import *


class Frontpage(webapp.RequestHandler):
    def get(self):
        if users.get_current_user():
            self.redirect('/dashboard')
        else:
            View(self, '', 'frontpage.html')


def main():
    Route([
             ('/', Frontpage),
            ])


if __name__ == '__main__':
    main()