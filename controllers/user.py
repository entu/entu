from google.appengine.api import users
from google.appengine.api import images
import urllib

from boFunctions import *
from models import *
from forms import *


class Activate(webapp.RequestHandler):

    def get(self, email = None, key = None):

        email = urllib.unquote(email).decode('utf8')
        key = urllib.unquote(key).decode('utf8')

        if email and key and users.get_current_user().federated_identity():
            c = db.Query(Contact).filter('type =', 'email').filter('value =', email).filter('activation_key =', key).get()

        if c:
            c.activation_key = None
            c.save()

            p = db.get(c.person.key())
            p.identities.append(users.get_current_user().federated_identity())
            p.save()

            self.redirect('/user/preferences')
        else:
            self.redirect('/')


class Preferences(webapp.RequestHandler):

    def get(self):
        p = boUser()
        form = UserPreferencesForm(self.request.POST, p)
        form.avatar.data = None

        boView(self, 'user_preferences', 'user_preferences.html', { 'form': form, 'person': p })

    def post(self):
        form = UserPreferencesForm(self.request.POST)

        if form.validate():
            p = boUser()
            p.forename = form.forename.data
            p.surname = form.surname.data
            p.language = form.language.data
            if self.request.get("avatar"):
                p.avatar = db.Blob(boRescale(self.request.get("avatar"), 40, 40))
            p.save()

        self.redirect('')


class ShowAvatar(webapp.RequestHandler):

    def get(self, key = None):
        try:
            if key:
                u = db.get(key)
                if (u and u.avatar):
                    self.response.headers['Content-Type'] = "image/png"
                    self.response.out.write(u.avatar)
                else:
                    self.redirect('/images/avatar.png')
        except:
            pass

def main():
    boWSGIApp([
              (r'/user/activate/(.*)/(.*)', Activate),
              (r'/user/preferences', Preferences),
              (r'/user/avatar/(.*)', ShowAvatar),
             ])


if __name__ == '__main__':
    main()