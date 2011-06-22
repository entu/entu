from bo import *


class Frontpage(boRequestHandler):
    def get(self):
        if users.get_current_user():
            self.redirect('/dashboard')
        else:
            self.view('', 'frontpage.html')


def main():
    Route([
             ('/', Frontpage),
            ])


if __name__ == '__main__':
    main()