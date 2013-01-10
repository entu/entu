-- Create syntax for TABLE 'app_settings'
CREATE TABLE `app_settings` (
  `keyname` varchar(25) CHARACTER SET ascii COLLATE ascii_bin NOT NULL DEFAULT '',
  `value` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  PRIMARY KEY (`keyname`)
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

-- Create syntax for TABLE 'file'
CREATE TABLE `file` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `created` datetime DEFAULT NULL,
  `created_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `changed` datetime DEFAULT NULL,
  `changed_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `deleted` datetime DEFAULT NULL,
  `deleted_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `filename` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `filesize` int(13) unsigned DEFAULT NULL,
  `file` longblob,
  `old_id` varchar(767) CHARACTER SET ascii COLLATE ascii_bin DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `old_id` (`old_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_estonian_ci;

-- Create syntax for TABLE 'tmp_file'
CREATE TABLE `tmp_file` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `created` datetime DEFAULT NULL,
  `created_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `filename` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `filesize` int(13) unsigned DEFAULT NULL,
  `file` longblob,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_estonian_ci;

-- Create syntax for TABLE 'counter'
CREATE TABLE `counter` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
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
  `old_id` varchar(200) CHARACTER SET utf8 COLLATE utf8_bin DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `old_id` (`old_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_estonian_ci;

-- Create syntax for TABLE 'entity_definition'
CREATE TABLE `entity_definition` (
  `keyname` varchar(25) CHARACTER SET ascii COLLATE ascii_bin NOT NULL DEFAULT '',
  `created` datetime DEFAULT NULL,
  `created_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `changed` datetime DEFAULT NULL,
  `changed_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `deleted` datetime DEFAULT NULL,
  `deleted_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `ordinal` int(11) DEFAULT NULL,
  `open_after_add` tinyint(1) NOT NULL DEFAULT '0',
  `public_path` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `estonian_label` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `estonian_label_plural` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `estonian_description` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `estonian_menu` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `estonian_public` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `estonian_displayname` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `estonian_displayinfo` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `estonian_displaytable` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `estonian_sort` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `english_label` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `english_label_plural` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `english_description` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `english_menu` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `english_public` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `english_displayname` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `english_displayinfo` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `english_displaytable` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `english_sort` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `actions_add` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `old_id` varchar(200) CHARACTER SET utf8 COLLATE utf8_bin DEFAULT NULL,
  PRIMARY KEY (`keyname`),
  UNIQUE KEY `keyname` (`keyname`),
  UNIQUE KEY `old_id` (`old_id`),
  KEY `public_path` (`public_path`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_estonian_ci;

-- Create syntax for TABLE 'entity'
CREATE TABLE `entity` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `entity_definition_keyname` varchar(25) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `created` datetime DEFAULT NULL,
  `created_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `changed` datetime DEFAULT NULL,
  `changed_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `deleted` datetime DEFAULT NULL,
  `deleted_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `public` tinyint(1) unsigned NOT NULL DEFAULT '0',
  `sort` varchar(100) CHARACTER SET utf8 DEFAULT NULL,
  `old_id` varchar(200) CHARACTER SET utf8 COLLATE utf8_bin DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `old_id` (`old_id`),
  KEY `entity_definition_keyname` (`entity_definition_keyname`),
  KEY `sort` (`sort`),
  CONSTRAINT `e_fk_ed` FOREIGN KEY (`entity_definition_keyname`) REFERENCES `entity_definition` (`keyname`) ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_estonian_ci;

-- Create syntax for TABLE 'relationship_definition'
CREATE TABLE `relationship_definition` (
  `keyname` varchar(25) CHARACTER SET ascii COLLATE ascii_bin NOT NULL DEFAULT '',
  `created` datetime DEFAULT NULL,
  `created_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `changed` datetime DEFAULT NULL,
  `changed_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `deleted` datetime DEFAULT NULL,
  `deleted_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `estonian_label` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `estonian_label_plural` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `estonian_description` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `english_label` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `english_label_plural` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `english_description` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  PRIMARY KEY (`keyname`),
  UNIQUE KEY `keyname` (`keyname`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_estonian_ci;

-- Create syntax for TABLE 'property_definition'
CREATE TABLE `property_definition` (
  `keyname` varchar(50) CHARACTER SET ascii COLLATE ascii_bin NOT NULL DEFAULT '',
  `entity_definition_keyname` varchar(25) CHARACTER SET ascii COLLATE ascii_bin DEFAULT NULL,
  `relationship_definition_keyname` varchar(25) CHARACTER SET ascii COLLATE ascii_bin DEFAULT NULL,
  `created` datetime DEFAULT NULL,
  `created_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `changed` datetime DEFAULT NULL,
  `changed_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `deleted` datetime DEFAULT NULL,
  `deleted_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `dataproperty` varchar(24) CHARACTER SET ascii COLLATE ascii_bin DEFAULT NULL,
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
  `classifying_entity_definition_keyname` varchar(100) CHARACTER SET ascii COLLATE ascii_bin DEFAULT NULL,
  `old_id` varchar(200) CHARACTER SET utf8 COLLATE utf8_bin DEFAULT NULL,
  PRIMARY KEY (`keyname`),
  UNIQUE KEY `keyname` (`keyname`),
  UNIQUE KEY `old_id` (`old_id`),
  KEY `ordinal` (`ordinal`),
  KEY `entity_definition_keyname` (`entity_definition_keyname`),
  KEY `relationship_definition_keyname` (`relationship_definition_keyname`),
  KEY `classifying_entity_definition_keyname` (`classifying_entity_definition_keyname`),
  CONSTRAINT `pd_fk_ced` FOREIGN KEY (`classifying_entity_definition_keyname`) REFERENCES `entity_definition` (`keyname`) ON UPDATE CASCADE,
  CONSTRAINT `pd_fk_ed` FOREIGN KEY (`entity_definition_keyname`) REFERENCES `entity_definition` (`keyname`) ON UPDATE CASCADE,
  CONSTRAINT `pd_fk_rd` FOREIGN KEY (`relationship_definition_keyname`) REFERENCES `relationship_definition` (`keyname`) ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_estonian_ci;

-- Create syntax for TABLE 'relationship'
CREATE TABLE `relationship` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `relationship_definition_keyname` varchar(25) CHARACTER SET ascii COLLATE ascii_bin NOT NULL DEFAULT '',
  `created` datetime DEFAULT NULL,
  `created_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `changed` datetime DEFAULT NULL,
  `changed_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `deleted` datetime DEFAULT NULL,
  `deleted_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `property_definition_keyname` varchar(50) CHARACTER SET ascii COLLATE ascii_bin DEFAULT NULL,
  `related_property_definition_keyname` varchar(50) CHARACTER SET ascii COLLATE ascii_bin DEFAULT NULL,
  `entity_definition_keyname` varchar(25) CHARACTER SET ascii COLLATE ascii_bin DEFAULT NULL,
  `related_entity_definition_keyname` varchar(25) CHARACTER SET ascii COLLATE ascii_bin DEFAULT NULL,
  `entity_id` int(11) unsigned DEFAULT NULL,
  `related_entity_id` int(11) unsigned DEFAULT NULL,
  `master_relationship_id` int(11) unsigned DEFAULT NULL,
  `old_id` varchar(200) CHARACTER SET utf8 COLLATE utf8_bin DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `old_id` (`old_id`),
  KEY `entity_id` (`entity_id`),
  KEY `related_entity_id` (`related_entity_id`),
  KEY `master_relationship_id` (`master_relationship_id`),
  KEY `entity_id_2` (`entity_id`,`related_entity_id`),
  KEY `r_fk_rd` (`relationship_definition_keyname`),
  KEY `r_fk_pd` (`property_definition_keyname`),
  KEY `r_fk_rpd` (`related_property_definition_keyname`),
  KEY `r_fk_ed` (`entity_definition_keyname`),
  KEY `r_fk_red` (`related_entity_definition_keyname`),
  CONSTRAINT `r_fk_red` FOREIGN KEY (`related_entity_definition_keyname`) REFERENCES `entity_definition` (`keyname`) ON UPDATE CASCADE,
  CONSTRAINT `relationship_ibfk_1` FOREIGN KEY (`entity_id`) REFERENCES `entity` (`id`),
  CONSTRAINT `relationship_ibfk_2` FOREIGN KEY (`related_entity_id`) REFERENCES `entity` (`id`),
  CONSTRAINT `relationship_ibfk_3` FOREIGN KEY (`master_relationship_id`) REFERENCES `relationship` (`id`),
  CONSTRAINT `r_fk_ed` FOREIGN KEY (`entity_definition_keyname`) REFERENCES `entity_definition` (`keyname`) ON UPDATE CASCADE,
  CONSTRAINT `r_fk_pd` FOREIGN KEY (`property_definition_keyname`) REFERENCES `property_definition` (`keyname`) ON UPDATE CASCADE,
  CONSTRAINT `r_fk_rd` FOREIGN KEY (`relationship_definition_keyname`) REFERENCES `relationship_definition` (`keyname`) ON UPDATE CASCADE,
  CONSTRAINT `r_fk_rpd` FOREIGN KEY (`related_property_definition_keyname`) REFERENCES `property_definition` (`keyname`) ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_estonian_ci;

-- Create syntax for TABLE 'property'
CREATE TABLE `property` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `property_definition_keyname` varchar(50) CHARACTER SET ascii COLLATE ascii_bin DEFAULT NULL,
  `created` datetime DEFAULT NULL,
  `created_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `changed` datetime DEFAULT NULL,
  `changed_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `deleted` datetime DEFAULT NULL,
  `deleted_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
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
  KEY `value_string` (`value_string`(255)),
  KEY `ordinal` (`ordinal`),
  KEY `language` (`language`),
  KEY `value_file` (`value_file`),
  KEY `value_reference` (`value_reference`),
  KEY `value_counter` (`value_counter`),
  KEY `entity_id` (`entity_id`),
  KEY `relationship_id` (`relationship_id`),
  KEY `value_entity` (`value_entity`),
  KEY `property_definition_keyname` (`property_definition_keyname`),
  CONSTRAINT `property_ibfk_1` FOREIGN KEY (`value_file`) REFERENCES `file` (`id`),
  CONSTRAINT `property_ibfk_3` FOREIGN KEY (`value_reference`) REFERENCES `entity` (`id`),
  CONSTRAINT `property_ibfk_4` FOREIGN KEY (`value_counter`) REFERENCES `counter` (`id`),
  CONSTRAINT `property_ibfk_5` FOREIGN KEY (`entity_id`) REFERENCES `entity` (`id`),
  CONSTRAINT `property_ibfk_6` FOREIGN KEY (`relationship_id`) REFERENCES `relationship` (`id`),
  CONSTRAINT `property_ibfk_7` FOREIGN KEY (`value_entity`) REFERENCES `entity` (`id`),
  CONSTRAINT `p_fk_pd` FOREIGN KEY (`property_definition_keyname`) REFERENCES `property_definition` (`keyname`) ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_estonian_ci;


CREATE TABLE `dag_formula` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `property_id` int(11) unsigned DEFAULT NULL,
  `related_property_id` int(11) unsigned DEFAULT NULL,
  `entity_id` int(11) unsigned DEFAULT NULL,
  `relationship_definition_keyname` varchar(25) CHARACTER SET ascii COLLATE ascii_bin DEFAULT NULL,
  `reverse_relationship` tinyint(1) unsigned DEFAULT NULL,
  `entity_definition_keyname` varchar(25) CHARACTER SET ascii COLLATE ascii_bin DEFAULT NULL,
  `dataproperty` varchar(24) CHARACTER SET ascii COLLATE ascii_bin DEFAULT NULL,
  `created` datetime DEFAULT NULL,
  `created_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `deleted` datetime DEFAULT NULL,
  `deleted_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fd_fk_p` (`property_id`),
  KEY `fd_fk_rp` (`related_property_id`),
  KEY `fd_fk_e` (`entity_id`),
  KEY `fd_fk_rdk` (`relationship_definition_keyname`),
  KEY `fd_fk_edk` (`entity_definition_keyname`),
  KEY `dataproperty` (`dataproperty`),
  CONSTRAINT `fd_fk_e` FOREIGN KEY (`entity_id`) REFERENCES `entity` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fd_fk_edk` FOREIGN KEY (`entity_definition_keyname`) REFERENCES `entity_definition` (`keyname`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fd_fk_p` FOREIGN KEY (`property_id`) REFERENCES `property` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fd_fk_rdk` FOREIGN KEY (`relationship_definition_keyname`) REFERENCES `relationship_definition` (`keyname`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fd_fk_rp` FOREIGN KEY (`related_property_id`) REFERENCES `property` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_estonian_ci;


CREATE TABLE `dag_entity` (
  `entity_id` int(11) unsigned NOT NULL DEFAULT '0',
  `related_entity_id` int(11) unsigned NOT NULL DEFAULT '0',
  `distance` int(10) unsigned NOT NULL DEFAULT '1',
  PRIMARY KEY (`entity_id`,`related_entity_id`),
  KEY `de_fk_re` (`related_entity_id`),
  CONSTRAINT `de_fk_e` FOREIGN KEY (`entity_id`) REFERENCES `entity` (`id`) ON DELETE CASCADE,
  CONSTRAINT `de_fk_re` FOREIGN KEY (`related_entity_id`) REFERENCES `entity` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_estonian_ci;