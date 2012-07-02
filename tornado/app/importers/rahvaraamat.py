from google.appengine.api import urlfetch
from BeautifulSoup import BeautifulSoup


def RahvaraamatImageByISBN(isbn):
    url = 'http://pood.rahvaraamat.ee/_otsing?page=1&Isbn=' + isbn
    content = urlfetch.fetch(url, deadline=10).content
    soup = BeautifulSoup(content)

    div = soup.find('div', attrs={'class' : 'list_product_thumb'})
    if div:
        img = div.find('img')
        if img:
            imgsrc = img['src'].replace('/product_2/', '/product_5/')
        if imgsrc != '/Content/Img/thumbs/blank_2.gif':
            return imgsrc