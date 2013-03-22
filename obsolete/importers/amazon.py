# Amazon data importer
# Ando Roots 2010

from bottlenose import *
from xml.dom import minidom

# AMAZON secrets
ACCESS_KEY_ID       = 'AKIAIWSREUOEGDASEMDQ'
SECRET_ACCESS_KEY   = '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'
ASSOCIATE_TAG       = None

book_details = {} # Holds the details of a single search result


# Search for a book by a keyword.
# Returns a list containing dicts for each result
def SearchBook(search_term):
    amazon = Amazon(ACCESS_KEY_ID, SECRET_ACCESS_KEY, ASSOCIATE_TAG)
    xml = amazon.ItemSearch(SearchIndex = 'Books', ResponseGroup = 'Medium', Keywords = search_term)
    dom = minidom.parseString(xml)
    
    final_data = []
    for book_item in dom.getElementsByTagName('Item'):
        
        global book_item
        global book_details
        
        addDetails('Title')
        addDetails('Author', True)
        addDetails('ISBN')
        addDetails('ASIN')
        addDetails('DetailPageURL')
        addDetails('Manufacturer')
        addDetails('ReleaseDate')
        book_details['LargeImage'] = getImage()
        
        final_data.append(book_details)
        book_details = {}
        
    return final_data


# Returns detailed information about a book
# Search by ASIN
def GetBook(ASIN):
    amazon = Amazon(ACCESS_KEY_ID, SECRET_ACCESS_KEY, ASSOCIATE_TAG)
    xml = amazon.ItemLookup(ItemId=ASIN, IdType='ASIN', ResponseGroup='Large')
    dom = minidom.parseString(xml)
    
    book_item = dom.getElementsByTagName('Item')[0]
    global book_item
    
    # What data to return? The argument indicates an XML tag name
    # If the tag is not found, the entry will be ignored
    addDetails('Title')
    addDetails('Author', True)
    addDetails('ISBN')
    addDetails('ASIN')
    addDetails('Edition')
    addDetails('Manufacturer')
    addDetails('ReleaseDate')
    addDetails('Studio')
    addDetails('DetailPageURL')
    addDetails('Binding')
    addDetails('Publisher')
    addDetails('ReleaseDate')
    book_details['LargeImage'] = getImage()
    
    return book_details


# Adds an additional return value to the GetBook query
def addDetails(tag_name, many = False):
    global book_item
    data = getElement(book_item, tag_name, many)
    if data:
        book_details[tag_name] = data


# Returns the largest available image of the item.
def getImage():
    global book_item
    try:
        large_image = book_item.getElementsByTagName('LargeImage')[0].getElementsByTagName('URL')[0].firstChild.data
        return large_image
    except IndexError, e:
        return None # For thesting, replace with empty string


# Extract element data from XML haystack
# Param many indicates that there might be multiple elements with the same name
# They are then returned as a list
def getElement(haystack, tag, many = False):
    element = haystack.getElementsByTagName(tag)
    try:
        if many :
            data = []
            i = 0
            for instance in element:
                data.append(element[i].firstChild.data)
                i += 1
            if (len(data) == 1):
                return data[0]
            else:
                return data #[0] + ' <font color="red">and </font>' + data[1] # For testing only
        else:
            return element[0].firstChild.data
    except IndexError, e:
        return None

# End of file amazon.py #