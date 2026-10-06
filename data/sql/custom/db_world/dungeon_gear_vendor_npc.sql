USE `acore_world`;

-- dungeon_gear_vendor_npc.sql
-- Adapted from raid_gear_vendor_npc.sql in jgjaraba/azerothcore-setup.
-- Matches dungeon_gear_vendor_item.sql: creature entries 90300-90325.
-- New spawn GUIDs 900010-900035; gossip/text IDs 92100-92125.
-- Uses the same custom Dark Rider display 90100: required in server/client DBC.
-- Inventory/currency/ExtendedCost creation belongs to the companion files/DBC.
-- Apply before dungeon_gear_vendor_item.sql and restart worldserver to load new spawns.
--
-- Coordinates and orientations supplied by the user on 2026-10-01.
-- World map IDs 0/1, template IDs and spawn GUIDs remain unchanged.
-- Reapplying this file replaces the 26 owned spawns at their specified GUIDs;
-- it does not add another spawn at the previous or the new position.
-- It restores the declared templates, dialogue and positions, so later manual
-- edits to those owned records must also be reflected in this file.
--
-- Source snapshot: Grimfeather/azerothcore-wotlk
-- 529b659668bcd8b1cfbf9acc44f40eb6ff830fe1 (game_tele, areatrigger_teleport,
-- creature and Commands/cs_go.cpp); setup main checked 2026-10-01.
-- Target creature spawn column is `id`, as in the current raid SQL.
-- Older base dumps with id1/id2/id3 require the normal core DB updates first.
-- Ranges are free in checked source data; live/custom DB occupancy is unknown.

START TRANSACTION;

-- ============================================================================
-- DARK RIDER DUNGEON VENDORS
-- ============================================================================

SET @DISPLAY_DARK_RIDER := 90100;

-- Creature template IDs
SET @NPC_RFC := 90300;
SET @NPC_WC := 90301;
SET @NPC_DEADMINES := 90302;
SET @NPC_SFK := 90303;
SET @NPC_BFD := 90304;
SET @NPC_STOCKADES := 90305;
SET @NPC_GNOMEREGAN := 90306;
SET @NPC_RFK := 90307;
SET @NPC_SM_GY := 90308;
SET @NPC_SM_LIB := 90309;
SET @NPC_SM_ARM := 90310;
SET @NPC_SM_CAT := 90311;
SET @NPC_RFD := 90312;
SET @NPC_ULDAMAN := 90313;
SET @NPC_ZF := 90314;
SET @NPC_MARAUDON := 90315;
SET @NPC_ST := 90316;
SET @NPC_BRD := 90317;
SET @NPC_LBRS := 90318;
SET @NPC_UBRS := 90319;
SET @NPC_DM_EAST := 90320;
SET @NPC_DM_WEST := 90321;
SET @NPC_DM_NORTH := 90322;
SET @NPC_SCHOLO := 90323;
SET @NPC_STRAT_LIVE := 90324;
SET @NPC_STRAT_UNDEAD := 90325;

-- Gossip menu and text IDs (same ID in the two separate tables)
SET @MENU_RFC := 92100;
SET @MENU_WC := 92101;
SET @MENU_DEADMINES := 92102;
SET @MENU_SFK := 92103;
SET @MENU_BFD := 92104;
SET @MENU_STOCKADES := 92105;
SET @MENU_GNOMEREGAN := 92106;
SET @MENU_RFK := 92107;
SET @MENU_SM_GY := 92108;
SET @MENU_SM_LIB := 92109;
SET @MENU_SM_ARM := 92110;
SET @MENU_SM_CAT := 92111;
SET @MENU_RFD := 92112;
SET @MENU_ULDAMAN := 92113;
SET @MENU_ZF := 92114;
SET @MENU_MARAUDON := 92115;
SET @MENU_ST := 92116;
SET @MENU_BRD := 92117;
SET @MENU_LBRS := 92118;
SET @MENU_UBRS := 92119;
SET @MENU_DM_EAST := 92120;
SET @MENU_DM_WEST := 92121;
SET @MENU_DM_NORTH := 92122;
SET @MENU_SCHOLO := 92123;
SET @MENU_STRAT_LIVE := 92124;
SET @MENU_STRAT_UNDEAD := 92125;

-- ============================================================================
-- CLEAN PREVIOUS VERSION
-- ============================================================================

DELETE FROM `creature_template_locale`
WHERE `entry` IN (@NPC_RFC, @NPC_WC, @NPC_DEADMINES, @NPC_SFK, @NPC_BFD, @NPC_STOCKADES, @NPC_GNOMEREGAN, @NPC_RFK, @NPC_SM_GY, @NPC_SM_LIB, @NPC_SM_ARM, @NPC_SM_CAT, @NPC_RFD, @NPC_ULDAMAN, @NPC_ZF, @NPC_MARAUDON, @NPC_ST, @NPC_BRD, @NPC_LBRS, @NPC_UBRS, @NPC_DM_EAST, @NPC_DM_WEST, @NPC_DM_NORTH, @NPC_SCHOLO, @NPC_STRAT_LIVE, @NPC_STRAT_UNDEAD);

DELETE FROM `creature_template_model`
WHERE `CreatureID` IN (@NPC_RFC, @NPC_WC, @NPC_DEADMINES, @NPC_SFK, @NPC_BFD, @NPC_STOCKADES, @NPC_GNOMEREGAN, @NPC_RFK, @NPC_SM_GY, @NPC_SM_LIB, @NPC_SM_ARM, @NPC_SM_CAT, @NPC_RFD, @NPC_ULDAMAN, @NPC_ZF, @NPC_MARAUDON, @NPC_ST, @NPC_BRD, @NPC_LBRS, @NPC_UBRS, @NPC_DM_EAST, @NPC_DM_WEST, @NPC_DM_NORTH, @NPC_SCHOLO, @NPC_STRAT_LIVE, @NPC_STRAT_UNDEAD);

DELETE FROM `creature_template`
WHERE `entry` IN (@NPC_RFC, @NPC_WC, @NPC_DEADMINES, @NPC_SFK, @NPC_BFD, @NPC_STOCKADES, @NPC_GNOMEREGAN, @NPC_RFK, @NPC_SM_GY, @NPC_SM_LIB, @NPC_SM_ARM, @NPC_SM_CAT, @NPC_RFD, @NPC_ULDAMAN, @NPC_ZF, @NPC_MARAUDON, @NPC_ST, @NPC_BRD, @NPC_LBRS, @NPC_UBRS, @NPC_DM_EAST, @NPC_DM_WEST, @NPC_DM_NORTH, @NPC_SCHOLO, @NPC_STRAT_LIVE, @NPC_STRAT_UNDEAD);

-- ============================================================================
-- CREATURE TEMPLATES
-- ============================================================================
-- Same template behavior as raid vendors: neutral faction 35, level 60,
-- PassiveAI, non-attackable (unit_flags 2), stationary, no loot or money.
-- Gossip/repair flags and mounted interaction are enabled below.
INSERT INTO `creature_template`
(
    `entry`,
    `name`,
    `subname`,
    `IconName`,
    `minlevel`,
    `maxlevel`,
    `exp`,
    `faction`,
    `npcflag`,
    `speed_walk`,
    `speed_run`,
    `speed_swim`,
    `speed_flight`,
    `detection_range`,
    `rank`,
    `dmgschool`,
    `BaseAttackTime`,
    `RangeAttackTime`,
    `BaseVariance`,
    `RangeVariance`,
    `unit_class`,
    `unit_flags`,
    `unit_flags2`,
    `dynamicflags`,
    `family`,
    `type`,
    `type_flags`,
    `lootid`,
    `pickpocketloot`,
    `skinloot`,
    `PetSpellDataId`,
    `VehicleId`,
    `mingold`,
    `maxgold`,
    `AIName`,
    `MovementType`,
    `HoverHeight`,
    `HealthModifier`,
    `ManaModifier`,
    `ArmorModifier`,
    `DamageModifier`,
    `ExperienceModifier`,
    `RacialLeader`,
    `movementId`,
    `RegenHealth`,
    `CreatureImmunitiesId`,
    `flags_extra`,
    `ScriptName`,
    `VerifiedBuild`
)
VALUES

-- Ragefire Chasm
(
    @NPC_RFC,
    'Dark Rider',
    'Collector of Ragefire Relics',
    'Buy',
    60,
    60,
    0,
    35,
    128,
    1,
    1.14286,
    1,
    1,
    20,
    0,
    0,
    2000,
    2000,
    1,
    1,
    1,
    2,
    0,
    0,
    0,
    7,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    'PassiveAI',
    0,
    1,
    1,
    1,
    1,
    1,
    1,
    0,
    0,
    1,
    0,
    2,
    '',
    -1
),

-- Wailing Caverns
(
    @NPC_WC,
    'Dark Rider',
    'Collector of Dreambound Relics',
    'Buy',
    60,
    60,
    0,
    35,
    128,
    1,
    1.14286,
    1,
    1,
    20,
    0,
    0,
    2000,
    2000,
    1,
    1,
    1,
    2,
    0,
    0,
    0,
    7,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    'PassiveAI',
    0,
    1,
    1,
    1,
    1,
    1,
    1,
    0,
    0,
    1,
    0,
    2,
    '',
    -1
),

-- The Deadmines
(
    @NPC_DEADMINES,
    'Dark Rider',
    'Collector of Defias Relics',
    'Buy',
    60,
    60,
    0,
    35,
    128,
    1,
    1.14286,
    1,
    1,
    20,
    0,
    0,
    2000,
    2000,
    1,
    1,
    1,
    2,
    0,
    0,
    0,
    7,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    'PassiveAI',
    0,
    1,
    1,
    1,
    1,
    1,
    1,
    0,
    0,
    1,
    0,
    2,
    '',
    -1
),

