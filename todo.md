# Todo

- (medium) Known gap of the round-4 table (its branch `log.md`): the Ranger's Waterskin ranks 802810, 802812-802817 are
  not valid on our server (items 10521-10528 missing) and hang on Crude Waterskin 802808, which nothing grants here;
  the startup line will count them as 7 problems. Note it in the queue unless the round closes it.
- (medium) The Felsworn's capital rifts are not faction-gated (queue `12-server-todo.md`): needs CoA's race-masked
  `SkillLineAbility` rows 23482-23487 on server and client, or a race mask in this table.
- (low) Knight of Xoroth Shieldgore cleanup: characters that learned ranks 806869-806874 before round 3 keep them; the
  cleanup SQL is a proposal (`F:\wowstuff\coa-program\cu3\wp6\proposal\`), the operator decides (queue).
- (low) Starting totems 5175-5178 for the shaman-fallback classes 13, 16, 29, 32: a design decision nobody has taken
  (queue); `OnPlayerFirstLogin` tests the real class.
- (low) `LearnSpells.Announce` is in the conf but no code reads it: implement the announce or drop the key.
- (low) `.github/workflows/core-build.yml` runs on pushes to `master`; this repo's branch is `main`, so a push never
  triggers it.
- (low) No `.gitignore`: the generator leaves an untracked `tools/__pycache__/` (seen in the main checkout
  2026-10-09).
