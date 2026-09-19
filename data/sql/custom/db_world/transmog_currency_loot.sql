-- ============================================================
-- AzerothCore - Moneda de Transfiguracion
-- Item ID: 90001
-- Objetivo:
--   * Crear/actualizar el item 90001 en item_template.
--   * Configurar su localizacion esES.
--   * Configurar drops 100% en contenido relevante de nivel 60.
--   * ITEM_FLAG_MULTI_DROP (2048) para loot individual/FFA por jugador.
--   * Drops separados por contenido para facilitar mantenimiento.
--
-- IMPORTANTE:
--   creature_loot_template.Entry usa creature_template.lootid,
--   no necesariamente creature_template.entry.
-- ============================================================

USE `acore_world`;

START TRANSACTION;

SET @TRANSMOG_TOKEN := 90001;

-- ============================================================
-- 0. CONFIGURACION DEL OBJETO
-- ============================================================

-- Idempotent creation/update of the Transmogrification Mark item.
-- If AzerothCore or a module ever changes this row, re-running this script
-- restores the intended custom values.
INSERT INTO `item_template`
(
    `entry`,
    `class`,
    `subclass`,
    `name`,
    `displayid`,
    `Quality`,
    `Flags`,
    `FlagsExtra`,
    `BuyCount`,
    `BuyPrice`,
    `SellPrice`,
    `InventoryType`,
    `AllowableClass`,
    `AllowableRace`,
    `ItemLevel`,
    `RequiredLevel`,
    `maxcount`,
    `stackable`,
    `bonding`,
    `description`,
    `BagFamily`,
    `VerifiedBuild`
)
VALUES
(
    @TRANSMOG_TOKEN,
    15,                                         -- Miscellaneous
    0,                                          -- Junk/Misc subclass
    'Transmogrification Mark',
    40753,                                      -- Icon/display ID
    3,                                          -- Rare quality
    2048,                                       -- ITEM_FLAG_MULTI_DROP
    0,
    1,
    0,
    0,
    0,                                          -- Non-equippable
    -1,
    -1,
    1,
    1,
    0,
    200,
    1,                                          -- Bind on Pickup
    'Awarded for overcoming challenging content. Used for transmogrification.',
    0,
    0
)
AS new_row
ON DUPLICATE KEY UPDATE
    `class`          = new_row.`class`,
    `subclass`       = new_row.`subclass`,
    `name`           = new_row.`name`,
    `displayid`      = new_row.`displayid`,
    `Quality`        = new_row.`Quality`,
    `Flags`          = new_row.`Flags`,
    `FlagsExtra`     = new_row.`FlagsExtra`,
    `BuyCount`       = new_row.`BuyCount`,
    `BuyPrice`       = new_row.`BuyPrice`,
    `SellPrice`      = new_row.`SellPrice`,
    `InventoryType`  = new_row.`InventoryType`,
    `AllowableClass` = new_row.`AllowableClass`,
    `AllowableRace`  = new_row.`AllowableRace`,
    `ItemLevel`      = new_row.`ItemLevel`,
    `RequiredLevel`  = new_row.`RequiredLevel`,
    `maxcount`       = new_row.`maxcount`,
    `stackable`      = new_row.`stackable`,
    `bonding`        = new_row.`bonding`,
    `description`    = new_row.`description`,
    `BagFamily`      = new_row.`BagFamily`,
    `VerifiedBuild`  = new_row.`VerifiedBuild`;

-- Ensure the multi-drop flag is always set, even if a previous value survived.
UPDATE `item_template`
SET `Flags` = `Flags` | 2048
WHERE `entry` = @TRANSMOG_TOKEN;

-- Spanish localization.
INSERT INTO `item_template_locale`
(
    `ID`,
    `locale`,
    `Name`,
    `Description`,
    `VerifiedBuild`
)
VALUES
    (
        @TRANSMOG_TOKEN,
        'esES',
        'Marca de Transfiguración',
        'Otorgada por superar desafíos. Se utiliza para transfigurar objetos.',
        0
    )
AS new_locale
ON DUPLICATE KEY UPDATE
    `Name`          = new_locale.`Name`,
    `Description`   = new_locale.`Description`,
    `VerifiedBuild` = new_locale.`VerifiedBuild`;


-- ============================================================
-- 1. MAZMORRAS NIVEL 55-60
-- 1 Marca en el jefe final de cada ruta/ala
-- ============================================================
-- BRD         : Emperor Dagran Thaurissan (9019)
-- LBRS        : Overlord Wyrmthalak (9568)
-- UBRS        : General Drakkisath (10363)
-- Scholomance : Darkmaster Gandling (1853)
-- Strat UD    : Baron Rivendare (10440)
-- Strat Live  : Balnazzar (10813)
-- Dire Maul E : Alzzin the Wildshaper (11492)
-- Dire Maul W : Prince Tortheldrin (11486)
-- Dire Maul N : King Gordok (11501)

