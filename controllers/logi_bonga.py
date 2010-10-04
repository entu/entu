import hashlib
import datetime

from helpers import *


class Login(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        sool = 'jebitritvojebohumat'
        user_name = user.nickname()
        user_key = hashlib.md5(user.nickname() + datetime.date.today().strftime('%Y-%m-%d') + sool).hexdigest()
        self.redirect('https://ois.artun.ee/logi_bonga.asp?u=' + str(user_name) + '&k=' + str(user_key))


class Logout(webapp.RequestHandler):
    def get(self):
        self.redirect(users.create_logout_url('https://ois.artun.ee/logivalja.asp'))


def main():
    Route([
             ('/logi_bonga/exit', Logout),
             ('/logi_bonga', Login),
            ])


if __name__ == '__main__':
    main()