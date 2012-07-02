from tornado import auth, web
from tornado import httpclient

import logging

from helper import *
from db import *


class GAEsql(myRequestHandler):
    def post(self):
        self.require_setting('app_title', 'GAE import')

        secret = self.settings['gae_secret']
        sql = self.get_argument('sql', None)

        if self.get_argument('secret', None) != secret or not sql:
            return self.forbidden()

        sql = sql.replace('%', '%%')

        try:
            db.connection().execute(sql)
        except Exception, e:
            logging.error('%s' % e)
            logging.error('%s' % self.get_argument('sql', ''))
            logging.error('%s' % self.get_argument('description', ''))
        self.write('OK')


class GAEFiles(myRequestHandler):
    @web.asynchronous
    def get(self):
        self.add_header('Content-Type', 'text/plain; charset=utf-8')
        for f in db.connection().query('SELECT gae_key FROM file WHERE file IS NULL AND gae_key NOT LIKE \'amphora_%%\' ORDER BY gae_key;'):
            url = 'https://dev-m.bubbledu.appspot.com/export/file/%s' % f.gae_key
            httpclient.AsyncHTTPClient().fetch(url, callback=self._got_file)
        self.write('Done!')
        self.flush()

    def _got_file(self, response):
        if not response.body:
            return

        gae_key = response.request.url.replace('https://dev-m.bubbledu.appspot.com/export/file/', '').strip()
        db.connection().execute('UPDATE file SET filesize = %s, file = %s WHERE gae_key = %s;', len(response.body), response.body, gae_key)
        self.write('%s\n' % len(response.body))
        self.flush()


class AmphoraFiles(myRequestHandler):
    @web.asynchronous
    def get(self):
        pass


class ExportApplicants(myRequestHandler):
    @web.authenticated
    def get(self):
        if self.current_user.email != 'argo.roots@artun.ee':
            return

        limit = 1000

        entity = db.Entity(user_locale=self.get_user_locale(), user_id=self.current_user.id)
        applicants = entity.get(entity_definition_id=10, full_definition=True, limit=limit)

        self.add_header('Content-Type', 'text/csv; charset=utf-8')

        self.write('"ID",')
        props = applicants[0].get('properties', {}).values()
        for p in sorted(props, key=itemgetter('ordinal')):
            self.write('"%s",' % p.get('label', ''))
        self.write('\n')

        for applicant in applicants:
            self.write('"%s",' % applicant.get('id',''))
            props = applicant.get('properties', {}).values()
            for p in sorted(props, key=itemgetter('ordinal')):
                if p.get('datatype', '') == 'file':
                    self.write('"%s",' % ' '.join(['http://entu.artun.ee/entity/file-%s' % v['db_value'] for v in p['values'] if v['value']]))
                else:
                    self.write('"%s",' % getValue(p))
            self.write('\n')


class ExportApplicantsSubscriptions(myRequestHandler):
    @web.authenticated
    def get(self):
        if self.current_user.email != 'argo.roots@artun.ee':
            return

        limit = 1000

        entity = db.Entity(user_locale=self.get_user_locale(), user_id=self.current_user.id)
        applicants = entity.get(entity_definition_id=10, full_definition=True, limit=limit)

        self.add_header('Content-Type', 'text/csv; charset=utf-8')

        for applicant in applicants:
            sub = entity.get_relatives(related_entity_id=applicant['id'], relation_type='leecher', entity_definition_id=20, reverse_relation=True, full_definition=True)
            if sub:
                sub = sub.values()[0]
                for s in sub:
                    self.write('"%s",' % applicant.get('id',''))
                    self.write('"%s",' % getValue(applicant.get('properties', {}).get('user', {}) ))
                    self.write('"%s",' % getValue(applicant.get('properties', {}).get('forename', {}) ))
                    self.write('"%s",' % getValue(applicant.get('properties', {}).get('surname', {}) ))
                    self.write('"%s",' % s.get('displayname', ''))
                    self.write('\n')


class ExportApplicantsChilds(myRequestHandler):
    @web.authenticated
    def get(self, entity_definition_id):
        if self.current_user.email != 'argo.roots@artun.ee':
            return

        limit = 1000

        entity = db.Entity(user_locale=self.get_user_locale(), user_id=self.current_user.id)
        applicants = entity.get(entity_definition_id=10, full_definition=True, limit=limit)

        self.add_header('Content-Type', 'text/csv; charset=utf-8')

        self.write('"ID","Email","Eesnimi","Perenimi"')
        self.write('\n')
        for applicant in applicants:
            edu = entity.get_relatives(entity_id=applicant['id'], relation_type='child', entity_definition_id=entity_definition_id, full_definition=True)
            if edu:
                edu = edu.values()[0]
                for e in edu:
                    self.write('"%s",' % applicant.get('id',''))
                    self.write('"%s",' % getValue(applicant.get('properties', {}).get('user', {}) ))
                    self.write('"%s",' % getValue(applicant.get('properties', {}).get('forename', {}) ))
                    self.write('"%s",' % getValue(applicant.get('properties', {}).get('surname', {}) ))

                    props = e.get('properties', {}).values()
                    for p in sorted(props, key=itemgetter('ordinal')):
                        if p.get('datatype', '') == 'file':
                            self.write('"%s",' % ' '.join(['http://entu.artun.ee/entity/file-%s' % v['db_value'] for v in p['values'] if v['value']]))
                        else:
                            self.write('"%s",' % getValue(p))

                    self.write('\n')



def getValue(p):
    logging.debug(p)
    if not p:
        return ''
    return ', '.join(['%s' % v['value'] for v in p['values'] if v['value']]).replace('"', '""')


handlers = [
    ('/import/gae', GAEsql),
    ('/import/gae_files', GAEFiles),
    ('/import/amphora_files', GAEFiles),
    ('/import/export', ExportApplicants),
    ('/import/export/subs', ExportApplicantsSubscriptions),
    (r'/import/export/(.*)', ExportApplicantsChilds),
]
