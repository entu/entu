from tornado import web

from main.helper import *


class ShowAuthPage(myRequestHandler):
    """
    Show Log in page.

    """
    def get(self):
        self.clear_all_cookies()
        self.clear_all_cookies(domain=self.settings['cookie_domain'])

        redirect_url = self.get_argument('next', '', strip=True)
        if redirect_url:
            if 'http' not in redirect_url:
                redirect_url = self.request.protocol + '://' + self.request.host + redirect_url

        if self.get_cookie('auth_provider'):
            self.redirect('%s/%s?next=%s' % (self.settings['auth_url'], self.get_cookie('auth_provider'), redirect_url))
        else:
            self.render('user/template/auth.html',
                redirect_url = redirect_url,
                mobileid = '%s/mobile-id' % self.settings['auth_url'],
                idcard = '%s/id-card?next=%s' % (self.settings['auth_url'], redirect_url),
                google = '%s/google?next=%s' % (self.settings['auth_url'], redirect_url),
                facebook = '%s/facebook?next=%s' % (self.settings['auth_url'], redirect_url),
                live = '%s/live?next=%s' % (self.settings['auth_url'], redirect_url),
                taat = '%s/taat?next=%s' % (self.settings['auth_url'], redirect_url)
            )


handlers = [
    ('/auth', ShowAuthPage)
]
