/* 2012-08-24 keyname relations for definitios instead of id */

UPDATE entity e
LEFT JOIN entity_definition ed ON ed.id = e.entity_definition_id
SET e.entity_definition_keyname = ed.keyname;

--

UPDATE property_definition pd
RIGHT JOIN entity_definition ed ON ed.id = pd.entity_definition_id
SET pd.entity_definition_keyname = ed.keyname,
    pd.keyname = concat(ed.keyname, '_E_', pd.dataproperty);

UPDATE property_definition pd
SET pd.entity_definition_keyname = NULL,
    pd.keyname = concat('R_', pd.dataproperty)
WHERE pd.entity_definition_id IS NULL;

UPDATE property_definition pd
RIGHT JOIN entity_definition ed ON ed.id = pd.classifying_entity_definition_id
SET pd.classifying_entity_definition_keyname = ed.keyname;

--

UPDATE property p
LEFT JOIN property_definition pd ON pd.id = p.property_definition_id
SET p.property_definition_keyname = pd.keyname;

--

UPDATE relationship r
LEFT JOIN relationship_definition rd ON rd.id = r.relationship_definition_id
SET r.relationship_definition_keyname = rd.keyname;

UPDATE relationship r
LEFT JOIN entity_definition ed ON ed.id = r.entity_definition_id
SET r.entity_definition_keyname = ed.keyname;

UPDATE relationship r
LEFT JOIN entity_definition ed ON ed.id = r.related_entity_definition_id
SET r.related_entity_definition_keyname = ed.keyname;

UPDATE relationship r
LEFT JOIN property_definition pd ON pd.id = r.property_definition_id
SET r.property_definition_keyname = pd.keyname;

UPDATE relationship r
LEFT JOIN property_definition pd ON pd.id = r.related_property_definition_id
SET r.related_property_definition_keyname = pd.keyname;
