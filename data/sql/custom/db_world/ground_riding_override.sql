-- ============================================================================
-- AzerothCore / Grimfeather Individual Progression
-- Ground mount level override: slow = 30, fast = 60
--
-- Idempotent: safe to execute repeatedly.
-- Scope:
--   * Apprentice Riding (33388) -> level 30
--   * Journeyman Riding (33391) -> level 60
--   * Ground mount items requiring Riding 75 -> level 30
--   * Ground mount items requiring Riding 150 -> level 60
--   * Known fixed-100%-speed ground mounts that exceptionally require Riding 75
--     (or have no normal Riding requirement) -> level 60
--   * Mount rows explicitly rewritten by mod-individual-progression are covered
--     defensively even if their RequiredSkill metadata differs.
--
-- Deliberately NOT modified:
--   * MoneyCost, BuyPrice, SellPrice, or any other price field
--   * Flying mount requirements (Riding 225/300)
--   * Mount quality, name, reputation requirements, vendor conditions, etc.
--   * Class mount quest/spell progression (Paladin/Warlock/Death Knight)
--
-- IMPORTANT: execute against the WORLD database, AFTER Individual Progression's
-- mounts_and_riding.sql / module DB updates.
-- ============================================================================

START TRANSACTION;

-- --------------------------------------------------------------------------
-- 1. Riding training levels only. Prices are intentionally left untouched.
-- --------------------------------------------------------------------------
UPDATE `trainer_spell`
SET `ReqLevel` = 30
WHERE `SpellID` = 33388
  AND `ReqLevel` <> 30;

UPDATE `trainer_spell`
SET `ReqLevel` = 60
WHERE `SpellID` = 33391
  AND `ReqLevel` <> 60;

-- --------------------------------------------------------------------------
-- 2. Generic slow ground mounts.
--
-- AzerothCore:
--   class    15 = Miscellaneous
--   subclass  5 = Mount
--   skill    762 = Riding
--   rank      75 = Apprentice Riding
--
-- Most Riding-75 mounts are 60% ground mounts. Fixed 100% exceptions are
-- excluded here and forced to level 60 later.
-- --------------------------------------------------------------------------
UPDATE `item_template`
SET `RequiredLevel` = 30
WHERE `class` = 15
  AND `subclass` = 5
  AND `RequiredSkill` = 762
  AND `RequiredSkillRank` = 75
  AND `entry` NOT IN (
      -- Fixed 100% ground mounts with the unusual Riding-75 requirement
      13086,                         -- Reins of the Winterspring Frostsaber
      18241, 18242, 18243, 18244,   -- Legacy Black War mounts (Alliance)
      18245, 18246, 18247, 18248,   -- Legacy Black War mounts (Horde)
      21218, 21321, 21323, 21324,   -- Qiraji Battle Tanks (100% in AQ40)
      46102,                         -- Whistle of the Venomhide Ravasaur
      52200                          -- Reins of the Crimson Deathcharger
  )
  AND `RequiredLevel` <> 30;

-- --------------------------------------------------------------------------
-- 3. Defensive override for every 60% ground mount explicitly changed by
--    mod-individual-progression's mounts_and_riding.sql.
--
-- This also covers legacy/unavailable rows whose old metadata may not use the
-- modern generic Riding skill in exactly the same way.
-- --------------------------------------------------------------------------
UPDATE `item_template`
SET `RequiredLevel` = 30
WHERE `entry` IN (
    -- Alliance 60%
    2411, 2414, 5655, 5656, 5864, 5872, 5873,
    8563, 8595, 13321, 13322, 13323, 13324,
    8629, 8631, 8632, 47100,

    -- Horde 60%
    1132, 5665, 5668, 8588, 8591, 8592,
    13331, 13332, 13333, 15277, 15290,

    -- Legacy/unavailable 60% mounts restored/touched by Individual Progression
    1133, 1134, 5663, 8583, 8589, 8590,
    8628, 8630, 8633, 12325, 12326, 12327, 13325,

    -- Additional legacy 60% terrestrial mount rows present in 3.3.5 data.
    -- These may retain pre-1.12 race-specific riding-skill metadata instead
    -- of RequiredSkill=762, so the generic rule above cannot safely catch them.
    5874,                          -- Harness: Black Ram
    5875,                          -- Harness: Blue Ram
    8627,                          -- Reins of the Nightsaber (legacy placeholder)
    14062,                         -- Kodo Mount
    16338,                         -- Knight-Lieutenant's Steed
    16343                          -- Blood Guard's Mount
)
AND `RequiredLevel` <> 30;

