-- ============================================================================
-- DARK RIDERS - DUNGEON CURIOS
-- Final-boss loot / Bad Luck Protection
--
-- One token per eligible player from the designated final boss of each
-- dungeon/wing. One guaranteed loot row, with one personal copy per player.
-- Each player loots their copy from the corpse through normal group loot
-- eligibility and distance rules. This is not automatic currency delivery.
--
-- Prerequisite: apply dungeon_gear_vendor.sql first (items 90010-90035).
-- Pattern: data/sql/custom/db_world/raid_gear_vendor_loot.sql
-- Designed for AzerothCore + Grimfeather/mod-individual-progression.
--
-- Source review:
-- Core: Grimfeather/azerothcore-wotlk @ 529b659668bcd8b1cfbf9acc44f40eb6ff830fe1
-- IP:   Grimfeather/mod-individual-progression @ db5dc9e76f176f0eb8af7ff6647743abfceda479
-- Final bosses: data/sql/base/db_world/instance_encounters.sql.
-- Personal copies: LootMgr.cpp (FillFFALoot) and Player::StoreLootItem.
-- The deployed database and in-game behavior have not been tested here.
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

-- ITEM_FLAG_MULTI_DROP: one independent copy for each eligible player.
SET @ITEM_FLAG_MULTI_DROP := 2048;


-- ============================================================================
-- MAKE CURIOS FREE-FOR-ALL / MULTI-DROP
--
-- The core creates a PlayerFFAItems entry for each eligible group member.
-- Looting marks only that player's copy as looted. Group Loot, Need Before
-- Greed and Master Loot skip these FFA items when allocating shared loot.
--
-- Keep BagFamily = 0, as in dungeon_gear_vendor.sql: the player must loot
-- the corpse. BagFamily = 8192 would enable automatic currency processing.
-- Preserve all other existing item flags.
-- ============================================================================


UPDATE `item_template`
SET
    `Flags`     = `Flags` | @ITEM_FLAG_MULTI_DROP,
    `BagFamily` = 0
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
-- TEMPORARY BOSS REWARD TABLE
--
-- Store CREATURE ENTRY, not lootid. Resolve creature_template.lootid when
-- applying the SQL, because a deployed lootid may differ from its entry.
-- A unique currency constraint enforces one designated final boss per token.
-- ============================================================================


DROP TEMPORARY TABLE IF EXISTS `tmp_dark_rider_dungeon_rewards`;

CREATE TEMPORARY TABLE `tmp_dark_rider_dungeon_rewards`
(
    `CreatureEntry` INT UNSIGNED NOT NULL,
    `CurioItem`     INT UNSIGNED NOT NULL,
    `CurioCount`    TINYINT UNSIGNED NOT NULL,
    `DungeonName`   VARCHAR(64) NOT NULL,
    `EncounterName` VARCHAR(100) NOT NULL,

    PRIMARY KEY (`CreatureEntry`, `CurioItem`),
    UNIQUE KEY `uq_dungeon_curio` (`CurioItem`)
);


-- ============================================================================
-- CLASSIC DUNGEONS - ONE CURIO FROM EACH FINAL BOSS
--
-- Ragefire Chasm: Taragaman is the final credit in instance_encounters.
-- Bazzalan and Jergosh do not award this token.
--
-- Wailing Caverns: Mutanus, after the Naralex event; not Verdan.
--
-- Scarlet Cathedral: Whitemane is the final-dungeon credit and the only
-- currency-bearing corpse. Mograine's fake death and final death award none.
-- This follows the core's Whitemane kill credit; no new both-bosses gate
-- or kill-order requirement is added to the encounter.
--
-- Dire Maul North: King Gordok's corpse, including tribute runs.
-- Do not also award the token from the tribute chest or Cho'Rush.
--
-- Dire Maul West ends at Prince Tortheldrin; Maraudon at Princess Theradras.
-- BRD has one token at Emperor Dagran Thaurissan, not intermediate bosses.
-- All selected final bosses use corpse loot. No chest reward is added.
-- ============================================================================


INSERT INTO `tmp_dark_rider_dungeon_rewards`
VALUES

