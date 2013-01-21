# ************************************************************
# Sequel Pro SQL dump
# Version 3408
#
# http://www.sequelpro.com/
# http://code.google.com/p/sequel-pro/
#
# Host: 127.0.0.1 (MySQL 5.1.66-0+squeeze1)
# Database: develop-mihkel
# Generation Time: 2013-01-21 01:10:53 +0000
# ************************************************************


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


# Dump of table app_settings
# ------------------------------------------------------------

DROP TABLE IF EXISTS `app_settings`;

CREATE TABLE `app_settings` (
  `keyname` varchar(100) COLLATE utf8_estonian_ci NOT NULL DEFAULT '',
  `value` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  PRIMARY KEY (`keyname`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_estonian_ci;



# Dump of table app_usage
# ------------------------------------------------------------

DROP TABLE IF EXISTS `app_usage`;

CREATE TABLE `app_usage` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `date` date DEFAULT NULL,
  `type` varchar(20) DEFAULT NULL,
  `amount` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;



# Dump of table counter
# ------------------------------------------------------------

DROP TABLE IF EXISTS `counter`;

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
  PRIMARY KEY (`id`),
  KEY `deleted` (`deleted`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_estonian_ci;



# Dump of table dag_entity
# ------------------------------------------------------------

DROP TABLE IF EXISTS `dag_entity`;

CREATE TABLE `dag_entity` (
  `entity_id` int(11) unsigned NOT NULL DEFAULT '0',
  `related_entity_id` int(11) unsigned NOT NULL DEFAULT '0',
  `distance` int(10) unsigned NOT NULL DEFAULT '1',
  PRIMARY KEY (`entity_id`,`related_entity_id`),
  KEY `de_fk_re` (`related_entity_id`),
  CONSTRAINT `de_fk_e` FOREIGN KEY (`entity_id`) REFERENCES `entity` (`id`) ON DELETE CASCADE,
  CONSTRAINT `de_fk_re` FOREIGN KEY (`related_entity_id`) REFERENCES `entity` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_estonian_ci;



# Dump of table dag_formula
# ------------------------------------------------------------

DROP TABLE IF EXISTS `dag_formula`;

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
  KEY `fd_fk_e` (`entity_id`),
  KEY `fd_fk_rdk` (`relationship_definition_keyname`),
  KEY `fd_fk_edk` (`entity_definition_keyname`),
  KEY `dataproperty` (`dataproperty`),
  CONSTRAINT `fd_fk_e` FOREIGN KEY (`entity_id`) REFERENCES `entity` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fd_fk_edk` FOREIGN KEY (`entity_definition_keyname`) REFERENCES `entity_definition` (`keyname`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fd_fk_p` FOREIGN KEY (`property_id`) REFERENCES `property` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fd_fk_rdk` FOREIGN KEY (`relationship_definition_keyname`) REFERENCES `relationship_definition` (`keyname`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_estonian_ci;



# Dump of table entity
# ------------------------------------------------------------

DROP TABLE IF EXISTS `entity`;

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
  `sort` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `old_id` varchar(200) CHARACTER SET utf8 COLLATE utf8_bin DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `old_id` (`old_id`),
  KEY `entity_definition_keyname` (`entity_definition_keyname`),
  KEY `sort` (`sort`),
  KEY `deleted` (`deleted`),
  CONSTRAINT `e_fk_ed` FOREIGN KEY (`entity_definition_keyname`) REFERENCES `entity_definition` (`keyname`) ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_estonian_ci;



# Dump of table entity_definition
# ------------------------------------------------------------

DROP TABLE IF EXISTS `entity_definition`;

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
  KEY `public_path` (`public_path`),
  KEY `deleted` (`deleted`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_estonian_ci;



# Dump of table file
# ------------------------------------------------------------

DROP TABLE IF EXISTS `file`;

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
  `old_id` varchar(200) CHARACTER SET utf8 COLLATE utf8_bin DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `old_id` (`old_id`),
  KEY `deleted` (`deleted`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_estonian_ci;



# Dump of table property
# ------------------------------------------------------------

DROP TABLE IF EXISTS `property`;

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
  `value_formula` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
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
  KEY `deleted` (`deleted`),
  CONSTRAINT `property_ibfk_1` FOREIGN KEY (`value_file`) REFERENCES `file` (`id`),
  CONSTRAINT `property_ibfk_3` FOREIGN KEY (`value_reference`) REFERENCES `entity` (`id`),
  CONSTRAINT `property_ibfk_4` FOREIGN KEY (`value_counter`) REFERENCES `counter` (`id`),
  CONSTRAINT `property_ibfk_5` FOREIGN KEY (`entity_id`) REFERENCES `entity` (`id`),
  CONSTRAINT `property_ibfk_6` FOREIGN KEY (`relationship_id`) REFERENCES `relationship` (`id`),
  CONSTRAINT `property_ibfk_7` FOREIGN KEY (`value_entity`) REFERENCES `entity` (`id`),
  CONSTRAINT `p_fk_pd` FOREIGN KEY (`property_definition_keyname`) REFERENCES `property_definition` (`keyname`) ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_estonian_ci;



# Dump of table property_definition
# ------------------------------------------------------------

DROP TABLE IF EXISTS `property_definition`;

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
  `formula` tinyint(1) unsigned NOT NULL DEFAULT '0',
  `executable` tinyint(1) unsigned NOT NULL DEFAULT '0',
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
  KEY `deleted` (`deleted`),
  CONSTRAINT `pd_fk_ced` FOREIGN KEY (`classifying_entity_definition_keyname`) REFERENCES `entity_definition` (`keyname`) ON UPDATE CASCADE,
  CONSTRAINT `pd_fk_ed` FOREIGN KEY (`entity_definition_keyname`) REFERENCES `entity_definition` (`keyname`) ON UPDATE CASCADE,
  CONSTRAINT `pd_fk_rd` FOREIGN KEY (`relationship_definition_keyname`) REFERENCES `relationship_definition` (`keyname`) ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_estonian_ci;



# Dump of table relationship
# ------------------------------------------------------------

DROP TABLE IF EXISTS `relationship`;

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
  KEY `related_entity_id` (`related_entity_id`),
  KEY `master_relationship_id` (`master_relationship_id`),
  KEY `relationship_definition_keyname` (`relationship_definition_keyname`),
  KEY `entity_id` (`entity_id`,`related_entity_id`),
  KEY `r_fk_pd` (`property_definition_keyname`),
  KEY `r_fk_rpd` (`related_property_definition_keyname`),
  KEY `r_fk_ed` (`entity_definition_keyname`),
  KEY `r_fk_red` (`related_entity_definition_keyname`),
  KEY `deleted` (`deleted`),
  CONSTRAINT `relationship_ibfk_2` FOREIGN KEY (`related_entity_id`) REFERENCES `entity` (`id`),
  CONSTRAINT `relationship_ibfk_3` FOREIGN KEY (`master_relationship_id`) REFERENCES `relationship` (`id`),
  CONSTRAINT `r_fk_ed` FOREIGN KEY (`entity_definition_keyname`) REFERENCES `entity_definition` (`keyname`) ON UPDATE CASCADE,
  CONSTRAINT `r_fk_pd` FOREIGN KEY (`property_definition_keyname`) REFERENCES `property_definition` (`keyname`) ON UPDATE CASCADE,
  CONSTRAINT `r_fk_rd` FOREIGN KEY (`relationship_definition_keyname`) REFERENCES `relationship_definition` (`keyname`) ON UPDATE CASCADE,
  CONSTRAINT `r_fk_red` FOREIGN KEY (`related_entity_definition_keyname`) REFERENCES `entity_definition` (`keyname`) ON UPDATE CASCADE,
  CONSTRAINT `r_fk_rpd` FOREIGN KEY (`related_property_definition_keyname`) REFERENCES `property_definition` (`keyname`) ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_estonian_ci;



# Dump of table relationship_definition
# ------------------------------------------------------------

DROP TABLE IF EXISTS `relationship_definition`;

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
  UNIQUE KEY `keyname` (`keyname`),
  KEY `deleted` (`deleted`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_estonian_ci;



# Dump of table tmp_file
# ------------------------------------------------------------

DROP TABLE IF EXISTS `tmp_file`;

CREATE TABLE `tmp_file` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `created` datetime DEFAULT NULL,
  `created_by` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `filename` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  `filesize` int(13) unsigned DEFAULT NULL,
  `file` longblob,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_estonian_ci;



# Dump of table user
# ------------------------------------------------------------

DROP TABLE IF EXISTS `user`;

CREATE TABLE `user` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `created` datetime DEFAULT NULL,
  `changed` datetime DEFAULT NULL,
  `provider` varchar(20) COLLATE utf8_estonian_ci DEFAULT NULL,
  `provider_id` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `name` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `email` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `picture` varchar(200) COLLATE utf8_estonian_ci DEFAULT NULL,
  `language` varchar(10) COLLATE utf8_estonian_ci DEFAULT NULL,
  `session` varchar(100) COLLATE utf8_estonian_ci DEFAULT NULL,
  `access_token` varchar(500) COLLATE utf8_estonian_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `provider` (`provider`,`provider_id`),
  KEY `session` (`session`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_estonian_ci;




--
-- Dumping routines (PROCEDURE) for database 'develop-mihkel'
--
DELIMITER ;;

# Dump of PROCEDURE FillDagEntity
# ------------------------------------------------------------

/*!50003 DROP PROCEDURE IF EXISTS `FillDagEntity` */;;
/*!50003 SET SESSION SQL_MODE=""*/;;
/*!50003 CREATE*/ /*!50020 DEFINER=`michelek`@`localhost`*/ /*!50003 PROCEDURE `FillDagEntity`()
BEGIN
  DECLARE no_more_childs, entity_id, related_entity_id, distance INT DEFAULT 0;

  DECLARE cur_childs CURSOR FOR
    SELECT de.entity_id, de2.related_entity_id AS related_entity_id, de.distance+de2.distance AS distance
    FROM dag_entity de
    LEFT JOIN dag_entity de2 ON de2.entity_id = de.related_entity_id
    WHERE de2.entity_id IS NOT NULL;
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET no_more_childs = 1;

  OPEN cur_childs;
    FETCH cur_childs INTO entity_id, related_entity_id, distance;
    WHILE no_more_childs = 0 DO
      INSERT INTO dag_entity (entity_id, related_entity_id, distance) VALUES (entity_id, related_entity_id, distance)
      ON DUPLICATE KEY UPDATE dag_entity.distance=least(dag_entity.distance, distance);

      FETCH cur_childs INTO entity_id, related_entity_id, distance;
    END WHILE;

  CLOSE cur_childs;

END */;;

/*!50003 SET SESSION SQL_MODE=@OLD_SQL_MODE */;;
# Dump of PROCEDURE GrantRecursiveViewer
# ------------------------------------------------------------

/*!50003 DROP PROCEDURE IF EXISTS `GrantRecursiveViewer` */;;
/*!50003 SET SESSION SQL_MODE=""*/;;
/*!50003 CREATE*/ /*!50020 DEFINER=`michelek`@`localhost`*/ /*!50003 PROCEDURE `GrantRecursiveViewer`(IN rootEntity_in INT(11), IN viewer_in INT(11))
BEGIN
  DECLARE no_more_childs, child_id INT DEFAULT 0;
  DECLARE viewer_rd INT;

  DECLARE cur_childs CURSOR FOR
    SELECT r.related_entity_id
    FROM relationship r
    WHERE r.entity_id = rootEntity_in AND r.relationship_definition_keyname = 'child' AND r.deleted IS NULL;

  DECLARE CONTINUE HANDLER FOR NOT FOUND SET no_more_childs = 1;

  -- Grant viewer rights
  INSERT IGNORE INTO relationship SET created=now(), created_by='GrantRecursiveViewer' ,relationship_definition_keyname = 'viewer', entity_id = rootEntity_in, related_entity_id = viewer_in
  ON DUPLICATE KEY UPDATE relationship_definition_keyname = 'viewer', entity_id = rootEntity_in, related_entity_id = viewer_in;

  OPEN cur_childs;
    FETCH cur_childs INTO child_id;
    WHILE no_more_childs = 0 DO
      CALL GrantRecursiveViewer(child_id, viewer_in);
      FETCH cur_childs INTO child_id;
    END WHILE;

  CLOSE cur_childs;

END */;;

/*!50003 SET SESSION SQL_MODE=@OLD_SQL_MODE */;;
DELIMITER ;

/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
