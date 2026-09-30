/*
 * Local Turtle - Warrior Rework
 *
 * Single-Minded Fury support for AzerothCore WotLK 3.3.5a.
 *
 * Required custom data:
 *   TalentID 3000
 *   SpellID  90000 - Single-Minded Fury / Furia enfilada (talent marker)
 *   SpellID  90001 - Single-Minded Fury bonus (+20% physical damage)
 *
 * The module deliberately keeps the equipment condition in C++:
 * spell 90001 is active only while the active spec contains talent spell
 * 90000 AND both main hand and off hand contain one-handed weapons.
 */

#include "Item.h"
#include "Player.h"
#include "ScriptMgr.h"

namespace WarriorRework
{
    enum CustomIds : uint32
    {
        TALENT_SINGLE_MINDED_FURY      = 3000,
        SPELL_SINGLE_MINDED_FURY       = 90000,
        SPELL_SINGLE_MINDED_FURY_BONUS = 90001
    };

    bool IsOneHandedWeapon(Item const* item)
    {
        if (!item)
            return false;

        ItemTemplate const* itemTemplate = item->GetTemplate();
        if (!itemTemplate || itemTemplate->Class != ITEM_CLASS_WEAPON)
            return false;

        // These are the one-handed weapon inventory types in WotLK.
        // INVTYPE_WEAPON can be used in either hand.
        // MAINHAND/OFFHAND variants are restricted by the normal core
        // equip rules and are valid here once actually equipped.
        switch (itemTemplate->InventoryType)
        {
            case INVTYPE_WEAPON:
            case INVTYPE_WEAPONMAINHAND:
            case INVTYPE_WEAPONOFFHAND:
                return true;
            default:
                return false;
        }
    }

    bool ShouldHaveSingleMindedFuryBonus(Player const* player)
    {
        if (!player)
            return false;

        // HasTalent() checks the actual talent map for the requested spec,
        // which makes this robust with dual spec.
        if (!player->HasTalent(SPELL_SINGLE_MINDED_FURY, player->GetActiveSpec()))
            return false;

        Item const* mainHand = player->GetItemByPos(
            INVENTORY_SLOT_BAG_0, EQUIPMENT_SLOT_MAINHAND);

        Item const* offHand = player->GetItemByPos(
            INVENTORY_SLOT_BAG_0, EQUIPMENT_SLOT_OFFHAND);

        return IsOneHandedWeapon(mainHand) && IsOneHandedWeapon(offHand);
    }

    void UpdateSingleMindedFuryBonus(Player* player)
    {
        if (!player)
            return;

        bool const shouldHaveBonus = ShouldHaveSingleMindedFuryBonus(player);
        bool const hasBonus = player->HasAura(SPELL_SINGLE_MINDED_FURY_BONUS);

        if (shouldHaveBonus)
        {
            if (!hasBonus)
                player->CastSpell(player, SPELL_SINGLE_MINDED_FURY_BONUS, true);

            return;
        }

        if (hasBonus)
            player->RemoveAurasDueToSpell(SPELL_SINGLE_MINDED_FURY_BONUS);
    }

    void RemoveSingleMindedFuryBonus(Player* player)
    {
        if (player && player->HasAura(SPELL_SINGLE_MINDED_FURY_BONUS))
            player->RemoveAurasDueToSpell(SPELL_SINGLE_MINDED_FURY_BONUS);
    }
}

class mod_warrior_rework_player : public PlayerScript
{
public:
    mod_warrior_rework_player()
        : PlayerScript("mod_warrior_rework_player",
        {
            PLAYERHOOK_ON_LOGIN,
            PLAYERHOOK_ON_EQUIP,
            PLAYERHOOK_ON_UNEQUIP_ITEM,
            PLAYERHOOK_ON_PLAYER_LEARN_TALENTS,
            PLAYERHOOK_ON_TALENTS_RESET,
            PLAYERHOOK_ON_AFTER_SPEC_SLOT_CHANGED,
            PLAYERHOOK_ON_FORGOT_SPELL,
            PLAYERHOOK_ON_PLAYER_RESURRECT
        })
    {
    }

    void OnPlayerLogin(Player* player) override
    {
        WarriorRework::UpdateSingleMindedFuryBonus(player);
    }

    void OnPlayerEquip(Player* player, Item* /*item*/, uint8 /*bag*/, uint8 /*slot*/, bool /*update*/) override
    {
        WarriorRework::UpdateSingleMindedFuryBonus(player);
    }

    void OnPlayerUnequip(Player* player, Item* /*item*/) override
    {
        WarriorRework::UpdateSingleMindedFuryBonus(player);
    }

    void OnPlayerLearnTalents(Player* player, uint32 talentId, uint32 /*talentRank*/, uint32 /*spellId*/) override
    {
        if (talentId == WarriorRework::TALENT_SINGLE_MINDED_FURY)
            WarriorRework::UpdateSingleMindedFuryBonus(player);
    }

    // AzerothCore calls this immediately BEFORE the reset itself, so do not
    // test HasTalent() here; just remove the conditional bonus proactively.
    void OnPlayerTalentsReset(Player* player, bool /*noCost*/) override
    {
        WarriorRework::RemoveSingleMindedFuryBonus(player);
    }

    // Called after the dual-spec switch has completed.
    void OnPlayerAfterSpecSlotChanged(Player* player, uint8 /*newSlot*/) override
    {
        WarriorRework::UpdateSingleMindedFuryBonus(player);
    }

    void OnPlayerForgotSpell(Player* player, uint32 spellId) override
    {
        if (spellId == WarriorRework::SPELL_SINGLE_MINDED_FURY)
            WarriorRework::RemoveSingleMindedFuryBonus(player);
    }

    void OnPlayerResurrect(Player* player, float /*restorePercent*/, bool& /*applySickness*/) override
    {
        WarriorRework::UpdateSingleMindedFuryBonus(player);
    }
};

void Addmod_warrior_reworkScripts()
{
    new mod_warrior_rework_player();
}
