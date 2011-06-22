from google.appengine.api import datastore_types
from google.appengine.ext import db
from django.utils.html import strip_tags
from datetime import *

from bo import *
from database.bubble import *


class Applications(boRequestHandler):
    def get(self):

        self.echo('<?xml version="1.0" encoding="UTF-8"?>')
        self.echo('<root>')

        d = []
        for b in db.Query(Bubble).filter('type', 'submission').filter('start_datetime <', datetime.now()).fetch(10000):
            if len(b.leechers) > 0 and b.end_datetime > datetime.now():
                d.append({
                    'label': strip_tags(b.name.translate()) + ' (' + str(len(b.leechers)) + ')',
                    'value': len(b.leechers),
                    'color': RandomColor()
                })
        n = 1
        othersum = 0
        for i in sorted(d, key=lambda k: k['value'], reverse=True):
            n += 1
            if n <= 20:
                self.echo('<item>')
                self.echo('<label>%s</label>' % i['label'])
                self.echo('<value>%s</value>' % i['value'])
                self.echo('<colour>%s</colour>' % i['color'])
                self.echo('</item>')
            else:
                othersum += i['value']

        self.echo('<item>')
        self.echo('<label>Other (%s)</label>' % othersum)
        self.echo('<value>%s</value>' % othersum)
        self.echo('<colour>FFFFFF</colour>')
        self.echo('</item>')
        self.echo('</root>')


class Applications2(boRequestHandler):
    def get(self):

        self.echo('<?xml version="1.0" encoding="UTF-8"?>')
        self.echo('<root>')

        dic = {}
        for b in db.Query(Bubble).filter('type', 'submission').filter('start_datetime <', datetime.now()).fetch(10000):
            if b.end_datetime > datetime.now():
                for cl in db.Query(ChangeLog).ancestor(b).filter('property_name', 'leechers').order('datetime').fetch(10000):
                #for cl in db.Query(ChangeLog).ancestor(b).filter('property_name', 'leechers').fetch(10000):
                    date = cl.datetime.strftime('%Y%m%d')
                    key = str(b.key())
                    if date not in dic:
                        dic[date] = {}
                    dic[date][key] = len(eval(cl.new_value))

        for date, key_value in dic.iteritems():
            sum = 0
            for key, value in key_value.iteritems():
                sum += value
            self.echo('<item day="%s">' % date)
            self.echo('<item>%s</item>' % sum)
            self.echo('</item>')

        self.echo('<settings>')
        self.echo('<axisx>%s</axisx>' % 'A')
        self.echo('<axisx>%s</axisx>' % 'B')
        self.echo('<axisy>%s</axisy>' % 0)
        self.echo('<axisy>%s</axisy>' % sum)
        self.echo('<colour>ff9900</colour>')
        self.echo('</settings>')
        self.echo('</root>')


class Feedback(boRequestHandler):
    def get(self):

        a = db.Query(QuestionaryPerson).filter('is_obsolete', False)
        kokku = a.count(limit=200000)

        a = db.Query(QuestionaryPerson).filter('is_obsolete', False).filter('is_completed', True)
        tehtud = a.count(limit=200000)

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


def main():
    Route([
            ('/xml/applications', Applications),
            ('/xml/applications2', Applications2),
            ('/xml/feedback', Feedback),
        ])


if __name__ == '__main__':
    main()