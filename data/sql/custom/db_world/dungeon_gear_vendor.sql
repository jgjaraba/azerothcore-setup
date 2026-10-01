-- ============================================================================
-- Dark Riders - Dungeon Curios
-- Bad Luck Protection currencies
--
-- 90010 - Ragefire Chasm Curio
-- 90011 - Wailing Caverns Curio
-- 90012 - Deadmines Curio
-- 90013 - Shadowfang Keep Curio
-- 90014 - Blackfathom Deeps Curio
-- 90015 - Stockade Curio
-- 90016 - Gnomeregan Curio
-- 90017 - Razorfen Kraul Curio
-- 90018 - Scarlet Graveyard Curio
-- 90019 - Scarlet Library Curio
-- 90020 - Scarlet Armory Curio
-- 90021 - Scarlet Cathedral Curio
-- 90022 - Razorfen Downs Curio
-- 90023 - Uldaman Curio
-- 90024 - Zul'Farrak Curio
-- 90025 - Maraudon Curio
-- 90026 - Sunken Temple Curio
-- 90027 - Blackrock Depths Curio
-- 90028 - Lower Blackrock Spire Curio
-- 90029 - Upper Blackrock Spire Curio
-- 90030 - Dire Maul East Curio
-- 90031 - Dire Maul West Curio
-- 90032 - Dire Maul North Curio
-- 90033 - Scholomance Curio
-- 90034 - Stratholme Living Quarter Curio
-- 90035 - Stratholme Undead Quarter Curio
--
-- AzerothCore 3.3.5a
-- Database: acore_world
--
-- Pattern: data/sql/custom/db_world/raid_gear_vendor.sql
-- Reference commit: d63193c1ce955594e8a367caf5b4dc3d1022dc70
--
-- This file defines the currency items and their esES localization.
-- Final-boss rewards (1 token per eligible player) belong in the loot SQL.
-- Vendor prices (2 tokens per item) belong in the vendor SQL / DBC.
--
-- Item IDs 90010-90035 have no occurrences in the reviewed custom world SQL
-- or tracked Item.dbc. The deployed world database was not inspected.
-- Native display IDs below exist in the tracked ItemDisplayInfo.dbc.
-- ============================================================================


USE `acore_world`;

START TRANSACTION;


-- ============================================================================
-- CONFIGURATION
-- ============================================================================


SET @RFC_CURIO               := 90010;
SET @WC_CURIO                := 90011;
SET @DEADMINES_CURIO         := 90012;
SET @SFK_CURIO               := 90013;
SET @BFD_CURIO               := 90014;
SET @STOCKADES_CURIO         := 90015;
SET @GNOMEREGAN_CURIO        := 90016;
SET @RFK_CURIO               := 90017;
SET @SM_GY_CURIO             := 90018;
SET @SM_LIB_CURIO            := 90019;
SET @SM_ARM_CURIO            := 90020;
SET @SM_CAT_CURIO            := 90021;
SET @RFD_CURIO               := 90022;
SET @ULDAMAN_CURIO           := 90023;
SET @ZF_CURIO                := 90024;
SET @MARAUDON_CURIO          := 90025;
SET @ST_CURIO                := 90026;
SET @BRD_CURIO               := 90027;
SET @LBRS_CURIO              := 90028;
SET @UBRS_CURIO              := 90029;
SET @DM_EAST_CURIO           := 90030;
SET @DM_WEST_CURIO           := 90031;
SET @DM_NORTH_CURIO          := 90032;
SET @SCHOLO_CURIO            := 90033;
SET @STRAT_LIVE_CURIO        := 90034;
SET @STRAT_UNDEAD_CURIO      := 90035;

-- Native item used as structural template.
-- Badge of Justice is already configured as a non-equippable token.
SET @BASE_ITEM := 29434;


-- ============================================================================
-- CLEAN PREVIOUS VERSIONS
-- ============================================================================


DELETE FROM `item_template_locale`
WHERE `ID` IN (
    @RFC_CURIO,
    @WC_CURIO,
    @DEADMINES_CURIO,
    @SFK_CURIO,
    @BFD_CURIO,
    @STOCKADES_CURIO,
    @GNOMEREGAN_CURIO,
    @RFK_CURIO,
    @SM_GY_CURIO,
    @SM_LIB_CURIO,
    @SM_ARM_CURIO,
    @SM_CAT_CURIO,
    @RFD_CURIO,
    @ULDAMAN_CURIO,
    @ZF_CURIO,
    @MARAUDON_CURIO,
    @ST_CURIO,
    @BRD_CURIO,
    @LBRS_CURIO,
    @UBRS_CURIO,
    @DM_EAST_CURIO,
    @DM_WEST_CURIO,
    @DM_NORTH_CURIO,
    @SCHOLO_CURIO,
    @STRAT_LIVE_CURIO,
    @STRAT_UNDEAD_CURIO
);

DELETE FROM `item_template`
WHERE `entry` IN (
    @RFC_CURIO,
    @WC_CURIO,
    @DEADMINES_CURIO,
    @SFK_CURIO,
    @BFD_CURIO,
    @STOCKADES_CURIO,
    @GNOMEREGAN_CURIO,
    @RFK_CURIO,
    @SM_GY_CURIO,
    @SM_LIB_CURIO,
    @SM_ARM_CURIO,
    @SM_CAT_CURIO,
    @RFD_CURIO,
    @ULDAMAN_CURIO,
    @ZF_CURIO,
    @MARAUDON_CURIO,
    @ST_CURIO,
    @BRD_CURIO,
    @LBRS_CURIO,
    @UBRS_CURIO,
    @DM_EAST_CURIO,
    @DM_WEST_CURIO,
    @DM_NORTH_CURIO,
    @SCHOLO_CURIO,
    @STRAT_LIVE_CURIO,
    @STRAT_UNDEAD_CURIO
);


