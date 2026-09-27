/*
 * Forgotten Land: the level-based spells of the 21 Chapters-of-Azeroth classes (ids 12-32) - see LearnSpellsCoA.h.
 */
#include "LearnSpellsCoA.h"
#include "LearnSpellsCoAData.h"

#include "Config.h"
#include "DisableMgr.h"
#include "Log.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "SharedDefines.h"
#include "SpellInfo.h"
#include "SpellMgr.h"

#include <array>
#include <unordered_set>

namespace LearnSpells
{
namespace
{
struct ClassRows
{
    std::size_t Begin = 0;
    std::size_t End = 0;
};

// The data file keeps each class's rows together; the startup check refuses a class that appears twice.
std::array<ClassRows, 256> const& Rows()
{
    static std::array<ClassRows, 256> const rows = []
    {
        std::array<ClassRows, 256> result{};
        auto const& table = CoAData::ClassSpells;
        for (std::size_t begin = 0; begin < table.size();)
        {
            std::size_t end = begin;
            while (end < table.size() && table[end].ClassId == table[begin].ClassId)
                ++end;
            if (!result[table[begin].ClassId].End)
                result[table[begin].ClassId] = { begin, end };
            begin = end;
        }
        return result;
    }();
    return rows;
}

bool FitsRace(CoAClassSpell const& row, Player const* player)
{
    return !row.RaceMask || (row.RaceMask & player->getRaceMask());
}
}

std::span<CoAClassSpell const> CoAClassSpells(uint8 classId)
{
    ClassRows const& rows = Rows()[classId];
    return { CoAData::ClassSpells.data() + rows.Begin, rows.End - rows.Begin };
}

bool IsCoAClassSpellAt(uint8 classId, uint32 spellId, uint8 level)
{
    for (CoAClassSpell const& row : CoAClassSpells(classId))
        if (row.SpellId == spellId && row.Level <= level)
            return true;
    return false;
}

uint32 LearnCoAClassSpells(Player* player)
{
    if (!player || !IsAscensionClass(player->getClass()) ||
        !sConfigMgr->GetOption<bool>("LearnSpells.Enable", true) ||
        player->GetLevel() > sConfigMgr->GetOption<uint8>("LearnSpells.MaxLevel", 80))
        return 0;

    uint8 const level = player->GetLevel();
    uint32 learned = 0;
    // Rows come in learning order, so a ladder is learned bottom-up in this one pass: a rank's requirement, when it
    // is a row of the class, was learned just before it.
    for (CoAClassSpell const& row : CoAClassSpells(player->getClass()))
    {
        if (row.Level > level || !FitsRace(row, player) || player->HasSpell(row.SpellId) ||
            (row.RequiredSpellId && !player->HasSpell(row.RequiredSpellId)))
            continue;

        // A spell the store cannot validate would be refused as a "Broken spell" and deleted from every character
        // (SpellMgr::CheckSpellValid); a disabled one is skipped, as for a stock class.
        SpellInfo const* spellInfo = sSpellMgr->GetSpellInfo(row.SpellId);
        if (!spellInfo || !sSpellMgr->IsSpellValid(spellInfo) ||
            DisableMgr::IsDisabledFor(DISABLE_TYPE_SPELL, row.SpellId, player))
            continue;

        // A character being created is not in the world yet: add the spell the way Player::LearnCustomSpells adds
        // the creation spells (the login's SMSG_INITIAL_SPELLS lists it); in the world, learn it as the stock sweep does.
        if (player->IsInWorld())
            player->learnSpell(row.SpellId);
        else
            player->addSpell(row.SpellId, SPEC_MASK_ALL, true);
        if (player->HasSpell(row.SpellId))
            ++learned;
    }

    if (learned)
        LOG_DEBUG("module", "mod-learn-spells: taught {} Chapters-of-Azeroth class spell(s) to {} (class {}, level {})",
                  learned, player->GetName(), uint32(player->getClass()), uint32(level));
    return learned;
}

// The data is generated against one server spell store; say at startup whether it still fits this one.
class LearnSpellsCoAWorld : public WorldScript
{
public:
    LearnSpellsCoAWorld() : WorldScript("LearnSpellsCoAWorld", { WORLDHOOK_ON_STARTUP }) { }

    void OnStartup() override
    {
        auto const& table = CoAData::ClassSpells;
        std::unordered_set<uint8> classes;
        uint8 previousClass = 0;
        uint32 problems = 0;
        for (CoAClassSpell const& row : table)
        {
            if (row.ClassId != previousClass && !classes.insert(row.ClassId).second)
            {
                LOG_ERROR("module", "mod-learn-spells: the Chapters-of-Azeroth rows of class {} are not together",
                          uint32(row.ClassId));
                ++problems;
            }
            previousClass = row.ClassId;

            SpellInfo const* spellInfo = sSpellMgr->GetSpellInfo(row.SpellId);
            if (!spellInfo || !sSpellMgr->IsSpellValid(spellInfo))
            {
                LOG_ERROR("module", "mod-learn-spells: Chapters-of-Azeroth class {} level {} spell {} is {} - it is "
                          "not taught", uint32(row.ClassId), uint32(row.Level), row.SpellId,
                          spellInfo ? "not valid (a created or reagent item is missing)" : "not in the spell store");
                ++problems;
            }
            if (row.RequiredSpellId && !sSpellMgr->GetSpellInfo(row.RequiredSpellId))
            {
                LOG_ERROR("module", "mod-learn-spells: Chapters-of-Azeroth class {} spell {} requires spell {}, which is "
                          "not in the spell store", uint32(row.ClassId), row.SpellId, row.RequiredSpellId);
                ++problems;
            }
        }

        LOG_INFO("module", "mod-learn-spells: {} Chapters-of-Azeroth class spell rows for {} classes, {} problem(s)",
                 uint32(table.size()), uint32(classes.size()), problems);
    }
};
}

void AddSC_LearnSpellsCoA()
{
    new LearnSpells::LearnSpellsCoAWorld();
}
