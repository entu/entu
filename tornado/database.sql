
CREATE TABLE `all_props_mv` (
  `bubble_definition_id` int(11) unsigned DEFAULT NULL,
  `bubble_id` int(11) unsigned DEFAULT NULL,
  `property_definition_id` int(11) unsigned DEFAULT NULL,
  `property_id` int(11) unsigned NOT NULL DEFAULT '0',
  `bubble_label` varchar(500) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  `bubble_label_plural` varchar(500) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  `bubble_description` varchar(500) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  `property_fieldset` varchar(500) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  `property_label` varchar(500) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  `property_label_plural` varchar(500) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  `property_description` varchar(500) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  `bubble_created` datetime DEFAULT NULL,
  `property_value` longblob,
  `property_datatype` varchar(10) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  `property_dataproperty` varchar(20) CHARACTER SET utf8 COLLATE utf8_estonian_ci DEFAULT NULL,
  `property_multiplicity` int(11) unsigned DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;


CREATE TABLE `all_props_view` (
   `bubble_definition_id` INT(11) UNSIGNED DEFAULT '0',
   `bubble_id` INT(11) UNSIGNED DEFAULT '0',
   `property_definition_id` INT(11) UNSIGNED DEFAULT '0',
   `property_id` INT(11) UNSIGNED NOT NULL DEFAULT '0',
   `bubble_label` VARCHAR(500) DEFAULT NULL,
   `bubble_label_plural` VARCHAR(500) DEFAULT NULL,
   `bubble_description` VARCHAR(500) DEFAULT NULL,
   `property_fieldset` VARCHAR(500) DEFAULT NULL,
   `property_label` VARCHAR(500) DEFAULT NULL,
   `property_label_plural` VARCHAR(500) DEFAULT NULL,
   `property_description` VARCHAR(500) DEFAULT NULL,
   `bubble_created` DATETIME DEFAULT NULL,
   `property_value` LONGBLOB DEFAULT NULL,
   `property_datatype` VARCHAR(10) DEFAULT NULL,
   `property_dataproperty` VARCHAR(100) DEFAULT NULL,
   `property_multiplicity` INT(11) UNSIGNED DEFAULT NULL
) ENGINE=MyISAM;


CREATE TABLE `app_settings` (
  `name` varchar(100) COLLATE utf8_estonian_ci NOT NULL DEFAULT '',
  `value` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  PRIMARY KEY (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_estonian_ci;


CREATE TABLE `bubble` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `gae_key` varchar(200) COLLATE utf8_estonian_ci DEFAULT NULL,
  `created` datetime DEFAULT NULL,
  `created_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `changed` datetime DEFAULT NULL,
  `changed_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `deleted` datetime DEFAULT NULL,
  `deleted_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `bubble_definition_id` int(11) unsigned DEFAULT NULL,
  `public` tinyint(1) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `gae_key` (`gae_key`),
  KEY `bubble_definition_id` (`bubble_definition_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_estonian_ci;


CREATE TABLE `bubble_definition` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `gae_key` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `created` datetime DEFAULT NULL,
  `created_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `changed` datetime DEFAULT NULL,
  `changed_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `deleted` datetime DEFAULT NULL,
  `deleted_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `allowed_subtypes_id` int(11) unsigned DEFAULT NULL,
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


CREATE TABLE `file` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `gae_key` varchar(767) CHARACTER SET ascii DEFAULT NULL,
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


CREATE TABLE `property` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `created` datetime DEFAULT NULL,
  `created_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `changed` datetime DEFAULT NULL,
  `changed_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `deleted` datetime DEFAULT NULL,
  `deleted_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `property_definition_id` int(11) unsigned DEFAULT NULL,
  `bubble_id` int(11) unsigned DEFAULT NULL,
  `ordinal` int(11) DEFAULT NULL,
  `language` varchar(10) COLLATE utf8_estonian_ci DEFAULT NULL,
  `value_string` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `value_text` text COLLATE utf8_estonian_ci,
  `value_integer` int(11) DEFAULT NULL,
  `value_decimal` decimal(15,4) DEFAULT NULL,
  `value_boolean` tinyint(1) unsigned DEFAULT NULL,
  `value_datetime` datetime DEFAULT NULL,
  `value_reference` int(11) unsigned DEFAULT NULL,
  `value_file` int(11) unsigned DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `property_definition_id` (`property_definition_id`),
  KEY `value_string` (`value_string`(255)),
  KEY `ordinal` (`ordinal`),
  KEY `language` (`language`),
  KEY `value_file` (`value_file`),
  CONSTRAINT `property_ibfk_1` FOREIGN KEY (`value_file`) REFERENCES `file` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_estonian_ci;


CREATE TABLE `property_definition` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `gae_key` varchar(200) COLLATE utf8_estonian_ci DEFAULT NULL,
  `created` datetime DEFAULT NULL,
  `created_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `changed` datetime DEFAULT NULL,
  `changed_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `deleted` datetime DEFAULT NULL,
  `deleted_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `bubble_definition_id` int(11) unsigned DEFAULT NULL,
  `dataproperty` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `multilingual` tinyint(1) unsigned NOT NULL DEFAULT '0',
  `datatype` varchar(10) COLLATE utf8_estonian_ci NOT NULL,
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
  `ordinal` int(11) DEFAULT NULL,
  `multiplicity` int(11) unsigned DEFAULT NULL,
  `readonly` tinyint(1) unsigned NOT NULL DEFAULT '0',
  `createonly` tinyint(1) unsigned NOT NULL DEFAULT '0',
  `public` tinyint(1) unsigned NOT NULL DEFAULT '0',
  `mandatory` tinyint(1) unsigned NOT NULL DEFAULT '0',
  `search` tinyint(1) unsigned NOT NULL DEFAULT '0',
  `propagates` tinyint(1) unsigned NOT NULL DEFAULT '0',
  `autocomplete` tinyint(1) unsigned NOT NULL DEFAULT '0',
  `classifying_bubble_definition_id` int(11) unsigned NOT NULL,
  `target_property_definition_id` int(11) unsigned NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `gae_key` (`gae_key`),
  KEY `bubble_definition_id` (`bubble_definition_id`),
  KEY `ordinal` (`ordinal`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_estonian_ci;


CREATE TABLE `relationship` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `gae_key` varchar(200) COLLATE utf8_estonian_ci DEFAULT NULL,
  `created` datetime DEFAULT NULL,
  `created_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `changed` datetime DEFAULT NULL,
  `changed_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `deleted` datetime DEFAULT NULL,
  `deleted_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `bubble_id` int(11) unsigned NOT NULL,
  `related_bubble_id` int(11) unsigned NOT NULL,
  `type` varchar(20) COLLATE utf8_estonian_ci NOT NULL,
  `master_relationship_id` int(11) unsigned NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `gae_key` (`gae_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_estonian_ci;


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


CREATE TABLE `user_profile` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `user_id` int(11) unsigned DEFAULT NULL,
  `created` datetime DEFAULT NULL,
  `created_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `changed` datetime DEFAULT NULL,
  `changed_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `deleted` datetime DEFAULT NULL,
  `deleted_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `provider` varchar(10) COLLATE utf8_estonian_ci DEFAULT NULL,
  `provider_id` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `name` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `email` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `picture` varchar(200) COLLATE utf8_estonian_ci DEFAULT NULL,
  `session` varchar(200) COLLATE utf8_estonian_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `provider` (`provider`,`provider_id`),
  KEY `user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_estonian_ci;


DROP TABLE `all_props_view`;
CREATE ALGORITHM=UNDEFINED DEFINER=`bubbledu`@`%` SQL SECURITY DEFINER VIEW `all_props_view`
AS select
   `bubble_definition`.`id` AS `bubble_definition_id`,
   `bubble`.`id` AS `bubble_id`,
   `property_definition`.`id` AS `property_definition_id`,
   `property`.`id` AS `property_id`,
   `bubble_definition`.`estonian_label` AS `bubble_label`,
   `bubble_definition`.`estonian_label_plural` AS `bubble_label_plural`,
   `bubble_definition`.`estonian_description` AS `bubble_description`,
   `property_definition`.`estonian_fieldset` AS `property_fieldset`,
   `property_definition`.`estonian_label` AS `property_label`,
   `property_definition`.`estonian_label_plural` AS `property_label_plural`,
   `property_definition`.`estonian_description` AS `property_description`,
   `bubble`.`created` AS `bubble_created`,if((`property_definition`.`datatype` = 'string'),`property`.`value_string`,if((`property_definition`.`datatype` = 'text'),`property`.`value_text`,if((`property_definition`.`datatype` = 'integer'),`property`.`value_integer`,if((`property_definition`.`datatype` = 'decimal'),`property`.`value_decimal`,if((`property_definition`.`datatype` = 'boolean'),`property`.`value_boolean`,if(((`property_definition`.`datatype` = 'datetime') or (`property_definition`.`datatype` = 'date')),`property`.`value_datetime`,NULL)))))) AS `property_value`,
   `property_definition`.`datatype` AS `property_datatype`,
   `property_definition`.`dataproperty` AS `property_dataproperty`,
   `property_definition`.`multiplicity` AS `property_multiplicity`
from (((`property` left join `property_definition` on((`property`.`property_definition_id` = `property_definition`.`id`))) left join `bubble` on((`property`.`bubble_id` = `bubble`.`id`))) left join `bubble_definition` on((`bubble`.`bubble_definition_id` = `bubble_definition`.`id`)))
where ((1 = 1) and (`bubble`.`public` = 1) and (`property_definition`.`public` = 1)) order by `bubble`.`id`,`property_definition`.`ordinal`,`property`.`ordinal`;