-- ============================================================================
-- TEMPORARY TEMPLATE
--
-- Using LIKE + SELECT * makes this compatible with the complete item_template
-- structure of the installed AzerothCore database without having to hardcode
-- every column.
--
-- Flags = 2048 preserves ITEM_FLAG_MULTI_DROP from the raid-curio pattern.
-- BagFamily = 0 keeps these as ordinary inventory items; this file does not
-- implement automatic distribution or create any loot rewards.
-- ============================================================================


DROP TEMPORARY TABLE IF EXISTS `tmp_currency_token`;

CREATE TEMPORARY TABLE `tmp_currency_token`
LIKE `item_template`;

INSERT INTO `tmp_currency_token`
SELECT *
FROM `item_template`
WHERE `entry` = @BASE_ITEM
    LIMIT 1;


-- ============================================================================
-- RAGEFIRE CHASM CURIO
-- ============================================================================


UPDATE `tmp_currency_token`
SET
    `entry`          = @RFC_CURIO,
    `class`          = 15,
    `subclass`       = 0,
    `name`           = 'Ragefire Chasm Curio',
    `Quality`        = 4,
    `area`           = 0,
    `Map`            = 0,
    `Flags`          = 2048,
    `FlagsExtra`     = 0,
    `BuyCount`       = 1,
    `BuyPrice`       = 0,
    `BagFamily`      = 0,
    `SellPrice`      = 0,
    `InventoryType`  = 0,
    `displayid`      = 21583,
    `AllowableClass` = -1,
    `AllowableRace`  = -1,
    `ItemLevel`      = 1,
    `RequiredLevel`  = 1,
    `maxcount`       = 0,
    `stackable`      = 200,
    `bonding`        = 1,
    `description`    = 'A scorched fragment recovered from the fiery caverns beneath Orgrimmar. A collector of rare artifacts might find value in it.',
    `VerifiedBuild`  = 0;

INSERT INTO `item_template`
SELECT *
FROM `tmp_currency_token`;


-- ============================================================================
-- WAILING CAVERNS CURIO
-- ============================================================================


UPDATE `tmp_currency_token`
SET
    `entry`          = @WC_CURIO,
    `class`          = 15,
    `subclass`       = 0,
    `name`           = 'Wailing Caverns Curio',
    `Quality`        = 4,
    `area`           = 0,
    `Map`            = 0,
    `Flags`          = 2048,
    `FlagsExtra`     = 0,
    `BuyCount`       = 1,
    `BuyPrice`       = 0,
    `BagFamily`      = 0,
    `SellPrice`      = 0,
    `InventoryType`  = 0,
    `displayid`      = 6850,
    `AllowableClass` = -1,
    `AllowableRace`  = -1,
    `ItemLevel`      = 1,
    `RequiredLevel`  = 1,
    `maxcount`       = 0,
    `stackable`      = 200,
    `bonding`        = 1,
    `description`    = 'A green stone that echoes with the troubled dreams of the Wailing Caverns. A collector of rare artifacts might find value in it.',
    `VerifiedBuild`  = 0;

INSERT INTO `item_template`
SELECT *
FROM `tmp_currency_token`;


-- ============================================================================
-- THE DEADMINES CURIO
-- ============================================================================


UPDATE `tmp_currency_token`
SET
    `entry`          = @DEADMINES_CURIO,
    `class`          = 15,
    `subclass`       = 0,
    `name`           = 'Deadmines Curio',
    `Quality`        = 4,
    `area`           = 0,
    `Map`            = 0,
    `Flags`          = 2048,
    `FlagsExtra`     = 0,
    `BuyCount`       = 1,
    `BuyPrice`       = 0,
    `BagFamily`      = 0,
    `SellPrice`      = 0,
    `InventoryType`  = 0,
    `displayid`      = 1270,
    `AllowableClass` = -1,
    `AllowableRace`  = -1,
    `ItemLevel`      = 1,
    `RequiredLevel`  = 1,
    `maxcount`       = 0,
    `stackable`      = 200,
    `bonding`        = 1,
    `description`    = 'A tarnished keepsake recovered from the Defias hideout beneath Westfall. A collector of rare artifacts might find value in it.',
    `VerifiedBuild`  = 0;

INSERT INTO `item_template`
SELECT *
FROM `tmp_currency_token`;


-- ============================================================================
-- SHADOWFANG KEEP CURIO
-- ============================================================================


UPDATE `tmp_currency_token`
SET
    `entry`          = @SFK_CURIO,
    `class`          = 15,
    `subclass`       = 0,
    `name`           = 'Shadowfang Keep Curio',
    `Quality`        = 4,
    `area`           = 0,
    `Map`            = 0,
    `Flags`          = 2048,
    `FlagsExtra`     = 0,
    `BuyCount`       = 1,
    `BuyPrice`       = 0,
    `BagFamily`      = 0,
    `SellPrice`      = 0,
    `InventoryType`  = 0,
    `displayid`      = 1496,
    `AllowableClass` = -1,
    `AllowableRace`  = -1,
    `ItemLevel`      = 1,
    `RequiredLevel`  = 1,
    `maxcount`       = 0,
    `stackable`      = 200,
    `bonding`        = 1,
    `description`    = 'A blackened claw carrying a trace of the curse that haunts Shadowfang Keep. A collector of rare artifacts might find value in it.',
    `VerifiedBuild`  = 0;

INSERT INTO `item_template`
SELECT *
FROM `tmp_currency_token`;


-- ============================================================================
-- BLACKFATHOM DEEPS CURIO
-- ============================================================================


UPDATE `tmp_currency_token`
SET
    `entry`          = @BFD_CURIO,
    `class`          = 15,
    `subclass`       = 0,
    `name`           = 'Blackfathom Deeps Curio',
    `Quality`        = 4,
    `area`           = 0,
    `Map`            = 0,
    `Flags`          = 2048,
    `FlagsExtra`     = 0,
    `BuyCount`       = 1,
    `BuyPrice`       = 0,
    `BagFamily`      = 0,
    `SellPrice`      = 0,
    `InventoryType`  = 0,
    `displayid`      = 12309,
    `AllowableClass` = -1,
    `AllowableRace`  = -1,
    `ItemLevel`      = 1,
    `RequiredLevel`  = 1,
    `maxcount`       = 0,
    `stackable`      = 200,
    `bonding`        = 1,
    `description`    = 'A salt-worn pearl recovered from the drowned halls of Blackfathom Deeps. A collector of rare artifacts might find value in it.',
    `VerifiedBuild`  = 0;

