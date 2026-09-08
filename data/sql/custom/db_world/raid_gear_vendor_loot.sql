-- ============================================================================
-- DARK RIDERS - RAID CURIOS
-- Boss loot / Bad Luck Protection
--
-- Molten Core       : 1 curio per encounter
-- Blackwing Lair    : 1 curio per encounter
-- Ahn'Qiraj 40      : 2 curios per encounter
-- Naxxramas 40      : 1 curio per encounter
--
-- Currencies:
--   90002 = Molten Core Curio
--   90003 = Blackwing Lair Curio
--   90004 = Ahn'Qiraj Curio
--   90005 = Naxxramas Curio
--
-- Designed for:
--   AzerothCore + Grimfeather/mod-individual-progression
-- ============================================================================

USE `acore_world`;

START TRANSACTION;


-- ============================================================================
-- CONFIGURATION
-- ============================================================================

SET @MC_CURIO   := 90002;
SET @BWL_CURIO  := 90003;
SET @AQ40_CURIO := 90004;
SET @NAXX_CURIO := 90005;

-- ITEM_FLAG_MULTI_DROP
-- Allows each eligible raid member to receive their own copy.
SET @ITEM_FLAG_MULTI_DROP := 2048;


-- ============================================================================
-- MAKE CURIOS FREE-FOR-ALL / MULTI-DROP
--
-- Grimfeather LootMgr:
-- ITEM_FLAG_MULTI_DROP -> freeforall
--
-- Since these items also have BagFamily = 8192 (Currency Tokens),
-- AzerothCore will automatically award them to every eligible group member
-- within loot reward distance.
-- ============================================================================

UPDATE `item_template`
SET `Flags` = `Flags` | @ITEM_FLAG_MULTI_DROP
WHERE `entry` IN
    (
    @MC_CURIO,
    @BWL_CURIO,
    @AQ40_CURIO,
    @NAXX_CURIO
    );


-- ============================================================================
-- TEMPORARY BOSS REWARD TABLE
--
-- We store CREATURE ENTRY here, not lootid.
-- Later we resolve creature_template.lootid dynamically.
--
-- This is safer because lootid does not necessarily equal creature entry.
-- ============================================================================

DROP TEMPORARY TABLE IF EXISTS `tmp_dark_rider_boss_rewards`;

CREATE TEMPORARY TABLE `tmp_dark_rider_boss_rewards`
(
    `CreatureEntry` INT UNSIGNED NOT NULL,
    `CurioItem`     INT UNSIGNED NOT NULL,
    `CurioCount`    TINYINT UNSIGNED NOT NULL,
    `RaidName`      VARCHAR(64) NOT NULL,
    `EncounterName` VARCHAR(100) NOT NULL,

    PRIMARY KEY (`CreatureEntry`, `CurioItem`)
);


-- ============================================================================
-- MOLTEN CORE
-- 1 Curio per encounter
--
-- Majordomo Executus is deliberately NOT here.
-- His reward is handled through Cache of the Firelord further below.
-- ============================================================================

INSERT INTO `tmp_dark_rider_boss_rewards`
VALUES

    (12118, @MC_CURIO, 1, 'Molten Core', 'Lucifron'),
    (11982, @MC_CURIO, 1, 'Molten Core', 'Magmadar'),
    (12259, @MC_CURIO, 1, 'Molten Core', 'Gehennas'),
    (12057, @MC_CURIO, 1, 'Molten Core', 'Garr'),
    (12056, @MC_CURIO, 1, 'Molten Core', 'Baron Geddon'),
    (12264, @MC_CURIO, 1, 'Molten Core', 'Shazzrah'),
    (12098, @MC_CURIO, 1, 'Molten Core', 'Sulfuron Harbinger'),
    (11988, @MC_CURIO, 1, 'Molten Core', 'Golemagg the Incinerator'),
    (11502, @MC_CURIO, 1, 'Molten Core', 'Ragnaros');


