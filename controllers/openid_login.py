from boFunctions import *
from models import *


class OpenIdLoginHandler(webapp.RequestHandler):
    def get(self):
        continue_url = self.request.GET.get('continue')
        openid_url = self.request.GET.get('openid')

        if continue_url:
            continue_url = continue_url.encode('utf8')
        else:
            continue_url = ''

        if not openid_url:
            boView(self, 'login', 'login.html', { 'continue': continue_url })
        else:
            self.redirect(users.create_login_url(continue_url, None, openid_url))


def main():
    boWSGIApp([
             ('/_ah/login_required', OpenIdLoginHandler),
            ])


if __name__ == '__main__':
    main()


#115198393782155764401