INSERT INTO `item_template`
SELECT *
FROM `tmp_currency_token`;


-- ============================================================================
-- THE STOCKADE CURIO
-- ============================================================================


UPDATE `tmp_currency_token`
SET
    `entry`          = @STOCKADES_CURIO,
    `class`          = 15,
    `subclass`       = 0,
    `name`           = 'Stockade Curio',
    `Quality`        = 4,
    `area`           = 0,
    `Map`            = 0,
    `Flags`          = 2048,
    `FlagsExtra`     = 0,
    `BuyCount`       = 1,
    `BuyPrice`       = 0,
    `BagFamily`      = 0,
    `SellPrice`      = 0,
    `InventoryType`  = 0,
    `displayid`      = 2530,
    `AllowableClass` = -1,
    `AllowableRace`  = -1,
    `ItemLevel`      = 1,
    `RequiredLevel`  = 1,
    `maxcount`       = 0,
    `stackable`      = 200,
    `bonding`        = 1,
    `description`    = 'A battered key recovered from the prison beneath Stormwind. A collector of rare artifacts might find value in it.',
    `VerifiedBuild`  = 0;

INSERT INTO `item_template`
SELECT *
FROM `tmp_currency_token`;


-- ============================================================================
-- GNOMEREGAN CURIO
-- ============================================================================


UPDATE `tmp_currency_token`
SET
    `entry`          = @GNOMEREGAN_CURIO,
    `class`          = 15,
    `subclass`       = 0,
    `name`           = 'Gnomeregan Curio',
    `Quality`        = 4,
    `area`           = 0,
    `Map`            = 0,
    `Flags`          = 2048,
    `FlagsExtra`     = 0,
    `BuyCount`       = 1,
    `BuyPrice`       = 0,
    `BagFamily`      = 0,
    `SellPrice`      = 0,
    `InventoryType`  = 0,
    `displayid`      = 1221,
    `AllowableClass` = -1,
    `AllowableRace`  = -1,
    `ItemLevel`      = 1,
    `RequiredLevel`  = 1,
    `maxcount`       = 0,
    `stackable`      = 200,
    `bonding`        = 1,
    `description`    = 'A curious cog salvaged from the abandoned machinery of Gnomeregan. A collector of rare artifacts might find value in it.',
    `VerifiedBuild`  = 0;

INSERT INTO `item_template`
SELECT *
FROM `tmp_currency_token`;


-- ============================================================================
-- RAZORFEN KRAUL CURIO
-- ============================================================================


UPDATE `tmp_currency_token`
SET
    `entry`          = @RFK_CURIO,
    `class`          = 15,
    `subclass`       = 0,
    `name`           = 'Razorfen Kraul Curio',
    `Quality`        = 4,
    `area`           = 0,
    `Map`            = 0,
    `Flags`          = 2048,
    `FlagsExtra`     = 0,
    `BuyCount`       = 1,
    `BuyPrice`       = 0,
    `BagFamily`      = 0,
    `SellPrice`      = 0,
    `InventoryType`  = 0,
    `displayid`      = 1040,
    `AllowableClass` = -1,
    `AllowableRace`  = -1,
    `ItemLevel`      = 1,
    `RequiredLevel`  = 1,
    `maxcount`       = 0,
    `stackable`      = 200,
    `bonding`        = 1,
    `description`    = 'A small idol tangled in the ancient roots of Razorfen Kraul. A collector of rare artifacts might find value in it.',
    `VerifiedBuild`  = 0;

INSERT INTO `item_template`
SELECT *
FROM `tmp_currency_token`;


-- ============================================================================
-- SCARLET MONASTERY - GRAVEYARD CURIO
-- ============================================================================


UPDATE `tmp_currency_token`
SET
    `entry`          = @SM_GY_CURIO,
    `class`          = 15,
    `subclass`       = 0,
    `name`           = 'Scarlet Graveyard Curio',
    `Quality`        = 4,
    `area`           = 0,
    `Map`            = 0,
    `Flags`          = 2048,
    `FlagsExtra`     = 0,
    `BuyCount`       = 1,
    `BuyPrice`       = 0,
    `BagFamily`      = 0,
    `SellPrice`      = 0,
    `InventoryType`  = 0,
    `displayid`      = 2853,
    `AllowableClass` = -1,
    `AllowableRace`  = -1,
    `ItemLevel`      = 1,
    `RequiredLevel`  = 1,
    `maxcount`       = 0,
    `stackable`      = 200,
    `bonding`        = 1,
    `description`    = 'A weathered funerary relic recovered from the Scarlet Monastery graveyard. A collector of rare artifacts might find value in it.',
    `VerifiedBuild`  = 0;

INSERT INTO `item_template`
SELECT *
FROM `tmp_currency_token`;


-- ============================================================================
-- SCARLET MONASTERY - LIBRARY CURIO
-- ============================================================================


UPDATE `tmp_currency_token`
SET
    `entry`          = @SM_LIB_CURIO,
    `class`          = 15,
    `subclass`       = 0,
    `name`           = 'Scarlet Library Curio',
    `Quality`        = 4,
    `area`           = 0,
    `Map`            = 0,
    `Flags`          = 2048,
    `FlagsExtra`     = 0,
    `BuyCount`       = 1,
    `BuyPrice`       = 0,
    `BagFamily`      = 0,
    `SellPrice`      = 0,
    `InventoryType`  = 0,
    `displayid`      = 1134,
    `AllowableClass` = -1,
    `AllowableRace`  = -1,
    `ItemLevel`      = 1,
    `RequiredLevel`  = 1,
    `maxcount`       = 0,
    `stackable`      = 200,
    `bonding`        = 1,
    `description`    = 'A forbidden volume taken from the guarded shelves of the Scarlet Library. A collector of rare artifacts might find value in it.',
    `VerifiedBuild`  = 0;