-- ============================================================================
-- BLACKWING LAIR
-- 1 Curio per encounter
-- ============================================================================

INSERT INTO `tmp_dark_rider_boss_rewards`
VALUES

    (12435, @BWL_CURIO, 1, 'Blackwing Lair', 'Razorgore the Untamed'),
    (13020, @BWL_CURIO, 1, 'Blackwing Lair', 'Vaelastrasz the Corrupt'),
    (12017, @BWL_CURIO, 1, 'Blackwing Lair', 'Broodlord Lashlayer'),
    (11983, @BWL_CURIO, 1, 'Blackwing Lair', 'Firemaw'),
    (14601, @BWL_CURIO, 1, 'Blackwing Lair', 'Ebonroc'),
    (11981, @BWL_CURIO, 1, 'Blackwing Lair', 'Flamegor'),
    (14020, @BWL_CURIO, 1, 'Blackwing Lair', 'Chromaggus'),
    (11583, @BWL_CURIO, 1, 'Blackwing Lair', 'Nefarian');


-- ============================================================================
-- AHN'QIRAJ 40
-- 2 Curios per encounter
--
-- BUG TRIO:
-- All three entries receive 2 curios because only the final surviving boss
-- becomes lootable. This gives 2 curios regardless of kill order.
--
-- TWIN EMPERORS:
-- Each emperor receives 1 curio, giving 2 total for the encounter.
-- ============================================================================

INSERT INTO `tmp_dark_rider_boss_rewards`
VALUES

-- Prophet Skeram
(15263, @AQ40_CURIO, 2, 'Ahn''Qiraj', 'The Prophet Skeram'),

-- Bug Trio - only final corpse is lootable
(15511, @AQ40_CURIO, 2, 'Ahn''Qiraj', 'Lord Kri'),
(15543, @AQ40_CURIO, 2, 'Ahn''Qiraj', 'Princess Yauj'),
(15544, @AQ40_CURIO, 2, 'Ahn''Qiraj', 'Vem'),

-- Remaining encounters
(15516, @AQ40_CURIO, 2, 'Ahn''Qiraj', 'Battleguard Sartura'),
(15510, @AQ40_CURIO, 2, 'Ahn''Qiraj', 'Fankriss the Unyielding'),
(15299, @AQ40_CURIO, 2, 'Ahn''Qiraj', 'Viscidus'),
(15509, @AQ40_CURIO, 2, 'Ahn''Qiraj', 'Princess Huhuran'),

-- Twin Emperors: 1 + 1 = 2 per encounter
(15275, @AQ40_CURIO, 1, 'Ahn''Qiraj', 'Emperor Vek''nilash'),
(15276, @AQ40_CURIO, 1, 'Ahn''Qiraj', 'Emperor Vek''lor'),

(15517, @AQ40_CURIO, 2, 'Ahn''Qiraj', 'Ouro'),
(15727, @AQ40_CURIO, 2, 'Ahn''Qiraj', 'C''Thun');


-- ============================================================================
-- NAXXRAMAS 40 - GRIMFEATHER
-- 1 Curio per encounter
--
-- IMPORTANT:
-- These are the custom Naxx40 creature entries introduced by
-- mod-individual-progression, NOT the normal WotLK Naxx entries.
--
-- Four Horsemen is handled separately through its chest.
-- ============================================================================

INSERT INTO `tmp_dark_rider_boss_rewards`
VALUES

-- Spider Wing
(351009, @NAXX_CURIO, 1, 'Naxxramas', 'Anub''Rekhan'),
(351007, @NAXX_CURIO, 1, 'Naxxramas', 'Grand Widow Faerlina'),
(351006, @NAXX_CURIO, 1, 'Naxxramas', 'Maexxna'),

