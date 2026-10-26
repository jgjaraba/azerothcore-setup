-- Private client-only glue extension. Native API arguments remain picker ordinals.
-- Coordinates below are generated from the pinned Turtle CharacterCreate.lua.
@RACE_COORDINATES@

function NewRaces_SetIcon(texture, fileString)
    local token = strupper(fileString);
    if ( token == "TURTLEHIGHELF" or token == "TURTLEGOBLIN" ) then
        texture:SetTexture("Interface\\Custom\\NewRaces\\RaceIcons");
    elseif ( texture == CharacterCreateRaceIcon ) then
        texture:SetTexture("Interface\\Glues\\CharacterCreate\\UI-CharacterCreate-RacesRound");
    else
        texture:SetTexture("Interface\\Glues\\CharacterCreate\\UI-CharacterCreate-Races");
    end
end

if ( GetLocale() == "esES" or GetLocale() == "esMX" ) then
    RACE_INFO_TURTLEHIGHELF = "Altos elfos de la Alianza.";
    RACE_INFO_TURTLEGOBLIN = "Goblins de la Horda.";
    TURTLEHIGHELF_DISABLED = "Esta raza no está disponible para esta cuenta.";
    TURTLEGOBLIN_DISABLED = "Esta raza no está disponible para esta cuenta.";
else
    RACE_INFO_TURTLEHIGHELF = "High elves of the Alliance.";
    RACE_INFO_TURTLEGOBLIN = "Goblins of the Horde.";
    TURTLEHIGHELF_DISABLED = "This race is not available for this account.";
    TURTLEGOBLIN_DISABLED = "This race is not available for this account.";
end
-- Names come from ChrRaces, classes from native CharBaseInfo validation.
-- No racial ability claims: gameplay support is outside this client payload.