-- Ragefire Chasm
(11520, @RFC_CURIO, 1, 'Ragefire Chasm', 'Taragaman the Hungerer'),

-- Wailing Caverns
(3654, @WC_CURIO, 1, 'Wailing Caverns', 'Mutanus the Devourer'),

-- The Deadmines
(639, @DEADMINES_CURIO, 1, 'The Deadmines', 'Edwin VanCleef'),

-- Shadowfang Keep
(4275, @SFK_CURIO, 1, 'Shadowfang Keep', 'Archmage Arugal'),

-- Blackfathom Deeps
(4829, @BFD_CURIO, 1, 'Blackfathom Deeps', 'Aku''mai'),

-- The Stockade
(1716, @STOCKADES_CURIO, 1, 'The Stockade', 'Bazil Thredd'),

-- Gnomeregan
(7800, @GNOMEREGAN_CURIO, 1, 'Gnomeregan', 'Mekgineer Thermaplugg'),

-- Razorfen Kraul
(4421, @RFK_CURIO, 1, 'Razorfen Kraul', 'Charlga Razorflank'),

-- Scarlet Monastery - Graveyard
(4543, @SM_GY_CURIO, 1, 'Scarlet Monastery - Graveyard', 'Bloodmage Thalnos'),

-- Scarlet Monastery - Library
(6487, @SM_LIB_CURIO, 1, 'Scarlet Monastery - Library', 'Arcanist Doan'),

-- Scarlet Monastery - Armory
(3975, @SM_ARM_CURIO, 1, 'Scarlet Monastery - Armory', 'Herod'),

-- Scarlet Monastery - Cathedral
(3977, @SM_CAT_CURIO, 1, 'Scarlet Monastery - Cathedral', 'High Inquisitor Whitemane'),

-- Razorfen Downs
(7358, @RFD_CURIO, 1, 'Razorfen Downs', 'Amnennar the Coldbringer'),

-- Uldaman
(2748, @ULDAMAN_CURIO, 1, 'Uldaman', 'Archaedas'),

-- Zul'Farrak
(7267, @ZF_CURIO, 1, 'Zul''Farrak', 'Chief Ukorz Sandscalp'),

-- Maraudon
(12201, @MARAUDON_CURIO, 1, 'Maraudon', 'Princess Theradras'),

-- The Temple of Atal'Hakkar
(5709, @ST_CURIO, 1, 'The Temple of Atal''Hakkar', 'Shade of Eranikus'),

-- Blackrock Depths
(9019, @BRD_CURIO, 1, 'Blackrock Depths', 'Emperor Dagran Thaurissan'),

-- Lower Blackrock Spire
(9568, @LBRS_CURIO, 1, 'Lower Blackrock Spire', 'Overlord Wyrmthalak'),

-- Upper Blackrock Spire
(10363, @UBRS_CURIO, 1, 'Upper Blackrock Spire', 'General Drakkisath'),

-- Dire Maul - East
(11492, @DM_EAST_CURIO, 1, 'Dire Maul - East', 'Alzzin the Wildshaper'),

-- Dire Maul - West
(11486, @DM_WEST_CURIO, 1, 'Dire Maul - West', 'Prince Tortheldrin'),

-- Dire Maul - North
(11501, @DM_NORTH_CURIO, 1, 'Dire Maul - North', 'King Gordok'),

-- Scholomance
(1853, @SCHOLO_CURIO, 1, 'Scholomance', 'Darkmaster Gandling'),

-- Stratholme - Living Quarter
(10813, @STRAT_LIVE_CURIO, 1, 'Stratholme - Living Quarter', 'Balnazzar'),

-- Stratholme - Undead Quarter
(10440, @STRAT_UNDEAD_CURIO, 1, 'Stratholme - Undead Quarter', 'Baron Rivendare');


-- ============================================================================
-- REMOVE PREVIOUS CUSTOM CURRENCY DROPS
--
-- Remove only the mapped boss/token pairs, regardless of their old group
-- or count. All other loot, raid curios and transmog marks are preserved.
-- ============================================================================