-- Plague Wing
(351008, @NAXX_CURIO, 1, 'Naxxramas', 'Noth the Plaguebringer'),
(351005, @NAXX_CURIO, 1, 'Naxxramas', 'Heigan the Unclean'),
(351020, @NAXX_CURIO, 1, 'Naxxramas', 'Loatheb'),

-- Military Wing
(351036, @NAXX_CURIO, 1, 'Naxxramas', 'Instructor Razuvious'),
(351035, @NAXX_CURIO, 1, 'Naxxramas', 'Gothik the Harvester'),

-- Construct Wing
(351028, @NAXX_CURIO, 1, 'Naxxramas', 'Patchwerk'),
(351003, @NAXX_CURIO, 1, 'Naxxramas', 'Grobbulus'),
(351004, @NAXX_CURIO, 1, 'Naxxramas', 'Gluth'),
(351000, @NAXX_CURIO, 1, 'Naxxramas', 'Thaddius'),

-- Frostwyrm Lair
(351018, @NAXX_CURIO, 1, 'Naxxramas', 'Sapphiron'),
(351019, @NAXX_CURIO, 1, 'Naxxramas', 'Kel''Thuzad');


-- ============================================================================
-- REMOVE PREVIOUS CUSTOM CURRENCY DROPS
--
-- We resolve the real lootid through creature_template instead of assuming
-- lootid == CreatureEntry.
-- ============================================================================

DELETE `clt`
FROM `creature_loot_template` AS `clt`
INNER JOIN `creature_template` AS `ct`
    ON `ct`.`lootid` = `clt`.`Entry`
INNER JOIN `tmp_dark_rider_boss_rewards` AS `reward`
    ON `reward`.`CreatureEntry` = `ct`.`entry`
   AND `reward`.`CurioItem` = `clt`.`Item`;


-- ============================================================================
-- INSERT BOSS CURRENCY DROPS
--
-- Chance        = 100%
-- QuestRequired = 0
-- LootMode      = 1
-- GroupId       = 0 (standalone guaranteed drop)
-- MinCount      = exact desired quantity
-- MaxCount      = exact desired quantity
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
            `reward`.`RaidName`,
            ' - ',
            `reward`.`EncounterName`
    )
FROM `tmp_dark_rider_boss_rewards` AS `reward`
         INNER JOIN `creature_template` AS `ct`
                    ON `ct`.`entry` = `reward`.`CreatureEntry`
WHERE `ct`.`lootid` <> 0;


-- ============================================================================
-- MOLTEN CORE - MAJORDOMO EXECUTUS
--
-- Majordomo does not use a normal boss corpse reward.
-- Cache of the Firelord:
--     gameobject entry = 179703
--
-- For chest gameobjects, Data1 points to gameobject_loot_template.Entry.
-- ============================================================================

DELETE `glt`
FROM `gameobject_loot_template` AS `glt`
INNER JOIN `gameobject_template` AS `got`
    ON `got`.`Data1` = `glt`.`Entry`
WHERE `got`.`entry` = 179703
  AND `got`.`type` = 3
  AND `glt`.`Item` = @MC_CURIO;


INSERT INTO `gameobject_loot_template`
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
    `Data1`,
    @MC_CURIO,
    0,
    100,
    0,
    1,
    0,
    1,
    1,
    'Dark Rider BLP - Molten Core - Majordomo Executus'
FROM `gameobject_template`
WHERE `entry` = 179703
  AND `type` = 3
  AND `Data1` <> 0;


-- ============================================================================
-- NAXXRAMAS 40 - FOUR HORSEMEN
--
-- Grimfeather's Naxx40 implementation rewards this encounter through
-- its custom Four Horsemen chest rather than one individual horseman.
--
-- gameobject entry = 361000
-- Data1 points to its gameobject loot template.
-- ============================================================================

DELETE `glt`
FROM `gameobject_loot_template` AS `glt`
INNER JOIN `gameobject_template` AS `got`
    ON `got`.`Data1` = `glt`.`Entry`
