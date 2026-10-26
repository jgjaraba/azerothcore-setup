-- Execute generated native Lua with a deliberately small mock of the glue API.
-- This tests Lua behavior, not the actual executable's APIs or UI acceptance.
local payload, locale = arg[1], arg[2];
strupper = string.upper;
function GetLocale() return locale end
local function noop() end
local function frame()
    local object = {};
    function object:SetTexture(value) self.texture = value end
    function object:SetTexCoord(...) self.coords = {...} end
    function object:Show() self.visible = true end
    function object:Hide() self.visible = false end
    function object:SetChecked(value) self.checked = value end
    function object:GetChecked() return self.checked end
    function object:SetText(value) self.text = value end
    function object:Enable() self.disabled = false end
    function object:Disable() self.disabled = true end
    function object:SetDesaturated() return true end
    function object:GetNormalTexture() return self end
    return setmetatable(object, {__index=function() return noop end});
end
CharacterCreate = frame();
for _, name in ipairs({"CharacterRace", "CharacterClass", "NameEdit", "RaceLabel", "RaceIcon",
                       "RaceText", "RaceAbilityText", "RaceScrollFrameScrollBar", "ConfigurationBackground"}) do
    _G["CharacterCreate"..name] = frame();
end
CharacterCreateNameEdit = frame();
for i=1,12 do
    local prefix = "CharacterCreateRaceButton"..i;
    _G[prefix] = frame();
    for _, suffix in ipairs({"NormalTexture", "PushedTexture", "Text"}) do _G[prefix..suffix] = frame() end
end
for i=1,10 do
    local prefix = "CharacterCreateClassButton"..i;
    _G[prefix] = frame();
    for _, suffix in ipairs({"NormalTexture", "PushedTexture", "DisableTexture"}) do _G[prefix..suffix] = frame() end
end
local selected, sex, enabled = 1, 2, 1;
local tokens = {"Human", "Dwarf", "NightElf", "Gnome", "Draenei", "TurtleHighElf",
                "Orc", "Scourge", "Tauren", "Troll", "BloodElf", "TurtleGoblin"};
function GetAvailableRaces()
    local values = {};
    for i,token in ipairs(tokens) do
        table.insert(values, "localized-"..token);
        table.insert(values, token);
        table.insert(values, i == 12 and enabled or 1);
    end
    return unpack(values);
end
function GetSelectedSex() return sex end
function GetSelectedRace() return selected end
function GetNameForRace() return "localized-"..tokens[selected], tokens[selected] end
function GetFactionForRace(ordinal)
    assert(ordinal >= 1 and ordinal <= 12, "Faction argument must be picker ordinal");
    local faction = ordinal <= 6 and "Alliance" or "Horde";
    return faction, faction;
end
function GetCreateBackgroundModel() return tokens[selected] end
local path, ambience, lighting;
function SetCharCustomizeBackground(value) path = value end
function SetCharSelectBackground(value) path = value end
function PlayGlueAmbience(value) ambience = value end
function message(value) error(value) end
assert(loadfile(payload.."/Interface/GlueXML/GlueParent.lua"))();
assert(loadfile(payload.."/Interface/GlueXML/CharacterCreate.lua"))();
-- Native GlueStrings is normally loaded by the client before CharacterCreate.
for i,token in ipairs(tokens) do
    if i ~= 6 and i ~= 12 then _G["RACE_INFO_"..strupper(token)] = "Native stock flavor" end