INSERT INTO `item_template`
SELECT *
FROM `tmp_currency_token`;


-- ============================================================================
-- SCARLET MONASTERY - ARMORY CURIO
-- ============================================================================


UPDATE `tmp_currency_token`
SET
    `entry`          = @SM_ARM_CURIO,
    `class`          = 15,
    `subclass`       = 0,
    `name`           = 'Scarlet Armory Curio',
    `Quality`        = 4,
    `area`           = 0,
    `Map`            = 0,
    `Flags`          = 2048,
    `FlagsExtra`     = 0,
    `BuyCount`       = 1,
    `BuyPrice`       = 0,
    `BagFamily`      = 0,
    `SellPrice`      = 0,
    `InventoryType`  = 0,
    `displayid`      = 946,
    `AllowableClass` = -1,
    `AllowableRace`  = -1,
    `ItemLevel`      = 1,
    `RequiredLevel`  = 1,
    `maxcount`       = 0,
    `stackable`      = 200,
    `bonding`        = 1,
    `description`    = 'An engraved token recovered from the weapon stores of the Scarlet Armory. A collector of rare artifacts might find value in it.',
    `VerifiedBuild`  = 0;

INSERT INTO `item_template`
SELECT *
FROM `tmp_currency_token`;


-- ============================================================================
-- SCARLET MONASTERY - CATHEDRAL CURIO
-- ============================================================================


UPDATE `tmp_currency_token`
SET
    `entry`          = @SM_CAT_CURIO,
    `class`          = 15,
    `subclass`       = 0,
    `name`           = 'Scarlet Cathedral Curio',
    `Quality`        = 4,
    `area`           = 0,
    `Map`            = 0,
    `Flags`          = 2048,
    `FlagsExtra`     = 0,
    `BuyCount`       = 1,
    `BuyPrice`       = 0,
    `BagFamily`      = 0,
    `SellPrice`      = 0,
    `InventoryType`  = 0,
    `displayid`      = 2516,
    `AllowableClass` = -1,
    `AllowableRace`  = -1,
    `ItemLevel`      = 1,
    `RequiredLevel`  = 1,
    `maxcount`       = 0,
    `stackable`      = 200,
    `bonding`        = 1,
    `description`    = 'A pale gemstone taken from a reliquary within the Scarlet Cathedral. A collector of rare artifacts might find value in it.',
    `VerifiedBuild`  = 0;

INSERT INTO `item_template`
SELECT *
FROM `tmp_currency_token`;


-- ============================================================================
-- RAZORFEN DOWNS CURIO
-- ============================================================================


UPDATE `tmp_currency_token`
SET
    `entry`          = @RFD_CURIO,
    `class`          = 15,
    `subclass`       = 0,
    `name`           = 'Razorfen Downs Curio',
    `Quality`        = 4,
    `area`           = 0,
    `Map`            = 0,
    `Flags`          = 2048,
    `FlagsExtra`     = 0,
    `BuyCount`       = 1,
    `BuyPrice`       = 0,
    `BagFamily`      = 0,
    `SellPrice`      = 0,
    `InventoryType`  = 0,
    `displayid`      = 10345,
    `AllowableClass` = -1,
    `AllowableRace`  = -1,
    `ItemLevel`      = 1,
    `RequiredLevel`  = 1,
    `maxcount`       = 0,
    `stackable`      = 200,
    `bonding`        = 1,
    `description`    = 'A ritual bone marked by the unnatural chill that hangs over Razorfen Downs. A collector of rare artifacts might find value in it.',
    `VerifiedBuild`  = 0;

INSERT INTO `item_template`
SELECT *
FROM `tmp_currency_token`;


-- ============================================================================
-- ULDAMAN CURIO
-- ============================================================================


UPDATE `tmp_currency_token`
SET
    `entry`          = @ULDAMAN_CURIO,
    `class`          = 15,
    `subclass`       = 0,
    `name`           = 'Uldaman Curio',
    `Quality`        = 4,
    `area`           = 0,
    `Map`            = 0,
    `Flags`          = 2048,
    `FlagsExtra`     = 0,
    `BuyCount`       = 1,
    `BuyPrice`       = 0,
    `BagFamily`      = 0,
    `SellPrice`      = 0,
    `InventoryType`  = 0,
    `displayid`      = 5562,
    `AllowableClass` = -1,
    `AllowableRace`  = -1,
    `ItemLevel`      = 1,
    `RequiredLevel`  = 1,
    `maxcount`       = 0,
    `stackable`      = 200,
    `bonding`        = 1,
    `description`    = 'A carved stone fragment unearthed from the ancient halls of Uldaman. A collector of rare artifacts might find value in it.',
    `VerifiedBuild`  = 0;

INSERT INTO `item_template`
SELECT *
FROM `tmp_currency_token`;


-- ============================================================================
-- ZUL'FARRAK CURIO
-- ============================================================================


UPDATE `tmp_currency_token`
SET
    `entry`          = @ZF_CURIO,
    `class`          = 15,
    `subclass`       = 0,
    `name`           = 'Zul''Farrak Curio',
    `Quality`        = 4,
    `area`           = 0,
    `Map`            = 0,
    `Flags`          = 2048,
    `FlagsExtra`     = 0,
    `BuyCount`       = 1,
    `BuyPrice`       = 0,
    `BagFamily`      = 0,
    `SellPrice`      = 0,
    `InventoryType`  = 0,
    `displayid`      = 2551,
    `AllowableClass` = -1,
    `AllowableRace`  = -1,
    `ItemLevel`      = 1,
    `RequiredLevel`  = 1,
    `maxcount`       = 0,
    `stackable`      = 200,
    `bonding`        = 1,
    `description`    = 'A sand-worn idol recovered from the sacred grounds of Zul''Farrak. A collector of rare artifacts might find value in it.',
    `VerifiedBuild`  = 0;

