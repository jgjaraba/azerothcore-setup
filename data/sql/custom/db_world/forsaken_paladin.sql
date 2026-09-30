USE `acore_world`;

-- Forsaken Paladin baseline: Undead (5) / Paladin (2) creation data and trainers.
-- This file is the sole manifest-owned source for this project's Forsaken Paladin baseline.

START TRANSACTION;

DELETE FROM `playercreateinfo_action` WHERE `race` = 5 AND `class` = 2;
DELETE FROM `playercreateinfo` WHERE `race` = 5 AND `class` = 2;
DELETE FROM `charstartoutfit_dbc` WHERE `ID` IN (9000, 9001);

DELETE FROM `creature_addon` WHERE `guid` IN (5300690, 5300691);
DELETE FROM `creature` WHERE `guid` IN (5300690, 5300691) AND `id` IN (90210, 90211);
DELETE FROM `creature_default_trainer` WHERE `CreatureId` IN (90210, 90211);
DELETE FROM `creature_template_locale` WHERE `entry` IN (90210, 90211);
DELETE FROM `creature_equip_template` WHERE `CreatureID` IN (90210, 90211);
DELETE FROM `creature_template_model` WHERE `CreatureID` IN (90210, 90211);
DELETE FROM `creature_template` WHERE `entry` IN (90210, 90211);

INSERT INTO `playercreateinfo`
    (`race`, `class`, `map`, `zone`, `position_x`, `position_y`, `position_z`, `orientation`)
VALUES
    (5, 2, 0, 85, 1676.71, 1678.31, 121.67, 2.70526);

INSERT INTO `playercreateinfo_action` (`race`, `class`, `button`, `action`, `type`) VALUES
    (5, 2, 0, 6603, 0),
    (5, 2, 1, 21084, 0),
    (5, 2, 2, 635, 0),
    (5, 2, 3, 20577, 0),
    (5, 2, 10, 159, 128),
    (5, 2, 11, 4604, 128);

INSERT INTO `charstartoutfit_dbc` (
    `ID`, `RaceID`, `ClassID`, `SexID`, `OutfitID`,
    `ItemID_1`, `ItemID_2`, `ItemID_3`, `ItemID_4`, `ItemID_5`, `ItemID_6`, `ItemID_7`,
    `DisplayItemID_1`, `DisplayItemID_2`, `DisplayItemID_3`, `DisplayItemID_4`, `DisplayItemID_5`,
    `DisplayItemID_6`, `DisplayItemID_7`,
    `InventoryType_1`, `InventoryType_2`, `InventoryType_3`, `InventoryType_4`, `InventoryType_5`,
    `InventoryType_6`, `InventoryType_7`
) VALUES
    (9000, 5, 2, 0, 0, 45, 43, 44, 6948, 2361, 159, 4604, 3265, 9938, 9937, 6418, 8690, 18084, 15852,
     4, 8, 7, 0, 17, 0, 0),
    (9001, 5, 2, 1, 0, 45, 43, 44, 6948, 2361, 159, 4604, 3265, 9938, 9937, 6418, 8690, 18084, 15852,
     4, 8, 7, 0, 17, 0, 0);

-- The custom templates retain current base template mechanics while making only
-- their project-owned identity and trainer metadata explicit.
INSERT INTO `creature_template` (
    `entry`, `difficulty_entry_1`, `difficulty_entry_2`, `difficulty_entry_3`, `KillCredit1`, `KillCredit2`,
    `name`, `subname`, `IconName`, `gossip_menu_id`, `minlevel`, `maxlevel`, `exp`, `faction`, `npcflag`,
    `speed_walk`, `speed_run`, `speed_swim`, `speed_flight`, `detection_range`, `rank`, `dmgschool`,
    `DamageModifier`, `BaseAttackTime`, `RangeAttackTime`, `BaseVariance`, `RangeVariance`, `unit_class`,
    `unit_flags`, `unit_flags2`, `dynamicflags`, `family`, `type`, `type_flags`, `lootid`, `pickpocketloot`,
    `skinloot`, `PetSpellDataId`, `VehicleId`, `mingold`, `maxgold`, `AIName`, `MovementType`, `HoverHeight`,
    `HealthModifier`, `ManaModifier`, `ArmorModifier`, `ExperienceModifier`, `RacialLeader`, `movementId`,
    `RegenHealth`, `CreatureImmunitiesId`, `flags_extra`, `ScriptName`, `VerifiedBuild`
)
SELECT
    90210, `difficulty_entry_1`, `difficulty_entry_2`, `difficulty_entry_3`, `KillCredit1`, `KillCredit2`,
    'Abraham West', 'Paladin Trainer', 'Trainer', 0, `minlevel`, `maxlevel`, `exp`, `faction`, 49,
    `speed_walk`, `speed_run`, `speed_swim`, `speed_flight`, `detection_range`, `rank`, `dmgschool`,
    `DamageModifier`, `BaseAttackTime`, `RangeAttackTime`, `BaseVariance`, `RangeVariance`, `unit_class`,
    `unit_flags`, `unit_flags2`, `dynamicflags`, `family`, `type`, `type_flags`, `lootid`, `pickpocketloot`,
    `skinloot`, `PetSpellDataId`, `VehicleId`, `mingold`, `maxgold`, `AIName`, `MovementType`, `HoverHeight`,
    `HealthModifier`, `ManaModifier`, `ArmorModifier`, `ExperienceModifier`, `RacialLeader`, `movementId`,
    `RegenHealth`, `CreatureImmunitiesId`, `flags_extra`, '', 0
