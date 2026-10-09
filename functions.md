# Functions

## Hooks

| Script | Hook | What |
|---|---|---|
| `LearnSpellsOnLevelUp` (PlayerScript) | `OnPlayerLogin` | a Witch Doctor (class 13) gets each of the Earth, Fire and Water Totem (5175-5177) it has neither in its bags nor in its bank (`HasItemCount(..., true)`, `AddItem`); with full bags a system line names the totem and the next login tries again. Its wards, effigies and idols carry a `TotemCategory` and fail with cast result 130 without one; no Witch Doctor spell asks for the Air Totem |
| `LearnSpellsOnLevelUp` (PlayerScript) | `OnPlayerFirstLogin` | with `LearnSpells.OnFirstLogin = 1`: `LearnSpellsForNewLevel(player, 1)`. A Shaman (class 7) always gets the totems 5175-5178 (`AddItem`), whatever the key says; a CoA class with a shaman fallback gets none |
| | `OnPlayerLevelChanged(player, oldLevel)` | with `LearnSpells.Enable` on, a level gain up to `LearnSpells.MaxLevel`: `LearnSpellsForNewLevel(player, oldLevel)`. A level loss teaches nothing |
| `LearnSpellsCoAWorld` (WorldScript) | `OnStartup` | checks the CoA table against this server's spell store (see "Startup check") |

## `LearnSpellsForNewLevel(Player*, uint8 fromLevel)`

- A CoA class (`IsAscensionClass`, core `SharedDefines.h`) goes to `LearnSpells::LearnCoAClassSpells(player)` and
  returns: it has no spell family, and `SPELLFAMILY_GENERIC` would be every generic spell of the store.
- A stock class, for every level from `fromLevel` to the current one: `ApplyAdditionalSpells(level, family, player)`,
  then every spell of the store that passes all of:
  - `SpellFamilyName` = the class's family (`GetSpellFamily`, classes 1-9 and 11);
  - not faction-restricted against the player (`SPELL_ATTR7_ALLIANCE_SPECIFIC_SPELL` / `..._HORDE_...`);
  - not a focus-power spell (`POWER_FOCUS`), not in `m_ignoreSpells`, not disabled (`DisableMgr`);
  - `BaseLevel` = this level (a spell `IsSpellValid` refuses skips this test);
  - a `SkillLineAbility` row with `RaceMask 0`, `AcquireMethod 0` that `AbilityFitsPlayer`;
  - its previous rank is held; a talent spell only from rank 2 on (the talent itself is never taught);

  and learns it (`learnSpell`).

`AbilityFitsPlayer(SkillLineAbilityEntry const*, Player const*)` (OI-10) is stock AzerothCore's
`Player::IsSpellFitByClassAndRace` test: the row's `ClassMask`, when set, names the player's class, and
`GetSkillRaceClassInfo(row.SkillLine, race, class)` exists. Without it ten CoA spells that keep a stock spell family
went to every Warrior, Shaman, Druid, Mage or Warlock (Mu'sha's Blessing 800292 to every Warrior at 2).

`m_additionalSpells` (level -> family -> spells, optionally per faction) adds what the sweep cannot find: Parry 3127,
Dual Wield 674, the warlock and paladin mounts, Life Tap and Redemption ranks, the mage teleports and portals per
faction, Bloodlust 2825 / Heroism 32182 at 70, Swift Flight Form 40120 at 71, and others. `m_ignoreSpells` lists the
family spells the sweep must not teach (quest, cosmetic, Dalaran-vendor and otherwise unwanted rows).

## CoA API (`src/LearnSpellsCoA.h`, namespace `LearnSpells`)

| Signature | What |
|---|---|
| `std::span<CoAClassSpell const> CoAClassSpells(uint8 classId)` | the class's rows in learning order; empty for a class without rows |
| `bool IsCoAClassSpellAt(uint8 classId, uint32 spellId, uint8 level)` | whether a row of the class teaches the spell at or below the level |
| `uint32 LearnCoAClassSpells(Player* player)` | teaches every row of the player's class at or below its level that fits its race and whose `RequiredSpellId` it holds; returns the number learned. Nothing for a stock class, with `Enable` off or above `MaxLevel` |

`LearnCoAClassSpells` skips a spell the store lacks, one `SpellMgr::IsSpellValid` refuses (it would be deleted from
every character as a broken spell) and a disabled one. In the world it uses `learnSpell`; for a character being
created (not in the world yet) `addSpell(spell, SPEC_MASK_ALL, true)`, which the login's initial spell list then
carries. One pass learns a whole rank ladder because the rows are in learning order.

Callers in mod-ascension-compat (`AscensionCompat.cpp`): `RestoreLevelSpells` after a talent or specialization
change, at character creation and on the GM repair `.localclassrepair`; its reconcile reads `CoAClassSpells` /
`IsCoAClassSpellAt` to take `CLASS` rows back below their level. A level-up does not go through that module, and the
login teaches nothing by level: a character above a new row's level gets it at its next level change or a repair.

## Startup check (`LearnSpellsCoAWorld::OnStartup`)

One ERROR line (`module` channel) per problem: a class whose rows are not together; a row's spell missing from the
store or not valid ("a created or reagent item is missing"); a `RequiredSpellId` missing from the store. Then the INFO
line `mod-learn-spells: <rows> Chapters-of-Azeroth class spell rows for <classes> classes, <n> problem(s)`. Such a
row is never taught. `LearnCoAClassSpells` logs a DEBUG line per character that learned something.

## Generator (`tools/build_coa_class_spells.py`)

```
build_coa_class_spells.py --coa-clone DIR --pin SHA --compat DIR --dbc-dir DIR --vanity-dbc FILE
                          [--spell-dbc-ids FILE] --out HEADER [--evidence JSON]
```

- Inputs are read, never executed: the CoA clone through `git show <pin>:<path>` (ClassSpells and the Felsworn rifts
  -> `CLASS`; `AscensionSpellProgressionData.h` ranks -> `RANK` / `RANK_ROOT`; CoA's mod-spellbook offer, trainer and
  rank data -> `OFFER`, `TRAINER`, `BOOK_RANK`), mod-ascension-compat's source, the server DBC files.
- Left out: talent-tree spells, Character Advancement entries, TalentReplacements ranks/targets, TaughtAbilities, class
  script replacement targets (mod-ascension-compat's `check_replacement_learns.py --targets`), Ascension vanity items
  (`VanityCollection.dbc`), deprecated spells, and the Book of Artisans (trainer 200001, profession recipes).
- `RaceMask` replays mod-ascension-compat's `CanGrantAscensionRacialSpell` for the playable races. Every copied
  function is pinned in `REPLAYED_RULES` by the SHA-256 of its text without comments and whitespace; the generator
  refuses to run when one changed. Re-check the copy against the module's new code, then record the printed
  fingerprint.
- Output must be byte-reproducible; mod-ascension-compat's `tools/build_class_spellbook_bindings.py` reads the same
  header.

## Characters SQL (OI-10)

`data/sql/db-characters/2026_09_27_02_learnspells_stock_class_coa_spells_out.sql` deletes, for characters of classes
1-11 only, the ten CoA spells a stock class had learned before `AbilityFitsPlayer` existed: their `character_spell`
rows, spell buttons (`character_action` type 0), self-cast auras (plus 92261 / 92262, which Hoarfrost puts on its
caster) and cooldowns. CoA classes keep theirs. Idempotent; the DB updater applies it while
`Updates.EnableDatabases` includes the characters database (2).
