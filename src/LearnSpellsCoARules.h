/*
 * Forgotten Land: the rules LearnCoAClassSpells applies on top of the generated rows (LearnSpellsCoAData.h). Kept free
 * of core headers apart from LearnSpellsCoA.h's own types, so tools/test_echo_exclusion.cpp can compile and run them
 * against the real data without a worldserver.
 */
#ifndef MOD_LEARN_SPELLS_COA_RULES_H
#define MOD_LEARN_SPELLS_COA_RULES_H

#include "LearnSpellsCoA.h"

#include <cstddef>
#include <span>

namespace LearnSpells
{
// Pyromancer: Explode (the root of its rank ladder) and Echo of Nozdormu, the talent aura that replaces every Explode
// rank with an Echo rank on the bars and in the book (mod-ascension-compat AscensionPyromancer.cpp, Refresh).
inline constexpr uint32 PyromancerExplode = 800792;
inline constexpr uint32 PyromancerEchoOfNozdormu = 520937;

// Whether `row` is a rank above `root` of its class's ladder: the chain of RequiredSpellId, followed through the rows
// of the class, leads back to `root`. The rank ladders of the generated rows hang on each other this way (every rank
// requires the one beneath), so this finds exactly the Ranks rows CoA lists with `root` as FirstSpellId.
inline bool IsRankAbove(std::span<CoAClassSpell const> rows, CoAClassSpell const& row, uint32 root)
{
    uint32 required = row.RequiredSpellId;
    for (std::size_t steps = 0; required && steps <= rows.size(); ++steps)
    {
        if (required == root)
            return true;

        CoAClassSpell const* below = nullptr;
        for (CoAClassSpell const& candidate : rows)
            if (candidate.SpellId == required)
            {
                below = &candidate;
                break;
            }
        if (!below)
            return false;
        required = below->RequiredSpellId;
    }
    return false;
}

// CoA c0eec7b9 (#7120): while Echo of Nozdormu replaces Explode, CoA's automatic rank pass skips every Explode rank -
// a rank the Pyromancer never casts, and one the client would list beside the Echo that stands in its place. The rank
// is taught again by the next pass once the aura is gone (a talent change asks LearnCoAClassSpells right after it
// removes the talent's spells). Explode itself, rank 1, is a class spell and is not part of the pass.
inline bool IsExplodeRankHeldBack(std::span<CoAClassSpell const> rows, CoAClassSpell const& row, bool echoActive)
{
    return echoActive && IsRankAbove(rows, row, PyromancerExplode);
}
}

#endif
