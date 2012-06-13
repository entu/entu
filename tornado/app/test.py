from tornado import auth, web
from datetime import datetime

import random
import string
import hashlib
import time
import logging

import db
from helper import *


class ShowTest(myRequestHandler):
    @web.authenticated
    def get(self, test_id=None):
        test_id = test_id.strip('-')
        entity = db.Entity(user_locale=self.get_user_locale(), user_id=self.current_user.id)

        test_ids = entity.get_relatives(ids_only=True, related_entity_id=self.current_user.id, entity_definition_id=60, relation_type='leecher', reverse_relation=True)
        if not test_ids:
            return self.redirect('/oldauth')

        test_ids = sorted(test_ids)

        if not test_id:
            test_id = test_ids[0]

        test_id = int(test_id)

        if test_id not in test_ids:
            return self.redirect('/test')

        db_con = db.connection()

        pages = []
        row = 0
        for id in test_ids:
            row += 1
            pages.append({
                'label': row,
                'id': id,
                'active': True if id == test_id else False
            })

        test = entity.get(entity_id=test_id, limit=1)
        test_questions = entity.get_relatives(entity_id=test_id, relation_type='child')

        questions = {}
        if test_questions.values():
            for q in test_questions.values()[0]:
                group = ''.join([x['value'] for x in q.get('properties', {}).get('group', []).get('values', []) if x['value']])

                prop = db_con.get(
                    """
                        SELECT
                            property.value_string AS value
                        FROM
                            relationship,
                            property
                        WHERE property.relationship_id = relationship.id
                        AND relationship.relationship_definition_id = 10
                        AND relationship.entity_id = %s
                        AND relationship.related_entity_id = %s
                        AND relationship.deleted IS NULL
                        AND property.deleted IS NULL
                        LIMIT 1;
                    """,
                    q.get('id'),
                    self.current_user.id
                )

                questions.setdefault(group, []).append({
                    'id': q['id'],
                    'label': ''.join([x['value'] for x in q.get('properties', {}).get('question', []).get('values', []) if x['value']]),
                    'type': ''.join([x['value'] for x in q.get('properties', {}).get('type', []).get('values', []) if x['value']]),
                    'value': prop.value if prop else ''
                })

        self.render('test/start.html',
            page_title = test.get('displayname', ''),
            test_id = test.get('id', ''),
            test_name = test.get('displayname', ''),
            test_description = ''.join([x['value'] for x in test.get('properties', {}).get('description', []).get('values', []) if x['value']]),
            pages = pages,
            questions = questions,
        )


class Answer(myRequestHandler):
    @web.authenticated
    def post(self):
        entity_id = self.get_argument('entity_id', default=None, strip=True)
        value = self.get_argument('value', default=None, strip=True)

        if not entity_id:
            return

        db_con = db.connection()

        entity = db.Entity(user_locale=self.get_user_locale(), user_id=self.current_user.id)
        if value:
            entity.set_relations(entity_id=entity_id, related_entity_id=self.current_user.id, relationship_type='rating', update=True)
            ratings = entity.get_relatives(relationship_ids_only=True, entity_id=entity_id, related_entity_id=self.current_user.id, relation_type='rating', reverse_relation=True)

            if ratings:
                prop = db_con.get('SELECT id FROM property WHERE property_definition_id = 513 AND relationship_id = %s AND deleted IS NULL LIMIT 1;', ratings[0])
                if prop:
                    property_id = prop.id
                else:
                    property_id = None
                entity.set_property(property_id=property_id, relationship_id=ratings[0], property_definition_id=513, value=value)
        else:
            entity.set_relations(entity_id=entity_id, related_entity_id=self.current_user.id, relationship_type='rating', delete=True)


class SubmitTest(myRequestHandler):
    @web.authenticated
    def get(self, test_id=None):
        test_id = test_id.strip('-')
        entity = db.Entity(user_locale=self.get_user_locale(), user_id=self.current_user.id)

        if not test_id:
            return self.redirect('/test')

        test_ids = entity.get_relatives(ids_only=True, related_entity_id=self.current_user.id, entity_definition_id=60, relation_type='leecher', reverse_relation=True)
        if not test_ids:
            return self.redirect('/')

        test_id = int(test_id)

        if test_id not in test_ids:
            return self.redirect('/test')

        db_con = db.connection()

        test_questions = entity.get_relatives(ids_only=True, entity_id=test_id, relation_type='child')

        unanswered = False
        for q in test_questions:
            prop = db_con.get(
                """
                    SELECT
                        property.value_string AS value
                    FROM
                        relationship,
                        property
                    WHERE property.relationship_id = relationship.id
                    AND relationship.relationship_definition_id = 10
                    AND relationship.entity_id = %s
                    AND relationship.related_entity_id = %s
                    AND relationship.deleted IS NULL
                    AND property.deleted IS NULL
                    LIMIT 1;
                """,
                q,
                self.current_user.id
            )
            if not prop:
                unanswered = True

        if unanswered == False:
            entity.set_relations(entity_id=test_id, related_entity_id=self.current_user.id, relationship_type='leecher', delete=True)
            return self.redirect('/test')

        self.redirect('/test-%s' % test_id)


handlers = [
    ('/test/answer', Answer),
    (r'/test-(.*)/submit', SubmitTest),
    (r'/test(.*)', ShowTest),
]