DELETE clt
FROM `creature_loot_template` clt
INNER JOIN `creature_template` ct ON ct.`lootid` = clt.`Entry`
WHERE clt.`Item` = @TRANSMOG_TOKEN
  AND ct.`entry` IN (
      9019, 9568, 10363, 1853, 10440, 10813, 11492, 11486, 11501
  );

INSERT INTO `creature_loot_template`
(
    `Entry`, `Item`, `Reference`, `Chance`, `QuestRequired`,
    `LootMode`, `GroupId`, `MinCount`, `MaxCount`, `Comment`
)
SELECT
    ct.`lootid`,
    @TRANSMOG_TOKEN,
    0,
    100,
    0,
    1,
    0,
    1,
    1,
    CONCAT('Marca de Transfiguracion - ', ct.`name`)
FROM `creature_template` ct
WHERE ct.`entry` IN (
                     9019, 9568, 10363, 1853, 10440, 10813, 11492, 11486, 11501
    )
  AND ct.`lootid` <> 0;


-- ============================================================
-- 2. ONYXIA'S LAIR
-- Onyxia: 2 Marcas
-- ============================================================

DELETE clt
FROM `creature_loot_template` clt
INNER JOIN `creature_template` ct ON ct.`lootid` = clt.`Entry`
WHERE clt.`Item` = @TRANSMOG_TOKEN
  AND ct.`entry` = 10184;

INSERT INTO `creature_loot_template`
(
    `Entry`, `Item`, `Reference`, `Chance`, `QuestRequired`,
    `LootMode`, `GroupId`, `MinCount`, `MaxCount`, `Comment`
)
SELECT
    ct.`lootid`,
    @TRANSMOG_TOKEN,
    0,
    100,
    0,
    1,
    0,
    2,
    2,
    CONCAT('Marca de Transfiguracion - ', ct.`name`)
FROM `creature_template` ct
WHERE ct.`entry` = 10184
  AND ct.`lootid` <> 0;


-- ============================================================
-- 3. MOLTEN CORE
-- Boss normal: 1 Marca
-- Ragnaros:    3 Marcas
-- Total run:  12 Marcas
-- ============================================================
-- 12118 Lucifron
-- 11982 Magmadar
-- 12259 Gehennas
-- 12057 Garr
-- 12264 Shazzrah
-- 12056 Baron Geddon
-- 12098 Sulfuron Harbinger
-- 11988 Golemagg the Incinerator
-- 12018 Majordomo Executus
-- 11502 Ragnaros

DELETE clt
FROM `creature_loot_template` clt
INNER JOIN `creature_template` ct ON ct.`lootid` = clt.`Entry`
WHERE clt.`Item` = @TRANSMOG_TOKEN
  AND ct.`entry` IN (
      12118, 11982, 12259, 12057, 12264,
      12056, 12098, 11988, 12018, 11502
  );

INSERT INTO `creature_loot_template`
(
    `Entry`, `Item`, `Reference`, `Chance`, `QuestRequired`,
    `LootMode`, `GroupId`, `MinCount`, `MaxCount`, `Comment`
)
SELECT
    ct.`lootid`,
    @TRANSMOG_TOKEN,
    0,
    100,
    0,
    1,
    0,
    CASE WHEN ct.`entry` = 11502 THEN 3 ELSE 1 END,
    CASE WHEN ct.`entry` = 11502 THEN 3 ELSE 1 END,
    CONCAT('Marca de Transfiguracion - ', ct.`name`)
FROM `creature_template` ct
WHERE ct.`entry` IN (
                     12118, 11982, 12259, 12057, 12264,
                     12056, 12098, 11988, 12018, 11502
    )
  AND ct.`lootid` <> 0;


-- ============================================================
-- 4. ZUL'GURUB
-- Hakkar: 2 Marcas
-- ============================================================

DELETE clt
FROM `creature_loot_template` clt
INNER JOIN `creature_template` ct ON ct.`lootid` = clt.`Entry`
WHERE clt.`Item` = @TRANSMOG_TOKEN
  AND ct.`entry` = 14834;

INSERT INTO `creature_loot_template`
(
    `Entry`, `Item`, `Reference`, `Chance`, `QuestRequired`,
    `LootMode`, `GroupId`, `MinCount`, `MaxCount`, `Comment`
)
SELECT
    ct.`lootid`,
    @TRANSMOG_TOKEN,
    0,
    100,
    0,
    1,
    0,
    2,
    2,
    CONCAT('Marca de Transfiguracion - ', ct.`name`)
