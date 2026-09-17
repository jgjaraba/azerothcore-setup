USE `acore_world`;

START TRANSACTION;

-- ============================================================================
-- DARK RIDER RAID VENDORS
-- ============================================================================

-- Custom CreatureDisplayInfo.dbc ID
SET @DISPLAY_DARK_RIDER := 90100;

-- Creature template IDs
SET @NPC_MC   := 90200;
SET @NPC_BWL  := 90201;
SET @NPC_AQ40 := 90202;
SET @NPC_NAXX := 90203;


-- ============================================================================
-- CLEAN PREVIOUS VERSION
-- ============================================================================

DELETE FROM `creature_template_locale`
WHERE `entry` IN
      (
       @NPC_MC,
       @NPC_BWL,
       @NPC_AQ40,
       @NPC_NAXX
          );

DELETE FROM `creature_template_model`
WHERE `CreatureID` IN
      (
       @NPC_MC,
       @NPC_BWL,
       @NPC_AQ40,
       @NPC_NAXX
          );

DELETE FROM `creature_template`
WHERE `entry` IN
      (
       @NPC_MC,
       @NPC_BWL,
       @NPC_AQ40,
       @NPC_NAXX
          );


-- ============================================================================
-- CREATURE TEMPLATES
--
-- faction 35     = friendly/neutral NPC faction
-- npcflag 128    = vendor
-- unit_flags 2   = non-attackable
-- type 7         = humanoid
-- AIName PassiveAI
-- MovementType 0 = idle
-- ============================================================================

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

