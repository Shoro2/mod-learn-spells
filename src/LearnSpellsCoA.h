/*
 * Forgotten Land: the level-based spells of the 21 Chapters-of-Azeroth classes (ids 12-32).
 *
 * The stock classes learn their spells here on a level-up by sweeping the spell store for their spell family. A CoA
 * class has no family of its own, so it learns from a table instead: LearnSpellsCoAData.h, what CoA's own class trainer
 * (the Books of Ascension) would sell a character of the class at each level - the class progression spells, the
 * rank ladders, and the trainer-taught spells nothing else grants. The trigger is the same level-up the stock classes
 * learn on (LearnSpells.Enable, LearnSpells.MaxLevel); a character that is already above a row's level gets it at its
 * next level change.
 *
 * mod-ascension-compat keeps the CoA talent system (Character Advancement, specializations and their automatic
 * spells) and teaches nothing by level itself. Where it takes spells away and gives them back - a specialization
 * switch, a talent change, character creation, an explicit repair - it asks LearnCoAClassSpells to put the level
 * spells back, and it reads the rows (never a copy of them) to decide what a level still allows.
 */
#ifndef MOD_LEARN_SPELLS_COA_H
#define MOD_LEARN_SPELLS_COA_H

#include "Define.h"

#include <span>

class Player;

namespace LearnSpells
{
// Where a row comes from (see LearnSpellsCoAData.h): CoA's class progression grants (CLASS) and rank ladders (RANK, and
// a ladder's first rank at its BaseLevel, RANK_ROOT), and what CoA's class trainer sold beyond them (OFFER, TRAINER,
// BOOK_RANK). Only CLASS carries a meaning outside documentation: mod-ascension-compat's reconcile takes those away
// again below their level, as it always did.
enum class CoASource : uint8
{
    CLASS,
    RANK,
    RANK_ROOT,
    OFFER,
    TRAINER,
    BOOK_RANK
};

struct CoAClassSpell
{
    uint8 ClassId;
    uint8 Level;               // the level CoA's class trainer sells it at
    uint32 SpellId;
    uint32 RequiredSpellId;    // the rank beneath, which the character must hold; 0 = none
    uint32 RaceMask;           // 0 = every race
    CoASource Source;
};

// The rows of one class, in learning order (a row's RequiredSpellId, when it is a row of the class, comes first);
// empty for a class that has none.
std::span<CoAClassSpell const> CoAClassSpells(uint8 classId);

// Whether a row of the class teaches this spell at or below this level.
bool IsCoAClassSpellAt(uint8 classId, uint32 spellId, uint8 level);

// Teach the player every row of its class at or below its level that fits its race and whose requirement it holds -
// what a level-up does. Returns the number of spells learned. Does nothing for a stock class, and nothing unless
// LearnSpells.Enable is on and the player's level is at most LearnSpells.MaxLevel, as for a stock class's level-up.
uint32 LearnCoAClassSpells(Player* player);
}

#endif
