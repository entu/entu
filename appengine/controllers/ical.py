from icalendar import Calendar, Event, vCalAddress, vText
from datetime import datetime, date
from datetime import *

from bo import *
from database.bubble import *

# http://tools.ietf.org/html/rfc5545
# http://icalvalid.cloudapp.net/Default.aspx
# http://codespeak.net/icalendar/
# https://github.com/collective/icalendar


class BubbleSubbubbles(boRequestHandler):
    def get(self, bubble_key):
        bubble = Bubble().get(bubble_key)

        cal = Calendar()
        cal.add('prodid', '-//%s//artun.ee//EN' % bubble.displayname)
        cal.add('version', '2.0')
        cal.add('x-wr-calname', bubble.displayname)
        cal.add('x-wr-caldesc', bubble.displayinfo)
        cal.add('method', 'PUBLISH')

        for subbubble in sorted(bubble.GetRelatives('subbubble'), key=attrgetter('start_datetime')):
            if getattr(subbubble, 'start_datetime', False) and getattr(subbubble, 'end_datetime', False):
                emptytime = True
                for leecher in subbubble.GetRelatives('leecher'):
                    emptytime = False
                    event = Event()
                    event.add('summary', leecher.displayname)
                    # event.add('description', subbubble.displayinfo)
                    if subbubble.start_datetime.strftime('%H:%M') == '00:00':
                        event.add('dtstart', subbubble.start_datetime.date())
                    else:
                        event.add('dtstart', subbubble.start_datetime)
                    if subbubble.end_datetime.strftime('%H:%M') == '00:00':
                        event.add('dtend', subbubble.end_datetime.date())
                    else:
                        event.add('dtend', subbubble.end_datetime)
                    event.add('dtstamp', subbubble.x_changed)
                    event['uid'] = '%s@artun.ee' % subbubble.key()

                if emptytime:
                    event = Event()
                    event.add('summary', '')
                    # event.add('description', subbubble.displayinfo)
                    if subbubble.start_datetime.strftime('%H:%M') == '00:00':
                        event.add('dtstart', subbubble.start_datetime.date())
                    else:
                        event.add('dtstart', subbubble.start_datetime)
                    if subbubble.end_datetime.strftime('%H:%M') == '00:00':
                        event.add('dtend', subbubble.end_datetime.date())
                    else:
                        event.add('dtend', subbubble.end_datetime)
                    event.add('dtstamp', subbubble.x_changed)
                    event['uid'] = '%s@artun.ee' % subbubble.key()



                # for leecher in subbubble.GetRelatives('leecher'):
                #     attendee = vCalAddress(leecher.displayname.encode('utf-8'))
                #     # attendee.params['cn'] = vText('%s' % leecher.displayname)
                #     # attendee.params['ROLE'] = vText('CHAIR')
                #     event.add('attendee', attendee, encode=0)

                event.add('priority', 5)
                cal.add_component(event)

        self.header('Content-Type', 'text/plain; charset=utf-8')
        self.echo(cal.to_ical(), False)


class Test(boRequestHandler):
    def get(self):


        cal = Calendar()
        from datetime import datetime
        from icalendar.tools import utctz # timezone
        cal.add('prodid', '-//My calendar product//mxm.dk//')
        cal.add('version', '2.0')

        event = Event()
        event.add('summary', 'Python meeting about calendaring')
        event.add('dtstart', datetime(2005,4,4,8,0,0,tzinfo=utctz()))
        event.add('dtend', datetime(2005,4,4,10,0,0,tzinfo=utctz()))
        event.add('dtstamp', datetime(2005,4,4,0,10,0,tzinfo=utctz()))
        event['uid'] = '20050115T101010/27346262376@mxm.dk'
        event.add('priority', 5)

        cal.add_component(event)

        self.echo(cal.to_ical())
        return




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
            ('/ical/(.*)', BubbleSubbubbles),
        ])


if __name__ == '__main__':
    main()