-- Shadowfang Keep
(
    @NPC_SFK,
    'Dark Rider',
    'Collector of Cursed Relics',
    'Buy',
    60,
    60,
    0,
    35,
    128,
    1,
    1.14286,
    1,
    1,
    20,
    0,
    0,
    2000,
    2000,
    1,
    1,
    1,
    2,
    0,
    0,
    0,
    7,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    'PassiveAI',
    0,
    1,
    1,
    1,
    1,
    1,
    1,
    0,
    0,
    1,
    0,
    2,
    '',
    -1
),

-- Blackfathom Deeps
(
    @NPC_BFD,
    'Dark Rider',
    'Collector of Abyssal Relics',
    'Buy',
    60,
    60,
    0,
    35,
    128,
    1,
    1.14286,
    1,
    1,
    20,
    0,
    0,
    2000,
    2000,
    1,
    1,
    1,
    2,
    0,
    0,
    0,
    7,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    'PassiveAI',
    0,
    1,
    1,
    1,
    1,
    1,
    1,
    0,
    0,
    1,
    0,
    2,
    '',
    -1
),

-- The Stockade
(
    @NPC_STOCKADES,
    'Dark Rider',
    'Collector of Confiscated Relics',
    'Buy',
    60,
    60,
    0,
    35,
    128,
    1,
    1.14286,
    1,
    1,
    20,
    0,
    0,
    2000,
    2000,
    1,
    1,
    1,
    2,
    0,
    0,
    0,
    7,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    'PassiveAI',
    0,
    1,
    1,
    1,
    1,
    1,
    1,
    0,
    0,
    1,
    0,
    2,
    '',
    -1
),

-- Gnomeregan
(
    @NPC_GNOMEREGAN,
    'Dark Rider',
    'Collector of Gnomish Relics',
    'Buy',
    60,
    60,
    0,
    35,
    128,
    1,
    1.14286,
    1,
    1,
    20,
    0,
    0,
    2000,
    2000,
    1,
    1,
    1,
    2,
    0,
    0,
    0,
    7,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    'PassiveAI',
    0,
    1,
    1,
    1,
    1,
    1,
    1,
    0,
    0,
    1,
    0,
    2,
    '',
    -1
),

-- Razorfen Kraul
(
    @NPC_RFK,
    'Dark Rider',
    'Collector of Quilboar Relics',
    'Buy',
    60,
    60,
    0,
    35,
    128,
    1,
    1.14286,
    1,
    1,
    20,
    0,
    0,
    2000,
    2000,
    1,
    1,
    1,
    2,
    0,
    0,
    0,
    7,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    'PassiveAI',
    0,
    1,
    1,
    1,
    1,
    1,
    1,
    0,
    0,
    1,
    0,
    2,
    '',
    -1
),

-- Scarlet Monastery - Graveyard
(
    @NPC_SM_GY,
    'Dark Rider',
    'Collector of Scarlet Graveyard Relics',
    'Buy',
    60,
    60,
    0,
    35,
    128,
    1,
    1.14286,
    1,
    1,
    20,
    0,
    0,
    2000,
    2000,
    1,
    1,
    1,
    2,
    0,
    0,
    0,
    7,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    'PassiveAI',
    0,
    1,
    1,
    1,
    1,
    1,
    1,
    0,
    0,
    1,
    0,
    2,
    '',
    -1
),

-- Scarlet Monastery - Library
(
    @NPC_SM_LIB,
    'Dark Rider',
    'Collector of Scarlet Library Relics',
    'Buy',
    60,
    60,
    0,
    35,
    128,
    1,
    1.14286,
    1,
    1,
    20,
    0,
    0,
    2000,
    2000,
    1,
    1,
    1,
    2,
    0,
    0,
    0,
    7,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    'PassiveAI',
    0,
    1,
    1,
    1,
    1,
    1,
    1,
    0,
    0,
    1,
    0,
    2,
    '',
    -1
),

-- Scarlet Monastery - Armory
(
    @NPC_SM_ARM,
    'Dark Rider',
    'Collector of Scarlet Armory Relics',
    'Buy',
    60,
    60,
    0,
    35,
    128,
    1,
    1.14286,
    1,
    1,
    20,
    0,
    0,
    2000,
    2000,
    1,
    1,
    1,
    2,
    0,
    0,
    0,
    7,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    'PassiveAI',
    0,
    1,
    1,
    1,
    1,
    1,
    1,
    0,
    0,
    1,
    0,
    2,
    '',
    -1
),

-- Scarlet Monastery - Cathedral
(
    @NPC_SM_CAT,
    'Dark Rider',
    'Collector of Scarlet Cathedral Relics',
    'Buy',
    60,
    60,
    0,
    35,
    128,
    1,
    1.14286,
    1,
    1,
    20,
    0,
    0,
    2000,
    2000,
    1,
    1,
    1,
    2,
    0,
    0,
    0,
    7,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    'PassiveAI',
    0,
    1,
    1,
    1,
    1,
    1,
    1,
    0,
    0,
    1,
    0,
    2,
    '',
    -1
),

-- Razorfen Downs
(
    @NPC_RFD,
    'Dark Rider',
    'Collector of Deathbound Relics',
    'Buy',
    60,
    60,
    0,
    35,
    128,
    1,
    1.14286,
    1,
    1,
    20,
    0,
    0,
    2000,
    2000,
    1,
    1,
    1,
    2,
    0,
    0,
    0,
    7,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    'PassiveAI',
    0,
    1,
    1,
    1,
    1,
    1,
    1,
    0,
    0,
    1,
    0,
    2,
    '',
    -1
),

-- Uldaman
(
    @NPC_ULDAMAN,
    'Dark Rider',
    'Collector of Titan Relics',
    'Buy',
    60,
    60,
    0,
    35,
    128,
    1,
    1.14286,
    1,
    1,
    20,
    0,
    0,
    2000,
    2000,
    1,
    1,
    1,
    2,
    0,
    0,
    0,
    7,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    'PassiveAI',
    0,
    1,
    1,
    1,
    1,
    1,
    1,
    0,
    0,
    1,
    0,
    2,
    '',
    -1
),

-- Zul'Farrak
(
    @NPC_ZF,
    'Dark Rider',
    'Collector of Sandfury Relics',
    'Buy',
    60,
    60,
    0,
    35,
    128,
    1,
    1.14286,
    1,
    1,
    20,
    0,
    0,
    2000,
    2000,
    1,
    1,
    1,
    2,
    0,
    0,
    0,
    7,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    'PassiveAI',
    0,
    1,
    1,
    1,
    1,
    1,
    1,
    0,
    0,
    1,
    0,
    2,
    '',
    -1
),

-- Maraudon
(
    @NPC_MARAUDON,
    'Dark Rider',
    'Collector of Theradras Relics',
    'Buy',
    60,
    60,
    0,
    35,
    128,
    1,
    1.14286,
    1,
    1,
    20,
    0,
    0,
    2000,
    2000,
    1,
    1,
    1,
    2,
    0,
    0,
    0,
    7,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    'PassiveAI',
    0,
    1,
    1,
    1,
    1,
    1,
    1,
    0,
    0,
    1,
    0,
    2,
    '',
    -1
),

-- The Temple of Atal'Hakkar
(
    @NPC_ST,
    'Dark Rider',
    'Collector of Atal''ai Relics',
    'Buy',
    60,
    60,
    0,
    35,
    128,
    1,
    1.14286,
    1,
    1,
    20,
    0,
    0,
    2000,
    2000,
    1,
    1,
    1,
    2,
    0,
    0,
    0,
    7,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    'PassiveAI',
    0,
    1,
    1,
    1,
    1,
    1,
    1,
    0,
    0,
    1,
    0,
    2,
    '',
    -1
),

-- Blackrock Depths
(
    @NPC_BRD,
    'Dark Rider',
    'Collector of Dark Iron Relics',
    'Buy',
    60,
    60,
    0,
    35,
    128,
    1,
    1.14286,
    1,
    1,
    20,
    0,
    0,
    2000,
    2000,
    1,
    1,
    1,
    2,
    0,
    0,
    0,
    7,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    'PassiveAI',
    0,
    1,
    1,
    1,
    1,
    1,
    1,
    0,
    0,
    1,
    0,
    2,
    '',
    -1
),

-- Lower Blackrock Spire
(
    @NPC_LBRS,
    'Dark Rider',
    'Collector of Lower Spire Relics',
    'Buy',
    60,
    60,
    0,
    35,
    128,
    1,
    1.14286,
    1,
    1,
    20,
    0,
    0,
    2000,
    2000,
    1,
    1,
    1,
    2,
    0,
    0,
    0,
    7,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    'PassiveAI',
    0,
    1,
    1,
    1,
    1,
    1,
    1,
    0,
    0,
    1,
    0,
    2,
    '',
    -1
),

-- Upper Blackrock Spire
(
    @NPC_UBRS,
    'Dark Rider',
    'Collector of Upper Spire Relics',
    'Buy',
    60,
    60,
    0,
    35,
    128,
    1,
    1.14286,
    1,
    1,
    20,
    0,
    0,
    2000,
    2000,
    1,
    1,
    1,
    2,
    0,
    0,
    0,
    7,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    'PassiveAI',
    0,
    1,
    1,
    1,
    1,
    1,
    1,
    0,
    0,
    1,
    0,
    2,
    '',
    -1
),