WHERE `got`.`entry` = 361000
  AND `got`.`type` = 3
  AND `glt`.`Item` = @NAXX_CURIO;


INSERT INTO `gameobject_loot_template`
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
    `Data1`,
    @NAXX_CURIO,
    0,
    100,
    0,
    1,
    0,
    1,
    1,
    'Dark Rider BLP - Naxxramas - The Four Horsemen'
FROM `gameobject_template`
WHERE `entry` = 361000
  AND `type` = 3
  AND `Data1` <> 0;


COMMIT;


-- ============================================================================
-- VERIFICATION 1
-- Currency item flags
-- ============================================================================

SELECT
    `entry`,
    `name`,
    `Flags`,
    (`Flags` & 2048) AS `HasMultiDropFlag`,
    `BagFamily`,
    (`BagFamily` & 8192) AS `IsCurrencyToken`
FROM `item_template`
WHERE `entry` IN
      (
       @MC_CURIO,
       @BWL_CURIO,
       @AQ40_CURIO,
       @NAXX_CURIO
          )
ORDER BY `entry`;


-- ============================================================================
-- VERIFICATION 2
-- Detect missing bosses / bosses without lootid
--
-- THIS QUERY SHOULD RETURN ZERO ROWS.
-- ============================================================================

SELECT
    `reward`.`RaidName`,
    `reward`.`EncounterName`,
    `reward`.`CreatureEntry`,
    `ct`.`name` AS `DatabaseName`,
    `ct`.`lootid`
FROM `tmp_dark_rider_boss_rewards` AS `reward`
         LEFT JOIN `creature_template` AS `ct`
                   ON `ct`.`entry` = `reward`.`CreatureEntry`
WHERE `ct`.`entry` IS NULL
   OR `ct`.`lootid` = 0;


-- ============================================================================
-- VERIFICATION 3
-- Show all creature rewards actually installed
-- ============================================================================

SELECT
    `reward`.`RaidName`,
    `reward`.`EncounterName`,
    `reward`.`CreatureEntry`,
    `ct`.`lootid`,
    `clt`.`Item`,
    `it`.`name` AS `CurrencyName`,
    `clt`.`Chance`,
    `clt`.`MinCount`,
    `clt`.`MaxCount`
FROM `tmp_dark_rider_boss_rewards` AS `reward`
         INNER JOIN `creature_template` AS `ct`
                    ON `ct`.`entry` = `reward`.`CreatureEntry`
         LEFT JOIN `creature_loot_template` AS `clt`
                   ON `clt`.`Entry` = `ct`.`lootid`
                       AND `clt`.`Item` = `reward`.`CurioItem`
         LEFT JOIN `item_template` AS `it`
                   ON `it`.`entry` = `reward`.`CurioItem`
ORDER BY
    `reward`.`RaidName`,
    `reward`.`EncounterName`;


-- ============================================================================
-- VERIFICATION 4
-- Special chest rewards
-- ============================================================================

SELECT
    `got`.`entry` AS `GameObjectEntry`,
    `got`.`name`,
    `got`.`Data1` AS `LootID`,
    `glt`.`Item`,
    `it`.`name` AS `CurrencyName`,
    `glt`.`MinCount`,
    `glt`.`MaxCount`
FROM `gameobject_template` AS `got`
         LEFT JOIN `gameobject_loot_template` AS `glt`
                   ON `glt`.`Entry` = `got`.`Data1`
                       AND `glt`.`Item` IN (@MC_CURIO, @NAXX_CURIO)
         LEFT JOIN `item_template` AS `it`
                   ON `it`.`entry` = `glt`.`Item`
WHERE `got`.`entry` IN
      (
       179703, -- Cache of the Firelord
       361000  -- Grimfeather Naxx40 Four Horsemen Chest
          );


DROP TEMPORARY TABLE IF EXISTS `tmp_dark_rider_boss_rewards`;