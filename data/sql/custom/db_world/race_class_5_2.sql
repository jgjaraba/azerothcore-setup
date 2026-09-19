USE `acore_world`;

-- ============================================================================
-- FORSAKEN PALADIN TRAINERS
-- ============================================================================
-- 90210 = Abraham West (Full trainer, TrainerId 4, Brill)
-- 90211 = Pancratius Ward (Starter trainer, TrainerId 6, Deathknell)
--
-- Based on Dark Cleric Beryl (2129, Brill) and Dark Cleric Duesten (2123, Deathknell)
-- This script is idempotent and can be re-run safely.
-- ============================================================================

SET @FULL_ENTRY       := 90210;
SET @STARTER_ENTRY    := 90211;

SET @FULL_SOURCE      := 2129; -- Dark Cleric Beryl, Brill
SET @STARTER_SOURCE   := 2123; -- Dark Cleric Duesten, Deathknell

SET @FULL_TRAINER     := 4;
SET @STARTER_TRAINER  := 6;

START TRANSACTION;

-- ============================================================================
-- CLEAN PREVIOUS INSTALLATION
-- ============================================================================

DELETE ca FROM `creature_addon` ca
INNER JOIN `creature` c ON c.`guid` = ca.`guid`
WHERE c.`id` IN (@FULL_ENTRY, @STARTER_ENTRY);
DELETE FROM `creature` WHERE `id` IN (@FULL_ENTRY, @STARTER_ENTRY);
DELETE FROM `creature_default_trainer` WHERE `CreatureId` IN (@FULL_ENTRY, @STARTER_ENTRY);
DELETE FROM `creature_template_locale` WHERE `entry` IN (@FULL_ENTRY, @STARTER_ENTRY);
DELETE FROM `creature_equip_template` WHERE `CreatureID` IN (@FULL_ENTRY, @STARTER_ENTRY);
DELETE FROM `creature_template_model` WHERE `CreatureID` IN (@FULL_ENTRY, @STARTER_ENTRY);
DELETE FROM `creature_template` WHERE `entry` IN (@FULL_ENTRY, @STARTER_ENTRY);

-- ============================================================================
-- 1. FULL FORSAKEN PALADIN TRAINER (Abraham West, Brill)
-- ============================================================================

DROP TEMPORARY TABLE IF EXISTS tmp_paladin_full;
CREATE TEMPORARY TABLE tmp_paladin_full LIKE `creature_template`;

INSERT INTO tmp_paladin_full SELECT * FROM `creature_template` WHERE `entry` = @FULL_SOURCE;

UPDATE tmp_paladin_full SET
    `entry`          = @FULL_ENTRY,
    `name`           = 'Abraham West',
    `subname`        = 'Paladin Trainer',
    `IconName`       = 'Trainer',
    `gossip_menu_id` = 0,
    `npcflag`        = 49,
    `ScriptName`     = '',
    `VerifiedBuild`  = 0;

INSERT INTO `creature_template` SELECT * FROM tmp_paladin_full;
DROP TEMPORARY TABLE tmp_paladin_full;

-- Model
INSERT INTO `creature_template_model` (`CreatureID`, `Idx`, `CreatureDisplayID`, `DisplayScale`, `Probability`, `VerifiedBuild`)
SELECT @FULL_ENTRY, `Idx`, `CreatureDisplayID`, `DisplayScale`, `Probability`, 0
FROM `creature_template_model` WHERE `CreatureID` = @FULL_SOURCE;

-- Equipment (from Brother Wilhelm 23779)
INSERT INTO `creature_equip_template` (`CreatureID`, `ID`, `ItemID1`, `ItemID2`, `ItemID3`, `VerifiedBuild`)
SELECT @FULL_ENTRY, `ID`, `ItemID1`, `ItemID2`, `ItemID3`, 0
FROM `creature_equip_template` WHERE `CreatureID` = 23779;

-- Trainer association
INSERT INTO `creature_default_trainer` (`CreatureId`, `TrainerId`) VALUES (@FULL_ENTRY, @FULL_TRAINER);

-- ============================================================================
-- 2. STARTER FORSAKEN PALADIN TRAINER (Pancratius Ward, Deathknell)
-- ============================================================================

DROP TEMPORARY TABLE IF EXISTS tmp_paladin_starter;
CREATE TEMPORARY TABLE tmp_paladin_starter LIKE `creature_template`;

INSERT INTO tmp_paladin_starter SELECT * FROM `creature_template` WHERE `entry` = @STARTER_SOURCE;

UPDATE tmp_paladin_starter SET
    `entry`          = @STARTER_ENTRY,
    `name`           = 'Pancratius Ward',
    `subname`        = 'Paladin Trainer',
    `IconName`       = 'Trainer',
    `gossip_menu_id` = 0,
    `npcflag`        = 49,
    `ScriptName`     = '',
    `VerifiedBuild`  = 0;

INSERT INTO `creature_template` SELECT * FROM tmp_paladin_starter;
DROP TEMPORARY TABLE tmp_paladin_starter;

-- Model
INSERT INTO `creature_template_model` (`CreatureID`, `Idx`, `CreatureDisplayID`, `DisplayScale`, `Probability`, `VerifiedBuild`)
SELECT @STARTER_ENTRY, `Idx`, `CreatureDisplayID`, `DisplayScale`, `Probability`, 0
FROM `creature_template_model` WHERE `CreatureID` = @STARTER_SOURCE;

-- Equipment (from source)
INSERT INTO `creature_equip_template` (`CreatureID`, `ID`, `ItemID1`, `ItemID2`, `ItemID3`, `VerifiedBuild`)
SELECT @STARTER_ENTRY, `ID`, `ItemID1`, `ItemID2`, `ItemID3`, 0
FROM `creature_equip_template` WHERE `CreatureID` = @STARTER_SOURCE;

-- Trainer association
INSERT INTO `creature_default_trainer` (`CreatureId`, `TrainerId`) VALUES (@STARTER_ENTRY, @STARTER_TRAINER);

-- ============================================================================
-- 3. esES LOCALIZATION
-- ============================================================================

INSERT INTO `creature_template_locale` (`entry`, `locale`, `Name`, `Title`, `VerifiedBuild`) VALUES
(@FULL_ENTRY, 'esES', 'Abraham West', 'Instructor de paladines', 0),
(@STARTER_ENTRY, 'esES', 'Pancratius Ward', 'Instructor de paladines', 0);

COMMIT;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

SELECT 'creature_template trainers' AS check_name, COUNT(*) AS count
FROM `creature_template` WHERE `entry` IN (@FULL_ENTRY, @STARTER_ENTRY);

SELECT 'creature_default_trainer' AS check_name, COUNT(*) AS count
FROM `creature_default_trainer` WHERE `CreatureId` IN (@FULL_ENTRY, @STARTER_ENTRY);

SELECT c.guid, c.id, ct.name, ct.subname, cdt.TrainerId, c.map, c.position_x, c.position_y, c.position_z
FROM `creature` c
JOIN `creature_template` ct ON c.id = ct.entry
JOIN `creature_default_trainer` cdt ON c.id = cdt.CreatureId
WHERE c.id IN (@FULL_ENTRY, @STARTER_ENTRY);
