-- ============================================================================
-- AzerothCore + mod-individual-progression
-- Override WotLK ground riding levels
--
-- Objetivo:
--   - Apprentice Riding (33388): nivel 40 -> 20
--   - Journeyman Riding (33391): nivel 60 -> 40
--   - Monturas raciales terrestres lentas: nivel 40 -> 20
--   - Monturas raciales terrestres rápidas: nivel 60 -> 40
--
-- NO modifica:
--   - Precios de instrucción
--   - Expert/Artisan Riding
--   - Vuelo
--   - Monturas especiales (ZG, AQ, Deathcharger, Winterspring, Alterac, etc.)
--   - Condiciones, fases o lógica de Individual Progression
--
-- Diseñado para poder ejecutarse repetidamente tras actualizaciones.
-- ============================================================================

USE `acore_world`;

-- Apprentice Riding:
UPDATE `trainer_spell`
SET `ReqLevel` = 30
WHERE `SpellID` = 33388

-- Journeyman Riding:
UPDATE `trainer_spell`
SET `ReqLevel` = 60
WHERE `SpellID` = 33391


USE `acore_world`;

START TRANSACTION;

UPDATE `item_template`
SET `RequiredLevel` = 30
WHERE `RequiredSkill` = 762
  AND `RequiredSkillRank` = 75
  AND `RequiredLevel` <> 30;

UPDATE `item_template`
SET `RequiredLevel` = 60
WHERE `RequiredSkill` = 762
  AND `RequiredSkillRank` = 150
  AND `RequiredLevel` <> 60;

-- Verification summary
SELECT
    `RequiredSkill`,
    `RequiredSkillRank`,
    `RequiredLevel`,
    COUNT(*) AS `Items`
FROM `item_template`
WHERE `RequiredSkill` = 762
  AND `RequiredSkillRank` IN (75, 150)
GROUP BY
    `RequiredSkill`,
    `RequiredSkillRank`,
    `RequiredLevel`
ORDER BY
    `RequiredSkillRank`,
    `RequiredLevel`;

-- This should return zero rows
SELECT
    `entry`,
    `Name`,
    `RequiredLevel`,
    `RequiredSkill`,
    `RequiredSkillRank`
FROM `item_template`
WHERE `RequiredSkill` = 762
  AND (
    (`RequiredSkillRank` = 75  AND `RequiredLevel` <> 30)
        OR (`RequiredSkillRank` = 150 AND `RequiredLevel` <> 60)
    )
ORDER BY
    `RequiredSkillRank`,
    `RequiredLevel`,
    `entry`;

COMMIT;

USE acore_world;

START TRANSACTION;

-- ============================================================
-- Individual Progression
-- Normalize newly-unlocked racial mounts
--
-- Apprentice / 60%:
--   Level 30
--   Riding 75
--   10 gold
--
-- Journeyman / 100%:
--   Level 60
--   Riding 150
--   100 gold
-- ============================================================


-- ------------------------------------------------------------
-- 60% racial mounts
-- ------------------------------------------------------------

UPDATE `item_template`
SET
    `Quality` = 3,
    `BuyPrice` = 100000,
    `RequiredLevel` = 30,
    `RequiredSkill` = 762,
    `RequiredSkillRank` = 75
WHERE `entry` IN (
                  46099, -- Horn of the Black Wolf
                  46100, -- White Kodo
                  46308  -- Black Skeletal Horse
    );


-- ------------------------------------------------------------
-- 100% racial mounts
-- ------------------------------------------------------------

UPDATE `item_template`
SET
    `Quality` = 4,
    `BuyPrice` = 1000000,
    `RequiredLevel` = 60,
    `RequiredSkill` = 762,
    `RequiredSkillRank` = 150
WHERE `entry` = 47101; -- Ochre Skeletal Warhorse


COMMIT;
