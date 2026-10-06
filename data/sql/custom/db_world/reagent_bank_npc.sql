-- ============================================================
-- Reagent Bank Account - NPC customization
--
-- NPC entry: 190012
--
-- Changes:
--   * Generic neutral-looking goblin banker model
--   * Custom English name/title
--   * esES / esMX localization
--   * Spawns in all 8 faction capitals
--
-- Safe to re-run / idempotent.
-- Existing spawns belonging to the module are NOT removed.
-- ============================================================

SET @NPC_ENTRY := 190012;
SET @MODEL_SOURCE_ENTRY := 2625; -- Viznik Goldgrubber <Banker>


-- ============================================================
-- 1. NAME AND TITLE
-- ============================================================

UPDATE `creature_template`
SET
    `name`    = 'Rizzik Copperstash',
    `subname` = 'Reagent Banker'
WHERE `entry` = @NPC_ENTRY;


-- ============================================================
-- 2. GOBLIN MODEL
--
-- Reuse Viznik Goldgrubber's model from the installed ACDB.
-- This avoids depending on a hardcoded CreatureDisplayID.
-- ============================================================

DELETE FROM `creature_template_model`
WHERE `CreatureID` = @NPC_ENTRY;

INSERT INTO `creature_template_model`
(
    `CreatureID`,
    `Idx`,
    `CreatureDisplayID`,
    `DisplayScale`,
    `Probability`,
    `VerifiedBuild`
)
SELECT
    @NPC_ENTRY,
    0,
    `CreatureDisplayID`,
    `DisplayScale`,
    1.0,
    NULL
FROM `creature_template_model`
WHERE `CreatureID` = @MODEL_SOURCE_ENTRY
ORDER BY `Idx`
    LIMIT 1;


-- ============================================================
-- 3. SPANISH LOCALIZATION
--
-- Default / enUS:
--   Rizzik Copperstash
--   <Reagent Banker>
--
-- esES / esMX:
--   Rizzik Guardacobre
--   <Banquero de componentes>
-- ============================================================

INSERT INTO `creature_template_locale`
(
    `entry`,
    `locale`,
    `Name`,
    `Title`,
    `VerifiedBuild`
)
VALUES
    (
        @NPC_ENTRY,
        'esES',
        'Rizzik Guardacobre',
        'Banquero de componentes',
        NULL
    ),
    (
        @NPC_ENTRY,
        'esMX',
        'Rizzik Guardacobre',
        'Banquero de componentes',
        NULL
    )
    ON DUPLICATE KEY UPDATE
                         `Name`          = VALUES(`Name`),
                         `Title`         = VALUES(`Title`),
                         `VerifiedBuild` = VALUES(`VerifiedBuild`);


-- ============================================================
-- 4. CAPITAL CITY SPAWNS
--
-- Map IDs:
--   0   Eastern Kingdoms
--   1   Kalimdor
--   530 Outland / TBC world (Silvermoon + Exodar)
--
-- Only spawns created by THIS script are removed.
-- Existing module/manual spawns are preserved.
-- ============================================================

DELETE FROM `creature`
WHERE `id` = @NPC_ENTRY
  AND `Comment` IN
      (
       'Custom Reagent Bank - Orgrimmar',
       'Custom Reagent Bank - Undercity',
       'Custom Reagent Bank - Thunder Bluff',
       'Custom Reagent Bank - Silvermoon City',
       'Custom Reagent Bank - Stormwind City',
       'Custom Reagent Bank - Ironforge',
       'Custom Reagent Bank - Darnassus',
       'Custom Reagent Bank - Exodar'
          );


INSERT INTO `creature`
(
    `id`,
    `map`,
    `zoneId`,
    `areaId`,
    `spawnMask`,
    `phaseMask`,
    `equipment_id`,
    `position_x`,
    `position_y`,
    `position_z`,
    `orientation`,
    `spawntimesecs`,
    `wander_distance`,
    `currentwaypoint`,
    `curhealth`,
    `curmana`,
    `MovementType`,
    `npcflag`,
    `unit_flags`,
    `dynamicflags`,
    `Comment`
)
VALUES

