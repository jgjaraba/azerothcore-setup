USE `acore_world`;

-- Forsaken Paladin Phase 2.1: project-owned class quests and their custom items.
-- The baseline remains exclusively owned by forsaken_paladin.sql.

START TRANSACTION;

DELETE FROM `conditions`
WHERE (`SourceTypeOrReferenceId` = 4 AND `SourceGroup` = 4767 AND `SourceEntry` = 92061)
   OR (`SourceTypeOrReferenceId` = 1 AND `SourceGroup` IN (1939, 1940, 1942, 1943) AND `SourceEntry` = 92063)
   OR (`SourceTypeOrReferenceId` = 1 AND `SourceGroup` = 1947 AND `SourceEntry` = 92060)
   OR (`SourceTypeOrReferenceId` = 1 AND `SourceGroup` = 2261 AND `SourceEntry` = 92062);
DELETE FROM `gameobject_questitem` WHERE `GameObjectEntry` = 105172 AND `ItemId` = 92061;
DELETE FROM `creature_questitem`
WHERE (`CreatureEntry` IN (1939, 1940, 1942, 1943) AND `ItemId` = 92063)
   OR (`CreatureEntry` = 1947 AND `ItemId` = 92060)
   OR (`CreatureEntry` = 2261 AND `ItemId` = 92062);
DELETE FROM `gameobject_loot_template` WHERE `Entry` = 4767 AND `Item` = 92061;
DELETE FROM `creature_loot_template`
WHERE (`Entry` IN (1939, 1940, 1942, 1943) AND `Item` = 92063)
   OR (`Entry` = 1947 AND `Item` = 92060)
   OR (`Entry` = 2261 AND `Item` = 92062);
DELETE FROM `creature_queststarter` WHERE `quest` IN (91010, 91011, 91012, 91013, 91014, 91015, 91016, 91020, 91021, 91022, 91023, 91024);
DELETE FROM `creature_questender` WHERE `quest` IN (91010, 91011, 91012, 91013, 91014, 91015, 91016, 91020, 91021, 91022, 91023, 91024);
DELETE FROM `quest_template_addon` WHERE `ID` IN (91010, 91011, 91012, 91013, 91014, 91015, 91016, 91020, 91021, 91022, 91023, 91024);
DELETE FROM `quest_request_items_locale` WHERE `ID` IN (91010, 91011, 91012, 91013, 91014, 91015, 91016, 91020, 91021, 91022, 91023, 91024);
DELETE FROM `quest_offer_reward_locale` WHERE `ID` IN (91010, 91011, 91012, 91013, 91014, 91015, 91016, 91020, 91021, 91022, 91023, 91024);
DELETE FROM `quest_request_items` WHERE `ID` IN (91010, 91011, 91012, 91013, 91014, 91015, 91016, 91020, 91021, 91022, 91023, 91024);
DELETE FROM `quest_offer_reward` WHERE `ID` IN (91010, 91011, 91012, 91013, 91014, 91015, 91016, 91020, 91021, 91022, 91023, 91024);
DELETE FROM `quest_template_locale` WHERE `ID` IN (91010, 91011, 91012, 91013, 91014, 91015, 91016, 91020, 91021, 91022, 91023, 91024);
DELETE FROM `quest_template` WHERE `ID` IN (91010, 91011, 91012, 91013, 91014, 91015, 91016, 91020, 91021, 91022, 91023, 91024);
DELETE FROM `item_template_locale` WHERE `ID` IN (92060, 92061, 92062, 92063, 92064);
DELETE FROM `item_template` WHERE `entry` IN (92060, 92061, 92062, 92063, 92064);

-- Preserve existing services while adding the questgiver flag required by custom quest relations.
UPDATE `creature_template`
SET `npcflag` = `npcflag` | 2
WHERE `entry` IN (2307, 4605, 90210, 90211);