-- Dire Maul - East
(
    @NPC_DM_EAST,
    'Dark Rider',
    'Collector of Warpwood Relics',
    'Buy',
    60,
    60,
    0,
    35,
    128,
    1,
    1.14286,
    1,
    1,
    20,
    0,
    0,
    2000,
    2000,
    1,
    1,
    1,
    2,
    0,
    0,
    0,
    7,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    'PassiveAI',
    0,
    1,
    1,
    1,
    1,
    1,
    1,
    0,
    0,
    1,
    0,
    2,
    '',
    -1
),

-- Dire Maul - West
(
    @NPC_DM_WEST,
    'Dark Rider',
    'Collector of Shen''dralar Relics',
    'Buy',
    60,
    60,
    0,
    35,
    128,
    1,
    1.14286,
    1,
    1,
    20,
    0,
    0,
    2000,
    2000,
    1,
    1,
    1,
    2,
    0,
    0,
    0,
    7,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    'PassiveAI',
    0,
    1,
    1,
    1,
    1,
    1,
    1,
    0,
    0,
    1,
    0,
    2,
    '',
    -1
),

-- Dire Maul - North
(
    @NPC_DM_NORTH,
    'Dark Rider',
    'Collector of Gordok Relics',
    'Buy',
    60,
    60,
    0,
    35,
    128,
    1,
    1.14286,
    1,
    1,
    20,
    0,
    0,
    2000,
    2000,
    1,
    1,
    1,
    2,
    0,
    0,
    0,
    7,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    'PassiveAI',
    0,
    1,
    1,
    1,
    1,
    1,
    1,
    0,
    0,
    1,
    0,
    2,
    '',
    -1
),

-- Scholomance
(
    @NPC_SCHOLO,
    'Dark Rider',
    'Collector of Necromantic Relics',
    'Buy',
    60,
    60,
    0,
    35,
    128,
    1,
    1.14286,
    1,
    1,
    20,
    0,
    0,
    2000,
    2000,
    1,
    1,
    1,
    2,
    0,
    0,
    0,
    7,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    'PassiveAI',
    0,
    1,
    1,
    1,
    1,
    1,
    1,
    0,
    0,
    1,
    0,
    2,
    '',
    -1
),

-- Stratholme - Living Quarter
(
    @NPC_STRAT_LIVE,
    'Dark Rider',
    'Collector of Scarlet Bastion Relics',
    'Buy',
    60,
    60,
    0,
    35,
    128,
    1,
    1.14286,
    1,
    1,
    20,
    0,
    0,
    2000,
    2000,
    1,
    1,
    1,
    2,
    0,
    0,
    0,
    7,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    'PassiveAI',
    0,
    1,
    1,
    1,
    1,
    1,
    1,
    0,
    0,
    1,
    0,
    2,
    '',
    -1
),

-- Stratholme - Undead Quarter
(
    @NPC_STRAT_UNDEAD,
    'Dark Rider',
    'Collector of the Baron''s Relics',
    'Buy',
    60,
    60,
    0,
    35,
    128,
    1,
    1.14286,
    1,
    1,
    20,
    0,
    0,
    2000,
    2000,
    1,
    1,
    1,
    2,
    0,
    0,
    0,
    7,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    'PassiveAI',
    0,
    1,
    1,
    1,
    1,
    1,
    1,
    0,
    0,
    1,
    0,
    2,
    '',
    -1
);

-- ============================================================================
-- MODEL
-- ============================================================================

INSERT INTO `creature_template_model`
(`CreatureID`, `Idx`, `CreatureDisplayID`, `DisplayScale`, `Probability`, `VerifiedBuild`)
VALUES
    (@NPC_RFC, 0, @DISPLAY_DARK_RIDER, 1, 1, 0),
    (@NPC_WC, 0, @DISPLAY_DARK_RIDER, 1, 1, 0),
    (@NPC_DEADMINES, 0, @DISPLAY_DARK_RIDER, 1, 1, 0),
    (@NPC_SFK, 0, @DISPLAY_DARK_RIDER, 1, 1, 0),
    (@NPC_BFD, 0, @DISPLAY_DARK_RIDER, 1, 1, 0),
    (@NPC_STOCKADES, 0, @DISPLAY_DARK_RIDER, 1, 1, 0),
    (@NPC_GNOMEREGAN, 0, @DISPLAY_DARK_RIDER, 1, 1, 0),
    (@NPC_RFK, 0, @DISPLAY_DARK_RIDER, 1, 1, 0),
    (@NPC_SM_GY, 0, @DISPLAY_DARK_RIDER, 1, 1, 0),
    (@NPC_SM_LIB, 0, @DISPLAY_DARK_RIDER, 1, 1, 0),
    (@NPC_SM_ARM, 0, @DISPLAY_DARK_RIDER, 1, 1, 0),
    (@NPC_SM_CAT, 0, @DISPLAY_DARK_RIDER, 1, 1, 0),
    (@NPC_RFD, 0, @DISPLAY_DARK_RIDER, 1, 1, 0),
    (@NPC_ULDAMAN, 0, @DISPLAY_DARK_RIDER, 1, 1, 0),
    (@NPC_ZF, 0, @DISPLAY_DARK_RIDER, 1, 1, 0),
    (@NPC_MARAUDON, 0, @DISPLAY_DARK_RIDER, 1, 1, 0),
    (@NPC_ST, 0, @DISPLAY_DARK_RIDER, 1, 1, 0),
    (@NPC_BRD, 0, @DISPLAY_DARK_RIDER, 1, 1, 0),
    (@NPC_LBRS, 0, @DISPLAY_DARK_RIDER, 1, 1, 0),
    (@NPC_UBRS, 0, @DISPLAY_DARK_RIDER, 1, 1, 0),
    (@NPC_DM_EAST, 0, @DISPLAY_DARK_RIDER, 1, 1, 0),
    (@NPC_DM_WEST, 0, @DISPLAY_DARK_RIDER, 1, 1, 0),
    (@NPC_DM_NORTH, 0, @DISPLAY_DARK_RIDER, 1, 1, 0),
    (@NPC_SCHOLO, 0, @DISPLAY_DARK_RIDER, 1, 1, 0),
    (@NPC_STRAT_LIVE, 0, @DISPLAY_DARK_RIDER, 1, 1, 0),
    (@NPC_STRAT_UNDEAD, 0, @DISPLAY_DARK_RIDER, 1, 1, 0);

-- ============================================================================
-- SPANISH LOCALIZATION
-- ============================================================================

INSERT INTO `creature_template_locale`
(`entry`, `locale`, `Name`, `Title`, `VerifiedBuild`)
VALUES
    (@NPC_RFC, 'esES', 'Jinete Oscuro', 'Coleccionista de reliquias ígneas', -1),
    (@NPC_WC, 'esES', 'Jinete Oscuro', 'Coleccionista de reliquias del Sueño', -1),
    (@NPC_DEADMINES, 'esES', 'Jinete Oscuro', 'Coleccionista de reliquias Defias', -1),
    (@NPC_SFK, 'esES', 'Jinete Oscuro', 'Coleccionista de reliquias malditas', -1),
    (@NPC_BFD, 'esES', 'Jinete Oscuro', 'Coleccionista de reliquias abisales', -1),
    (@NPC_STOCKADES, 'esES', 'Jinete Oscuro', 'Coleccionista de reliquias confiscadas', -1),
    (@NPC_GNOMEREGAN, 'esES', 'Jinete Oscuro', 'Coleccionista de reliquias gnómicas', -1),
    (@NPC_RFK, 'esES', 'Jinete Oscuro', 'Coleccionista de reliquias jabaespín', -1),
    (@NPC_SM_GY, 'esES', 'Jinete Oscuro', 'Coleccionista de reliquias del Cementerio', -1),
    (@NPC_SM_LIB, 'esES', 'Jinete Oscuro', 'Coleccionista de reliquias de la Biblioteca', -1),
    (@NPC_SM_ARM, 'esES', 'Jinete Oscuro', 'Coleccionista de reliquias de la Armería', -1),
    (@NPC_SM_CAT, 'esES', 'Jinete Oscuro', 'Coleccionista de reliquias de la Catedral', -1),
    (@NPC_RFD, 'esES', 'Jinete Oscuro', 'Coleccionista de reliquias de la Muerte', -1),
    (@NPC_ULDAMAN, 'esES', 'Jinete Oscuro', 'Coleccionista de reliquias titánicas', -1),
    (@NPC_ZF, 'esES', 'Jinete Oscuro', 'Coleccionista de reliquias Furiarena', -1),
    (@NPC_MARAUDON, 'esES', 'Jinete Oscuro', 'Coleccionista de reliquias de Theradras', -1),
    (@NPC_ST, 'esES', 'Jinete Oscuro', 'Coleccionista de reliquias Atal''ai', -1),
    (@NPC_BRD, 'esES', 'Jinete Oscuro', 'Coleccionista de reliquias Hierro Negro', -1),
    (@NPC_LBRS, 'esES', 'Jinete Oscuro', 'Coleccionista de reliquias de la Cumbre inferior', -1),
    (@NPC_UBRS, 'esES', 'Jinete Oscuro', 'Coleccionista de reliquias de la Cumbre superior', -1),
    (@NPC_DM_EAST, 'esES', 'Jinete Oscuro', 'Coleccionista de reliquias de La Masacre Este', -1),
    (@NPC_DM_WEST, 'esES', 'Jinete Oscuro', 'Coleccionista de reliquias de La Masacre Oeste', -1),
    (@NPC_DM_NORTH, 'esES', 'Jinete Oscuro', 'Coleccionista de reliquias de La Masacre Norte', -1),
    (@NPC_SCHOLO, 'esES', 'Jinete Oscuro', 'Coleccionista de reliquias nigrománticas', -1),
    (@NPC_STRAT_LIVE, 'esES', 'Jinete Oscuro', 'Coleccionista de reliquias del Bastión Escarlata', -1),
    (@NPC_STRAT_UNDEAD, 'esES', 'Jinete Oscuro', 'Coleccionista de reliquias del Barón', -1);

