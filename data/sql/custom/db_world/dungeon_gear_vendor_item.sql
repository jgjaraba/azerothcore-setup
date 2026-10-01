USE `acore_world`;

-- DARK RIDER: CLASSIC DUNGEON BOSS GEAR
-- Structure follows data/sql/custom/db_world/raid_gear_vendor_item.sql.
-- Install alongside dungeon_gear_vendor.sql (currencies 90010-90035).
-- PREREQUISITES: reserve/create creature_template entries 90300-90325;
-- set npcflag vendor (128) and define ItemExtendedCost.dbc rows below on
-- BOTH server and client before loading these vendor inventories.
-- Each ExtendedCost has ItemID[0] = Currency, ItemCount[0] = 2;
-- other ItemID/ItemCount fields, honor, arena and rating requirements = 0.
-- ExtendedCost is a DBC RECORD ID, not the price or the currency item ID.
-- This SQL creates inventories only; it does not create NPCs or DBC records.
-- No vendor catalog exceeds the 3.3.5 limit of 150 displayed items.
--
-- Scope: named Classic boss/rare/summoned encounter drops: equipment,
-- bags/quivers, dropped recipes and unique special drops.
-- Includes boss reward caches (The Seven, Theldren, Jarien/Sothos).
-- Excludes trash/world drops, quest-only rewards/items, keys, ammunition,
-- materials, merchant recipes, Dire Maul tribute/Knot cache, and SoD/TBC/WotLK items.
-- Flightblade Throwing Axe uses 28972, the working 3.3.5 replacement for
-- Classic 13173 (Broken Flightblade Throwing Axe in this database).
-- Shared boss loot is listed once per vendor; Armor, Weapons, Extra ordering.
-- Stratholme entrance encounters (Skul, Hearthsinger, Unforgiven, Postmaster,
-- Balzaphon) use the Living currency; the gauntlet uses the Undead currency.
--
-- Sources checked 2026-10-01:
-- https://github.com/jgjaraba/azerothcore-setup/blob/main/data/sql/custom/db_world/raid_gear_vendor_item.sql
-- Wowhead Classic normal-mode zone lists (individual URLs below).
-- Missing/ambiguous zone attribution, including Sunken Temple's SoD-only
-- current zone tab, checked against AtlasLootClassic normal boss tables:
-- https://github.com/Hoizame/AtlasLootClassic/blob/8e99341e4e779328460bf7684c0d5b22ce50ddf1/AtlasLootClassic_DungeonsAndRaids/data.lua
-- Item IDs and boss loot references checked against Grimfeather core
-- 529b659668bcd8b1cfbf9acc44f40eb6ff830fe1. Classic drop attribution is kept
-- where its WotLK loot placement differs; this file does not change drops.
--
-- NPC    ExtendedCost  Currency  Count  Dungeon
-- 90300  97010         90010     2      Ragefire Chasm
-- 90301  97011         90011     2      Wailing Caverns
-- 90302  97012         90012     2      The Deadmines
-- 90303  97013         90013     2      Shadowfang Keep
-- 90304  97014         90014     2      Blackfathom Deeps
-- 90305  97015         90015     2      The Stockade
-- 90306  97016         90016     2      Gnomeregan
-- 90307  97017         90017     2      Razorfen Kraul
-- 90308  97018         90018     2      Scarlet Monastery - Graveyard
-- 90309  97019         90019     2      Scarlet Monastery - Library
-- 90310  97020         90020     2      Scarlet Monastery - Armory
-- 90311  97021         90021     2      Scarlet Monastery - Cathedral
-- 90312  97022         90022     2      Razorfen Downs
-- 90313  97023         90023     2      Uldaman
-- 90314  97024         90024     2      Zul'Farrak
-- 90315  97025         90025     2      Maraudon
-- 90316  97026         90026     2      The Temple of Atal'Hakkar
-- 90317  97027         90027     2      Blackrock Depths
-- 90318  97028         90028     2      Lower Blackrock Spire
-- 90319  97029         90029     2      Upper Blackrock Spire
-- 90320  97030         90030     2      Dire Maul - East
-- 90321  97031         90031     2      Dire Maul - West
-- 90322  97032         90032     2      Dire Maul - North
-- 90323  97033         90033     2      Scholomance
-- 90324  97034         90034     2      Stratholme - Living Quarter
-- 90325  97035         90035     2      Stratholme - Undead Quarter

START TRANSACTION;

DELETE FROM `npc_vendor`
WHERE `entry` IN
(
    90300, 90301, 90302, 90303, 90304, 90305, 90306, 90307, 90308, 90309, 90310, 90311, 90312,
    90313, 90314, 90315, 90316, 90317, 90318, 90319, 90320, 90321, 90322, 90323, 90324, 90325
);

INSERT INTO `npc_vendor`
(
    entry,
    slot,
    item,
    maxcount,
    incrtime,
    ExtendedCost,
    VerifiedBuild
)
VALUES

-- =========================================================
-- RAGEFIRE CHASM
-- NPC 90300 | Currency 90010 | ExtendedCost 97010 | 6 items
-- https://www.wowhead.com/classic/zone=2437#drops;mode:normal
-- =========================================================

-- Armor
(90300,   0, 14147, 0, 0, 97010, 0), -- Cavedweller Bracers | Jergosh the Invoker
(90300,   1, 14148, 0, 0, 97010, 0), -- Crystalline Cuffs | Taragaman the Hungerer
(90300,   2, 14149, 0, 0, 97010, 0), -- Subterranean Cape | Taragaman the Hungerer
(90300,   3, 14150, 0, 0, 97010, 0), -- Robe of Evocation | Jergosh the Invoker

-- Weapons
(90300,   4, 14145, 0, 0, 97010, 0), -- Cursed Felblade | Taragaman the Hungerer
(90300,   5, 14151, 0, 0, 97010, 0), -- Chanting Blade | Jergosh the Invoker

-- =========================================================
-- WAILING CAVERNS
-- NPC 90301 | Currency 90011 | ExtendedCost 97011 | 24 items
-- https://www.wowhead.com/classic/zone=718#drops;mode:normal
-- =========================================================

-- Armor
(90301,   0,  5404, 0, 0, 97011, 0), -- Serpent's Shoulders | Lady Anacondra
(90301,   1,  5970, 0, 0, 97011, 0), -- Serpent Gloves | Lord Serpentis
(90301,   2,  6447, 0, 0, 97011, 0), -- Worn Turtle Shell Shield | Kresh
(90301,   3,  6449, 0, 0, 97011, 0), -- Glowing Lizardscale Cloak | Skum
(90301,   4,  6459, 0, 0, 97011, 0), -- Savage Trodders | Lord Serpentis
(90301,   5,  6460, 0, 0, 97011, 0), -- Cobrahn's Grasp | Lord Cobrahn
(90301,   6,  6461, 0, 0, 97011, 0), -- Slime-encrusted Pads | Mutanus the Devourer
(90301,   7,  6463, 0, 0, 97011, 0), -- Deep Fathom Ring | Mutanus the Devourer
(90301,   8,  6465, 0, 0, 97011, 0), -- Robe of the Moccasin | Lord Cobrahn
(90301,   9,  6473, 0, 0, 97011, 0), -- Armor of the Fang | Lord Pythas
(90301,  10,  6627, 0, 0, 97011, 0), -- Mutant Scale Breastplate | Mutanus the Devourer
(90301,  11,  6629, 0, 0, 97011, 0), -- Sporid Cape | Verdan the Everliving
(90301,  12,  6630, 0, 0, 97011, 0), -- Seedcloud Buckler | Verdan the Everliving
(90301,  13,  6632, 0, 0, 97011, 0), -- Feyscale Cloak | Deviate Faerie Dragon
(90301,  14, 10410, 0, 0, 97011, 0), -- Leggings of the Fang | Lord Cobrahn
(90301,  15, 10411, 0, 0, 97011, 0), -- Footpads of the Fang | Lord Serpentis
(90301,  16, 10412, 0, 0, 97011, 0), -- Belt of the Fang | Lady Anacondra
(90301,  17, 13245, 0, 0, 97011, 0), -- Kresh's Back | Kresh

-- Weapons
(90301,  18,  5243, 0, 0, 97011, 0), -- Firebelcher | Deviate Faerie Dragon
(90301,  19,  6448, 0, 0, 97011, 0), -- Tail Spike | Skum
(90301,  20,  6469, 0, 0, 97011, 0), -- Venomstrike | Lord Serpentis
(90301,  21,  6472, 0, 0, 97011, 0), -- Stinging Viper | Lord Pythas
(90301,  22,  6631, 0, 0, 97011, 0), -- Living Root | Verdan the Everliving

-- Extra
(90301,  23,  6446, 0, 0, 97011, 0), -- Snakeskin Bag | Lady Anacondra

-- =========================================================
-- THE DEADMINES
-- NPC 90302 | Currency 90012 | ExtendedCost 97012 | 22 items
-- https://www.wowhead.com/classic/zone=1581#drops;mode:normal
-- =========================================================

-- Armor
(90302,   0,  1156, 0, 0, 97012, 0), -- Lavishly Jeweled Ring | Gilnid
(90302,   1,  5193, 0, 0, 97012, 0), -- Cape of the Brotherhood | Edwin VanCleef
(90302,   2,  5195, 0, 0, 97012, 0), -- Gold-flecked Gloves | Sneed
(90302,   3,  5199, 0, 0, 97012, 0), -- Smelting Pants | Gilnid
(90302,   4,  5202, 0, 0, 97012, 0), -- Corsair's Overshirt | Edwin VanCleef
(90302,   5,  5443, 0, 0, 97012, 0), -- Gold-plated Buckler | Miner Johnson
(90302,   6,  5444, 0, 0, 97012, 0), -- Miner's Cape | Miner Johnson
(90302,   7, 10399, 0, 0, 97012, 0), -- Blackened Defias Armor | Edwin VanCleef
(90302,   8, 10403, 0, 0, 97012, 0), -- Blackened Defias Belt | Captain Greenskin

-- Weapons
(90302,   9,   872, 0, 0, 97012, 0), -- Rockslicer | Rhahk'Zor
(90302,  10,  1937, 0, 0, 97012, 0), -- Buzz Saw | Sneed's Shredder
(90302,  11,  2169, 0, 0, 97012, 0), -- Buzzer Blade | Sneed's Shredder
(90302,  12,  5187, 0, 0, 97012, 0), -- Rhahk'Zor's Hammer | Rhahk'Zor
(90302,  13,  5191, 0, 0, 97012, 0), -- Cruel Barb | Edwin VanCleef
(90302,  14,  5192, 0, 0, 97012, 0), -- Thief's Blade | Mr. Smite
(90302,  15,  5194, 0, 0, 97012, 0), -- Taskmaster Axe | Sneed
(90302,  16,  5196, 0, 0, 97012, 0), -- Smite's Reaver | Mr. Smite
(90302,  17,  5197, 0, 0, 97012, 0), -- Cookie's Tenderizer | Cookie
(90302,  18,  5198, 0, 0, 97012, 0), -- Cookie's Stirring Rod | Cookie
(90302,  19,  5200, 0, 0, 97012, 0), -- Impaling Harpoon | Captain Greenskin
(90302,  20,  5201, 0, 0, 97012, 0), -- Emberstone Staff | Captain Greenskin
(90302,  21,  7230, 0, 0, 97012, 0), -- Smite's Mighty Hammer | Mr. Smite

-- =========================================================
-- SHADOWFANG KEEP
-- NPC 90303 | Currency 90013 | ExtendedCost 97013 | 22 items
-- https://www.wowhead.com/classic/zone=209#drops;mode:normal
-- =========================================================

-- Armor
(90303,   0,  3230, 0, 0, 97013, 0), -- Black Wolf Bracers | Fenrus the Devourer
(90303,   1,  3748, 0, 0, 97013, 0), -- Feline Mantle | Wolf Master Nandos
(90303,   2,  5254, 0, 0, 97013, 0), -- Rugged Spaulders | Rethilgore
(90303,   3,  5943, 0, 0, 97013, 0), -- Rift Bracers | Arugal's Voidwalker
(90303,   4,  6226, 0, 0, 97013, 0), -- Bloody Apron | Razorclaw the Butcher
(90303,   5,  6314, 0, 0, 97013, 0), -- Wolfmaster Cape | Wolf Master Nandos
(90303,   6,  6319, 0, 0, 97013, 0), -- Girdle of the Blindwatcher | Odo the Blindwatcher
(90303,   7,  6320, 0, 0, 97013, 0), -- Commander's Crest | Commander Springvale
(90303,   8,  6321, 0, 0, 97013, 0), -- Silverlaine's Family Seal | Baron Silverlaine
(90303,   9,  6324, 0, 0, 97013, 0), -- Robes of Arugal | Archmage Arugal
(90303,  10,  6340, 0, 0, 97013, 0), -- Fenrus' Hide | Fenrus the Devourer
(90303,  11,  6392, 0, 0, 97013, 0), -- Belt of Arugal | Archmage Arugal
(90303,  12,  6642, 0, 0, 97013, 0), -- Phantom Armor | Deathsworn Captain
(90303,  13, 23173, 0, 0, 97013, 0), -- Abomination Skin Leggings | Sever

-- Weapons
(90303,  14,  1292, 0, 0, 97013, 0), -- Butcher's Cleaver | Razorclaw the Butcher
(90303,  15,  3191, 0, 0, 97013, 0), -- Arced War Axe | Commander Springvale
(90303,  16,  6220, 0, 0, 97013, 0), -- Meteor Shard | Archmage Arugal
(90303,  17,  6318, 0, 0, 97013, 0), -- Odo's Ley Staff | Odo the Blindwatcher
(90303,  18,  6323, 0, 0, 97013, 0), -- Baron's Scepter | Baron Silverlaine
(90303,  19,  6633, 0, 0, 97013, 0), -- Butcher's Slicer | Razorclaw the Butcher
(90303,  20,  6641, 0, 0, 97013, 0), -- Haunting Blade | Deathsworn Captain
(90303,  21, 23171, 0, 0, 97013, 0), -- The Axe of Severing | Sever

-- =========================================================
-- BLACKFATHOM DEEPS
-- NPC 90304 | Currency 90014 | ExtendedCost 97014 | 16 items
-- https://www.wowhead.com/classic/zone=719#drops;mode:normal
-- =========================================================

-- Armor
(90304,   0,   888, 0, 0, 97014, 0), -- Naga Battle Gloves | Lady Sarevess
(90304,   1,  6901, 0, 0, 97014, 0), -- Glowing Thresher Cape | Old Serra'kis
(90304,   2,  6902, 0, 0, 97014, 0), -- Bands of Serra'kis | Old Serra'kis
(90304,   3,  6903, 0, 0, 97014, 0), -- Gaze Dreamer Pants | Twilight Lord Kelris
(90304,   4,  6906, 0, 0, 97014, 0), -- Algae Fists | Gelihast
(90304,   5,  6907, 0, 0, 97014, 0), -- Tortoise Armor | Ghamoo-ra
(90304,   6,  6908, 0, 0, 97014, 0), -- Ghamoo-ra's Bind | Ghamoo-ra
(90304,   7,  6910, 0, 0, 97014, 0), -- Leech Pants | Aku'mai
(90304,   8,  6911, 0, 0, 97014, 0), -- Moss Cinch | Aku'mai