DELETE `clt`
FROM `creature_loot_template` AS `clt`
INNER JOIN `creature_template` AS `ct`
    ON `ct`.`lootid` = `clt`.`Entry`
INNER JOIN `tmp_dark_rider_dungeon_rewards` AS `reward`
    ON `reward`.`CreatureEntry` = `ct`.`entry`
   AND `reward`.`CurioItem` = `clt`.`Item`;


-- ============================================================================
-- INSERT FINAL-BOSS CURRENCY DROPS
--
-- Chance        = 100% (guaranteed)
-- Reference     = 0 (real item, not a reference loot table)
-- QuestRequired = 0 (no quest prerequisite)
-- LootMode      = 1 (normal/default creature loot mode)
-- GroupId       = 0 (standalone; does not compete with other drops)
-- MinCount      = 1
-- MaxCount      = 1
--
-- Do not set count to the party size: MULTI_DROP provides the copies.
-- Skip missing currencies and shared loot IDs; the verification queries
-- below expose those prerequisites instead of affecting unrelated creatures.
-- ============================================================================


INSERT INTO `creature_loot_template`
(
    `Entry`,
    `Item`,
    `Reference`,
    `Chance`,
    `QuestRequired`,
    `LootMode`,
    `GroupId`,
    `MinCount`,
    `MaxCount`,
    `Comment`
)
SELECT
    `ct`.`lootid`,
    `reward`.`CurioItem`,
    0,
    100,
    0,
    1,
    0,
    `reward`.`CurioCount`,
    `reward`.`CurioCount`,
    CONCAT(
        'Dark Rider BLP - ',
        `reward`.`DungeonName`,
        ' - ',
        `reward`.`EncounterName`,
        ' - final boss'
    )
FROM `tmp_dark_rider_dungeon_rewards` AS `reward`
INNER JOIN `creature_template` AS `ct`
    ON `ct`.`entry` = `reward`.`CreatureEntry`
INNER JOIN `item_template` AS `it`
    ON `it`.`entry` = `reward`.`CurioItem`
WHERE `ct`.`lootid` <> 0
  AND NOT EXISTS
      (
          SELECT 1
          FROM `creature_template` AS `other`
          WHERE `other`.`lootid` = `ct`.`lootid`
            AND `other`.`entry` <> `ct`.`entry`
      );

COMMIT;


-- ============================================================================
-- VERIFICATION 1 - CURRENCY ITEMS
--
-- Expected: 26 rows; HasMultiDropFlag = 2048 and BagFamily = 0.
-- ============================================================================


SELECT
    `it`.`entry`,
    `it`.`name`,
    `it`.`Flags`,
    (`it`.`Flags` & 2048) AS `HasMultiDropFlag`,
    `it`.`BagFamily`,
    `it`.`stackable`,
    `it`.`bonding`
FROM `tmp_dark_rider_dungeon_rewards` AS `reward`
INNER JOIN `item_template` AS `it`
    ON `it`.`entry` = `reward`.`CurioItem`
ORDER BY `it`.`entry`;


-- ============================================================================
-- VERIFICATION 2 - MISSING CURRENCIES
--
-- Expected: ZERO rows. If present, apply dungeon_gear_vendor.sql first.
-- ============================================================================


SELECT
    `reward`.`DungeonName`,
    `reward`.`CurioItem` AS `MissingCurrencyItem`
FROM `tmp_dark_rider_dungeon_rewards` AS `reward`
LEFT JOIN `item_template` AS `it`
    ON `it`.`entry` = `reward`.`CurioItem`
WHERE `it`.`entry` IS NULL
ORDER BY `reward`.`CurioItem`;


-- ============================================================================
-- VERIFICATION 3 - MISSING BOSSES / BOSSES WITHOUT LOOTID
--
-- Expected: ZERO rows.
-- ============================================================================


SELECT
    `reward`.`DungeonName`,
    `reward`.`EncounterName`,
    `reward`.`CreatureEntry`,
    `ct`.`name` AS `DatabaseName`,
    `ct`.`lootid`
FROM `tmp_dark_rider_dungeon_rewards` AS `reward`
LEFT JOIN `creature_template` AS `ct`
    ON `ct`.`entry` = `reward`.`CreatureEntry`
