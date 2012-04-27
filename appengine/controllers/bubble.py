from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers

from operator import attrgetter

import string
import csv
import cStringIO
import urllib
from datetime import *

from bo import *
from database.bubble import *
from database.dictionary import *


class ShowBubbleList(boRequestHandler):
    def get(self, url):
        bt = db.Query(Bubble).filter('path', '%s' % url).get()
        if not bt:
            self.error(404)
            return

        self.view(
            main_template='main/index.html',
            template_file = 'main/list.html',
            page_title = GetDictionaryValue(bt.name_plural),
            values = {
                'list_url': '/bubble/%s' % url,
                'content_url': '/bubble/show',
            }
        )

    def post(self, url):
        key = self.request.get('key').strip()
        if key:
            bubble = Bubble().get(key)
            # bubble.AutoFix()

            if bubble.type not in ['cv_edu', 'cv_work', 'state_exam', 'applicant_doc', 'message', 'submission']:
                if not bubble.Authorize('viewer'):
                    self.error(404)
                    return

            self.echo_json({
                'id': bubble.key().id(),
                'key': str(bubble.key()),
                'image': bubble.GetPhotoUrl(32, True),
                'title': StripTags(bubble.displayname),
                'info': StripTags(bubble.displayinfo),
                'count': bubble.displaycount,
                'type': bubble.type,
                'type_name': bubble.GetType().displayname,
            })
            return

        keys = []
        bt = db.Query(Bubble).filter('path', url).get()

        filtertype = self.request.get('type').strip().lower()
        value = self.request.get('value').strip()
        sortfield = 'x_sort_%s' % UserPreferences().current.language
        sortreverse = getattr(bt, 'sort_descending', False)

        if filtertype == 'search':
            if value:
                keys = []
                for s in StrToList(value.lower()):
                    keylist = [str(k) for k in list(db.Query(Bubble, keys_only=True).filter('x_br_viewer', CurrentUser().key()).filter('x_type', bt.key()).filter('x_is_deleted', False).filter('x_search', '%s:%s' % (UserPreferences().current.language, s)).order('%s%s' % ('-' if sortreverse else '', sortfield)))]
                    if len(keys) == 0:
                        keys = keylist
                    else:
                        keys = ListMatch(keys, keylist)
            else:
                keys = [str(k) for k in list(db.Query(Bubble, keys_only=True).filter('x_br_viewer', CurrentUser().key()).filter('x_type', bt.key()).filter('x_is_deleted', False).order('%s%s' % ('-' if sortreverse else '', sortfield)))]

        if filtertype == 'leecher':
            bubble = Bubble().get(value)
            bubbles = [b for b in Bubble().get(bubble.GetValueAsList('x_br_leecher')) if b]
            keys = [str(b.key()) for b in sorted(bubbles, key=attrgetter(sortfield), reverse=sortreverse)]

        if filtertype == 'leecher_in':
            keys = [str(k) for k in list(db.Query(Bubble, keys_only=True).filter('x_br_leecher', db.Key(value)).filter('x_is_deleted', False).order('%s%s' % ('-' if sortreverse else '', sortfield)))]

        if filtertype == 'subbubbles':
            bubble = Bubble().get(value)
            keys = [str(b.key()) for b in sorted(bubble.GetRelatives('subbubble', bt.path), key=attrgetter(sortfield), reverse=sortreverse)]

        self.echo_json({'keys': keys})


class ShowBubble(boRequestHandler):
    def get(self, bubble_id):
        bubble = Bubble().get_by_id(int(bubble_id))
        bubble.AutoFix()

        if not bubble.Authorize('viewer'):
            self.view(
                main_template = '',
                template_file = 'bubble/locked.html',
            )
            return

        bubble.photourl = bubble.GetPhotoUrl(200, False)
        if bubble.type == 'exam':
            bubble.icalurl = 'webcal://%s/ical/%s' % (self.request.headers.get('host'), str(bubble.key()))
        self.view(
            main_template = 'main/index.html',
            template_file = 'bubble/info.html',
            page_title = StripTags(bubble.displayname),
            values = {
                'bubble': bubble,
                'bubbletype': bubble.GetType(),
                'bubbletypes': bubble.GetSubtypes(),
                # 'bubbletypes': db.Query(Bubble).filter('type', 'bubble_type').fetch(100)
            }
        )