-- Weapons
(90304,   9,  1155, 0, 0, 97014, 0), -- Rod of the Sleepwalker | Twilight Lord Kelris
(90304,  10,  3078, 0, 0, 97014, 0), -- Naga Heartpiercer | Lady Sarevess
(90304,  11,  6904, 0, 0, 97014, 0), -- Bite of Serra'kis | Old Serra'kis
(90304,  12,  6905, 0, 0, 97014, 0), -- Reef Axe | Gelihast
(90304,  13,  6909, 0, 0, 97014, 0), -- Strike of the Hydra | Aku'mai
(90304,  14, 11121, 0, 0, 97014, 0), -- Darkwater Talwar | Lady Sarevess

-- Extra
(90304,  15,  1470, 0, 0, 97014, 0), -- Murloc Skin Bag | Gelihast

-- =========================================================
-- THE STOCKADE
-- NPC 90305 | Currency 90015 | ExtendedCost 97015 | 4 items
-- https://www.wowhead.com/classic/zone=717#drops;mode:normal
-- =========================================================

-- Armor
(90305,   0,  3228, 0, 0, 97015, 0), -- Jimmied Handcuffs | Bruegal Ironknuckle

-- Weapons
(90305,   1,  2280, 0, 0, 97015, 0), -- Kam's Walking Stick | Kam Deepfury
(90305,   2,  2941, 0, 0, 97015, 0), -- Prison Shank | Bruegal Ironknuckle
(90305,   3,  2942, 0, 0, 97015, 0), -- Iron Knuckles | Bruegal Ironknuckle

-- =========================================================
-- GNOMEREGAN
-- NPC 90306 | Currency 90016 | ExtendedCost 97016 | 22 items
-- https://www.wowhead.com/classic/zone=721#drops;mode:normal
-- =========================================================

-- Armor
(90306,   0,  9444, 0, 0, 97016, 0), -- Techbot CPU Shell | Techbot
(90306,   1,  9445, 0, 0, 97016, 0), -- Grubbis Paws | Grubbis
(90306,   2,  9447, 0, 0, 97016, 0), -- Electrocutioner Lagnut | Electrocutioner 6000
(90306,   3,  9448, 0, 0, 97016, 0), -- Spidertank Oilrag | Electrocutioner 6000
(90306,   4,  9450, 0, 0, 97016, 0), -- Gnomebot Operating Boots | Crowd Pummeler 9-60
(90306,   5,  9454, 0, 0, 97016, 0), -- Acidic Walkers | Viscous Fallout
(90306,   6,  9455, 0, 0, 97016, 0), -- Emissary Cuffs | Dark Iron Ambassador
(90306,   7,  9458, 0, 0, 97016, 0), -- Thermaplugg's Central Core | Mekgineer Thermaplugg
(90306,   8,  9461, 0, 0, 97016, 0), -- Charged Gear | Mekgineer Thermaplugg
(90306,   9,  9492, 0, 0, 97016, 0), -- Electromagnetic Gigaflux Reactivator | Mekgineer Thermaplugg

-- Weapons
(90306,  10,  9446, 0, 0, 97016, 0), -- Electrocutioner Leg | Electrocutioner 6000
(90306,  11,  9449, 0, 0, 97016, 0), -- Manual Crowd Pummeler | Crowd Pummeler 9-60
(90306,  12,  9452, 0, 0, 97016, 0), -- Hydrocane | Viscous Fallout
(90306,  13,  9453, 0, 0, 97016, 0), -- Toxic Revenger | Viscous Fallout
(90306,  14,  9456, 0, 0, 97016, 0), -- Glass Shooter | Dark Iron Ambassador
(90306,  15,  9457, 0, 0, 97016, 0), -- Royal Diplomatic Scepter | Dark Iron Ambassador
(90306,  16,  9459, 0, 0, 97016, 0), -- Thermaplugg's Left Arm | Mekgineer Thermaplugg

-- Extra
(90306,  17,  4411, 0, 0, 97016, 0), -- Schematic: Flame Deflector | Mekgineer Thermaplugg
(90306,  18,  4413, 0, 0, 97016, 0), -- Schematic: Discombobulator Ray | Mekgineer Thermaplugg
(90306,  19,  4415, 0, 0, 97016, 0), -- Schematic: Craftsman's Monocle | Mekgineer Thermaplugg
(90306,  20,  7742, 0, 0, 97016, 0), -- Schematic: Gnomish Cloaking Device | Mekgineer Thermaplugg
(90306,  21, 11828, 0, 0, 97016, 0), -- Schematic: Pet Bombling | Mekgineer Thermaplugg

-- =========================================================
-- RAZORFEN KRAUL
-- NPC 90307 | Currency 90017 | ExtendedCost 97017 | 17 items
-- https://www.wowhead.com/classic/zone=491#drops;mode:normal
-- =========================================================

-- Armor
(90307,   0,  6682, 0, 0, 97017, 0), -- Death Speaker Robes | Death Speaker Jargba
(90307,   1,  6685, 0, 0, 97017, 0), -- Death Speaker Mantle | Death Speaker Jargba
(90307,   2,  6686, 0, 0, 97017, 0), -- Tusken Helm | Overlord Ramtusk
(90307,   3,  6688, 0, 0, 97017, 0), -- Whisperwind Headdress | Earthcaller Halmgar
(90307,   4,  6690, 0, 0, 97017, 0), -- Ferine Leggings | Agathelos the Raging
(90307,   5,  6693, 0, 0, 97017, 0), -- Agamaggan's Clutch | Charlga Razorflank
(90307,   6,  6694, 0, 0, 97017, 0), -- Heart of Agamaggan | Charlga Razorflank
(90307,   7,  6695, 0, 0, 97017, 0), -- Stygian Bone Amulet | Blind Hunter
(90307,   8,  6697, 0, 0, 97017, 0), -- Batwing Mantle | Blind Hunter

-- Weapons
(90307,   9,  2816, 0, 0, 97017, 0), -- Death Speaker Scepter | Death Speaker Jargba
(90307,  10,  6679, 0, 0, 97017, 0), -- Armor Piercer | Razorfen Spearhide
(90307,  11,  6681, 0, 0, 97017, 0), -- Thornspike | Aggem Thorncurse
(90307,  12,  6687, 0, 0, 97017, 0), -- Corpsemaker | Overlord Ramtusk
(90307,  13,  6689, 0, 0, 97017, 0), -- Wind Spirit Staff | Earthcaller Halmgar
(90307,  14,  6691, 0, 0, 97017, 0), -- Swinetusk Shank | Agathelos the Raging
(90307,  15,  6692, 0, 0, 97017, 0), -- Pronged Reaver | Charlga Razorflank
(90307,  16,  6696, 0, 0, 97017, 0), -- Nightstalker Bow | Blind Hunter

-- =========================================================
-- SCARLET MONASTERY - GRAVEYARD
-- NPC 90308 | Currency 90018 | ExtendedCost 97018 | 16 items
-- https://www.wowhead.com/classic/zone=796#drops;mode:normal
-- =========================================================

-- Armor
(90308,   0,  7684, 0, 0, 97018, 0), -- Bloodmage Mantle | Bloodmage Thalnos
(90308,   1,  7685, 0, 0, 97018, 0), -- Orb of the Forgotten Seer | Bloodmage Thalnos
(90308,   2,  7686, 0, 0, 97018, 0), -- Ironspine's Eye | Ironspine
(90308,   3,  7688, 0, 0, 97018, 0), -- Ironspine's Ribcage | Ironspine
(90308,   4,  7690, 0, 0, 97018, 0), -- Ebon Vise | Fallen Champion
(90308,   5,  7691, 0, 0, 97018, 0), -- Embalmed Shroud | Fallen Champion
(90308,   6,  7709, 0, 0, 97018, 0), -- Blighted Leggings | Azshir the Sleepless
(90308,   7,  7731, 0, 0, 97018, 0), -- Ghostshard Talisman | Azshir the Sleepless
(90308,   8, 23169, 0, 0, 97018, 0), -- Scorn's Icy Choker | Scorn
(90308,   9, 23170, 0, 0, 97018, 0), -- The Frozen Clutch | Scorn

-- Weapons
(90308,  10,  7682, 0, 0, 97018, 0), -- Torturing Poker | Interrogator Vishas
(90308,  11,  7683, 0, 0, 97018, 0), -- Bloody Brass Knuckles | Interrogator Vishas
(90308,  12,  7687, 0, 0, 97018, 0), -- Ironspine's Fist | Ironspine
(90308,  13,  7689, 0, 0, 97018, 0), -- Morbid Dawn | Fallen Champion
(90308,  14,  7708, 0, 0, 97018, 0), -- Necrotic Wand | Azshir the Sleepless
(90308,  15, 23168, 0, 0, 97018, 0), -- Scorn's Focal Dagger | Scorn

-- =========================================================
-- SCARLET MONASTERY - LIBRARY
-- NPC 90309 | Currency 90019 | ExtendedCost 97019 | 6 items
-- https://www.wowhead.com/classic/zone=796#drops;mode:normal
-- =========================================================

-- Armor
(90309,   0,  7711, 0, 0, 97019, 0), -- Robe of Doan | Arcanist Doan
(90309,   1,  7712, 0, 0, 97019, 0), -- Mantle of Doan | Arcanist Doan
(90309,   2,  7756, 0, 0, 97019, 0), -- Dog Training Gloves | Houndmaster Loksey

-- Weapons
(90309,   3,  7710, 0, 0, 97019, 0), -- Loksey's Training Stick | Houndmaster Loksey
(90309,   4,  7713, 0, 0, 97019, 0), -- Illusionary Rod | Arcanist Doan
(90309,   5,  7714, 0, 0, 97019, 0), -- Hypnotic Blade | Arcanist Doan

-- =========================================================
-- SCARLET MONASTERY - ARMORY
-- NPC 90310 | Currency 90020 | ExtendedCost 97020 | 4 items
-- https://www.wowhead.com/classic/zone=796#drops;mode:normal
-- =========================================================

-- Armor
(90310,   0,  7718, 0, 0, 97020, 0), -- Herod's Shoulder | Herod
(90310,   1,  7719, 0, 0, 97020, 0), -- Raging Berserker's Helm | Herod
(90310,   2, 10330, 0, 0, 97020, 0), -- Scarlet Leggings | Herod

-- Weapons
(90310,   3,  7717, 0, 0, 97020, 0), -- Ravager | Herod

-- =========================================================
-- SCARLET MONASTERY - CATHEDRAL
-- NPC 90311 | Currency 90021 | ExtendedCost 97021 | 10 items
-- https://www.wowhead.com/classic/zone=796#drops;mode:normal
-- =========================================================

-- Armor
(90311,   0,  7720, 0, 0, 97021, 0), -- Whitemane's Chapeau | High Inquisitor Whitemane
(90311,   1,  7722, 0, 0, 97021, 0), -- Triune Amulet | High Inquisitor Whitemane
(90311,   2,  7724, 0, 0, 97021, 0), -- Gauntlets of Divinity | Scarlet Commander Mograine
(90311,   3,  7726, 0, 0, 97021, 0), -- Aegis of the Scarlet Commander | Scarlet Commander Mograine
(90311,   4, 10330, 0, 0, 97021, 0), -- Scarlet Leggings | Scarlet Commander Mograine
(90311,   5, 19507, 0, 0, 97021, 0), -- Inquisitor's Shawl | High Inquisitor Fairbanks
(90311,   6, 19508, 0, 0, 97021, 0), -- Branded Leather Bracers | High Inquisitor Fairbanks
(90311,   7, 19509, 0, 0, 97021, 0), -- Dusty Mail Boots | High Inquisitor Fairbanks

-- Weapons
(90311,   8,  7721, 0, 0, 97021, 0), -- Hand of Righteousness | High Inquisitor Whitemane
(90311,   9,  7723, 0, 0, 97021, 0), -- Mograine's Might | Scarlet Commander Mograine

-- =========================================================
-- RAZORFEN DOWNS
-- NPC 90312 | Currency 90022 | ExtendedCost 97022 | 20 items
-- https://www.wowhead.com/classic/zone=722#drops;mode:normal
-- =========================================================

-- Armor
(90312,   0, 10760, 0, 0, 97022, 0), -- Swine Fists | Plaguemaw the Rotting
(90312,   1, 10762, 0, 0, 97022, 0), -- Robes of the Lich | Amnennar the Coldbringer
(90312,   2, 10763, 0, 0, 97022, 0), -- Icemetal Barbute | Amnennar the Coldbringer
(90312,   3, 10764, 0, 0, 97022, 0), -- Deathchill Armor | Amnennar the Coldbringer
(90312,   4, 10765, 0, 0, 97022, 0), -- Bonefingers | Amnennar the Coldbringer
(90312,   5, 10767, 0, 0, 97022, 0), -- Savage Boar's Guard | Ragglesnout
(90312,   6, 10768, 0, 0, 97022, 0), -- Boar Champion's Belt | Ragglesnout
(90312,   7, 10769, 0, 0, 97022, 0), -- Glowing Eye of Mordresh | Mordresh Fire Eye
(90312,   8, 10770, 0, 0, 97022, 0), -- Mordresh's Lifeless Skull | Mordresh Fire Eye
(90312,   9, 10771, 0, 0, 97022, 0), -- Deathmage Sash | Mordresh Fire Eye
(90312,  10, 10774, 0, 0, 97022, 0), -- Fleshhide Shoulders | Glutton
(90312,  11, 10775, 0, 0, 97022, 0), -- Carapace of Tuten'kash | Tuten'kash
(90312,  12, 10776, 0, 0, 97022, 0), -- Silky Spider Cape | Tuten'kash
(90312,  13, 10777, 0, 0, 97022, 0), -- Arachnid Gloves | Tuten'kash
(90312,  14, 23178, 0, 0, 97022, 0), -- Mantle of Lady Falther'ess | Lady Falther'ess

-- Weapons
(90312,  15, 10758, 0, 0, 97022, 0), -- X'caliboar | Ragglesnout
(90312,  16, 10761, 0, 0, 97022, 0), -- Coldrage Dagger | Amnennar the Coldbringer
(90312,  17, 10766, 0, 0, 97022, 0), -- Plaguerot Sprig | Plaguemaw the Rotting
(90312,  18, 10772, 0, 0, 97022, 0), -- Glutton's Cleaver | Glutton
(90312,  19, 23177, 0, 0, 97022, 0), -- Lady Falther'ess' Finger | Lady Falther'ess

-- =========================================================
-- ULDAMAN
-- NPC 90313 | Currency 90023 | ExtendedCost 97023 | 25 items
-- https://www.wowhead.com/classic/zone=1337#drops;mode:normal
-- =========================================================

