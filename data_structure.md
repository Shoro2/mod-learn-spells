# Data structure

| Path | What |
|---|---|
| `.github/README.md` | the README: upstream text plus the FL sections (the stock sweep's class-mask rule, the 21 CoA classes) |
| `.github/workflows/core-build.yml` | AzerothCore's reusable module build; triggers on pushes to `master` and on pull requests |
| `.github/ISSUE_TEMPLATE/` | upstream bug-report and feature-request forms |
| `conf/mod_learnspells.conf.dist` | the four `LearnSpells.*` keys |
| `src/LS_loader.cpp` | `Addmod_learn_spellsScripts()` -> `AddSC_LearnAllSpells()`, `AddSC_LearnSpellsCoA()` |
| `src/mod_learnspells.cpp` | `LearnSpellsOnLevelUp`: the stock classes' spell-family sweep, the per-level extra spells, the ignore list, the Shaman and Witch Doctor totems; hands a CoA class to `LearnCoAClassSpells` |
| `src/LearnSpellsCoA.h` | the CoA API (`CoASource`, `CoAClassSpell`, `CoAClassSpells`, `IsCoAClassSpellAt`, `LearnCoAClassSpells`) that mod-ascension-compat includes |
| `src/LearnSpellsCoA.cpp` | the API and the startup check `LearnSpellsCoAWorld` |
| `src/LearnSpellsCoAData.h` | **generated** `LearnSpells::CoAData::ClassSpells`; its header names the CoA pin, the inputs and what was left out. Never edit by hand |
| `tools/build_coa_class_spells.py` | the generator of `LearnSpellsCoAData.h` |
| `data/sql/db-characters/2026_09_27_02_learnspells_stock_class_coa_spells_out.sql` | OI-10 cleanup: ten CoA spells (spell rows, action buttons, self-cast auras, cooldowns) out of characters of classes 1-11; idempotent |
| `include.sh` | empty (module convention) |
| `LICENSE.md` | AGPL v3 |

No `.gitignore`: running the generator leaves an untracked `tools/__pycache__/`.

## Tables

No table of its own. Learning goes through the core (`Player::learnSpell` / `addSpell` -> `character_spell`). The
characters SQL touches `character_spell`, `character_action` (type 0), `character_aura` (caster = the character) and
`character_spell_cooldown`, joined to `characters.class` 1-11. Read at runtime: the spell store, `SkillLineAbility`
and `SkillRaceClassInfo` (DBC), `disables`.

## The CoA row (`LearnSpells::CoAClassSpell`)

| Field | Meaning |
|---|---|
| `ClassId` | 12-32; a class's rows stand together (the startup check refuses a split class) |
| `Level` | the level CoA's class trainer sells the spell at |
| `SpellId` | the spell taught |
| `RequiredSpellId` | the rank beneath that the character must hold; 0 = none |
| `RaceMask` | races allowed (mod-ascension-compat's racial rule, replayed by the generator); 0 = every race |
| `Source` | `CLASS` (CoA's ClassSpells and the Felsworn's Horde-capital rifts), `RANK`, `RANK_ROOT`, `OFFER`, `TRAINER`, `BOOK_RANK` |

Rows of a class are in learning order: a row's requirement, when it is a row of the class, comes first.

## Config

Deployed `C:\wowstuff\dcore\configs\modules\mod_learnspells.conf` holds the same values as the `.dist`.

| Key | Value | Read by |
|---|---|---|
| `LearnSpells.Enable` | 1 | the level-up hook and `LearnCoAClassSpells` |
| `LearnSpells.OnFirstLogin` | 0 | `OnPlayerFirstLogin` (teach from level 1 at the first login) |
| `LearnSpells.MaxLevel` | 80 | the level-up hook and `LearnCoAClassSpells` |
| `LearnSpells.Announce` | 1 | nothing: no code reads it (not since the 2026-07-13 import) |
