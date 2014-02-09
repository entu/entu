# taskdb.py

import torndb


class myDatabase():

    def get_app_settings(self, args):

        db = torndb.Connection(
            host     = args.database_host,
            database = args.database_name,
            user     = args.database_user,
            password = args.database_password,
        )

        sql = """
            SELECT DISTINCT
                e.id AS entity,
                property_definition.dataproperty AS property,
                IF(
                    property_definition.datatype='decimal',
                    property.value_decimal,
                    IF(
                        property_definition.datatype='integer',
                        property.value_integer,
                        IF(
                            property_definition.datatype='file',
                            property.value_file,
                            property.value_string
                        )
                    )
                ) AS value
            FROM (
                SELECT
                    entity.id,
                    entity.entity_definition_keyname
                FROM
                    entity,
                    relationship
                WHERE relationship.related_entity_id = entity.id
                AND entity.is_deleted = 0
                AND relationship.is_deleted = 0
                AND relationship.relationship_definition_keyname = 'child'
                AND relationship.entity_id IN (%s)
            ) AS e
            LEFT JOIN property_definition ON property_definition.entity_definition_keyname = e.entity_definition_keyname AND property_definition.is_deleted = 0
            LEFT JOIN property ON property.property_definition_keyname = property_definition.keyname AND property.entity_id = e.id AND property.is_deleted = 0;
        """ % args.customer_group

        customers = {}
        for c in db.query(sql):
            customers.setdefault(c.entity, {})[c.property] = c.value

        self.__app_settings = {}
        for c in customers.values():
            self.__app_settings[c.get('domain', '')] = c

        return self.__app_settings
