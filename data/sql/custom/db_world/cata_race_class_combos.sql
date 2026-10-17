-- Cataclysm race/class combinations: Blood Elf Warrior, Night Elf Mage, Draenei Rogue,
-- Tauren Priest, and Gnome Hunter.
--
-- Provides playercreateinfo spawn rows, action bars, charstartoutfit_dbc overlays,
-- and extends the Dwarf Hunter pet-taming quest chain to Gnomes.

SET NAMES utf8mb4;
USE acore_world;

START TRANSACTION;

-- -------------------------------------------------------------------------
-- Cleanup owned rows for idempotency
-- -------------------------------------------------------------------------

DELETE FROM `playercreateinfo` WHERE (`race`, `class`) IN (
    (10, 1), -- Blood Elf Warrior
    (4, 8),  -- Night Elf Mage
    (11, 4), -- Draenei Rogue
    (6, 5),  -- Tauren Priest
    (7, 3)   -- Gnome Hunter
);

DELETE FROM `playercreateinfo_action` WHERE (`race`, `class`) IN (
    (10, 1),
    (4, 8),
    (11, 4),
    (6, 5),
    (7, 3)
);

DELETE FROM `charstartoutfit_dbc` WHERE `ID` BETWEEN 9006 AND 9015;

DELETE FROM `playercreateinfo_skills` WHERE (`raceMask`, `classMask`, `skill`) IN (
    (64,  4,  44), -- Gnome Hunter - Axes
    (64,  4,  46), -- Gnome Hunter - Guns
    (64,  4, 172), -- Gnome Hunter - Two-Handed Axes
    (512, 1,  55), -- Blood Elf Warrior - Two-Handed Swords
    (32,  16, 136) -- Tauren Priest - Staves
);

DELETE FROM `skillraceclassinfo_dbc` WHERE `ID` IN (200000, 200001);

-- -------------------------------------------------------------------------
-- Spawn positions
-- -------------------------------------------------------------------------

INSERT INTO `playercreateinfo` (`race`, `class`, `map`, `zone`, `position_x`, `position_y`, `position_z`, `orientation`) VALUES
(10, 1, 530, 3431, 10349.6, -6357.29, 33.4026, 5.31605), -- Blood Elf Warrior (Sunstrider Isle)
(4, 8, 1, 141, 10311.3, 832.463, 1326.41, 5.69632),      -- Night Elf Mage (Shadowglen)
(11, 4, 530, 3526, -3961.64, -13931.2, 100.615, 2.08364), -- Draenei Rogue (Ammen Vale)
(6, 5, 1, 215, -2917.58, -257.98, 52.9968, 0),            -- Tauren Priest (Camp Narache)
(7, 3, 0, 1, -6240.32, 331.033, 382.758, 0);              -- Gnome Hunter (Dun Morogh)

-- -------------------------------------------------------------------------
-- Action bars
-- -------------------------------------------------------------------------

INSERT INTO `playercreateinfo_action` (`race`, `class`, `button`, `action`, `type`) VALUES
-- Blood Elf Warrior
(10, 1, 72, 6603, 0),
(10, 1, 73, 78, 0),
(10, 1, 74, 28730, 0),   -- Arcane Torrent
-- Night Elf Mage
(4, 8, 0, 6603, 0),
(4, 8, 1, 133, 0),
(4, 8, 2, 168, 0),
-- Draenei Rogue
(11, 4, 0, 6603, 0),
(11, 4, 1, 1752, 0),
(11, 4, 2, 2098, 0),
(11, 4, 3, 2764, 0),
(11, 4, 4, 28880, 0),   -- Gift of the Naaru
-- Tauren Priest
(6, 5, 0, 6603, 0),
(6, 5, 1, 585, 0),
(6, 5, 2, 2050, 0),
(6, 5, 3, 20549, 0),    -- War Stomp
-- Gnome Hunter
(7, 3, 0, 6603, 0),
(7, 3, 1, 2973, 0),
(7, 3, 2, 75, 0),
(7, 3, 3, 20589, 0);    -- Escape Artist

