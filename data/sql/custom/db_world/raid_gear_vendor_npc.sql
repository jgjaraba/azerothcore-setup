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

DELETE FROM `npc_vendor`
WHERE `entry` IN
      (
       @NPC_MC,
       @NPC_BWL,
       @NPC_AQ40,
       @NPC_NAXX
          );

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
    (@NPC_MC,   0, @DISPLAY_DARK_RIDER, 1, 1, -1),
    (@NPC_BWL,  0, @DISPLAY_DARK_RIDER, 1, 1, -1),
    (@NPC_AQ40, 0, @DISPLAY_DARK_RIDER, 1, 1, -1),
    (@NPC_NAXX, 0, @DISPLAY_DARK_RIDER, 1, 1, -1);


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


USE acore_world;

DELETE FROM creature_template_model
WHERE CreatureID IN (90200, 90201, 90202, 90203);

INSERT INTO creature_template_model
(
    CreatureID,
    Idx,
    CreatureDisplayID,
    DisplayScale,
    Probability,
    VerifiedBuild
)
VALUES
    (90200, 0, 90100, 1.0, 1.0, 0),
    (90201, 0, 90100, 1.0, 1.0, 0),
    (90202, 0, 90100, 1.0, 1.0, 0),
    (90203, 0, 90100, 1.0, 1.0, 0);


USE acore_world;

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
        'Show me your collection.',
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
        'Show me your collection.',
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
        'Show me your collection.',
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
        'Show me your collection.',
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
    (92000, 0, 'esES', 'Muéstrame tu colección.', ''),
    (92001, 0, 'esES', 'Muéstrame tu colección.', ''),
    (92002, 0, 'esES', 'Muéstrame tu colección.', ''),
    (92003, 0, 'esES', 'Muéstrame tu colección.', '');


UPDATE creature_template
SET
    IconName = 'Speak',
    npcflag = 129
WHERE entry IN (90200, 90201, 90202, 90203);