INSERT INTO `item_template` (
    `entry`, `class`, `subclass`, `SoundOverrideSubclass`, `name`, `displayid`, `Quality`, `Flags`, `FlagsExtra`,
    `BuyCount`, `BuyPrice`, `SellPrice`, `InventoryType`, `AllowableClass`, `AllowableRace`, `ItemLevel`,
    `RequiredLevel`, `RequiredSkill`, `RequiredSkillRank`, `requiredspell`, `requiredhonorrank`, `RequiredCityRank`,
    `RequiredReputationFaction`, `RequiredReputationRank`, `maxcount`, `stackable`, `ContainerSlots`,
    `stat_type1`, `stat_value1`, `stat_type2`, `stat_value2`, `stat_type3`, `stat_value3`, `dmg_min1`, `dmg_max1`,
    `dmg_type1`, `delay`, `bonding`, `Material`, `sheath`, `MaxDurability`, `RequiredDisenchantSkill`,
    `DisenchantID`, `VerifiedBuild`
) VALUES
    (92060, 12, 0, -1, 'Ravenclaw Counterweight', 8927, 1, 0, 0, 1, 0, 0, 0, -1, -1, 1, 0, 0, 0, 0, 0, 0,
     0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, -1, 0, 0, -1, 0, 0),
    (92061, 12, 0, -1, 'Agamand Weapon Haft', 8927, 1, 0, 0, 1, 0, 0, 0, -1, -1, 1, 0, 0, 0, 0, 0, 0,
     0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, -1, 0, 0, -1, 0, 0),
    (92062, 12, 0, -1, 'Durnholde Forged Iron', 8927, 1, 0, 0, 1, 0, 0, 0, -1, -1, 1, 0, 0, 0, 0, 0, 0,
     0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, -1, 0, 0, -1, 0, 0),
    (92063, 12, 0, -1, 'Rot Hide Binding', 8927, 1, 0, 0, 1, 0, 0, 0, -1, -1, 1, 0, 0, 0, 0, 0, 0,
     0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, -1, 0, 0, -1, 0, 0),
    (92064, 2, 5, -1, 'Lordaeron\'s Vigil', 13466, 3, 0, 0, 1, 37297, 7459, 17, 2, -1, 31, 0, 0, 0, 0, 0, 0,
     0, 0, 0, 1, 0, 7, 7, 6, 12, 5, 6, 65, 99, 0, 3200, 1, 2, 1, 100, 75, 43, 12340);

INSERT INTO `item_template_locale` (`ID`, `locale`, `Name`, `Description`, `VerifiedBuild`) VALUES
    (92060, 'esES', 'Contrapeso Corvozarpa', '', 0),
    (92061, 'esES', 'Mango de arma Agamand', '', 0),
    (92062, 'esES', 'Hierro forjado de Durnholde', '', 0),
    (92063, 'esES', 'Atadura Putrepellejo', '', 0),
    (92064, 'esES', 'Vigilia de Lordaeron', '', 0);

INSERT INTO `quest_template` (
    `ID`, `QuestType`, `QuestLevel`, `MinLevel`, `QuestSortID`, `QuestInfoID`, `SuggestedGroupNum`,
    `RewardNextQuest`, `RewardXPDifficulty`, `RewardMoney`, `RewardMoneyDifficulty`, `RewardDisplaySpell`,
    `RewardSpell`, `Flags`, `RequiredNpcOrGo1`, `RequiredNpcOrGoCount1`, `RequiredItemId1`,
    `RequiredItemCount1`, `AllowableRaces`, `LogTitle`, `LogDescription`, `QuestDescription`,
    `AreaDescription`, `QuestCompletionLog`, `ObjectiveText1`, `VerifiedBuild`
) VALUES
    (91010, 2, -1, 12, -141, 0, 0, 91011, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 16,
     'A Handful of Ash', 'Speak with Abraham West in Brill.',
     'You have learned to call upon the Light. That is not the same as knowing why.\n\nAbraham West keeps the old discipline in Brill. There are few who endure it, and fewer who speak openly. Some call them the Ashen Hand, but do not mistake a whispered name for an order.\n\nSpeak with Abraham. He will tell you what is required.',
     'Speak with Abraham West in Brill.', 'Speak with Abraham West in Brill.', 'Speak with Abraham West', 0),
    (91011, 2, -1, 12, -141, 0, 0, 91012, 5, 0, 0, 0, 0, 0, 0, 0, 2589, 10, 16,
     'A Kindness Without Witness', 'Bring 10 Linen Cloth to Caretaker Caice in Deathknell.',
     'Caretaker Caice tends those who rise in Deathknell. Some wake torn, some bewildered, and some do not wake at all.\n\nBring him ten pieces of linen for bindings and shrouds. A kindness does not become righteous merely because someone witnesses it.',
     'Bring 10 Linen Cloth to Caretaker Caice in Deathknell.', 'Bring 10 Linen Cloth to Caretaker Caice in Deathknell.', 'Linen Cloth', 0),
    (91012, 2, -1, 12, -141, 0, 0, 91013, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 16,
     'What the Dead Still Need', 'Return to Abraham West in Brill.',
     'Tell Abraham the work is done.\n\nThe dead still require hands, patience and someone willing to remain after curiosity has passed.',
     'Return to Abraham West in Brill.', 'Return to Abraham West in Brill.', 'Return to Abraham West', 0),
    (91013, 2, -1, 12, -141, 0, 0, 91014, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 16,
     'The Measure of Mercy', 'Speak with Magistrate Sevren in Brill.',
     'Mercy is not softness, $N, nor is it permission for murder.\n\nMagistrate Sevren has work fit for someone learning the difference. Hear him out, then act without relish.',
     'Speak with Magistrate Sevren in Brill.', 'Speak with Magistrate Sevren in Brill.', 'Speak with Magistrate Sevren', 0),
    (91014, 2, -1, 12, -141, 0, 0, 91015, 5, 0, 0, 0, 0, 0, 1535, 8, 0, 0, 16,
     'The Light Without Pity', 'Kill 8 Scarlet Warriors, then return to Magistrate Sevren in Brill.',
     'The Scarlets offer no quarter to the Forsaken. Drive their warriors back, but do not mistake necessity for virtue.\n\nKill eight Scarlet Warriors east of Brill, then report to me.',
     'Kill 8 Scarlet Warriors, then return to Magistrate Sevren in Brill.', 'Kill 8 Scarlet Warriors, then return to Magistrate Sevren in Brill.', 'Scarlet Warriors slain', 0),
    (91015, 2, -1, 12, -141, 0, 0, 91016, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 16,
     'A Report in Ash', 'Report to Abraham West in Brill.',
     'Tell Abraham the patrol has been broken and the road is secure.\n\nHe asked whether you could distinguish mercy from surrender. I believe he has his answer.',
     'Report to Abraham West in Brill.', 'Report to Abraham West in Brill.', 'Report to Abraham West', 0),
    (91016, 2, -1, 12, -141, 0, 0, 0, 6, 0, 0, 7328, 7329, 8, 0, 0, 0, 0, 16,
     'The Light Does Not Spare Us', 'Complete your instruction with Abraham West.',
     'The Light does not become gentle because it passes through dead flesh. It burns, and still it answers.\n\nA paladin\'s duty is not merely to endure that pain. It is to call a fallen companion back to service when battle takes them.\n\nAttend, and I will show you how.',
     'Complete your instruction with Abraham West.', 'Complete your instruction with Abraham West.', 'Complete your instruction', 0);