class ShowBubbleXML(boRequestHandler):
    def get(self, bubble_id):
        bubble = Bubble().get_by_id(int(bubble_id))
        if not bubble.Authorize('viewer'):
            self.error(404)
            return

        self.header('Content-Type', 'text/xml')
        self.echo(bubble.to_xml())


class EditBubble(boRequestHandler):
    def get(self, bubble_id):
        bubble = Bubble().get_by_id(int(bubble_id))
        if not bubble.Authorize('viewer'):
            self.error(404)
            return

        self.view(
            main_template = '',
            template_file = 'bubble/edit.html',
            values = {
                'bubble': bubble,
                'blobstore_upload_url': blobstore.create_upload_url('/bubble/upload_file/%s' % bubble_id),
            }
        )

    def post(self, bubble_id):
        bubble = Bubble().get_by_id(int(bubble_id))
        if not bubble.Authorize('viewer'):
            self.error(404)
            return

        value = bubble.SetProperty(
            propertykey = self.request.get('property').strip(),
            oldvalue = self.request.get('oldvalue').strip(),
            newvalue = self.request.get('newvalue').strip(),
        )

        # Send messages
        if self.request.get('oldvalue').strip() != self.request.get('newvalue').strip():
            bt = bubble.GetType()
            alter = bt.GetValueAsList('notify_on_alter')
            if len(alter) > 0:
                message = ''
                for t in bubble.GetProperties():
                    message += '<b>%s</b>:<br/>\n' % t['name']
                    message += '%s<br/>\n' % '<br/>\n'.join(['%s' % n['value'].replace('\n', '<br/>\n') for n in t['values'] if n['value']])
                    message += '<br/>\n'
                for a in alter:
                    for r in bubble.GetRelatives(a):
                        emails = ListMerge(getattr(r, 'email', []), getattr(r, 'user', []))
                        SendMail(
                            to = emails,
                            subject = Translate('message_notify_on_alter_subject') % bt.displayname.lower(),
                            message = message,
                        )

        self.echo(value, False)


class AddBubble(boRequestHandler):
    def get(self, bubbletype, bubble_id):
        bubble = Bubble().get_by_id(int(bubble_id))
        if not bubble.Authorize('viewer'):
            self.error(404)
            return

        newbubble = bubble.AddSubbubble(bubbletype)
        self.redirect('/bubble/edit/%s' % newbubble.key().id())


class DownloadBubbleFile(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, data_property, file_key=None):
        b = blobstore.BlobInfo.get(urllib.unquote(file_key))
        if not b:
            self.error(404)
            return

        bubble = db.Query(Bubble).filter(data_property, b.key()).get()
        if not bubble:
            self.error(404)
            return

        if not bubble.Authorize('viewer'):
            self.error(404)
            return

        self.send_blob(b, save_as = ReplaceUTF(b.filename))


class UploadBubbleFile(blobstore_handlers.BlobstoreUploadHandler):
    def post(self, bubble_id):
        bubble = Bubble().get_by_id(int(bubble_id))
        if not bubble.Authorize('viewer'):
            self.error(404)
            return

        upload_files = self.get_uploads('file')
        if not upload_files:
            return

        blob_info = upload_files[0]

        value = bubble.SetProperty(
            propertykey = self.request.get('property').strip(),
            newvalue = blob_info.key(),
        )

        self.response.out.write(blob_info.filename)