-- ============================================================================
-- GOSSIP MENU
-- ============================================================================

UPDATE `creature_template`
SET `npcflag` = 129,
    `gossip_menu_id` = CASE `entry`
        WHEN @NPC_RFC THEN @MENU_RFC
        WHEN @NPC_WC THEN @MENU_WC
        WHEN @NPC_DEADMINES THEN @MENU_DEADMINES
        WHEN @NPC_SFK THEN @MENU_SFK
        WHEN @NPC_BFD THEN @MENU_BFD
        WHEN @NPC_STOCKADES THEN @MENU_STOCKADES
        WHEN @NPC_GNOMEREGAN THEN @MENU_GNOMEREGAN
        WHEN @NPC_RFK THEN @MENU_RFK
        WHEN @NPC_SM_GY THEN @MENU_SM_GY
        WHEN @NPC_SM_LIB THEN @MENU_SM_LIB
        WHEN @NPC_SM_ARM THEN @MENU_SM_ARM
        WHEN @NPC_SM_CAT THEN @MENU_SM_CAT
        WHEN @NPC_RFD THEN @MENU_RFD
        WHEN @NPC_ULDAMAN THEN @MENU_ULDAMAN
        WHEN @NPC_ZF THEN @MENU_ZF
        WHEN @NPC_MARAUDON THEN @MENU_MARAUDON
        WHEN @NPC_ST THEN @MENU_ST
        WHEN @NPC_BRD THEN @MENU_BRD
        WHEN @NPC_LBRS THEN @MENU_LBRS
        WHEN @NPC_UBRS THEN @MENU_UBRS
        WHEN @NPC_DM_EAST THEN @MENU_DM_EAST
        WHEN @NPC_DM_WEST THEN @MENU_DM_WEST
        WHEN @NPC_DM_NORTH THEN @MENU_DM_NORTH
        WHEN @NPC_SCHOLO THEN @MENU_SCHOLO
        WHEN @NPC_STRAT_LIVE THEN @MENU_STRAT_LIVE
        WHEN @NPC_STRAT_UNDEAD THEN @MENU_STRAT_UNDEAD
    END
WHERE `entry` IN (@NPC_RFC, @NPC_WC, @NPC_DEADMINES, @NPC_SFK, @NPC_BFD, @NPC_STOCKADES, @NPC_GNOMEREGAN, @NPC_RFK, @NPC_SM_GY, @NPC_SM_LIB, @NPC_SM_ARM, @NPC_SM_CAT, @NPC_RFD, @NPC_ULDAMAN, @NPC_ZF, @NPC_MARAUDON, @NPC_ST, @NPC_BRD, @NPC_LBRS, @NPC_UBRS, @NPC_DM_EAST, @NPC_DM_WEST, @NPC_DM_NORTH, @NPC_SCHOLO, @NPC_STRAT_LIVE, @NPC_STRAT_UNDEAD);

DELETE FROM `gossip_menu_option_locale`
WHERE `MenuID` IN (@MENU_RFC, @MENU_WC, @MENU_DEADMINES, @MENU_SFK, @MENU_BFD, @MENU_STOCKADES, @MENU_GNOMEREGAN, @MENU_RFK, @MENU_SM_GY, @MENU_SM_LIB, @MENU_SM_ARM, @MENU_SM_CAT, @MENU_RFD, @MENU_ULDAMAN, @MENU_ZF, @MENU_MARAUDON, @MENU_ST, @MENU_BRD, @MENU_LBRS, @MENU_UBRS, @MENU_DM_EAST, @MENU_DM_WEST, @MENU_DM_NORTH, @MENU_SCHOLO, @MENU_STRAT_LIVE, @MENU_STRAT_UNDEAD);

DELETE FROM `gossip_menu_option`
WHERE `MenuID` IN (@MENU_RFC, @MENU_WC, @MENU_DEADMINES, @MENU_SFK, @MENU_BFD, @MENU_STOCKADES, @MENU_GNOMEREGAN, @MENU_RFK, @MENU_SM_GY, @MENU_SM_LIB, @MENU_SM_ARM, @MENU_SM_CAT, @MENU_RFD, @MENU_ULDAMAN, @MENU_ZF, @MENU_MARAUDON, @MENU_ST, @MENU_BRD, @MENU_LBRS, @MENU_UBRS, @MENU_DM_EAST, @MENU_DM_WEST, @MENU_DM_NORTH, @MENU_SCHOLO, @MENU_STRAT_LIVE, @MENU_STRAT_UNDEAD);

DELETE FROM `gossip_menu`
WHERE `MenuID` IN (@MENU_RFC, @MENU_WC, @MENU_DEADMINES, @MENU_SFK, @MENU_BFD, @MENU_STOCKADES, @MENU_GNOMEREGAN, @MENU_RFK, @MENU_SM_GY, @MENU_SM_LIB, @MENU_SM_ARM, @MENU_SM_CAT, @MENU_RFD, @MENU_ULDAMAN, @MENU_ZF, @MENU_MARAUDON, @MENU_ST, @MENU_BRD, @MENU_LBRS, @MENU_UBRS, @MENU_DM_EAST, @MENU_DM_WEST, @MENU_DM_NORTH, @MENU_SCHOLO, @MENU_STRAT_LIVE, @MENU_STRAT_UNDEAD);

DELETE FROM `npc_text_locale`
WHERE `ID` IN (@MENU_RFC, @MENU_WC, @MENU_DEADMINES, @MENU_SFK, @MENU_BFD, @MENU_STOCKADES, @MENU_GNOMEREGAN, @MENU_RFK, @MENU_SM_GY, @MENU_SM_LIB, @MENU_SM_ARM, @MENU_SM_CAT, @MENU_RFD, @MENU_ULDAMAN, @MENU_ZF, @MENU_MARAUDON, @MENU_ST, @MENU_BRD, @MENU_LBRS, @MENU_UBRS, @MENU_DM_EAST, @MENU_DM_WEST, @MENU_DM_NORTH, @MENU_SCHOLO, @MENU_STRAT_LIVE, @MENU_STRAT_UNDEAD);

DELETE FROM `npc_text`
WHERE `ID` IN (@MENU_RFC, @MENU_WC, @MENU_DEADMINES, @MENU_SFK, @MENU_BFD, @MENU_STOCKADES, @MENU_GNOMEREGAN, @MENU_RFK, @MENU_SM_GY, @MENU_SM_LIB, @MENU_SM_ARM, @MENU_SM_CAT, @MENU_RFD, @MENU_ULDAMAN, @MENU_ZF, @MENU_MARAUDON, @MENU_ST, @MENU_BRD, @MENU_LBRS, @MENU_UBRS, @MENU_DM_EAST, @MENU_DM_WEST, @MENU_DM_NORTH, @MENU_SCHOLO, @MENU_STRAT_LIVE, @MENU_STRAT_UNDEAD);