INSERT INTO `quest_template` (
    `ID`, `QuestType`, `QuestLevel`, `MinLevel`, `QuestSortID`, `QuestInfoID`, `SuggestedGroupNum`,
    `RewardNextQuest`, `RewardXPDifficulty`, `RewardMoney`, `RewardMoneyDifficulty`, `RewardDisplaySpell`,
    `RewardSpell`, `Flags`, `RewardItem1`, `RewardAmount1`, `RequiredItemId1`, `RequiredItemCount1`,
    `RequiredItemId2`, `RequiredItemCount2`, `AllowableRaces`, `LogTitle`, `LogDescription`,
    `QuestDescription`, `AreaDescription`, `QuestCompletionLog`, `ObjectiveText1`, `ObjectiveText2`,
    `VerifiedBuild`
) VALUES
    (91020, 2, 20, 20, -141, 0, 0, 91021, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 16,
     'A Weapon of This Soil', 'Speak with Basil Frye in the War Quarter of Undercity.',
     'At your level, a borrowed weapon and a bought weapon teach the same lesson: very little.\n\nBasil Frye works a forge in the War Quarter. He is no celebrated master, which may make him suitable. Ask whether he can fashion something from what Lordaeron has left us.',
     'Speak with Basil Frye in the War Quarter of Undercity.',
     'Speak with Basil Frye in the War Quarter of Undercity.', 'Speak with Basil Frye', '', 0),
    (91021, 2, 20, 20, -141, 0, 0, 91022, 5, 0, 0, 0, 0, 0, 0, 0, 92061, 1, 92063, 1, 16,
     'Wood and Sinew', 'Bring an Agamand Weapon Haft and a Rot Hide Binding to Basil Frye in Undercity.',
     'The Agamands kept racks for their weapons. Search the old mill and take a haft that has not split with age.\n\nFor the binding, use no fresh leather. The Rot Hides cure their straps with filth and grave-mould; unpleasant, but strong. Bring me one usable length.',
     'Bring an Agamand Weapon Haft and a Rot Hide Binding to Basil Frye in Undercity.',
     'Bring an Agamand Weapon Haft and a Rot Hide Binding to Basil Frye in Undercity.',
     'Agamand Weapon Haft', 'Rot Hide Binding', 0),
    (91022, 2, 20, 20, -141, 0, 0, 91023, 5, 0, 0, 0, 0, 0, 0, 0, 92060, 1, 0, 0, 16,
     'The Raven\'s Weight', 'Take the Ravenclaw Counterweight from Thule Ravenclaw on Fenris Isle and bring it to Basil Frye.',
     'The head will need a counterweight. Thule Ravenclaw carries a worked piece of iron heavy enough for the task.\n\nHe has made Fenris Isle a grave for others. Do not go there seeking a grand victory. Take the iron, return alive and let the dead keep no more than they already possess.',
     'Take the Ravenclaw Counterweight from Thule Ravenclaw on Fenris Isle and bring it to Basil Frye.',
     'Take the Ravenclaw Counterweight from Thule Ravenclaw on Fenris Isle and bring it to Basil Frye.',
     'Ravenclaw Counterweight', '', 0),
    (91023, 2, 20, 20, -141, 0, 0, 91024, 5, 0, 0, 0, 0, 0, 0, 0, 92062, 1, 0, 0, 16,
     'Iron in Captivity', 'Recover Durnholde Forged Iron from a Syndicate Watchman at Durnholde and bring it to Basil Frye.',
     'For the striking face, I need iron that has already endured a proper forge.\n\nThe Syndicate watchmen at Durnholde carry pieces cut and refitted from the keep\'s stores. Bring me one sound piece. We will remove their marks in the fire.',
     'Recover Durnholde Forged Iron from a Syndicate Watchman at Durnholde and bring it to Basil Frye.',
     'Recover Durnholde Forged Iron from a Syndicate Watchman at Durnholde and bring it to Basil Frye.',
     'Durnholde Forged Iron', '', 0),
    (91024, 2, 20, 20, -141, 0, 0, 0, 6, 0, 0, 0, 0, 8, 92064, 1, 0, 0, 0, 0, 16,
     'Lordaeron\'s Vigil', 'Remain with Basil Frye while he finishes Lordaeron\'s Vigil.',
     'The pieces are ready. Stay while I fit them together.\n\nThis is forge work, not a rite. Hold the haft when I tell you, and do not pull away when the hot iron meets the binding.',
     'Remain with Basil Frye while he finishes Lordaeron\'s Vigil.',
     'Remain with Basil Frye while he finishes Lordaeron\'s Vigil.', 'Complete the forging', '', 0);

