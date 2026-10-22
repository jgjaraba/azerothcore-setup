-- azerothcore-setup: acceso nativo a Cripta de Karazhan (piloto).
-- Generated from tools/crypt_portals.json; verify with build_crypt_portals.py.
-- Requires existing instance_template(800,0,empty,0) and matching client DBC.
-- Exact reruns are no-ops; any differing owned row fails closed.
-- Run with mysql batch stop-on-error, never --force. No runtime reload here.
-- On failed CALL the transaction is rolled back; remove the helper routine
-- azerothcore_setup_crypt_access after inspecting the collision, before retry.
USE `acore_world`;
SET NAMES utf8mb4;
DELIMITER $$
CREATE PROCEDURE `azerothcore_setup_crypt_access`()
BEGIN
  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    RESIGNAL;
  END;
  START TRANSACTION;
  IF NOT EXISTS (SELECT 1 FROM `instance_template` WHERE `map`=800 AND `parent`=0 AND BINARY `script`=BINARY '' AND `allowMount`=0)
     OR EXISTS (SELECT 1 FROM `dungeon_access_template` WHERE `map_id`=800 AND `id`<>124)
     OR EXISTS (SELECT 1 FROM `dungeon_access_requirements` WHERE `dungeon_access_id`=124)
     OR EXISTS (SELECT 1 FROM `areatrigger_scripts` WHERE `entry` IN (900800,900801))
     OR EXISTS (SELECT 1 FROM `areatrigger_tavern` WHERE `id` IN (900800,900801))
     OR EXISTS (SELECT 1 FROM `areatrigger_involvedrelation` WHERE `id` IN (900800,900801))
     OR EXISTS (SELECT 1 FROM `gameobject` WHERE `id` IN (900800,900801) AND `guid` NOT IN (900800,900801)) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='azerothcore-setup: crypt prerequisite or binding collision';
  END IF;
  INSERT INTO `areatrigger` (`entry`, `map`, `x`, `y`, `z`, `radius`, `length`, `width`, `height`, `orientation`)
  SELECT 900800, 0, -11068.14, -1826.3, 62.2, 0, 1, 8, 6, 1.59698
  WHERE NOT EXISTS (SELECT 1 FROM `areatrigger` WHERE `entry` <=> 900800
      AND `map` <=> 0
      AND ABS(`x` - -11068.14) <= 0.001
      AND ABS(`y` - -1826.3) <= 0.001
      AND ABS(`z` - 62.2) <= 0.001
      AND `radius` <=> 0
      AND ABS(`length` - 1) <= 0.001
      AND ABS(`width` - 8) <= 0.001
      AND ABS(`height` - 6) <= 0.001
      AND ABS(`orientation` - 1.59698) <= 0.001);
  INSERT INTO `areatrigger_teleport` (`ID`, `Name`, `target_map`, `target_position_x`, `target_position_y`, `target_position_z`, `target_orientation`)
  SELECT 900800, 'azerothcore-setup: Cripta de Karazhan - Entrada', 800, -11068.1, -1806.4, 52.85, 1.5
  WHERE NOT EXISTS (SELECT 1 FROM `areatrigger_teleport` WHERE `ID` <=> 900800
      AND BINARY `Name` <=> BINARY 'azerothcore-setup: Cripta de Karazhan - Entrada'
      AND `target_map` <=> 800
      AND ABS(`target_position_x` - -11068.1) <= 0.001
      AND ABS(`target_position_y` - -1806.4) <= 0.001
      AND ABS(`target_position_z` - 52.85) <= 0.001
      AND ABS(`target_orientation` - 1.5) <= 0.001);
  INSERT INTO `gameobject_template` (`entry`, `type`, `displayId`, `name`, `IconName`, `castBarCaption`, `unk1`, `size`, `Data0`, `Data1`, `Data2`, `Data3`, `Data4`, `Data5`, `Data6`, `Data7`, `Data8`, `Data9`, `Data10`, `Data11`, `Data12`, `Data13`, `Data14`, `Data15`, `Data16`, `Data17`, `Data18`, `Data19`, `Data20`, `Data21`, `Data22`, `Data23`, `AIName`, `ScriptName`, `VerifiedBuild`)
  SELECT 900800, 5, 672, 'azerothcore-setup: Cripta de Karazhan - Entrada', '', '', '', 1.6, 0, 1, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, '', '', NULL
  WHERE NOT EXISTS (SELECT 1 FROM `gameobject_template` WHERE `entry` <=> 900800
      AND `type` <=> 5
      AND `displayId` <=> 672
      AND BINARY `name` <=> BINARY 'azerothcore-setup: Cripta de Karazhan - Entrada'
      AND BINARY `IconName` <=> BINARY ''
      AND BINARY `castBarCaption` <=> BINARY ''
      AND BINARY `unk1` <=> BINARY ''
      AND ABS(`size` - 1.6) <= 0.001
      AND `Data0` <=> 0
      AND `Data1` <=> 1
      AND `Data2` <=> 0
      AND `Data3` <=> 0
      AND `Data4` <=> 0
      AND `Data5` <=> 0
      AND `Data6` <=> -1
      AND `Data7` <=> 0
      AND `Data8` <=> 0
      AND `Data9` <=> 0
      AND `Data10` <=> 0
      AND `Data11` <=> 0
      AND `Data12` <=> 0
      AND `Data13` <=> 0
      AND `Data14` <=> 0
      AND `Data15` <=> 0
      AND `Data16` <=> 0
      AND `Data17` <=> 0
      AND `Data18` <=> 0
      AND `Data19` <=> 0
      AND `Data20` <=> 0
      AND `Data21` <=> 0
      AND `Data22` <=> 0
      AND `Data23` <=> 0
      AND BINARY `AIName` <=> BINARY ''
      AND BINARY `ScriptName` <=> BINARY ''
      AND `VerifiedBuild` <=> NULL);
  INSERT INTO `gameobject` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `position_x`, `position_y`, `position_z`, `orientation`, `rotation0`, `rotation1`, `rotation2`, `rotation3`, `spawntimesecs`, `animprogress`, `state`, `ScriptName`, `VerifiedBuild`, `Comment`)
  SELECT 900800, 900800, 0, 41, 2563, 1, 1, -11068.14, -1826.3, 60.2, 1.59698, 0, 0, 0.7163032463465403, 0.6977891223524537, 300, 255, 1, '', NULL, 'azerothcore-setup: Cripta de Karazhan - Entrada'
  WHERE NOT EXISTS (SELECT 1 FROM `gameobject` WHERE `guid` <=> 900800
      AND `id` <=> 900800
      AND `map` <=> 0
      AND `zoneId` <=> 41
      AND `areaId` <=> 2563
      AND `spawnMask` <=> 1
      AND `phaseMask` <=> 1
      AND ABS(`position_x` - -11068.14) <= 0.001
      AND ABS(`position_y` - -1826.3) <= 0.001
      AND ABS(`position_z` - 60.2) <= 0.001
      AND ABS(`orientation` - 1.59698) <= 0.001
      AND ABS(`rotation0` - 0) <= 0.001
      AND ABS(`rotation1` - 0) <= 0.001
      AND ABS(`rotation2` - 0.7163032463465403) <= 0.001
      AND ABS(`rotation3` - 0.6977891223524537) <= 0.001
      AND `spawntimesecs` <=> 300
      AND `animprogress` <=> 255
      AND `state` <=> 1
      AND BINARY `ScriptName` <=> BINARY ''
      AND `VerifiedBuild` <=> NULL
      AND BINARY `Comment` <=> BINARY 'azerothcore-setup: Cripta de Karazhan - Entrada');
  INSERT INTO `areatrigger` (`entry`, `map`, `x`, `y`, `z`, `radius`, `length`, `width`, `height`, `orientation`)
  SELECT 900801, 800, -11068.2998046875, -1814.06005859375, 53.97779846191406, 3, 0, 0, 0, 0
  WHERE NOT EXISTS (SELECT 1 FROM `areatrigger` WHERE `entry` <=> 900801
      AND `map` <=> 800
      AND ABS(`x` - -11068.2998046875) <= 0.001
      AND ABS(`y` - -1814.06005859375) <= 0.001
      AND ABS(`z` - 53.97779846191406) <= 0.001
      AND ABS(`radius` - 3) <= 0.001
      AND ABS(`length` - 0) <= 0.001
      AND ABS(`width` - 0) <= 0.001
      AND ABS(`height` - 0) <= 0.001
      AND ABS(`orientation` - 0) <= 0.001);
  INSERT INTO `areatrigger_teleport` (`ID`, `Name`, `target_map`, `target_position_x`, `target_position_y`, `target_position_z`, `target_orientation`)
  SELECT 900801, 'azerothcore-setup: Cripta de Karazhan - Salida', 0, -11068.9, -1828.6, 60.4, 3.1
  WHERE NOT EXISTS (SELECT 1 FROM `areatrigger_teleport` WHERE `ID` <=> 900801
      AND BINARY `Name` <=> BINARY 'azerothcore-setup: Cripta de Karazhan - Salida'
      AND `target_map` <=> 0
      AND ABS(`target_position_x` - -11068.9) <= 0.001
      AND ABS(`target_position_y` - -1828.6) <= 0.001
      AND ABS(`target_position_z` - 60.4) <= 0.001
      AND ABS(`target_orientation` - 3.1) <= 0.001);
  INSERT INTO `gameobject_template` (`entry`, `type`, `displayId`, `name`, `IconName`, `castBarCaption`, `unk1`, `size`, `Data0`, `Data1`, `Data2`, `Data3`, `Data4`, `Data5`, `Data6`, `Data7`, `Data8`, `Data9`, `Data10`, `Data11`, `Data12`, `Data13`, `Data14`, `Data15`, `Data16`, `Data17`, `Data18`, `Data19`, `Data20`, `Data21`, `Data22`, `Data23`, `AIName`, `ScriptName`, `VerifiedBuild`)
  SELECT 900801, 5, 672, 'azerothcore-setup: Cripta de Karazhan - Salida', '', '', '', 1.6, 0, 1, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, '', '', NULL
  WHERE NOT EXISTS (SELECT 1 FROM `gameobject_template` WHERE `entry` <=> 900801
      AND `type` <=> 5
      AND `displayId` <=> 672
      AND BINARY `name` <=> BINARY 'azerothcore-setup: Cripta de Karazhan - Salida'
      AND BINARY `IconName` <=> BINARY ''
      AND BINARY `castBarCaption` <=> BINARY ''
      AND BINARY `unk1` <=> BINARY ''
      AND ABS(`size` - 1.6) <= 0.001
      AND `Data0` <=> 0
      AND `Data1` <=> 1
      AND `Data2` <=> 0
      AND `Data3` <=> 0
      AND `Data4` <=> 0
      AND `Data5` <=> 0
      AND `Data6` <=> -1
      AND `Data7` <=> 0
      AND `Data8` <=> 0
      AND `Data9` <=> 0
      AND `Data10` <=> 0
      AND `Data11` <=> 0
      AND `Data12` <=> 0
      AND `Data13` <=> 0
      AND `Data14` <=> 0
      AND `Data15` <=> 0
      AND `Data16` <=> 0
      AND `Data17` <=> 0
      AND `Data18` <=> 0
      AND `Data19` <=> 0
      AND `Data20` <=> 0
      AND `Data21` <=> 0
      AND `Data22` <=> 0
      AND `Data23` <=> 0
      AND BINARY `AIName` <=> BINARY ''
      AND BINARY `ScriptName` <=> BINARY ''
      AND `VerifiedBuild` <=> NULL);
  INSERT INTO `gameobject` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `position_x`, `position_y`, `position_z`, `orientation`, `rotation0`, `rotation1`, `rotation2`, `rotation3`, `spawntimesecs`, `animprogress`, `state`, `ScriptName`, `VerifiedBuild`, `Comment`)
  SELECT 900801, 900801, 800, 5086, 5086, 1, 1, -11068.3, -1814.06, 53.9778, 4.69079, 0, 0, 0.714701791324783, -0.6994293027012426, 300, 255, 1, '', NULL, 'azerothcore-setup: Cripta de Karazhan - Salida'
  WHERE NOT EXISTS (SELECT 1 FROM `gameobject` WHERE `guid` <=> 900801
      AND `id` <=> 900801
      AND `map` <=> 800
      AND `zoneId` <=> 5086
      AND `areaId` <=> 5086
      AND `spawnMask` <=> 1
      AND `phaseMask` <=> 1
      AND ABS(`position_x` - -11068.3) <= 0.001
      AND ABS(`position_y` - -1814.06) <= 0.001
      AND ABS(`position_z` - 53.9778) <= 0.001
      AND ABS(`orientation` - 4.69079) <= 0.001
      AND ABS(`rotation0` - 0) <= 0.001
      AND ABS(`rotation1` - 0) <= 0.001
      AND ABS(`rotation2` - 0.714701791324783) <= 0.001
      AND ABS(`rotation3` - -0.6994293027012426) <= 0.001
      AND `spawntimesecs` <=> 300
      AND `animprogress` <=> 255
      AND `state` <=> 1
      AND BINARY `ScriptName` <=> BINARY ''
      AND `VerifiedBuild` <=> NULL
      AND BINARY `Comment` <=> BINARY 'azerothcore-setup: Cripta de Karazhan - Salida');
  INSERT INTO `dungeon_access_template` (`id`, `map_id`, `difficulty`, `min_level`, `max_level`, `min_avg_item_level`, `comment`)
  SELECT 124, 800, 0, 55, 0, 0, 'azerothcore-setup: Cripta de Karazhan - Normal'
  WHERE NOT EXISTS (SELECT 1 FROM `dungeon_access_template` WHERE `id` <=> 124
      AND `map_id` <=> 800
      AND `difficulty` <=> 0
      AND `min_level` <=> 55
      AND `max_level` <=> 0
      AND `min_avg_item_level` <=> 0
      AND BINARY `comment` <=> BINARY 'azerothcore-setup: Cripta de Karazhan - Normal');
  COMMIT;
END$$
DELIMITER ;
CALL `azerothcore_setup_crypt_access`();
DROP PROCEDURE `azerothcore_setup_crypt_access`;