-- Armor
(90313,   0,  9387, 0, 0, 97023, 0), -- Revelosh's Boots | Revelosh
(90313,   1,  9388, 0, 0, 97023, 0), -- Revelosh's Armguards | Revelosh
(90313,   2,  9389, 0, 0, 97023, 0), -- Revelosh's Spaulders | Revelosh
(90313,   3,  9390, 0, 0, 97023, 0), -- Revelosh's Gloves | Revelosh
(90313,   4,  9394, 0, 0, 97023, 0), -- Horned Viking Helmet | Eric "The Swift"
(90313,   5,  9398, 0, 0, 97023, 0), -- Worn Running Boots | Eric "The Swift"
(90313,   6,  9403, 0, 0, 97023, 0), -- Battered Viking Shield | Olaf
(90313,   7,  9404, 0, 0, 97023, 0), -- Olaf's All Purpose Shield | Olaf
(90313,   8,  9407, 0, 0, 97023, 0), -- Stoneweaver Leggings | Ironaya
(90313,   9,  9409, 0, 0, 97023, 0), -- Ironaya's Bracers | Ironaya
(90313,  10,  9410, 0, 0, 97023, 0), -- Cragfists | Ancient Stone Keeper
(90313,  11,  9411, 0, 0, 97023, 0), -- Rockshard Pauldrons | Ancient Stone Keeper
(90313,  12,  9414, 0, 0, 97023, 0), -- Oilskin Leggings | Grimlok
(90313,  13,  9415, 0, 0, 97023, 0), -- Grimlok's Tribal Vestments | Grimlok
(90313,  14, 11118, 0, 0, 97023, 0), -- Archaedic Stone | Archaedas
(90313,  15, 11310, 0, 0, 97023, 0), -- Flameseer Mantle | Galgann Firehammer
(90313,  16, 11311, 0, 0, 97023, 0), -- Emberscale Cape | Galgann Firehammer

-- Weapons
(90313,  17,  9400, 0, 0, 97023, 0), -- Baelog's Shortbow | Baelog
(90313,  18,  9401, 0, 0, 97023, 0), -- Nordic Longshank | Baelog
(90313,  19,  9408, 0, 0, 97023, 0), -- Ironshod Bludgeon | Ironaya
(90313,  20,  9412, 0, 0, 97023, 0), -- Galgann's Fireblaster | Galgann Firehammer
(90313,  21,  9413, 0, 0, 97023, 0), -- The Rockpounder | Archaedas
(90313,  22,  9416, 0, 0, 97023, 0), -- Grimlok's Charge | Grimlok
(90313,  23,  9418, 0, 0, 97023, 0), -- Stoneslayer | Archaedas
(90313,  24,  9419, 0, 0, 97023, 0), -- Galgann's Firehammer | Galgann Firehammer

-- =========================================================
-- ZUL'FARRAK
-- NPC 90314 | Currency 90024 | ExtendedCost 97024 | 19 items
-- https://www.wowhead.com/classic/zone=1176#drops;mode:normal
-- =========================================================

-- Armor
(90314,   0,  9469, 0, 0, 97024, 0), -- Gahz'rilla Scale Armor | Gahz'rilla
(90314,   1,  9470, 0, 0, 97024, 0), -- Bad Mojo Mask | Shadowpriest Sezz'ziz
(90314,   2,  9473, 0, 0, 97024, 0), -- Jinxed Hoodoo Skin | Shadowpriest Sezz'ziz
(90314,   3,  9474, 0, 0, 97024, 0), -- Jinxed Hoodoo Kilt | Shadowpriest Sezz'ziz
(90314,   4,  9476, 0, 0, 97024, 0), -- Big Bad Pauldrons | Chief Ukorz Sandscalp
(90314,   5,  9479, 0, 0, 97024, 0), -- Embrace of the Lycan | Chief Ukorz Sandscalp
(90314,   6,  9640, 0, 0, 97024, 0), -- Vice Grips | Antu'sul
(90314,   7,  9641, 0, 0, 97024, 0), -- Lifeblood Amulet | Antu'sul
(90314,   8, 12470, 0, 0, 97024, 0), -- Sandstalker Ankleguards | Zerillis
(90314,   9, 12471, 0, 0, 97024, 0), -- Desertwalker Cane | Dustwraith
(90314,  10, 18083, 0, 0, 97024, 0), -- Jumanza Grips | Witch Doctor Zum'rah

-- Weapons
(90314,  11,  9379, 0, 0, 97024, 0), -- Sang'thraze the Deflector | Antu'sul
(90314,  12,  9467, 0, 0, 97024, 0), -- Gahz'rilla Fang | Gahz'rilla
(90314,  13,  9475, 0, 0, 97024, 0), -- Diabolic Skiver | Shadowpriest Sezz'ziz
(90314,  14,  9477, 0, 0, 97024, 0), -- The Chief's Enforcer | Chief Ukorz Sandscalp
(90314,  15,  9478, 0, 0, 97024, 0), -- Ripsaw | Chief Ukorz Sandscalp
(90314,  16,  9639, 0, 0, 97024, 0), -- The Hand of Antu'sul | Antu'sul
(90314,  17, 11086, 0, 0, 97024, 0), -- Jang'thraze the Protector | Chief Ukorz Sandscalp
(90314,  18, 18082, 0, 0, 97024, 0), -- Zum'rah's Vexing Cane | Witch Doctor Zum'rah

-- =========================================================
-- MARAUDON
-- NPC 90315 | Currency 90025 | ExtendedCost 97025 | 34 items
-- https://www.wowhead.com/classic/zone=2100#drops;mode:normal
-- =========================================================

-- Armor
(90315,   0, 17707, 0, 0, 97025, 0), -- Gemshard Heart | Princess Theradras
(90315,   1, 17711, 0, 0, 97025, 0), -- Elemental Rockridge Leggings | Princess Theradras
(90315,   2, 17713, 0, 0, 97025, 0), -- Blackstone Ring | Princess Theradras
(90315,   3, 17714, 0, 0, 97025, 0), -- Bracers of the Stone Princess | Princess Theradras
(90315,   4, 17715, 0, 0, 97025, 0), -- Eye of Theradras | Princess Theradras
(90315,   5, 17718, 0, 0, 97025, 0), -- Gizlock's Hypertech Buckler | Tinkerer Gizlock
(90315,   6, 17728, 0, 0, 97025, 0), -- Albino Crocscale Boots | Rotgrip
(90315,   7, 17732, 0, 0, 97025, 0), -- Rotgrip Mantle | Rotgrip
(90315,   8, 17734, 0, 0, 97025, 0), -- Helm of the Mountain | Landslide
(90315,   9, 17736, 0, 0, 97025, 0), -- Rockgrip Gauntlets | Landslide
(90315,  10, 17737, 0, 0, 97025, 0), -- Cloud Stone | Landslide
(90315,  11, 17739, 0, 0, 97025, 0), -- Grovekeeper's Drape | Celebras the Cursed
(90315,  12, 17740, 0, 0, 97025, 0), -- Soothsayer's Headdress | Celebras the Cursed
(90315,  13, 17741, 0, 0, 97025, 0), -- Nature's Embrace | Meshlok the Harvester
(90315,  14, 17742, 0, 0, 97025, 0), -- Fungus Shroud Armor | Meshlok the Harvester
(90315,  15, 17744, 0, 0, 97025, 0), -- Heart of Noxxion | Noxxion
(90315,  16, 17746, 0, 0, 97025, 0), -- Noxxion's Shackles | Noxxion
(90315,  17, 17748, 0, 0, 97025, 0), -- Vinerot Sandals | Razorlash
(90315,  18, 17749, 0, 0, 97025, 0), -- Phytoskin Spaulders | Razorlash
(90315,  19, 17750, 0, 0, 97025, 0), -- Chloromesh Girdle | Razorlash
(90315,  20, 17751, 0, 0, 97025, 0), -- Brusslehide Leggings | Razorlash
(90315,  21, 17754, 0, 0, 97025, 0), -- Infernal Trickster Leggings | Lord Vyletongue
(90315,  22, 17755, 0, 0, 97025, 0), -- Satyrmane Sash | Lord Vyletongue
(90315,  23, 17767, 0, 0, 97025, 0), -- Bloomsprout Headpiece | Meshlok the Harvester

-- Weapons
(90315,  24, 17710, 0, 0, 97025, 0), -- Charstone Dirk | Princess Theradras
(90315,  25, 17717, 0, 0, 97025, 0), -- Megashot Rifle | Tinkerer Gizlock
(90315,  26, 17719, 0, 0, 97025, 0), -- Inventor's Focal Sword | Tinkerer Gizlock
(90315,  27, 17730, 0, 0, 97025, 0), -- Gatorbite Axe | Rotgrip
(90315,  28, 17738, 0, 0, 97025, 0), -- Claw of Celebras | Celebras the Cursed
(90315,  29, 17745, 0, 0, 97025, 0), -- Noxious Shooter | Noxxion
(90315,  30, 17752, 0, 0, 97025, 0), -- Satyr's Lash | Lord Vyletongue
(90315,  31, 17766, 0, 0, 97025, 0), -- Princess Theradras' Scepter | Princess Theradras
(90315,  32, 17780, 0, 0, 97025, 0), -- Blade of Eternal Darkness | Princess Theradras
(90315,  33, 17943, 0, 0, 97025, 0), -- Fist of Stone | Landslide

-- =========================================================
-- THE TEMPLE OF ATAL'HAKKAR
-- NPC 90316 | Currency 90026 | ExtendedCost 97026 | 39 items
-- https://www.wowhead.com/classic/zone=1477#drops;mode:normal
-- =========================================================

-- Armor
(90316,   0, 10783, 0, 0, 97026, 0), -- Atal'ai Spaulders | Balcony Minibosses
(90316,   1, 10784, 0, 0, 97026, 0), -- Atal'ai Breastplate | Balcony Minibosses
(90316,   2, 10785, 0, 0, 97026, 0), -- Atal'ai Leggings | Balcony Minibosses
(90316,   3, 10786, 0, 0, 97026, 0), -- Atal'ai Boots | Balcony Minibosses
(90316,   4, 10787, 0, 0, 97026, 0), -- Atal'ai Gloves | Balcony Minibosses
(90316,   5, 10788, 0, 0, 97026, 0), -- Atal'ai Girdle | Balcony Minibosses
(90316,   6, 10795, 0, 0, 97026, 0), -- Drakeclaw Band | Dreamscythe / Weaver / Hazzas / Morphaz
(90316,   7, 10796, 0, 0, 97026, 0), -- Drakestone | Dreamscythe / Weaver / Hazzas / Morphaz
(90316,   8, 10798, 0, 0, 97026, 0), -- Atal'alarion's Tusk Ring | Atal'alarion
(90316,   9, 10800, 0, 0, 97026, 0), -- Darkwater Bracers | Atal'alarion
(90316,  10, 10801, 0, 0, 97026, 0), -- Slitherscale Boots | Spawn of Hakkar
(90316,  11, 10802, 0, 0, 97026, 0), -- Wingveil Cloak | Spawn of Hakkar
(90316,  12, 10806, 0, 0, 97026, 0), -- Vestments of the Atal'ai Prophet | Jammal'an the Prophet
(90316,  13, 10807, 0, 0, 97026, 0), -- Kilt of the Atal'ai Prophet | Jammal'an the Prophet
(90316,  14, 10808, 0, 0, 97026, 0), -- Gloves of the Atal'ai Prophet | Jammal'an the Prophet
(90316,  15, 10829, 0, 0, 97026, 0), -- The Dragon's Eye | Shade of Eranikus
(90316,  16, 10833, 0, 0, 97026, 0), -- Horns of Eranikus | Shade of Eranikus
(90316,  17, 10835, 0, 0, 97026, 0), -- Crest of Supremacy | Shade of Eranikus
(90316,  18, 10842, 0, 0, 97026, 0), -- Windscale Sarong | Avatar of Hakkar
(90316,  19, 10843, 0, 0, 97026, 0), -- Featherskin Cape | Avatar of Hakkar
(90316,  20, 10845, 0, 0, 97026, 0), -- Warrior's Embrace | Avatar of Hakkar
(90316,  21, 10846, 0, 0, 97026, 0), -- Bloodshot Greaves | Avatar of Hakkar
(90316,  22, 12462, 0, 0, 97026, 0), -- Embrace of the Wind Serpent | Avatar of Hakkar
(90316,  23, 12464, 0, 0, 97026, 0), -- Bloodfire Talons | Dreamscythe / Weaver / Hazzas / Morphaz
(90316,  24, 12465, 0, 0, 97026, 0), -- Nightfall Drape | Dreamscythe / Weaver / Hazzas / Morphaz
(90316,  25, 12466, 0, 0, 97026, 0), -- Dawnspire Cord | Dreamscythe / Weaver / Hazzas / Morphaz

-- Weapons
(90316,  26, 10797, 0, 0, 97026, 0), -- Firebreather | Dreamscythe / Weaver / Hazzas / Morphaz
(90316,  27, 10799, 0, 0, 97026, 0), -- Headspike | Atal'alarion
(90316,  28, 10803, 0, 0, 97026, 0), -- Blade of the Wretched | Ogom the Wretched
(90316,  29, 10804, 0, 0, 97026, 0), -- Fist of the Damned | Ogom the Wretched
(90316,  30, 10805, 0, 0, 97026, 0), -- Eater of the Dead | Ogom the Wretched
(90316,  31, 10828, 0, 0, 97026, 0), -- Dire Nail | Shade of Eranikus
(90316,  32, 10836, 0, 0, 97026, 0), -- Rod of Corrosion | Shade of Eranikus
(90316,  33, 10837, 0, 0, 97026, 0), -- Tooth of Eranikus | Shade of Eranikus
(90316,  34, 10838, 0, 0, 97026, 0), -- Might of Hakkar | Avatar of Hakkar
(90316,  35, 10844, 0, 0, 97026, 0), -- Spire of Hakkar | Avatar of Hakkar
(90316,  36, 10847, 0, 0, 97026, 0), -- Dragon's Call | Shade of Eranikus
(90316,  37, 12243, 0, 0, 97026, 0), -- Smoldering Claw | Dreamscythe / Weaver / Hazzas / Morphaz
(90316,  38, 12463, 0, 0, 97026, 0), -- Drakefang Butcher | Dreamscythe / Weaver / Hazzas / Morphaz

-- =========================================================
-- BLACKROCK DEPTHS
-- NPC 90317 | Currency 90027 | ExtendedCost 97027 | 132 items
-- https://www.wowhead.com/classic/zone=1584#drops;mode:normal
-- =========================================================

