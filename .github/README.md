# ![logo](https://raw.githubusercontent.com/azerothcore/azerothcore.github.io/master/images/logo-github.png) AzerothCore

## mod-learn-spells
### This is a module for [AzerothCore](http://www.azerothcore.org)

- Latest build status with azerothcore:

[![Build Status](https://github.com/azerothcore/mod-learn-spells/workflows/core-build/badge.svg?branch=master&event=push)](https://github.com/azerothcore/mod-learn-spells)

#### Features:

LearnAllSpells teach new spells on level-up, like in Cataclysm and up.

#### Forgotten Land: the 21 Chapters-of-Azeroth classes

The stock classes learn by sweeping the spell store for their spell family. A Chapters-of-Azeroth class (ids 12-32)
has no family of its own, so it learns from a table instead: `src/LearnSpellsCoAData.h`, what CoA's own class trainer
(its Books of Ascension) sells a character of the class at each level - CoA's class progression spells, the rank
ladders and the trainer-taught spells, 3,648 rows. The trigger is the same level-up (`LearnSpells.Enable`,
`LearnSpells.MaxLevel`); the table is walked up to the level reached, so a character that is already above a row's
level gets it at its next level change. Profession recipes and Ascension's vanity spells are not rows.

- `src/LearnSpellsCoA.h` is the entry point mod-ascension-compat calls (`LearnCoAClassSpells`, `IsCoAClassSpellAt`,
  `CoAClassSpells`): that module keeps the CoA talent system and teaches nothing by level itself; where it takes
  spells away and gives them back (a specialization switch, a talent change, character creation, an explicit repair)
  it asks this module to put the level spells back.
- `tools/build_coa_class_spells.py` regenerates the table from a CoA clone at the pinned commit, mod-ascension-compat's
  data and the server DBCs (usage in the file). Re-run it when the CoA pin, the class data or the spell package
  changes; mod-ascension-compat's `tools/build_class_spellbook_bindings.py` reads the same table.
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