INSERT INTO `item_template`
SELECT *
FROM `tmp_currency_token`;


-- ============================================================================
-- MARAUDON CURIO
-- ============================================================================


UPDATE `tmp_currency_token`
SET
    `entry`          = @MARAUDON_CURIO,
    `class`          = 15,
    `subclass`       = 0,
    `name`           = 'Maraudon Curio',
    `Quality`        = 4,
    `area`           = 0,
    `Map`            = 0,
    `Flags`          = 2048,
    `FlagsExtra`     = 0,
    `BuyCount`       = 1,
    `BuyPrice`       = 0,
    `BagFamily`      = 0,
    `SellPrice`      = 0,
    `InventoryType`  = 0,
    `displayid`      = 1231,
    `AllowableClass` = -1,
    `AllowableRace`  = -1,
    `ItemLevel`      = 1,
    `RequiredLevel`  = 1,
    `maxcount`       = 0,
    `stackable`      = 200,
    `bonding`        = 1,
    `description`    = 'A violet crystal formed among the ancient roots and stone chambers of Maraudon. A collector of rare artifacts might find value in it.',
    `VerifiedBuild`  = 0;

INSERT INTO `item_template`
SELECT *
FROM `tmp_currency_token`;


-- ============================================================================
-- THE TEMPLE OF ATAL'HAKKAR CURIO
-- ============================================================================


UPDATE `tmp_currency_token`
SET
    `entry`          = @ST_CURIO,
    `class`          = 15,
    `subclass`       = 0,
    `name`           = 'Sunken Temple Curio',
    `Quality`        = 4,
    `area`           = 0,
    `Map`            = 0,
    `Flags`          = 2048,
    `FlagsExtra`     = 0,
    `BuyCount`       = 1,
    `BuyPrice`       = 0,
    `BagFamily`      = 0,
    `SellPrice`      = 0,
    `InventoryType`  = 0,
    `displayid`      = 4005,
    `AllowableClass` = -1,
    `AllowableRace`  = -1,
    `ItemLevel`      = 1,
    `RequiredLevel`  = 1,
    `maxcount`       = 0,
    `stackable`      = 200,
    `bonding`        = 1,
    `description`    = 'A blood-red stone recovered from the drowned sanctum of Atal''Hakkar. A collector of rare artifacts might find value in it.',
    `VerifiedBuild`  = 0;

INSERT INTO `item_template`
SELECT *
FROM `tmp_currency_token`;


-- ============================================================================
-- BLACKROCK DEPTHS CURIO
-- ============================================================================


UPDATE `tmp_currency_token`
SET
    `entry`          = @BRD_CURIO,
    `class`          = 15,
    `subclass`       = 0,
    `name`           = 'Blackrock Depths Curio',
    `Quality`        = 4,
    `area`           = 0,
    `Map`            = 0,
    `Flags`          = 2048,
    `FlagsExtra`     = 0,
    `BuyCount`       = 1,
    `BuyPrice`       = 0,
    `BagFamily`      = 0,
    `SellPrice`      = 0,
    `InventoryType`  = 0,
    `displayid`      = 20219,
    `AllowableClass` = -1,
    `AllowableRace`  = -1,
    `ItemLevel`      = 1,
    `RequiredLevel`  = 1,
    `maxcount`       = 0,
    `stackable`      = 200,
    `bonding`        = 1,
    `description`    = 'A runic relic blackened by the forges of the Dark Iron dwarves. A collector of rare artifacts might find value in it.',
    `VerifiedBuild`  = 0;

INSERT INTO `item_template`
SELECT *
FROM `tmp_currency_token`;


-- ============================================================================
-- LOWER BLACKROCK SPIRE CURIO
-- ============================================================================


UPDATE `tmp_currency_token`
SET
    `entry`          = @LBRS_CURIO,
    `class`          = 15,
    `subclass`       = 0,
    `name`           = 'Lower Blackrock Spire Curio',
    `Quality`        = 4,
    `area`           = 0,
    `Map`            = 0,
    `Flags`          = 2048,
    `FlagsExtra`     = 0,
    `BuyCount`       = 1,
    `BuyPrice`       = 0,
    `BagFamily`      = 0,
    `SellPrice`      = 0,
    `InventoryType`  = 0,
    `displayid`      = 3347,
    `AllowableClass` = -1,
    `AllowableRace`  = -1,
    `ItemLevel`      = 1,
    `RequiredLevel`  = 1,
    `maxcount`       = 0,
    `stackable`      = 200,
    `bonding`        = 1,
    `description`    = 'A dark scale recovered from the lower strongholds of Blackrock Spire. A collector of rare artifacts might find value in it.',
    `VerifiedBuild`  = 0;

INSERT INTO `item_template`
SELECT *
FROM `tmp_currency_token`;


-- ============================================================================
-- UPPER BLACKROCK SPIRE CURIO
-- ============================================================================


UPDATE `tmp_currency_token`
SET
    `entry`          = @UBRS_CURIO,
    `class`          = 15,
    `subclass`       = 0,
    `name`           = 'Upper Blackrock Spire Curio',
    `Quality`        = 4,
    `area`           = 0,
    `Map`            = 0,
    `Flags`          = 2048,
    `FlagsExtra`     = 0,
    `BuyCount`       = 1,
    `BuyPrice`       = 0,
    `BagFamily`      = 0,
    `SellPrice`      = 0,
    `InventoryType`  = 0,
    `displayid`      = 21363,
    `AllowableClass` = -1,
    `AllowableRace`  = -1,
    `ItemLevel`      = 1,
    `RequiredLevel`  = 1,
    `maxcount`       = 0,
    `stackable`      = 200,
    `bonding`        = 1,
    `description`    = 'A hardened dragon scale recovered from the upper halls of Blackrock Spire. A collector of rare artifacts might find value in it.',
    `VerifiedBuild`  = 0;

INSERT INTO `item_template`
SELECT *
FROM `tmp_currency_token`;