-- Armor
(90317,   0, 11623, 0, 0, 97027, 0), -- Spritecaster Cape | Houndmaster Grebmar
(90317,   1, 11624, 0, 0, 97027, 0), -- Kentic Amice | High Interrogator Gerstahn
(90317,   2, 11625, 0, 0, 97027, 0), -- Enthralled Sphere | High Interrogator Gerstahn
(90317,   3, 11626, 0, 0, 97027, 0), -- Blackveil Cape | High Interrogator Gerstahn
(90317,   4, 11627, 0, 0, 97027, 0), -- Fleetfoot Greaves | Houndmaster Grebmar
(90317,   5, 11631, 0, 0, 97027, 0), -- Stoneshell Guard | Lord Roccor
(90317,   6, 11632, 0, 0, 97027, 0), -- Earthslag Shoulders | Lord Roccor
(90317,   7, 11633, 0, 0, 97027, 0), -- Spiderfang Carapace | Hedrum the Creeper
(90317,   8, 11634, 0, 0, 97027, 0), -- Silkweb Gloves | Hedrum the Creeper
(90317,   9, 11662, 0, 0, 97027, 0), -- Ban'thok Sash | Ok'thor the Breaker
(90317,  10, 11665, 0, 0, 97027, 0), -- Ogreseer Fists | Ok'thor the Breaker
(90317,  11, 11669, 0, 0, 97027, 0), -- Naglering | Golem Lord Argelmach
(90317,  12, 11675, 0, 0, 97027, 0), -- Shadefiend Boots | Anub'shiah
(90317,  13, 11677, 0, 0, 97027, 0), -- Graverot Cape | Anub'shiah
(90317,  14, 11678, 0, 0, 97027, 0), -- Carapace of Anub'shiah | Anub'shiah
(90317,  15, 11679, 0, 0, 97027, 0), -- Rubicund Armguards | Eviscerator
(90317,  16, 11685, 0, 0, 97027, 0), -- Splinthide Shoulders | Eviscerator
(90317,  17, 11686, 0, 0, 97027, 0), -- Girdle of Beastial Fury | Eviscerator
(90317,  18, 11703, 0, 0, 97027, 0), -- Stonewall Girdle | Grizzle
(90317,  19, 11722, 0, 0, 97027, 0), -- Dregmetal Spaulders | Grizzle
(90317,  20, 11726, 0, 0, 97027, 0), -- Savage Gladiator Chain | Gorosh the Dervish
(90317,  21, 11728, 0, 0, 97027, 0), -- Savage Gladiator Leggings | Ok'thor the Breaker
(90317,  22, 11729, 0, 0, 97027, 0), -- Savage Gladiator Helm | Hedrum the Creeper
(90317,  23, 11730, 0, 0, 97027, 0), -- Savage Gladiator Grips | Eviscerator
(90317,  24, 11731, 0, 0, 97027, 0), -- Savage Gladiator Greaves | Anub'shiah
(90317,  25, 11735, 0, 0, 97027, 0), -- Ragefury Eyepatch | Guzzler
(90317,  26, 11745, 0, 0, 97027, 0), -- Fists of Phalanx | Phalanx
(90317,  27, 11746, 0, 0, 97027, 0), -- Golem Skull Helm | Magmus
(90317,  28, 11747, 0, 0, 97027, 0), -- Flamestrider Robes | Pyromancer Loregrain
(90317,  29, 11749, 0, 0, 97027, 0), -- Searingscale Leggings | Pyromancer Loregrain
(90317,  30, 11755, 0, 0, 97027, 0), -- Verek's Collar | Verek
(90317,  31, 11764, 0, 0, 97027, 0), -- Cinderhide Armsplints | Lord Incendius
(90317,  32, 11765, 0, 0, 97027, 0), -- Pyremail Wristguards | Lord Incendius
(90317,  33, 11766, 0, 0, 97027, 0), -- Flameweave Cuffs | Lord Incendius
(90317,  34, 11767, 0, 0, 97027, 0), -- Emberplate Armguards | Lord Incendius
(90317,  35, 11768, 0, 0, 97027, 0), -- Incendic Bracers | Lord Incendius
(90317,  36, 11782, 0, 0, 97027, 0), -- Boreal Mantle | Warder Stilgiss
(90317,  37, 11783, 0, 0, 97027, 0), -- Chillsteel Girdle | Warder Stilgiss
(90317,  38, 11785, 0, 0, 97027, 0), -- Rock Golem Bulwark | Panzor the Invincible
(90317,  39, 11787, 0, 0, 97027, 0), -- Shalehusk Boots | Panzor the Invincible
(90317,  40, 11802, 0, 0, 97027, 0), -- Lavacrest Leggings | Bael'Gar
(90317,  41, 11807, 0, 0, 97027, 0), -- Sash of the Burning Heart | Bael'Gar
(90317,  42, 11808, 0, 0, 97027, 0), -- Circle of Flame | Ambassador Flamelash
(90317,  43, 11810, 0, 0, 97027, 0), -- Force of Will | General Angerforge
(90317,  44, 11812, 0, 0, 97027, 0), -- Cape of the Fire Salamander | Ambassador Flamelash
(90317,  45, 11814, 0, 0, 97027, 0), -- Molten Fists | Ambassador Flamelash
(90317,  46, 11815, 0, 0, 97027, 0), -- Hand of Justice | Emperor Dagran Thaurissan
(90317,  47, 11819, 0, 0, 97027, 0), -- Second Wind | Golem Lord Argelmach
(90317,  48, 11820, 0, 0, 97027, 0), -- Royal Decorated Armor | General Angerforge
(90317,  49, 11821, 0, 0, 97027, 0), -- Warstrife Leggings | General Angerforge
(90317,  50, 11822, 0, 0, 97027, 0), -- Omnicast Boots | Golem Lord Argelmach
(90317,  51, 11823, 0, 0, 97027, 0), -- Luminary Kilt | Golem Lord Argelmach
(90317,  52, 11824, 0, 0, 97027, 0), -- Cyclopean Band | Ok'thor the Breaker
(90317,  53, 11832, 0, 0, 97027, 0), -- Burst of Knowledge | Ambassador Flamelash
(90317,  54, 11839, 0, 0, 97027, 0), -- Chief Architect's Monocle | Fineous Darkvire
(90317,  55, 11840, 0, 0, 97027, 0), -- Master Builder's Shirt | Fineous Darkvire
(90317,  56, 11841, 0, 0, 97027, 0), -- Senior Designer's Pantaloons | Fineous Darkvire / General Angerforge
(90317,  57, 11842, 0, 0, 97027, 0), -- Lead Surveyor's Mantle | Fineous Darkvire
(90317,  58, 11924, 0, 0, 97027, 0), -- Robes of the Royal Crown | Emperor Dagran Thaurissan
(90317,  59, 11925, 0, 0, 97027, 0), -- Ghostshroud | Chest of The Seven
(90317,  60, 11926, 0, 0, 97027, 0), -- Deathdealer Breastplate | Chest of The Seven
(90317,  61, 11927, 0, 0, 97027, 0), -- Legplates of the Eternal Guardian | Chest of The Seven
(90317,  62, 11928, 0, 0, 97027, 0), -- Thaurissan's Royal Scepter | Emperor Dagran Thaurissan
(90317,  63, 11929, 0, 0, 97027, 0), -- Haunting Specter Leggings | Chest of The Seven
(90317,  64, 11930, 0, 0, 97027, 0), -- The Emperor's New Cape | Emperor Dagran Thaurissan
(90317,  65, 11933, 0, 0, 97027, 0), -- Imperial Jewel | Emperor Dagran Thaurissan
(90317,  66, 11934, 0, 0, 97027, 0), -- Emperor's Seal | Emperor Dagran Thaurissan
(90317,  67, 11935, 0, 0, 97027, 0), -- Magmus Stone | Magmus
(90317,  68, 12553, 0, 0, 97027, 0), -- Swiftwalker Boots | Princess Moira Bronzebeard
(90317,  69, 12554, 0, 0, 97027, 0), -- Hands of the Exalted Herald | Princess Moira Bronzebeard
(90317,  70, 12556, 0, 0, 97027, 0), -- High Priestess Boots | Princess Moira Bronzebeard
(90317,  71, 12557, 0, 0, 97027, 0), -- Ebonsteel Spaulders | Princess Moira Bronzebeard
(90317,  72, 12793, 0, 0, 97027, 0), -- Mixologist's Tunic | Guzzler
(90317,  73, 18043, 0, 0, 97027, 0), -- Coal Miner Boots | Guzzler
(90317,  74, 22204, 0, 0, 97027, 0), -- Wristguards of Renown | Emperor Dagran Thaurissan
(90317,  75, 22205, 0, 0, 97027, 0), -- Black Steel Bindings | Watchman Doomgrip
(90317,  76, 22207, 0, 0, 97027, 0), -- Sash of the Grand Hunt | Emperor Dagran Thaurissan
(90317,  77, 22212, 0, 0, 97027, 0), -- Golem Fitted Pauldrons | Phalanx
(90317,  78, 22223, 0, 0, 97027, 0), -- Foreman's Head Protector | Fineous Darkvire
(90317,  79, 22234, 0, 0, 97027, 0), -- Mantle of Lost Hope | Lord Roccor
(90317,  80, 22240, 0, 0, 97027, 0), -- Greaves of Withering Despair | High Interrogator Gerstahn
(90317,  81, 22241, 0, 0, 97027, 0), -- Dark Warder's Pauldrons | Warder Stilgiss
(90317,  82, 22242, 0, 0, 97027, 0), -- Verek's Leash | Verek
(90317,  83, 22245, 0, 0, 97027, 0), -- Soot Encrusted Footwear | Panzor the Invincible
(90317,  84, 22255, 0, 0, 97027, 0), -- Magma Forged Band | Watchman Doomgrip
(90317,  85, 22256, 0, 0, 97027, 0), -- Mana Shaping Handwraps | Watchman Doomgrip
(90317,  86, 22257, 0, 0, 97027, 0), -- Bloodclot Band | Gorosh the Dervish
(90317,  87, 22270, 0, 0, 97027, 0), -- Entrenching Boots | Grizzle
(90317,  88, 22271, 0, 0, 97027, 0), -- Leggings of Frenzied Magic | Gorosh the Dervish
(90317,  89, 22275, 0, 0, 97027, 0), -- Firemoss Boots | Guzzler
(90317,  90, 22305, 0, 0, 97027, 0), -- Ironweave Mantle | Theldren
(90317,  91, 22330, 0, 0, 97027, 0), -- Shroud of Arcane Mastery | Theldren
(90317,  92, 22395, 0, 0, 97027, 0), -- Totem of Rage | Magmus
(90317,  93, 22397, 0, 0, 97027, 0), -- Idol of Ferocity | Lord Roccor
(90317,  94, 22400, 0, 0, 97027, 0), -- Libram of Truth | Magmus

-- Weapons
(90317,  95, 11628, 0, 0, 97027, 0), -- Houndmaster's Bow | Houndmaster Grebmar
(90317,  96, 11629, 0, 0, 97027, 0), -- Houndmaster's Rifle | Houndmaster Grebmar
(90317,  97, 11635, 0, 0, 97027, 0), -- Hookfang Shanker | Hedrum the Creeper
(90317,  98, 11684, 0, 0, 97027, 0), -- Ironfoe | Emperor Dagran Thaurissan
(90317,  99, 11702, 0, 0, 97027, 0), -- Grizzle's Skinner | Grizzle
(90317, 100, 11743, 0, 0, 97027, 0), -- Rockfist | Phalanx
(90317, 101, 11744, 0, 0, 97027, 0), -- Bloodfist | Phalanx
(90317, 102, 11748, 0, 0, 97027, 0), -- Pyric Caduceus | Pyromancer Loregrain
(90317, 103, 11750, 0, 0, 97027, 0), -- Kindling Stave | Pyromancer Loregrain
(90317, 104, 11784, 0, 0, 97027, 0), -- Arbiter's Blade | Warder Stilgiss
(90317, 105, 11786, 0, 0, 97027, 0), -- Stone of the Earth | Panzor the Invincible
(90317, 106, 11803, 0, 0, 97027, 0), -- Force of Magma | Bael'Gar
(90317, 107, 11805, 0, 0, 97027, 0), -- Rubidium Hammer | Bael'Gar
(90317, 108, 11809, 0, 0, 97027, 0), -- Flame Wrath | Ambassador Flamelash
(90317, 109, 11816, 0, 0, 97027, 0), -- Angerforge's Battle Axe | General Angerforge
(90317, 110, 11817, 0, 0, 97027, 0), -- Lord General's Sword | General Angerforge
(90317, 111, 11920, 0, 0, 97027, 0), -- Wraith Scythe | Chest of The Seven
(90317, 112, 11921, 0, 0, 97027, 0), -- Impervious Giant | Chest of The Seven
(90317, 113, 11922, 0, 0, 97027, 0), -- Blood-etched Blade | Chest of The Seven
(90317, 114, 11923, 0, 0, 97027, 0), -- The Hammer of Grace | Chest of The Seven
(90317, 115, 11931, 0, 0, 97027, 0), -- Dreadforge Retaliator | Emperor Dagran Thaurissan
(90317, 116, 11932, 0, 0, 97027, 0), -- Guiding Stave of Wisdom | Emperor Dagran Thaurissan
(90317, 117, 12791, 0, 0, 97027, 0), -- Barman Shanker | Guzzler
(90317, 118, 18044, 0, 0, 97027, 0), -- Hurley's Tankard | Guzzler
(90317, 119, 22208, 0, 0, 97027, 0), -- Lavastone Hammer | Magmus
(90317, 120, 22254, 0, 0, 97027, 0), -- Wand of Eternal Light | Watchman Doomgrip
(90317, 121, 22266, 0, 0, 97027, 0), -- Flarethorn | Gorosh the Dervish
(90317, 122, 22317, 0, 0, 97027, 0), -- Lefty's Brass Knuckle | Theldren
(90317, 123, 22318, 0, 0, 97027, 0), -- Malgen's Long Bow | Theldren

-- Extra
(90317, 124,  2662, 0, 0, 97027, 0), -- Ribbly's Quiver | Guzzler
(90317, 125,  2663, 0, 0, 97027, 0), -- Ribbly's Bandolier | Guzzler
(90317, 126, 11207, 0, 0, 97027, 0), -- Formula: Enchant Weapon - Fiery Weapon | Pyromancer Loregrain
(90317, 127, 11610, 0, 0, 97027, 0), -- Plans: Dark Iron Pulverizer | Grizzle
(90317, 128, 11612, 0, 0, 97027, 0), -- Plans: Dark Iron Plate | Guzzler
(90317, 129, 11742, 0, 0, 97027, 0), -- Wayfarer's Knapsack | Guzzler
(90317, 130, 11813, 0, 0, 97027, 0), -- Formula: Smoking Heart of the Mountain | Lord Roccor
(90317, 131, 18653, 0, 0, 97027, 0), -- Schematic: Goblin Jumper Cables XL | Guzzler

-- =========================================================
-- LOWER BLACKROCK SPIRE
-- NPC 90318 | Currency 90028 | ExtendedCost 97028 | 70 items
-- https://www.wowhead.com/classic/zone=1583#drops;mode:normal
-- =========================================================