-- ------------------------------------------------------------
-- HORDE
-- ------------------------------------------------------------

-- Orgrimmar
(
    @NPC_ENTRY,
    1,
    0,
    0,
    1,
    1,
    0,
    1621.8923,
    -4385.306,
    12.514554,
    0.8851048,
    300,
    0,
    0,
    1,
    0,
    0,
    0,
    0,
    0,
    'Custom Reagent Bank - Orgrimmar'
),

-- Undercity
(
    @NPC_ENTRY,
    0,
    0,
    0,
    1,
    1,
    0,
    1585.8442,
    249.90082,
    -52.14907,
    5.3660097,
    300,
    0,
    0,
    1,
    0,
    0,
    0,
    0,
    0,
    'Custom Reagent Bank - Undercity'
),

-- Thunder Bluff
(
    @NPC_ENTRY,
    1,
    0,
    0,
    1,
    1,
    0,
    -1265.4512,
    47.623966,
    127.785995,
    0.7624653,
    300,
    0,
    0,
    1,
    0,
    0,
    0,
    0,
    0,
    'Custom Reagent Bank - Thunder Bluff'
),

-- Silvermoon City
(
    @NPC_ENTRY,
    530,
    0,
    0,
    1,
    1,
    0,
    9508.673,
    -7206.846,
    16.153944,
    6.2378216,
    300,
    0,
    0,
    1,
    0,
    0,
    0,
    0,
    0,
    'Custom Reagent Bank - Silvermoon City'
),


-- ------------------------------------------------------------
-- ALLIANCE
-- ------------------------------------------------------------

-- Stormwind City
(
    @NPC_ENTRY,
    0,
    0,
    0,
    1,
    1,
    0,
    -8911.802,
    612.35187,
    99.5229,
    1.9025854,
    300,
    0,
    0,
    1,
    0,
    0,
    0,
    0,
    0,
    'Custom Reagent Bank - Stormwind City'
),

-- Ironforge
(
    @NPC_ENTRY,
    0,
    0,
    0,
    1,
    1,
    0,
    -4902.705,
    -999.0135,
    503.94098,
    0.66631633,
    300,
    0,
    0,
    1,
    0,
    0,
    0,
    0,
    0,
    'Custom Reagent Bank - Ironforge'
),

-- Darnassus
(
    @NPC_ENTRY,
    1,
    0,
    0,
    1,
    1,
    0,
    9926.524,
    2507.917,
    1318.2577,
    4.839561,
    300,
    0,
    0,
    1,
    0,
    0,
    0,
    0,
    0,
    'Custom Reagent Bank - Darnassus'
),

-- Exodar
(
    @NPC_ENTRY,
    530,
    0,
    0,
    1,
    1,
    0,
    -3931.1128,
    -11560.196,
    -150.33945,
    6.227419,
    300,
    0,
    0,
    1,
    0,
    0,
    0,
    0,
    0,
    'Custom Reagent Bank - Exodar'
);


-- ============================================================
-- 5. VERIFICATION
-- ============================================================

SELECT
    ct.`entry`,
    ct.`name`,
    ct.`subname`,
    ctm.`CreatureDisplayID`,
    ctm.`DisplayScale`
FROM `creature_template` ct
         LEFT JOIN `creature_template_model` ctm
                   ON ctm.`CreatureID` = ct.`entry`
WHERE ct.`entry` = @NPC_ENTRY;


SELECT
    `entry`,
    `locale`,
    `Name`,
    `Title`
FROM `creature_template_locale`
WHERE `entry` = @NPC_ENTRY
  AND `locale` IN ('esES', 'esMX')
ORDER BY `locale`;


SELECT
    `guid`,
    `id`,
    `map`,
    `position_x`,
    `position_y`,
    `position_z`,
    `orientation`,
    `Comment`
FROM `creature`
WHERE `id` = @NPC_ENTRY
ORDER BY `map`, `guid`;