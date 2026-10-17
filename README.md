# mod-learn-spells

Teaches class spells on level-up for an [AzerothCore](https://www.azerothcore.org/) **WoW 3.3.5a (WotLK)** server, so no class trainer visit is needed. Based on AzerothCore's `mod-learn-spells`, extended for the Forgotten Land server project.

## Features

- **Stock classes (1-11)**: on every level gained, the player learns each spell of its spell family whose base level it reaches, provided the spell has a race-free trainer row in `SkillLineAbility` that fits the class (the same class-mask and `SkillRaceClassInfo` test AzerothCore applies to a trainer). A small table adds spells the sweep cannot find (Parry, Dual Wield, mounts, mage teleports and portals per faction, Bloodlust/Heroism, Swift Flight Form, ...), and an ignore list holds back quest, cosmetic and vendor spells.
- **Chapters-of-Azeroth classes (ids 12-32)**: these classes have no spell family, so they learn from a generated table (`src/LearnSpellsCoAData.h`, about 3,650 rows): what the CoA class trainer would sell the class at each level, including rank ladders. The same level-up trigger applies; a character above a row's level gets it at its next level change. At startup the table is checked against the server's spell store and rows the store cannot validate are skipped and logged once.
- A Shaman gets the four starter totems (items 5175-5178) on first login; a Witch Doctor (class 13) gets the Earth, Fire and Water Totem at login if it holds none.
- `src/LearnSpellsCoA.h` exposes a small API (`LearnCoAClassSpells`, `IsCoAClassSpellAt`, `CoAClassSpells`) for other modules that need to restore a CoA class's level spells.
- The module never removes spells it taught.

## Requirements

- AzerothCore WotLK, **the [Shoro2/azerothcore-wotlk](https://github.com/Shoro2/azerothcore-wotlk) fork**. The code uses `IsAscensionClass` and the Chapters-of-Azeroth class ids 12-32 from the fork's core headers, which upstream AzerothCore does not have; it does not build against upstream. Without CoA classes in the core the table part has nothing to do, so for a plain AzerothCore server use the upstream `azerothcore/mod-learn-spells` instead.
- The Chapters-of-Azeroth class module (mod-ascension-compat) calls this module's API; the two are built together.

## Installation

1. Clone the module into the `modules/` directory of the server source:
   ```bash
   cd azerothcore-wotlk/modules
   git clone https://github.com/Shoro2/mod-learn-spells.git
   ```
2. Re-run CMake and rebuild the server.
3. SQL: `data/sql/db-characters/2026_09_27_02_learnspells_stock_class_coa_spells_out.sql` removes ten Chapters-of-Azeroth spells that earlier versions taught to the stock classes 1-11 (spells, action-bar buttons, auras and cooldowns). The AzerothCore DB updater applies it on the next start, but only while `Updates.EnableDatabases` includes the characters database (value `2`).
4. Copy `conf/mod_learnspells.conf.dist` to your server's module config folder as `mod_learnspells.conf`.
5. Restart the world server. The startup log prints one line with the number of CoA rows, classes and problems found.

## Configuration

`conf/mod_learnspells.conf.dist`:

- `LearnSpells.Enable` - master toggle (default `1`).
- `LearnSpells.OnFirstLogin` - teach every spell up to level 1 on first login (instant-levelling servers; default `0`).
- `LearnSpells.MaxLevel` - highest level at which spells are taught (default `80`).
- `LearnSpells.Announce` is present in the file but not read by the code.

## Regenerating the CoA table

`tools/build_coa_class_spells.py` regenerates `src/LearnSpellsCoAData.h` from a Chapters-of-Azeroth source checkout, the mod-ascension-compat data and the server DBCs (usage in the script's docstring). Do not edit the header by hand.

## Credits

Based on [azerothcore/mod-learn-spells](https://github.com/azerothcore/mod-learn-spells), which teaches new spells on level-up as Cataclysm and later do. See also the [AzerothCore](https://github.com/azerothcore) organisation, the [WotLK core](https://github.com/azerothcore/azerothcore-wotlk) repository and the [AzerothCore website](https://www.azerothcore.org/).

## License

GNU AGPL v3 (see `LICENSE.md`).