WHERE `ct`.`entry` IS NULL
   OR `ct`.`lootid` = 0
ORDER BY `reward`.`CurioItem`;


-- ============================================================================
-- VERIFICATION 4 - SHARED LOOTIDS
--
-- Expected: ZERO rows. These rewards are skipped to avoid giving a
-- dungeon token to another creature sharing the same loot table.
-- ============================================================================


SELECT
    `reward`.`DungeonName`,
    `reward`.`CreatureEntry`,
    `ct`.`lootid`,
    `other`.`entry` AS `OtherCreatureEntry`,
    `other`.`name` AS `OtherCreatureName`
FROM `tmp_dark_rider_dungeon_rewards` AS `reward`
INNER JOIN `creature_template` AS `ct`
    ON `ct`.`entry` = `reward`.`CreatureEntry`
INNER JOIN `creature_template` AS `other`
    ON `other`.`lootid` = `ct`.`lootid`
   AND `other`.`entry` <> `ct`.`entry`
WHERE `ct`.`lootid` <> 0
ORDER BY `reward`.`CurioItem`, `other`.`entry`;


-- ============================================================================
-- VERIFICATION 5 - INSTALLED FINAL-BOSS REWARDS
--
-- Expected: 26 rows, each with Chance = 100, MinCount = MaxCount = 1,
-- Reference = 0, QuestRequired = 0, LootMode = 1 and GroupId = 0.
-- ============================================================================


SELECT
    `reward`.`DungeonName`,
    `reward`.`EncounterName`,
    `reward`.`CreatureEntry`,
    `ct`.`lootid`,
    `reward`.`CurioItem`,
    `it`.`name` AS `CurrencyName`,
    `clt`.`Reference`,
    `clt`.`Chance`,
    `clt`.`QuestRequired`,
    `clt`.`LootMode`,
    `clt`.`GroupId`,
    `clt`.`MinCount`,
    `clt`.`MaxCount`
FROM `tmp_dark_rider_dungeon_rewards` AS `reward`
LEFT JOIN `creature_template` AS `ct`
    ON `ct`.`entry` = `reward`.`CreatureEntry`
LEFT JOIN `item_template` AS `it`
    ON `it`.`entry` = `reward`.`CurioItem`
LEFT JOIN `creature_loot_template` AS `clt`
    ON `clt`.`Entry` = `ct`.`lootid`
   AND `clt`.`Item` = `reward`.`CurioItem`
ORDER BY `reward`.`CurioItem`;


-- ============================================================================
-- VERIFICATION 6 - MISSING OR MISCONFIGURED REWARDS
--
-- Expected: ZERO rows. A successful run defines 26 valid rewards.
-- ============================================================================


SELECT
    `reward`.`DungeonName`,
    `reward`.`CreatureEntry`,
    `reward`.`CurioItem`
FROM `tmp_dark_rider_dungeon_rewards` AS `reward`
LEFT JOIN `creature_template` AS `ct`
    ON `ct`.`entry` = `reward`.`CreatureEntry`
LEFT JOIN `item_template` AS `it`
    ON `it`.`entry` = `reward`.`CurioItem`
LEFT JOIN `creature_loot_template` AS `clt`
    ON `clt`.`Entry` = `ct`.`lootid`
   AND `clt`.`Item` = `reward`.`CurioItem`
WHERE `it`.`entry` IS NULL
   OR (`it`.`Flags` & 2048) = 0
   OR `it`.`BagFamily` <> 0
   OR `clt`.`Entry` IS NULL
   OR `clt`.`Reference` <> 0
   OR `clt`.`Chance` <> 100
   OR `clt`.`QuestRequired` <> 0
   OR `clt`.`LootMode` <> 1
   OR `clt`.`GroupId` <> 0
   OR `clt`.`MinCount` <> 1
   OR `clt`.`MaxCount` <> 1
ORDER BY `reward`.`CurioItem`;


-- ============================================================================
-- CLEANUP
-- ============================================================================


DROP TEMPORARY TABLE IF EXISTS `tmp_dark_rider_dungeon_rewards`;
