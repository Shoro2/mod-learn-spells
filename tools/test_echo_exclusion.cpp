// Standalone check of the Explode / Echo of Nozdormu exclusion (CoA c0eec7b9) against the real generated rows.
// No worldserver and no core headers: LearnSpellsCoARules.h and LearnSpellsCoAData.h are compiled with a stub Define.h.
//
//   cl /nologo /std:c++20 /EHsc /W4 /I src /I tools\test_stub tools\test_echo_exclusion.cpp /Fe:test_echo_exclusion.exe
//   test_echo_exclusion.exe            (exit code 0 = every check passed)
#include "LearnSpellsCoARules.h"
#include "LearnSpellsCoAData.h"

#include <algorithm>
#include <cstdio>
#include <iterator>
#include <set>
#include <vector>

using namespace LearnSpells;

namespace
{
int failures = 0;

void Check(bool ok, char const* what)
{
    std::printf("%s  %s\n", ok ? "PASS" : "FAIL", what);
    if (!ok)
        ++failures;
}

std::span<CoAClassSpell const> RowsOf(uint8 classId)
{
    auto const& table = CoAData::ClassSpells;
    std::size_t begin = 0;
    while (begin < table.size() && table[begin].ClassId != classId)
        ++begin;
    std::size_t end = begin;
    while (end < table.size() && table[end].ClassId == classId)
        ++end;
    return { table.data() + begin, end - begin };
}

// The pass of LearnCoAClassSpells without the core: what a character that holds `have` learns at `level`.
std::set<uint32> Pass(std::span<CoAClassSpell const> rows, std::set<uint32> have, uint8 level, bool echo)
{
    std::set<uint32> learned;
    for (CoAClassSpell const& row : rows)
    {
        if (row.Level > level || have.count(row.SpellId) || (row.RequiredSpellId && !have.count(row.RequiredSpellId)) ||
            IsExplodeRankHeldBack(rows, row, echo))
            continue;
        have.insert(row.SpellId);
        learned.insert(row.SpellId);
    }
    return learned;
}
}

int main()
{
    uint32 constexpr ranks[] = { 502057, 502058, 502059, 502060, 502061, 502062, 502063, 570750 };
    auto const pyromancer = RowsOf(24);
    Check(!pyromancer.empty(), "class 24 (Pyromancer) has rows");

    // 1. exactly CoA's eight Explode ranks are held back while Echo stands; none otherwise
    std::set<uint32> held, heldWithoutEcho;
    for (CoAClassSpell const& row : pyromancer)
    {
        if (IsExplodeRankHeldBack(pyromancer, row, true))
            held.insert(row.SpellId);
        if (IsExplodeRankHeldBack(pyromancer, row, false))
            heldWithoutEcho.insert(row.SpellId);
    }
    Check(held == std::set<uint32>(std::begin(ranks), std::end(ranks)), "with Echo: held back = the 8 Explode ranks 2-9");
    Check(heldWithoutEcho.empty(), "without Echo: nothing is held back");
    Check(std::any_of(pyromancer.begin(), pyromancer.end(),
                      [](CoAClassSpell const& r) { return r.SpellId == PyromancerExplode && r.RequiredSpellId == 0; }) &&
              !held.count(PyromancerExplode),
          "Explode rank 1 (800792) is a class spell and is never held back");

    // 2. no other class loses a row
    std::size_t other = 0;
    for (CoAClassSpell const& row : CoAData::ClassSpells)
        if (row.ClassId != 24 && IsExplodeRankHeldBack(RowsOf(row.ClassId), row, true))
            ++other;
    Check(other == 0, "no row of any other class is held back");

    // 3. the pass: a level 30 Pyromancer with Explode ranks 1-3 (levels 1/4/12)
    std::set<uint32> have;
    for (CoAClassSpell const& row : pyromancer)
        if (row.Level <= 12)
            have.insert(row.SpellId);
    auto const withEcho = Pass(pyromancer, have, 30, true);
    auto const withoutEcho = Pass(pyromancer, have, 30, false);
    Check(!withEcho.count(502059) && !withEcho.count(502060), "level 30 with Echo: Explode ranks 4 (18) and 5 (26) are not taught");
    Check(withoutEcho.count(502059) && withoutEcho.count(502060), "level 30 without Echo: Explode ranks 4 and 5 are taught");
    std::set<uint32> expectedGap;
    std::set_difference(withoutEcho.begin(), withoutEcho.end(), withEcho.begin(), withEcho.end(),
                        std::inserter(expectedGap, expectedGap.begin()));
    Check(expectedGap == std::set<uint32>({ 502059, 502060 }), "the Echo pass differs from the plain pass by those two ranks only");
    auto const later = Pass(pyromancer, [&] { auto h = have; h.insert(withEcho.begin(), withEcho.end()); return h; }(), 30, false);
    Check(later.count(502059) && later.count(502060) && later.size() == 2,
          "after Echo is gone the next pass teaches exactly the two held-back ranks");

    // 4. a requirement cycle or a requirement outside the rows ends the walk
    CoAClassSpell cycle[] = { { 24, 1, 1, 2, 0, CoASource::RANK }, { 24, 1, 2, 1, 0, CoASource::RANK },
                              { 24, 1, 3, 99, 0, CoASource::RANK } };
    std::span<CoAClassSpell const> const synthetic(cycle);
    Check(!IsRankAbove(synthetic, cycle[0], PyromancerExplode) && !IsRankAbove(synthetic, cycle[2], PyromancerExplode),
          "a cycle and an unknown requirement end the walk without a match");

    std::printf("%s (%d failure(s))\n", failures ? "FAILED" : "ALL PASSED", failures);
    return failures ? 1 : 0;
}
