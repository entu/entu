# -*- coding: utf-8 -*-
# Methods to get book information from lasering.ee
# Dev/maintainer: Ando Roots 2010

import re
from google.appengine.api import urlfetch
from BeautifulSoup import BeautifulSoup
from BeautifulSoup import BeautifulStoneSoup

def GetItemByID(toote_id):
    lasering_url = 'http://www.lasering.ee/index.php?make=item_show&toote_id=' + toote_id
    #soup = BeautifulSoup(urlfetch.fetch(lasering_url).content)
    f = open('../importers/lasering.txt')
    soup = BeautifulSoup(f.read())
    f.close
    data_object = soup.html.body.table.tbody.tr.td
    #if ReSearch(soup, r'0,00&nbsp;&euro; / 0&nbsp;EEK&nbsp;'):
    #    return None # If 404
    
    
    
    data = {'a': str(data_object),
            'as': '',
            }

    return data

# ------------------------------ Helper functions --------------------------------- #

# Regex search - find needle in haystack and return it
def ReSearch(haystack, needle):
	p = re.compile(needle).search(str(haystack))
	if p:
		return p.group(0)
	else:
		return None