INSERT INTO `npc_text`
(`ID`, `text0_0`, `text0_1`, `BroadcastTextID0`, `lang0`, `Probability0`, `em0_0`, `em0_1`, `em0_2`, `em0_3`, `em0_4`, `em0_5`, `VerifiedBuild`)
VALUES
    (@MENU_RFC, 'Even the flames beneath Orgrimmar cannot consume every secret.', 'Even the flames beneath Orgrimmar cannot consume every secret.', 0, 0, 1, 0, 0, 0, 0, 0, 0, 0),
    (@MENU_WC, 'Dreams leave traces upon the waking world. Some can be held in the palm of a hand.', 'Dreams leave traces upon the waking world. Some can be held in the palm of a hand.', 0, 0, 1, 0, 0, 0, 0, 0, 0, 0),
    (@MENU_DEADMINES, 'The Defias concealed more than stolen gold in those mines.', 'The Defias concealed more than stolen gold in those mines.', 0, 0, 1, 0, 0, 0, 0, 0, 0, 0),
    (@MENU_SFK, 'Arugal''s curse lingers in the stones of that keep, and in the treasures within.', 'Arugal''s curse lingers in the stones of that keep, and in the treasures within.', 0, 0, 1, 0, 0, 0, 0, 0, 0, 0),
    (@MENU_BFD, 'The depths surrender their secrets reluctantly. I am a patient collector.', 'The depths surrender their secrets reluctantly. I am a patient collector.', 0, 0, 1, 0, 0, 0, 0, 0, 0, 0),
    (@MENU_STOCKADES, 'Behind those bars, even a stolen trinket can have a remarkable history.', 'Behind those bars, even a stolen trinket can have a remarkable history.', 0, 0, 1, 0, 0, 0, 0, 0, 0, 0),
    (@MENU_GNOMEREGAN, 'The gears have fallen silent, but the inventions of Gnomeregan still hold value.', 'The gears have fallen silent, but the inventions of Gnomeregan still hold value.', 0, 0, 1, 0, 0, 0, 0, 0, 0, 0),
    (@MENU_RFK, 'Old blood nourishes those thorns. Old relics lie tangled among their roots.', 'Old blood nourishes those thorns. Old relics lie tangled among their roots.', 0, 0, 1, 0, 0, 0, 0, 0, 0, 0),
    (@MENU_SM_GY, 'The Scarlet dead keep their secrets poorly. Let us see what the graves have yielded.', 'The Scarlet dead keep their secrets poorly. Let us see what the graves have yielded.', 0, 0, 1, 0, 0, 0, 0, 0, 0, 0),
    (@MENU_SM_LIB, 'A zealot may burn a book. A collector knows what would be lost.', 'A zealot may burn a book. A collector knows what would be lost.', 0, 0, 1, 0, 0, 0, 0, 0, 0, 0),
    (@MENU_SM_ARM, 'Steel remembers the hands that wielded it. The armory has many stories to tell.', 'Steel remembers the hands that wielded it. The armory has many stories to tell.', 0, 0, 1, 0, 0, 0, 0, 0, 0, 0),
    (@MENU_SM_CAT, 'Faith can sanctify a relic, or conceal its true nature. I look beyond appearances.', 'Faith can sanctify a relic, or conceal its true nature. I look beyond appearances.', 0, 0, 1, 0, 0, 0, 0, 0, 0, 0),
    (@MENU_RFD, 'The dead have claimed those halls. They have little need of their treasures.', 'The dead have claimed those halls. They have little need of their treasures.', 0, 0, 1, 0, 0, 0, 0, 0, 0, 0),
    (@MENU_ULDAMAN, 'The makers left more than stone beneath Uldaman. I seek what they left behind.', 'The makers left more than stone beneath Uldaman. I seek what they left behind.', 0, 0, 1, 0, 0, 0, 0, 0, 0, 0),
    (@MENU_ZF, 'The sands bury kingdoms, but a worthy relic can outlast them all.', 'The sands bury kingdoms, but a worthy relic can outlast them all.', 0, 0, 1, 0, 0, 0, 0, 0, 0, 0),
    (@MENU_MARAUDON, 'Stone, root and ancient sorrow guard the treasures of Maraudon.', 'Stone, root and ancient sorrow guard the treasures of Maraudon.', 0, 0, 1, 0, 0, 0, 0, 0, 0, 0),
    (@MENU_ST, 'Some temples should remain forgotten. Their relics, however, deserve closer study.', 'Some temples should remain forgotten. Their relics, however, deserve closer study.', 0, 0, 1, 0, 0, 0, 0, 0, 0, 0),
    (@MENU_BRD, 'The Dark Iron forge their secrets as carefully as their steel.', 'The Dark Iron forge their secrets as carefully as their steel.', 0, 0, 1, 0, 0, 0, 0, 0, 0, 0),
    (@MENU_LBRS, 'The lower halls of the spire conceal trophies gathered by many cruel hands.', 'The lower halls of the spire conceal trophies gathered by many cruel hands.', 0, 0, 1, 0, 0, 0, 0, 0, 0, 0),
    (@MENU_UBRS, 'The masters of the upper spire hoard more than power. Their treasures interest me.', 'The masters of the upper spire hoard more than power. Their treasures interest me.', 0, 0, 1, 0, 0, 0, 0, 0, 0, 0),
    (@MENU_DM_EAST, 'The gardens have run wild, but the relics of Eldre''Thalas have not lost their worth.', 'The gardens have run wild, but the relics of Eldre''Thalas have not lost their worth.', 0, 0, 1, 0, 0, 0, 0, 0, 0, 0),
    (@MENU_DM_WEST, 'The western halls remember an age of elven splendor. So do the objects within.', 'The western halls remember an age of elven splendor. So do the objects within.', 0, 0, 1, 0, 0, 0, 0, 0, 0, 0),
    (@MENU_DM_NORTH, 'The Gordok judge a treasure by its weight. My interests are more particular.', 'The Gordok judge a treasure by its weight. My interests are more particular.', 0, 0, 1, 0, 0, 0, 0, 0, 0, 0),
    (@MENU_SCHOLO, 'Necromancy leaves its mark upon every instrument. Such marks tell useful stories.', 'Necromancy leaves its mark upon every instrument. Such marks tell useful stories.', 0, 0, 1, 0, 0, 0, 0, 0, 0, 0),
    (@MENU_STRAT_LIVE, 'The Scarlet Bastion guards its relics fiercely. I offer them a quieter resting place.', 'The Scarlet Bastion guards its relics fiercely. I offer them a quieter resting place.', 0, 0, 1, 0, 0, 0, 0, 0, 0, 0),
    (@MENU_STRAT_UNDEAD, 'The Baron''s servants cling to their possessions as stubbornly as they cling to undeath.', 'The Baron''s servants cling to their possessions as stubbornly as they cling to undeath.', 0, 0, 1, 0, 0, 0, 0, 0, 0, 0);

INSERT INTO `gossip_menu`
(`MenuID`, `TextID`)
VALUES
    (@MENU_RFC, @MENU_RFC),
    (@MENU_WC, @MENU_WC),
    (@MENU_DEADMINES, @MENU_DEADMINES),
    (@MENU_SFK, @MENU_SFK),
    (@MENU_BFD, @MENU_BFD),
    (@MENU_STOCKADES, @MENU_STOCKADES),
    (@MENU_GNOMEREGAN, @MENU_GNOMEREGAN),
    (@MENU_RFK, @MENU_RFK),
    (@MENU_SM_GY, @MENU_SM_GY),
    (@MENU_SM_LIB, @MENU_SM_LIB),
    (@MENU_SM_ARM, @MENU_SM_ARM),
    (@MENU_SM_CAT, @MENU_SM_CAT),
    (@MENU_RFD, @MENU_RFD),
    (@MENU_ULDAMAN, @MENU_ULDAMAN),
    (@MENU_ZF, @MENU_ZF),
    (@MENU_MARAUDON, @MENU_MARAUDON),
    (@MENU_ST, @MENU_ST),
    (@MENU_BRD, @MENU_BRD),
    (@MENU_LBRS, @MENU_LBRS),
    (@MENU_UBRS, @MENU_UBRS),
    (@MENU_DM_EAST, @MENU_DM_EAST),
    (@MENU_DM_WEST, @MENU_DM_WEST),
    (@MENU_DM_NORTH, @MENU_DM_NORTH),
    (@MENU_SCHOLO, @MENU_SCHOLO),
    (@MENU_STRAT_LIVE, @MENU_STRAT_LIVE),
    (@MENU_STRAT_UNDEAD, @MENU_STRAT_UNDEAD);

INSERT INTO `gossip_menu_option`
(`MenuID`, `OptionID`, `OptionIcon`, `OptionText`, `OptionBroadcastTextID`, `OptionType`, `OptionNpcFlag`, `ActionMenuID`, `ActionPoiID`, `BoxCoded`, `BoxMoney`, `BoxText`, `BoxBroadcastTextID`, `VerifiedBuild`)
VALUES
    (@MENU_RFC, 0, 1, 'Show me the relics of Ragefire Chasm.', 0, 3, 128, 0, 0, 0, 0, '', 0, 0),
    (@MENU_WC, 0, 1, 'Show me the relics of Wailing Caverns.', 0, 3, 128, 0, 0, 0, 0, '', 0, 0),
    (@MENU_DEADMINES, 0, 1, 'Show me the relics of The Deadmines.', 0, 3, 128, 0, 0, 0, 0, '', 0, 0),
    (@MENU_SFK, 0, 1, 'Show me the relics of Shadowfang Keep.', 0, 3, 128, 0, 0, 0, 0, '', 0, 0),
    (@MENU_BFD, 0, 1, 'Show me the relics of Blackfathom Deeps.', 0, 3, 128, 0, 0, 0, 0, '', 0, 0),
    (@MENU_STOCKADES, 0, 1, 'Show me the relics of The Stockade.', 0, 3, 128, 0, 0, 0, 0, '', 0, 0),
    (@MENU_GNOMEREGAN, 0, 1, 'Show me the relics of Gnomeregan.', 0, 3, 128, 0, 0, 0, 0, '', 0, 0),
    (@MENU_RFK, 0, 1, 'Show me the relics of Razorfen Kraul.', 0, 3, 128, 0, 0, 0, 0, '', 0, 0),
    (@MENU_SM_GY, 0, 1, 'Show me the relics of Scarlet Monastery - Graveyard.', 0, 3, 128, 0, 0, 0, 0, '', 0, 0),
    (@MENU_SM_LIB, 0, 1, 'Show me the relics of Scarlet Monastery - Library.', 0, 3, 128, 0, 0, 0, 0, '', 0, 0),
    (@MENU_SM_ARM, 0, 1, 'Show me the relics of Scarlet Monastery - Armory.', 0, 3, 128, 0, 0, 0, 0, '', 0, 0),
    (@MENU_SM_CAT, 0, 1, 'Show me the relics of Scarlet Monastery - Cathedral.', 0, 3, 128, 0, 0, 0, 0, '', 0, 0),
    (@MENU_RFD, 0, 1, 'Show me the relics of Razorfen Downs.', 0, 3, 128, 0, 0, 0, 0, '', 0, 0),
    (@MENU_ULDAMAN, 0, 1, 'Show me the relics of Uldaman.', 0, 3, 128, 0, 0, 0, 0, '', 0, 0),
    (@MENU_ZF, 0, 1, 'Show me the relics of Zul''Farrak.', 0, 3, 128, 0, 0, 0, 0, '', 0, 0),
    (@MENU_MARAUDON, 0, 1, 'Show me the relics of Maraudon.', 0, 3, 128, 0, 0, 0, 0, '', 0, 0),
    (@MENU_ST, 0, 1, 'Show me the relics of The Temple of Atal''Hakkar.', 0, 3, 128, 0, 0, 0, 0, '', 0, 0),
    (@MENU_BRD, 0, 1, 'Show me the relics of Blackrock Depths.', 0, 3, 128, 0, 0, 0, 0, '', 0, 0),
    (@MENU_LBRS, 0, 1, 'Show me the relics of Lower Blackrock Spire.', 0, 3, 128, 0, 0, 0, 0, '', 0, 0),
    (@MENU_UBRS, 0, 1, 'Show me the relics of Upper Blackrock Spire.', 0, 3, 128, 0, 0, 0, 0, '', 0, 0),
    (@MENU_DM_EAST, 0, 1, 'Show me the relics of Dire Maul - East.', 0, 3, 128, 0, 0, 0, 0, '', 0, 0),
    (@MENU_DM_WEST, 0, 1, 'Show me the relics of Dire Maul - West.', 0, 3, 128, 0, 0, 0, 0, '', 0, 0),
    (@MENU_DM_NORTH, 0, 1, 'Show me the relics of Dire Maul - North.', 0, 3, 128, 0, 0, 0, 0, '', 0, 0),
    (@MENU_SCHOLO, 0, 1, 'Show me the relics of Scholomance.', 0, 3, 128, 0, 0, 0, 0, '', 0, 0),
    (@MENU_STRAT_LIVE, 0, 1, 'Show me the relics of Stratholme - Living Quarter.', 0, 3, 128, 0, 0, 0, 0, '', 0, 0),
    (@MENU_STRAT_UNDEAD, 0, 1, 'Show me the relics of Stratholme - Undead Quarter.', 0, 3, 128, 0, 0, 0, 0, '', 0, 0);

