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
-- ============================================================================
-- 1. Riding trainers
-- ============================================================================

-- Apprentice Riding:

UPDATE `trainer_spell`
SET `ReqLevel` = 20
WHERE `SpellID` = 33388
  AND `ReqLevel` = 40;

-- Journeyman Riding:

-- UPDATE `trainer_spell`
-- SET `ReqLevel` = 40
-- WHERE `SpellID` = 33391
--   AND `ReqLevel` = 60;


-- ============================================================================
-- 2. Monturas raciales lentas (Riding 75)
-- ============================================================================

UPDATE `item_template`
SET `RequiredLevel` = 30
WHERE `entry` IN (
    2411,   -- Black Stallion
    2414,   -- Pinto
    5655,   -- Chestnut Mare
    5656,   -- Brown Horse
    5864,   -- Gray Ram
    5872,   -- Brown Ram
    5873,   -- White Ram
    8563,   -- Red Mechanostrider
    8595,   -- Blue Mechanostrider
    13321,  -- Green Mechanostrider
    13322,  -- Unpainted Mechanostrider
    13323,  -- Purple Mechanostrider
    13324,  -- Red and Blue Mechanostrider
    8629,   -- Striped Nightsaber
    8631,   -- Striped Frostsaber
    8632,   -- Spotted Frostsaber
    47100,  -- Striped Dawnsaber
    1132,   -- Timber Wolf
    5665,   -- Dire Wolf
    5668,   -- Brown Wolf
    8588,   -- Emerald Raptor
    8591,   -- Turquoise Raptor
    8592,   -- Violet Raptor
    13331,  -- Red Skeletal Horse
    13332,  -- Blue Skeletal Horse
    13333,  -- Brown Skeletal Horse
    15277,  -- Gray Kodo
    15290   -- Brown Kodo
)
AND `RequiredSkill` = 762
AND `RequiredSkillRank` = 75
AND `RequiredLevel` = 40;


-- ============================================================================
-- 3. Monturas raciales rápidas (Riding 150)
-- ============================================================================

-- UPDATE `item_template`
-- SET `RequiredLevel` = 40
-- WHERE `entry` IN (
--     -- Alliance
--     12302,  -- Frostsaber
--     12303,  -- Nightsaber
--     18766,  -- Swift Frostsaber
--     18767,  -- Swift Mistsaber
--     18768,  -- Swift Dawnsaber
--     18902,  -- Swift Stormsaber
--
--     13326,  -- White Mechanostrider Mod A
--     13327,  -- Icy Blue Mechanostrider Mod A
--     18772,  -- Swift Green Mechanostrider
--     18773,  -- Swift White Mechanostrider
--     18774,  -- Swift Yellow Mechanostrider
--
--     12353,  -- White Stallion
--     12354,  -- Palomino
--     18776,  -- Swift Palomino
--     18777,  -- Swift Brown Steed
--     18778,  -- Swift White Steed
--
--     13328,  -- Black Ram
--     13329,  -- Frost Ram
--     18785,  -- Swift White Ram
--     18786,  -- Swift Brown Ram
--     18787,  -- Swift Gray Ram
--
--     -- Horde
--     8586,   -- Mottled Red Raptor
--     13317,  -- Ivory Raptor
--     18788,  -- Swift Blue Raptor
--     18789,  -- Swift Olive Raptor
--     18790,  -- Swift Orange Raptor
--
--     13334,  -- Green Skeletal Warhorse
--     18791,  -- Purple Skeletal Warhorse
--
--     15292,  -- Green Kodo
--     15293,  -- Teal Kodo
--     18793,  -- Great White Kodo
--     18794,  -- Great Brown Kodo
--     18795,  -- Great Gray Kodo
--
--     12330,  -- Red Wolf
--     12351,  -- Arctic Wolf
--     18796,  -- Swift Brown Wolf
--     18797,  -- Swift Timber Wolf
--     18798   -- Swift Gray Wolf
-- )
-- AND `RequiredSkill` = 762
-- AND `RequiredSkillRank` = 150
-- AND `RequiredLevel` = 60;


-- ============================================================================
-- 4. Verificación
-- ============================================================================

SELECT
    `SpellID`,
    `MoneyCost`,
    `ReqSkillLine`,
    `ReqSkillRank`,
    `ReqLevel`
FROM `trainer_spell`
WHERE `SpellID` IN (33388, 33391, 34090, 34091)
ORDER BY `SpellID`;

SELECT
    `RequiredSkillRank`,
    `RequiredLevel`,
    COUNT(*) AS `Items`
FROM `item_template`
WHERE `RequiredSkill` = 762
GROUP BY `RequiredSkillRank`, `RequiredLevel`
ORDER BY `RequiredSkillRank`, `RequiredLevel`;
