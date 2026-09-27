-- Single-Minded Fury / Furia enfilada for AzerothCore 3.3.5a
-- Generated to match the accompanying Spell.dbc/Talent.dbc additions.
-- Custom IDs verified absent from the supplied DBCs:
--   TalentID 3000
--   SpellID  90000  (talent marker)
--   SpellID  90001  (+20% physical damage aura; applied conditionally by C++ module)

START TRANSACTION;

DELETE FROM `talent_dbc` WHERE `ID` = 3000;
INSERT INTO `talent_dbc`
(`ID`,`TabID`,`TierID`,`ColumnIndex`,
 `SpellRank_1`,`SpellRank_2`,`SpellRank_3`,`SpellRank_4`,`SpellRank_5`,`SpellRank_6`,`SpellRank_7`,`SpellRank_8`,`SpellRank_9`,
 `PrereqTalent_1`,`PrereqTalent_2`,`PrereqTalent_3`,`PrereqRank_1`,`PrereqRank_2`,`PrereqRank_3`,
 `Flags`,`RequiredSpellID`,`CategoryMask_1`,`CategoryMask_2`)
VALUES
(3000,164,10,2,
 90000,0,0,0,0,0,0,0,0,
 0,0,0,0,0,0,
 0,0,0,0);

DELETE FROM `spell_dbc` WHERE `ID` IN (90000,90001);
INSERT INTO `spell_dbc`
(`ID`,`Attributes`,`CastingTimeIndex`,`DurationIndex`,`RangeIndex`,
 `EquippedItemClass`,`EquippedItemSubclass`,`EquippedItemInvTypes`,
 `Effect_1`,`EffectDieSides_1`,`EffectBasePoints_1`,`ImplicitTargetA_1`,`EffectAura_1`,`EffectMiscValue_1`,
 `SpellIconID`,
 `Name_Lang_enUS`,`Name_Lang_esES`,`Name_Lang_Mask`,
 `NameSubtext_Lang_enUS`,`NameSubtext_Lang_esES`,`NameSubtext_Lang_Mask`,
 `Description_Lang_enUS`,`Description_Lang_esES`,`Description_Lang_Mask`,
 `AuraDescription_Lang_Mask`,
 `SpellClassSet`,`SchoolMask`,
 `EffectChainAmplitude_1`,`EffectChainAmplitude_2`,`EffectChainAmplitude_3`)
VALUES
-- Visible one-point talent. Effect 1 is a harmless passive DUMMY aura.
(90000,464,1,21,1,
 -1,0,0,
 6,1,-1,1,4,0,
 533,
 'Single-Minded Fury','Furia enfilada',0x00FF01FE,
 'Rank 1','Rango 1',0x00FF01FE,
 'While dual-wielding one-handed weapons, your physical damage dealt is increased by $90001s1%.',
 'Mientras empuñas un arma de una mano en cada mano, el daño físico que infliges aumenta un $90001s1%.',0x00FF01FE,
 0x00FF01FC,
 4,1,
 1.0,0.0,0.0),
-- Hidden bonus aura. EffectBasePoints=19 resolves to +20%; MiscValue=1 means Physical school.
(90001,448,1,0,1,
 -1,0,0,
 6,1,19,1,79,1,
 533,
 'Single-Minded Fury (Bonus)','Furia enfilada (bonificación)',0x00FF01FE,
 NULL,NULL,0x00FF01FC,
 NULL,NULL,0x00FF01FE,
 0x00FF01FC,
 4,1,
 1.0,1.0,1.0);

COMMIT;

-- IMPORTANT: data alone does not enforce "one-handed weapon in BOTH hands".
-- The server module must apply spell 90001 only while the player knows spell 90000
-- and both EQUIPMENT_SLOT_MAINHAND and EQUIPMENT_SLOT_OFFHAND contain one-handed weapons;
-- otherwise it must remove aura 90001.
