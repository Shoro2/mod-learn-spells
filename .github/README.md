# ![logo](https://raw.githubusercontent.com/azerothcore/azerothcore.github.io/master/images/logo-github.png) AzerothCore

## mod-learn-spells
### This is a module for [AzerothCore](http://www.azerothcore.org)

- Latest build status with azerothcore:

[![Build Status](https://github.com/azerothcore/mod-learn-spells/workflows/core-build/badge.svg?branch=master&event=push)](https://github.com/azerothcore/mod-learn-spells)

#### Features:

LearnAllSpells teach new spells on level-up, like in Cataclysm and up.

#### Forgotten Land: which spells the stock classes' sweep takes

A stock class learns every spell of its spell family whose base level it reaches and that has a race-free trainer
row in SkillLineAbility (RaceMask 0, AcquireMethod 0) - and only if that row fits the class the way stock AzerothCore
decides it for a trainer (`Player::IsSpellFitByClassAndRace`): the row's class mask, when set, names the class, and
SkillRaceClassInfo gives the row's skill line to the race and class. Without that test ten Chapters-of-Azeroth
spells that keep a stock family (Mu'sha's Blessing, Upheaval, Spiritual Recall, Sundering, Skitterer Form, Melt Lock,
Hourglass of Time, Summoning Obelisk, Blood Covenant, Hoarfrost) went to every Warrior, Shaman, Druid, Mage or
Warlock. `data/sql/db-characters/2026_09_27_02_learnspells_stock_class_coa_spells_out.sql` takes them back from the
characters of the classes 1-11 that learned them before (the spells, their action-bar buttons, the auras cast with
them, their cooldowns); the DB updater applies it only while `Updates.EnableDatabases` includes the characters
database (2).

#### Forgotten Land: the 21 Chapters-of-Azeroth classes

The stock classes learn by sweeping the spell store for their spell family. A Chapters-of-Azeroth class (ids 12-32)
has no family of its own, so it learns from a table instead: `src/LearnSpellsCoAData.h`, what CoA's own class trainer
(its Books of Ascension) sells a character of the class at each level - CoA's class progression spells, the rank
ladders and the trainer-taught spells, 3,656 rows. The trigger is the same level-up (`LearnSpells.Enable`,
`LearnSpells.MaxLevel`); the table is walked up to the level reached, so a character that is already above a row's
level gets it at its next level change. Profession recipes and Ascension's vanity spells are not rows.

This module never removes a spell. The class progression spells - rows of source `CLASS`: CoA's `ClassSpells` and the
Felsworn's Horde-capital rifts, which CoA grants and takes back with them - are taken back below their level by
mod-ascension-compat's reconcile, as CoA does.

- `src/LearnSpellsCoA.h` is the entry point mod-ascension-compat calls (`LearnCoAClassSpells`, `IsCoAClassSpellAt`,
  `CoAClassSpells`): that module keeps the CoA talent system and teaches nothing by level itself; where it takes
  spells away and gives them back (a specialization switch, a talent change, character creation, an explicit repair)
  it asks this module to put the level spells back.
- `tools/build_coa_class_spells.py` regenerates the table from a CoA clone at the pinned commit, mod-ascension-compat's
  data and the server DBCs (usage in the file). Re-run it when the CoA pin, the class data or the spell package
  changes; mod-ascension-compat's `tools/build_class_spellbook_bindings.py` reads the same table. The race masks
  replay mod-ascension-compat's racial rule and its Felsworn rift faction rule (`AscensionFelsworn::CanLearnRift`: a
  rift whose SkillLineAbility row carries a race mask goes to those races only): their tables are read from that
  module's source, and the functions the generator copies are pinned by fingerprint, so the generator refuses to run
  when one of them changed until the copy is re-checked (`REPLAYED_RULES`). A CoA row whose spell the server's
  `Spell.dbc` does not carry is no row; the generator's `--evidence` lists them (`not_in_store`).
- A row whose spell the store cannot validate is skipped and named once at startup (`mod-learn-spells: ... problem(s)`
  in the Server log).

### This module currently requires:

- AzerothCore v1.0.1+

### How to install

1. Simply place the module under the `modules` folder of your AzerothCore source folder.
2. Re-run cmake and launch a clean build of AzerothCore
3. Ready.

### AzerothCore Links:

- GitHub: [Organisation](https://github.com/azerothcore)
- GitHub: [WOTLK](https://github.com/azerothcore/azerothcore-wotlk) Repository
- Website: [AzerothCore](http://azerothcore.org)
- Discord: [AzerothCore](https://discord.com/invite/gkt4y2x)
