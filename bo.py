import os
from types import ListType
from pytz.gae import pytz
from google.appengine.api import mail
from google.appengine.api import users
from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp import util
from django.core.validators import email_re
from django.template.defaultfilters import striptags
from django.utils import simplejson

from datetime import timedelta
import random
import time
import logging

from settings import *


def Route(url_mapping):
    application = webapp.WSGIApplication(url_mapping, debug=True)
    util.run_wsgi_app(application)


class boRequestHandler(webapp.RequestHandler):
    def __init__(self, *args, **kwargs):
        self.starttime = time.time()
        webapp.RequestHandler.__init__(self, *args, **kwargs)

    def authorize(self, controller=None):
        from database.person import *
        #from database.feedback import *

        #if db.Query(QuestionaryPerson).filter('person', Person().current).filter('is_completed', False).filter('is_obsolete', False).get():
        if 1==2:
            #path = str(self.request.url)
            #Cache().set('redirect_after_feedback', path)
            #self.redirect('/feedback')
            #return False
            return True
        else:
            if controller and users.is_current_user_admin() == False:
                rights = []
                for role in Person().current.roles:
                    rights = rights + role.role.rights
                if controller in rights:
                    return True
                else:
                    return False
            else:
                return True

    def view(self, page_title, templatefile, values={}):
        controllertime = (time.time() - self.starttime)
        logging.debug('Controller: %ss' % round(controllertime, 2))
        from database.person import *

        browser = str(self.request.headers['User-Agent'])
        if browser.find('MSIE 5') > -1 or browser.find('MSIE 6') > -1 or browser.find('MSIE 7') > -1:
            path = os.path.join(os.path.dirname(__file__), 'templates', 'brausererror.html')
            self.response.out.write(template.render(path, {}))
        else:
            values['str'] = Translate()
            values['system_title'] = SYSTEM_TITLE.decode('utf8')
            values['system_logo'] = SYSTEM_LOGO_URL.decode('utf8')
            if page_title:
                values['site_name'] = SYSTEM_TITLE.decode('utf8') + ' - ' + Translate(page_title)
                values['page_title'] = Translate(page_title)
            else:
                values['site_name'] = SYSTEM_TITLE.decode('utf8')
                values['page_title'] = '&nbsp;'
            values['site_url'] = self.request.headers.get('host')
            values['user'] = Person().current
            values['loginurl'] = users.create_login_url('/')
            values['logouturl'] = users.create_logout_url('/')
            path = os.path.join(os.path.dirname(__file__), 'templates', templatefile)
            self.response.out.write(template.render(path, values))
        viewtime = (time.time() - self.starttime)
        logging.debug('View: %ss' % round((viewtime - controllertime), 2))
        logging.debug('Total: %ss' % round(viewtime, 2))

    def echo(self, string, newline=True):
        self.response.out.write(string)
        if newline:
            self.response.out.write('\n')

    def echo_json(self, dictionary):
        self.response.out.write(simplejson.dumps(dictionary))

    def header(self, key, value):
        self.response.headers[key] = value


class UserPreferences(db.Model):
    language = db.StringProperty(default=SYSTEM_LANGUAGE)
    timezone = db.StringProperty(default=SYSTEM_TIMEZONE)

    @property
    def current(self):
        user = users.get_current_user()
        if user:
            email = user.email()
        else:
            email = 'guest'

        u = UserPreferences().get_by_key_name(email)
        if not u:
            u = UserPreferences(key_name=email)
            u.put()
        return u

    def set(self, field, value):
        user = users.get_current_user()
        if user:
            u = UserPreferences().get_by_key_name(user.email())
            if u:
                setattr(u, field, value)
                u.put()


class ChangeLog(db.Expando):
    kind_name       = db.StringProperty()
    property_name   = db.StringProperty()
    user            = db.StringProperty()
    datetime        = db.DateTimeProperty(auto_now_add=True)
    model_version   = db.StringProperty(default='B')


class ChangeLogModel(db.Model):
    def put(self, email=None):
        if not email:
            user = users.get_current_user()
            if user:
                email = user.email()
        if self.is_saved():
            old = db.get(self.key())
            for prop_key, prop_value in self.properties().iteritems():
                if old:
                    old_value = prop_value.get_value_for_datastore(old)
                    if old_value == []:
                        old_value = None
                else:
                    old_value = None
                new_value = prop_value.get_value_for_datastore(self)
                if new_value == []:
                    new_value = None
                if old_value != new_value:
                    cl = ChangeLog(parent=self)
                    cl.kind_name = self.kind()
                    cl.property_name = prop_key
                    cl.user = email
                    if old_value:
                        cl.old_value = old_value
                    if new_value:
                        cl.new_value = new_value
                    cl.put()
        return db.Model.put(self)

    @property
    def last_change(self):
        return db.Query(ChangeLog).ancestor(self).order('-datetime').get()


    def history(self, property=None, datetime=None):
        cl = db.Query(ChangeLog).ancestor(self)
        """if property:
            cl.filter('property_name', property)
        if datetime:
            cl.filter('datetime <=', datetime)
        cl.order('datetime')
        cl.fetch(10000)

        h = []
        for c in cl:
            h.append({
                'datetime' = c.datetime,
                'value' = c.new_value,
            })"""



