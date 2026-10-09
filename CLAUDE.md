# mod-learn-spells

Teaches spells on level-up, so no class trainer is needed. The stock classes learn the trainer spells of their
spell family at the level they reach; the 21 Conquest of Azeroth (CoA) classes (ids 12-32) learn what CoA's own class
trainer would sell them, from a generated table. FL's copy of AzerothCore's module, and since 2026-09-27 the only
place the CoA classes' level spells come from (operator: "das soll alles über das autolearn modul laufen").
Full description: [.github/README.md](.github/README.md) (this repo keeps its README under `.github/`).

## Ids and tables

| What | Id / name |
|---|---|
| Scripts | `LearnSpellsOnLevelUp` (PlayerScript: first login, level change), `LearnSpellsCoAWorld` (WorldScript: startup check); loader `Addmod_learn_spellsScripts` |
| Classes | stock 1-11 (spell-family sweep); CoA 12-32 (`IsAscensionClass`), rows in `src/LearnSpellsCoAData.h` |
| API for mod-ascension-compat | `src/LearnSpellsCoA.h`, namespace `LearnSpells`: `LearnCoAClassSpells`, `IsCoAClassSpellAt`, `CoAClassSpells` |
| Starting totems | items 5175-5178 to a Shaman (class 7) on first login; the Earth, Fire and Water Totem (5175-5177) to a Witch Doctor (class 13) at every login, each one it has neither in its bags nor in its bank (operator 2026-10-10) |
| Characters SQL | `2026_09_27_02_learnspells_stock_class_coa_spells_out.sql`: CoA spells 800292, 984202, 583092, 760121, 800911, 804662, 1200006, 1200011, 1200012, 92263 (auras also 92261, 92262) out of classes 1-11 |
| Tables | none of its own; teaches through the core (`character_spell`); the SQL above deletes from `character_spell`, `character_action`, `character_aura`, `character_spell_cooldown` |
| Config | `LearnSpells.Enable`, `LearnSpells.OnFirstLogin`, `LearnSpells.MaxLevel`; `LearnSpells.Announce` exists but nothing reads it |
| Startup line | `mod-learn-spells: <rows> Chapters-of-Azeroth class spell rows for <classes> classes, <n> problem(s)` |

## Status and progress

- Where it runs: workbench, built from `azerothcore-wotlk/modules/mod-learn-spells` (`main`); its 2026-10-09 boot
  reports the CoA table with 0 problems. Host: since the joint window MIG-051 (2026-10-03) with MIG-038 (OI-9/OI-10:
  the CoA table, the class-mask rule, the characters SQL) and MIG-046 (round 3's regenerated table); before it the
  host ran the initial import. Players: every class learns its spells on level-up; a new CoA character gets its
  level-1 rows at creation (mod-ascension-compat asks this module).
- Evidence: **T2** for the OI-9/OI-10 behaviour - the operator's round-7 check B on the workbench passed 2026-10-01
  ("Ranger levelup", "Warrior Battle Shout"; vault `coa-classes/program-records/progress.md`); MIG-051's host check A1
  (a CoA class created, a level-1 cast) passed 2026-10-03 ("coa klappt alles"). Round 3's regenerated table: T1 (build, boot, byte-reproducible generator,
  stock classes unchanged; `cu3-wp6-report.md`), live on the host since MIG-051.
- Done:
  - CoA classes never reach the stock sweep (M5): family 0 would be every generic spell of the store.
  - CoA classes learn from the generated table at level-up (OI-9); stock classes take a spell only from a
    `SkillLineAbility` row that fits the class (OI-10), and the ten CoA spells they had learned were removed.
  - The generator replays mod-ascension-compat's racial rule from that module's source, with the copied functions
    pinned by fingerprint; the Felsworn's Horde-capital rifts are CLASS rows, taken back on a level drop (round 3).

## Next steps

1. CoA catch-up round 4 (running, thread "CoA-Fork syncen"): WP-6 re-checked the two refused rule copies and
   regenerated the table on branch `claude/coa-round4-ad93e862`, not on `main` yet; merge after the round's T1, host
   through the reserved MIG-105..110 in HOST11 (vault `cu4-plan-report-20261009.md` §4.6/§6.2, FL/15 §4).
2. Felsworn capital rifts are not faction-gated (queue): needs CoA's race-masked `SkillLineAbility` rows 23482-23487
   on server and client, or a race mask in this table; round 4 gates only Theramore and Stonard.
3. Shieldgore character cleanup (queue proposal, the operator decides).
4. Witch Doctor totems at login (operator 2026-10-10, "ja"): built and bot-tested (mod-woodworking
   `tests/coa_witchdoctor_totems.tbs`) after HOST11, then on `main`; host through MIG-117. The other
   shaman-fallback classes (16, 29, 32) learn no spell that needs a totem.
4. Every later CoA pin: regenerate; the generator refuses when a copied rule changed (re-check, record the new
   fingerprint). New CoA bugs are only noted in the queue; fixes come from CoA upstream through pin rounds
   (operator 2026-10-08).

Open points in full: [todo.md](todo.md).

## Working here

- Branch `claude/<topic>-<sessionId>`, merge into `main` and push (project rule: no pull requests).
- Never edit `src/LearnSpellsCoAData.h` by hand: regenerate with `tools/build_coa_class_spells.py` (usage in its
  docstring), prove it byte-reproducible and the stock classes unchanged. mod-ascension-compat includes
  `LearnSpellsCoA.h` and its `tools/build_class_spellbook_bindings.py` reads the table: change, build and deploy both
  together.
- Build `C:\wowstuff\dcore_bin` (a new source file needs `cmake` first); restart only via the workspace's
  `scripts\worldserver_restart.ps1` (vault `13-bug-report-playbook.md` §3). The characters SQL applies only while
  `Updates.EnableDatabases` includes 2.
- Bot scenarios for this module live in mod-woodworking `tests/` (`coa_stock_warrior`, `coa_pyromancer_seal`,
  `coa_felsworn_rifts`, `coa_knight_shieldgore`); TBOT accounts only.
- Host-relevant change: MIG entry in share-public `docs/World of Warcraft/forgotten-land/15-host-migration-log.md`.
- Vault (`share-public/docs/World of Warcraft/`): `12-server-todo.md`, `coa-classes/00-INDEX.md`,
  `coa-classes/05-program-21-classes-on-dcore.md`, `coa-classes/08-upstream-sync-20261009.md`,
  `coa-classes/program-records/oi9-report.md`, `oi10-report.md`, `cu3-wp6-report.md`, `cu4-plan-report-20261009.md`.
- Doc set: INDEX.md, CLAUDE.md, data_structure.md, functions.md, log.md (newest first), todo.md.
