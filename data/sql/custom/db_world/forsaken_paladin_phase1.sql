USE `acore_world`;

-- ============================================================================
-- FORSAKEN PALADIN - PHASE 1: CHARACTER CREATION FOUNDATION
-- ============================================================================
-- Enables race 5 (Undead) / class 2 (Paladin) character creation.
-- This script is idempotent and can be re-run safely.
-- ============================================================================

START TRANSACTION;

-- ============================================================================
-- 1. PLAYERCREATEINFO - Starting position
-- ============================================================================
-- Deathknell starting location (same as other Undead classes)

DELETE FROM `playercreateinfo` WHERE `race` = 5 AND `class` = 2;

INSERT INTO `playercreateinfo` (`race`, `class`, `map`, `zone`, `position_x`, `position_y`, `position_z`, `orientation`)
VALUES (5, 2, 0, 85, 1676.71, 1678.31, 121.67, 2.70526);

-- ============================================================================
-- 2. PLAYERCREATEINFO_ACTION - Starting action bar
-- ============================================================================
-- Combines Paladin abilities with Undead racial

DELETE FROM `playercreateinfo_action` WHERE `race` = 5 AND `class` = 2;

INSERT INTO `playercreateinfo_action` (`race`, `class`, `button`, `action`, `type`) VALUES
(5, 2, 0, 6603, 0),    -- Attack
(5, 2, 1, 21084, 0),   -- Seal of Righteousness
(5, 2, 2, 635, 0),     -- Holy Light (Rank 1)
(5, 2, 3, 20577, 0),   -- Cannibalize (Undead racial)
(5, 2, 10, 159, 128),  -- Refreshing Spring Water (drink)
(5, 2, 11, 4604, 128); -- Forest Mushroom Cap (food)

-- ============================================================================
-- 3. CHARSTARTOUTFIT_DBC - Starting gear
-- ============================================================================
-- Uses DB overlay to override DBC. IDs 9000-9001 are safe (outside IP range 1-346).
-- Items: Squire's Shirt (45), Squire's Boots (43), Squire's Pants (44), 
--        Hearthstone (6948), Battleworn Hammer (2361), Refreshing Spring Water (159),
--        Darnassian Bleu (2070)

DELETE FROM `charstartoutfit_dbc` WHERE `ID` IN (9000, 9001);

INSERT INTO `charstartoutfit_dbc` (
    `ID`, `RaceID`, `ClassID`, `SexID`, `OutfitID`,
    `ItemID_1`, `ItemID_2`, `ItemID_3`, `ItemID_4`, `ItemID_5`, `ItemID_6`, `ItemID_7`,
    `ItemID_8`, `ItemID_9`, `ItemID_10`, `ItemID_11`, `ItemID_12`,
    `ItemID_13`, `ItemID_14`, `ItemID_15`, `ItemID_16`, `ItemID_17`, `ItemID_18`, `ItemID_19`,
    `ItemID_20`, `ItemID_21`, `ItemID_22`, `ItemID_23`, `ItemID_24`,
    `DisplayItemID_1`, `DisplayItemID_2`, `DisplayItemID_3`, `DisplayItemID_4`, `DisplayItemID_5`,
    `DisplayItemID_6`, `DisplayItemID_7`, `DisplayItemID_8`, `DisplayItemID_9`, `DisplayItemID_10`,
    `DisplayItemID_11`, `DisplayItemID_12`,
    `DisplayItemID_13`, `DisplayItemID_14`, `DisplayItemID_15`, `DisplayItemID_16`, `DisplayItemID_17`,
    `DisplayItemID_18`, `DisplayItemID_19`, `DisplayItemID_20`, `DisplayItemID_21`, `DisplayItemID_22`,
    `DisplayItemID_23`, `DisplayItemID_24`,
    `InventoryType_1`, `InventoryType_2`, `InventoryType_3`, `InventoryType_4`, `InventoryType_5`,
    `InventoryType_6`, `InventoryType_7`, `InventoryType_8`, `InventoryType_9`, `InventoryType_10`,
    `InventoryType_11`, `InventoryType_12`,
    `InventoryType_13`, `InventoryType_14`, `InventoryType_15`, `InventoryType_16`, `InventoryType_17`,
    `InventoryType_18`, `InventoryType_19`, `InventoryType_20`, `InventoryType_21`, `InventoryType_22`,
    `InventoryType_23`, `InventoryType_24`
) VALUES
-- Male (SexID=0): Squire's Shirt, Boots, Pants, Hearthstone, Hammer, Water, Cheese
(9000, 5, 2, 0, 0, 45, 43, 44, 6948, 2361, 159, 2070, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3265, 9938, 9937, 6418, 8690, 18084, 6353, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 8, 7, 0, 17, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
-- Female (SexID=1): Same items
(9001, 5, 2, 1, 0, 45, 43, 44, 6948, 2361, 159, 2070, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3265, 9938, 9937, 6418, 8690, 18084, 6353, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 8, 7, 0, 17, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0);

COMMIT;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

SELECT 'playercreateinfo (5,2)' AS check_name, COUNT(*) AS count
FROM playercreateinfo WHERE race = 5 AND class = 2;

SELECT 'playercreateinfo_action (5,2)' AS check_name, COUNT(*) AS count
FROM playercreateinfo_action WHERE race = 5 AND class = 2;

SELECT 'charstartoutfit_dbc (5,2)' AS check_name, COUNT(*) AS count
FROM charstartoutfit_dbc WHERE RaceID = 5 AND ClassID = 2;