FROM `creature_template` ct
WHERE ct.`entry` = 14834
  AND ct.`lootid` <> 0;


-- ============================================================
-- 5. RUINS OF AHN'QIRAJ (AQ20)
-- Ossirian the Unscarred: 2 Marcas
-- ============================================================

DELETE clt
FROM `creature_loot_template` clt
INNER JOIN `creature_template` ct ON ct.`lootid` = clt.`Entry`
WHERE clt.`Item` = @TRANSMOG_TOKEN
  AND ct.`entry` = 15339;

INSERT INTO `creature_loot_template`
(
    `Entry`, `Item`, `Reference`, `Chance`, `QuestRequired`,
    `LootMode`, `GroupId`, `MinCount`, `MaxCount`, `Comment`
)
SELECT
    ct.`lootid`,
    @TRANSMOG_TOKEN,
    0,
    100,
    0,
    1,
    0,
    2,
    2,
    CONCAT('Marca de Transfiguracion - ', ct.`name`)
FROM `creature_template` ct
WHERE ct.`entry` = 15339
  AND ct.`lootid` <> 0;


-- ============================================================
-- 6. BLACKWING LAIR
-- Boss normal: 1 Marca
-- Nefarian:    3 Marcas
-- Total run:  10 Marcas
-- ============================================================

DELETE clt
FROM `creature_loot_template` clt
INNER JOIN `creature_template` ct ON ct.`lootid` = clt.`Entry`
WHERE clt.`Item` = @TRANSMOG_TOKEN
  AND ct.`entry` IN (
      12435, 13020, 12017, 11983,
      14601, 11981, 14020, 11583
  );

INSERT INTO `creature_loot_template`
(
    `Entry`, `Item`, `Reference`, `Chance`, `QuestRequired`,
    `LootMode`, `GroupId`, `MinCount`, `MaxCount`, `Comment`
)
SELECT
    ct.`lootid`,
    @TRANSMOG_TOKEN,
    0,
    100,
    0,
    1,
    0,
    CASE WHEN ct.`entry` = 11583 THEN 3 ELSE 1 END,
    CASE WHEN ct.`entry` = 11583 THEN 3 ELSE 1 END,
    CONCAT('Marca de Transfiguracion - ', ct.`name`)
FROM `creature_template` ct
WHERE ct.`entry` IN (
                     12435, 13020, 12017, 11983,
                     14601, 11981, 14020, 11583
    )
  AND ct.`lootid` <> 0;


-- ============================================================
-- 7. TEMPLE OF AHN'QIRAJ (AQ40)
-- C'Thun: 3 Marcas
-- ============================================================

DELETE clt
FROM `creature_loot_template` clt
INNER JOIN `creature_template` ct ON ct.`lootid` = clt.`Entry`
WHERE clt.`Item` = @TRANSMOG_TOKEN
  AND ct.`entry` = 15727;

INSERT INTO `creature_loot_template`
(
    `Entry`, `Item`, `Reference`, `Chance`, `QuestRequired`,
    `LootMode`, `GroupId`, `MinCount`, `MaxCount`, `Comment`
)
SELECT
    ct.`lootid`,
    @TRANSMOG_TOKEN,
    0,
    100,
    0,
    1,
    0,
    3,
    3,
    CONCAT('Marca de Transfiguracion - ', ct.`name`)
FROM `creature_template` ct
WHERE ct.`entry` = 15727
  AND ct.`lootid` <> 0;


-- ============================================================
-- 8. NAXXRAMAS (NIVEL 60 / INDIVIDUAL PROGRESSION)
-- Kel'Thuzad: 3 Marcas
-- ============================================================

DELETE clt
FROM `creature_loot_template` clt
INNER JOIN `creature_template` ct ON ct.`lootid` = clt.`Entry`
WHERE clt.`Item` = @TRANSMOG_TOKEN
  AND ct.`entry` = 15990;

INSERT INTO `creature_loot_template`
(
    `Entry`, `Item`, `Reference`, `Chance`, `QuestRequired`,
    `LootMode`, `GroupId`, `MinCount`, `MaxCount`, `Comment`
)
SELECT
    ct.`lootid`,
    @TRANSMOG_TOKEN,
    0,
    100,
    0,
    1,
    0,
    3,
    3,
    CONCAT('Marca de Transfiguracion - ', ct.`name`)
FROM `creature_template` ct
WHERE ct.`entry` = 15990
  AND ct.`lootid` <> 0;

COMMIT;
