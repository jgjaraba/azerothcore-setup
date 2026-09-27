# mod-warrior-rework

Small AzerothCore WotLK module for the Local Turtle Warrior rework.

## Implemented feature

### Single-Minded Fury / Furia enfilada

The module expects the custom client/server data already created for:

- `TalentID 3000`
- `SpellID 90000` — the visible one-point talent
- `SpellID 90001` — hidden +20% physical-damage aura

The bonus is active **only** when all of these are true:

1. The player's **active spec** contains talent spell `90000`.
2. Main hand contains a one-handed weapon.
3. Off hand contains a one-handed weapon.

Valid one-handed inventory types are:

- `INVTYPE_WEAPON`
- `INVTYPE_WEAPONMAINHAND`
- `INVTYPE_WEAPONOFFHAND`

This naturally excludes:

- shields / held-in-off-hand items
- two-handed weapons
- ranged weapons
- empty hands

Titan's Grip and Single-Minded Fury may both be learned, but their benefits do
not stack: spell `90001` is never applied while using a two-handed weapon.

## Why the condition is implemented in C++

`Spell.dbc` equipment requirements can describe the properties of an equipped
item, but do not cleanly express the compound requirement:

    main hand = one-handed weapon
    AND
    off hand = one-handed weapon

Keeping that rule in one small function also makes later balancing/rework easy.

## AzerothCore hooks used

The module updates the bonus only when relevant state can change:

- `OnPlayerLogin`
- `OnPlayerEquip`
- `OnPlayerUnequip`
- `OnPlayerLearnTalents`
- `OnPlayerTalentsReset`
- `OnPlayerAfterSpecSlotChanged`
- `OnPlayerForgotSpell`
- `OnPlayerResurrect`

There is no per-tick polling.

## Installation

Copy the directory into:

    <azerothcore>/modules/mod-warrior-rework/

The module relies on the SQL/DBC data already prepared for TalentID 3000 and
SpellIDs 90000/90001. It intentionally does not ship a second copy of that SQL
so that your tracked `azerothcore-setup/data/sql/custom/db_world` remains the
single source of truth.

After adding a new module, re-run your existing CMake configure step, then
rebuild and install AzerothCore.

Typical flow from an existing build directory:

    cmake <the same options/source path you normally use>
    make -j$(nproc)
    make install

Restart `worldserver`.

## Verification

Learn **Single-Minded Fury** normally from the Fury talent tree.

With two one-handed weapons:

    .list auras id 90001

Expected: aura `90001` is present.

Then test:

| State | 90001 |
|---|---|
| Talent + 1H / 1H | present |
| Talent + 1H / shield | absent |
| Talent + 1H / empty offhand | absent |
| Talent + 2H / 2H (Titan's Grip) | absent |
| Talent + 2H / 1H | absent |
| Spec without SMF + 1H / 1H | absent |
| After talent reset | absent |

Also verify that switching back to the SMF spec while 1H/1H is equipped
re-applies `90001`.

## Notes

- The module checks the **actual equipped items**, not transmog appearances.
- It uses `Player::HasTalent(..., GetActiveSpec())`, so inactive dual-spec
  talents cannot activate the bonus.
- Directly using `.learn 90000` is not equivalent to buying the talent because
  the module intentionally checks the talent map rather than merely `HasSpell`.
