USE `acore_world`;

-- Orc Mage (race 2 / class 8) and Troll Warlock (race 8 / class 9)
-- creation data, plus extension of the existing race-specific class quests.
-- No new quests are created; existing quest IDs are reused.

START TRANSACTION;

-- ---------------------------------------------------------------------------
-- Character creation positions: same Valley of Trials spawn used by every
-- other Orc and Troll combination on this realm.
-- ---------------------------------------------------------------------------
DELETE FROM `playercreateinfo`
WHERE (`race` = 2 AND `class` = 8)
   OR (`race` = 8 AND `class` = 9);

INSERT INTO `playercreateinfo`
    (`race`, `class`, `map`, `zone`, `position_x`, `position_y`, `position_z`, `orientation`)
VALUES
    (2, 8, 1, 14, -618.518, -4251.67, 38.718, 0),
    (8, 9, 1, 14, -618.518, -4251.67, 38.718, 0);

-- ---------------------------------------------------------------------------
-- Initial action bars: mirror the existing same-race caster layout and swap
-- only the racial ability.
--   Orc Mage  -> Troll Mage actions with Orc Blood Fury (33702).
--   Troll Warlock -> Orc Warlock actions with Troll Berserking (168).
-- ---------------------------------------------------------------------------
DELETE FROM `playercreateinfo_action`
WHERE (`race` = 2 AND `class` = 8)
   OR (`race` = 8 AND `class` = 9);

INSERT INTO `playercreateinfo_action` (`race`, `class`, `button`, `action`, `type`)
VALUES
    -- Orc Mage
    (2, 8, 0, 6603, 0),
    (2, 8, 1, 133, 0),
    (2, 8, 2, 33702, 0),
    (2, 8, 10, 159, 128),
    (2, 8, 11, 117, 128),
    -- Troll Warlock
    (8, 9, 0, 6603, 0),
    (8, 9, 1, 686, 0),
    (8, 9, 2, 687, 0),
    (8, 9, 3, 168, 0),
    (8, 9, 10, 159, 128),
    (8, 9, 11, 117, 128);

-- ---------------------------------------------------------------------------
-- Server-side CharStartOutfit overlay.  The tracked client patch already
-- contains the matching DBC rows, but the server DBC file used by this DEV
-- install is the original 126-record set and lacks these combos.  Adding the
-- rows to `charstartoutfit_dbc` lets worldserver supply the start outfit via
-- the standard DB overlay mechanism.
--
-- IDs 9002/9003 and 9004/9005 are new project-owned entries.
-- Orc Mage outfit is cloned from the existing Troll Mage `charstartoutfit_dbc` rows.
-- Troll Warlock outfit is cloned from the existing Orc Warlock `charstartoutfit_dbc` rows.
-- ---------------------------------------------------------------------------
DELETE FROM `charstartoutfit_dbc`
WHERE `ID` IN (9002, 9003, 9004, 9005);

-- Clone the existing same-gender source outfits field-for-field, changing only
-- the project-owned ID and the race/class identifiers.
INSERT INTO `charstartoutfit_dbc`
SELECT 9002, 2, 8, `SexID`, `OutfitID`,
       `ItemID_1`, `ItemID_2`, `ItemID_3`, `ItemID_4`, `ItemID_5`, `ItemID_6`, `ItemID_7`,
       `ItemID_8`, `ItemID_9`, `ItemID_10`, `ItemID_11`, `ItemID_12`, `ItemID_13`, `ItemID_14`,
       `ItemID_15`, `ItemID_16`, `ItemID_17`, `ItemID_18`, `ItemID_19`, `ItemID_20`,
       `ItemID_21`, `ItemID_22`, `ItemID_23`, `ItemID_24`,
       `DisplayItemID_1`, `DisplayItemID_2`, `DisplayItemID_3`, `DisplayItemID_4`,
       `DisplayItemID_5`, `DisplayItemID_6`, `DisplayItemID_7`, `DisplayItemID_8`,
       `DisplayItemID_9`, `DisplayItemID_10`, `DisplayItemID_11`, `DisplayItemID_12`,
       `DisplayItemID_13`, `DisplayItemID_14`, `DisplayItemID_15`, `DisplayItemID_16`,
       `DisplayItemID_17`, `DisplayItemID_18`, `DisplayItemID_19`, `DisplayItemID_20`,
       `DisplayItemID_21`, `DisplayItemID_22`, `DisplayItemID_23`, `DisplayItemID_24`,
       `InventoryType_1`, `InventoryType_2`, `InventoryType_3`, `InventoryType_4`,
       `InventoryType_5`, `InventoryType_6`, `InventoryType_7`, `InventoryType_8`,
       `InventoryType_9`, `InventoryType_10`, `InventoryType_11`, `InventoryType_12`,
       `InventoryType_13`, `InventoryType_14`, `InventoryType_15`, `InventoryType_16`,
       `InventoryType_17`, `InventoryType_18`, `InventoryType_19`, `InventoryType_20`,
       `InventoryType_21`, `InventoryType_22`, `InventoryType_23`, `InventoryType_24`