-- ============================================================================
-- DIRE MAUL - EAST CURIO
-- ============================================================================


UPDATE `tmp_currency_token`
SET
    `entry`          = @DM_EAST_CURIO,
    `class`          = 15,
    `subclass`       = 0,
    `name`           = 'Dire Maul East Curio',
    `Quality`        = 4,
    `area`           = 0,
    `Map`            = 0,
    `Flags`          = 2048,
    `FlagsExtra`     = 0,
    `BuyCount`       = 1,
    `BuyPrice`       = 0,
    `BagFamily`      = 0,
    `SellPrice`      = 0,
    `InventoryType`  = 0,
    `displayid`      = 1217,
    `AllowableClass` = -1,
    `AllowableRace`  = -1,
    `ItemLevel`      = 1,
    `RequiredLevel`  = 1,
    `maxcount`       = 0,
    `stackable`      = 200,
    `bonding`        = 1,
    `description`    = 'A green crystal overgrown with roots from the eastern gardens of Dire Maul. A collector of rare artifacts might find value in it.',
    `VerifiedBuild`  = 0;

INSERT INTO `item_template`
SELECT *
FROM `tmp_currency_token`;


-- ============================================================================
-- DIRE MAUL - WEST CURIO
-- ============================================================================


UPDATE `tmp_currency_token`
SET
    `entry`          = @DM_WEST_CURIO,
    `class`          = 15,
    `subclass`       = 0,
    `name`           = 'Dire Maul West Curio',
    `Quality`        = 4,
    `area`           = 0,
    `Map`            = 0,
    `Flags`          = 2048,
    `FlagsExtra`     = 0,
    `BuyCount`       = 1,
    `BuyPrice`       = 0,
    `BagFamily`      = 0,
    `SellPrice`      = 0,
    `InventoryType`  = 0,
    `displayid`      = 3231,
    `AllowableClass` = -1,
    `AllowableRace`  = -1,
    `ItemLevel`      = 1,
    `RequiredLevel`  = 1,
    `maxcount`       = 0,
    `stackable`      = 200,
    `bonding`        = 1,
    `description`    = 'An arcane orb that still hums with the fading magic of Eldre''Thalas. A collector of rare artifacts might find value in it.',
    `VerifiedBuild`  = 0;

INSERT INTO `item_template`
SELECT *
FROM `tmp_currency_token`;


-- ============================================================================
-- DIRE MAUL - NORTH CURIO
-- ============================================================================


UPDATE `tmp_currency_token`
SET
    `entry`          = @DM_NORTH_CURIO,
    `class`          = 15,
    `subclass`       = 0,
    `name`           = 'Dire Maul North Curio',
    `Quality`        = 4,
    `area`           = 0,
    `Map`            = 0,
    `Flags`          = 2048,
    `FlagsExtra`     = 0,
    `BuyCount`       = 1,
    `BuyPrice`       = 0,
    `BagFamily`      = 0,
    `SellPrice`      = 0,
    `InventoryType`  = 0,
    `displayid`      = 1274,
    `AllowableClass` = -1,
    `AllowableRace`  = -1,
    `ItemLevel`      = 1,
    `RequiredLevel`  = 1,
    `maxcount`       = 0,
    `stackable`      = 200,
    `bonding`        = 1,
    `description`    = 'A bone trophy claimed from the Gordok halls in northern Dire Maul. A collector of rare artifacts might find value in it.',
    `VerifiedBuild`  = 0;

INSERT INTO `item_template`
SELECT *
FROM `tmp_currency_token`;


-- ============================================================================
-- SCHOLOMANCE CURIO
-- ============================================================================


UPDATE `tmp_currency_token`
SET
    `entry`          = @SCHOLO_CURIO,
    `class`          = 15,
    `subclass`       = 0,
    `name`           = 'Scholomance Curio',
    `Quality`        = 4,
    `area`           = 0,
    `Map`            = 0,
    `Flags`          = 2048,
    `FlagsExtra`     = 0,
    `BuyCount`       = 1,
    `BuyPrice`       = 0,
    `BagFamily`      = 0,
    `SellPrice`      = 0,
    `InventoryType`  = 0,
    `displayid`      = 1155,
    `AllowableClass` = -1,
    `AllowableRace`  = -1,
    `ItemLevel`      = 1,
    `RequiredLevel`  = 1,
    `maxcount`       = 0,
    `stackable`      = 200,
    `bonding`        = 1,
    `description`    = 'A forbidden grimoire recovered from the necromantic halls beneath Caer Darrow. A collector of rare artifacts might find value in it.',
    `VerifiedBuild`  = 0;

INSERT INTO `item_template`
SELECT *
FROM `tmp_currency_token`;


-- ============================================================================
-- STRATHOLME - LIVING QUARTER CURIO
-- ============================================================================


UPDATE `tmp_currency_token`
SET
    `entry`          = @STRAT_LIVE_CURIO,
    `class`          = 15,
    `subclass`       = 0,
    `name`           = 'Stratholme Living Quarter Curio',
    `Quality`        = 4,
    `area`           = 0,
    `Map`            = 0,
    `Flags`          = 2048,
    `FlagsExtra`     = 0,
    `BuyCount`       = 1,
    `BuyPrice`       = 0,
    `BagFamily`      = 0,
    `SellPrice`      = 0,
    `InventoryType`  = 0,
    `displayid`      = 20977,
    `AllowableClass` = -1,
    `AllowableRace`  = -1,
    `ItemLevel`      = 1,
    `RequiredLevel`  = 1,
    `maxcount`       = 0,
    `stackable`      = 200,
    `bonding`        = 1,
    `description`    = 'A crimson gem recovered from the Scarlet stronghold in ruined Stratholme. A collector of rare artifacts might find value in it.',
    `VerifiedBuild`  = 0;

INSERT INTO `item_template`
SELECT *
FROM `tmp_currency_token`;


-- ============================================================================
-- STRATHOLME - UNDEAD QUARTER CURIO
-- ============================================================================


