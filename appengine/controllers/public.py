from google.appengine.api import urlfetch
from datetime import *

from bo import *
from database.bubble import *
from database.feedback import *
from database.dictionary import *


class ShowSearech(boRequestHandler):
    def get(self):
        search = self.request.get('q').strip().lower()
        language = self.request.get('language', SystemPreferences().get('default_language')).strip()

        if not search:
            self.view(
                main_template = 'public/index.html',
                template_file = 'public/start.html',
            )
            return

        cache_key = 'public_search_%s' % hashlib.md5(search).hexdigest()
        cached_search = Cache().get(cache_key)

        if not cached_search:
            cached_search = {}
            keys = []
            for s in StrToList(search):
                keylist = [str(k) for k in list(db.Query(Bubble, keys_only=True).filter('is_public', True).filter('x_is_deleted', False).filter('x_search_%s' % language, search))]
                if len(keys) == 0:
                    keys = keylist
                else:
                    keys = ListMatch(keys, keylist)

            cached_search['totalcount'] = len(keys)
            keys = keys[:25]

            bubbles = []
            for bubble in Bubble.get(keys):
                bt = bubble.GetType()

                b_number = bubble.GetProperty(bt, 'registry_number', language)
                b_name = bubble.GetProperty(bt, 'name', language)
                b_created = bubble.GetProperty(bt, 'x_created', language)

                # props = bubble.GetProperties()
                bubbles.append({
                    'key': bubble.public_key,
                    'type': bt.displayname,
                    'number': ', '.join([v['value'] for v in b_number['values'] if v['value']]) if b_number else '',
                    'name': ', '.join([v['value'] for v in b_name['values'] if v['value']]) if b_name else '',
                    'created': ', '.join([v['value'] for v in b_created['values'] if v['value']]) if b_created else '',
                })

            cached_search['bubbles'] = sorted(bubbles, key=lambda k: k['name'].lower())
            cached_search['bubblecount'] = len(bubbles)

            if cached_search['totalcount'] > 0:
                Cache().set(key = cache_key, value=cached_search, time=21600)

        if cached_search['bubblecount'] == 0:
            count = Translate('public_result_count_0')
        elif cached_search['bubblecount'] == 1:
            count = Translate('public_result_count_1')
        elif cached_search['bubblecount'] == cached_search['totalcount']:
            count = Translate('public_result_count_more') % cached_search['bubblecount']
        else:
            count = Translate('public_result_count_much_more') % {'show': cached_search['bubblecount'], 'total': cached_search['totalcount']}

        self.view(
            main_template = 'public/index.html',
            template_file = 'public/list.html',
            values = {
                'bubbles': cached_search['bubbles'],
                'search': search,
                'count': count
            }
        )


class ShowBubble(boRequestHandler):
    def get(self, key):
        language = self.request.get('language', SystemPreferences().get('default_language')).strip()
        bubble = db.Query(Bubble).filter('is_public', True).filter('x_public_key', key).get()

        if not bubble:
            return self.redirect('/public')

        self.view(
            main_template = 'public/index.html',
            template_file = 'public/bubble.html',
            values = {
                'name': ', '.join([v['value'] for v in bubble.GetProperty(bubble.GetType(), 'name', language)['values'] if v['value']]),
                'bubble': bubble,
            }
        )


class Feedback(boRequestHandler):
    def get(self):

        a = db.Query(QuestionaryPerson).filter('is_obsolete', False)
        kokku = a.count(limit=200000)

        a = db.Query(QuestionaryPerson).filter('is_obsolete', False).filter('is_completed', True)
        tehtud = a.count(limit=200000)

        #url = 'http://chart.apis.google.com/chart?chs=500x300&cht=p&chds=0,%(b)s&chd=t:%(a)s,%(b)s&chdl=Tehtud|Teha&chp=4.71238898&chl=%(a)s|%(b)s' % {'a':tehtud, 'b':(kokku-tehtud)}

        url = 'http://chart.apis.google.com/chart?chxl=1:|0|%(b)s&chxr=1,0,%(b)s&chxs=0,676767,15|1,49188F,15,0,l,676767&chxt=x,y&chs=350x200&cht=gm&chds=0,%(b)s&chd=t:%(a)s&chl=%(a)s&chco=49188F,CE0000|FFFF88|008000' % {'a':tehtud, 'b':kokku}

        self.header('Content-Type', 'image/png')
        self.echo(urlfetch.fetch(url, deadline=10).content, False)
        return

        self.echo('<?xml version="1.0" encoding="UTF-8"?>')
        self.echo('<root>')
        self.echo('<item>%s</item>' % tehtud)
        self.echo('<min>')
        self.echo('<value>0</value>')
        self.echo('<text></text>')
        self.echo('</min>')
        self.echo('<max>')
        self.echo('<value>%s</value>' % kokku)
        self.echo('<text></text>')
        self.echo('</max>')
        self.echo('</root>')


class ShowStatus(boRequestHandler):
    def get(self):
        self.header('Content-Type', 'text/plain; charset=utf-8')
        self.echo('OK')


def main():
    Route([
            ('/public', ShowSearech),
            ('/public/(.*)', ShowBubble),
            ('/public/feedback', Feedback),
            ('/public/status', ShowStatus),
        ])


if __name__ == '__main__':
    main()
