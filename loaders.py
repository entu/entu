from google.appengine.tools import bulkloader
from google.appengine.ext import db
from google.appengine.ext import search
import datetime
import sys
import os.path


sys.path.append(
    os.path.abspath(
        os.path.dirname(
            os.path.realpath(__file__))))

from database import *


def get_date(s):
    if s:
        return datetime.datetime.strptime(s, '%Y-%m-%d').date()
    else:
        return None

def get_utf8(s):
    if s:
        return s.decode('utf-8')
    else:
        return None

def get_list(s):
    if s:
        return [s.decode('utf-8')]
    else:
        return []

def get_boolean(s):
    if s:
        if s.decode('utf-8').strip().lower() == 'true':
            return True
        else:
            return False
    else:
        return False


def get_dictionary_key(s):
    if s:
        return db.Key.from_path('Dictionary', s.decode('utf-8'))
    else:
        return None

def get_person_key(s):
    if s:
        return db.Key.from_path('Person', s.decode('utf-8'))
    else:
        return None

def get_role_key(s):
    if s:
        return db.Key.from_path('Role', s.decode('utf-8'))
    else:
        return None

def get_department_key(s):
    if s:
        return db.Key.from_path('Department', s.decode('utf-8'))
    else:
        return None

def get_curriculum_key(s):
    if s:
        return db.Key.from_path('Curriculum', s.decode('utf-8'))
    else:
        return None

def get_orientation_key(s):
    if s:
        return db.Key.from_path('Orientation', s.decode('utf-8'))
    else:
        return None

def get_module_key(s):
    if s:
        return db.Key.from_path('Module', s.decode('utf-8'))
    else:
        return None

def get_subject_key(s):
    if s:
        return db.Key.from_path('Subject', s.decode('utf-8'))
    else:
        return None

def get_ratingscale_key(s):
    if s:
        return db.Key.from_path('RatingScale', s.decode('utf-8'))
    else:
        return None



# DICTIONARY

class Dictionary_loader(bulkloader.Loader):
    def __init__(self):
        bulkloader.Loader.__init__(self, 'Dictionary', [
            ('key_name', get_utf8),
            ('name', get_utf8),
            ('value', get_utf8),
        ])
    def handle_entity(self, entity):
        entity.save()


class Translation_loader(bulkloader.Loader):
    def __init__(self):
        bulkloader.Loader.__init__(self, 'Translation', [
            ('key_name', get_utf8),
            ('dictionary', get_dictionary_key),
            ('dictionary_name', get_utf8),
            ('language', get_utf8),
            ('value', get_utf8),
        ])
    def handle_entity(self, entity):
        entity.save()



#PERSONS DATA

class Person_loader(bulkloader.Loader):
    def __init__(self):
        bulkloader.Loader.__init__(self, 'Person', [
            ('key_name', get_utf8),
            ('forename', get_utf8),
            ('surname', get_utf8),
            ('idcode', get_utf8),
            ('gender', get_dictionary_key),
            ('birth_date', get_date),
        ])
    def handle_entity(self, entity):
        entity.save()


class Contact_loader(bulkloader.Loader):
    def __init__(self):
        bulkloader.Loader.__init__(self, 'Contact', [
            ('key_name', get_utf8),
            ('person', get_person_key),
            ('type', get_dictionary_key),
            ('value', get_utf8),
        ])
    def handle_entity(self, entity):
        entity.save()


class Role_loader(bulkloader.Loader):
    def __init__(self):
        bulkloader.Loader.__init__(self, 'Role', [
            ('key_name', get_utf8),
            ('name', get_dictionary_key),
        ])
    def handle_entity(self, entity):
        entity.save()


class PersonRole_loader(bulkloader.Loader):
    def __init__(self):
        bulkloader.Loader.__init__(self, 'PersonRole', [
            ('key_name', get_utf8),
            ('person', get_person_key),
            ('role', get_role_key),
            ('department', get_department_key),
        ])
    def handle_entity(self, entity):
        entity.save()




class Department_loader(bulkloader.Loader):
    def __init__(self):
        bulkloader.Loader.__init__(self, 'Department', [
            ('key_name', get_utf8),
            ('name', get_dictionary_key),
            ('is_academic', get_boolean),
            ('parent_department', get_department_key),
        ])
    def handle_entity(self, entity):
        entity.save()





#CURRICULUM

class Curriculum_loader(bulkloader.Loader):
    def __init__(self):
        bulkloader.Loader.__init__(self, 'Curriculum', [
            ('key_name', get_utf8),
            ('name', get_dictionary_key),
            ('code', get_utf8),
            ('tags', get_list),
            ('level_of_education', get_dictionary_key),
            ('form_of_training', get_dictionary_key),
            ('nominal_years', int),
            ('nominal_credit_points', float),
            ('degree', get_dictionary_key),
        ])
    def handle_entity(self, entity):
        entity.save()


class Orientation_loader(bulkloader.Loader):
    def __init__(self):
        bulkloader.Loader.__init__(self, 'Orientation', [
            ('key_name', get_utf8),
            ('name', get_dictionary_key),
            ('code', get_utf8),
            ('tags', get_list),
            ('curriculum', get_curriculum_key),
        ])
    def handle_entity(self, entity):
        entity.save()


class Module_loader(bulkloader.Loader):
    def __init__(self):
        bulkloader.Loader.__init__(self, 'Module', [
            ('key_name', get_utf8),
            ('name', get_dictionary_key),
            ('orientation', get_orientation_key),
        ])
    def handle_entity(self, entity):
        entity.save()


class Subject_loader(bulkloader.Loader):
    def __init__(self):
        bulkloader.Loader.__init__(self, 'Subject', [
            ('key_name', get_utf8),
            ('name', get_dictionary_key),
            ('code', get_utf8),
            ('tags', get_list),
            ('credit_points', float),
            ('rating_scale', get_ratingscale_key),
        ])
    def handle_entity(self, entity):
        entity.save()


class ModuleSubject_loader(bulkloader.Loader):
    def __init__(self):
        bulkloader.Loader.__init__(self, 'ModuleSubject', [
            ('key_name', get_utf8),
            ('mandatory', get_boolean),
            ('module', get_module_key),
            ('subject', get_subject_key),
        ])
    def handle_entity(self, entity):
        entity.save()


class RatingScale_loader(bulkloader.Loader):
    def __init__(self):
        bulkloader.Loader.__init__(self, 'RatingScale', [
            ('key_name', get_utf8),
            ('name', get_dictionary_key),
        ])
    def handle_entity(self, entity):
        entity.save()


loaders = [
    Person_loader,
    Contact_loader,
    Role_loader,
    PersonRole_loader,
    Curriculum_loader,
    Orientation_loader,
    Module_loader,
    RatingScale_loader,
    Subject_loader,
    ModuleSubject_loader,
    Dictionary_loader,
    Translation_loader,
    Department_loader,
]