FROM `charstartoutfit_dbc`
WHERE `ID` = 317;

INSERT INTO `charstartoutfit_dbc`
SELECT 9003, 2, 8, `SexID`, `OutfitID`,
       `ItemID_1`, `ItemID_2`, `ItemID_3`, `ItemID_4`, `ItemID_5`, `ItemID_6`, `ItemID_7`,
       `ItemID_8`, `ItemID_9`, `ItemID_10`, `ItemID_11`, `ItemID_12`, `ItemID_13`, `ItemID_14`,
       `ItemID_15`, `ItemID_16`, `ItemID_17`, `ItemID_18`, `ItemID_19`, `ItemID_20`,
       `ItemID_21`, `ItemID_22`, `ItemID_23`, `ItemID_24`,
       `DisplayItemID_1`, `DisplayItemID_2`, `DisplayItemID_3`, `DisplayItemID_4`,
       `DisplayItemID_5`, `DisplayItemID_6`, `DisplayItemID_7`, `DisplayItemID_8`,
       `DisplayItemID_9`, `DisplayItemID_10`, `DisplayItemID_11`, `DisplayItemID_12`,
       `DisplayItemID_13`, `DisplayItemID_14`, `DisplayItemID_15`, `DisplayItemID_16`,
       `DisplayItemID_17`, `DisplayItemID_18`, `DisplayItemID_19`, `DisplayItemID_20`,
       `DisplayItemID_21`, `DisplayItemID_22`, `DisplayItemID_23`, `DisplayItemID_24`,
       `InventoryType_1`, `InventoryType_2`, `InventoryType_3`, `InventoryType_4`,
       `InventoryType_5`, `InventoryType_6`, `InventoryType_7`, `InventoryType_8`,
       `InventoryType_9`, `InventoryType_10`, `InventoryType_11`, `InventoryType_12`,
       `InventoryType_13`, `InventoryType_14`, `InventoryType_15`, `InventoryType_16`,
       `InventoryType_17`, `InventoryType_18`, `InventoryType_19`, `InventoryType_20`,
       `InventoryType_21`, `InventoryType_22`, `InventoryType_23`, `InventoryType_24`
FROM `charstartoutfit_dbc`
WHERE `ID` = 318;

INSERT INTO `charstartoutfit_dbc`
SELECT 9004, 8, 9, `SexID`, `OutfitID`,
       `ItemID_1`, `ItemID_2`, `ItemID_3`, `ItemID_4`, `ItemID_5`, `ItemID_6`, `ItemID_7`,
       `ItemID_8`, `ItemID_9`, `ItemID_10`, `ItemID_11`, `ItemID_12`, `ItemID_13`, `ItemID_14`,
       `ItemID_15`, `ItemID_16`, `ItemID_17`, `ItemID_18`, `ItemID_19`, `ItemID_20`,
       `ItemID_21`, `ItemID_22`, `ItemID_23`, `ItemID_24`,
       `DisplayItemID_1`, `DisplayItemID_2`, `DisplayItemID_3`, `DisplayItemID_4`,
       `DisplayItemID_5`, `DisplayItemID_6`, `DisplayItemID_7`, `DisplayItemID_8`,
       `DisplayItemID_9`, `DisplayItemID_10`, `DisplayItemID_11`, `DisplayItemID_12`,
       `DisplayItemID_13`, `DisplayItemID_14`, `DisplayItemID_15`, `DisplayItemID_16`,
       `DisplayItemID_17`, `DisplayItemID_18`, `DisplayItemID_19`, `DisplayItemID_20`,
       `DisplayItemID_21`, `DisplayItemID_22`, `DisplayItemID_23`, `DisplayItemID_24`,
       `InventoryType_1`, `InventoryType_2`, `InventoryType_3`, `InventoryType_4`,
       `InventoryType_5`, `InventoryType_6`, `InventoryType_7`, `InventoryType_8`,
       `InventoryType_9`, `InventoryType_10`, `InventoryType_11`, `InventoryType_12`,
       `InventoryType_13`, `InventoryType_14`, `InventoryType_15`, `InventoryType_16`,
       `InventoryType_17`, `InventoryType_18`, `InventoryType_19`, `InventoryType_20`,
       `InventoryType_21`, `InventoryType_22`, `InventoryType_23`, `InventoryType_24`
