from google.appengine.api import memcache
from google.appengine.api import urlfetch

from BeautifulSoup import BeautifulSoup

from HTMLParser import HTMLParser
from urllib import quote

#http://www.loc.gov/marc/bibliographic/
MARCMAP = {
    '020':  'isbn',
    '022':  'issn',
    '041':  'language',
    '041h': 'original_language',
    '072':  'udc',
    '080':  'udc',
    '245':  'title',
    '245b': 'subtitle',
    '245p': 'subtitle',
    '245n': 'number',
    '250':  'edition',
    '260':  'publishing_place',
    '260b': 'publisher',
    '260c': 'publishing_date',
    '300':  'pages',
    '300c': 'dimensions',
    '440':  'series',
    '440p': 'series',
    '440n': 'series_number',
    '440v': 'series_number',
    '500':  'notes',
    '501':  'notes',
    '502':  'notes',
    '504':  'notes',
    '505':  'notes',
    '520':  'notes',
    '525':  'notes',
    '530':  'notes',
    '650':  'tag',
    '655':  'tag',
}


def EsterSearch(search_term):
    items = []
    id = None
    search_isbn = False
    
    if len(search_term) == 10 and search_term.isdigit():
        search_isbn = True
    if len(search_term) == 10 and search_term[:9].isdigit():
        search_isbn = True
    if len(search_term) == 13 and search_term.isdigit():
        search_isbn = True

    if search_isbn == True:
        soup = BeautifulSoup(urlfetch.fetch('http://tallinn.ester.ee/search*est/i?SEARCH='+search_term+'&searchscope=1&SUBMIT=OTSI', deadline=60).content)
        id = soup.find('a', attrs={'id': 'recordnum'})['href'].replace('http://tallinn.ester.ee/record=', '').replace('~S1', '').replace('*est', '').strip()
        items.append(EsterGetByID(id))
    else:
        soup = BeautifulSoup(urlfetch.fetch('http://tallinn.ester.ee/search*est/X?SEARCH='+quote(search_term.encode('utf-8'))+'&searchscope=1&SUBMIT=OTSI', deadline=60).content)
        id = soup.find('a', attrs={'id': 'recordnum'})
        if id:
            id = id['href'].replace('http://tallinn.ester.ee/record=', '').replace('~S1', '').replace('*est', '').strip()
            items.append(EsterGetByID(id))
        else:
            for i in soup.findAll('table', attrs={'class': 'browseList'}):
                cells = i.findAll('td')
                id = cells[0].input['value'].strip()
                title = cells[1].span.a.contents[0].strip()
                isbn = cells[1].find(text='ISBN/ISSN').next.strip(':&nbsp;\n ').strip()
                year = cells[4].contents[0].strip()
                items.append({
                    'id': id,
                    'isbn': [{'value': isbn}],
                    'title': [{'value': title}],
                    'publishing_date': [{'value': year}],
                })

    return items


def EsterGetByID(id):
    marc = urlfetch.fetch('http://tallinn.ester.ee/search~S1?/.'+id+'/.'+id+'/1%2C1%2C1%2CB/marc~'+id).content.split('<pre>')[1].split('</pre>')[0].strip()
    item = ParseMARC(HTMLParser().unescape(marc))
    item['id'] = id
    return item


def ParseMARC(data):
    result = {}
    rows = []
    rownum = 0
    for row in data.strip().split('\n'):
        if row[:7].strip():
            rownum += 1
            rows.append(row)
        else:
            rows[rownum-1] += row[7:]

    for row in rows:
        key = row[:3]
        values = row[7:].split('|')

        if key in ['100', '700']:
            if values[0]:
                tag = 'author'
                tag_value = CleanData(values[0])
                tag_note = None
                for v in values[1:]:
                    if v:
                        if v[0] == 'd':
                            tag_note = CleanData(v[1:])
                        if key == '700' and v[0] == 'e':
                            tag = CleanData(v[1:])
                if tag not in result:
                    result[tag] = []
                result[tag].append({'value': tag_value, 'note': tag_note})
        else:
            if values[0]:
                if key in MARCMAP:
                    tag = MARCMAP[key]
                    if tag not in result:
                        result[tag] = []
                    result[tag].append({'value': CleanData(values[0], tag), 'note': None})
            for v in values[1:]:
                if v:
                    if key+v[0] in MARCMAP:
                        tag = MARCMAP[key+v[0]]
                        if tag not in result:
                            result[tag] = []
                        result[tag].append({'value': CleanData(v[1:], tag), 'note': None})
    return result


def CleanData(value, tag=None):
    value = value.decode('utf-8').strip(' /,;:')
    if value[0:1] == '[' and value[-1] == ']':
        value = value[1:][:-1]
    if tag == 'publishing_date' and not value[0:1].isdigit():
        value = value[1:]
    return value


def unescape(text):
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text)


def GetType(record):

    if '000' in record:
        a = record['000'][0]['a'][6:7]
        b = record['000'][0]['a'][7:8]

        if a == 'a':
            if 'acdm'.find(b) > 0:
                return 'book'
            if 'bis'.find(b) > 0:
                return 'series'

        if a == 't':
            return 'book'

        if a == 'p':
            return 'mixed'

        if a == 'm':
            return 'file'

        if 'ef'.find(a) > 0:
            return 'map'

        if 'gkor'.find(a) > 0:
            return 'visual'

        if 'sdij'.find(a) > 0:
            return 'music'