INSERT INTO `npc_text_locale`
(`ID`, `locale`, `Text0_0`, `Text0_1`)
VALUES
    (@MENU_RFC, 'esES', 'Ni siquiera las llamas bajo Orgrimmar pueden consumir todos los secretos.', 'Ni siquiera las llamas bajo Orgrimmar pueden consumir todos los secretos.'),
    (@MENU_WC, 'esES', 'Los sueños dejan huellas en el mundo de los vivos. Algunas caben en la palma de la mano.', 'Los sueños dejan huellas en el mundo de los vivos. Algunas caben en la palma de la mano.'),
    (@MENU_DEADMINES, 'esES', 'Los Defias ocultaron algo más que oro robado en esas minas.', 'Los Defias ocultaron algo más que oro robado en esas minas.'),
    (@MENU_SFK, 'esES', 'La maldición de Arugal perdura en las piedras de ese castillo y en sus tesoros.', 'La maldición de Arugal perdura en las piedras de ese castillo y en sus tesoros.'),
    (@MENU_BFD, 'esES', 'Las profundidades entregan sus secretos a regañadientes. Soy un coleccionista paciente.', 'Las profundidades entregan sus secretos a regañadientes. Soy un coleccionista paciente.'),
    (@MENU_STOCKADES, 'esES', 'Tras esos barrotes, hasta una baratija robada puede tener una historia extraordinaria.', 'Tras esos barrotes, hasta una baratija robada puede tener una historia extraordinaria.'),
    (@MENU_GNOMEREGAN, 'esES', 'Los engranajes han enmudecido, pero los inventos de Gnomeregan aún conservan su valor.', 'Los engranajes han enmudecido, pero los inventos de Gnomeregan aún conservan su valor.'),
    (@MENU_RFK, 'esES', 'La sangre antigua alimenta esas espinas. Entre sus raíces yacen viejas reliquias.', 'La sangre antigua alimenta esas espinas. Entre sus raíces yacen viejas reliquias.'),
    (@MENU_SM_GY, 'esES', 'Los muertos Escarlata guardan mal sus secretos. Veamos qué han entregado las tumbas.', 'Los muertos Escarlata guardan mal sus secretos. Veamos qué han entregado las tumbas.'),
    (@MENU_SM_LIB, 'esES', 'Un fanático puede quemar un libro. Un coleccionista sabe lo que se perdería.', 'Un fanático puede quemar un libro. Un coleccionista sabe lo que se perdería.'),
    (@MENU_SM_ARM, 'esES', 'El acero recuerda las manos que lo empuñaron. Esa armería tiene muchas historias que contar.', 'El acero recuerda las manos que lo empuñaron. Esa armería tiene muchas historias que contar.'),
    (@MENU_SM_CAT, 'esES', 'La fe puede santificar una reliquia u ocultar su verdadera naturaleza. Yo miro más allá de las apariencias.', 'La fe puede santificar una reliquia u ocultar su verdadera naturaleza. Yo miro más allá de las apariencias.'),
    (@MENU_RFD, 'esES', 'Los muertos se han adueñado de esas salas. Poco necesitan sus tesoros.', 'Los muertos se han adueñado de esas salas. Poco necesitan sus tesoros.'),
    (@MENU_ULDAMAN, 'esES', 'Los creadores dejaron algo más que piedra bajo Uldaman. Busco los vestigios de su obra.', 'Los creadores dejaron algo más que piedra bajo Uldaman. Busco los vestigios de su obra.'),
    (@MENU_ZF, 'esES', 'Las arenas sepultan reinos, pero una buena reliquia puede sobrevivirlos a todos.', 'Las arenas sepultan reinos, pero una buena reliquia puede sobrevivirlos a todos.'),
    (@MENU_MARAUDON, 'esES', 'La piedra, las raíces y una pena ancestral custodian los tesoros de Maraudon.', 'La piedra, las raíces y una pena ancestral custodian los tesoros de Maraudon.'),
    (@MENU_ST, 'esES', 'Algunos templos deberían permanecer olvidados. Sus reliquias, sin embargo, merecen un estudio más atento.', 'Algunos templos deberían permanecer olvidados. Sus reliquias, sin embargo, merecen un estudio más atento.'),
    (@MENU_BRD, 'esES', 'Los Hierro Negro forjan sus secretos con tanto cuidado como su acero.', 'Los Hierro Negro forjan sus secretos con tanto cuidado como su acero.'),
    (@MENU_LBRS, 'esES', 'Las salas inferiores de la cumbre ocultan trofeos reunidos por muchas manos crueles.', 'Las salas inferiores de la cumbre ocultan trofeos reunidos por muchas manos crueles.'),
    (@MENU_UBRS, 'esES', 'Los señores de la cumbre superior acumulan algo más que poder. Sus tesoros me interesan.', 'Los señores de la cumbre superior acumulan algo más que poder. Sus tesoros me interesan.'),
    (@MENU_DM_EAST, 'esES', 'Los jardines se han vuelto salvajes, pero las reliquias de Eldre''Thalas no han perdido su valor.', 'Los jardines se han vuelto salvajes, pero las reliquias de Eldre''Thalas no han perdido su valor.'),
    (@MENU_DM_WEST, 'esES', 'Las salas occidentales recuerdan una era de esplendor élfico. También los objetos que albergan.', 'Las salas occidentales recuerdan una era de esplendor élfico. También los objetos que albergan.'),
    (@MENU_DM_NORTH, 'esES', 'Los Gordok juzgan un tesoro por su peso. Mis intereses son más selectos.', 'Los Gordok juzgan un tesoro por su peso. Mis intereses son más selectos.'),
    (@MENU_SCHOLO, 'esES', 'La nigromancia deja su huella en cada instrumento. Esas huellas cuentan historias útiles.', 'La nigromancia deja su huella en cada instrumento. Esas huellas cuentan historias útiles.'),
    (@MENU_STRAT_LIVE, 'esES', 'El Bastión Escarlata custodia sus reliquias con fiereza. Yo les ofrezco un lugar de reposo más tranquilo.', 'El Bastión Escarlata custodia sus reliquias con fiereza. Yo les ofrezco un lugar de reposo más tranquilo.'),
    (@MENU_STRAT_UNDEAD, 'esES', 'Los siervos del Barón se aferran a sus posesiones con la misma obstinación que a la no-muerte.', 'Los siervos del Barón se aferran a sus posesiones con la misma obstinación que a la no-muerte.');

INSERT INTO `gossip_menu_option_locale`
(`MenuID`, `OptionID`, `Locale`, `OptionText`, `BoxText`)
VALUES
    (@MENU_RFC, 0, 'esES', 'Muéstrame las reliquias de Sima Ígnea.', ''),
    (@MENU_WC, 0, 'esES', 'Muéstrame las reliquias de las Cuevas de los Lamentos.', ''),
    (@MENU_DEADMINES, 0, 'esES', 'Muéstrame las reliquias de las Minas de la Muerte.', ''),
    (@MENU_SFK, 0, 'esES', 'Muéstrame las reliquias del Castillo de Colmillo Oscuro.', ''),
    (@MENU_BFD, 0, 'esES', 'Muéstrame las reliquias de las Cavernas de Brazanegra.', ''),
    (@MENU_STOCKADES, 0, 'esES', 'Muéstrame las reliquias de las Mazmorras de Ventormenta.', ''),
    (@MENU_GNOMEREGAN, 0, 'esES', 'Muéstrame las reliquias de Gnomeregan.', ''),
    (@MENU_RFK, 0, 'esES', 'Muéstrame las reliquias de Horado Rajacieno.', ''),
    (@MENU_SM_GY, 0, 'esES', 'Muéstrame las reliquias del Cementerio Escarlata.', ''),
    (@MENU_SM_LIB, 0, 'esES', 'Muéstrame las reliquias de la Biblioteca Escarlata.', ''),
    (@MENU_SM_ARM, 0, 'esES', 'Muéstrame las reliquias de la Armería Escarlata.', ''),
    (@MENU_SM_CAT, 0, 'esES', 'Muéstrame las reliquias de la Catedral Escarlata.', ''),
    (@MENU_RFD, 0, 'esES', 'Muéstrame las reliquias de la Zahúrda Rajacieno.', ''),
    (@MENU_ULDAMAN, 0, 'esES', 'Muéstrame las reliquias de Uldaman.', ''),
    (@MENU_ZF, 0, 'esES', 'Muéstrame las reliquias de Zul''Farrak.', ''),
    (@MENU_MARAUDON, 0, 'esES', 'Muéstrame las reliquias de Maraudon.', ''),
    (@MENU_ST, 0, 'esES', 'Muéstrame las reliquias del Templo Sumergido.', ''),
    (@MENU_BRD, 0, 'esES', 'Muéstrame las reliquias de las Profundidades de Roca Negra.', ''),
    (@MENU_LBRS, 0, 'esES', 'Muéstrame las reliquias de la Cumbre de Roca Negra inferior.', ''),
    (@MENU_UBRS, 0, 'esES', 'Muéstrame las reliquias de la Cumbre de Roca Negra superior.', ''),
    (@MENU_DM_EAST, 0, 'esES', 'Muéstrame las reliquias de La Masacre Este.', ''),
    (@MENU_DM_WEST, 0, 'esES', 'Muéstrame las reliquias de La Masacre Oeste.', ''),
    (@MENU_DM_NORTH, 0, 'esES', 'Muéstrame las reliquias de La Masacre Norte.', ''),
    (@MENU_SCHOLO, 0, 'esES', 'Muéstrame las reliquias de Scholomance.', ''),
    (@MENU_STRAT_LIVE, 0, 'esES', 'Muéstrame las reliquias de Stratholme: sector vivo.', ''),
    (@MENU_STRAT_UNDEAD, 0, 'esES', 'Muéstrame las reliquias de Stratholme: sector no muerto.', '');

