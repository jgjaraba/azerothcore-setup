USE `acore_world`;

-- ============================================================================
-- FORSAKEN PALADIN PHASE 1.1 - STARTING STATE & TRAINER POLISH
-- ============================================================================
-- Fixes:
-- 1. Starting food mismatch (Darnassian Bleu -> Forest Mushroom Cap)
-- 2. Trainer repositioning (avoid overlap with Priest trainers)
-- 3. Trainer appearance (distinct Forsaken Paladin models)
--
-- This script is idempotent and can be re-run safely.
-- ============================================================================

START TRANSACTION;

-- ============================================================================
-- 1. FIX STARTING FOOD MISMATCH
-- ============================================================================
-- Change starting outfit from Darnassian Bleu (2070) to Forest Mushroom Cap (4604)
-- to match the action bar and be consistent with other Forsaken classes.

DELETE FROM `charstartoutfit_dbc` WHERE `ID` IN (9000, 9001);

INSERT INTO `charstartoutfit_dbc` (
    `ID`, `RaceID`, `ClassID`, `SexID`, `OutfitID`,
    `ItemID_1`, `ItemID_2`, `ItemID_3`, `ItemID_4`, `ItemID_5`, `ItemID_6`, `ItemID_7`,
    `ItemID_8`, `ItemID_9`, `ItemID_10`, `ItemID_11`, `ItemID_12`, `ItemID_13`, `ItemID_14`,
    `ItemID_15`, `ItemID_16`, `ItemID_17`, `ItemID_18`, `ItemID_19`, `ItemID_20`, `ItemID_21`,
    `ItemID_22`, `ItemID_23`, `ItemID_24`,
    `DisplayItemID_1`, `DisplayItemID_2`, `DisplayItemID_3`, `DisplayItemID_4`, `DisplayItemID_5`,
    `DisplayItemID_6`, `DisplayItemID_7`, `DisplayItemID_8`, `DisplayItemID_9`, `DisplayItemID_10`,
    `DisplayItemID_11`, `DisplayItemID_12`, `DisplayItemID_13`, `DisplayItemID_14`, `DisplayItemID_15`,
    `DisplayItemID_16`, `DisplayItemID_17`, `DisplayItemID_18`, `DisplayItemID_19`, `DisplayItemID_20`,
    `DisplayItemID_21`, `DisplayItemID_22`, `DisplayItemID_23`, `DisplayItemID_24`,
    `InventoryType_1`, `InventoryType_2`, `InventoryType_3`, `InventoryType_4`, `InventoryType_5`,
    `InventoryType_6`, `InventoryType_7`, `InventoryType_8`, `InventoryType_9`, `InventoryType_10`,
    `InventoryType_11`, `InventoryType_12`, `InventoryType_13`, `InventoryType_14`, `InventoryType_15`,
    `InventoryType_16`, `InventoryType_17`, `InventoryType_18`, `InventoryType_19`, `InventoryType_20`,
    `InventoryType_21`, `InventoryType_22`, `InventoryType_23`, `InventoryType_24`
) VALUES
-- Male (SexID=0): Squire's Shirt, Boots, Pants, Hearthstone, Hammer, Water, Forest Mushroom Cap
(9000, 5, 2, 0, 0, 45, 43, 44, 6948, 2361, 159, 4604, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3265, 9938, 9937, 6418, 8690, 18084, 18084, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 8, 7, 0, 17, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
-- Female (SexID=1): Same items
(9001, 5, 2, 1, 0, 45, 43, 44, 6948, 2361, 159, 4604, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3265, 9938, 9937, 6418, 8690, 18084, 18084, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 8, 7, 0, 17, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0);

-- ============================================================================
-- 2. TRAINER SPAWNS
-- ============================================================================

-- `race_class_5_2.sql` owns templates and trainer mappings. This script is the
-- sole source of truth for the final trainer spawn state.
-- Remove per-spawn addon rows before their creatures to avoid orphaned addons.
DELETE ca FROM `creature_addon` ca
INNER JOIN `creature` c ON c.`guid` = ca.`guid`
WHERE c.`id` IN (90210, 90211);

-- Replace existing spawns with their stable, live-captured GUIDs.
DELETE FROM `creature` WHERE `id` IN (90210, 90211);

-- Update models and equipment
DELETE FROM `creature_template_model` WHERE `CreatureID` IN (90210, 90211);
DELETE FROM `creature_equip_template` WHERE `CreatureID` IN (90210, 90211);

-- Pancratius Ward (90211) - Deathknell starter trainer
-- New location: Near the graveyard area, separate from Priest trainer
-- Model: Display 1578 (Dannal Stern) - humble but martial appearance
INSERT INTO `creature_template_model` (`CreatureID`, `Idx`, `CreatureDisplayID`, `DisplayScale`, `Probability`, `VerifiedBuild`)
VALUES (90211, 0, 1578, 1, 1, 0);

-- Equipment: Basic mace (appropriate for Paladin starter)
INSERT INTO `creature_equip_template` (`CreatureID`, `ID`, `ItemID1`, `ItemID2`, `ItemID3`, `VerifiedBuild`)
VALUES (90211, 1, 1903, 0, 0, 0);  -- Monster - Mace, Basic Metal Hammer

-- Final live-captured spawn in Deathknell.
INSERT INTO `creature` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `equipment_id`,
    `position_x`, `position_y`, `position_z`, `orientation`, `spawntimesecs`, `wander_distance`, `MovementType`,
    `npcflag`, `unit_flags`, `dynamicflags`, `VerifiedBuild`, `CreateObject`, `Comment`)