INSERT INTO `quest_template_addon` (`ID`, `AllowableClasses`, `PrevQuestID`, `NextQuestID`) VALUES
    (91010, 2, 0, 91011), (91011, 2, 91010, 91012), (91012, 2, 91011, 91013),
    (91013, 2, 91012, 91014), (91014, 2, 91013, 91015), (91015, 2, 91014, 91016),
    (91016, 2, 91015, 0), (91020, 2, 0, 91021), (91021, 2, 91020, 91022),
    (91022, 2, 91021, 91023), (91023, 2, 91022, 91024), (91024, 2, 91023, 0);

INSERT INTO `creature_queststarter` (`id`, `quest`) VALUES
    (90211, 91010), (90210, 91011), (2307, 91012), (90210, 91013), (1499, 91014), (1499, 91015),
    (90210, 91016), (90210, 91020), (4605, 91021), (4605, 91022), (4605, 91023), (4605, 91024);
INSERT INTO `creature_questender` (`id`, `quest`) VALUES
    (90210, 91010), (2307, 91011), (90210, 91012), (1499, 91013), (1499, 91014), (90210, 91015),
    (90210, 91016), (4605, 91020), (4605, 91021), (4605, 91022), (4605, 91023), (4605, 91024);

INSERT INTO `quest_request_items` (`ID`, `EmoteOnComplete`, `EmoteOnIncomplete`, `CompletionText`, `VerifiedBuild`) VALUES
    (91010, 0, 0, 'Pancratius sent you? Then he believes you are ready to be useful.', 0),
    (91011, 0, 0, 'The newly risen are not patient with old wrappings. Have you brought the linen?', 0),
    (91012, 0, 0, 'Did Caice find a use for you?', 0),
    (91013, 0, 0, 'Abraham sent you? Good. I require a steady hand, not a sermon.', 0),
    (91014, 0, 0, 'The Scarlets will mistake hesitation for weakness. Is the road secure?', 0),
    (91015, 0, 0, 'Sevren does not send praise lightly. What happened?', 0),
    (91016, 0, 0, 'Stand ready. This lesson will not be comfortable.', 0),
    (91020, 0, 0, 'You want a weapon made here? That depends upon what you are willing to bring me.', 0),
    (91021, 0, 0, 'A warped haft will ruin the balance, and rotten binding will part on the first swing. Choose carefully.', 0),
    (91022, 0, 0, 'Thule still has the iron, or you would have placed it on my bench.', 0),
    (91023, 0, 0, 'Any cracked or rust-eaten piece is useless to me. Have you found sound iron?', 0),
    (91024, 0, 0, 'The forge is hot. We begin when you are ready.', 0);