UPDATE `creature_template`
SET `IconName` = 'Speak',
    `npcflag` = `npcflag` | 4096,
    `type_flags` = `type_flags` | 0x08000000
WHERE `entry` IN (@NPC_RFC, @NPC_WC, @NPC_DEADMINES, @NPC_SFK, @NPC_BFD, @NPC_STOCKADES, @NPC_GNOMEREGAN, @NPC_RFK, @NPC_SM_GY, @NPC_SM_LIB, @NPC_SM_ARM, @NPC_SM_CAT, @NPC_RFD, @NPC_ULDAMAN, @NPC_ZF, @NPC_MARAUDON, @NPC_ST, @NPC_BRD, @NPC_LBRS, @NPC_UBRS, @NPC_DM_EAST, @NPC_DM_WEST, @NPC_DM_NORTH, @NPC_SCHOLO, @NPC_STRAT_LIVE, @NPC_STRAT_UNDEAD);

-- ============================================================================
-- SPAWNS
-- ============================================================================
-- Remove only the expected GUID/template pairs; do not erase an unrelated
-- creature that happens to occupy a reserved GUID. Such a collision causes
-- the INSERT to fail and must be resolved before deploying these allocations.
DELETE FROM `creature`
WHERE
    (`guid` = 900010 AND `id` = @NPC_RFC)
 OR     (`guid` = 900011 AND `id` = @NPC_WC)
 OR     (`guid` = 900012 AND `id` = @NPC_DEADMINES)
 OR     (`guid` = 900013 AND `id` = @NPC_SFK)
 OR     (`guid` = 900014 AND `id` = @NPC_BFD)
 OR     (`guid` = 900015 AND `id` = @NPC_STOCKADES)
 OR     (`guid` = 900016 AND `id` = @NPC_GNOMEREGAN)
 OR     (`guid` = 900017 AND `id` = @NPC_RFK)
 OR     (`guid` = 900018 AND `id` = @NPC_SM_GY)
 OR     (`guid` = 900019 AND `id` = @NPC_SM_LIB)
 OR     (`guid` = 900020 AND `id` = @NPC_SM_ARM)
 OR     (`guid` = 900021 AND `id` = @NPC_SM_CAT)
 OR     (`guid` = 900022 AND `id` = @NPC_RFD)
 OR     (`guid` = 900023 AND `id` = @NPC_ULDAMAN)
 OR     (`guid` = 900024 AND `id` = @NPC_ZF)
 OR     (`guid` = 900025 AND `id` = @NPC_MARAUDON)
 OR     (`guid` = 900026 AND `id` = @NPC_ST)
 OR     (`guid` = 900027 AND `id` = @NPC_BRD)
 OR     (`guid` = 900028 AND `id` = @NPC_LBRS)
 OR     (`guid` = 900029 AND `id` = @NPC_UBRS)
 OR     (`guid` = 900030 AND `id` = @NPC_DM_EAST)
 OR     (`guid` = 900031 AND `id` = @NPC_DM_WEST)
 OR     (`guid` = 900032 AND `id` = @NPC_DM_NORTH)
 OR     (`guid` = 900033 AND `id` = @NPC_SCHOLO)
 OR     (`guid` = 900034 AND `id` = @NPC_STRAT_LIVE)
 OR     (`guid` = 900035 AND `id` = @NPC_STRAT_UNDEAD);

INSERT INTO `creature`
(`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`,
 `equipment_id`, `position_x`, `position_y`, `position_z`, `orientation`,
 `spawntimesecs`, `wander_distance`, `MovementType`, `npcflag`, `unit_flags`,
 `dynamicflags`, `VerifiedBuild`, `CreateObject`, `Comment`)