-- Armor
(90318,   0, 12608, 0, 0, 97028, 0), -- Butcher's Apron | Spirestone Butcher
(90318,   1, 12626, 0, 0, 97028, 0), -- Funeral Cuffs | Shadow Hunter Vosh'gajin
(90318,   2, 12634, 0, 0, 97028, 0), -- Chiselbrand Girdle | Bannok Grimaxe
(90318,   3, 12637, 0, 0, 97028, 0), -- Backusarian Gauntlets | Bannok Grimaxe
(90318,   4, 13143, 0, 0, 97028, 0), -- Mark of the Dragon Lord | Overlord Wyrmthalak
(90318,   5, 13162, 0, 0, 97028, 0), -- Reiver Claws | Overlord Wyrmthalak
(90318,   6, 13164, 0, 0, 97028, 0), -- Heart of the Scale | Overlord Wyrmthalak
(90318,   7, 13166, 0, 0, 97028, 0), -- Slamshot Shoulders | Highlord Omokk
(90318,   8, 13168, 0, 0, 97028, 0), -- Plate of the Shaman King | Highlord Omokk
(90318,   9, 13169, 0, 0, 97028, 0), -- Tressermane Leggings | Highlord Omokk
(90318,  10, 13170, 0, 0, 97028, 0), -- Skyshroud Leggings | Highlord Omokk
(90318,  11, 13177, 0, 0, 97028, 0), -- Talisman of Evasion | War Master Voone
(90318,  12, 13178, 0, 0, 97028, 0), -- Rosewine Circle | Urok Doomhowl
(90318,  13, 13179, 0, 0, 97028, 0), -- Brazecore Armguards | War Master Voone
(90318,  14, 13181, 0, 0, 97028, 0), -- Demonskin Gloves | Burning Felguard
(90318,  15, 13184, 0, 0, 97028, 0), -- Fallbrush Handgrips | Crystal Fang
(90318,  16, 13185, 0, 0, 97028, 0), -- Sunderseer Mantle | Crystal Fang
(90318,  17, 13203, 0, 0, 97028, 0), -- Armswake Cloak | Ghok Bashguud
(90318,  18, 13205, 0, 0, 97028, 0), -- Rhombeard Protector | Gizrul the Slavener
(90318,  19, 13206, 0, 0, 97028, 0), -- Wolfshear Leggings | Gizrul the Slavener
(90318,  20, 13208, 0, 0, 97028, 0), -- Bleak Howler Armguards | Gizrul the Slavener
(90318,  21, 13210, 0, 0, 97028, 0), -- Pads of the Dread Wolf | Halycon
(90318,  22, 13211, 0, 0, 97028, 0), -- Slashclaw Bracers | Halycon
(90318,  23, 13212, 0, 0, 97028, 0), -- Halycon's Spiked Collar | Halycon
(90318,  24, 13213, 0, 0, 97028, 0), -- Smolderweb's Eye | Mother Smolderweb
(90318,  25, 13244, 0, 0, 97028, 0), -- Gilded Gauntlets | Mother Smolderweb
(90318,  26, 13252, 0, 0, 97028, 0), -- Cloudrunner Girdle | Quartermaster Zigris
(90318,  27, 13253, 0, 0, 97028, 0), -- Hands of Power | Quartermaster Zigris
(90318,  28, 13255, 0, 0, 97028, 0), -- Trueaim Gauntlets | Shadow Hunter Vosh'gajin
(90318,  29, 13257, 0, 0, 97028, 0), -- Demonic Runed Spaulders | Shadow Hunter Vosh'gajin
(90318,  30, 13258, 0, 0, 97028, 0), -- Slaghide Gauntlets | Urok Doomhowl
(90318,  31, 13259, 0, 0, 97028, 0), -- Ribsteel Footguards | Urok Doomhowl
(90318,  32, 13261, 0, 0, 97028, 0), -- Globe of D'sak | Spirestone Lord Magus
(90318,  33, 13282, 0, 0, 97028, 0), -- Ogreseer Tower Boots | Spirestone Lord Magus
(90318,  34, 13283, 0, 0, 97028, 0), -- Magus Ring | Spirestone Lord Magus
(90318,  35, 13284, 0, 0, 97028, 0), -- Swiftdart Battleboots | Spirestone Battle Lord
(90318,  36, 16670, 0, 0, 97028, 0), -- Boots of Elements | Highlord Omokk
(90318,  37, 16676, 0, 0, 97028, 0), -- Beaststalker's Gloves | War Master Voone
(90318,  38, 16679, 0, 0, 97028, 0), -- Beaststalker's Mantle | Overlord Wyrmthalak
(90318,  39, 16712, 0, 0, 97028, 0), -- Shadowcraft Gloves | Shadow Hunter Vosh'gajin
(90318,  40, 16715, 0, 0, 97028, 0), -- Wildheart Boots | Mother Smolderweb
(90318,  41, 16718, 0, 0, 97028, 0), -- Wildheart Spaulders | Gizrul the Slavener
(90318,  42, 22231, 0, 0, 97028, 0), -- Kayser's Boots of Precision | War Master Voone
(90318,  43, 22232, 0, 0, 97028, 0), -- Marksman's Girdle | Urok Doomhowl
(90318,  44, 22306, 0, 0, 97028, 0), -- Ironweave Belt | Mor Grayhoof
(90318,  45, 22313, 0, 0, 97028, 0), -- Ironweave Bracers | Halycon
(90318,  46, 22319, 0, 0, 97028, 0), -- Tome of Divine Right | Mor Grayhoof
(90318,  47, 22321, 0, 0, 97028, 0), -- Heart of Wyrmthalak | Overlord Wyrmthalak
(90318,  48, 22325, 0, 0, 97028, 0), -- Belt of the Trickster | Mor Grayhoof
(90318,  49, 22398, 0, 0, 97028, 0), -- Idol of Rejuvenation | Mor Grayhoof

-- Weapons
(90318,  50, 12582, 0, 0, 97028, 0), -- Keris of Zul'Serak | War Master Voone
(90318,  51, 12621, 0, 0, 97028, 0), -- Demonfork | Bannok Grimaxe
(90318,  52, 12651, 0, 0, 97028, 0), -- Blackcrow | Shadow Hunter Vosh'gajin
(90318,  53, 12653, 0, 0, 97028, 0), -- Riphook | Shadow Hunter Vosh'gajin
(90318,  54, 13148, 0, 0, 97028, 0), -- Chillpike | Overlord Wyrmthalak
(90318,  55, 13161, 0, 0, 97028, 0), -- Trindlehaven Staff | Overlord Wyrmthalak
(90318,  56, 13163, 0, 0, 97028, 0), -- Relentless Scythe | Overlord Wyrmthalak
(90318,  57, 13167, 0, 0, 97028, 0), -- Fist of Omokk | Highlord Omokk
(90318,  58, 13175, 0, 0, 97028, 0), -- Voone's Twitchbow | War Master Voone
(90318,  59, 13182, 0, 0, 97028, 0), -- Phase Blade | Burning Felguard
(90318,  60, 13183, 0, 0, 97028, 0), -- Venomspitter | Mother Smolderweb
(90318,  61, 13198, 0, 0, 97028, 0), -- Hurd Smasher | Ghok Bashguud
(90318,  62, 13204, 0, 0, 97028, 0), -- Bashguuder | Ghok Bashguud
(90318,  63, 13218, 0, 0, 97028, 0), -- Fang of the Crystal Spider | Crystal Fang
(90318,  64, 13285, 0, 0, 97028, 0), -- The Blackrock Slicer | Spirestone Battle Lord
(90318,  65, 13286, 0, 0, 97028, 0), -- Rivenspike | Spirestone Butcher
(90318,  66, 22322, 0, 0, 97028, 0), -- The Jaw Breaker | Mor Grayhoof
(90318,  67, 28972, 0, 0, 97028, 0), -- Flightblade Throwing Axe | War Master Voone

-- Extra
(90318,  68, 12835, 0, 0, 97028, 0), -- Plans: Annihilator | Quartermaster Zigris
(90318,  69, 12838, 0, 0, 97028, 0), -- Plans: Arcanite Reaper | Bannok Grimaxe

-- =========================================================
-- UPPER BLACKROCK SPIRE
-- NPC 90319 | Currency 90029 | ExtendedCost 97029 | 78 items
-- https://www.wowhead.com/classic/zone=1583#drops;mode:normal
-- =========================================================

-- Armor
(90319,   0, 12587, 0, 0, 97029, 0), -- Eye of Rend | Warchief Rend Blackhand
(90319,   1, 12588, 0, 0, 97029, 0), -- Bonespike Shoulder | Warchief Rend Blackhand
(90319,   2, 12589, 0, 0, 97029, 0), -- Dustfeather Sash | Solakar Flamewreath
(90319,   3, 12602, 0, 0, 97029, 0), -- Draconian Deflector | General Drakkisath
(90319,   4, 12603, 0, 0, 97029, 0), -- Nightbrace Tunic | Solakar Flamewreath
(90319,   5, 12604, 0, 0, 97029, 0), -- Starfire Tiara | Jed Runewatcher
(90319,   6, 12606, 0, 0, 97029, 0), -- Crystallized Girdle | Solakar Flamewreath
(90319,   7, 12609, 0, 0, 97029, 0), -- Polychromatic Visionwrap | Solakar Flamewreath
(90319,   8, 12905, 0, 0, 97029, 0), -- Wildfire Cape | Pyroguard Emberseer
(90319,   9, 12926, 0, 0, 97029, 0), -- Flaming Band | Pyroguard Emberseer
(90319,  10, 12927, 0, 0, 97029, 0), -- Truestrike Shoulders | Pyroguard Emberseer
(90319,  11, 12929, 0, 0, 97029, 0), -- Emberfury Talisman | Pyroguard Emberseer
(90319,  12, 12930, 0, 0, 97029, 0), -- Briarwood Reed | Jed Runewatcher
(90319,  13, 12935, 0, 0, 97029, 0), -- Warmaster Legguards | Warchief Rend Blackhand
(90319,  14, 12936, 0, 0, 97029, 0), -- Battleborn Armbraces | Warchief Rend Blackhand
(90319,  15, 12952, 0, 0, 97029, 0), -- Gyth's Skull | Gyth
(90319,  16, 12953, 0, 0, 97029, 0), -- Dragoneye Coif | Gyth
(90319,  17, 12960, 0, 0, 97029, 0), -- Tribal War Feathers | Gyth
(90319,  18, 12963, 0, 0, 97029, 0), -- Blademaster Leggings | The Beast
(90319,  19, 12964, 0, 0, 97029, 0), -- Tristam Legguards | The Beast
(90319,  20, 12965, 0, 0, 97029, 0), -- Spiritshroud Leggings | The Beast
(90319,  21, 12966, 0, 0, 97029, 0), -- Blackmist Armguards | The Beast
(90319,  22, 12967, 0, 0, 97029, 0), -- Bloodmoon Cloak | The Beast
(90319,  23, 12968, 0, 0, 97029, 0), -- Frostweaver Cape | The Beast
(90319,  24, 13098, 0, 0, 97029, 0), -- Painweaver Band | General Drakkisath
(90319,  25, 13141, 0, 0, 97029, 0), -- Tooth of Gnarr | General Drakkisath
(90319,  26, 13142, 0, 0, 97029, 0), -- Brigam Girdle | General Drakkisath
(90319,  27, 13498, 0, 0, 97029, 0), -- Handcrafted Mastersmith Leggings | Goraluk Anvilcrack
(90319,  28, 13502, 0, 0, 97029, 0), -- Handcrafted Mastersmith Girdle | Goraluk Anvilcrack
(90319,  29, 16666, 0, 0, 97029, 0), -- Vest of Elements | General Drakkisath
(90319,  30, 16669, 0, 0, 97029, 0), -- Pauldrons of Elements | Gyth
(90319,  31, 16672, 0, 0, 97029, 0), -- Gauntlets of Elements | Pyroguard Emberseer
(90319,  32, 16674, 0, 0, 97029, 0), -- Beaststalker's Tunic | General Drakkisath
(90319,  33, 16688, 0, 0, 97029, 0), -- Magister's Robes | General Drakkisath
(90319,  34, 16690, 0, 0, 97029, 0), -- Devout Robe | General Drakkisath
(90319,  35, 16695, 0, 0, 97029, 0), -- Devout Mantle | Solakar Flamewreath
(90319,  36, 16700, 0, 0, 97029, 0), -- Dreadmist Robe | General Drakkisath
(90319,  37, 16706, 0, 0, 97029, 0), -- Wildheart Vest | General Drakkisath
(90319,  38, 16721, 0, 0, 97029, 0), -- Shadowcraft Tunic | General Drakkisath
(90319,  39, 16726, 0, 0, 97029, 0), -- Lightforge Breastplate | General Drakkisath
(90319,  40, 16729, 0, 0, 97029, 0), -- Lightforge Spaulders | The Beast
(90319,  41, 16730, 0, 0, 97029, 0), -- Breastplate of Valor | General Drakkisath
(90319,  42, 16733, 0, 0, 97029, 0), -- Spaulders of Valor | Warchief Rend Blackhand
(90319,  43, 18047, 0, 0, 97029, 0), -- Flame Walkers | Goraluk Anvilcrack
(90319,  44, 18102, 0, 0, 97029, 0), -- Dragonrider Boots | Warchief Rend Blackhand
(90319,  45, 18103, 0, 0, 97029, 0), -- Band of Rumination | Warchief Rend Blackhand
(90319,  46, 18104, 0, 0, 97029, 0), -- Feralsurge Girdle | Warchief Rend Blackhand
(90319,  47, 22225, 0, 0, 97029, 0), -- Dragonskin Cowl | Gyth
(90319,  48, 22247, 0, 0, 97029, 0), -- Faith Healer's Boots | Warchief Rend Blackhand
(90319,  49, 22253, 0, 0, 97029, 0), -- Tome of the Lost | General Drakkisath
(90319,  50, 22267, 0, 0, 97029, 0), -- Spellweaver's Turban | General Drakkisath
(90319,  51, 22268, 0, 0, 97029, 0), -- Draconic Infused Emblem | General Drakkisath
(90319,  52, 22269, 0, 0, 97029, 0), -- Shadow Prowler's Cloak | General Drakkisath
(90319,  53, 22302, 0, 0, 97029, 0), -- Ironweave Cowl | Lord Valthalak
(90319,  54, 22311, 0, 0, 97029, 0), -- Ironweave Boots | The Beast
(90319,  55, 22336, 0, 0, 97029, 0), -- Draconian Aegis of the Legion | Lord Valthalak
(90319,  56, 22337, 0, 0, 97029, 0), -- Shroud of Domination | Lord Valthalak
(90319,  57, 22339, 0, 0, 97029, 0), -- Rune Band of Wizardry | Lord Valthalak
(90319,  58, 22340, 0, 0, 97029, 0), -- Pendant of Celerity | Lord Valthalak
(90319,  59, 22342, 0, 0, 97029, 0), -- Leggings of Torment | Lord Valthalak
(90319,  60, 22343, 0, 0, 97029, 0), -- Handguards of Savagery | Lord Valthalak

-- Weapons
(90319,  61, 12583, 0, 0, 97029, 0), -- Blackhand Doomsaw | Warchief Rend Blackhand
(90319,  62, 12590, 0, 0, 97029, 0), -- Felstriker | Warchief Rend Blackhand
(90319,  63, 12592, 0, 0, 97029, 0), -- Blackblade of Shahram | General Drakkisath
(90319,  64, 12605, 0, 0, 97029, 0), -- Serpentine Skuller | Jed Runewatcher
(90319,  65, 12709, 0, 0, 97029, 0), -- Finkle's Skinner | The Beast
(90319,  66, 12939, 0, 0, 97029, 0), -- Dal'Rend's Tribal Guardian | Warchief Rend Blackhand
(90319,  67, 12940, 0, 0, 97029, 0), -- Dal'Rend's Sacred Charge | Warchief Rend Blackhand
(90319,  68, 12969, 0, 0, 97029, 0), -- Seeping Willow | The Beast
(90319,  69, 18048, 0, 0, 97029, 0), -- Mastersmith's Hammer | Goraluk Anvilcrack
(90319,  70, 22335, 0, 0, 97029, 0), -- Lord Valthalak's Staff of Command | Lord Valthalak

