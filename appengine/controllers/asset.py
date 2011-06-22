from bo import *
from database.asset import *

class Show(boRequestHandler):
    def get(self):
        if self.authorize():

            self.view('', 'assetspy_download.html')
    def post(self):
        a = Asset()
        a.location = self.request.get('location')
        a.user = self.request.get('user')
        a.room = self.request.get('room')
        a.asset_id = self.request.get('asset_id')
        a.put()

        asset_id = a.key().id()

        self.response.headers['Content-type'] = 'application/octet-stream;'
        self.response.headers['Content-disposition'] = 'attachment;filename=sysinfo128.bat'

        self.response.out.write('@echo off\r\n')
        self.response.out.write('echo a%s.xml > sysinfo128.txt\r\n' % asset_id)
        self.response.out.write('echo open roots.ee > sysinfo128.ftp\r\n')
        self.response.out.write('echo user eka_ftp.roots.ee Ekagram91 >> sysinfo128.ftp\r\n')
        self.response.out.write('echo binary >> sysinfo128.ftp\r\n')
        self.response.out.write('echo get sysinfo128_ftp.bat >> sysinfo128.ftp\r\n')
        self.response.out.write('echo bye >> sysinfo128.ftp\r\n')
        self.response.out.write('ftp -n -s:sysinfo128.ftp > sysinfo128.out\r\n')
        self.response.out.write('del sysinfo128.ftp\r\n')
        self.response.out.write('del sysinfo128.out\r\n')
        self.response.out.write('sysinfo128_ftp.bat\r\n')
        self.response.out.write('del sysinfo128_ftp.bat\r\n')


def main():
    Route([
            ('/assets', Show)
        ])


if __name__ == '__main__':
    main()