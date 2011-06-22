from icalendar import Calendar, Event, vCalAddress, vText, UTC
from datetime import datetime, date
from datetime import *

from bo import *
from database.bubble import *

# http://tools.ietf.org/html/rfc5545
# http://icalvalid.cloudapp.net/Default.aspx
# http://codespeak.net/icalendar/


class BubbleTypeCalendar(boRequestHandler):
    def get(self, key):
        type = db.Query(BubbleType).filter('type', key).get()
        if type:
            cal = Calendar()
            cal.add('prodid', '-//%s//artun.ee//EN' % type.displayname)
            cal.add('version', '2.0')
            cal.add('x-wr-calname', type.displayname)
            if type.description:
                cal.add('x-wr-caldesc', type.description.translate())
            cal.add('method', 'PUBLISH')

            for b in db.Query(Bubble).filter('type', type.type).order('start_datetime').fetch(1000000):
                if b.start_datetime and b.end_datetime:
                    event = Event()
                    event.add('summary', b.displayname)
                    if b.description:
                        event.add('description', b.description.translate())
                    if b.start_datetime.strftime('%H:%M') == '00:00':
                        event.add('dtstart', b.start_datetime.date())
                    else:
                        event.add('dtstart', b.start_datetime)
                    if b.end_datetime.strftime('%H:%M') == '00:00':
                        event.add('dtend', b.end_datetime.date())
                    else:
                        event.add('dtend', b.end_datetime)
                    if b.last_change.datetime:
                        event.add('dtstamp', b.last_change.datetime)
                    event['uid'] = '%s@artun.ee' % b.key()

                    """if b.leechers:
                        for p in db.get(b.leechers):
                            attendee = vCalAddress('MAILTO:%s' % p.primary_email)
                            attendee.params['cn'] = vText('%s' % p.displayname)
                            attendee.params['ROLE'] = vText('CHAIR')
                            event.add('attendee', attendee, encode=0)"""

                    event.add('priority', 5)
                    cal.add_component(event)

            self.header('Content-Type', 'text/plain; charset=utf-8')
            self.echo(cal.as_string(), False)


class Test(boRequestHandler):
    def get(self):

        cal = Calendar()
        cal.add('prodid', '-//qsalidfuoisudfo//mxm.dk//')
        cal.add('version', '2.0')
        cal.add('x-wr-calname', 'Testkalender')
        cal.add('x-wr-caldesc', 'Mingi asi.')
        cal.add('method', 'PUBLISH')

        event = Event()
        event.add('summary', 'Python meeting about calendaring')
        event.add('description', 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.')
        event.add('dtstart', datetime(2011,4,4,8,0,0,tzinfo=UTC))
        event.add('dtend', datetime(2011,4,4,10,0,0,tzinfo=UTC))
        event.add('dtstamp', datetime(2011,4,4,0,10,0,tzinfo=UTC))
        event['uid'] = '20050115T101010/27346262376@mxm.dk'
        event.add('priority', 5)

        #event.add('attendee', 'mailto:argo@roots.ee')

        attendee = vCalAddress('MAILTO:argo.roots@artun.ee')
        attendee.params['cn'] = vText('Argo Roots')
        attendee.params['ROLE'] = vText('CHAIR')
        event.add('attendee', attendee, encode=0)

        attendee = vCalAddress('MAILTO:mihkel.putrinsh@artun.ee')
        attendee.params['cn'] = vText('Mihkel Putrinsh')
        attendee.params['ROLE'] = vText('REQ-PARTICIPANT')
        event.add('attendee', attendee, encode=0)

        attendee = vCalAddress('MAILTO:maxm3@example.com')
        attendee.params['cn'] = vText('Max Rasmussen 3')
        attendee.params['ROLE'] = vText('OPT-PARTICIPANT')
        #event.add('attendee', attendee, encode=0)

        attendee = vCalAddress('MAILTO:maxm4@example.com')
        attendee.params['cn'] = vText('Non')
        attendee.params['ROLE'] = vText('NON-PARTICIPANT')
        #event.add('attendee', attendee, encode=0)

        cal.add_component(event)

        event = Event()
        event.add('summary', 'Python meeting about calendaring 2')
        event.add('dtstart', date(2011,4,6))
        event.add('dtend', date(2011,4,6))
        event.add('dtstamp', datetime(2011,4,4,0,10,0,tzinfo=UTC))
        event['uid'] = '20110115T101010/27346262376@mxm.dk'
        event.add('priority', 5)

        attendee = vCalAddress('MAILTO:mihkel.putrinsh@artun.ee')
        attendee.params['cn'] = vText('Mihkel Putrinsh')
        attendee.params['ROLE'] = vText('REQ-PARTICIPANT')
        event.add('attendee', attendee, encode=0)

        cal.add_component(event)

        self.echo(str(cal), False)


def main():
    Route([
            ('/ical/test', Test),
            ('/ical/(.*)', BubbleTypeCalendar),
        ])


if __name__ == '__main__':
    main()