INSERT INTO `quest_offer_reward` (
    `ID`, `Emote1`, `Emote2`, `Emote3`, `Emote4`, `EmoteDelay1`, `EmoteDelay2`, `EmoteDelay3`, `EmoteDelay4`,
    `RewardText`, `VerifiedBuild`
) VALUES
    (91010, 0, 0, 0, 0, 0, 0, 0, 0, 'We have no church and no banner, $N. We are merely a handful of the dead attempting an old discipline.\n\nIf you intend to remain, you will serve before you judge.', 0),
    (91011, 0, 0, 0, 0, 0, 0, 0, 0, 'Good. This will serve for bandages and for shrouds.\n\nThe Light will not fold them for us.', 0),
    (91012, 0, 0, 0, 0, 0, 0, 0, 0, 'Compassion that depends upon gratitude is only trade.\n\nYou served people who could offer you nothing. Remember that.', 0),
    (91013, 0, 0, 0, 0, 0, 0, 0, 0, 'Scarlet Warriors have been probing the road east of Brill. Their zeal will not spare our people.\n\nThin their patrols before they grow bold enough to strike the town.', 0),
    (91014, 0, 0, 0, 0, 0, 0, 0, 0, 'Eight fewer blades pointed at Brill. That is enough.\n\nYou did what was required and did not make a pageant of it. Abraham should hear that.', 0),
    (91015, 0, 0, 0, 0, 0, 0, 0, 0, 'You tended the helpless and defended those still standing. Neither deed made you pure, and neither required purity before it could be done.\n\nThere is one duty left to discuss.', 0),
    (91016, 0, 0, 0, 0, 0, 0, 0, 0, 'The Light did not spare you, nor did it refuse you.\n\nYou now bear the power to return a fallen companion to life. Use it as a duty, never as proof that we have mastered what passes through us.', 0),
    (91020, 0, 0, 0, 0, 0, 0, 0, 0, 'I can shape the metal, but I will not pretend the forge creates substance from nothing.\n\nWe will begin with a sound haft and something fit to bind it.', 0),
    (91021, 0, 0, 0, 0, 0, 0, 0, 0, 'The wood is old but straight, and this binding has survived worse treatment than you will give it.\n\nThey are ugly materials. They will serve.', 0),
    (91022, 0, 0, 0, 0, 0, 0, 0, 0, 'Dense, well shaped and marked by no craft worth honoring.\n\nOnce it is in the weapon, it will serve a better purpose than its former bearer.', 0),
    (91023, 0, 0, 0, 0, 0, 0, 0, 0, 'This will take the hammer.\n\nThe keep changed hands, but its iron remained. Once reforged, it will owe allegiance to no jailer or thief.', 0),
    (91024, 0, 0, 0, 0, 0, 0, 0, 0, 'There. No royal seal, no saint\'s name and no promise that the Light finds us worthy.\n\nIt was made from Lordaeron by hands that still serve Lordaeron. Keep watch.', 0);

INSERT INTO `quest_request_items_locale` (`ID`, `locale`, `CompletionText`, `VerifiedBuild`) VALUES
    (91010, 'esES', '¿Te envía Pancratius? Entonces cree que ya puedes resultar útil.', 0),
    (91011, 'esES', 'Los recién alzados no tratan con cuidado sus viejas vendas. ¿Has traído el lino?', 0),
    (91012, 'esES', '¿Te encontró Caice alguna utilidad?', 0),
    (91013, 'esES', '¿Te envía Abraham? Bien. Necesito una mano firme, no un sermón.', 0),
    (91014, 'esES', 'Los Escarlata confundirán cualquier vacilación con debilidad. ¿Está seguro el camino?', 0),
    (91015, 'esES', 'Sevren no concede elogios con facilidad. ¿Qué ocurrió?', 0),
    (91016, 'esES', 'Prepárate. Esta lección no será agradable.', 0),
    (91020, 'esES', '¿Quieres un arma forjada aquí? Dependerá de lo que estés $gdispuesto:dispuesta; a traerme.', 0),
    (91021, 'esES', 'Un mango torcido arruinará el equilibrio, y una atadura podrida cederá al primer golpe. Elige con cuidado.', 0),
    (91022, 'esES', 'Thule aún conserva el hierro, o ya lo habrías dejado sobre mi banco.', 0),
    (91023, 'esES', 'Una pieza agrietada o comida por el óxido no me sirve. ¿Has encontrado hierro en buen estado?', 0),
    (91024, 'esES', 'La forja está caliente. Empezaremos cuando estés $gpreparado:preparada;.', 0);