UPDATE `tmp_currency_token`
SET
    `entry`          = @STRAT_UNDEAD_CURIO,
    `class`          = 15,
    `subclass`       = 0,
    `name`           = 'Stratholme Undead Quarter Curio',
    `Quality`        = 4,
    `area`           = 0,
    `Map`            = 0,
    `Flags`          = 2048,
    `FlagsExtra`     = 0,
    `BuyCount`       = 1,
    `BuyPrice`       = 0,
    `BagFamily`      = 0,
    `SellPrice`      = 0,
    `InventoryType`  = 0,
    `displayid`      = 4127,
    `AllowableClass` = -1,
    `AllowableRace`  = -1,
    `ItemLevel`      = 1,
    `RequiredLevel`  = 1,
    `maxcount`       = 0,
    `stackable`      = 200,
    `bonding`        = 1,
    `description`    = 'A cold rune recovered from the Scourge-held streets of Stratholme. A collector of rare artifacts might find value in it.',
    `VerifiedBuild`  = 0;

INSERT INTO `item_template`
SELECT *
FROM `tmp_currency_token`;


-- ============================================================================
-- SPANISH LOCALIZATION (esES)
-- ============================================================================


INSERT INTO `item_template_locale`
(
    `ID`,
    `locale`,
    `Name`,
    `Description`,
    `VerifiedBuild`
)
VALUES

-- Ragefire Chasm
(
    @RFC_CURIO,
    'esES',
    'Curiosidad de Sima Ígnea',
    'Un fragmento chamuscado recuperado de las cavernas ardientes bajo Orgrimmar. Un coleccionista de artefactos extraños podría encontrarle valor.',
    -1
),

-- Wailing Caverns
(
    @WC_CURIO,
    'esES',
    'Curiosidad de las Cuevas de los Lamentos',
    'Una piedra verde que resuena con los sueños atormentados de las Cuevas de los Lamentos. Un coleccionista de artefactos extraños podría encontrarle valor.',
    -1
),

-- The Deadmines
(
    @DEADMINES_CURIO,
    'esES',
    'Curiosidad de las Minas de la Muerte',
    'Un recuerdo deslustrado recuperado del escondite Defias bajo los Páramos de Poniente. Un coleccionista de artefactos extraños podría encontrarle valor.',
    -1
),

-- Shadowfang Keep
(
    @SFK_CURIO,
    'esES',
    'Curiosidad del Castillo de Colmillo Oscuro',
    'Una garra ennegrecida que conserva un rastro de la maldición del Castillo de Colmillo Oscuro. Un coleccionista de artefactos extraños podría encontrarle valor.',
    -1
),

-- Blackfathom Deeps
(
    @BFD_CURIO,
    'esES',
    'Curiosidad de las Cavernas de Brazanegra',
    'Una perla erosionada por la sal, recuperada de las salas sumergidas de las Cavernas de Brazanegra. Un coleccionista de artefactos extraños podría encontrarle valor.',
    -1
),

-- The Stockade
(
    @STOCKADES_CURIO,
    'esES',
    'Curiosidad de las Mazmorras de Ventormenta',
    'Una llave maltrecha recuperada de la prisión bajo Ventormenta. Un coleccionista de artefactos extraños podría encontrarle valor.',
    -1
),

-- Gnomeregan
(
    @GNOMEREGAN_CURIO,
    'esES',
    'Curiosidad de Gnomeregan',
    'Un curioso engranaje rescatado de la maquinaria abandonada de Gnomeregan. Un coleccionista de artefactos extraños podría encontrarle valor.',
    -1
),

-- Razorfen Kraul
(
    @RFK_CURIO,
    'esES',
    'Curiosidad de Horado Rajacieno',
    'Un pequeño ídolo enredado en las antiguas raíces de Horado Rajacieno. Un coleccionista de artefactos extraños podría encontrarle valor.',
    -1
),

-- Scarlet Monastery - Graveyard
(
    @SM_GY_CURIO,
    'esES',
    'Curiosidad del Cementerio Escarlata',
    'Una reliquia funeraria desgastada, recuperada del cementerio del Monasterio Escarlata. Un coleccionista de artefactos extraños podría encontrarle valor.',
    -1
),

-- Scarlet Monastery - Library
(
    @SM_LIB_CURIO,
    'esES',
    'Curiosidad de la Biblioteca Escarlata',
    'Un volumen prohibido tomado de los estantes custodiados de la Biblioteca Escarlata. Un coleccionista de artefactos extraños podría encontrarle valor.',
    -1
),

-- Scarlet Monastery - Armory
(
    @SM_ARM_CURIO,
    'esES',
    'Curiosidad de la Armería Escarlata',
    'Una pieza grabada recuperada de los depósitos de armas de la Armería Escarlata. Un coleccionista de artefactos extraños podría encontrarle valor.',
    -1
),

-- Scarlet Monastery - Cathedral
(
    @SM_CAT_CURIO,
    'esES',
    'Curiosidad de la Catedral Escarlata',
    'Una gema pálida extraída de un relicario de la Catedral Escarlata. Un coleccionista de artefactos extraños podría encontrarle valor.',
    -1
),

-- Razorfen Downs
(
    @RFD_CURIO,
    'esES',
    'Curiosidad de la Zahúrda Rajacieno',
    'Un hueso ritual marcado por el frío antinatural que envuelve la Zahúrda Rajacieno. Un coleccionista de artefactos extraños podría encontrarle valor.',
    -1
),

-- Uldaman
(
    @ULDAMAN_CURIO,
    'esES',
    'Curiosidad de Uldaman',
    'Un fragmento de piedra tallada desenterrado de las antiguas salas de Uldaman. Un coleccionista de artefactos extraños podría encontrarle valor.',
    -1
),

-- Zul'Farrak
(
    @ZF_CURIO,
    'esES',
    'Curiosidad de Zul''Farrak',
    'Un ídolo erosionado por la arena, recuperado de los recintos sagrados de Zul''Farrak. Un coleccionista de artefactos extraños podría encontrarle valor.',
    -1
),

