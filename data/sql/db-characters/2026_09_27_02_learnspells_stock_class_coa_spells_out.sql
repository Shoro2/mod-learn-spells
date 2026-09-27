-- The Chapters-of-Azeroth spells the family sweep taught the stock classes, taken back (OI-10).
-- Until src/mod_learnspells.cpp honoured the SkillLineAbility row's class mask (AbilityFitsPlayer), the sweep taught
-- a stock class every spell of its spell family with a race-free trainer row (RaceMask 0, AcquireMethod 0), whoever
-- the row was for. Ten CoA spells keep a stock family while their row names a CoA class, so every character of that
-- stock class learned them on its level-up:
--   Warrior  800292  Mu'sha's Blessing   level  2  (row: Starcaller, skill 92)
--   Shaman   984202  Upheaval            level  2  (row: Chronomancer, skill 26)
--   Shaman   583092  Spiritual Recall    level 30  (row: Witch Doctor, skill 49)
--   Shaman   760121  Sundering           level 34  (row: Chronomancer, skill 373)
--   Druid    800911  Skitterer Form      level 16  (row: Venomancer, skill 104)
--   Mage     804662  Melt Lock           level 11  (row: Pyromancer, skill 85)
--   Warlock  1200006 Hourglass of Time   level 20  (row: Chronomancer, skill 81)
--   Warlock  1200011 Summoning Obelisk   level 20  (row: Cultist, skill 89)
--   Warlock  1200012 Blood Covenant      level 20  (row: Bloodmage, skill 73)
--   Warlock  92263   Hoarfrost           level 30  (row: Ranger, skill 50)
-- A holder's next login would delete nine of them itself, with an error line each (Player::_LoadSpells ->
-- CheckSkillLearnedBySpell: the row's skill line is not one of the class's), and keep Sundering for good (its skill
-- line, Enhancement, is a shaman one). This file removes all ten before that login: the spell rows, the spell
-- buttons of the action bars, the auras the character put on itself with them (Hoarfrost's with the two it puts on
-- its caster, 92261 and 92262) and their cooldowns.
-- Only characters of the stock classes 1-11 are touched; a CoA class (12-32) keeps its own copy of these spells.
-- Measured on a copy of the workbench's acore_characters (2026-09-27): no stock-class character holds one yet.
-- Idempotent: a second run finds nothing to delete.

SET @OI10_STOCK_CLASS_MIN := 1, @OI10_STOCK_CLASS_MAX := 11;

-- character_action (spell buttons)
DELETE t FROM `character_action` t JOIN `characters` c ON c.`guid` = t.`guid` WHERE c.`class` BETWEEN @OI10_STOCK_CLASS_MIN AND @OI10_STOCK_CLASS_MAX AND t.`type` = 0 AND t.`action` IN (800292, 984202, 583092, 760121, 800911, 804662, 1200006, 1200011, 1200012, 92263);
-- character_aura (cast by the character itself)
DELETE t FROM `character_aura` t JOIN `characters` c ON c.`guid` = t.`guid` WHERE c.`class` BETWEEN @OI10_STOCK_CLASS_MIN AND @OI10_STOCK_CLASS_MAX AND t.`casterGuid` = t.`guid` AND t.`spell` IN (800292, 984202, 583092, 760121, 800911, 804662, 1200006, 1200011, 1200012, 92263, 92261, 92262);
-- character_spell_cooldown
DELETE t FROM `character_spell_cooldown` t JOIN `characters` c ON c.`guid` = t.`guid` WHERE c.`class` BETWEEN @OI10_STOCK_CLASS_MIN AND @OI10_STOCK_CLASS_MAX AND t.`spell` IN (800292, 984202, 583092, 760121, 800911, 804662, 1200006, 1200011, 1200012, 92263);
-- character_spell
DELETE t FROM `character_spell` t JOIN `characters` c ON c.`guid` = t.`guid` WHERE c.`class` BETWEEN @OI10_STOCK_CLASS_MIN AND @OI10_STOCK_CLASS_MAX AND t.`spell` IN (800292, 984202, 583092, 760121, 800911, 804662, 1200006, 1200011, 1200012, 92263);
