-- Create syntax for TABLE 'app_settings'
CREATE TABLE `app_settings` (
  `name` varchar(100) COLLATE utf8_estonian_ci NOT NULL DEFAULT '',
  `value` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  PRIMARY KEY (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_estonian_ci;

-- Create syntax for TABLE 'app_usage'
CREATE TABLE `app_usage` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `date` date DEFAULT NULL,
  `type` varchar(20) DEFAULT NULL,
  `amount` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- Create syntax for TABLE 'counter'
CREATE TABLE `counter` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `gae_key` varchar(200) CHARACTER SET utf8 COLLATE utf8_bin DEFAULT NULL,
  `created` datetime DEFAULT NULL,
  `created_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `changed` datetime DEFAULT NULL,
  `changed_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `deleted` datetime DEFAULT NULL,
  `deleted_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `estonian_label` varchar(200) COLLATE utf8_estonian_ci DEFAULT NULL,
  `english_label` varchar(200) COLLATE utf8_estonian_ci DEFAULT NULL,
  `value` int(11) DEFAULT '1',
  `increment` int(11) NOT NULL DEFAULT '1',
  `type` enum('childcount','increment') COLLATE utf8_estonian_ci NOT NULL DEFAULT 'increment',
  PRIMARY KEY (`id`),
  UNIQUE KEY `gae_key` (`gae_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_estonian_ci;

-- Create syntax for TABLE 'entity'
CREATE TABLE `entity` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `gae_key` varchar(200) CHARACTER SET utf8 COLLATE utf8_bin DEFAULT NULL,
  `created` datetime DEFAULT NULL,
  `created_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `changed` datetime DEFAULT NULL,
  `changed_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `deleted` datetime DEFAULT NULL,
  `deleted_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `entity_definition_id` int(11) unsigned DEFAULT NULL,
  `public` tinyint(1) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `gae_key` (`gae_key`),
  KEY `entity_definition_id` (`entity_definition_id`),
  CONSTRAINT `entity_ibfk_1` FOREIGN KEY (`entity_definition_id`) REFERENCES `entity_definition` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_estonian_ci;

-- Create syntax for TABLE 'entity_definition'
CREATE TABLE `entity_definition` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `gae_key` varchar(100) CHARACTER SET utf8 COLLATE utf8_bin DEFAULT NULL,
  `created` datetime DEFAULT NULL,
  `created_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `changed` datetime DEFAULT NULL,
  `changed_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `deleted` datetime DEFAULT NULL,
  `deleted_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `ordinal` int(11) DEFAULT NULL,
  `estonian_label` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `estonian_label_plural` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `estonian_description` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `estonian_menu` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `estonian_displayname` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `estonian_displayinfo` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `estonian_displaytable` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `estonian_sort` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `english_label` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `english_label_plural` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `english_description` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `english_menu` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `english_displayname` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `english_displayinfo` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `english_displaytable` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `english_sort` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `gae_key` (`gae_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_estonian_ci;

-- Create syntax for TABLE 'file'
CREATE TABLE `file` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `gae_key` varchar(767) CHARACTER SET ascii COLLATE ascii_bin DEFAULT NULL,
  `created` datetime DEFAULT NULL,
  `created_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `changed` datetime DEFAULT NULL,
  `changed_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `deleted` datetime DEFAULT NULL,
  `deleted_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `filename` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `filesize` int(13) unsigned DEFAULT NULL,
  `file` longblob,
  PRIMARY KEY (`id`),
  UNIQUE KEY `gae_key` (`gae_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_estonian_ci;

-- Create syntax for TABLE 'property'
CREATE TABLE `property` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `created` datetime DEFAULT NULL,
  `created_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `changed` datetime DEFAULT NULL,
  `changed_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `deleted` datetime DEFAULT NULL,
  `deleted_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `property_definition_id` int(11) unsigned DEFAULT NULL,
  `entity_id` int(11) unsigned DEFAULT NULL,
  `ordinal` int(11) DEFAULT NULL,
  `language` varchar(10) COLLATE utf8_estonian_ci DEFAULT NULL,
  `value_string` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `value_text` text COLLATE utf8_estonian_ci,
  `value_integer` int(11) DEFAULT NULL,
  `value_decimal` decimal(15,4) DEFAULT NULL,
  `value_boolean` tinyint(1) unsigned DEFAULT NULL,
  `value_datetime` datetime DEFAULT NULL,
  `value_entity` int(11) unsigned DEFAULT NULL,
  `value_reference` int(11) unsigned DEFAULT NULL,
  `value_file` int(11) unsigned DEFAULT NULL,
  `value_counter` int(11) unsigned DEFAULT NULL,
  `relationship_id` int(11) unsigned DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `property_definition_id` (`property_definition_id`),
  KEY `value_string` (`value_string`(255)),
  KEY `ordinal` (`ordinal`),
  KEY `language` (`language`),
  KEY `value_file` (`value_file`),
  KEY `value_reference` (`value_reference`),
  KEY `value_counter` (`value_counter`),
  KEY `entity_id` (`entity_id`),
  KEY `relationship_id` (`relationship_id`),
  KEY `value_entity` (`value_entity`),
  CONSTRAINT `property_ibfk_1` FOREIGN KEY (`value_file`) REFERENCES `file` (`id`),
  CONSTRAINT `property_ibfk_2` FOREIGN KEY (`property_definition_id`) REFERENCES `property_definition` (`id`),
  CONSTRAINT `property_ibfk_3` FOREIGN KEY (`value_reference`) REFERENCES `entity` (`id`),
  CONSTRAINT `property_ibfk_4` FOREIGN KEY (`value_counter`) REFERENCES `counter` (`id`),
  CONSTRAINT `property_ibfk_5` FOREIGN KEY (`entity_id`) REFERENCES `entity` (`id`),
  CONSTRAINT `property_ibfk_6` FOREIGN KEY (`relationship_id`) REFERENCES `relationship` (`id`),
  CONSTRAINT `property_ibfk_7` FOREIGN KEY (`value_entity`) REFERENCES `entity` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_estonian_ci;

-- Create syntax for TABLE 'property_definition'
CREATE TABLE `property_definition` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `gae_key` varchar(200) CHARACTER SET utf8 COLLATE utf8_bin DEFAULT NULL,
  `created` datetime DEFAULT NULL,
  `created_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `changed` datetime DEFAULT NULL,
  `changed_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `deleted` datetime DEFAULT NULL,
  `deleted_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `entity_definition_id` int(11) unsigned DEFAULT NULL,
  `dataproperty` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `datatype` enum('boolean','counter','counter_value','decimal','date','datetime','file','integer','reference','string','text') COLLATE utf8_estonian_ci NOT NULL DEFAULT 'string',
  `defaultvalue` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `estonian_fieldset` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `estonian_label` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `estonian_label_plural` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `estonian_description` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `estonian_formatstring` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `english_fieldset` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `english_label` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `english_label_plural` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `english_description` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `english_formatstring` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `visible` tinyint(1) unsigned NOT NULL DEFAULT '1',
  `ordinal` int(11) DEFAULT NULL,
  `multilingual` tinyint(1) unsigned NOT NULL DEFAULT '0',
  `multiplicity` int(11) unsigned DEFAULT NULL,
  `readonly` tinyint(1) unsigned NOT NULL DEFAULT '0',
  `createonly` tinyint(1) unsigned NOT NULL DEFAULT '0',
  `public` tinyint(1) unsigned NOT NULL DEFAULT '0',
  `mandatory` tinyint(1) unsigned NOT NULL DEFAULT '0',
  `search` tinyint(1) unsigned NOT NULL DEFAULT '0',
  `propagates` tinyint(1) unsigned NOT NULL DEFAULT '0',
  `autocomplete` tinyint(1) unsigned NOT NULL DEFAULT '0',
  `classifying_entity_definition_id` int(11) unsigned DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `gae_key` (`gae_key`),
  KEY `entity_definition_id` (`entity_definition_id`),
  KEY `ordinal` (`ordinal`),
  KEY `classifying_entity_definition_id` (`classifying_entity_definition_id`),
  CONSTRAINT `property_definition_ibfk_1` FOREIGN KEY (`entity_definition_id`) REFERENCES `entity_definition` (`id`),
  CONSTRAINT `property_definition_ibfk_2` FOREIGN KEY (`classifying_entity_definition_id`) REFERENCES `entity_definition` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_estonian_ci;

-- Create syntax for TABLE 'relationship'
CREATE TABLE `relationship` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `gae_key` varchar(200) CHARACTER SET utf8 COLLATE utf8_bin DEFAULT NULL,
  `created` datetime DEFAULT NULL,
  `created_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `changed` datetime DEFAULT NULL,
  `changed_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `deleted` datetime DEFAULT NULL,
  `deleted_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `relationship_definition_id` int(11) unsigned DEFAULT NULL,
  `type` varchar(20) COLLATE utf8_estonian_ci DEFAULT '',
  `property_definition_id` int(11) unsigned DEFAULT NULL,
  `entity_id` int(11) unsigned DEFAULT NULL,
  `entity_definition_id` int(11) unsigned DEFAULT NULL,
  `related_property_definition_id` int(11) unsigned DEFAULT NULL,
  `related_entity_id` int(11) unsigned DEFAULT NULL,
  `related_entity_definition_id` int(11) unsigned DEFAULT NULL,
  `master_relationship_id` int(11) unsigned DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `gae_key` (`gae_key`),
  KEY `entity_id` (`entity_id`),
  KEY `related_entity_id` (`related_entity_id`),
  KEY `master_relationship_id` (`master_relationship_id`),
  KEY `entity_definition_id` (`entity_definition_id`),
  KEY `related_entity_definition_id` (`related_entity_definition_id`),
  KEY `property_definition_id` (`property_definition_id`),
  KEY `related_property_definition_id` (`related_property_definition_id`),
  KEY `entity_id_2` (`entity_id`,`related_entity_id`),
  KEY `relationship_definition_id` (`relationship_definition_id`),
  CONSTRAINT `relationship_ibfk_1` FOREIGN KEY (`entity_id`) REFERENCES `entity` (`id`),
  CONSTRAINT `relationship_ibfk_2` FOREIGN KEY (`related_entity_id`) REFERENCES `entity` (`id`),
  CONSTRAINT `relationship_ibfk_3` FOREIGN KEY (`master_relationship_id`) REFERENCES `relationship` (`id`),
  CONSTRAINT `relationship_ibfk_4` FOREIGN KEY (`entity_definition_id`) REFERENCES `entity_definition` (`id`),
  CONSTRAINT `relationship_ibfk_5` FOREIGN KEY (`related_entity_definition_id`) REFERENCES `entity_definition` (`id`),
  CONSTRAINT `relationship_ibfk_6` FOREIGN KEY (`property_definition_id`) REFERENCES `property_definition` (`id`),
  CONSTRAINT `relationship_ibfk_7` FOREIGN KEY (`related_property_definition_id`) REFERENCES `property_definition` (`id`),
  CONSTRAINT `relationship_ibfk_8` FOREIGN KEY (`relationship_definition_id`) REFERENCES `relationship_definition` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_estonian_ci;

-- Create syntax for TABLE 'relationship_definition'
CREATE TABLE `relationship_definition` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `created` datetime DEFAULT NULL,
  `created_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `changed` datetime DEFAULT NULL,
  `changed_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `deleted` datetime DEFAULT NULL,
  `deleted_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `type` varchar(20) COLLATE utf8_estonian_ci DEFAULT NULL,
  `estonian_label` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `estonian_label_plural` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `estonian_description` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `english_label` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `english_label_plural` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `english_description` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_estonian_ci;

-- Create syntax for TABLE 'user'
CREATE TABLE `user` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `created` datetime DEFAULT NULL,
  `created_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `changed` datetime DEFAULT NULL,
  `changed_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `deleted` datetime DEFAULT NULL,
  `deleted_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `name` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `email` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `picture` varchar(200) COLLATE utf8_estonian_ci DEFAULT NULL,
  `language` varchar(10) COLLATE utf8_estonian_ci DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_estonian_ci;

-- Create syntax for TABLE 'user_profile'
CREATE TABLE `user_profile` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `user_id` int(11) unsigned DEFAULT NULL,
  `created` datetime DEFAULT NULL,
  `created_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `changed` datetime DEFAULT NULL,
  `changed_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `deleted` datetime DEFAULT NULL,
  `deleted_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `provider` varchar(20) COLLATE utf8_estonian_ci DEFAULT NULL,
  `provider_id` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `name` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `email` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `picture` varchar(200) COLLATE utf8_estonian_ci DEFAULT NULL,
  `session` varchar(200) COLLATE utf8_estonian_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `provider` (`provider`,`provider_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `user_profile_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_estonian_ci;