FROM `creature_template`
WHERE `entry` = 2129;

INSERT INTO `creature_template` (
    `entry`, `difficulty_entry_1`, `difficulty_entry_2`, `difficulty_entry_3`, `KillCredit1`, `KillCredit2`,
    `name`, `subname`, `IconName`, `gossip_menu_id`, `minlevel`, `maxlevel`, `exp`, `faction`, `npcflag`,
    `speed_walk`, `speed_run`, `speed_swim`, `speed_flight`, `detection_range`, `rank`, `dmgschool`,
    `DamageModifier`, `BaseAttackTime`, `RangeAttackTime`, `BaseVariance`, `RangeVariance`, `unit_class`,
    `unit_flags`, `unit_flags2`, `dynamicflags`, `family`, `type`, `type_flags`, `lootid`, `pickpocketloot`,
    `skinloot`, `PetSpellDataId`, `VehicleId`, `mingold`, `maxgold`, `AIName`, `MovementType`, `HoverHeight`,
    `HealthModifier`, `ManaModifier`, `ArmorModifier`, `ExperienceModifier`, `RacialLeader`, `movementId`,
    `RegenHealth`, `CreatureImmunitiesId`, `flags_extra`, `ScriptName`, `VerifiedBuild`
)
SELECT
    90211, `difficulty_entry_1`, `difficulty_entry_2`, `difficulty_entry_3`, `KillCredit1`, `KillCredit2`,
    'Pancratius Ward', 'Paladin Trainer', 'Trainer', 0, `minlevel`, `maxlevel`, `exp`, `faction`, 49,
    `speed_walk`, `speed_run`, `speed_swim`, `speed_flight`, `detection_range`, `rank`, `dmgschool`,
    `DamageModifier`, `BaseAttackTime`, `RangeAttackTime`, `BaseVariance`, `RangeVariance`, `unit_class`,
    `unit_flags`, `unit_flags2`, `dynamicflags`, `family`, `type`, `type_flags`, `lootid`, `pickpocketloot`,
    `skinloot`, `PetSpellDataId`, `VehicleId`, `mingold`, `maxgold`, `AIName`, `MovementType`, `HoverHeight`,
    `HealthModifier`, `ManaModifier`, `ArmorModifier`, `ExperienceModifier`, `RacialLeader`, `movementId`,
    `RegenHealth`, `CreatureImmunitiesId`, `flags_extra`, '', 0
FROM `creature_template`
WHERE `entry` = 2123;

INSERT INTO `creature_template_model`
    (`CreatureID`, `Idx`, `CreatureDisplayID`, `DisplayScale`, `Probability`, `VerifiedBuild`)
VALUES
    (90210, 0, 1583, 1, 1, 0),
    (90211, 0, 1578, 1, 1, 0);

INSERT INTO `creature_equip_template` (`CreatureID`, `ID`, `ItemID1`, `ItemID2`, `ItemID3`, `VerifiedBuild`) VALUES
    (90210, 1, 2813, 6187, 0, 0),
    (90211, 1, 1903, 0, 0, 0);

INSERT INTO `creature_default_trainer` (`CreatureId`, `TrainerId`) VALUES
    (90210, 4),
    (90211, 6);

INSERT INTO `creature_template_locale` (`entry`, `locale`, `Name`, `Title`, `VerifiedBuild`) VALUES
    (90210, 'esES', 'Abraham West', 'Instructor de paladines', 0),
    (90211, 'esES', 'Pancratius Ward', 'Instructor de paladines', 0);

-- `creature`.`id` is the authoritative entry column in the current DEV schema.
INSERT INTO `creature` (
    `guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `equipment_id`,
    `position_x`, `position_y`, `position_z`, `orientation`, `spawntimesecs`, `wander_distance`,
    `currentwaypoint`, `curhealth`, `curmana`, `MovementType`, `npcflag`, `unit_flags`, `dynamicflags`,
    `ScriptName`, `VerifiedBuild`, `CreateObject`, `Comment`
) VALUES
    (5300690, 90210, 0, 0, 0, 1, 1, 1, 2260.15, 249.694, 33.6343, 1.32611, 300, 0, 0, 1, 0, 0, 0, 0, 0,
     '', 0, 0, 'Abraham West - Forsaken Paladin Trainer'),
    (5300691, 90211, 0, 0, 0, 1, 1, 1, 1884.16, 1623.87, 94.3018, 1.62771, 300, 0, 0, 1, 0, 0, 0, 0, 0,
     '', 0, 0, 'Pancratius Ward - Forsaken Paladin Starter Trainer');

INSERT INTO `creature_addon`
    (`guid`, `path_id`, `mount`, `bytes1`, `bytes2`, `emote`, `visibilityDistanceType`, `auras`)
VALUES
    (5300690, 0, 0, 8, 0, 0, 0, NULL),
    (5300691, 0, 0, 8, 0, 0, 0, NULL);

COMMIT;