-- Extra
(90319,  71, 12834, 0, 0, 97029, 0), -- Plans: Arcanite Champion | Goraluk Anvilcrack
(90319,  72, 12837, 0, 0, 97029, 0), -- Plans: Masterwork Stormhammer | Goraluk Anvilcrack
(90319,  73, 13519, 0, 0, 97029, 0), -- Recipe: Flask of the Titans | General Drakkisath
(90319,  74, 13522, 0, 0, 97029, 0), -- Recipe: Flask of Chromatic Resistance | Gyth
(90319,  75, 15730, 0, 0, 97029, 0), -- Pattern: Red Dragonscale Breastplate | General Drakkisath
(90319,  76, 18657, 0, 0, 97029, 0), -- Schematic: Hyper-Radiant Flame Reflector | Solakar Flamewreath
(90319,  77, 24101, 0, 0, 97029, 0), -- Book of Ferocious Bite V | The Beast

-- =========================================================
-- DIRE MAUL - EAST
-- NPC 90320 | Currency 90030 | ExtendedCost 97030 | 32 items
-- https://www.wowhead.com/classic/zone=2557#drops;mode:normal
-- =========================================================

-- Armor
(90320,   0, 18302, 0, 0, 97030, 0), -- Band of Vigor | Lethtendris
(90320,   1, 18305, 0, 0, 97030, 0), -- Breakwater Legguards | Hydrospawn
(90320,   2, 18306, 0, 0, 97030, 0), -- Gloves of Shadowy Mist | Zevrim Thornhoof
(90320,   3, 18307, 0, 0, 97030, 0), -- Riptide Shoes | Hydrospawn
(90320,   4, 18308, 0, 0, 97030, 0), -- Clever Hat | Zevrim Thornhoof
(90320,   5, 18309, 0, 0, 97030, 0), -- Gloves of Restoration | Alzzin the Wildshaper
(90320,   6, 18312, 0, 0, 97030, 0), -- Energized Chestplate | Alzzin the Wildshaper
(90320,   7, 18313, 0, 0, 97030, 0), -- Helm of Awareness | Zevrim Thornhoof
(90320,   8, 18314, 0, 0, 97030, 0), -- Ring of Demonic Guile | Alzzin the Wildshaper
(90320,   9, 18315, 0, 0, 97030, 0), -- Ring of Demonic Potency | Alzzin the Wildshaper
(90320,  10, 18317, 0, 0, 97030, 0), -- Tempest Talisman | Hydrospawn
(90320,  11, 18318, 0, 0, 97030, 0), -- Merciful Greaves | Alzzin the Wildshaper
(90320,  12, 18319, 0, 0, 97030, 0), -- Fervent Helm | Zevrim Thornhoof
(90320,  13, 18322, 0, 0, 97030, 0), -- Waterspout Boots | Hydrospawn
(90320,  14, 18325, 0, 0, 97030, 0), -- Felhide Cap | Lethtendris
(90320,  15, 18326, 0, 0, 97030, 0), -- Razor Gauntlets | Alzzin the Wildshaper
(90320,  16, 18327, 0, 0, 97030, 0), -- Whipvine Cord | Alzzin the Wildshaper
(90320,  17, 18328, 0, 0, 97030, 0), -- Shadewood Cloak | Alzzin the Wildshaper
(90320,  18, 18354, 0, 0, 97030, 0), -- Pimgib's Collar | Pimgib
(90320,  19, 22304, 0, 0, 97030, 0), -- Ironweave Gloves | Isalien
(90320,  20, 22345, 0, 0, 97030, 0), -- Totem of Rebirth | Isalien
(90320,  21, 22401, 0, 0, 97030, 0), -- Libram of Hope | Isalien
(90320,  22, 22472, 0, 0, 97030, 0), -- Boots of Ferocity | Isalien

-- Weapons
(90320,  23, 18301, 0, 0, 97030, 0), -- Lethtendris's Wand | Lethtendris
(90320,  24, 18310, 0, 0, 97030, 0), -- Fiendish Machete | Alzzin the Wildshaper
(90320,  25, 18311, 0, 0, 97030, 0), -- Quel'dorei Channeling Rod | Lethtendris
(90320,  26, 18321, 0, 0, 97030, 0), -- Energetic Rod | Alzzin the Wildshaper
(90320,  27, 18323, 0, 0, 97030, 0), -- Satyr's Bow | Zevrim Thornhoof
(90320,  28, 18324, 0, 0, 97030, 0), -- Waveslicer | Hydrospawn
(90320,  29, 22314, 0, 0, 97030, 0), -- Huntsman's Harpoon | Isalien
(90320,  30, 22315, 0, 0, 97030, 0), -- Hammer of Revitalization | Isalien

-- Extra
(90320,  31, 18267, 0, 0, 97030, 0), -- Recipe: Runn Tum Tuber Surprise | Pusillin

-- =========================================================
-- DIRE MAUL - WEST
-- NPC 90321 | Currency 90031 | ExtendedCost 97031 | 44 items
-- https://www.wowhead.com/classic/zone=2557#drops;mode:normal
-- =========================================================

-- Armor
(90321,   0, 18345, 0, 0, 97031, 0), -- Murmuring Ring | Tsu'zee
(90321,   1, 18346, 0, 0, 97031, 0), -- Threadbare Trousers | Tsu'zee
(90321,   2, 18349, 0, 0, 97031, 0), -- Gauntlets of Accuracy | Illyanna Ravenoak
(90321,   3, 18350, 0, 0, 97031, 0), -- Amplifying Cloak | Magister Kalendris
(90321,   4, 18351, 0, 0, 97031, 0), -- Magically Sealed Bracers | Magister Kalendris
(90321,   5, 18352, 0, 0, 97031, 0), -- Petrified Bark Shield | Tendris Warpwood
(90321,   6, 18370, 0, 0, 97031, 0), -- Vigilance Charm | Immol'thar
(90321,   7, 18371, 0, 0, 97031, 0), -- Mindtap Talisman | Magister Kalendris
(90321,   8, 18373, 0, 0, 97031, 0), -- Chestplate of Tranquility | Prince Tortheldrin
(90321,   9, 18374, 0, 0, 97031, 0), -- Flamescarred Shoulders | Magister Kalendris
(90321,  10, 18375, 0, 0, 97031, 0), -- Bracers of the Eclipse | Prince Tortheldrin
(90321,  11, 18377, 0, 0, 97031, 0), -- Quickdraw Gloves | Immol'thar
(90321,  12, 18378, 0, 0, 97031, 0), -- Silvermoon Leggings | Prince Tortheldrin
(90321,  13, 18379, 0, 0, 97031, 0), -- Odious Greaves | Immol'thar
(90321,  14, 18380, 0, 0, 97031, 0), -- Eldritch Reinforced Legplates | Prince Tortheldrin
(90321,  15, 18381, 0, 0, 97031, 0), -- Evil Eye Pendant | Immol'thar
(90321,  16, 18382, 0, 0, 97031, 0), -- Fluctuating Cloak | Prince Tortheldrin
(90321,  17, 18383, 0, 0, 97031, 0), -- Force Imbued Gauntlets | Illyanna Ravenoak
(90321,  18, 18384, 0, 0, 97031, 0), -- Bile-etched Spaulders | Immol'thar
(90321,  19, 18385, 0, 0, 97031, 0), -- Robe of Everlasting Night | Immol'thar
(90321,  20, 18386, 0, 0, 97031, 0), -- Padre's Trousers | Illyanna Ravenoak
(90321,  21, 18387, 0, 0, 97031, 0), -- Brightspark Gloves | Tsu'zee
(90321,  22, 18389, 0, 0, 97031, 0), -- Cloak of the Cosmos | Immol'thar
(90321,  23, 18390, 0, 0, 97031, 0), -- Tanglemoss Leggings | Tendris Warpwood
(90321,  24, 18391, 0, 0, 97031, 0), -- Eyestalk Cord | Immol'thar
(90321,  25, 18393, 0, 0, 97031, 0), -- Warpwood Binding | Tendris Warpwood
(90321,  26, 18394, 0, 0, 97031, 0), -- Demon Howl Wristguards | Immol'thar
(90321,  27, 18395, 0, 0, 97031, 0), -- Emerald Flame Ring | Prince Tortheldrin
(90321,  28, 18397, 0, 0, 97031, 0), -- Elder Magus Pendant | Magister Kalendris
(90321,  29, 18754, 0, 0, 97031, 0), -- Fel Hardened Bracers | Lord Hel'nurath
(90321,  30, 18756, 0, 0, 97031, 0), -- Dreadguard's Protector | Lord Hel'nurath
(90321,  31, 18757, 0, 0, 97031, 0), -- Diabolic Mantle | Lord Hel'nurath
(90321,  32, 23127, 0, 0, 97031, 0), -- Cloak of Revanchion | Revanchion
(90321,  33, 23128, 0, 0, 97031, 0), -- The Shadow's Grasp | Revanchion
(90321,  34, 23129, 0, 0, 97031, 0), -- Bracers of Mending | Revanchion

-- Weapons
(90321,  35, 18347, 0, 0, 97031, 0), -- Well Balanced Axe | Illyanna Ravenoak
(90321,  36, 18353, 0, 0, 97031, 0), -- Stoneflower Staff | Tendris Warpwood
(90321,  37, 18372, 0, 0, 97031, 0), -- Blade of the New Moon | Immol'thar
(90321,  38, 18376, 0, 0, 97031, 0), -- Timeworn Mace | Prince Tortheldrin
(90321,  39, 18388, 0, 0, 97031, 0), -- Stoneshatter | Prince Tortheldrin
(90321,  40, 18392, 0, 0, 97031, 0), -- Distracting Dagger | Prince Tortheldrin
(90321,  41, 18396, 0, 0, 97031, 0), -- Mind Carver | Prince Tortheldrin
(90321,  42, 18755, 0, 0, 97031, 0), -- Xorothian Firestick | Lord Hel'nurath

-- Extra
(90321,  43, 22309, 0, 0, 97031, 0), -- Pattern: Big Bag of Enchantment | Magister Kalendris

-- =========================================================
-- DIRE MAUL - NORTH
-- NPC 90322 | Currency 90032 | ExtendedCost 97032 | 30 items
-- https://www.wowhead.com/classic/zone=2557#drops;mode:normal
-- =========================================================

-- Armor
(90322,   0, 18425, 0, 0, 97032, 0), -- Kreeg's Mug | Stomper Kreeg
(90322,   1, 18450, 0, 0, 97032, 0), -- Robe of Combustion | Guard Mol'dar / Guard Fengus / Guard Slip'kik
(90322,   2, 18451, 0, 0, 97032, 0), -- Hyena Hide Belt | Guard Mol'dar / Guard Fengus / Guard Slip'kik
(90322,   3, 18458, 0, 0, 97032, 0), -- Modest Armguards | Guard Mol'dar / Guard Fengus / Guard Slip'kik
(90322,   4, 18459, 0, 0, 97032, 0), -- Gallant's Wristguards | Guard Mol'dar / Guard Fengus / Guard Slip'kik
(90322,   5, 18464, 0, 0, 97032, 0), -- Gordok Nose Ring | Guard Mol'dar / Guard Fengus / Guard Slip'kik
(90322,   6, 18485, 0, 0, 97032, 0), -- Observer's Shield | Cho'Rush the Observer
(90322,   7, 18490, 0, 0, 97032, 0), -- Insightful Hood | Cho'Rush the Observer
(90322,   8, 18493, 0, 0, 97032, 0), -- Bulky Iron Spaulders | Guard Mol'dar / Guard Slip'kik
(90322,   9, 18494, 0, 0, 97032, 0), -- Denwatcher's Shoulders | Guard Mol'dar / Guard Slip'kik
(90322,  10, 18496, 0, 0, 97032, 0), -- Heliotrope Cloak | Guard Mol'dar / Guard Slip'kik
(90322,  11, 18497, 0, 0, 97032, 0), -- Sublime Wristguards | Guard Mol'dar / Guard Slip'kik
(90322,  12, 18503, 0, 0, 97032, 0), -- Kromcrush's Chestplate | Captain Kromcrush
(90322,  13, 18505, 0, 0, 97032, 0), -- Mugger's Belt | Captain Kromcrush
(90322,  14, 18507, 0, 0, 97032, 0), -- Boots of the Full Moon | Captain Kromcrush
(90322,  15, 18521, 0, 0, 97032, 0), -- Grimy Metal Boots | King Gordok
(90322,  16, 18522, 0, 0, 97032, 0), -- Band of the Ogre King | King Gordok
(90322,  17, 18523, 0, 0, 97032, 0), -- Brightly Glowing Stone | King Gordok
(90322,  18, 18524, 0, 0, 97032, 0), -- Leggings of Destruction | King Gordok
(90322,  19, 18525, 0, 0, 97032, 0), -- Bracers of Prosperity | King Gordok
(90322,  20, 18526, 0, 0, 97032, 0), -- Crown of the Ogre King | King Gordok
(90322,  21, 18527, 0, 0, 97032, 0), -- Harmonious Gauntlets | King Gordok

-- Weapons
(90322,  22, 18460, 0, 0, 97032, 0), -- Unsophisticated Hand Cannon | Guard Mol'dar / Guard Fengus / Guard Slip'kik
(90322,  23, 18462, 0, 0, 97032, 0), -- Jagged Bone Fist | Guard Mol'dar / Guard Fengus / Guard Slip'kik
(90322,  24, 18463, 0, 0, 97032, 0), -- Ogre Pocket Knife | Guard Mol'dar / Guard Fengus / Guard Slip'kik
(90322,  25, 18483, 0, 0, 97032, 0), -- Mana Channeling Wand | Cho'Rush the Observer
(90322,  26, 18484, 0, 0, 97032, 0), -- Cho'Rush's Blade | Cho'Rush the Observer
(90322,  27, 18498, 0, 0, 97032, 0), -- Hedgecutter | Guard Mol'dar / Guard Slip'kik
(90322,  28, 18502, 0, 0, 97032, 0), -- Monstrous Glaive | Captain Kromcrush
(90322,  29, 18520, 0, 0, 97032, 0), -- Barbarous Blade | King Gordok

-- =========================================================
-- SCHOLOMANCE
-- NPC 90323 | Currency 90033 | ExtendedCost 97033 | 107 items
-- https://www.wowhead.com/classic/zone=2057#drops;mode:normal
-- =========================================================