-- ============================================================================
-- MOLTEN CORE
-- ============================================================================
(
    @NPC_MC,
    'Dark Rider',
    'Collector of Molten Relics',
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

-- ============================================================================
-- BLACKWING LAIR
-- ============================================================================
(
    @NPC_BWL,
    'Dark Rider',
    'Collector of Draconic Relics',
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

-- ============================================================================
-- AHN'QIRAJ
-- ============================================================================
(
    @NPC_AQ40,
    'Dark Rider',
    'Collector of Qiraji Relics',
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

-- ============================================================================
-- NAXXRAMAS
-- ============================================================================
(
    @NPC_NAXX,
    'Dark Rider',
    'Collector of Desecrated Relics',
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
--
-- All four Dark Riders currently use the same custom display.
-- ============================================================================

INSERT INTO `creature_template_model`
(
    `CreatureID`,
    `Idx`,
    `CreatureDisplayID`,
    `DisplayScale`,
    `Probability`,
    `VerifiedBuild`
)
VALUES
    (@NPC_MC,   0, @DISPLAY_DARK_RIDER, 1, 1, 0),
    (@NPC_BWL,  0, @DISPLAY_DARK_RIDER, 1, 1, 0),
    (@NPC_AQ40, 0, @DISPLAY_DARK_RIDER, 1, 1, 0),
    (@NPC_NAXX, 0, @DISPLAY_DARK_RIDER, 1, 1, 0);

-- ============================================================================
-- SPANISH LOCALIZATION
-- ============================================================================

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
        @NPC_MC,
        'esES',
        'Jinete Oscuro',
        'Coleccionista de reliquias ígneas',
        -1
    ),

    (
        @NPC_BWL,
        'esES',
        'Jinete Oscuro',
        'Coleccionista de reliquias dracónicas',
        -1
    ),

    (
        @NPC_AQ40,
        'esES',
        'Jinete Oscuro',
        'Coleccionista de reliquias qiraji',
        -1
    ),

    (
        @NPC_NAXX,
        'esES',
        'Jinete Oscuro',
        'Coleccionista de reliquias profanadas',
        -1
    );


COMMIT;


-- ============================================================================
-- VERIFICATION
-- ============================================================================

SELECT
    `entry`,
    `name`,
    `subname`,
    `faction`,
    `npcflag`,
    `AIName`,
    `MovementType`
FROM `creature_template`
WHERE `entry` IN
      (
       @NPC_MC,
       @NPC_BWL,
       @NPC_AQ40,
       @NPC_NAXX
          )
ORDER BY `entry`;


SELECT
    `CreatureID`,
    `CreatureDisplayID`,
    `DisplayScale`,
    `Probability`
FROM `creature_template_model`
WHERE `CreatureID` IN
      (
       @NPC_MC,
       @NPC_BWL,
       @NPC_AQ40,
       @NPC_NAXX
          )
ORDER BY `CreatureID`;


SELECT
    `entry`,
    `locale`,
    `Name`,
    `Title`
FROM `creature_template_locale`
WHERE `entry` IN
      (
       @NPC_MC,
       @NPC_BWL,
       @NPC_AQ40,
       @NPC_NAXX
          )
ORDER BY `entry`;


START TRANSACTION;

-- ADD GOSSIP MENU
UPDATE creature_template
SET
    npcflag = 129,
    gossip_menu_id = CASE entry
                         WHEN 90200 THEN 92000
                         WHEN 90201 THEN 92001
                         WHEN 90202 THEN 92002
                         WHEN 90203 THEN 92003
        END
WHERE entry IN (90200, 90201, 90202, 90203);

DELETE FROM npc_text
WHERE ID IN (92000, 92001, 92002, 92003);

INSERT INTO npc_text
(
    ID,
    text0_0,
    text0_1,
    BroadcastTextID0,
    lang0,
    Probability0,
    em0_0,
    em0_1,
    em0_2,
    em0_3,
    em0_4,
    em0_5,
    VerifiedBuild
)
VALUES

    (
        92000,
        'The fire leaves its mark even upon that which it cannot consume. Show me what you have recovered from the depths.',
        'The fire leaves its mark even upon that which it cannot consume. Show me what you have recovered from the depths.',
        0,
        0,
        1,
        0,0,0,0,0,0,
        0
    ),

    (
        92001,
        'The Black Dragonflight hoards relics as dragons hoard gold. Some deserve a different keeper.',
        'The Black Dragonflight hoards relics as dragons hoard gold. Some deserve a different keeper.',
        0,
        0,
        1,
        0,0,0,0,0,0,
        0
    ),

    (
        92002,
        'There are things beneath those sands that should have remained buried. Others are worth a great deal to the right collector.',
        'There are things beneath those sands that should have remained buried. Others are worth a great deal to the right collector.',
        0,
        0,
        1,
        0,0,0,0,0,0,
        0
    ),

    (
        92003,
        'Death clings to objects much as it clings to souls. Let me see what you have brought from the necropolis.',
        'Death clings to objects much as it clings to souls. Let me see what you have brought from the necropolis.',
        0,
        0,
        1,
        0,0,0,0,0,0,
        0
    );


DELETE FROM gossip_menu
WHERE MenuID IN (92000, 92001, 92002, 92003);

INSERT INTO gossip_menu
(
    MenuID,
    TextID
)
VALUES
    (92000, 92000),
    (92001, 92001),
    (92002, 92002),
    (92003, 92003);


DELETE FROM gossip_menu_option
WHERE MenuID IN (92000, 92001, 92002, 92003);

INSERT INTO gossip_menu_option
(
    MenuID,
    OptionID,
    OptionIcon,
    OptionText,
    OptionBroadcastTextID,
    OptionType,
    OptionNpcFlag,
    ActionMenuID,
    ActionPoiID,
    BoxCoded,
    BoxMoney,
    BoxText,
    BoxBroadcastTextID,
    VerifiedBuild
)
VALUES

    (
        92000,
        0,
        1,
        'Show me the relics of Molten Core.',
        0,
        3,
        128,
        0,
        0,
        0,
        0,
        '',
        0,
        0
    ),

    (
        92001,
        0,
        1,
        'Show me the relics of Blackwing Lair.',
        0,
        3,
        128,
        0,
        0,
        0,
        0,
        '',
        0,
        0
    ),

    (
        92002,
        0,
        1,
        'Show me the relics of the Temple of Ahn\'Qiraj.',
        0,
        3,
        128,
        0,
        0,
        0,
        0,
        '',
        0,
        0
    ),

    (
        92003,
        0,
        1,
        'Show me the relics of Naxxramas.',
        0,
        3,
        128,
        0,
        0,
        0,
        0,
        '',
        0,
        0
    );

DELETE FROM npc_text_locale
WHERE ID IN (92000, 92001, 92002, 92003)
  AND locale = 'esES';

INSERT INTO npc_text_locale
(
    ID,
    locale,
    Text0_0,
    Text0_1
)
VALUES

    (
        92000,
        'esES',
        'El fuego deja su marca incluso sobre aquello que no puede consumir. Muéstrame lo que has recuperado de las profundidades.',
        'El fuego deja su marca incluso sobre aquello que no puede consumir. Muéstrame lo que has recuperado de las profundidades.'
    ),

    (
        92001,
        'esES',
        'El Vuelo Negro acumula reliquias como los dragones acumulan oro. Algunas merecen un custodio diferente.',
        'El Vuelo Negro acumula reliquias como los dragones acumulan oro. Algunas merecen un custodio diferente.'
    ),

    (
        92002,
        'esES',
        'Hay cosas bajo esas arenas que deberían haber permanecido enterradas. Otras valen mucho para el coleccionista adecuado.',
        'Hay cosas bajo esas arenas que deberían haber permanecido enterradas. Otras valen mucho para el coleccionista adecuado.'
    ),

    (
        92003,
        'esES',
        'La muerte se aferra a los objetos del mismo modo que a las almas. Déjame ver qué has traído de la necrópolis.',
        'La muerte se aferra a los objetos del mismo modo que a las almas. Déjame ver qué has traído de la necrópolis.'
    );

DELETE FROM gossip_menu_option_locale
WHERE MenuID IN (92000, 92001, 92002, 92003)
  AND Locale = 'esES';

INSERT INTO gossip_menu_option_locale
(
    MenuID,
    OptionID,
    Locale,
    OptionText,
    BoxText
)
VALUES
    (92000, 0, 'esES', 'Muéstrame las reliquias del Núcleo de Magma.', ''),
    (92001, 0, 'esES', 'Muéstrame las reliquias de la Guarida de Alanegra.', ''),
    (92002, 0, 'esES', 'Muéstrame las reliquias del Templo de Ahn\'Qiraj.', ''),
    (92003, 0, 'esES', 'Muéstrame las reliquias de Naxxramas.', '');


UPDATE `creature_template`
SET
    `IconName`            = 'Speak',
    `npcflag`             = `npcflag` | 4096,
    `type_flags`          = `type_flags` | 0x08000000
WHERE `entry` IN (90200, 90201, 90202, 90203);

COMMIT;


-- ============================================================================
-- SPAWNS
--
-- Each Dark Rider stands near the entrance of its associated raid, on stable
-- ground and clear of portals/triggers.
--
-- IMPORTANT: CreatureDisplayID 90100 is an intentional custom display. It must
-- be present in the server's CreatureDisplayInfo.dbc (and in the client patch)
-- for the NPC to render. If it is missing, the NPC will be invisible/unknown
-- model but the vendor functionality will still work server-side.
-- ============================================================================

START TRANSACTION;

DELETE FROM `creature`
WHERE `guid` IN (900000, 900001, 900002, 900003)
  AND `id` IN (90200, 90201, 90202, 90203);

INSERT INTO `creature`
(
    `guid`,
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
    `MovementType`,
    `npcflag`,
    `unit_flags`,
    `dynamicflags`,
    `VerifiedBuild`,
    `CreateObject`,
    `Comment`
)
VALUES
    -- Molten Core: Blackrock Mountain, near the Molten Core entrance.
    (900000, 90200, 0, 0, 0, 1, 1, 0,
     -7523.3477, -1080.9742, 177.48135, 5.5566907,
     300, 0, 0, 4225, 0, 0, 0, 0,
     'Dark Rider - Molten Core vendor'),

    -- Blackwing Lair: Blackrock Mountain, near the Orb of Command.
    (900001, 90201, 0, 0, 0, 1, 1, 0,
     -7662.351, -1214.0305, 287.7885, 1.1198819,
     300, 0, 0, 4225, 0, 0, 0, 0,
     'Dark Rider - Blackwing Lair vendor'),

    -- Ahn'Qiraj Temple: Gates of Ahn'Qiraj, near the AQ40 entrance.
    (900002, 90202, 1, 0, 0, 1, 1, 0,
     -8471.158, 1843.6754, 78.4028, 0.27567154,
     300, 0, 0, 4225, 0, 0, 0, 0,
     'Dark Rider - Ahn\'Qiraj Temple vendor'),

    -- Naxxramas: Eastern Plaguelands / Plaguewood, near the Naxxramas entrance.
    (900003, 90203, 0, 0, 0, 1, 1, 0,
     3064.0972, -3805.824, 124.75007, 2.9153957,
     300, 0, 0, 4225, 0, 0, 0, 0,
     'Dark Rider - Naxxramas vendor');

COMMIT;
