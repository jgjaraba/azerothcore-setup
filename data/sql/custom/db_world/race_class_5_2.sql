USE acore_world;

-- ============================================================
-- Forsaken Paladin Trainers
--
-- 90210 = Full trainer    -> TrainerId 4
-- 90211 = Starter trainer -> TrainerId 6
--
-- Full template based on Dark Cleric Beryl (2129, Brill)
-- Starter template based on Dark Cleric Duesten (2123, Deathknell)
-- ============================================================

SET @FULL_ENTRY       := 90210;
SET @STARTER_ENTRY    := 90211;

SET @FULL_SOURCE      := 2129; -- Dark Cleric Beryl, Brill
SET @STARTER_SOURCE   := 2123; -- Dark Cleric Duesten, Deathknell

SET @FULL_TRAINER     := 4;
SET @STARTER_TRAINER  := 6;


-- ============================================================
-- SAFETY CHECK
-- Execute this SELECT first if desired.
-- Both entries should return no rows before first installation.
-- ============================================================

SELECT
    entry,
    name,
    subname
FROM creature_template
WHERE entry IN (@FULL_ENTRY, @STARTER_ENTRY);


START TRANSACTION;


-- ============================================================
-- CLEAN PREVIOUS INSTALLATION
-- Makes the script re-runnable.
-- ============================================================

DELETE FROM creature
WHERE id IN (@FULL_ENTRY, @STARTER_ENTRY);

DELETE FROM creature_default_trainer
WHERE CreatureId IN (@FULL_ENTRY, @STARTER_ENTRY);

DELETE FROM creature_template_locale
WHERE entry IN (@FULL_ENTRY, @STARTER_ENTRY);

DELETE FROM creature_equip_template
WHERE CreatureID IN (@FULL_ENTRY, @STARTER_ENTRY);

DELETE FROM creature_template_model
WHERE CreatureID IN (@FULL_ENTRY, @STARTER_ENTRY);

DELETE FROM creature_template
WHERE entry IN (@FULL_ENTRY, @STARTER_ENTRY);


-- ============================================================
-- 1. FULL FORSAKEN PALADIN TRAINER
-- Base: Dark Cleric Beryl (2129), Brill
-- ============================================================

DROP TEMPORARY TABLE IF EXISTS tmp_paladin_full;

CREATE TEMPORARY TABLE tmp_paladin_full
LIKE creature_template;

INSERT INTO tmp_paladin_full
SELECT *
FROM creature_template
WHERE entry = @FULL_SOURCE;

UPDATE tmp_paladin_full
SET
    entry          = @FULL_ENTRY,
    name           = 'Abraham West',
    subname        = 'Paladin Trainer',
    IconName       = 'Trainer',
    gossip_menu_id = 0,
    npcflag        = 49,
    ScriptName     = '',
    VerifiedBuild  = 0;

INSERT INTO creature_template
SELECT *
FROM tmp_paladin_full;

DROP TEMPORARY TABLE tmp_paladin_full;


-- Copy Beryl's model.
INSERT INTO creature_template_model
(
    CreatureID,
    Idx,
    CreatureDisplayID,
    DisplayScale,
    Probability,
    VerifiedBuild
)
SELECT
    @FULL_ENTRY,
    Idx,
    CreatureDisplayID,
    DisplayScale,
    Probability,
    0
FROM creature_template_model
WHERE CreatureID = @FULL_SOURCE;


-- Copy equipment if Beryl has any.
INSERT INTO creature_equip_template
(
    CreatureID,
    ID,
    ItemID1,
    ItemID2,
    ItemID3,
    VerifiedBuild
)
SELECT
    @FULL_ENTRY,
    ID,
    ItemID1,
    ItemID2,
    ItemID3,
    0
FROM creature_equip_template
WHERE CreatureID = @FULL_SOURCE;


-- Associate with Horde Paladin trainer.
INSERT INTO creature_default_trainer
(
    CreatureId,
    TrainerId
)
VALUES
    (
        @FULL_ENTRY,
        @FULL_TRAINER
    );


-- ============================================================
-- 2. STARTER FORSAKEN PALADIN TRAINER
-- Base: Dark Cleric Duesten (2123), Deathknell
-- ============================================================

DROP TEMPORARY TABLE IF EXISTS tmp_paladin_starter;

CREATE TEMPORARY TABLE tmp_paladin_starter
LIKE creature_template;

INSERT INTO tmp_paladin_starter
SELECT *
FROM creature_template
WHERE entry = @STARTER_SOURCE;

UPDATE tmp_paladin_starter
SET
    entry          = @STARTER_ENTRY,
    name           = 'Pancratius Ward',
    subname        = 'Paladin Trainer',
    IconName       = 'Trainer',
    gossip_menu_id = 0,
    npcflag        = 49,
    ScriptName     = '',
    VerifiedBuild  = 0;

INSERT INTO creature_template
SELECT *
FROM tmp_paladin_starter;

DROP TEMPORARY TABLE tmp_paladin_starter;


-- Copy Duesten's model.
INSERT INTO creature_template_model
(
    CreatureID,
    Idx,
    CreatureDisplayID,
    DisplayScale,
    Probability,
    VerifiedBuild
)
SELECT
    @STARTER_ENTRY,
    Idx,
    CreatureDisplayID,
    DisplayScale,
    Probability,
    0
FROM creature_template_model
WHERE CreatureID = @STARTER_SOURCE;


-- Copy equipment if Duesten has any.
INSERT INTO creature_equip_template
(
    CreatureID,
    ID,
    ItemID1,
    ItemID2,
    ItemID3,
    VerifiedBuild
)
SELECT
    @STARTER_ENTRY,
    ID,
    ItemID1,
    ItemID2,
    ItemID3,
    0
FROM creature_equip_template
WHERE CreatureID = @STARTER_SOURCE;


-- Associate with restricted starter Paladin trainer.
INSERT INTO creature_default_trainer
(
    CreatureId,
    TrainerId
)
VALUES
    (
        @STARTER_ENTRY,
        @STARTER_TRAINER
    );


-- ============================================================
-- 3. esES LOCALIZATION
-- ============================================================

INSERT INTO creature_template_locale
(
    entry,
    locale,
    Name,
    Title,
    VerifiedBuild
)
VALUES
    (
        @FULL_ENTRY,
        'esES',
        'Abraham West',
        'Instructor de paladines',
        0
    ),
    (
        @STARTER_ENTRY,
        'esES',
        'Pancratius Ward',
        'Instructor de paladines',
        0
    );


COMMIT;



SET @TARGET := 90210;
SET @SOURCE := 23779; -- Brother Wilhelm

DELETE FROM creature_equip_template
WHERE CreatureID = @TARGET;

INSERT INTO creature_equip_template
(
    CreatureID,
    ID,
    ItemID1,
    ItemID2,
    ItemID3,
    VerifiedBuild
)
SELECT
    @TARGET,
    ID,
    ItemID1,
    ItemID2,
    ItemID3,
    0
FROM creature_equip_template
WHERE CreatureID = @SOURCE;

UPDATE creature
SET equipment_id = 1
WHERE id = @TARGET;





USE acore_world;

DELETE FROM creature_template_model
WHERE CreatureID IN (90210, 90211);

INSERT INTO creature_template_model
(CreatureID, Idx, CreatureDisplayID, DisplayScale, Probability, VerifiedBuild)
VALUES
    (90210, 0, 4342, 1, 1, 0),
    (90211, 0, 2654, 1, 1, 0);