-- Armor
(90323,   0, 13314, 0, 0, 97033, 0), -- Alanna's Embrace | Ras Frostwhisper
(90323,   1, 13398, 0, 0, 97033, 0), -- Boots of the Shrieker | Darkmaster Gandling
(90323,   2, 13944, 0, 0, 97033, 0), -- Tombstone Breastplate | Darkmaster Gandling
(90323,   3, 13950, 0, 0, 97033, 0), -- Detention Strap | Darkmaster Gandling
(90323,   4, 13951, 0, 0, 97033, 0), -- Vigorsteel Vambraces | Darkmaster Gandling
(90323,   5, 13955, 0, 0, 97033, 0), -- Stoneform Shoulders | Kirtonos the Herald
(90323,   6, 13956, 0, 0, 97033, 0), -- Clutch of Andros | Kirtonos the Herald
(90323,   7, 13957, 0, 0, 97033, 0), -- Gargoyle Slashers | Kirtonos the Herald
(90323,   8, 13960, 0, 0, 97033, 0), -- Heart of the Fiend | Kirtonos the Herald
(90323,   9, 13967, 0, 0, 97033, 0), -- Windreaver Greaves | Kirtonos the Herald
(90323,  10, 13969, 0, 0, 97033, 0), -- Loomguard Armbraces | Kirtonos the Herald
(90323,  11, 14340, 0, 0, 97033, 0), -- Freezing Lich Robes | Ras Frostwhisper
(90323,  12, 14502, 0, 0, 97033, 0), -- Frostbite Girdle | Ras Frostwhisper
(90323,  13, 14503, 0, 0, 97033, 0), -- Death's Clutch | Ras Frostwhisper
(90323,  14, 14522, 0, 0, 97033, 0), -- Maelstrom Leggings | Ras Frostwhisper
(90323,  15, 14525, 0, 0, 97033, 0), -- Boneclenched Gauntlets | Ras Frostwhisper
(90323,  16, 14528, 0, 0, 97033, 0), -- Rattlecage Buckler | Rattlegore
(90323,  17, 14537, 0, 0, 97033, 0), -- Corpselight Greaves | Rattlegore
(90323,  18, 14538, 0, 0, 97033, 0), -- Deadwalker Mantle | Rattlegore
(90323,  19, 14539, 0, 0, 97033, 0), -- Bone Ring Helm | Rattlegore
(90323,  20, 14543, 0, 0, 97033, 0), -- Darkshade Gloves | Jandice Barov
(90323,  21, 14545, 0, 0, 97033, 0), -- Ghostloom Leggings | Jandice Barov
(90323,  22, 14548, 0, 0, 97033, 0), -- Royal Cap Spaulders | Jandice Barov
(90323,  23, 14577, 0, 0, 97033, 0), -- Skullsmoke Pants | Vectus
(90323,  24, 14611, 0, 0, 97033, 0), -- Bloodmail Hauberk | Instructor Malicia / Doctor Theolen Krastinov / Lorekeeper Polkelt / The Ravenian / Lord Alexei Barov / Lady Illucia Barov
(90323,  25, 14612, 0, 0, 97033, 0), -- Bloodmail Legguards | Instructor Malicia / Doctor Theolen Krastinov / Lorekeeper Polkelt / The Ravenian / Lord Alexei Barov / Lady Illucia Barov
(90323,  26, 14614, 0, 0, 97033, 0), -- Bloodmail Belt | Instructor Malicia / Doctor Theolen Krastinov / Lorekeeper Polkelt / The Ravenian / Lord Alexei Barov / Lady Illucia Barov
(90323,  27, 14615, 0, 0, 97033, 0), -- Bloodmail Gauntlets | Instructor Malicia / Doctor Theolen Krastinov / Lorekeeper Polkelt / The Ravenian / Lord Alexei Barov / Lady Illucia Barov
(90323,  28, 14616, 0, 0, 97033, 0), -- Bloodmail Boots | Instructor Malicia / Doctor Theolen Krastinov / Lorekeeper Polkelt / The Ravenian / Lord Alexei Barov / Lady Illucia Barov
(90323,  29, 14617, 0, 0, 97033, 0), -- Sawbones Shirt | Doctor Theolen Krastinov
(90323,  30, 14620, 0, 0, 97033, 0), -- Deathbone Girdle | Instructor Malicia / Doctor Theolen Krastinov / Lorekeeper Polkelt / The Ravenian / Lord Alexei Barov / Lady Illucia Barov
(90323,  31, 14621, 0, 0, 97033, 0), -- Deathbone Sabatons | Instructor Malicia / Doctor Theolen Krastinov / Lorekeeper Polkelt / The Ravenian / Lord Alexei Barov / Lady Illucia Barov
(90323,  32, 14622, 0, 0, 97033, 0), -- Deathbone Gauntlets | Instructor Malicia / Doctor Theolen Krastinov / Lorekeeper Polkelt / The Ravenian / Lord Alexei Barov / Lady Illucia Barov
(90323,  33, 14623, 0, 0, 97033, 0), -- Deathbone Legguards | Instructor Malicia / Doctor Theolen Krastinov / Lorekeeper Polkelt / The Ravenian / Lord Alexei Barov / Lady Illucia Barov
(90323,  34, 14624, 0, 0, 97033, 0), -- Deathbone Chestplate | Instructor Malicia / Doctor Theolen Krastinov / Lorekeeper Polkelt / The Ravenian / Lord Alexei Barov / Lady Illucia Barov
(90323,  35, 14626, 0, 0, 97033, 0), -- Necropile Robe | Instructor Malicia / Doctor Theolen Krastinov / Lorekeeper Polkelt / The Ravenian / Lord Alexei Barov / Lady Illucia Barov
(90323,  36, 14629, 0, 0, 97033, 0), -- Necropile Cuffs | Instructor Malicia / Doctor Theolen Krastinov / Lorekeeper Polkelt / The Ravenian / Lord Alexei Barov / Lady Illucia Barov
(90323,  37, 14631, 0, 0, 97033, 0), -- Necropile Boots | Instructor Malicia / Doctor Theolen Krastinov / Lorekeeper Polkelt / The Ravenian / Lord Alexei Barov / Lady Illucia Barov
(90323,  38, 14632, 0, 0, 97033, 0), -- Necropile Leggings | Instructor Malicia / Doctor Theolen Krastinov / Lorekeeper Polkelt / The Ravenian / Lord Alexei Barov / Lady Illucia Barov
(90323,  39, 14633, 0, 0, 97033, 0), -- Necropile Mantle | Instructor Malicia / Doctor Theolen Krastinov / Lorekeeper Polkelt / The Ravenian / Lord Alexei Barov / Lady Illucia Barov
(90323,  40, 14636, 0, 0, 97033, 0), -- Cadaverous Belt | Instructor Malicia / Doctor Theolen Krastinov / Lorekeeper Polkelt / The Ravenian / Lord Alexei Barov / Lady Illucia Barov
(90323,  41, 14637, 0, 0, 97033, 0), -- Cadaverous Armor | Instructor Malicia / Doctor Theolen Krastinov / Lorekeeper Polkelt / The Ravenian / Lord Alexei Barov / Lady Illucia Barov
(90323,  42, 14638, 0, 0, 97033, 0), -- Cadaverous Leggings | Instructor Malicia / Doctor Theolen Krastinov / Lorekeeper Polkelt / The Ravenian / Lord Alexei Barov / Lady Illucia Barov
(90323,  43, 14640, 0, 0, 97033, 0), -- Cadaverous Gloves | Instructor Malicia / Doctor Theolen Krastinov / Lorekeeper Polkelt / The Ravenian / Lord Alexei Barov / Lady Illucia Barov
(90323,  44, 14641, 0, 0, 97033, 0), -- Cadaverous Walkers | Instructor Malicia / Doctor Theolen Krastinov / Lorekeeper Polkelt / The Ravenian / Lord Alexei Barov / Lady Illucia Barov
(90323,  45, 16667, 0, 0, 97033, 0), -- Coif of Elements | Darkmaster Gandling
(90323,  46, 16677, 0, 0, 97033, 0), -- Beaststalker's Cap | Darkmaster Gandling
(90323,  47, 16684, 0, 0, 97033, 0), -- Magister's Gloves | Doctor Theolen Krastinov
(90323,  48, 16686, 0, 0, 97033, 0), -- Magister's Crown | Darkmaster Gandling
(90323,  49, 16689, 0, 0, 97033, 0), -- Magister's Mantle | Ras Frostwhisper
(90323,  50, 16693, 0, 0, 97033, 0), -- Devout Crown | Darkmaster Gandling
(90323,  51, 16698, 0, 0, 97033, 0), -- Dreadmist Mask | Darkmaster Gandling
(90323,  52, 16701, 0, 0, 97033, 0), -- Dreadmist Mantle | Jandice Barov
(90323,  53, 16705, 0, 0, 97033, 0), -- Dreadmist Wraps | Lorekeeper Polkelt
(90323,  54, 16707, 0, 0, 97033, 0), -- Shadowcraft Cap | Darkmaster Gandling
(90323,  55, 16710, 0, 0, 97033, 0), -- Shadowcraft Bracers | Instructor Malicia
(90323,  56, 16711, 0, 0, 97033, 0), -- Shadowcraft Boots | Rattlegore
(90323,  57, 16716, 0, 0, 97033, 0), -- Wildheart Belt | The Ravenian
(90323,  58, 16720, 0, 0, 97033, 0), -- Wildheart Cowl | Darkmaster Gandling
(90323,  59, 16722, 0, 0, 97033, 0), -- Lightforge Bracers | Lord Alexei Barov
(90323,  60, 16727, 0, 0, 97033, 0), -- Lightforge Helm | Darkmaster Gandling
(90323,  61, 16731, 0, 0, 97033, 0), -- Helm of Valor | Darkmaster Gandling
(90323,  62, 16734, 0, 0, 97033, 0), -- Boots of Valor | Kirtonos the Herald
(90323,  63, 18681, 0, 0, 97033, 0), -- Burial Shawl | Instructor Malicia / Doctor Theolen Krastinov / Lorekeeper Polkelt / The Ravenian / Lord Alexei Barov / Lady Illucia Barov
(90323,  64, 18682, 0, 0, 97033, 0), -- Ghoul Skin Leggings | Instructor Malicia / Doctor Theolen Krastinov / Lorekeeper Polkelt / The Ravenian / Lord Alexei Barov / Lady Illucia Barov
(90323,  65, 18684, 0, 0, 97033, 0), -- Dimly Opalescent Ring | Instructor Malicia / Doctor Theolen Krastinov / Lorekeeper Polkelt / The Ravenian / Lord Alexei Barov / Lady Illucia Barov
(90323,  66, 18686, 0, 0, 97033, 0), -- Bone Golem Shoulders | Rattlegore
(90323,  67, 18689, 0, 0, 97033, 0), -- Phantasmal Cloak | Jandice Barov
(90323,  68, 18690, 0, 0, 97033, 0), -- Wraithplate Leggings | Jandice Barov
(90323,  69, 18691, 0, 0, 97033, 0), -- Dark Advisor's Pendant | Vectus
(90323,  70, 18692, 0, 0, 97033, 0), -- Death Knight Sabatons | Marduk Blackpool
(90323,  71, 18693, 0, 0, 97033, 0), -- Shivery Handwraps | Ras Frostwhisper
(90323,  72, 18694, 0, 0, 97033, 0), -- Shadowy Mail Greaves | Ras Frostwhisper
(90323,  73, 18695, 0, 0, 97033, 0), -- Spellbound Tome | Ras Frostwhisper
(90323,  74, 18696, 0, 0, 97033, 0), -- Intricately Runed Shield | Ras Frostwhisper
(90323,  75, 18760, 0, 0, 97033, 0), -- Necromantic Band | Death Knight Darkreaver
(90323,  76, 22303, 0, 0, 97033, 0), -- Ironweave Pants | Kormok
(90323,  77, 22326, 0, 0, 97033, 0), -- Amalgam's Band | Kormok
(90323,  78, 22331, 0, 0, 97033, 0), -- Band of the Steadfast Hero | Kormok
(90323,  79, 22433, 0, 0, 97033, 0), -- Don Mauricio's Band of Domination | Darkmaster Gandling
(90323,  80, 23139, 0, 0, 97033, 0), -- Lord Blackwood's Buckler | Lord Blackwood
(90323,  81, 23156, 0, 0, 97033, 0), -- Blackwood's Thigh | Lord Blackwood
(90323,  82, 23200, 0, 0, 97033, 0), -- Totem of Sustaining | Instructor Malicia / Doctor Theolen Krastinov / Lorekeeper Polkelt / The Ravenian / Lord Alexei Barov / Lady Illucia Barov
(90323,  83, 23201, 0, 0, 97033, 0), -- Libram of Divinity | Instructor Malicia / Doctor Theolen Krastinov / Lorekeeper Polkelt / The Ravenian / Lord Alexei Barov / Lady Illucia Barov

-- Weapons
(90323,  84, 13937, 0, 0, 97033, 0), -- Headmaster's Charge | Darkmaster Gandling
(90323,  85, 13938, 0, 0, 97033, 0), -- Bonecreeper Stylus | Darkmaster Gandling
(90323,  86, 13952, 0, 0, 97033, 0), -- Iceblade Hacker | Ras Frostwhisper
(90323,  87, 13953, 0, 0, 97033, 0), -- Silent Fang | Darkmaster Gandling
(90323,  88, 13964, 0, 0, 97033, 0), -- Witchblade | Darkmaster Gandling
(90323,  89, 13983, 0, 0, 97033, 0), -- Gravestone War Axe | Kirtonos the Herald
(90323,  90, 14024, 0, 0, 97033, 0), -- Frightalon | Kirtonos the Herald
(90323,  91, 14487, 0, 0, 97033, 0), -- Bonechill Hammer | Ras Frostwhisper
(90323,  92, 14531, 0, 0, 97033, 0), -- Frightskull Shaft | Rattlegore
(90323,  93, 14541, 0, 0, 97033, 0), -- Barovian Family Sword | Jandice Barov
(90323,  94, 14576, 0, 0, 97033, 0), -- Ebon Hilt of Marduk | Marduk Blackpool
(90323,  95, 18680, 0, 0, 97033, 0), -- Ancient Bone Bow | Instructor Malicia / Doctor Theolen Krastinov / Lorekeeper Polkelt / The Ravenian / Lord Alexei Barov / Lady Illucia Barov
(90323,  96, 18683, 0, 0, 97033, 0), -- Hammer of the Vesper | Instructor Malicia / Doctor Theolen Krastinov / Lorekeeper Polkelt / The Ravenian / Lord Alexei Barov / Lady Illucia Barov
(90323,  97, 18758, 0, 0, 97033, 0), -- Specter's Blade | Death Knight Darkreaver
(90323,  98, 18759, 0, 0, 97033, 0), -- Malicious Axe | Death Knight Darkreaver
(90323,  99, 18761, 0, 0, 97033, 0), -- Oblivion's Touch | Death Knight Darkreaver
(90323, 100, 22332, 0, 0, 97033, 0), -- Blade of Necromancy | Kormok
(90323, 101, 22333, 0, 0, 97033, 0), -- Hammer of Divine Might | Kormok
(90323, 102, 22394, 0, 0, 97033, 0), -- Staff of Metanoia | Jandice Barov
(90323, 103, 23132, 0, 0, 97033, 0), -- Lord Blackwood's Blade | Lord Blackwood

-- Extra
(90323, 104, 13501, 0, 0, 97033, 0), -- Recipe: Major Mana Potion | Darkmaster Gandling
(90323, 105, 13521, 0, 0, 97033, 0), -- Recipe: Flask of Supreme Power | Ras Frostwhisper
(90323, 106, 14514, 0, 0, 97033, 0), -- Pattern: Robe of the Void | Darkmaster Gandling

