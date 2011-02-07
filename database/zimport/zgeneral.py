from google.appengine.ext import db


class zSchoolList(db.Model):
    name = db.StringProperty()