end
-- Keep native SetLighting, and observe its selected race without mocking its body.
local nativeLighting = SetLighting;
function SetLighting(model, race) lighting = race; return nativeLighting(model, race) end
assert(MAX_RACES == 12 and MAX_CLASSES_PER_RACE == 10);
local stock = "Interface\\Glues\\CharacterCreate\\UI-CharacterCreate-Races";
local stockPortrait = "Interface\\Glues\\CharacterCreate\\UI-CharacterCreate-RacesRound";
local custom = "Interface\\Custom\\NewRaces\\RaceIcons";
for _, gender in ipairs({SEX_MALE, SEX_FEMALE}) do
    sex = gender;
    CharacterCreateEnumerateRaces(GetAvailableRaces());
    assert(CharacterCreate.numRaces == 12);
    for i,token in ipairs(tokens) do
        local expected = (i == 6 or i == 12) and custom or stock;
        assert(_G["CharacterCreateRaceButton"..i].visible);
        assert(_G["CharacterCreateRaceButton"..i].name == "localized-"..token);
        for _,suffix in ipairs({"NormalTexture", "PushedTexture"}) do
            assert(_G["CharacterCreateRaceButton"..i..suffix].texture == expected);
        end
    end
    -- Switch custom -> stock repeatedly; the shared portrait must restore its atlas.
    for _,ordinal in ipairs({6, 12, 11, 1, 12, 6, 1}) do
        selected = ordinal;
        SetCharacterRace(selected);
        assert(CharacterCreate.selectedRace == ordinal);
        assert(CharacterCreateRaceIcon.texture == ((ordinal == 6 or ordinal == 12) and custom or stockPortrait));
        if ordinal == 6 or ordinal == 12 then
            local scene = ordinal == 6 and "BloodElf" or "Orc";
            assert(path == "Interface\\Glues\\Models\\UI_"..scene.."\\UI_"..scene..".m2");
            assert(lighting == strupper(scene));
            assert(ambience == GlueAmbienceTracks[strupper(scene)]);
            assert(CharacterCreateRaceText.text:find(ordinal == 6 and
                   (locale == "esES" and "Altos elfos" or "High elves") or
                   (locale == "esES" and "Goblins" or "Goblins")));
            assert(CharacterCreateRaceAbilityText.text == "");
        end
    end
end
enabled = 0;
CharacterCreateEnumerateRaces(GetAvailableRaces());
assert(CharacterCreateRaceButton12.enable == false);
assert(CharacterCreateRaceButton12.tooltip == TURTLEGOBLIN_DISABLED);
-- A shorter dynamic enumeration hides unused slots rather than faking races.
CharacterCreateEnumerateRaces("One", "Human", 1);
for i=2,12 do assert(not _G["CharacterCreateRaceButton"..i].visible) end

local classes = {"WARRIOR", "PALADIN", "HUNTER", "ROGUE", "PRIEST", "DEATHKNIGHT", "SHAMAN", "MAGE", "WARLOCK", "DRUID"};
function GetAvailableClasses()
    local values = {};
    for _, token in ipairs(classes) do
        table.insert(values, token); table.insert(values, token); table.insert(values, 1);
    end
    return unpack(values);
end
-- Mock the parent-owned DBC contract. Native Lua must consult this API and keep
-- the existing custom Undead Paladin combination (Scourge picker ordinal 8).
local pairs = {[6]={[1]=true,[2]=true,[3]=true,[4]=true,[5]=true,[8]=true},
               [12]={[1]=true,[3]=true,[4]=true,[8]=true,[9]=true}, [8]={[2]=true}};
function IsRaceClassValid(raceOrdinal, classOrdinal)
    assert(raceOrdinal <= 12 and classOrdinal <= 10);
    return pairs[raceOrdinal] and pairs[raceOrdinal][classOrdinal] or false;
end
for _,ordinal in ipairs({6,12,8}) do
    CharacterCreate.selectedRace = ordinal;
    CharacterCreateEnumerateClasses(GetAvailableClasses());
    assert(CharacterCreate.numClasses == 10);
    for i=1,10 do
        assert(_G["CharacterCreateClassButton"..i].enable == (pairs[ordinal][i] or false));
    end
end
-- Exercise the original click handler, including native SetSelectedRace ordinal.
function SetSelectedRace(ordinal) assert(ordinal == 6 or ordinal == 12); selected = ordinal end
function GetSelectedClass() return "Warrior", "WARRIOR", 1 end
function SetSelectedSex(value) sex = value end
SetCharacterCreateFacing, PlaySound = noop, noop;
SetCharacterClass, CharacterCreate_UpdateHairCustomization, CharacterChangeFixup = noop, noop, noop;
selected = 1;
CharacterCreateEnumerateRaces(GetAvailableRaces());
for _,ordinal in ipairs({6,12}) do
    local button = _G["CharacterCreateRaceButton"..ordinal]; button:SetChecked(1);
    CharacterRace_OnClick(button, ordinal);
    assert(selected == ordinal);
end
print("PASS mocked native glue: "..locale..", both sexes, 12 triples, ordinal clicks, icons, classes, scenes");