-- --------------------------------------------------------------------------
-- 4. Generic fast terrestrial mounts.
--
-- Riding 150 is Journeyman Riding and, for normal terrestrial mount items,
-- corresponds to the 100% ground-mount tier. Flying mounts require higher
-- Riding ranks (225/300), so they are deliberately not matched here.
-- --------------------------------------------------------------------------
UPDATE `item_template`
SET `RequiredLevel` = 60
WHERE `class` = 15
  AND `subclass` = 5
  AND `RequiredSkill` = 762
  AND `RequiredSkillRank` = 150
  AND `RequiredLevel` <> 60;

-- --------------------------------------------------------------------------
-- 5. Explicit fast-ground backstop.
--
-- Includes:
--   * every 100% terrestrial mount explicitly rewritten by Individual
--     Progression;
--   * legacy/current PvP variants;
--   * fixed-speed exceptions that require only Riding 75;
--   * the original Naxxramas Deathcharger item, whose item template does not
--     necessarily carry the normal Riding-150 requirement.
--
-- This statement MUST remain after the slow-mount rules.
-- --------------------------------------------------------------------------
UPDATE `item_template`
SET `RequiredLevel` = 60
WHERE `entry` IN (
    -- Individual Progression: Alliance 100%
    12302, 12303,
    18766, 18767, 18768, 18902,
    13326, 13327,
    18772, 18773, 18774,
    12353, 12354,
    18776, 18777, 18778,
    13328, 13329,
    18785, 18786, 18787,

    -- Individual Progression: Horde 100%
    8586, 13317,
    18788, 18789, 18790,
    13334, 18791,
    15292, 15293,
    18793, 18794, 18795,
    12330, 12351,
    18796, 18797, 18798,

    -- Individual Progression: special / legacy fast terrestrial mounts
    13086,                         -- Winterspring Frostsaber (100%, Riding 75)
    13335,                         -- Deathcharger's Reins
    18241, 18242, 18243, 18244,   -- Legacy Black War mounts
    18245, 18246, 18247, 18248,
    19029,                         -- Frostwolf Howler
    19030,                         -- Stormpike Battle Charger
    19872,                         -- Swift Razzashi Raptor
    19902,                         -- Swift Zulian Tiger
    20221,                         -- Foror's Fabled Steed
    21176,                         -- Black Qiraji Resonating Crystal
    21218, 21321, 21323, 21324,   -- Colored Qiraji Battle Tanks

    -- WotLK/current PvP Black War mount item IDs (normally Riding 150)
    29465, 29466, 29467, 29468,
    29469, 29470, 29471, 29472,

    -- Additional legacy fixed-100%-speed rows that can retain old
    -- race-specific riding-skill metadata rather than Riding 150.
    16339,                         -- Commander's Steed
    16344,                         -- Lieutenant General's Mount
    18063,                         -- Test Epic Mount / Deathcharger test item

    -- Other fixed-100%-speed exceptions not covered safely by rank alone
    23193,                         -- Naxxramas Deathcharger Reins
    46102,                         -- Venomhide Ravasaur (100%, Riding 75)
    52200                          -- Crimson Deathcharger (100%, Riding 75)
)
AND `RequiredLevel` <> 60;

COMMIT;

