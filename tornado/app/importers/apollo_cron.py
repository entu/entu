# -*- coding: utf-8 -*-
# A Cron test for Apollo importer that runs once a day.
# Check if Apollo has changed it's HTML structure wich would mean the importer is broken.
# Idea - store importer data in GQL so it would be possible to disable the importer when needed

import pickle
import hashlib
import random
from bo import *
from importers.apollo import *

class ApolloCronTest(webapp.RequestHandler):
    def get(self, param):
        
        # I know something about those 4 books. If my info is not the same as Apollo's response
        # ...then it's a good guess the admin needs to check the syntax manually.
        known_data = {
        '0722492': '4c817381eabb0af5db834258f09e2102',
        '0761862': 'dba4ea11c0c2a59ba011b6ac6c34bfc2',
        '0305224': 'a86a02c949e3f41de6fac971964b5863',
        '3289239': '29920ee3407050e50658d0d95a381dd2',
        }
        
        random.seed()
        random_check = random.randrange(0,3)
        book_id = known_data.keys()
        result = pickle.dumps(set(GetBookByID(book_id[random_check]).items())) # Pickle it - make dict a string
        result = hashlib.md5(result).hexdigest() # MD5 it - make a long string short
        
        # Notify admins about system failure.
        if result != known_data[book_id[random_check]]:
			SendMail('ando@roots.ee',Translate('apollo_failure_msg_title'), Translate('apollo_failure_msg'))
			self.response.out.write('Something is broken.<br />')
        self.response.out.write('Cron done.')
        

def main():
    Route([
             ('/apollo_cron/(.*)', ApolloCronTest),
            ])


if __name__ == '__main__':
    main()