-- Maraudon
(
    @MARAUDON_CURIO,
    'esES',
    'Curiosidad de Maraudon',
    'Un cristal violeta formado entre las antiguas raíces y las cámaras de piedra de Maraudon. Un coleccionista de artefactos extraños podría encontrarle valor.',
    -1
),

-- The Temple of Atal'Hakkar
(
    @ST_CURIO,
    'esES',
    'Curiosidad del Templo Sumergido',
    'Una piedra de color rojo sangre recuperada del santuario sumergido de Atal''Hakkar. Un coleccionista de artefactos extraños podría encontrarle valor.',
    -1
),

-- Blackrock Depths
(
    @BRD_CURIO,
    'esES',
    'Curiosidad de las Profundidades de Roca Negra',
    'Una reliquia rúnica ennegrecida por las forjas de los enanos Hierro Negro. Un coleccionista de artefactos extraños podría encontrarle valor.',
    -1
),

-- Lower Blackrock Spire
(
    @LBRS_CURIO,
    'esES',
    'Curiosidad de la Cumbre de Roca Negra inferior',
    'Una escama oscura recuperada de los bastiones inferiores de la Cumbre de Roca Negra. Un coleccionista de artefactos extraños podría encontrarle valor.',
    -1
),

-- Upper Blackrock Spire
(
    @UBRS_CURIO,
    'esES',
    'Curiosidad de la Cumbre de Roca Negra superior',
    'Una escama de dragón endurecida, recuperada de las salas superiores de la Cumbre de Roca Negra. Un coleccionista de artefactos extraños podría encontrarle valor.',
    -1
),

-- Dire Maul - East
(
    @DM_EAST_CURIO,
    'esES',
    'Curiosidad de La Masacre Este',
    'Un cristal verde cubierto de raíces de los jardines orientales de La Masacre. Un coleccionista de artefactos extraños podría encontrarle valor.',
    -1
),

-- Dire Maul - West
(
    @DM_WEST_CURIO,
    'esES',
    'Curiosidad de La Masacre Oeste',
    'Un orbe arcano que aún vibra con la magia menguante de Eldre''Thalas. Un coleccionista de artefactos extraños podría encontrarle valor.',
    -1
),

-- Dire Maul - North
(
    @DM_NORTH_CURIO,
    'esES',
    'Curiosidad de La Masacre Norte',
    'Un trofeo de hueso obtenido en las salas Gordok del norte de La Masacre. Un coleccionista de artefactos extraños podría encontrarle valor.',
    -1
),

-- Scholomance
(
    @SCHOLO_CURIO,
    'esES',
    'Curiosidad de Scholomance',
    'Un grimorio prohibido recuperado de las salas de nigromancia bajo Castel Darrow. Un coleccionista de artefactos extraños podría encontrarle valor.',
    -1
),

-- Stratholme - Living Quarter
(
    @STRAT_LIVE_CURIO,
    'esES',
    'Curiosidad de Stratholme: sector vivo',
    'Una gema carmesí recuperada del bastión Escarlata de la arruinada Stratholme. Un coleccionista de artefactos extraños podría encontrarle valor.',
    -1
),

-- Stratholme - Undead Quarter
(
    @STRAT_UNDEAD_CURIO,
    'esES',
    'Curiosidad de Stratholme: sector no muerto',
    'Una runa helada recuperada de las calles de Stratholme dominadas por la Plaga. Un coleccionista de artefactos extraños podría encontrarle valor.',
    -1
);


-- ============================================================================
-- CLEANUP
-- ============================================================================

DROP TEMPORARY TABLE IF EXISTS `tmp_currency_token`;

COMMIT;


-- ============================================================================
-- VERIFICATION
-- ============================================================================

SELECT
    `entry`,
    `name`,
    `displayid`,
    `Quality`,
    `stackable`,
    `bonding`,
    `BagFamily`,
    `description`
FROM `item_template`
WHERE `entry` IN (
    @RFC_CURIO,
    @WC_CURIO,
    @DEADMINES_CURIO,
    @SFK_CURIO,
    @BFD_CURIO,
    @STOCKADES_CURIO,
    @GNOMEREGAN_CURIO,
    @RFK_CURIO,
    @SM_GY_CURIO,
    @SM_LIB_CURIO,
    @SM_ARM_CURIO,
    @SM_CAT_CURIO,
    @RFD_CURIO,
    @ULDAMAN_CURIO,
    @ZF_CURIO,
    @MARAUDON_CURIO,
    @ST_CURIO,
    @BRD_CURIO,
    @LBRS_CURIO,
    @UBRS_CURIO,
    @DM_EAST_CURIO,
    @DM_WEST_CURIO,
    @DM_NORTH_CURIO,
    @SCHOLO_CURIO,
    @STRAT_LIVE_CURIO,
    @STRAT_UNDEAD_CURIO
)
ORDER BY `entry`;

SELECT
    `ID`,
    `locale`,
    `Name`,
    `Description`
FROM `item_template_locale`
WHERE `ID` IN (
    @RFC_CURIO,
    @WC_CURIO,
    @DEADMINES_CURIO,
    @SFK_CURIO,
    @BFD_CURIO,
    @STOCKADES_CURIO,
    @GNOMEREGAN_CURIO,
    @RFK_CURIO,
    @SM_GY_CURIO,
    @SM_LIB_CURIO,
    @SM_ARM_CURIO,
    @SM_CAT_CURIO,
    @RFD_CURIO,
    @ULDAMAN_CURIO,
    @ZF_CURIO,
    @MARAUDON_CURIO,
    @ST_CURIO,
    @BRD_CURIO,
    @LBRS_CURIO,
    @UBRS_CURIO,
    @DM_EAST_CURIO,
    @DM_WEST_CURIO,
    @DM_NORTH_CURIO,
    @SCHOLO_CURIO,
    @STRAT_LIVE_CURIO,
    @STRAT_UNDEAD_CURIO
)
ORDER BY `ID`, `locale`;