-- -------------------------------------------------------------------------
-- Weapon proficiency availability
--
-- The base server DBC lacks SkillRaceClassInfo entries for Gnome Hunters to
-- use guns/axes, and the playercreateinfo_skills table has no starting rows
-- for the weapon skills used by the new combos. Without these the starting
-- weapons end up in the bag instead of being equipped.
-- -------------------------------------------------------------------------

-- SkillRaceClassInfo overlays (IDs 200000-200001 were verified free).
INSERT INTO `skillraceclassinfo_dbc` (`ID`, `SkillID`, `RaceMask`, `ClassMask`, `Flags`, `MinLevel`, `SkillTierID`, `SkillCostIndex`) VALUES
(200000, 46, 64, 4, 128, 0, 0, 0), -- Gnome Hunter - Guns
(200001, 44, 64, 4, 128, 0, 0, 0); -- Gnome Hunter - Axes

INSERT INTO `playercreateinfo_skills` (`raceMask`, `classMask`, `skill`, `rank`, `comment`) VALUES
(64,  4,  46, 0, 'Gnome Hunter - Guns'),
(64,  4,  44, 0, 'Gnome Hunter - Axes'),
(64,  4, 172, 0, 'Gnome Hunter - Two-Handed Axes'),
(512, 1,  55, 0, 'Blood Elf Warrior - Two-Handed Swords'),
(32,  16, 136, 0, 'Tauren Priest - Staves');

-- -------------------------------------------------------------------------
-- Start outfit overlays (imported from the tracked client CharStartOutfit.dbc)
-- Outfit IDs 9006-9015 were verified free before this file was written.
-- -------------------------------------------------------------------------

-- Auto-generated charstartoutfit_dbc inserts from project/client CharStartOutfit.dbc

