# -*- coding: utf-8 -*-
# Methods to get book information from apollo.ee
# Dev/maintainer: Ando Roots 2010

import re
from google.appengine.api import urlfetch
from BeautifulSoup import BeautifulSoup
from BeautifulSoup import BeautifulStoneSoup


# Lookup book data from Apollo.ee DB by book ID
# Input: Book ID
# Output: Dict with Apollo's info
def GetBookByID(book_id):
    apollo_url = 'http://apollo.ee/product.php/' + book_id
    soup = BeautifulSoup(urlfetch.fetch(apollo_url).content)
    if ReSearch(soup, r'Toodet (.*?) eksisteeri'):
    	return None # If 404

    data_object = soup.find('div', attrs={'class' : 'wrapRaamat'})
    article_object = soup.find('div', attrs={'class' : 'wrapArtikkel'})

    # If there are any authors, put them in a list. If not, leave it be.
    authors = None
    if data_object.findAll('a', attrs={'title': 'Veel sellelt autorilt'}):
        authors = data_object.findAll('a', attrs={'title': 'Veel sellelt autorilt'})

    # If there are any editors, put them in a list. If not, leave it be.
    editors = ReSearch(data_object, r'Toimetanud (.*?)<br />')
    if editors:
    	editors = editors.split(',')

    # This is the main data dict
    data = {
        'id': book_id,
        'isbn10': ReSearch(data_object, r'ISBN-10 (.*?)(;|<br />)'),
        'isbn13': ReSearch(data_object, r'ISBN-13 (.*?)(;|<br />)'),
        'title': data_object.h2,
        'subtitle': soup.find('h3', attrs={'style' : 'font-weight:normal;'}),
        'series': soup.find('a', attrs={'title' : 'Veel samast sarjast'}),
        'description': data_object.p,
        'authors': authors,
        'publisher': ReSearch(data_object, r'Kirjastus (.*?)<br />'),
        'published': ReSearch(data_object, r'Ilmumisaasta (.*?)(;|<br />)'),
        'translator': ReSearch(data_object, r'Tõlkinud (.*?)<br />'),
        'editors': editors,
        'illustrator': ReSearch(data_object, r'Illustreerinud (.*?)<br />').split(','),
        'price': soup.find('span', attrs={'class' : 'tooteHind'}),
        'format': ReSearch(data_object, r'Formaat (.*?)(;|<br />)'),
        'dimensions': ReSearch(data_object, r'Mõõtmed (.*?)<br />'),
        'pages': ReSearch(data_object, r'Lehekülgi (.*?);'),
        'image': 'http://apollo.ee' + article_object('img')[0]['src'],
        'url': apollo_url,
    }

    # Trouble with encoding, convert every member of data dict
    nice_data = {}
    for i in data:
        nice_data[i] = ConvertSoup(StripHTML(data[i]))

    # ----------------------------------------------------------------------------------------------------------- #
    # N.B! When changing the structure of the output dict, you MUST UPDATE the stored values in apollo_cron.py !
    # ----------------------------------------------------------------------------------------------------------- #
    return nice_data



# Search Apollo for a book. N.B! Only returns first 15 results!
# Input: String search_term
# Output: a list with nested dict-s, one for each result
def SearchBook(search_term):

    # Post the search and get the HTML of the result page.
    apollo_url = 'http://apollo.ee/search.php?keyword='+search_term
    soup = BeautifulSoup(urlfetch.fetch(apollo_url, deadline=10).content)
    if ReSearch(soup, r'Tooteid (.*?) leitud'):
    	return None # If 404
    result_block = soup.find('div', attrs={'class' : 'otsingTulemusRaamat'})

    # Since the results are poorly structured we have to split it into individual parts.
    data_objects = str(result_block).split('<div class="sisuSplitter">&nbsp;</div>')
    data = []
    for data_object in data_objects:
    	current_soup = BeautifulSoup(data_object)

    	# Primary data gathering
    	current_info = {
            'id': ReSearch(current_soup, r'php/(.*?)"'),
            'title': current_soup.find('a'),
    		'description': current_soup.find('p'),
    		'authors': current_soup.findAll('a', attrs={'title': 'Veel sellelt autorilt'}),
        }

    	# Get around UTF-8 problems
    	nice_current_info = {}
    	for i in current_info:
    		nice_current_info[i] = ConvertSoup(StripHTML(current_info[i]))
    	data.append(nice_current_info)
    	nice_current_info = None
    	current_soup = None

    return data

# ------------------------------ Helper functions --------------------------------- #


# Authors need special parsing - one book can have multiple authors.
def ParseAuthors(soup):
    authors = []
    #for n in soup.findAll('a', attrs={'title': 'Veel sellelt autorilt'}):
    #    authors.append(''.join(n.renderContents()))
    authors = ConvertSoup(StripHTML(soup.findAll('a', attrs={'title': 'Veel sellelt autorilt'})))
    authors = unicode(authors.split(','))
    #for index, author in enumerate(authors):
    #	authors[index] = author.strip()
    if not authors:
    	return None
    else:
    	return authors



# Strip out any HTML tags found in input string
def StripHTML(data):
    data = str(data)
    p = re.compile(r'<.*?>')
    return p.sub('', data)


# Regex search - find needle in haystack and return it
def ReSearch(haystack, needle):
	p = re.compile(needle).search(str(haystack))
	if p:
		return p.group(1)
	else:
		return None


# Converts non-English symbols for output
def ConvertSoup(input):
    result = BeautifulStoneSoup(input, convertEntities=BeautifulStoneSoup.ALL_ENTITIES)
    return result.renderContents()

# -- End of file -- #