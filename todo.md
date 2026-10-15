# Todo

- (medium) Explode / Echo of Nozdormu (round 5, CoA `c0eec7b9`): offline-proven only (`tools/test_echo_exclusion.cpp`,
  the real rows). In game: a Pyromancer with Echo (aura 520937) levels up past an Explode rank level (18 / 26 / 36):
  no new Explode rank in the book or on the bars, Echo stays; dropping the Echo talent teaches the missing ranks at
  once. A bot scenario would need the Echo talent on a TBOT Pyromancer.
- (medium) Skinning in the stock sweep (found in round 5, a static model, not run): `dcore\Data\dbc\Spell.dbc` of 2026-10-14 23:05
  (the worgen/goblin script 210) gives the eight Skinning spells (8613, 8617, 8618, 10768, 13697, 32678, 50305, 52158)
  SpellFamilyName 3 (Mage). The sweep reads a stock Mage's family, and Skinning's SkillLineAbility row (line 393) fits every
  class, so a Mage would be taught Skinning at level 0 (60 pairs differ from round 4's install state). Check on a bot Mage;
  the fix belongs to whoever owns script 210 (or the ignore list here).
- (medium) Known gap of the round-4 table (its branch `log.md`): the Ranger's Waterskin ranks 802810, 802812-802817 are
  not valid on our server (items 10521-10528 missing) and hang on Crude Waterskin 802808, which nothing grants here;
  the startup line will count them as 7 problems. Note it in the queue unless the round closes it.
- (medium) The Felsworn's capital rifts are not faction-gated (queue `12-server-todo.md`): needs CoA's race-masked
  `SkillLineAbility` rows 23482-23487 on server and client, or a race mask in this table.
- (low) Knight of Xoroth Shieldgore cleanup: characters that learned ranks 806869-806874 before round 3 keep them; the
  cleanup SQL is a proposal (`F:\wowstuff\coa-program\cu3\wp6\proposal\`), the operator decides (queue).
- (medium) Witch Doctor totems at login: T1 done (bot run 582); host MIG-117 rides HOST11; T2 owed (a Witch Doctor
  logs in on the host and finds the Earth, Fire and Water Totem in its bags).
- (low) `LearnSpells.Announce` is in the conf but no code reads it: implement the announce or drop the key.
- (low) `.github/workflows/core-build.yml` runs on pushes to `master`; this repo's branch is `main`, so a push never
  triggers it.
- (low) No `.gitignore`: the generator leaves an untracked `tools/__pycache__/` (seen in the main checkout
  2026-10-09).