-- Blood Elf Warrior male (source DBC ID 161)
INSERT INTO `charstartoutfit_dbc` (`ID`, `RaceID`, `ClassID`, `SexID`, `OutfitID`, `ItemID_1`, `ItemID_2`, `ItemID_3`, `ItemID_4`, `ItemID_5`, `ItemID_6`, `ItemID_7`, `ItemID_8`, `ItemID_9`, `ItemID_10`, `ItemID_11`, `ItemID_12`, `ItemID_13`, `ItemID_14`, `ItemID_15`, `ItemID_16`, `ItemID_17`, `ItemID_18`, `ItemID_19`, `ItemID_20`, `ItemID_21`, `ItemID_22`, `ItemID_23`, `ItemID_24`, `DisplayItemID_1`, `DisplayItemID_2`, `DisplayItemID_3`, `DisplayItemID_4`, `DisplayItemID_5`, `DisplayItemID_6`, `DisplayItemID_7`, `DisplayItemID_8`, `DisplayItemID_9`, `DisplayItemID_10`, `DisplayItemID_11`, `DisplayItemID_12`, `DisplayItemID_13`, `DisplayItemID_14`, `DisplayItemID_15`, `DisplayItemID_16`, `DisplayItemID_17`, `DisplayItemID_18`, `DisplayItemID_19`, `DisplayItemID_20`, `DisplayItemID_21`, `DisplayItemID_22`, `DisplayItemID_23`, `DisplayItemID_24`, `InventoryType_1`, `InventoryType_2`, `InventoryType_3`, `InventoryType_4`, `InventoryType_5`, `InventoryType_6`, `InventoryType_7`, `InventoryType_8`, `InventoryType_9`, `InventoryType_10`, `InventoryType_11`, `InventoryType_12`, `InventoryType_13`, `InventoryType_14`, `InventoryType_15`, `InventoryType_16`, `InventoryType_17`, `InventoryType_18`, `InventoryType_19`, `InventoryType_20`, `InventoryType_21`, `InventoryType_22`, `InventoryType_23`, `InventoryType_24`) VALUES (9006, 10, 1, 0, 0, 0, 0, 0, 24143, 0, 0, 24145, 24146, 0, 0, 0, 0, 0, 0, 23346, 0, 0, 0, 0, 0, 0, 0, 0, 6948, 0, 0, 0, 36789, 0, 0, 36790, 36793, 0, 0, 0, 0, 0, 0, 2380, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 16, 21, 22, 15, 17, 14, 11, 11, 18, 18, 18, 18, 0, 0);
-- Blood Elf Warrior female (source DBC ID 162)
INSERT INTO `charstartoutfit_dbc` (`ID`, `RaceID`, `ClassID`, `SexID`, `OutfitID`, `ItemID_1`, `ItemID_2`, `ItemID_3`, `ItemID_4`, `ItemID_5`, `ItemID_6`, `ItemID_7`, `ItemID_8`, `ItemID_9`, `ItemID_10`, `ItemID_11`, `ItemID_12`, `ItemID_13`, `ItemID_14`, `ItemID_15`, `ItemID_16`, `ItemID_17`, `ItemID_18`, `ItemID_19`, `ItemID_20`, `ItemID_21`, `ItemID_22`, `ItemID_23`, `ItemID_24`, `DisplayItemID_1`, `DisplayItemID_2`, `DisplayItemID_3`, `DisplayItemID_4`, `DisplayItemID_5`, `DisplayItemID_6`, `DisplayItemID_7`, `DisplayItemID_8`, `DisplayItemID_9`, `DisplayItemID_10`, `DisplayItemID_11`, `DisplayItemID_12`, `DisplayItemID_13`, `DisplayItemID_14`, `DisplayItemID_15`, `DisplayItemID_16`, `DisplayItemID_17`, `DisplayItemID_18`, `DisplayItemID_19`, `DisplayItemID_20`, `DisplayItemID_21`, `DisplayItemID_22`, `DisplayItemID_23`, `DisplayItemID_24`, `InventoryType_1`, `InventoryType_2`, `InventoryType_3`, `InventoryType_4`, `InventoryType_5`, `InventoryType_6`, `InventoryType_7`, `InventoryType_8`, `InventoryType_9`, `InventoryType_10`, `InventoryType_11`, `InventoryType_12`, `InventoryType_13`, `InventoryType_14`, `InventoryType_15`, `InventoryType_16`, `InventoryType_17`, `InventoryType_18`, `InventoryType_19`, `InventoryType_20`, `InventoryType_21`, `InventoryType_22`, `InventoryType_23`, `InventoryType_24`) VALUES (9007, 10, 1, 1, 0, 0, 0, 0, 24143, 0, 0, 24145, 24146, 0, 0, 0, 0, 0, 0, 23346, 0, 0, 0, 0, 0, 0, 0, 0, 6948, 0, 0, 0, 36789, 0, 0, 36790, 36793, 0, 0, 0, 0, 0, 0, 2380, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 16, 21, 22, 15, 17, 14, 11, 11, 18, 18, 18, 18, 0, 0);
-- Night Elf Mage male (source DBC ID 75)
INSERT INTO `charstartoutfit_dbc` (`ID`, `RaceID`, `ClassID`, `SexID`, `OutfitID`, `ItemID_1`, `ItemID_2`, `ItemID_3`, `ItemID_4`, `ItemID_5`, `ItemID_6`, `ItemID_7`, `ItemID_8`, `ItemID_9`, `ItemID_10`, `ItemID_11`, `ItemID_12`, `ItemID_13`, `ItemID_14`, `ItemID_15`, `ItemID_16`, `ItemID_17`, `ItemID_18`, `ItemID_19`, `ItemID_20`, `ItemID_21`, `ItemID_22`, `ItemID_23`, `ItemID_24`, `DisplayItemID_1`, `DisplayItemID_2`, `DisplayItemID_3`, `DisplayItemID_4`, `DisplayItemID_5`, `DisplayItemID_6`, `DisplayItemID_7`, `DisplayItemID_8`, `DisplayItemID_9`, `DisplayItemID_10`, `DisplayItemID_11`, `DisplayItemID_12`, `DisplayItemID_13`, `DisplayItemID_14`, `DisplayItemID_15`, `DisplayItemID_16`, `DisplayItemID_17`, `DisplayItemID_18`, `DisplayItemID_19`, `DisplayItemID_20`, `DisplayItemID_21`, `DisplayItemID_22`, `DisplayItemID_23`, `DisplayItemID_24`, `InventoryType_1`, `InventoryType_2`, `InventoryType_3`, `InventoryType_4`, `InventoryType_5`, `InventoryType_6`, `InventoryType_7`, `InventoryType_8`, `InventoryType_9`, `InventoryType_10`, `InventoryType_11`, `InventoryType_12`, `InventoryType_13`, `InventoryType_14`, `InventoryType_15`, `InventoryType_16`, `InventoryType_17`, `InventoryType_18`, `InventoryType_19`, `InventoryType_20`, `InventoryType_21`, `InventoryType_22`, `InventoryType_23`, `InventoryType_24`) VALUES (9008, 4, 8, 0, 0, 0, 0, 0, 0, 56, 0, 1395, 55, 0, 0, 0, 0, 0, 0, 35, 0, 0, 0, 0, 0, 0, 0, 0, 6948, 0, 0, 0, 0, 12647, 0, 9924, 9929, 0, 0, 0, 0, 0, 0, 472, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 16, 21, 22, 15, 17, 14, 11, 11, 18, 18, 18, 18, 0, 0);
-- Night Elf Mage female (source DBC ID 76)
INSERT INTO `charstartoutfit_dbc` (`ID`, `RaceID`, `ClassID`, `SexID`, `OutfitID`, `ItemID_1`, `ItemID_2`, `ItemID_3`, `ItemID_4`, `ItemID_5`, `ItemID_6`, `ItemID_7`, `ItemID_8`, `ItemID_9`, `ItemID_10`, `ItemID_11`, `ItemID_12`, `ItemID_13`, `ItemID_14`, `ItemID_15`, `ItemID_16`, `ItemID_17`, `ItemID_18`, `ItemID_19`, `ItemID_20`, `ItemID_21`, `ItemID_22`, `ItemID_23`, `ItemID_24`, `DisplayItemID_1`, `DisplayItemID_2`, `DisplayItemID_3`, `DisplayItemID_4`, `DisplayItemID_5`, `DisplayItemID_6`, `DisplayItemID_7`, `DisplayItemID_8`, `DisplayItemID_9`, `DisplayItemID_10`, `DisplayItemID_11`, `DisplayItemID_12`, `DisplayItemID_13`, `DisplayItemID_14`, `DisplayItemID_15`, `DisplayItemID_16`, `DisplayItemID_17`, `DisplayItemID_18`, `DisplayItemID_19`, `DisplayItemID_20`, `DisplayItemID_21`, `DisplayItemID_22`, `DisplayItemID_23`, `DisplayItemID_24`, `InventoryType_1`, `InventoryType_2`, `InventoryType_3`, `InventoryType_4`, `InventoryType_5`, `InventoryType_6`, `InventoryType_7`, `InventoryType_8`, `InventoryType_9`, `InventoryType_10`, `InventoryType_11`, `InventoryType_12`, `InventoryType_13`, `InventoryType_14`, `InventoryType_15`, `InventoryType_16`, `InventoryType_17`, `InventoryType_18`, `InventoryType_19`, `InventoryType_20`, `InventoryType_21`, `InventoryType_22`, `InventoryType_23`, `InventoryType_24`) VALUES (9009, 4, 8, 1, 0, 0, 0, 0, 0, 56, 0, 1395, 55, 0, 0, 0, 0, 0, 0, 35, 0, 0, 0, 0, 0, 0, 0, 0, 6948, 0, 0, 0, 0, 12647, 0, 9924, 9929, 0, 0, 0, 0, 0, 0, 472, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 16, 21, 22, 15, 17, 14, 11, 11, 18, 18, 18, 18, 0, 0);
-- Draenei Rogue male (source DBC ID 187)
INSERT INTO `charstartoutfit_dbc` (`ID`, `RaceID`, `ClassID`, `SexID`, `OutfitID`, `ItemID_1`, `ItemID_2`, `ItemID_3`, `ItemID_4`, `ItemID_5`, `ItemID_6`, `ItemID_7`, `ItemID_8`, `ItemID_9`, `ItemID_10`, `ItemID_11`, `ItemID_12`, `ItemID_13`, `ItemID_14`, `ItemID_15`, `ItemID_16`, `ItemID_17`, `ItemID_18`, `ItemID_19`, `ItemID_20`, `ItemID_21`, `ItemID_22`, `ItemID_23`, `ItemID_24`, `DisplayItemID_1`, `DisplayItemID_2`, `DisplayItemID_3`, `DisplayItemID_4`, `DisplayItemID_5`, `DisplayItemID_6`, `DisplayItemID_7`, `DisplayItemID_8`, `DisplayItemID_9`, `DisplayItemID_10`, `DisplayItemID_11`, `DisplayItemID_12`, `DisplayItemID_13`, `DisplayItemID_14`, `DisplayItemID_15`, `DisplayItemID_16`, `DisplayItemID_17`, `DisplayItemID_18`, `DisplayItemID_19`, `DisplayItemID_20`, `DisplayItemID_21`, `DisplayItemID_22`, `DisplayItemID_23`, `DisplayItemID_24`, `InventoryType_1`, `InventoryType_2`, `InventoryType_3`, `InventoryType_4`, `InventoryType_5`, `InventoryType_6`, `InventoryType_7`, `InventoryType_8`, `InventoryType_9`, `InventoryType_10`, `InventoryType_11`, `InventoryType_12`, `InventoryType_13`, `InventoryType_14`, `InventoryType_15`, `InventoryType_16`, `InventoryType_17`, `InventoryType_18`, `InventoryType_19`, `InventoryType_20`, `InventoryType_21`, `InventoryType_22`, `InventoryType_23`, `InventoryType_24`) VALUES (9010, 11, 4, 0, 0, 0, 0, 0, 49, 0, 0, 48, 47, 0, 0, 0, 2092, 50055, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 6948, 0, 0, 0, 9906, 0, 0, 9913, 9915, 0, 0, 0, 6442, 6442, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 16, 21, 22, 15, 17, 14, 11, 11, 18, 18, 18, 18, 0, 0);
-- Draenei Rogue female (source DBC ID 188)
INSERT INTO `charstartoutfit_dbc` (`ID`, `RaceID`, `ClassID`, `SexID`, `OutfitID`, `ItemID_1`, `ItemID_2`, `ItemID_3`, `ItemID_4`, `ItemID_5`, `ItemID_6`, `ItemID_7`, `ItemID_8`, `ItemID_9`, `ItemID_10`, `ItemID_11`, `ItemID_12`, `ItemID_13`, `ItemID_14`, `ItemID_15`, `ItemID_16`, `ItemID_17`, `ItemID_18`, `ItemID_19`, `ItemID_20`, `ItemID_21`, `ItemID_22`, `ItemID_23`, `ItemID_24`, `DisplayItemID_1`, `DisplayItemID_2`, `DisplayItemID_3`, `DisplayItemID_4`, `DisplayItemID_5`, `DisplayItemID_6`, `DisplayItemID_7`, `DisplayItemID_8`, `DisplayItemID_9`, `DisplayItemID_10`, `DisplayItemID_11`, `DisplayItemID_12`, `DisplayItemID_13`, `DisplayItemID_14`, `DisplayItemID_15`, `DisplayItemID_16`, `DisplayItemID_17`, `DisplayItemID_18`, `DisplayItemID_19`, `DisplayItemID_20`, `DisplayItemID_21`, `DisplayItemID_22`, `DisplayItemID_23`, `DisplayItemID_24`, `InventoryType_1`, `InventoryType_2`, `InventoryType_3`, `InventoryType_4`, `InventoryType_5`, `InventoryType_6`, `InventoryType_7`, `InventoryType_8`, `InventoryType_9`, `InventoryType_10`, `InventoryType_11`, `InventoryType_12`, `InventoryType_13`, `InventoryType_14`, `InventoryType_15`, `InventoryType_16`, `InventoryType_17`, `InventoryType_18`, `InventoryType_19`, `InventoryType_20`, `InventoryType_21`, `InventoryType_22`, `InventoryType_23`, `InventoryType_24`) VALUES (9011, 11, 4, 1, 0, 0, 0, 0, 49, 0, 0, 48, 47, 0, 0, 0, 2092, 50055, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 6948, 0, 0, 0, 9906, 0, 0, 9913, 9915, 0, 0, 0, 6442, 6442, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 16, 21, 22, 15, 17, 14, 11, 11, 18, 18, 18, 18, 0, 0);
-- Tauren Priest male (source DBC ID 109)
INSERT INTO `charstartoutfit_dbc` (`ID`, `RaceID`, `ClassID`, `SexID`, `OutfitID`, `ItemID_1`, `ItemID_2`, `ItemID_3`, `ItemID_4`, `ItemID_5`, `ItemID_6`, `ItemID_7`, `ItemID_8`, `ItemID_9`, `ItemID_10`, `ItemID_11`, `ItemID_12`, `ItemID_13`, `ItemID_14`, `ItemID_15`, `ItemID_16`, `ItemID_17`, `ItemID_18`, `ItemID_19`, `ItemID_20`, `ItemID_21`, `ItemID_22`, `ItemID_23`, `ItemID_24`, `DisplayItemID_1`, `DisplayItemID_2`, `DisplayItemID_3`, `DisplayItemID_4`, `DisplayItemID_5`, `DisplayItemID_6`, `DisplayItemID_7`, `DisplayItemID_8`, `DisplayItemID_9`, `DisplayItemID_10`, `DisplayItemID_11`, `DisplayItemID_12`, `DisplayItemID_13`, `DisplayItemID_14`, `DisplayItemID_15`, `DisplayItemID_16`, `DisplayItemID_17`, `DisplayItemID_18`, `DisplayItemID_19`, `DisplayItemID_20`, `DisplayItemID_21`, `DisplayItemID_22`, `DisplayItemID_23`, `DisplayItemID_24`, `InventoryType_1`, `InventoryType_2`, `InventoryType_3`, `InventoryType_4`, `InventoryType_5`, `InventoryType_6`, `InventoryType_7`, `InventoryType_8`, `InventoryType_9`, `InventoryType_10`, `InventoryType_11`, `InventoryType_12`, `InventoryType_13`, `InventoryType_14`, `InventoryType_15`, `InventoryType_16`, `InventoryType_17`, `InventoryType_18`, `InventoryType_19`, `InventoryType_20`, `InventoryType_21`, `InventoryType_22`, `InventoryType_23`, `InventoryType_24`) VALUES (9012, 6, 5, 0, 0, 0, 0, 0, 53, 6144, 0, 52, 51, 0, 0, 0, 0, 0, 0, 35, 0, 0, 0, 0, 0, 0, 0, 0, 6948, 0, 0, 0, 9944, 12680, 0, 9945, 9946, 0, 0, 0, 0, 0, 0, 472, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 16, 21, 22, 15, 17, 14, 11, 11, 18, 18, 18, 18, 0, 0);
-- Tauren Priest female (source DBC ID 110)
INSERT INTO `charstartoutfit_dbc` (`ID`, `RaceID`, `ClassID`, `SexID`, `OutfitID`, `ItemID_1`, `ItemID_2`, `ItemID_3`, `ItemID_4`, `ItemID_5`, `ItemID_6`, `ItemID_7`, `ItemID_8`, `ItemID_9`, `ItemID_10`, `ItemID_11`, `ItemID_12`, `ItemID_13`, `ItemID_14`, `ItemID_15`, `ItemID_16`, `ItemID_17`, `ItemID_18`, `ItemID_19`, `ItemID_20`, `ItemID_21`, `ItemID_22`, `ItemID_23`, `ItemID_24`, `DisplayItemID_1`, `DisplayItemID_2`, `DisplayItemID_3`, `DisplayItemID_4`, `DisplayItemID_5`, `DisplayItemID_6`, `DisplayItemID_7`, `DisplayItemID_8`, `DisplayItemID_9`, `DisplayItemID_10`, `DisplayItemID_11`, `DisplayItemID_12`, `DisplayItemID_13`, `DisplayItemID_14`, `DisplayItemID_15`, `DisplayItemID_16`, `DisplayItemID_17`, `DisplayItemID_18`, `DisplayItemID_19`, `DisplayItemID_20`, `DisplayItemID_21`, `DisplayItemID_22`, `DisplayItemID_23`, `DisplayItemID_24`, `InventoryType_1`, `InventoryType_2`, `InventoryType_3`, `InventoryType_4`, `InventoryType_5`, `InventoryType_6`, `InventoryType_7`, `InventoryType_8`, `InventoryType_9`, `InventoryType_10`, `InventoryType_11`, `InventoryType_12`, `InventoryType_13`, `InventoryType_14`, `InventoryType_15`, `InventoryType_16`, `InventoryType_17`, `InventoryType_18`, `InventoryType_19`, `InventoryType_20`, `InventoryType_21`, `InventoryType_22`, `InventoryType_23`, `InventoryType_24`) VALUES (9013, 6, 5, 1, 0, 0, 0, 0, 53, 6144, 0, 52, 51, 0, 0, 0, 0, 0, 0, 35, 0, 0, 0, 0, 0, 0, 0, 0, 6948, 0, 0, 0, 9944, 12680, 0, 9945, 9946, 0, 0, 0, 0, 0, 0, 472, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 16, 21, 22, 15, 17, 14, 11, 11, 18, 18, 18, 18, 0, 0);
-- Gnome Hunter male (source DBC ID 125)
INSERT INTO `charstartoutfit_dbc` (`ID`, `RaceID`, `ClassID`, `SexID`, `OutfitID`, `ItemID_1`, `ItemID_2`, `ItemID_3`, `ItemID_4`, `ItemID_5`, `ItemID_6`, `ItemID_7`, `ItemID_8`, `ItemID_9`, `ItemID_10`, `ItemID_11`, `ItemID_12`, `ItemID_13`, `ItemID_14`, `ItemID_15`, `ItemID_16`, `ItemID_17`, `ItemID_18`, `ItemID_19`, `ItemID_20`, `ItemID_21`, `ItemID_22`, `ItemID_23`, `ItemID_24`, `DisplayItemID_1`, `DisplayItemID_2`, `DisplayItemID_3`, `DisplayItemID_4`, `DisplayItemID_5`, `DisplayItemID_6`, `DisplayItemID_7`, `DisplayItemID_8`, `DisplayItemID_9`, `DisplayItemID_10`, `DisplayItemID_11`, `DisplayItemID_12`, `DisplayItemID_13`, `DisplayItemID_14`, `DisplayItemID_15`, `DisplayItemID_16`, `DisplayItemID_17`, `DisplayItemID_18`, `DisplayItemID_19`, `DisplayItemID_20`, `DisplayItemID_21`, `DisplayItemID_22`, `DisplayItemID_23`, `DisplayItemID_24`, `InventoryType_1`, `InventoryType_2`, `InventoryType_3`, `InventoryType_4`, `InventoryType_5`, `InventoryType_6`, `InventoryType_7`, `InventoryType_8`, `InventoryType_9`, `InventoryType_10`, `InventoryType_11`, `InventoryType_12`, `InventoryType_13`, `InventoryType_14`, `InventoryType_15`, `InventoryType_16`, `InventoryType_17`, `InventoryType_18`, `InventoryType_19`, `InventoryType_20`, `InventoryType_21`, `InventoryType_22`, `InventoryType_23`, `InventoryType_24`) VALUES (9014, 7, 3, 0, 0, 0, 0, 0, 148, 0, 0, 147, 129, 0, 0, 0, 0, 0, 2508, 12282, 0, 0, 0, 2102, 0, 0, 0, 2516, 6948, 0, 0, 0, 9976, 0, 0, 9975, 9977, 0, 0, 0, 0, 0, 6606, 22291, 0, 0, 0, 1816, 0, 0, 0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 16, 21, 22, 15, 17, 14, 11, 11, 18, 18, 18, 18, 0, 0);
-- Gnome Hunter female (source DBC ID 126)
INSERT INTO `charstartoutfit_dbc` (`ID`, `RaceID`, `ClassID`, `SexID`, `OutfitID`, `ItemID_1`, `ItemID_2`, `ItemID_3`, `ItemID_4`, `ItemID_5`, `ItemID_6`, `ItemID_7`, `ItemID_8`, `ItemID_9`, `ItemID_10`, `ItemID_11`, `ItemID_12`, `ItemID_13`, `ItemID_14`, `ItemID_15`, `ItemID_16`, `ItemID_17`, `ItemID_18`, `ItemID_19`, `ItemID_20`, `ItemID_21`, `ItemID_22`, `ItemID_23`, `ItemID_24`, `DisplayItemID_1`, `DisplayItemID_2`, `DisplayItemID_3`, `DisplayItemID_4`, `DisplayItemID_5`, `DisplayItemID_6`, `DisplayItemID_7`, `DisplayItemID_8`, `DisplayItemID_9`, `DisplayItemID_10`, `DisplayItemID_11`, `DisplayItemID_12`, `DisplayItemID_13`, `DisplayItemID_14`, `DisplayItemID_15`, `DisplayItemID_16`, `DisplayItemID_17`, `DisplayItemID_18`, `DisplayItemID_19`, `DisplayItemID_20`, `DisplayItemID_21`, `DisplayItemID_22`, `DisplayItemID_23`, `DisplayItemID_24`, `InventoryType_1`, `InventoryType_2`, `InventoryType_3`, `InventoryType_4`, `InventoryType_5`, `InventoryType_6`, `InventoryType_7`, `InventoryType_8`, `InventoryType_9`, `InventoryType_10`, `InventoryType_11`, `InventoryType_12`, `InventoryType_13`, `InventoryType_14`, `InventoryType_15`, `InventoryType_16`, `InventoryType_17`, `InventoryType_18`, `InventoryType_19`, `InventoryType_20`, `InventoryType_21`, `InventoryType_22`, `InventoryType_23`, `InventoryType_24`) VALUES (9015, 7, 3, 1, 0, 0, 0, 0, 148, 0, 0, 147, 129, 0, 0, 0, 0, 0, 2508, 12282, 0, 0, 0, 2102, 0, 0, 0, 2516, 6948, 0, 0, 0, 9976, 0, 0, 9975, 9977, 0, 0, 0, 0, 0, 6606, 22291, 0, 0, 0, 1816, 0, 0, 0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 16, 21, 22, 15, 17, 14, 11, 11, 18, 18, 18, 18, 0, 0);

-- -------------------------------------------------------------------------
-- Quest race-mask extensions
-- -------------------------------------------------------------------------

-- Allow Gnomes to take the Dwarf Hunter pet-taming chain.
UPDATE `quest_template`
SET `AllowableRaces` = `AllowableRaces` | 64
WHERE `ID` IN (3108, 6074, 6075, 6076, 6064, 6084, 6085, 6086)
  AND NOT (`AllowableRaces` & 64);

COMMIT;