VALUES

    -- Ragefire Chasm: User-supplied position, 2026-10-01.
    -- GM: .go creature 900010
    (900010, @NPC_RFC, 1, 0, 0, 1, 1, 0,
     1811.9, -4384.75, -16.537, 4.250574,
     300, 0, 0, 4225, 0, 0, 0, 0,
     'Dark Rider - Ragefire Chasm vendor'),

    -- Wailing Caverns: User-supplied position, 2026-10-01.
    -- GM: .go creature 900011
    (900011, @NPC_WC, 1, 0, 0, 1, 1, 0,
     -670.804, -2238.71, 18.9871, 5.789955,
     300, 0, 0, 4225, 0, 0, 0, 0,
     'Dark Rider - Wailing Caverns vendor'),

    -- The Deadmines: User-supplied position, 2026-10-01.
    -- GM: .go creature 900012
    (900012, @NPC_DEADMINES, 0, 0, 0, 1, 1, 0,
     -11096.912, 1516.5846, 43.13031, 4.756349,
     300, 0, 0, 4225, 0, 0, 0, 0,
     'Dark Rider - The Deadmines vendor'),

    -- Shadowfang Keep: User-supplied position, 2026-10-01.
    -- GM: .go creature 900013
    (900013, @NPC_SFK, 0, 0, 0, 1, 1, 0,
     -324.39685, 1470.9333, 31.773205, 1.5501448,
     300, 0, 0, 4225, 0, 0, 0, 0,
     'Dark Rider - Shadowfang Keep vendor'),

    -- Blackfathom Deeps: User-supplied position, 2026-10-01.
    -- GM: .go creature 900014
    (900014, @NPC_BFD, 1, 0, 0, 1, 1, 0,
     4180.859, 742.51526, -30.03402, 0.4696683,
     300, 0, 0, 4225, 0, 0, 0, 0,
     'Dark Rider - Blackfathom Deeps vendor'),

    -- The Stockade: User-supplied position, 2026-10-01.
    -- GM: .go creature 900015
    (900015, @NPC_STOCKADES, 0, 0, 0, 1, 1, 0,
     -8868.648, 1085.8124, 84.41705, 3.056784,
     300, 0, 0, 4225, 0, 0, 0, 0,
     'Dark Rider - The Stockade vendor'),

    -- Gnomeregan: User-supplied position, 2026-10-01.
    -- GM: .go creature 900016
    (900016, @NPC_GNOMEREGAN, 0, 0, 0, 1, 1, 0,
     -4973.159, 765.3167, 258.97653, 5.774279,
     300, 0, 0, 4225, 0, 0, 0, 0,
     'Dark Rider - Gnomeregan vendor'),

    -- Razorfen Kraul: User-supplied position, 2026-10-01.
    -- GM: .go creature 900017
    (900017, @NPC_RFK, 1, 0, 0, 1, 1, 0,
     -4472.6504, -1759.6238, 92.79058, 1.712969,
     300, 0, 0, 4225, 0, 0, 0, 0,
     'Dark Rider - Razorfen Kraul vendor'),

    -- Scarlet Monastery - Graveyard: User-supplied position, 2026-10-01.
    -- GM: .go creature 900018
    (900018, @NPC_SM_GY, 0, 0, 0, 1, 1, 0,
     2698.2522, -732.77875, 145.15324, 0.020454023,
     300, 0, 0, 4225, 0, 0, 0, 0,
     'Dark Rider - Scarlet Monastery - Graveyard vendor'),

    -- Scarlet Monastery - Library: User-supplied position, 2026-10-01.
    -- GM: .go creature 900019
    (900019, @NPC_SM_LIB, 0, 0, 0, 1, 1, 0,
     2811.2952, -878.19147, 154.133, 3.0905924,
     300, 0, 0, 4225, 0, 0, 0, 0,
     'Dark Rider - Scarlet Monastery - Library vendor'),

    -- Scarlet Monastery - Armory: User-supplied position, 2026-10-01.
    -- GM: .go creature 900020
    (900020, @NPC_SM_ARM, 0, 0, 0, 1, 1, 0,
     2869.3362, -621.4665, 137.97792, 3.9568863,
     300, 0, 0, 4225, 0, 0, 0, 0,
     'Dark Rider - Scarlet Monastery - Armory vendor'),

    -- Scarlet Monastery - Cathedral: User-supplied position, 2026-10-01.
    -- GM: .go creature 900021
    (900021, @NPC_SM_CAT, 0, 0, 0, 1, 1, 0,
     2876.9177, -723.2528, 155.0001, 1.7075171,
     300, 0, 0, 4225, 0, 0, 0, 0,
     'Dark Rider - Scarlet Monastery - Cathedral vendor'),

    -- Razorfen Downs: User-supplied position, 2026-10-01.
    -- GM: .go creature 900022
    (900022, @NPC_RFD, 1, 0, 0, 1, 1, 0,
     -4697.999, -2355.9446, 101.31632, 5.7883334,
     300, 0, 0, 4225, 0, 0, 0, 0,
     'Dark Rider - Razorfen Downs vendor'),

    -- Uldaman: User-supplied position, 2026-10-01.
    -- GM: .go creature 900023
    (900023, @NPC_ULDAMAN, 0, 0, 0, 1, 1, 0,
     -6090.8076, -2938.374, 207.56148, 3.9984617,
     300, 0, 0, 4225, 0, 0, 0, 0,
     'Dark Rider - Uldaman vendor'),

    -- Zul'Farrak: User-supplied position, 2026-10-01.
    -- GM: .go creature 900024
    (900024, @NPC_ZF, 1, 0, 0, 1, 1, 0,
     -6800.0825, -2911.416, 11.912806, 1.2605822,
     300, 0, 0, 4225, 0, 0, 0, 0,
     'Dark Rider - Zul''Farrak vendor'),

    -- Maraudon: User-supplied position, 2026-10-01.
    -- GM: .go creature 900025
    (900025, @NPC_MARAUDON, 1, 0, 0, 1, 1, 0,
     -1337.5436, 2677.2026, 86.17391, 3.3261893,
     300, 0, 0, 4225, 0, 0, 0, 0,
     'Dark Rider - Maraudon vendor'),

    -- The Temple of Atal'Hakkar: User-supplied position, 2026-10-01.
    -- GM: .go creature 900026
    (900026, @NPC_ST, 0, 0, 0, 1, 1, 0,
     -10446.328, -3798.274, 30.40214, 5.0893497,
     300, 0, 0, 4225, 0, 0, 0, 0,
     'Dark Rider - The Temple of Atal''Hakkar vendor'),

    -- Blackrock Depths: User-supplied position, 2026-10-01.
    -- GM: .go creature 900027
    (900027, @NPC_BRD, 0, 0, 0, 1, 1, 0,
     -7492.572, -1055.5618, 179.08177, 1.0868131,
     300, 0, 0, 4225, 0, 0, 0, 0,
     'Dark Rider - Blackrock Depths vendor'),

    -- Lower Blackrock Spire: User-supplied position, 2026-10-01.
    -- GM: .go creature 900028
    (900028, @NPC_LBRS, 0, 0, 0, 1, 1, 0,
     -7488.246, -1164.9067, 275.85565, 4.0173798,
     300, 0, 0, 4225, 0, 0, 0, 0,
     'Dark Rider - Lower Blackrock Spire vendor'),

    -- Upper Blackrock Spire: User-supplied position, 2026-10-01.
    -- GM: .go creature 900029
    (900029, @NPC_UBRS, 0, 0, 0, 1, 1, 0,
     -7626.424, -1249.3458, 234.45316, 5.4758673,
     300, 0, 0, 4225, 0, 0, 0, 0,
     'Dark Rider - Upper Blackrock Spire vendor'),

    -- Dire Maul - East: User-supplied position, 2026-10-01.
    -- GM: .go creature 900030
    (900030, @NPC_DM_EAST, 1, 0, 0, 1, 1, 0,
     -3833.4045, 935.5105, 160.9928, 6.2627654,
     300, 0, 0, 4225, 0, 0, 0, 0,
     'Dark Rider - Dire Maul - East vendor'),

    -- Dire Maul - West: User-supplied position, 2026-10-01.
    -- GM: .go creature 900031
    (900031, @NPC_DM_WEST, 1, 0, 0, 1, 1, 0,
     -3781.4148, 1139.0455, 160.56325, 4.7665987,
     300, 0, 0, 4225, 0, 0, 0, 0,
     'Dark Rider - Dire Maul - West vendor'),

    -- Dire Maul - North: User-supplied position, 2026-10-01.
    -- GM: .go creature 900032
    (900032, @NPC_DM_NORTH, 1, 0, 0, 1, 1, 0,
     -3528.6072, 1142.5148, 161.02605, 4.9411974,
     300, 0, 0, 4225, 0, 0, 0, 0,
     'Dark Rider - Dire Maul - North vendor'),

    -- Scholomance: User-supplied position, 2026-10-01.
    -- GM: .go creature 900033
    (900033, @NPC_SCHOLO, 0, 0, 0, 1, 1, 0,
     1273.0782, -2558.7307, 119.31771, 5.135725,
     300, 0, 0, 4225, 0, 0, 0, 0,
     'Dark Rider - Scholomance vendor'),

    -- Stratholme - Living Quarter: User-supplied position, 2026-10-01.
    -- GM: .go creature 900034
    (900034, @NPC_STRAT_LIVE, 0, 0, 0, 1, 1, 0,
     3358.067, -3440.8103, 143.67215, 0.7744151,
     300, 0, 0, 4225, 0, 0, 0, 0,
     'Dark Rider - Stratholme - Living Quarter vendor'),

    -- Stratholme - Undead Quarter: User-supplied position, 2026-10-01.
    -- GM: .go creature 900035
    (900035, @NPC_STRAT_UNDEAD, 0, 0, 0, 1, 1, 0,
     3198.197, -4007.3074, 121.78505, 3.832752,
     300, 0, 0, 4225, 0, 0, 0, 0,
     'Dark Rider - Stratholme - Undead Quarter vendor');

COMMIT;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

SELECT `entry`, `name`, `subname`, `faction`, `npcflag`, `gossip_menu_id`, `AIName`, `MovementType`
FROM `creature_template`
WHERE `entry` IN (@NPC_RFC, @NPC_WC, @NPC_DEADMINES, @NPC_SFK, @NPC_BFD, @NPC_STOCKADES, @NPC_GNOMEREGAN, @NPC_RFK, @NPC_SM_GY, @NPC_SM_LIB, @NPC_SM_ARM, @NPC_SM_CAT, @NPC_RFD, @NPC_ULDAMAN, @NPC_ZF, @NPC_MARAUDON, @NPC_ST, @NPC_BRD, @NPC_LBRS, @NPC_UBRS, @NPC_DM_EAST, @NPC_DM_WEST, @NPC_DM_NORTH, @NPC_SCHOLO, @NPC_STRAT_LIVE, @NPC_STRAT_UNDEAD)
ORDER BY `entry`;

SELECT `CreatureID`, `CreatureDisplayID`, `DisplayScale`, `Probability`
FROM `creature_template_model`
WHERE `CreatureID` IN (@NPC_RFC, @NPC_WC, @NPC_DEADMINES, @NPC_SFK, @NPC_BFD, @NPC_STOCKADES, @NPC_GNOMEREGAN, @NPC_RFK, @NPC_SM_GY, @NPC_SM_LIB, @NPC_SM_ARM, @NPC_SM_CAT, @NPC_RFD, @NPC_ULDAMAN, @NPC_ZF, @NPC_MARAUDON, @NPC_ST, @NPC_BRD, @NPC_LBRS, @NPC_UBRS, @NPC_DM_EAST, @NPC_DM_WEST, @NPC_DM_NORTH, @NPC_SCHOLO, @NPC_STRAT_LIVE, @NPC_STRAT_UNDEAD)
ORDER BY `CreatureID`;

SELECT `entry`, `locale`, `Name`, `Title`
FROM `creature_template_locale`
WHERE `entry` IN (@NPC_RFC, @NPC_WC, @NPC_DEADMINES, @NPC_SFK, @NPC_BFD, @NPC_STOCKADES, @NPC_GNOMEREGAN, @NPC_RFK, @NPC_SM_GY, @NPC_SM_LIB, @NPC_SM_ARM, @NPC_SM_CAT, @NPC_RFD, @NPC_ULDAMAN, @NPC_ZF, @NPC_MARAUDON, @NPC_ST, @NPC_BRD, @NPC_LBRS, @NPC_UBRS, @NPC_DM_EAST, @NPC_DM_WEST, @NPC_DM_NORTH, @NPC_SCHOLO, @NPC_STRAT_LIVE, @NPC_STRAT_UNDEAD)
ORDER BY `entry`;

SELECT `guid`, `id`, `map`, `position_x`, `position_y`, `position_z`, `orientation`
FROM `creature`
WHERE `guid` IN (900010, 900011, 900012, 900013, 900014, 900015, 900016, 900017, 900018, 900019, 900020, 900021, 900022, 900023, 900024, 900025, 900026, 900027, 900028, 900029, 900030, 900031, 900032, 900033, 900034, 900035)
ORDER BY `guid`;

SELECT `entry`, COUNT(*) AS `vendor_items`
FROM `npc_vendor`
WHERE `entry` IN (@NPC_RFC, @NPC_WC, @NPC_DEADMINES, @NPC_SFK, @NPC_BFD, @NPC_STOCKADES, @NPC_GNOMEREGAN, @NPC_RFK, @NPC_SM_GY, @NPC_SM_LIB, @NPC_SM_ARM, @NPC_SM_CAT, @NPC_RFD, @NPC_ULDAMAN, @NPC_ZF, @NPC_MARAUDON, @NPC_ST, @NPC_BRD, @NPC_LBRS, @NPC_UBRS, @NPC_DM_EAST, @NPC_DM_WEST, @NPC_DM_NORTH, @NPC_SCHOLO, @NPC_STRAT_LIVE, @NPC_STRAT_UNDEAD)
GROUP BY `entry`
ORDER BY `entry`;