VALUES (5300690, 90211, 0, 0, 0, 1, 1, 1,
    1884.16, 1623.87, 94.3018, 1.62771,
    300, 0, 0, 0, 0, 0, 0, 0, 'Pancratius Ward - Forsaken Paladin Starter Trainer');

-- Abraham West (90210) - Brill full trainer
-- New location: Near the chapel ruins, separate from Dark Cleric Beryl
-- Model: Display 1583 (Executor Arren) - imposing, experienced warrior
INSERT INTO `creature_template_model` (`CreatureID`, `Idx`, `CreatureDisplayID`, `DisplayScale`, `Probability`, `VerifiedBuild`)
VALUES (90210, 0, 1583, 1, 1, 0);

-- Equipment: Better mace and shield (appropriate for full Paladin trainer)
INSERT INTO `creature_equip_template` (`CreatureID`, `ID`, `ItemID1`, `ItemID2`, `ItemID3`, `VerifiedBuild`)
VALUES (90210, 1, 2813, 6187, 0, 0);  -- Monster - Mace, Standard Basic + Dwarven Defender (shield)

-- Final live-captured spawn in Brill.
INSERT INTO `creature` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `equipment_id`,
    `position_x`, `position_y`, `position_z`, `orientation`, `spawntimesecs`, `wander_distance`, `MovementType`,
    `npcflag`, `unit_flags`, `dynamicflags`, `VerifiedBuild`, `CreateObject`, `Comment`)
VALUES (5300691, 90210, 0, 0, 0, 1, 1, 1,
    2260.15, 249.694, 33.6343, 1.32611,
    300, 0, 0, 0, 0, 0, 0, 0, 'Abraham West - Forsaken Paladin Trainer');

-- ============================================================================
-- 3. KNEELING STATE
-- ============================================================================
-- `bytes1` low byte is UNIT_STAND_STATE_KNEEL (8). creature_addon is scoped
-- to these individual spawns, unlike creature_template_addon.
DELETE FROM `creature_addon` WHERE `guid` IN (5300690, 5300691);

INSERT INTO `creature_addon` (`guid`, `path_id`, `mount`, `bytes1`, `bytes2`, `emote`, `visibilityDistanceType`, `auras`)
VALUES
(5300690, 0, 0, 8, 0, 0, 0, NULL),
(5300691, 0, 0, 8, 0, 0, 0, NULL);

COMMIT;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

SELECT 'charstartoutfit_dbc (5,2)' AS check_name, COUNT(*) AS count
FROM `charstartoutfit_dbc` WHERE `RaceID` = 5 AND `ClassID` = 2;

SELECT 'creature spawns' AS check_name, COUNT(*) AS count
FROM `creature` WHERE `id` IN (90210, 90211);

SELECT 'creature_template_model' AS check_name, COUNT(*) AS count
FROM `creature_template_model` WHERE `CreatureID` IN (90210, 90211);

SELECT 'creature_equip_template' AS check_name, COUNT(*) AS count
FROM `creature_equip_template` WHERE `CreatureID` IN (90210, 90211);

-- Verify the final live-captured spawn state.
SELECT 
    c.guid,
    c.id,
    ct.name,
    c.position_x,
    c.position_y,
    c.position_z,
    c.orientation,
    c.phaseMask,
    c.MovementType,
    c.wander_distance,
    ctm.CreatureDisplayID
FROM `creature` c
JOIN `creature_template` ct ON c.id = ct.entry
JOIN `creature_template_model` ctm ON c.id = ctm.CreatureID
WHERE c.id IN (90210, 90211);

-- Verify starting food matches action bar
SELECT 
    'Starting outfit food' AS item_type,
    it.name AS item_name,
    it.entry AS item_id
FROM `charstartoutfit_dbc` cs
JOIN `item_template` it ON cs.ItemID_7 = it.entry
WHERE cs.RaceID = 5 AND cs.ClassID = 2 AND cs.SexID = 0
UNION ALL
SELECT 
    'Action bar food' AS item_type,
    it.name AS item_name,
    pca.action AS item_id
FROM `playercreateinfo_action` pca
JOIN `item_template` it ON pca.action = it.entry
WHERE pca.race = 5 AND pca.class = 2 AND pca.button = 11;

-- Verify kneeling state
SELECT 
    c.id,
    ct.name,
    ca.bytes1,
    CASE 
        WHEN ca.bytes1 & 255 = 8 THEN 'KNEELING'
        ELSE 'NOT KNEELING'
    END AS state
FROM `creature` c
JOIN `creature_template` ct ON c.id = ct.entry
LEFT JOIN `creature_addon` ca ON c.guid = ca.guid
WHERE c.id IN (90210, 90211);