-- =========================================================
-- STRATHOLME - LIVING QUARTER
-- NPC 90324 | Currency 90034 | ExtendedCost 97034 | 62 items
-- https://www.wowhead.com/classic/zone=2017#drops;mode:normal
-- =========================================================

-- Armor
(90324,   0, 12103, 0, 0, 97034, 0), -- Star of Mystaria | Balnazzar
(90324,   1, 13353, 0, 0, 97034, 0), -- Book of the Dead | Balnazzar
(90324,   2, 13358, 0, 0, 97034, 0), -- Wyrmtongue Shoulders | Balnazzar
(90324,   3, 13359, 0, 0, 97034, 0), -- Crown of Tyranny | Balnazzar
(90324,   4, 13369, 0, 0, 97034, 0), -- Fire Striders | Balnazzar
(90324,   5, 13378, 0, 0, 97034, 0), -- Songbird Blouse | Hearthsinger Forresten
(90324,   6, 13379, 0, 0, 97034, 0), -- Piccolo of the Flaming Fire | Hearthsinger Forresten
(90324,   7, 13381, 0, 0, 97034, 0), -- Master Cannoneer Boots | Cannon Master Willey
(90324,   8, 13382, 0, 0, 97034, 0), -- Cannonball Runner | Cannon Master Willey
(90324,   9, 13383, 0, 0, 97034, 0), -- Woollies of the Prancing Minstrel | Hearthsinger Forresten
(90324,  10, 13384, 0, 0, 97034, 0), -- Rainbow Girdle | Hearthsinger Forresten
(90324,  11, 13385, 0, 0, 97034, 0), -- Tome of Knowledge | Archivist Galford
(90324,  12, 13386, 0, 0, 97034, 0), -- Archivist Cape | Archivist Galford
(90324,  13, 13387, 0, 0, 97034, 0), -- Foresight Girdle | Archivist Galford
(90324,  14, 13388, 0, 0, 97034, 0), -- The Postmaster's Tunic | Postmaster Malown
(90324,  15, 13389, 0, 0, 97034, 0), -- The Postmaster's Trousers | Postmaster Malown
(90324,  16, 13390, 0, 0, 97034, 0), -- The Postmaster's Band | Postmaster Malown
(90324,  17, 13391, 0, 0, 97034, 0), -- The Postmaster's Treads | Postmaster Malown
(90324,  18, 13392, 0, 0, 97034, 0), -- The Postmaster's Seal | Postmaster Malown
(90324,  19, 13394, 0, 0, 97034, 0), -- Skul's Cold Embrace | Skul
(90324,  20, 13395, 0, 0, 97034, 0), -- Skul's Fingerbone Claws | Skul
(90324,  21, 13400, 0, 0, 97034, 0), -- Vambraces of the Sadist | Timmy the Cruel
(90324,  22, 13402, 0, 0, 97034, 0), -- Timmy's Galoshes | Timmy the Cruel
(90324,  23, 13403, 0, 0, 97034, 0), -- Grimgore Noose | Timmy the Cruel
(90324,  24, 13404, 0, 0, 97034, 0), -- Mask of the Unforgiven | The Unforgiven
(90324,  25, 13405, 0, 0, 97034, 0), -- Wailing Nightbane Pauldrons | The Unforgiven
(90324,  26, 13409, 0, 0, 97034, 0), -- Tearfall Bracers | The Unforgiven
(90324,  27, 16682, 0, 0, 97034, 0), -- Magister's Boots | Hearthsinger Forresten
(90324,  28, 16692, 0, 0, 97034, 0), -- Devout Gloves | Archivist Galford
(90324,  29, 16708, 0, 0, 97034, 0), -- Shadowcraft Spaulders | Cannon Master Willey
(90324,  30, 16717, 0, 0, 97034, 0), -- Wildheart Gloves | The Unforgiven
(90324,  31, 16724, 0, 0, 97034, 0), -- Lightforge Gauntlets | Timmy the Cruel
(90324,  32, 16725, 0, 0, 97034, 0), -- Lightforge Boots | Balnazzar
(90324,  33, 18716, 0, 0, 97034, 0), -- Ash Covered Boots | Archivist Galford
(90324,  34, 18718, 0, 0, 97034, 0), -- Grand Crusader's Helm | Balnazzar
(90324,  35, 18720, 0, 0, 97034, 0), -- Shroud of the Nathrezim | Balnazzar
(90324,  36, 18721, 0, 0, 97034, 0), -- Barrage Girdle | Cannon Master Willey
(90324,  37, 22301, 0, 0, 97034, 0), -- Ironweave Robe | Sothos and Jarien's Heirlooms
(90324,  38, 22327, 0, 0, 97034, 0), -- Amulet of the Redeemed | Sothos and Jarien's Heirlooms
(90324,  39, 22328, 0, 0, 97034, 0), -- Legplates of Vigilance | Sothos and Jarien's Heirlooms
(90324,  40, 22329, 0, 0, 97034, 0), -- Scepter of Interminable Focus | Sothos and Jarien's Heirlooms
(90324,  41, 22334, 0, 0, 97034, 0), -- Band of Mending | Balnazzar / Sothos and Jarien's Heirlooms
(90324,  42, 22403, 0, 0, 97034, 0), -- Diana's Pearl Necklace | Cannon Master Willey
(90324,  43, 22405, 0, 0, 97034, 0), -- Mantle of the Scarlet Crusade | Cannon Master Willey
(90324,  44, 22407, 0, 0, 97034, 0), -- Helm of the New Moon | Cannon Master Willey
(90324,  45, 23125, 0, 0, 97034, 0), -- Chains of the Lich | Balzaphon
(90324,  46, 23126, 0, 0, 97034, 0), -- Waistband of Balzaphon | Balzaphon

-- Weapons
(90324,  47, 13348, 0, 0, 97034, 0), -- Demonshear | Balnazzar
(90324,  48, 13360, 0, 0, 97034, 0), -- Gift of the Elven Magi | Balnazzar
(90324,  49, 13380, 0, 0, 97034, 0), -- Willey's Portable Howitzer | Cannon Master Willey
(90324,  50, 13393, 0, 0, 97034, 0), -- Malown's Slam | Postmaster Malown
(90324,  51, 13396, 0, 0, 97034, 0), -- Skul's Ghastly Touch | Skul
(90324,  52, 13401, 0, 0, 97034, 0), -- The Cruel Hand of Timmy | Timmy the Cruel
(90324,  53, 13408, 0, 0, 97034, 0), -- Soul Breaker | The Unforgiven
(90324,  54, 18717, 0, 0, 97034, 0), -- Hammer of the Grand Crusader | Balnazzar
(90324,  55, 22404, 0, 0, 97034, 0), -- Willey's Back Scratcher | Cannon Master Willey
(90324,  56, 22406, 0, 0, 97034, 0), -- Redemption | Cannon Master Willey
(90324,  57, 23124, 0, 0, 97034, 0), -- Staff of Balzaphon | Balzaphon

-- Extra
(90324,  58, 12839, 0, 0, 97034, 0), -- Plans: Heartseeker | Cannon Master Willey
(90324,  59, 13520, 0, 0, 97034, 0), -- Recipe: Flask of Distilled Wisdom | Balnazzar
(90324,  60, 14512, 0, 0, 97034, 0), -- Pattern: Truefaith Vestments | Balnazzar
(90324,  61, 22897, 0, 0, 97034, 0), -- Tome of Conjure Food VII | Archivist Galford

-- =========================================================
-- STRATHOLME - UNDEAD QUARTER
-- NPC 90325 | Currency 90035 | ExtendedCost 97035 | 67 items
-- https://www.wowhead.com/classic/zone=2017#drops;mode:normal
-- =========================================================

-- Armor
(90325,   0, 13340, 0, 0, 97035, 0), -- Cape of the Black Baron | Baron Rivendare
(90325,   1, 13344, 0, 0, 97035, 0), -- Dracorian Gauntlets | Baron Rivendare
(90325,   2, 13345, 0, 0, 97035, 0), -- Seal of Rivendare | Baron Rivendare
(90325,   3, 13346, 0, 0, 97035, 0), -- Robes of the Exalted | Baron Rivendare
(90325,   4, 13373, 0, 0, 97035, 0), -- Band of Flesh | Ramstein the Gorger
(90325,   5, 13374, 0, 0, 97035, 0), -- Soulstealer Mantle | Ramstein the Gorger
(90325,   6, 13375, 0, 0, 97035, 0), -- Crest of Retribution | Ramstein the Gorger
(90325,   7, 13376, 0, 0, 97035, 0), -- Royal Tribunal Cloak | Magistrate Barthilas
(90325,   8, 13397, 0, 0, 97035, 0), -- Stoneskin Gargoyle Cape | Stonespine
(90325,   9, 13515, 0, 0, 97035, 0), -- Ramstein's Lightning Bolts | Ramstein the Gorger
(90325,  10, 13524, 0, 0, 97035, 0), -- Skull of Burning Shadows | Maleki the Pallid
(90325,  11, 13525, 0, 0, 97035, 0), -- Darkbind Fingers | Maleki the Pallid
(90325,  12, 13526, 0, 0, 97035, 0), -- Flamescarred Girdle | Maleki the Pallid
(90325,  13, 13527, 0, 0, 97035, 0), -- Lavawalker Greaves | Maleki the Pallid
(90325,  14, 13528, 0, 0, 97035, 0), -- Twilight Void Bracers | Maleki the Pallid
(90325,  15, 13529, 0, 0, 97035, 0), -- Husk of Nerub'enkan | Nerub'enkan
(90325,  16, 13530, 0, 0, 97035, 0), -- Fangdrip Runners | Nerub'enkan
(90325,  17, 13531, 0, 0, 97035, 0), -- Crypt Stalker Leggings | Nerub'enkan
(90325,  18, 13532, 0, 0, 97035, 0), -- Darkspinner Claws | Nerub'enkan
(90325,  19, 13533, 0, 0, 97035, 0), -- Acid-etched Pauldrons | Nerub'enkan
(90325,  20, 13535, 0, 0, 97035, 0), -- Coldtouch Phantom Wraps | Baroness Anastari
(90325,  21, 13537, 0, 0, 97035, 0), -- Chillhide Bracers | Baroness Anastari
(90325,  22, 13538, 0, 0, 97035, 0), -- Windshrieker Pauldrons | Baroness Anastari
(90325,  23, 13539, 0, 0, 97035, 0), -- Banshee's Touch | Baroness Anastari
(90325,  24, 13954, 0, 0, 97035, 0), -- Verdant Footpads | Stonespine
(90325,  25, 16668, 0, 0, 97035, 0), -- Kilt of Elements | Baron Rivendare
(90325,  26, 16675, 0, 0, 97035, 0), -- Beaststalker's Boots | Nerub'enkan
(90325,  27, 16678, 0, 0, 97035, 0), -- Beaststalker's Pants | Baron Rivendare
(90325,  28, 16687, 0, 0, 97035, 0), -- Magister's Leggings | Baron Rivendare
(90325,  29, 16691, 0, 0, 97035, 0), -- Devout Sandals | Maleki the Pallid
(90325,  30, 16694, 0, 0, 97035, 0), -- Devout Skirt | Baron Rivendare
(90325,  31, 16699, 0, 0, 97035, 0), -- Dreadmist Leggings | Baron Rivendare
(90325,  32, 16704, 0, 0, 97035, 0), -- Dreadmist Sandals | Baroness Anastari
(90325,  33, 16709, 0, 0, 97035, 0), -- Shadowcraft Pants | Baron Rivendare
(90325,  34, 16719, 0, 0, 97035, 0), -- Wildheart Kilt | Baron Rivendare
(90325,  35, 16728, 0, 0, 97035, 0), -- Lightforge Legplates | Baron Rivendare
(90325,  36, 16732, 0, 0, 97035, 0), -- Legplates of Valor | Baron Rivendare
(90325,  37, 16737, 0, 0, 97035, 0), -- Gauntlets of Valor | Ramstein the Gorger
(90325,  38, 18722, 0, 0, 97035, 0), -- Death Grips | Magistrate Barthilas
(90325,  39, 18723, 0, 0, 97035, 0), -- Animated Chain Necklace | Ramstein the Gorger
(90325,  40, 18726, 0, 0, 97035, 0), -- Magistrate's Cuffs | Magistrate Barthilas
(90325,  41, 18727, 0, 0, 97035, 0), -- Crimson Felt Hat | Magistrate Barthilas
(90325,  42, 18728, 0, 0, 97035, 0), -- Anastari Heirloom | Baroness Anastari
(90325,  43, 18730, 0, 0, 97035, 0), -- Shadowy Laced Handwraps | Baroness Anastari
(90325,  44, 18734, 0, 0, 97035, 0), -- Pale Moon Cloak | Maleki the Pallid
(90325,  45, 18735, 0, 0, 97035, 0), -- Maleki's Footwraps | Maleki the Pallid
(90325,  46, 18739, 0, 0, 97035, 0), -- Chitinous Plate Legguards | Nerub'enkan
(90325,  47, 18740, 0, 0, 97035, 0), -- Thuzadin Sash | Nerub'enkan
(90325,  48, 22409, 0, 0, 97035, 0), -- Tunic of the Crescent Moon | Baron Rivendare
(90325,  49, 22410, 0, 0, 97035, 0), -- Gauntlets of Deftness | Baron Rivendare
(90325,  50, 22411, 0, 0, 97035, 0), -- Helm of the Executioner | Baron Rivendare
(90325,  51, 22412, 0, 0, 97035, 0), -- Thuzadin Mantle | Baron Rivendare
(90325,  52, 23198, 0, 0, 97035, 0), -- Idol of Brutality | Magistrate Barthilas

-- Weapons
(90325,  53, 13349, 0, 0, 97035, 0), -- Scepter of the Unholy | Baron Rivendare
(90325,  54, 13361, 0, 0, 97035, 0), -- Skullforge Reaver | Baron Rivendare
(90325,  55, 13368, 0, 0, 97035, 0), -- Bonescraper | Baron Rivendare
(90325,  56, 13372, 0, 0, 97035, 0), -- Slavedriver's Cane | Ramstein the Gorger
(90325,  57, 13399, 0, 0, 97035, 0), -- Gargoyle Shredder Talons | Stonespine
(90325,  58, 13505, 0, 0, 97035, 0), -- Runeblade of Baron Rivendare | Baron Rivendare
(90325,  59, 13534, 0, 0, 97035, 0), -- Banshee Finger | Baroness Anastari
(90325,  60, 18725, 0, 0, 97035, 0), -- Peacemaker | Magistrate Barthilas
(90325,  61, 18729, 0, 0, 97035, 0), -- Screeching Bow | Baroness Anastari
(90325,  62, 18737, 0, 0, 97035, 0), -- Bone Slicing Hatchet | Maleki the Pallid
(90325,  63, 18738, 0, 0, 97035, 0), -- Carapace Spine Crossbow | Nerub'enkan
(90325,  64, 22408, 0, 0, 97035, 0), -- Ritssyn's Wand of Bad Mojo | Baron Rivendare

-- Extra
(90325,  65, 12833, 0, 0, 97035, 0), -- Plans: Hammer of the Titans | Maleki the Pallid
(90325,  66, 13335, 0, 0, 97035, 0); -- Deathcharger's Reins | Baron Rivendare

COMMIT;