INSERT INTO `quest_offer_reward_locale` (`ID`, `locale`, `RewardText`, `VerifiedBuild`) VALUES
    (91010, 'esES', 'No tenemos iglesia ni estandarte, $N. Solo somos un puñado de muertos que intenta seguir una antigua disciplina.\n\nSi pretendes quedarte, servirás antes de juzgar.', 0),
    (91011, 'esES', 'Bien. Servirá para vendajes y para mortajas.\n\nLa Luz no va a doblarlos por nosotros.', 0),
    (91012, 'esES', 'La compasión que exige gratitud no es más que un trueque.\n\nHas servido a quienes nada podían ofrecerte. Recuérdalo.', 0),
    (91013, 'esES', 'Los Guerreros Escarlata están tanteando el camino al este de Rémol. Su fanatismo no tendrá piedad de los nuestros.\n\nReduce sus patrullas antes de que se atrevan a atacar el pueblo.', 0),
    (91014, 'esES', 'Ocho hojas menos apuntan ahora hacia Rémol. Basta.\n\nHiciste lo necesario sin convertirlo en un espectáculo. Abraham debe saberlo.', 0),
    (91015, 'esES', 'Atendiste a los indefensos y defendiste a quienes aún seguían en pie. Ningún acto te hizo puro, ni exigía pureza para llevarlo a cabo.\n\nQueda un deber del que debemos hablar.', 0),
    (91016, 'esES', 'La Luz no te ha dado tregua, pero tampoco te ha rechazado.\n\nAhora posees el poder de devolver la vida a un compañero caído. Empléalo como un deber, nunca como prueba de que dominamos aquello que nos atraviesa.', 0),
    (91020, 'esES', 'Puedo dar forma al metal, pero no fingiré que la forja crea materia de la nada.\n\nEmpezaremos con un mango firme y algo adecuado para sujetarlo.', 0),
    (91021, 'esES', 'La madera es vieja, pero recta, y esta atadura ha soportado peores tratos de los que tú le darás.\n\nSon materiales feos. Servirán.', 0),
    (91022, 'esES', 'Es denso, está bien formado y no lleva marca alguna de una artesanía digna de honor.\n\nCuando forme parte del arma, servirá a un propósito mejor que su antiguo portador.', 0),
    (91023, 'esES', 'Esto soportará el martillo.\n\nEl castillo cambió de manos, pero su hierro permaneció. Una vez reforjado, no deberá lealtad a carcelero ni ladrón alguno.', 0),
    (91024, 'esES', 'Ya está. Sin sello real, sin nombre de santo y sin promesa de que la Luz nos considere dignos.\n\nFue forjada con restos de Lordaeron por manos que aún sirven a Lordaeron. Mantén la vigilia.', 0);

