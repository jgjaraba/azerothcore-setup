-- ============================================================================
-- Dark Riders - Raid Curios
-- Bad Luck Protection currencies
--
-- 90002 - Molten Core Curio
-- 90003 - Blackwing Lair Curio
-- 90004 - Ahn'Qiraj Curio
-- 90005 - Naxxramas Curio
--
-- AzerothCore 3.3.5a
-- Database: acore_world
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

-- Native item used as structural template.
-- Badge of Justice is already configured as a non-equippable token.
SET @BASE_ITEM := 29434;


-- ============================================================================
-- CLEAN PREVIOUS VERSIONS
-- ============================================================================

DELETE FROM `item_template_locale`
WHERE `ID` IN (@MC_CURIO, @BWL_CURIO, @AQ40_CURIO, @NAXX_CURIO);

DELETE FROM `item_template`
WHERE `entry` IN (@MC_CURIO, @BWL_CURIO, @AQ40_CURIO, @NAXX_CURIO);


-- ============================================================================
-- TEMPORARY TEMPLATE
--
-- Using LIKE + SELECT * makes this compatible with the complete item_template
-- structure of the installed AzerothCore database without having to hardcode
-- every column.
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
-- MOLTEN CORE CURIO
-- ============================================================================

UPDATE `tmp_currency_token`
SET
    `entry`          = @MC_CURIO,
    `class`          = 15,
    `subclass`       = 0,
    `name`           = 'Molten Core Curio',
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
    `description`    = 'A fire-scarred relic recovered from the depths of Blackrock Mountain. A collector of rare artifacts might find value in it.',
    `VerifiedBuild`  = 0;

INSERT INTO `item_template`
SELECT *
FROM `tmp_currency_token`;


-- ============================================================================
-- BLACKWING LAIR CURIO
-- ============================================================================

UPDATE `tmp_currency_token`
SET
    `entry`          = @BWL_CURIO,
    `class`          = 15,
    `subclass`       = 0,
    `name`           = 'Blackwing Lair Curio',
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
    `displayid`      = 19502,
    `AllowableClass` = -1,
    `AllowableRace`  = -1,
    `ItemLevel`      = 1,
    `RequiredLevel`  = 1,
    `maxcount`       = 0,
    `stackable`      = 200,
    `bonding`        = 1,
    `description`    = 'A dark remnant bearing the unmistakable mark of the Black Dragonflight. A collector of rare artifacts might find value in it.',
    `VerifiedBuild`  = 0;

INSERT INTO `item_template`
SELECT *
FROM `tmp_currency_token`;


-- ============================================================================
-- AHN'QIRAJ CURIO
-- ============================================================================

UPDATE `tmp_currency_token`
SET
    `entry`          = @AQ40_CURIO,
    `class`          = 15,
    `subclass`       = 0,
    `name`           = 'Ahn''Qiraj Curio',
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
    `displayid`      = 34143,
    `AllowableClass` = -1,
    `AllowableRace`  = -1,
    `ItemLevel`      = 1,
    `RequiredLevel`  = 1,
    `maxcount`       = 0,
    `stackable`      = 200,
    `bonding`        = 1,
    `description`    = 'An ancient Qiraji relic covered in markings that seem to shift at the edge of sight. Best not studied for too long. A collector of rare artifacts might find value in it.',
    `VerifiedBuild`  = 0;

INSERT INTO `item_template`
SELECT *
FROM `tmp_currency_token`;


-- ============================================================================
-- NAXXRAMAS CURIO
-- ============================================================================

UPDATE `tmp_currency_token`
SET
    `entry`          = @NAXX_CURIO,
    `class`          = 15,
    `subclass`       = 0,
    `name`           = 'Naxxramas Curio',
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
    `displayid`      = 35350,
    `AllowableClass` = -1,
    `AllowableRace`  = -1,
    `ItemLevel`      = 1,
    `RequiredLevel`  = 1,
    `maxcount`       = 0,
    `stackable`      = 200,
    `bonding`        = 1,
    `description`    = 'A desecrated relic recovered from the necropolis. It remains deathly cold no matter how long it is held. A collector of rare artifacts might find value in it.',
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

-- Molten Core
(
    @MC_CURIO,
    'esES',
    'Curiosidad del Núcleo de Magma',
    'Una reliquia marcada por el fuego, recuperada de las profundidades de la Montaña Roca Negra. Un coleccionista de artefactos extraños podría encontrarle valor.',
    -1
),

-- Blackwing Lair
(
    @BWL_CURIO,
    'esES',
    'Curiosidad de la Guarida de Alanegra',
    'Un oscuro vestigio que porta la inconfundible marca del Vuelo Negro. Un coleccionista de artefactos extraños podría encontrarle valor.',
    -1
),

-- Ahn'Qiraj
(
    @AQ40_CURIO,
    'esES',
    'Curiosidad de Ahn''Qiraj',
    'Una antigua reliquia qiraji cubierta de marcas que parecen cambiar cuando se observan de soslayo. Quizá sea mejor no estudiarla durante demasiado tiempo. Un coleccionista de artefactos extraños podría encontrarle valor.',
    -1
),

-- Naxxramas
(
    @NAXX_CURIO,
    'esES',
    'Curiosidad de Naxxramas',
    'Una reliquia profanada recuperada de la necrópolis. Permanece gélida al tacto sin importar cuánto tiempo se sostenga. Un coleccionista de artefactos extraños podría encontrarle valor.',
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
WHERE `entry` IN (@MC_CURIO, @BWL_CURIO, @AQ40_CURIO, @NAXX_CURIO)
ORDER BY `entry`;

SELECT
    `ID`,
    `locale`,
    `Name`,
    `Description`
FROM `item_template_locale`
WHERE `ID` IN (@MC_CURIO, @BWL_CURIO, @AQ40_CURIO, @NAXX_CURIO)
ORDER BY `ID`, `locale`;