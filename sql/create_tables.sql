-- Create syntax for TABLE '_entu'
CREATE TABLE `_template` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_estonian_ci;


-- Create syntax for TABLE 'counter'
CREATE TABLE `counter` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `estonian_label` varchar(200) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  `english_label` varchar(200) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  `value` int DEFAULT '1',
  `increment` int NOT NULL DEFAULT '1',
  `type` enum('childcount','increment') CHARACTER SET utf8 COLLATE utf8_estonian_ci NOT NULL DEFAULT 'increment',
  `created` datetime DEFAULT NULL,
  `created_by` varchar(100) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  `changed` datetime DEFAULT NULL,
  `changed_by` varchar(100) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  `deleted` datetime DEFAULT NULL,
  `deleted_by` varchar(100) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  `old_id` varchar(200) CHARACTER SET utf8 COLLATE utf8_bin DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `old_id` (`old_id`),
  KEY `deleted` (`deleted`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_estonian_ci;

-- Create syntax for TABLE 'dag_entity'
CREATE TABLE `dag_entity` (
  `entity_id` int unsigned NOT NULL DEFAULT '0',
  `related_entity_id` int unsigned NOT NULL DEFAULT '0',
  `distance` int unsigned NOT NULL DEFAULT '1',
  PRIMARY KEY (`entity_id`,`related_entity_id`),
  KEY `de_fk_re` (`related_entity_id`),
  CONSTRAINT `de_fk_e` FOREIGN KEY (`entity_id`) REFERENCES `entity` (`id`) ON DELETE CASCADE,
  CONSTRAINT `de_fk_re` FOREIGN KEY (`related_entity_id`) REFERENCES `entity` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_estonian_ci;

-- Create syntax for TABLE 'entity'
CREATE TABLE `entity` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `definition_id` int unsigned DEFAULT NULL,
  `entity_definition_keyname` varchar(25) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `public` tinyint unsigned NOT NULL DEFAULT '0',
  `sharing` enum('public','link','domain','private') CHARACTER SET utf8 COLLATE utf8_estonian_ci NOT NULL DEFAULT 'private',
  `sharing_key` varchar(64) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  `sort` varchar(100) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  `search` text COLLATE utf8_estonian_ci,
  `public_search` text COLLATE utf8_estonian_ci,
  `created` datetime DEFAULT NULL,
  `created_by` varchar(100) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  `changed` datetime DEFAULT NULL,
  `changed_by` varchar(100) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  `deleted` datetime DEFAULT NULL,
  `is_deleted` tinyint unsigned NOT NULL DEFAULT '0',
  `deleted_by` varchar(100) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  `old_id` varchar(200) CHARACTER SET utf8 COLLATE utf8_bin DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `public` (`public`),
  KEY `entity_definition_keyname` (`entity_definition_keyname`),
  KEY `sort` (`sort`),
  KEY `deleted` (`deleted`),
  KEY `sharing` (`sharing`),
  KEY `sharing_key` (`sharing_key`),
  FULLTEXT KEY `search` (`search`),
  FULLTEXT KEY `public_search` (`public_search`),
  CONSTRAINT `e_fk_ed` FOREIGN KEY (`entity_definition_keyname`) REFERENCES `entity_definition` (`keyname`) ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_estonian_ci;

-- Create syntax for TABLE 'entity_definition'
CREATE TABLE `entity_definition` (
  `keyname` varchar(25) CHARACTER SET ascii COLLATE ascii_bin NOT NULL DEFAULT '',
  `ordinal` int DEFAULT NULL,
  `open_after_add` tinyint(1) NOT NULL DEFAULT '0',
  `public_path` varchar(100) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  `estonian_public` varchar(100) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  `english_public` varchar(100) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  `actions_add` varchar(100) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  `created` datetime DEFAULT NULL,
  `created_by` varchar(100) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  `changed` datetime DEFAULT NULL,
  `changed_by` varchar(100) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  `deleted` datetime DEFAULT NULL,
  `is_deleted` tinyint(1) NOT NULL DEFAULT '0',
  `deleted_by` varchar(100) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  `old_id` varchar(200) CHARACTER SET utf8 COLLATE utf8_bin DEFAULT NULL,
  PRIMARY KEY (`keyname`),
  UNIQUE KEY `old_id` (`old_id`),
  KEY `public_path` (`public_path`),
  KEY `deleted` (`deleted`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_estonian_ci;

-- Create syntax for TABLE 'file'
CREATE TABLE `file` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `md5` varchar(32) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  `filename` varchar(500) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  `filesize` int unsigned DEFAULT NULL,
  `url` varchar(2048) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  `s3_key` varchar(2048) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  `created` datetime DEFAULT NULL,
  `created_by` varchar(100) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  `changed` datetime DEFAULT NULL,
  `changed_by` varchar(100) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  `deleted` datetime DEFAULT NULL,
  `deleted_by` varchar(100) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  `old_id` varchar(200) CHARACTER SET utf8 COLLATE utf8_bin DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `old_id` (`old_id`),
  KEY `deleted` (`deleted`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_estonian_ci;

-- Create syntax for TABLE 'file_do'
CREATE TABLE `file_do` (
  `key` varchar(256) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `modified` datetime DEFAULT NULL,
  `etag` varchar(256) DEFAULT NULL,
  `size` int DEFAULT NULL,
  `class` varchar(256) DEFAULT NULL,
  PRIMARY KEY (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- Create syntax for TABLE 'file_s3'
CREATE TABLE `file_s3` (
  `key` varchar(256) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `modified` datetime DEFAULT NULL,
  `etag` varchar(256) DEFAULT NULL,
  `size` int DEFAULT NULL,
  `class` varchar(256) DEFAULT NULL,
  PRIMARY KEY (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- Create syntax for TABLE 'property'
CREATE TABLE `property` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `definition_id` int unsigned DEFAULT NULL,
  `property_definition_keyname` varchar(50) CHARACTER SET ascii COLLATE ascii_bin DEFAULT NULL,
  `entity_id` int unsigned NOT NULL,
  `ordinal` int DEFAULT NULL,
  `language` varchar(10) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  `value_display` varchar(500) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  `value_formula` varchar(500) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  `value_string` varchar(500) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  `value_text` text CHARACTER SET utf8 COLLATE utf8_estonian_ci,
  `value_integer` int DEFAULT NULL,
  `value_decimal` decimal(15,4) DEFAULT NULL,
  `value_boolean` tinyint unsigned DEFAULT NULL,
  `value_datetime` datetime DEFAULT NULL,
  `value_entity` int unsigned DEFAULT NULL,
  `value_reference` int unsigned DEFAULT NULL,
  `value_file` int unsigned DEFAULT NULL,
  `value_counter` int unsigned DEFAULT NULL,
  `created` datetime DEFAULT NULL,
  `created_by` varchar(100) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  `changed` datetime DEFAULT NULL,
  `changed_by` varchar(100) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  `deleted` datetime DEFAULT NULL,
  `is_deleted` tinyint unsigned NOT NULL DEFAULT '0',
  `deleted_by` varchar(100) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `property_definition_keyname` (`property_definition_keyname`),
  KEY `entity_id` (`entity_id`),
  KEY `ordinal` (`ordinal`),
  KEY `language` (`language`),
  KEY `value_string` (`value_string`(255)),
  KEY `value_file` (`value_file`),
  KEY `value_reference` (`value_reference`),
  KEY `value_counter` (`value_counter`),
  KEY `value_entity` (`value_entity`),
  KEY `deleted` (`deleted`),
  KEY `created` (`created`),
  KEY `changed` (`changed`),
  KEY `value_display` (`value_display`(255)),
  CONSTRAINT `p_fk_e` FOREIGN KEY (`entity_id`) REFERENCES `entity` (`id`),
  CONSTRAINT `p_fk_pd` FOREIGN KEY (`property_definition_keyname`) REFERENCES `property_definition` (`keyname`) ON UPDATE CASCADE,
  CONSTRAINT `p_fk_v_counter` FOREIGN KEY (`value_counter`) REFERENCES `counter` (`id`),
  CONSTRAINT `p_fk_v_file` FOREIGN KEY (`value_file`) REFERENCES `file` (`id`),
  CONSTRAINT `p_fk_v_reference` FOREIGN KEY (`value_reference`) REFERENCES `entity` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_estonian_ci;

-- Create syntax for TABLE 'property_definition'
CREATE TABLE `property_definition` (
  `keyname` varchar(50) CHARACTER SET ascii COLLATE ascii_bin NOT NULL DEFAULT '',
  `entity_definition_keyname` varchar(25) CHARACTER SET ascii COLLATE ascii_bin DEFAULT NULL,
  `dataproperty` varchar(24) CHARACTER SET ascii COLLATE ascii_bin DEFAULT NULL,
  `datatype` enum('boolean','counter','counter-value','decimal','date','datetime','file','integer','reference','string','text','secret') CHARACTER SET utf8 COLLATE utf8_estonian_ci NOT NULL DEFAULT 'string',
  `defaultvalue` varchar(500) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  `formula` tinyint unsigned NOT NULL DEFAULT '0',
  `executable` tinyint unsigned NOT NULL DEFAULT '0',
  `visible` tinyint unsigned NOT NULL DEFAULT '1',
  `ordinal` int DEFAULT NULL,
  `multilingual` tinyint unsigned NOT NULL DEFAULT '0',
  `multiplicity` int unsigned DEFAULT NULL,
  `readonly` tinyint unsigned NOT NULL DEFAULT '0',
  `createonly` tinyint unsigned NOT NULL DEFAULT '0',
  `public` tinyint unsigned NOT NULL DEFAULT '0',
  `mandatory` tinyint unsigned NOT NULL DEFAULT '0',
  `search` tinyint unsigned NOT NULL DEFAULT '0',
  `propagates` tinyint unsigned NOT NULL DEFAULT '0',
  `autocomplete` tinyint unsigned NOT NULL DEFAULT '0',
  `classifying_entity_definition_keyname` varchar(25) CHARACTER SET ascii COLLATE ascii_bin DEFAULT NULL,
  `created` datetime DEFAULT NULL,
  `created_by` varchar(100) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  `changed` datetime DEFAULT NULL,
  `changed_by` varchar(100) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  `deleted` datetime DEFAULT NULL,
  `is_deleted` tinyint(1) NOT NULL DEFAULT '0',
  `deleted_by` varchar(100) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  `old_id` varchar(200) CHARACTER SET utf8 COLLATE utf8_bin DEFAULT NULL,
  PRIMARY KEY (`keyname`),
  UNIQUE KEY `old_id` (`old_id`),
  KEY `ordinal` (`ordinal`),
  KEY `dataproperty` (`dataproperty`),
  KEY `entity_definition_keyname` (`entity_definition_keyname`),
  KEY `classifying_entity_definition_keyname` (`classifying_entity_definition_keyname`),
  KEY `deleted` (`deleted`),
  CONSTRAINT `pd_fk_ced` FOREIGN KEY (`classifying_entity_definition_keyname`) REFERENCES `entity_definition` (`keyname`) ON UPDATE CASCADE,
  CONSTRAINT `pd_fk_ed` FOREIGN KEY (`entity_definition_keyname`) REFERENCES `entity_definition` (`keyname`) ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_estonian_ci;

-- Create syntax for TABLE 'relationship'
CREATE TABLE `relationship` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `relationship_definition_keyname` varchar(25) CHARACTER SET ascii COLLATE ascii_bin NOT NULL DEFAULT '',
  `property_definition_keyname` varchar(50) CHARACTER SET ascii COLLATE ascii_bin DEFAULT NULL,
  `related_property_definition_keyname` varchar(50) CHARACTER SET ascii COLLATE ascii_bin DEFAULT NULL,
  `entity_definition_keyname` varchar(25) CHARACTER SET ascii COLLATE ascii_bin DEFAULT NULL,
  `related_entity_definition_keyname` varchar(25) CHARACTER SET ascii COLLATE ascii_bin DEFAULT NULL,
  `entity_id` int unsigned DEFAULT NULL,
  `related_entity_id` int unsigned DEFAULT NULL,
  `created` datetime DEFAULT NULL,
  `created_by` varchar(100) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  `changed` datetime DEFAULT NULL,
  `changed_by` varchar(100) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  `deleted` datetime DEFAULT NULL,
  `is_deleted` tinyint unsigned NOT NULL DEFAULT '0',
  `deleted_by` varchar(100) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  `old_id` varchar(200) CHARACTER SET utf8 COLLATE utf8_bin DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `old_id` (`old_id`),
  KEY `entity_id` (`entity_id`,`related_entity_id`),
  KEY `related_entity_id` (`related_entity_id`),
  KEY `relationship_definition_keyname` (`relationship_definition_keyname`),
  KEY `property_definition_keyname` (`property_definition_keyname`),
  KEY `related_property_definition_keyname` (`related_property_definition_keyname`),
  KEY `entity_definition_keyname` (`entity_definition_keyname`),
  KEY `related_entity_definition_keyname` (`related_entity_definition_keyname`),
  CONSTRAINT `r_fk_e` FOREIGN KEY (`entity_id`) REFERENCES `entity` (`id`),
  CONSTRAINT `r_fk_ed` FOREIGN KEY (`entity_definition_keyname`) REFERENCES `entity_definition` (`keyname`) ON UPDATE CASCADE,
  CONSTRAINT `r_fk_pd` FOREIGN KEY (`property_definition_keyname`) REFERENCES `property_definition` (`keyname`) ON UPDATE CASCADE,
  CONSTRAINT `r_fk_rd` FOREIGN KEY (`relationship_definition_keyname`) REFERENCES `relationship_definition` (`keyname`) ON UPDATE CASCADE,
  CONSTRAINT `r_fk_re` FOREIGN KEY (`related_entity_id`) REFERENCES `entity` (`id`),
  CONSTRAINT `r_fk_red` FOREIGN KEY (`related_entity_definition_keyname`) REFERENCES `entity_definition` (`keyname`) ON UPDATE CASCADE,
  CONSTRAINT `r_fk_rpd` FOREIGN KEY (`related_property_definition_keyname`) REFERENCES `property_definition` (`keyname`) ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_estonian_ci;

-- Create syntax for TABLE 'relationship_definition'
CREATE TABLE `relationship_definition` (
  `keyname` varchar(25) CHARACTER SET ascii COLLATE ascii_bin NOT NULL DEFAULT '',
  `created` datetime DEFAULT NULL,
  `created_by` varchar(100) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  `changed` datetime DEFAULT NULL,
  `changed_by` varchar(100) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  `deleted` datetime DEFAULT NULL,
  `is_deleted` tinyint(1) NOT NULL DEFAULT '0',
  `deleted_by` varchar(100) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  PRIMARY KEY (`keyname`),
  KEY `deleted` (`deleted`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_estonian_ci;

-- Create syntax for TABLE 'tmp_file'
CREATE TABLE `tmp_file` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `filename` varchar(500) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  `filesize` int unsigned DEFAULT NULL,
  `file` longblob,
  `created` datetime DEFAULT NULL,
  `created_by` varchar(100) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_estonian_ci;

-- Create syntax for TABLE 'translation'
CREATE TABLE `translation` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `entity_definition_keyname` varchar(25) CHARACTER SET ascii COLLATE ascii_bin DEFAULT NULL,
  `property_definition_keyname` varchar(50) CHARACTER SET ascii COLLATE ascii_bin DEFAULT NULL,
  `relationship_definition_keyname` varchar(25) CHARACTER SET ascii COLLATE ascii_bin DEFAULT NULL,
  `field` enum('','description','displayinfo','displayname','displaytable','displaytableheader','label','label_plural','menu','public','sort') CHARACTER SET ascii COLLATE ascii_bin NOT NULL DEFAULT '',
  `language` enum('','estonian','english') CHARACTER SET ascii COLLATE ascii_bin DEFAULT NULL,
  `value` varchar(300) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `language` (`language`),
  KEY `entity_definition_keyname` (`entity_definition_keyname`),
  KEY `property_definition_keyname` (`property_definition_keyname`),
  KEY `relationship_definition_keyname` (`relationship_definition_keyname`),
  CONSTRAINT `translation_ibfk_1` FOREIGN KEY (`entity_definition_keyname`) REFERENCES `entity_definition` (`keyname`) ON UPDATE CASCADE,
  CONSTRAINT `translation_ibfk_2` FOREIGN KEY (`property_definition_keyname`) REFERENCES `property_definition` (`keyname`) ON UPDATE CASCADE,
  CONSTRAINT `translation_ibfk_3` FOREIGN KEY (`relationship_definition_keyname`) REFERENCES `relationship_definition` (`keyname`) ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;


-- Create syntax for TABLE 'session'
CREATE TABLE `session` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `session_key` varchar(64) COLLATE utf8_estonian_ci DEFAULT NULL,
  `email` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `ip` varchar(64) COLLATE utf8_estonian_ci DEFAULT NULL,
  `browser` varchar(255) COLLATE utf8_estonian_ci DEFAULT NULL,
  `login_count` int(11) NOT NULL DEFAULT '0',
  `created` datetime DEFAULT NULL,
  `changed` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`),
  KEY `session_key` (`session_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_estonian_ci;