INSERT INTO `quest_template_locale` (
    `ID`, `locale`, `Title`, `Details`, `Objectives`, `EndText`, `CompletedText`, `ObjectiveText1`, `ObjectiveText2`,
    `VerifiedBuild`
) VALUES
    (91010, 'esES', 'Un puñado de ceniza',
     'Has aprendido a invocar la Luz. Eso no significa que sepas para qué.\n\nAbraham West conserva la antigua disciplina en Rémol. Pocos soportan su peso, y menos aún hablan de ella abiertamente. Algunos los llaman la Mano Cinérea, pero no confundas un nombre susurrado con una orden.\n\nHabla con Abraham. Él te dirá qué se espera de ti.',
     'Habla con Abraham West en Rémol.', '¿Te envía Pancratius? Entonces cree que ya puedes resultar útil.',
      'No tenemos iglesia ni estandarte, $N. Solo somos un puñado de muertos que intenta seguir una antigua disciplina.\n\nSi pretendes quedarte, servirás antes de juzgar.', 'Habla con Abraham West', '', 0),
    (91011, 'esES', 'Bondad sin testigos',
     'El custodio Caice atiende a quienes se alzan en Camposanto. Algunos despiertan maltrechos, otros confusos, y otros no llegan a despertar.\n\nLlévale diez paños de lino para vendajes y mortajas. Una bondad no se vuelve justa porque alguien la presencie.',
     'Lleva 10 paños de lino al custodio Caice en Camposanto.', 'Los recién alzados no tratan con cuidado sus viejas vendas. ¿Has traído el lino?',
      'Bien. Servirá para vendajes y para mortajas.\n\nLa Luz no va a doblarlos por nosotros.', 'Paño de lino', '', 0),
    (91012, 'esES', 'Lo que aún necesitan los muertos',
     'Dile a Abraham que el trabajo está hecho.\n\nLos muertos aún necesitan manos, paciencia y a alguien dispuesto a quedarse cuando haya pasado la curiosidad.',
     'Vuelve con Abraham West en Rémol.', '¿Te encontró Caice alguna utilidad?',
      'La compasión que exige gratitud no es más que un trueque.\n\nHas servido a quienes nada podían ofrecerte. Recuérdalo.', 'Vuelve con Abraham West', '', 0),
    (91013, 'esES', 'La medida de la compasión',
     'La compasión no es debilidad, $N, ni permiso para asesinar.\n\nEl magistrado Sevren tiene una tarea adecuada para quien está aprendiendo la diferencia. Escúchalo y actúa sin deleitarte en ello.',
     'Habla con el magistrado Sevren en Rémol.', '¿Te envía Abraham? Bien. Necesito una mano firme, no un sermón.',
      'Los Guerreros Escarlata están tanteando el camino al este de Rémol. Su fanatismo no tendrá piedad de los nuestros.\n\nReduce sus patrullas antes de que se atrevan a atacar el pueblo.', 'Habla con el magistrado Sevren', '', 0),
    (91014, 'esES', 'La Luz sin piedad',
     'Los Escarlata no conceden cuartel a los Renegados. Haz retroceder a sus guerreros, pero no confundas la necesidad con la virtud.\n\nMata a ocho Guerreros Escarlata al este de Rémol y vuelve conmigo.',
     'Mata a 8 Guerreros Escarlata y vuelve con el magistrado Sevren en Rémol.', 'Los Escarlata confundirán cualquier vacilación con debilidad. ¿Está seguro el camino?',
      'Ocho hojas menos apuntan ahora hacia Rémol. Basta.\n\nHiciste lo necesario sin convertirlo en un espectáculo. Abraham debe saberlo.', 'Guerreros Escarlata muertos', '', 0),
    (91015, 'esES', 'Un informe en ceniza',
     'Dile a Abraham que la patrulla ha sido deshecha y que el camino está seguro.\n\nQuería saber si sabrías distinguir la compasión de la rendición. Creo que ya tiene su respuesta.',
     'Informa a Abraham West en Rémol.', 'Sevren no concede elogios con facilidad. ¿Qué ocurrió?',
      'Atendiste a los indefensos y defendiste a quienes aún seguían en pie. Ningún acto te hizo puro, ni exigía pureza para llevarlo a cabo.\n\nQueda un deber del que debemos hablar.', 'Informa a Abraham West', '', 0),
    (91016, 'esES', 'La Luz no nos da tregua',
     'La Luz no se vuelve amable por atravesar carne muerta. Quema y, aun así, responde.\n\nEl deber de un paladín no consiste solo en soportar ese dolor. Debe llamar de nuevo al servicio a un compañero caído cuando la batalla se lo arrebata.\n\nPresta atención y te enseñaré cómo hacerlo.',
     'Completa tu instrucción con Abraham West.', 'Prepárate. Esta lección no será agradable.',
      'La Luz no te ha dado tregua, pero tampoco te ha rechazado.\n\nAhora posees el poder de devolver la vida a un compañero caído. Empléalo como un deber, nunca como prueba de que dominamos aquello que nos atraviesa.', 'Completa tu instrucción', '', 0),
    (91020, 'esES', 'Un arma de esta tierra',
     'A tu nivel, un arma prestada y otra comprada enseñan lo mismo: muy poco.\n\nBasil Frye trabaja en una forja del Barrio de la Guerra. No es un maestro célebre, lo cual quizá lo haga adecuado. Pregúntale si puede fabricar algo con lo que aún queda de Lordaeron.',
     'Habla con Basil Frye en el Barrio de la Guerra de Entrañas.',
     '¿Quieres un arma forjada aquí? Dependerá de lo que estés $gdispuesto:dispuesta; a traerme.',
     'Puedo dar forma al metal, pero no fingiré que la forja crea materia de la nada.\n\nEmpezaremos con un mango firme y algo adecuado para sujetarlo.', 'Habla con Basil Frye', '', 0),
    (91021, 'esES', 'Madera y tendón',
     'Los Agamand guardaban sus armas en expositores. Busca en el viejo molino y toma un mango que no se haya agrietado con los años.\n\nPara la atadura no emplearemos cuero nuevo. Los Putrepellejo curten sus correas con inmundicia y moho de tumba; es desagradable, pero resistente. Tráeme un trozo aprovechable.',
     'Lleva un Mango de arma Agamand y una Atadura Putrepellejo a Basil Frye en Entrañas.',
     'Un mango torcido arruinará el equilibrio, y una atadura podrida cederá al primer golpe. Elige con cuidado.',
     'La madera es vieja, pero recta, y esta atadura ha soportado peores tratos de los que tú le darás.\n\nSon materiales feos. Servirán.', 'Mango de arma Agamand', 'Atadura Putrepellejo', 0),
    (91022, 'esES', 'El peso del cuervo',
     'La cabeza necesitará un contrapeso. Thule Corvozarpa lleva una pieza de hierro trabajado con el peso adecuado.\n\nHa convertido la Isla de Fenris en la tumba de otros. No vayas allí en busca de una gran victoria. Toma el hierro, regresa con vida y no permitas que los muertos conserven más de lo que ya poseen.',
     'Arrebata el Contrapeso Corvozarpa a Thule Corvozarpa en la Isla de Fenris y llévaselo a Basil Frye.',
     'Thule aún conserva el hierro, o ya lo habrías dejado sobre mi banco.',
     'Es denso, está bien formado y no lleva marca alguna de una artesanía digna de honor.\n\nCuando forme parte del arma, servirá a un propósito mejor que su antiguo portador.', 'Contrapeso Corvozarpa', '', 0),
    (91023, 'esES', 'Hierro cautivo',
     'Para la cara de golpe necesito hierro que ya haya resistido una forja adecuada.\n\nLos Veladores de la Hermandad de Durnholde llevan piezas recortadas y adaptadas de las reservas del castillo. Tráeme una que esté entera. Borraremos sus marcas en el fuego.',
     'Consigue Hierro forjado de Durnholde de un Velador de la Hermandad en Durnholde y llévaselo a Basil Frye.',
     'Una pieza agrietada o comida por el óxido no me sirve. ¿Has encontrado hierro en buen estado?',
     'Esto soportará el martillo.\n\nEl castillo cambió de manos, pero su hierro permaneció. Una vez reforjado, no deberá lealtad a carcelero ni ladrón alguno.', 'Hierro forjado de Durnholde', '', 0),
    (91024, 'esES', 'Vigilia de Lordaeron',
     'Las piezas están listas. Quédate mientras las uno.\n\nEsto es trabajo de forja, no un rito. Sujeta el mango cuando te lo indique y no retrocedas cuando el hierro caliente toque la atadura.',
     'Permanece con Basil Frye mientras termina la Vigilia de Lordaeron.',
     'La forja está caliente. Empezaremos cuando estés $gpreparado:preparada;.',
     'Ya está. Sin sello real, sin nombre de santo y sin promesa de que la Luz nos considere dignos.\n\nFue forjada con restos de Lordaeron por manos que aún sirven a Lordaeron. Mantén la vigilia.', 'Completa la forja', '', 0);

