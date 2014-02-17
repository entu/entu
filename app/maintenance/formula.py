# formula.py
# !NB duplicate from db.formula

import logging
import re
import string
from decimal import Decimal

class Formula():
    """
    entity_id is accessed from FExpression.fetch_path_from_db() method
    """
    def __init__(self, db, property_id, entity_id, formula):
        self.db                     = db
        self.formula_property_id    = property_id
        self.entity_id              = entity_id
        self.formula                = formula
        self.value                  = []

        # logging.debug('Formula.init')
        # print 'Formula.init'

    def evaluate(self):
        if not self.formula:
            return ''

        for m in re.findall(r"([^{]*){([^{}]*)}|(.*?)$",self.formula):
            if m[0]:
                self.value.append(u'%s' % m[0])
            if m[1]:
                self.value.append(u'%s' % ','.join([u'%s' % x for x in FExpression(self, m[1]).value]))
            if m[2]:
                self.value.append(u'%s' % m[2])

        return self.value

    def save_property(self, new_property_id, old_property_id):

        self.db.execute('UPDATE property SET value_formula = %s WHERE id = %s;', self.formula, new_property_id)


class FExpression():
    def __init__(self, formula, xpr):
        self.db             = formula.db
        self.formula        = formula
        self.xpr            = re.sub(' ', '', xpr)
        self.value          = []

        # logging.debug(self.xpr)

        if not self.parcheck():
            self.value = "ERROR"
            return self.value

        re.sub(r"(.*?)([A-Z]+)\(([^\)]*)\)", mdbg, self.xpr)

        for m in re.findall(r"(.*?)([A-Z]+)\(([^\)]*)\)",self.xpr):
            self.value.append('%s%s' % (m[0], self.evalfunc(m[1], m[2])))
            # self.value.append('%s%s' % (m[0], ','.join(self.evalfunc(m[1], m[2]))))

        if self.value == []:
            _values = []
            for row in self.fetch_path_from_db(self.xpr):
                # logging.debug(row.value)
                _values.append(row.value)

            self.value = ['<->'.join(['%s' % x for x in _values])]
            # logging.debug(self.value)

        # logging.debug(re.findall(r"(.*?)([A-Z]+)\(([^\)]*)\)",self.xpr))
        # logging.debug(self.value)
        # self.value = map(eval, self.value)
        # logging.debug(self.value)

    def evalfunc(self, fname, path):
        FFunc = {
            'SUM' : self.FE_sum,
            'MIN' : self.FE_min,
            'MAX' : self.FE_max,
            'COUNT' : self.FE_count,
            'AVERAGE' : self.FE_average,
        }
        # logging.debug(FFunc[fname](self.fetch_path_from_db(path)))
        return FFunc[fname](self.fetch_path_from_db(path))

    def FE_sum(self, items):
        # [{'value': 'A'}, {'value': 'SS'}, {'value': 'E'}]
        try:
            return sum([Decimal(v.value) for v in items])
        except Exception, e:
            return string([Decimal(v.value) for v in items])

    def FE_min(self, items):
        try:
            return min([Decimal(v.value) for v in items])
        except Exception, e:
            return string([Decimal(v.value) for v in items])

    def FE_max(self, items):
        try:
            return max([Decimal(v.value) for v in items])
        except Exception, e:
            return string([Decimal(v.value) for v in items])

    def FE_average(self, items):
        try:
            return Decimal(sum([Decimal(v.value) for v in items]) / len(items))
        except Exception, e:
            return string([Decimal(v.value) for v in items])

    def FE_count(self, items):
        return len(items)

    def fetch_path_from_db(self, path):
        """
        https://github.com/argoroots/Entu/blob/master/docs/Formula.md
        """
        tokens = re.split('\.', path)
        # logging.debug(tokens)

        if len(tokens) < 2:
            return []

        if len(tokens) > 4:
            return []

        if tokens[0] == 'self':
            tokens[0] = self.formula.entity_id

        # Entity id:{self.id} is called {self.name}; and id:{6.id} description is {6.description}
        if len(tokens) == 2:
            sql = 'SELECT ifnull(p.value_decimal, ifnull(p.value_string, ifnull(p.value_text, ifnull(p.value_integer, ifnull(p.value_datetime, ifnull(p.value_boolean, p.value_file)))))) as value'
            if tokens[1] == 'id':
                sql = 'SELECT e.id as value'

            sql += """
                FROM entity e
            """

            if tokens[1] != 'id':
                sql += """
                    LEFT JOIN property p ON p.entity_id = e.id
                    LEFT JOIN property_definition pd ON pd.keyname = p.property_definition_keyname
                """

            sql += """
                WHERE e.id = %(entity_id)s
                AND e.is_deleted = 0
            """  % {'entity_id': tokens[0]}

            if tokens[1] != 'id':
                sql += """
                    AND p.is_deleted = 0
                    AND pd.dataproperty = '%(pdk)s'
                """ % {'pdk': tokens[1]}

            # logging.debug(sql)

            result = self.db.query(sql)

            # Entity {self.id} is called {self.name}, but {12.id} is called {12.name}

            return result

        # If second token is not one of relationship definition names,
        # then it has to be name of reference property
        # and third token has to be property name of referenced entity (entities);
        if tokens[1] not in ('child', 'viewer', 'expander', 'editor', 'owner', '-child', '-viewer', '-expander', '-editor', '-owner'):
            # also there should be exactly three tokens.
            if len(tokens) != 3:
                return []

            sql = 'SELECT ifnull(rep.value_decimal, ifnull(rep.value_string, ifnull(rep.value_text, ifnull(rep.value_integer, ifnull(rep.value_datetime, ifnull(rep.value_boolean, rep.value_file)))))) as value'
            if tokens[2] == 'id':
                sql = 'SELECT re.id as value'

            if tokens[1][:1] == '-':
                sql += """
                    FROM entity e
                    LEFT JOIN property p ON p.value_reference = e.id
                    LEFT JOIN property_definition pd ON pd.keyname = p.property_definition_keyname
                    LEFT JOIN entity re ON re.id = p.entity_id
                """
                tokens[1] = tokens[1][1:]
            else:
                sql += """
                    FROM entity e
                    LEFT JOIN property p ON p.entity_id = e.id
                    LEFT JOIN property_definition pd ON pd.keyname = p.property_definition_keyname
                    LEFT JOIN entity re ON re.id = p.value_reference
                """

            if tokens[2] != 'id':
                sql += """
                    LEFT JOIN property rep ON rep.entity_id = re.id
                    LEFT JOIN property_definition repd ON repd.keyname = rep.property_definition_keyname
                """

            sql += """
                WHERE e.id = %(entity_id)s
                AND e.is_deleted = 0
                AND p.is_deleted = 0
                AND pd.is_deleted = 0
                AND re.is_deleted = 0
                AND pd.dataproperty = '%(pdk)s'
            """  % {'entity_id': self.formula.entity_id, 'pdk': tokens[1]}

            if tokens[2] != 'id':
                sql += """
                    AND rep.is_deleted = 0
                    AND repd.is_deleted = 0
                    AND repd.dataproperty = '%(repdk)s'
                """  % {'repdk': tokens[2]}

            # logging.debug(sql)

            # There are {COUNT(self.child.folder.id)} folders called {self.child.folder.name}

            return self.db.query(sql)


        if len(tokens) != 4:
            return []

        sql = 'SELECT ifnull(p.value_decimal, ifnull(p.value_string, ifnull(p.value_text, ifnull(p.value_integer, ifnull(p.value_datetime, ifnull(p.value_boolean, p.value_file)))))) as value'
        if tokens[3] == 'id':
            sql = 'SELECT re.id as value'

        _entity = 'entity'
        _related_entity = 'related_entity'
        if tokens[1][:1] == '-':
            _entity = 'related_entity'
            _related_entity = 'entity'
            tokens[1] = tokens[1][1:]

        sql += """
            FROM entity e
            LEFT JOIN relationship r ON r.%(entity)s_id = e.id
            LEFT JOIN entity re ON re.id = r.%(related_entity)s_id
        """ % {'entity': _entity, 'related_entity': _related_entity}

        if tokens[3] != 'id':
            sql += """
                LEFT JOIN property p ON p.entity_id = re.id
                LEFT JOIN property_definition pd ON pd.keyname = p.property_definition_keyname
            """

        sql += """
            WHERE e.id = %(entity_id)s
            AND r.relationship_definition_keyname = '%(rdk)s'
            AND re.is_deleted = 0
            AND e.is_deleted = 0
            AND r.is_deleted = 0
        """  % {'entity_id': self.formula.entity_id, 'rdk': tokens[1]}

        if tokens[2] != '*':
            sql += """
                AND re.entity_definition_keyname = '%(edk)s'
            """  % {'edk': tokens[2]}

        if tokens[3] != 'id':
            sql += """
                AND p.is_deleted = 0
                AND pd.dataproperty = '%(pdk)s'
            """ % {'pdk': tokens[3]}

        # logging.debug(sql)

        # There are {COUNT(self.child.folder.id)} folders called {self.child.folder.name}

        return self.db.query(sql)

    def parcheck(self):
        return True
        s = Stack()
        balanced = True
        index = 0
        parenstr = re.search('([()])', self.xpr).join()
        while index < len(parenstr) and balanced:
            symbol = parenstr[index]
            if symbol == "(":
                s.push(symbol)
            else:
                if s.isEmpty():
                    balanced = False
                else:
                    s.pop()

            index = index + 1

        if balanced and s.isEmpty():
            return True
        else:
            return False


class Stack:
    def __init__(self):
        self.stack = []
    def push(self, item):
        self.stack.append(item)
    def check(self, item):
        return item in self.stack
    def pop(self):
        return self.stack.pop()
    @property
    def isEmpty(self):
        return self.stack == []
    @property
    def size(self):
        return len(self.stack)


class Queue:
    def __init__(self):
        self.in_stack = []
        self.out_stack = []
    def push(self, item):
        self.in_stack.append(item)
    def check(self, item):
        return (item in self.in_stack or item in self.out_stack)
    def pop(self):
        if not self.out_stack:
            self.in_stack.reverse()
            self.out_stack = self.in_stack
            self.in_stack = []
        return self.out_stack.pop()
    @property
    def isEmpty(self):
        return self.in_stack == [] and self.out_stack == []
    @property
    def size(self):
        return len(self.in_stack) + len(self.out_stack)


def mdbg(matchobj):
    # mdbg() is for regex match object debugging.
    #   i.e: re.sub(r"([^{]*){([^{}]*)}|(.*?)$", mdbg, self.formula)(ha()a)
    for m in matchobj.groups():
        pass
        # logging.debug(m)