FROM `charstartoutfit_dbc`
WHERE `ID` = 20;

INSERT INTO `charstartoutfit_dbc`
SELECT 9005, 8, 9, `SexID`, `OutfitID`,
       `ItemID_1`, `ItemID_2`, `ItemID_3`, `ItemID_4`, `ItemID_5`, `ItemID_6`, `ItemID_7`,
       `ItemID_8`, `ItemID_9`, `ItemID_10`, `ItemID_11`, `ItemID_12`, `ItemID_13`, `ItemID_14`,
       `ItemID_15`, `ItemID_16`, `ItemID_17`, `ItemID_18`, `ItemID_19`, `ItemID_20`,
       `ItemID_21`, `ItemID_22`, `ItemID_23`, `ItemID_24`,
       `DisplayItemID_1`, `DisplayItemID_2`, `DisplayItemID_3`, `DisplayItemID_4`,
       `DisplayItemID_5`, `DisplayItemID_6`, `DisplayItemID_7`, `DisplayItemID_8`,
       `DisplayItemID_9`, `DisplayItemID_10`, `DisplayItemID_11`, `DisplayItemID_12`,
       `DisplayItemID_13`, `DisplayItemID_14`, `DisplayItemID_15`, `DisplayItemID_16`,
       `DisplayItemID_17`, `DisplayItemID_18`, `DisplayItemID_19`, `DisplayItemID_20`,
       `DisplayItemID_21`, `DisplayItemID_22`, `DisplayItemID_23`, `DisplayItemID_24`,
       `InventoryType_1`, `InventoryType_2`, `InventoryType_3`, `InventoryType_4`,
       `InventoryType_5`, `InventoryType_6`, `InventoryType_7`, `InventoryType_8`,
       `InventoryType_9`, `InventoryType_10`, `InventoryType_11`, `InventoryType_12`,
       `InventoryType_13`, `InventoryType_14`, `InventoryType_15`, `InventoryType_16`,
       `InventoryType_17`, `InventoryType_18`, `InventoryType_19`, `InventoryType_20`,
       `InventoryType_21`, `InventoryType_22`, `InventoryType_23`, `InventoryType_24`
FROM `charstartoutfit_dbc`
WHERE `ID` = 46;

-- ---------------------------------------------------------------------------
-- Extend existing race-specific class quests to the new combinations.
--   3086 Glyphic Tablet          (Troll Mage) -> also available to Orc Mage
--   3090 Tainted Parchment       (Orc Warlock starter) -> also Troll Warlock
--   1506 Gan'rul's Summons       (Orc Warlock) -> also Troll Warlock
--   1501 Creature of the Void    (Orc Warlock) -> also Troll Warlock
--   1504 The Binding             (Orc Warlock) -> also Troll Warlock
--   10790 Return to Gan'rul Bloodeye (Orc Warlock) -> also Troll Warlock
--
-- Bit masks:
--   Orc race    = 1 << (2 - 1) = 2
--   Troll race  = 1 << (8 - 1) = 128
--   Mage class  = 1 << (8 - 1) = 128
--   Warlock class = 1 << (9 - 1) = 256
-- ---------------------------------------------------------------------------
UPDATE `quest_template`
SET `AllowableRaces` = `AllowableRaces` | 2
WHERE `ID` = 3086
  AND (`AllowableRaces` & 2) = 0;

UPDATE `quest_template`
SET `AllowableRaces` = `AllowableRaces` | 128
WHERE `ID` IN (3090, 1506, 1501, 1504, 10790)
  AND (`AllowableRaces` & 128) = 0;

COMMIT;