UPDATE `quest_template_locale`
SET `EndText` = `Objectives`, `CompletedText` = `Objectives`
WHERE `ID` IN (91010, 91011, 91012, 91013, 91014, 91015, 91016, 91020, 91021, 91022, 91023, 91024)
  AND `locale` = 'esES';

INSERT INTO `gameobject_loot_template` (
    `Entry`, `Item`, `Reference`, `Chance`, `QuestRequired`, `LootMode`, `GroupId`, `MinCount`, `MaxCount`, `Comment`
) VALUES
    (4767, 92061, 0, 100, 1, 1, 0, 1, 1, 'Agamand Weapon Rack - Agamand Weapon Haft');

INSERT INTO `creature_loot_template` (
    `Entry`, `Item`, `Reference`, `Chance`, `QuestRequired`, `LootMode`, `GroupId`, `MinCount`, `MaxCount`, `Comment`
) VALUES
    (1939, 92063, 0, 100, 1, 1, 0, 1, 1, 'Rot Hide Brute - Rot Hide Binding'),
    (1940, 92063, 0, 100, 1, 1, 0, 1, 1, 'Rot Hide Plague Weaver - Rot Hide Binding'),
    (1942, 92063, 0, 100, 1, 1, 0, 1, 1, 'Rot Hide Savage - Rot Hide Binding'),
    (1943, 92063, 0, 100, 1, 1, 0, 1, 1, 'Raging Rot Hide - Rot Hide Binding'),
    (1947, 92060, 0, 100, 1, 1, 0, 1, 1, 'Thule Ravenclaw - Ravenclaw Counterweight'),
    (2261, 92062, 0, 100, 1, 1, 0, 1, 1, 'Syndicate Watchman - Durnholde Forged Iron');

INSERT INTO `conditions` (
    `SourceTypeOrReferenceId`, `SourceGroup`, `SourceEntry`, `SourceId`, `ElseGroup`, `ConditionTypeOrReference`,
    `ConditionTarget`, `ConditionValue1`, `ConditionValue2`, `ConditionValue3`, `NegativeCondition`, `ErrorType`,
    `ErrorTextId`, `ScriptName`, `Comment`
) VALUES
    (4, 4767, 92061, 0, 0, 9, 0, 91021, 0, 0, 0, 0, 0, '', 'Agamand Weapon Haft requires quest 91021'),
    (1, 1939, 92063, 0, 0, 9, 0, 91021, 0, 0, 0, 0, 0, '', 'Rot Hide Binding requires quest 91021'),
    (1, 1940, 92063, 0, 0, 9, 0, 91021, 0, 0, 0, 0, 0, '', 'Rot Hide Binding requires quest 91021'),
    (1, 1942, 92063, 0, 0, 9, 0, 91021, 0, 0, 0, 0, 0, '', 'Rot Hide Binding requires quest 91021'),
    (1, 1943, 92063, 0, 0, 9, 0, 91021, 0, 0, 0, 0, 0, '', 'Rot Hide Binding requires quest 91021'),
    (1, 1947, 92060, 0, 0, 9, 0, 91022, 0, 0, 0, 0, 0, '', 'Ravenclaw Counterweight requires quest 91022'),
    (1, 2261, 92062, 0, 0, 9, 0, 91023, 0, 0, 0, 0, 0, '', 'Durnholde Forged Iron requires quest 91023');

INSERT INTO `gameobject_questitem` (`GameObjectEntry`, `Idx`, `ItemId`, `VerifiedBuild`) VALUES
    (105172, 1, 92061, 0);

INSERT INTO `creature_questitem` (`CreatureEntry`, `Idx`, `ItemId`, `VerifiedBuild`) VALUES
    (1939, 1, 92063, 0), (1940, 1, 92063, 0), (1942, 1, 92063, 0), (1943, 1, 92063, 0),
    (1947, 1, 92060, 0), (2261, 1, 92062, 0);

COMMIT;
