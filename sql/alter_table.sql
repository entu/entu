/* 2012-08-19 12:59   Add javascript datatype to property definition */
ALTER TABLE `property_definition` CHANGE `datatype` `datatype` ENUM('boolean','counter','counter_value','decimal','date','datetime','file','integer','reference','string','text','javascript')  NOT NULL  DEFAULT 'string';

/* 2012-08-24 keyname relations for definitios instead of id */

ALTER TABLE `entity` ADD `entity_definition_keyname` VARCHAR(100)  NOT NULL  DEFAULT ''  AFTER `deleted_by`;
ALTER TABLE `entity_definition` ADD `keyname` VARCHAR(100)  NOT NULL  DEFAULT ''  AFTER `id`;

UPDATE entity e
LEFT JOIN entity_definition ed ON ed.id = e.entity_definition_id
SET e.entity_definition_keyname = ed.keyname
WHERE IFNULL(e. entity_definition_keyname, '') = '';

ALTER TABLE `property` ADD `property_definition_keyname` VARCHAR(100)  NOT NULL  DEFAULT ''  AFTER `deleted_by`;
ALTER TABLE `property_definition` ADD `keyname` VARCHAR(100)  NOT NULL  DEFAULT ''  AFTER `id`;

UPDATE property p
LEFT JOIN property_definition pd ON pd.id = p.property_definition_id
SET p.property_definition_keyname = pd.keyname
WHERE IFNULL(p.property_definition_keyname, '') = '';

ALTER TABLE `property_definition` ADD `entity_definition_keyname` VARCHAR(100)  NOT NULL  DEFAULT ''  AFTER `keyname`;

UPDATE property_definition pd
LEFT JOIN entity_definition ed ON ed.id = pd.entity_definition_id
SET pd.entity_definition_keyname = ed.keyname
WHERE IFNULL(pd.entity_definition_keyname, '') = '';

ALTER TABLE `relationship` ADD `related_entity_definition_keyname` VARCHAR(100)  NOT NULL  DEFAULT ''  AFTER `deleted_by`;
ALTER TABLE `relationship` ADD `entity_definition_keyname` VARCHAR(100)  NOT NULL  DEFAULT ''  AFTER `deleted_by`;
ALTER TABLE `relationship` ADD `related_property_definition_keyname` VARCHAR(100)  NOT NULL  DEFAULT ''  AFTER `deleted_by`;
ALTER TABLE `relationship` ADD `property_definition_keyname` VARCHAR(100)  NOT NULL  DEFAULT ''  AFTER `deleted_by`;


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
