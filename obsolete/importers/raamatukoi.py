from google.appengine.api import urlfetch
from BeautifulSoup import BeautifulSoup


def RaamatukoiList(string):
    url = 'http://www.raamatukoi.ee/cgi-bin/index?valik=otsing&paring=' + string


def RaamatukoiImageByISBN(isbn):
    url = 'http://www.raamatukoi.ee/cgi-bin/index?valik=otsing&paring=' + isbn
    headers = urlfetch.fetch(url, follow_redirects=False, deadline=10).headers

    if 'location' in headers:
        url2 = 'http://www.raamatukoi.ee/cgi-bin/' + headers['location']
        content = urlfetch.fetch(url2, deadline=10).content
        soup = BeautifulSoup(content)

        img = soup.find('img', attrs={'height' : '150'})
        if img:
            return img['src']