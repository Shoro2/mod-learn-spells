# Log (newest first)

- 2026-10-15 - CoA catch-up round 5 (CU5-WP6) on branch `claude/coa-round5-f111171c` (off `main` `1d426cf`), not yet
  on `main`. Built and installed by the round's install step together with mod-ascension-compat
  `claude/coa-round5-f111171c` (`6caae328`); nothing was built here (a syntax-only `cl /Zs` of `LearnSpellsCoA.cpp`
  against the integration build's include paths passes).
  - `src/LearnSpellsCoAData.h` regenerated at CoA `4670ac251d86` (the generator is unchanged): the same 3,656 rows,
    nothing added, removed or changed, only the `Source:` pin line differs. All nine `REPLAYED_RULES` fingerprints hold
    on `6caae328` (the merge cut `cd0f9b9b`'s spec-loot lines, the only change that would have moved
    `LoadCoATalentData`). The round's two new TaughtAbilities rows - Witch Hunter Saber Slash (Fire) 680230 at 10 (CoA
    `0a34af87`) and Runemaster Branded 707717 at 50 (`f1742262`) - are not trainer rows (Branded is also a tree spell),
    so no row moves; the output is the same with dcore's `Spell.dbc` and with CU5-WP2's staged one (+7 rows).
  - New rule (CoA `c0eec7b9`, #7120): while a Pyromancer holds Echo of Nozdormu (aura 520937), which replaces Explode
    (800792) in the book and on the bars, `LearnCoAClassSpells` teaches no Explode rank 2-9 (502057-502063, 570750). The
    core hands a live replacement on to a new rank server-side, but `learnSpell` still announces the rank to a client
    that lists Echo in that slot, and CoA treats ranks the player never casts as a defect; the rule is upstream's,
    ported as `IsExplodeRankHeldBack` in the new `src/LearnSpellsCoARules.h`. The ranks follow with the next pass once
    the aura is gone (a talent change calls the pass right after removing the talent's spells). Proof offline:
    `tools/test_echo_exclusion.cpp` (10 checks against the real rows, stub `Define.h`), and the rule selects exactly
    CoA's eight Ranks rows with FirstSpellId 800792 and the core's `spell_ranks` chain. Not run in game (todo).
- 2026-10-14 — feat(tools): `build_coa_class_spells.py` knows Forgotten Land's Goblin (9) and Worgen (12) (WP-D of
  `forgotten-land/server/24-worgen-goblin-races.md`, branch `claude/worgoblin-cd9f5812`). A multi-race `RaceMask` that
  holds the donor race (Orc 2 -> Goblin 256, Human 1 -> Worgen 2048) now also holds the new race (`widen_race_mask`);
  race 0 and single-race masks (racials) are untouched. `src/LearnSpellsCoAData.h` regenerated from the same inputs as
  the last regeneration (CoA `fc359be9bf79`, mod-ascension-compat main `295ecd2`, dcore DBCs, VanityCollection, 5,905
  `spell_dbc` ids; the unchanged generator reproduced the committed file byte for byte first): the only changes are
  two entries, Fel Rift: Theramore 535601 (1101 -> 3149) and Fel Rift: Stonard 535602 (690 -> 946). Not built.

- 2026-10-10 — feat: a Witch Doctor gets the Earth, Fire and Water Totem at every login it lacks one
  (`OnPlayerLogin`; operator 2026-10-10 "ja", thread "Hexing Effigy"). Its ten wards, effigies and idols carry a
  `TotemCategory` (Fire 4, Earth 2, Water 5) and failed with cast result 130 for every Witch Doctor, since only a
  Shaman got totems (first login). Existing characters included; bags and bank count (7c1118e). T1 2026-10-10: built
  (only this file and an unchanged `ptr_template.cpp` recompiled), boot errors = the 87 baseline lines, startup line
  "3656 ... rows for 21 classes, 7 problem(s)", bot run 582 PASS 18/0; host MIG-117 in HOST11

- 2026-10-09 — CoA catch-up round 4 (CU4-WP6) on branch `claude/coa-round4-ad93e862`, not yet on `main`. Built and
  installed by the round's install step together with mod-ascension-compat `claude/coa-round4-ad93e862`
  (`c18ae4e74c48`), which includes `LearnSpellsCoA.h`.
  - `tools/build_coa_class_spells.py` re-checked against the merged class module, where it refused on two copied
    rules: `CanGrantAscensionRacialSpell` now asks `AscensionFelsworn::CanLearnRift` (CoA `cf6b1797`: the same per-row
    race-mask test over eight rifts instead of six; the rifts are read from that function, which is pinned as a ninth
    rule), and `LoadCoATalentData` keeps prerequisites but builds the same catalog (new fingerprint only).
    `TalentReplacements` rows may end in `RequiresAura` (CoA `b03b7cfe`, aura windows). The evidence JSON lists the
    CoA rows the server's `Spell.dbc` cannot carry (`not_in_store`).
  - `src/LearnSpellsCoAData.h` regenerated at CoA `fc359be9bf79` with CU4-WP2's staged server `Spell.dbc`
    (`19a9a549`): 3,642 -> 3,656 rows.
    Out: Warbringer ranks 2-6 (Knight of Xoroth), now ranks of the talent 570727 (CoA `132c6eb3`).
    In from CoA's range: Running Wild 800175 at 20 (Bloodmage, CoA `1554e3c2`), Chromatic Shard rank 9 at 60
    (Chronomancer, CoA `09e723bf`), Waterskin ranks 2-8 (Ranger, CoA `4be4259e`).
    In because their spells reached our server `Spell.dbc` (CoA's Books sold them before): Brutal Shout rank 7 at 65
    (Barbarian), Aeroblast ranks 8-10 (Stormbringer) and Sanguinary Offering rank 6 at 72 (Bloodmage) with CU4-WP2's
    package; Deathwind ranks 8-12 (Reaper) with round 3's final package, after round 3's generation.
    Race masks: Fel Rift: Theramore for the Alliance races only, Fel Rift: Stonard for the Horde races only (CoA
    `cf6b1797` reading our SkillLineAbility rows 40204 / 40205). The six capital rifts stay every race's: our server
    has none of CoA's race-masked rows 23482-23487.
  - Known gap: the seven Waterskin rows are not valid on our server yet (their items 10521-10528 are missing) and hang
    on Crude Waterskin 802808, which nothing grants here (CoA grants it through SkillLineAbility 86420); the startup
    line counts them as 7 problems and no Ranger learns them.

- 2026-09-30 feat(data): regenerate the CoA class spells at CoA 10fa1627f63b on the merged class module (04de1e6)
- 2026-09-30 feat(tools): make the Felsworn's Horde-capital rifts CLASS rows, as CoA's class progression treats them (51ade65)
- 2026-09-30 feat(tools): replay the racial rule from mod-ascension-compat's source and pin the copied logic (a6160a8)
- 2026-09-27 fix(data): take the CoA spells the sweep taught back from stock-class characters (a6cc6c8)
- 2026-09-27 fix(learn): take a stock class's spell only from a row that fits the class (308fe64)
- 2026-09-27 feat: teach the 21 CoA classes their level spells on the level-up (5152350)
- 2026-09-27 feat(data): the level spells of the 21 CoA classes as rows (99b4a4a)
- 2026-09-20 style(learn): include SharedDefines.h explicitly (6e1266f)
- 2026-09-20 fix(learn): do not auto-teach the 21 CoA classes (d8cc4ee)
- 2026-07-13 Initial import: mod-learn-spells (58c65da)
