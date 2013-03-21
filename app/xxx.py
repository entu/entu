import time
import logging
import random
import string

from helper import *
from db import *


class XXX1(myRequestHandler):
    def get(self):
        time.sleep(60)
        rnd = ''.join(random.choice(string.digits) for x in range(4))
        logging.warning(rnd)
        self.write(rnd)

class XXX2(myRequestHandler):
    def get(self):
        rnd = ''.join(random.choice(string.digits) for x in range(4))
        logging.warning(rnd)
        self.write(rnd)


handlers = [
    ('/xxx1', XXX1),
    ('/xxx2', XXX2),
]