def Translate(key = None):
    if users.get_current_user():
        languagefile = 'translations.' + UserPreferences().current.language
    else:
        languagefile = 'translations.' + SYSTEM_LANGUAGE

    l = __import__(languagefile, globals(), locals(), ['translation'], -1)

    if key:
        if key in l.translation():
            return l.translation()[key].decode('utf8')
        else:
            return key
    else:
        return l.translation()


class Cache:
    def set(self, key, value=None, user_specific=True, time=3600):
        if user_specific == True:
            user = users.get_current_user()
            if user:
                key = key + '_' + user.user_id()
            else:
                return False
        if value:
            memcache.delete(key)
            memcache.add(
                key = key,
                value = value,
                time = time
            )
        else:
            memcache.delete(key)
        return value

    def get(self, key, user_specific=True):
        if user_specific == True:
            user = users.get_current_user()
            if user:
                key = key + '_' + user.user_id()
        return memcache.get(key)


def SendMail(to, subject, message, reply_to=None, html=True, attachments=None):
    valid_to = []
    if isinstance(to, ListType):
        for t in to:
            if email_re.match(t):
                valid_to.append(t)
    else:
        if email_re.match(to):
            valid_to.append(to)
    if len(valid_to) > 0:
        m = mail.EmailMessage()
        m.sender = SYSTEM_EMAIL
        if reply_to:
            if email_re.match(reply_to):
                m.reply_to = reply_to
        m.bcc = SYSTEM_EMAIL
        m.to = valid_to
        m.subject = SYSTEM_EMAIL_PREFIX + subject
        if html == True:
            m.html = message
        else:
            m.body = message
        if attachments:
            m.attachments = attachments
        m.send()

        return True


def StrToList(string):
    if string:
        return [x.strip() for x in string.strip().replace('\n', ' ').replace(',', ' ').replace(';', ' ').split(' ') if len(x.strip()) > 0]
    else:
        return []

def StrToKeyList(string):
    if string:
        strlist = StrToList(string)
        keylist = []
        for key in strlist:
            keylist.append(db.Key(key))
        return keylist
    else:
        return []


def rReplace(s, old, new, occurrence):
    li = s.rsplit(old, occurrence)
    return new.join(li)


def UtcToLocalDateTime(utc_time):
    utc = pytz.timezone('UTC')
    tz = pytz.timezone(UserPreferences().current.timezone)
    d_tz = utc.normalize(utc.localize(utc_time))
    d_utc = d_tz.astimezone(tz)
    return d_utc


def UtcFromLocalDateTime(local_time):
    utc = pytz.timezone('UTC')
    tz = pytz.timezone(UserPreferences().current.timezone)
    d_tz = tz.normalize(tz.localize(local_time))
    d_utc = d_tz.astimezone(utc)
    return d_utc


def AddToList(s_value=None, s_list=[], unique=True):
    if s_value:
        s_list.append(s_value)
    if unique==True:
        return GetUniqueList(s_list)
    else:
        return s_list


def GetUniqueList(s_list):
    return list(set(s_list))


def StripTags(string):
    return striptags(string)


def RandomColor(r1=0, r2=255, g1=0, g2=255, b1=0, b2=255):
    return (('0'+(hex(random.randint(r1, r2))[2:]))[-2:] + ('0'+(hex(random.randint(g1, g2))[2:]))[-2:] + ('0'+(hex(random.randint(b1, b2))[2:]))[-2:]).upper()


def ImageRescale(img_data, width, height, halign='middle', valign='middle'):
    image = images.Image(img_data)

    desired_wh_ratio = float(width) / float(height)
    wh_ratio = float(image.width) / float(image.height)

    if desired_wh_ratio > wh_ratio:
        image.resize(width=width)
        image.execute_transforms()
        trim_y = (float(image.height - height) / 2) / image.height
        if valign == 'top':
            image.crop(0.0, 0.0, 1.0, 1 - (2 * trim_y))
        elif valign == 'bottom':
            image.crop(0.0, (2 * trim_y), 1.0, 1.0)
        else:
            image.crop(0.0, trim_y, 1.0, 1 - trim_y)
    else:
        image.resize(height=height)
        image.execute_transforms()
        trim_x = (float(image.width - width) / 2) / image.width
        if halign == 'left':
            image.crop(0.0, 0.0, 1 - (2 * trim_x), 1.0)
        elif halign == 'right':
            image.crop((2 * trim_x), 0.0, 1.0, 1.0)
        else:
            image.crop(trim_x, 0.0, 1 - trim_x, 1.0)

    return image.execute_transforms()