class SelectFieldValues(boRequestHandler):
    def post(self):
        language = UserPreferences().current.language
        p = CurrentUser()

        if not self.request.get('property').strip():
            return

        bp = Bubble().get(self.request.get('property').strip())

        cache_key = 'select_field_' + '_' + str(p.key())
        result = Cache().get(cache_key, True)
        if result:
            self.echo_json(result)
            return

        values = []
        if bp.GetValue('data_type') == 'select':
            for c in sorted(bp.GetValueAsList('choices')):
                values.append({
                    'key': c,
                    'value': c
                })
        if bp.GetValue('data_type') == 'dictionary_select':
            for c in bp.GetValueAsList('choices'):
                for d in sorted(db.Query(Dictionary).filter('name', c).fetch(100), key=attrgetter(language)):
                    values.append({
                        'key': str(d.key()),
                        'value': getattr(d, language)
                    })
        if bp.GetValue('data_type') == 'reference':
            for t in bp.GetValueAsList('choices'):
                for d in db.Query(Bubble).filter('x_is_deleted', False).filter('type', t).order('x_sort_%s' % language).fetch(1000):
                    values.append({
                        'key': str(d.key()),
                        'value': d.displayname
                    })
        if bp.GetValue('data_type') == 'counter':
            for d in sorted(db.Query(Counter).fetch(1000), key=attrgetter('displayname')):
                values.append({
                    'key': str(d.key()),
                    'value': d.displayname
                })

        result = {
            'property': str(bp.key()),
            'values': values
        }
        Cache().set(cache_key, result, True, 600)

        self.echo_json(result)


class BubbleRights(boRequestHandler):
    def get(self, bubble_id):
        bubble = Bubble().get_by_id(int(bubble_id))
        if not bubble.Authorize('viewer'):
            self.error(404)
            return

        user_key = CurrentUser().key()
        rights = ['viewer', 'subbubbler', 'editor', 'owner']
        persons = []
        for r in rights:
            bubbles = bubble.GetRelatives(r)
            if bubbles:
                for b in bubbles:
                    b.relation_type = r
                    if b.key() == user_key:
                        b.relation_currentuser = True
                persons = ListMerge(persons, bubbles)

        self.view(
            main_template = '',
            template_file = 'bubble/rights.html',
            values = {
                'bubble': bubble,
                'persons': persons,
            }
        )

    def post(self, bubble_id):
        bubble = Bubble().get_by_id(int(bubble_id))
        if not bubble.Authorize('viewer'):
            return

        person = Bubble().get(self.request.get('person').strip())

        AddTask('/taskqueue/rights', {
            'bubble': str(bubble.key()),
            'person': str(person.key()),
            'right': self.request.get('right').strip(),
            'user': CurrentUser()._googleuser
        }, 'rights')

        self.echo_json({
            'key': str(person.key()),
            'name': person.displayname,
            'right': self.request.get('right').strip(),
        })


class BubbleAutocomplete(boRequestHandler):
    def get(self):
        query = self.request.get('query').strip()
        if not self.request.get('query').strip():
            return

        suggestions = []
        data = []

        bt = db.Query(Bubble).filter('path', 'person').get()
        sortfield = 'x_sort_%s' % UserPreferences().current.language
        for b in db.Query(Bubble).filter('x_type', bt.key()).filter('x_is_deleted', False).filter('x_search', '%s:%s' % (UserPreferences().current.language, query)).order(sortfield).fetch(20):
            suggestions.append(b.displayname)
            data.append(str(b.key()))

        self.echo_json({
            'query': query,
            'suggestions': suggestions,
            'data': data
        })



def main():
    Route([
            (r'/bubble/show/(.*)', ShowBubble),
            (r'/bubble/edit/(.*)', EditBubble),
            (r'/bubble/add/(.*)/(.*)', AddBubble),
            (r'/bubble/file/(.*)/(.*)', DownloadBubbleFile),
            (r'/bubble/upload_file/(.*)', UploadBubbleFile),
            ('/bubble/sfv', SelectFieldValues),
            (r'/bubble/rights/(.*)', BubbleRights),
            (r'/bubble/autocomplete', BubbleAutocomplete),
            (r'/bubble/xml/(.*)', ShowBubbleXML),
            (r'/bubble/(.*)', ShowBubbleList),
        ])


if __name__ == '__main__':
    main()
