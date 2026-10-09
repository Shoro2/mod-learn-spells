#!/usr/bin/env python3
r"""Generate src/LearnSpellsCoAData.h: the level-based spells of the 21 Chapters-of-Azeroth classes (ids 12-32).

What a CoA class learns on a level-up is what CoA's own class trainer - the Books of Ascension, module
mod-spellbook of Chapters of Azeroth - would sell it at that level (spellbook.cpp BuildRows, window view):

  1. the class progression spells, ClassSpells in src/server/coa/AscensionCustomClassData.h, at their level, and the
     Felsworn's Horde-capital rifts, FelswornHordeCapitalRifts in src/server/coa/AscensionCompat.cpp, which CoA's
     SynchronizeProgression grants at their level and takes back below it exactly as it does ClassSpells;
  2. the rank ladders, AscensionProgression::Ranks in AscensionSpellProgressionData.h: a ladder's first rank at its
     Spell.dbc BaseLevel when nothing else grants it, every higher rank at its level and requiring the rank beneath;
  3. SpellbookOfferData, SpellbookTrainerData and SpellbookRankData: the services CoA's captured original trainer
     window sold that the generated class data never resolved (the "trainer-taught" spells), at their level and
     requiring the rank beneath.

A spell the talent trees grant is not a trainer row (SpellbookTreeSpellData, as in the window), and neither is a spell
the Forgotten Land talent system owns: a Character Advancement entry's spell (CharacterAdvancement.dbc read as
mod-ascension-compat's LoadCoATalentData reads it), a TalentReplacements rank or target - a talent's, or an aura
window's (RequiresAura, CoA b03b7cfe) - or a TaughtAbilities spell (mod-ascension-compat's data headers), or a
spell a class script makes a replacement target (resolved by mod-ascension-compat's own gate,
tools/check_replacement_learns.py --targets). A spell that creates an Ascension vanity item (VanityCollection.dbc) or
whose name marks it deprecated is left out too. Nothing of the Book of Artisans (trainer 200001) is read: a spell only
it teaches is a profession recipe. A CoA row whose spell the server's Spell.dbc does not carry is no row (the
evidence JSON lists them as not_in_store): it becomes one when a spell package brings the spell.

RaceMask replays mod-ascension-compat's CanGrantAscensionRacialSpell for every playable race (0 = every race). The
replay reads the rule's data from the module's source - the racial skill lines (AscensionRacialAbilities::Skills),
the class variants outside the DBC masks (ClassVariantsOutsideDbcMask, CoA c9389794) and the Felsworn rifts the
faction rule gates by race (AscensionFelsworn::CanLearnRift, CoA cf6b1797) - with the enum names resolved through
CoA's src/server/shared/SharedDefines.h at the pin and the header's own enums. The faction rule reads the race masks
of the rifts' SkillLineAbility rows, so a rift without a race-masked row on this server is every race's. Its logic
is a copy of the module's functions, and a copy is only right while the module runs the code it copied: every copied
function (REPLAYED_RULES) is pinned by the SHA-256 of its text without comments and whitespace, and the generator
refuses to run when one differs. Re-check the replay against the module's new code, then record the fingerprint the
refusal prints.

Every input is read, never executed: the CoA clone through `git show <pin>:<path>`, the DBC files directly.

usage:
  build_coa_class_spells.py --coa-clone DIR --pin SHA --compat DIR --dbc-dir DIR --vanity-dbc FILE
                            [--spell-dbc-ids FILE] --out HEADER [--evidence JSON]
"""
import argparse
import collections
import hashlib
import json
import os
import re
import struct
import subprocess
import sys

COA_CLASSES = range(12, 33)
PLAYABLE_RACES = (1, 2, 3, 4, 5, 6, 7, 8, 10, 11)
SKILL_LINE_ABILITY_LEARNED_ON_SKILL_LEARN = 2   # DBCEnums.h
SOURCES = ("CLASS", "RANK", "RANK_ROOT", "OFFER", "TRAINER", "BOOK_RANK")
ITEM_EFFECTS = (24, 157, 34, 66)

RACIAL_HEADER = "src/AscensionRacialAbilities.h"
COMPAT_SOURCE = "src/AscensionCompat.cpp"
FELSWORN_SOURCE = "src/AscensionFelsworn.cpp"
# The mod-ascension-compat functions whose logic this generator copies, with the SHA-256 of each one's text (comments
# and whitespace removed) as last checked against the copy: (file, function, fingerprint, where the copy lives).
# Checked against mod-ascension-compat c18ae4e74c48 (CoA fc359be9bf79 merged). There CanGrantAscensionRacialSpell asks
# AscensionFelsworn::CanLearnRift first (CoA cf6b1797): the per-row race-mask test it made inline before, now over
# eight rifts instead of six (Theramore 535601 and Stonard 535602 join the six capitals). LoadCoATalentData now also
# keeps a paid entry's prerequisites and two flags (CoA b8b7252c / d60f0243); the catalog of spells it builds, which
# catalog_spells copies, is unchanged.
REPLAYED_RULES = (
    (RACIAL_HEADER, "GetRace",
     "6bb00b110a7d71c3599d0476c566ae069f81ceabcf0bb3d5872f859fc91afd38", "Racial.race_of"),
    (RACIAL_HEADER, "IsClassVariantOutsideDbcMask",
     "88041417ac791f21027a41aa7c63c7d90c288f3bd94e5830ac15ac9460528ac1", "Racial.variant"),
    (RACIAL_HEADER, "CanLearn",
     "f089d2a8b7bd8b6974e893377407c24ed7f430904181e2b86e91cf61fd94cef4", "Racial.can_learn"),
    (COMPAT_SOURCE, "IsSupersededRacialCopy",
     "6e17d3f9d068adfa89c8b81c8401aafaaea8536dc9a78786f13d5cf9a4aeba40", "Racial.superseded_copy"),
    (COMPAT_SOURCE, "GetAscensionRacialSpells",
     "75f1d432e4c8af933451b27dc0032d8f2f5e69328fb2ef2c46ae996d982f42a2", "Racial.racials (evidence only)"),
    (COMPAT_SOURCE, "CanGrantAscensionRacialSpell",
     "ac721205c3e8d7232a608457c46e0670c1a6757a7f83ee94fed2ab28141c99d7", "Racial.can_grant"),
    (FELSWORN_SOURCE, "CanLearnRift",
     "53dbf11650222debea18c058aea3d62bc992c827ccfdfa05ccca4abe29dcf73e",
     "Racial.can_grant (the rift faction rule) and read_racial_rules (its rifts)"),
    ("src/AscensionCoATalentData.cpp", "LoadCoATalentData",
     "f77588ff9cad87a5aef92ef1aa780950e7a58db1663ae375c58af3319f431804", "catalog_spells"),
    ("src/AscensionClassMechanics.cpp", "HasDeprecatedWord",
     "1722fbc876ffd5f01f6a3a1b106318a935d3542c81d13d0fdbf4834e19cf8b36", "deprecated"),
)


class Dbc(object):
    """WDBC reader; a string offset is read as the client and AzerothCore read it (no special case for 0)."""

    def __init__(self, path):
        raw = open(path, "rb").read()
        if raw[:4] != b"WDBC":
            raise SystemExit("%s: not WDBC" % path)
        self.raw = raw
        self.count, self.fields, self.rsize, self.ssize = struct.unpack_from("<IIII", raw, 4)
        self.sbase = 20 + self.count * self.rsize

    def u32(self, i, f):
        return struct.unpack_from("<I", self.raw, 20 + i * self.rsize + f * 4)[0]

    def s(self, i, f):
        off = self.u32(i, f)
        if off >= self.ssize:
            return ""
        st = self.sbase + off
        return self.raw[st:self.raw.index(b"\x00", st)].decode("utf-8", "replace")


def strip_comments(text):
    return re.sub(r"//[^\n]*", " ", re.sub(r"/\*.*?\*/", " ", text, flags=re.S))


def table_rows(text, name, fields):
    m = re.search(r"std::array<[^>]+>\s+" + re.escape(name) + r"\s*=\s*\{\{(.*?)\}\};", text, re.S)
    if not m:
        raise SystemExit("table %s not found" % name)
    rows = [dict(zip(fields, [int(x) for x in re.findall(r"-?\d+", inner)]))
            for inner in re.findall(r"\{([^{}]*)\}", m.group(1))]
    rows = [r for r in rows if len(r) == len(fields)]
    size = re.search(r"std::array<[^,>]+,\s*(\d+)>\s+" + re.escape(name) + r"\b", text)
    if size and int(size.group(1)) != len(rows):
        raise SystemExit("%s: parsed %d rows, declared %s" % (name, len(rows), size.group(1)))
    return rows


def read_compat(compat, path):
    return open(os.path.join(compat, path), encoding="utf-8", errors="replace").read()


def definition(text, name):
    """The one definition of a C++ function in a comment-free text: from its name through its balanced body."""
    heads = list(re.finditer(r"\b%s\s*\([^;{}()]*\)\s*(?:const\s*)?\{" % re.escape(name), text))
    if len(heads) != 1:
        raise SystemExit("%d definitions of %s found, expected exactly one" % (len(heads), name))
    i, depth = heads[0].end() - 1, 0
    while i < len(text):
        c = text[i]
        if c in "\"'":                      # a string or character literal: its braces do not count
            i += 1
            while text[i] != c:
                i += 2 if text[i] == "\\" else 1
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if not depth:
                return text[heads[0].start():i + 1]
        i += 1
    raise SystemExit("the body of %s is not balanced" % name)


def check_replayed_rules(compat):
    """Refuse to replay a module rule whose code is no longer the code the replay copied (REPLAYED_RULES)."""
    stale, checked = [], {}
    for path, name, recorded, copy in REPLAYED_RULES:
        try:
            text = re.sub(r"\s+", "", definition(strip_comments(read_compat(compat, path)), name))
        except SystemExit as missing:
            stale.append("%s %s (replayed as %s): %s" % (path, name, copy, missing))
            continue
        actual = hashlib.sha256(text.encode("utf-8")).hexdigest()
        checked["%s %s" % (path, name)] = actual
        if actual != recorded:
            stale.append("%s %s (replayed as %s): %s, recorded %s" % (path, name, copy, actual, recorded or "none"))
    if stale:
        raise SystemExit("mod-ascension-compat's code changed under a rule this generator replays - re-check the copy "
                         "against it, then record the new fingerprint in REPLAYED_RULES:\n  " + "\n  ".join(stale))
    return checked


def cpp_constants(*texts):
    """NAME = number pairs (enumerators, constants) of comment-free C++ texts, every value a name was given."""
    values = collections.defaultdict(set)
    for text in texts:
        for m in re.finditer(r"\b([A-Z][A-Z0-9_]*)\s*=\s*(0x[0-9A-Fa-f]+|\d+)\b", text):
            values[m.group(1)].add(int(m.group(2), 0))
    return values


def constant(values, token, where):
    if token.isdigit():
        return int(token)
    found = values.get(token, set())
    if len(found) != 1:
        raise SystemExit("%s: %s resolves to %s" % (where, token, sorted(found) or "nothing"))
    return next(iter(found))


def read_racial_rules(compat, shared_defines):
    """The data of mod-ascension-compat's racial rule, read from its source: the racial skill lines per race
    (AscensionRacialAbilities::Skills, in order), the class variants outside the DBC masks (ClassVariantsOutsideDbcMask)
    and the Felsworn rifts CanGrantAscensionRacialSpell gates by race - the factionRifts of
    AscensionFelsworn::CanLearnRift (AscensionFelsworn.cpp), read from the function the fingerprint pins."""
    header = strip_comments(read_compat(compat, RACIAL_HEADER))
    values = cpp_constants(shared_defines, header)

    def pairs(table):
        m = re.search(r"std::array<\s*\w+\s*,\s*(\d+)\s*>\s+%s\s*=\s*\{\{(.*?)\}\};" % table, header, re.S)
        if not m:
            raise SystemExit("%s: table %s not found" % (RACIAL_HEADER, table))
        rows = re.findall(r"\{\s*(\w+)\s*,\s*(\w+)\s*\}", m.group(2))
        if len(rows) != int(m.group(1)):
            raise SystemExit("%s: %s parsed %d rows, declared %s" % (RACIAL_HEADER, table, len(rows), m.group(1)))
        return [(constant(values, a, RACIAL_HEADER), constant(values, b, RACIAL_HEADER)) for a, b in rows]

    skills = pairs("Skills")
    variants = pairs("ClassVariantsOutsideDbcMask")
    rule = definition(strip_comments(read_compat(compat, FELSWORN_SOURCE)), "CanLearnRift")
    m = re.search(r"std::array<\s*uint32\s*,\s*(\d+)\s*>\s+factionRifts\s*=\s*\{([^{}]*)\};", rule)
    if not m:
        raise SystemExit("%s: CanLearnRift's factionRifts not found" % FELSWORN_SOURCE)
    rifts = [int(x) for x in re.findall(r"\d+", m.group(2))]
    if len(rifts) != int(m.group(1)):
        raise SystemExit("%s: factionRifts parsed %d, declared %s" % (FELSWORN_SOURCE, len(rifts), m.group(1)))
    return skills, variants, rifts


class Coa(object):
    def __init__(self, clone, pin):
        self.clone, self.pin = clone, pin
        self.sha = self.git("rev-parse", pin + "^{commit}").strip()

    def git(self, *args):
        return subprocess.run(["git", "-C", self.clone] + list(args), capture_output=True,
                              check=True).stdout.decode("utf-8", "replace")

    def show(self, path):
        return self.git("show", "%s:%s" % (self.pin, path))


def spell_store(dbc_dir):
    d = Dbc(os.path.join(dbc_dir, "Spell.dbc"))
    if d.fields != 234:
        raise SystemExit("Spell.dbc has %d fields, expected 234" % d.fields)
    spells = {}
    for i in range(d.count):
        sid = d.u32(i, 0)
        spells[sid] = dict(name=d.s(i, 136), rank=d.s(i, 153), base=d.u32(i, 38),
                           eff=[d.u32(i, f) for f in (71, 72, 73)], item=[d.u32(i, f) for f in (107, 108, 109)])
    return spells


def skill_line_abilities(dbc_dir):
    sla = Dbc(os.path.join(dbc_dir, "SkillLineAbility.dbc"))
    sl = Dbc(os.path.join(dbc_dir, "SkillLine.dbc"))
    by_spell, by_line = collections.defaultdict(list), collections.defaultdict(list)
    for i in range(sla.count):
        r = dict(line=sla.u32(i, 1), spell=sla.u32(i, 2), race=sla.u32(i, 3), cls=sla.u32(i, 4),
                 minrank=sla.u32(i, 7), superceded=sla.u32(i, 8), acquire=sla.u32(i, 9))
        by_spell[r["spell"]].append(r)
        by_line[r["line"]].append(r)
    category = {sl.u32(i, 0): sl.u32(i, 1) for i in range(sl.count)}
    return by_spell, by_line, category


def catalog_spells(dbc_dir):
    """CharacterAdvancement.dbc read the way mod-ascension-compat's LoadCoATalentData reads it."""
    D = lambda n: Dbc(os.path.join(dbc_dir, n))
    classes, ctypes_, tabdbc, specs, adv = (D("ChrClasses.dbc"), D("CharacterAdvancementClassTypes.dbc"),
                                            D("CharacterAdvancementTabTypes.dbc"), D("ChrSpecs.dbc"),
                                            D("CharacterAdvancement.dbc"))
    token = {classes.u32(i, 0): classes.s(i, 55) for i in range(classes.count)}
    ctype = {ctypes_.u32(i, 0): (ctypes_.u32(i, 2), ctypes_.u32(i, 4) != 0) for i in range(ctypes_.count)}
    tabtok = {tabdbc.u32(i, 0): tabdbc.s(i, 1).upper() for i in range(tabdbc.count)}
    spec_by = {(specs.s(i, 1), specs.s(i, 2)): specs.u32(i, 0) for i in range(specs.count)}
    out, entries = collections.defaultdict(set), 0
    for i in range(adv.count):
        ct = ctype.get(adv.u32(i, 32))
        if not ct or not ct[1] or not 12 <= ct[0] <= 32:
            continue
        cls, tab = ct[0], adv.u32(i, 33)
        if tab != 87 and spec_by.get((token.get(cls), tabtok.get(tab))) is None:
            continue
        ranks = [adv.u32(i, f) for f in range(5, 10) if adv.u32(i, f)]
        if len(ranks) > 3:
            continue
        entries += 1
        out[cls].update(ranks)
    return out, entries


def deprecated(text):
    for word in ("deprecated", "depreacated"):
        low = (text or "").lower()
        at = low.find(word)
        while at != -1:
            before = at == 0 or not (low[at - 1].isalnum() or low[at - 1] == "_")
            end = at + len(word)
            after = end == len(low) or not (low[end].isalnum() or low[end] == "_")
            if before and after:
                return True
            at = low.find(word, at + 1)
    return False


class Racial(object):
    """CanLearn / IsSupersededRacialCopy / CanGrantAscensionRacialSpell (with AscensionFelsworn::CanLearnRift) /
    GetAscensionRacialSpells of mod-ascension-compat, offline (REPLAYED_RULES). skills and rifts are the module's
    tables (read_racial_rules); variant(cls, ability) is IsClassVariantOutsideDbcMask - the module's is (cls, spell) in
    its variants table."""

    def __init__(self, spells, by_spell, by_line, skills, variant, rifts):
        self.spells, self.by_spell, self.by_line = spells, by_spell, by_line
        self.skills, self.variant, self.rifts = list(skills), variant, set(rifts)
        self.race_of = {}
        for race, line in self.skills:       # GetRace: the first row that names the line
            self.race_of.setdefault(line, race)

    def can_learn(self, a, race, cls):
        if not race or self.race_of.get(a["line"]) != race or cls not in COA_CLASSES:
            return False
        return a["acquire"] == SKILL_LINE_ABILITY_LEARNED_ON_SKILL_LEARN and a["minrank"] <= 1 and \
            not a["superceded"] and (not a["race"] or a["race"] & (1 << (race - 1))) and \
            (self.variant(cls, a) or not a["cls"] or a["cls"] & (1 << (cls - 1)))

    def superseded_copy(self, race, cls, sid):
        if sid not in self.spells:           # RacialSpellName: no SpellInfo
            return False
        name = self.spells[sid]["name"]
        for r, line in self.skills:
            if r != race:
                continue
            for a in self.by_line.get(line, []):
                if a["spell"] >= sid or not self.can_learn(a, race, cls):
                    continue
                if self.spells.get(a["spell"], {}).get("name") == name:
                    return True
        return False

    def can_grant(self, race, cls, sid):
        rows = self.by_spell.get(sid, [])
        if sid in self.rifts:                # CanLearnRift: a rift's race-masked row must name the race
            for a in rows:
                if a["race"] and not a["race"] & (1 << (race - 1)):
                    return False
        racial = False
        for a in rows:
            if a["line"] in self.race_of:
                racial = True
                if self.can_learn(a, race, cls):
                    return not self.superseded_copy(race, cls, sid)
        return not racial

    def mask(self, cls, sid):
        allowed = [r for r in PLAYABLE_RACES if self.can_grant(r, cls, sid)]
        if len(allowed) == len(PLAYABLE_RACES):
            return 0
        return sum(1 << (r - 1) for r in allowed)

    def racials(self, race, cls):
        """What the module offers the character from its racial lines (CanLearn), what T2 takes away as a same-name
        copy (IsSupersededRacialCopy), and so what it grants (GetAscensionRacialSpells)."""
        offered, removes = set(), set()
        for r, line in self.skills:
            if r == race:
                for a in self.by_line.get(line, []):
                    if self.can_learn(a, race, cls):
                        offered.add(a["spell"])
                    if self.superseded_copy(race, cls, a["spell"]):
                        removes.add(a["spell"])
        return dict(offered=sorted(offered), t2_removes=sorted(removes), granted=sorted(offered - removes))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--coa-clone", required=True)
    ap.add_argument("--pin", required=True)
    ap.add_argument("--compat", required=True, help="a mod-ascension-compat tree (talent system data)")
    ap.add_argument("--dbc-dir", required=True, help="the server's DBC directory")
    ap.add_argument("--vanity-dbc", required=True, help="Ascension's VanityCollection.dbc")
    ap.add_argument("--spell-dbc-ids", help="ids of the world DB's spell_dbc table, one per line")
    ap.add_argument("--out", required=True)
    ap.add_argument("--evidence")
    args = ap.parse_args()

    rule_fingerprints = check_replayed_rules(args.compat)
    coa = Coa(args.coa_clone, args.pin)
    ccd = strip_comments(coa.show("src/server/coa/AscensionCustomClassData.h"))
    prog = strip_comments(coa.show("src/server/coa/AscensionSpellProgressionData.h"))
    shared_defines = strip_comments(coa.show("src/server/shared/SharedDefines.h"))
    book = "modules/mod-spellbook/src/"
    class_spells = table_rows(ccd, "ClassSpells", ["ClassId", "RequiredLevel", "SpellId"])
    # CoA's SynchronizeProgression grants the Felsworn (CLASS_DEMON_HUNTER) its Horde-capital rifts at their level and
    # takes them back below it, exactly as it does ClassSpells: rows of CLASS, which mod-ascension-compat's reconcile
    # takes back the same way (the Alliance-capital rifts are ClassSpells rows).
    felsworn = constant(cpp_constants(shared_defines), "CLASS_DEMON_HUNTER", "SharedDefines.h")
    horde_rifts = [dict(ClassId=felsworn, RequiredLevel=r["RequiredLevel"], SpellId=r["SpellId"]) for r in table_rows(
        strip_comments(coa.show("src/server/coa/AscensionCompat.cpp")), "FelswornHordeCapitalRifts",
        ["SpellId", "RequiredLevel"])]
    unresolved = table_rows(ccd, "UnresolvedTrainerSpells", ["ClassId", "RequiredLevel", "SpellId"])
    ranks = table_rows(prog, "Ranks", ["ClassId", "FirstSpellId", "SpellId", "RequiredLevel"])
    offers = table_rows(strip_comments(coa.show(book + "SpellbookOfferData.h")), "Offers",
                        ["ClassId", "RequiredLevel", "FirstSpellId", "SpellId"])
    trainer = table_rows(strip_comments(coa.show(book + "SpellbookTrainerData.h")), "Offers",
                         ["ClassId", "RequiredLevel", "FirstSpellId", "SpellId"])
    book_ranks = table_rows(strip_comments(coa.show(book + "SpellbookRankData.h")), "Ranks",
                            ["ClassId", "RequiredLevel", "RankNumber", "RequiredSpellId", "SpellId"])
    tree = table_rows(strip_comments(coa.show(book + "SpellbookTreeSpellData.h")), "TreeSpells", ["ClassId", "SpellId"])

    rd = lambda n: strip_comments(open(os.path.join(args.compat, "src", n), encoding="utf-8", errors="replace").read())
    taught = table_rows(rd("AscensionTaughtAbilityData.h"), "TaughtAbilities",
                        ["ClassId", "SpecId", "RequiredLevel", "ParentSpellId", "SpellId"])
    repl_text = rd("AscensionTalentReplacementData.h")
    replacements = []
    # { ClassId, SpecId, ParentSpellId, OriginalSpellId, {{ ranks }} [, RequiresAura] }: an aura-gated row (CoA
    # b03b7cfe) is a window the parent aura opens, not a talent - its ranks are the replacement system's all the same
    for m in re.finditer(r"\{\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*\{\{(.*?)\}\}"
                         r"\s*(?:,\s*(true|false)\s*)?\}", repl_text[repl_text.find("TalentReplacements"):], re.S):
        replacements.append(dict(ClassId=int(m.group(1)), Parent=int(m.group(3)), Original=int(m.group(4)),
                                 Ranks=[int(a) for a, _ in re.findall(r"\{\s*(\d+)\s*,\s*(\d+)\s*\}", m.group(5))],
                                 RequiresAura=m.group(6) == "true"))
    declared = re.search(r"std::array<\s*TalentReplacement\s*,\s*(\d+)\s*>\s+TalentReplacements\b", repl_text)
    if not declared or int(declared.group(1)) != len(replacements):
        raise SystemExit("TalentReplacements: parsed %d rows, declared %s"
                         % (len(replacements), declared and declared.group(1)))

    spells = spell_store(args.dbc_dir)
    by_spell, by_line, line_category = skill_line_abilities(args.dbc_dir)
    catalog, catalog_entries = catalog_spells(args.dbc_dir)
    skills, variants, rifts = read_racial_rules(args.compat, shared_defines)
    variant_pairs = set(variants)
    racial = Racial(spells, by_spell, by_line, skills, lambda cls, a: (cls, a["spell"]) in variant_pairs, rifts)
    for r in horde_rifts:
        if r["SpellId"] not in spells or not 1 <= r["RequiredLevel"] <= 80:
            raise SystemExit("FelswornHordeCapitalRifts row %s: not a spell of the store at a level 1-80" % r)
    vd = Dbc(args.vanity_dbc)
    vanity = {struct.unpack_from("<I", vd.raw, 20 + i * vd.rsize + 4)[0] for i in range(vd.count)} - {0}
    spell_dbc_ids = set()
    if args.spell_dbc_ids:
        spell_dbc_ids = {int(x) for x in open(args.spell_dbc_ids).read().split()}

    talent_owned = collections.defaultdict(dict)
    for e in replacements:
        for s in e["Ranks"]:
            if s:
                talent_owned[e["ClassId"]][s] = "TalentReplacements rank of %s %d" % (
                    "aura window" if e["RequiresAura"] else "talent", e["Parent"])
    for e in taught:
        talent_owned[e["ClassId"]][e["SpellId"]] = "TaughtAbilities spell of %d" % e["ParentSpellId"]
    # every spell a class script of mod-ascension-compat makes a replacement target: the module's own gate resolves
    # them (tools/check_replacement_learns.py, rule 2 - no announcing learn may teach one)
    gate_out = subprocess.run([sys.executable, "-B", os.path.join(args.compat, "tools", "check_replacement_learns.py"),
                               os.path.join(args.compat, "src"), "--targets"], capture_output=True).stdout.decode()
    replacement_targets = {int(t) for t in re.findall(r"^\s*target (\d+)", gate_out, re.M)}
    if len(replacement_targets) < 50:
        raise SystemExit("the replacement gate resolved only %d targets" % len(replacement_targets))

    rows_out, excluded, per_class = [], [], {}
    not_in_store = collections.OrderedDict()   # CoA rows this server's Spell.dbc cannot carry: (class, spell) -> row
    for cls in COA_CLASSES:
        tree_spells = {r["SpellId"] for r in tree if r["ClassId"] == cls}
        rows = collections.OrderedDict()

        def add(sid, level, req, source):
            if sid and sid not in spells and sid not in tree_spells:
                not_in_store.setdefault((cls, sid), dict(ClassId=cls, Level=level, SpellId=sid, Source=source))
            if not sid or sid not in spells or sid in tree_spells or sid in rows:
                return
            rows[sid] = dict(ClassId=cls, Level=level, SpellId=sid, RequiredSpellId=req, Source=source)

        for e in class_spells + horde_rifts:
            if e["ClassId"] == cls:
                add(e["SpellId"], e["RequiredLevel"], 0, "CLASS")
        ladders = collections.OrderedDict()
        for e in ranks:
            if e["ClassId"] != cls:
                continue
            members = ladders.setdefault(e["FirstSpellId"], [])
            if not members and e["FirstSpellId"] in spells:
                members.append((min(spells[e["FirstSpellId"]]["base"], 255), e["FirstSpellId"]))
            members.append((e["RequiredLevel"], e["SpellId"]))

        def rank_below(root, level, sid):
            below = 0
            for lvl, member in ladders.get(root, []):
                if member != sid and lvl < level:
                    below = member
            if below:
                return below
            return root if sid != root else 0

        for e in ranks:
            if e["ClassId"] != cls:
                continue
            first = spells.get(e["FirstSpellId"])
            if first and 1 <= first["base"] <= 80:
                add(e["FirstSpellId"], first["base"], 0, "RANK_ROOT")
            add(e["SpellId"], e["RequiredLevel"], rank_below(e["FirstSpellId"], e["RequiredLevel"], e["SpellId"]), "RANK")
        for o in offers:
            if o["ClassId"] == cls:
                add(o["SpellId"], o["RequiredLevel"], rank_below(o["FirstSpellId"], o["RequiredLevel"], o["SpellId"]), "OFFER")
        for o in trainer:
            if o["ClassId"] == cls:
                add(o["SpellId"], o["RequiredLevel"], rank_below(o["FirstSpellId"], o["RequiredLevel"], o["SpellId"]), "TRAINER")
        for r in book_ranks:
            if r["ClassId"] == cls:
                add(r["SpellId"], r["RequiredLevel"], r["RequiredSpellId"], "BOOK_RANK")

        kept = []
        for r in rows.values():
            s = spells[r["SpellId"]]
            why = None
            if r["Source"] not in ("CLASS", "RANK"):   # today's CoA progression data stays exactly as it was
                if r["SpellId"] in catalog[cls]:
                    why = "Character Advancement entry spell (the talent system grants it)"
                elif r["SpellId"] in talent_owned[cls]:
                    why = talent_owned[cls][r["SpellId"]] + " (the talent system grants it)"
                elif r["SpellId"] in replacement_targets:
                    why = "replacement target of a class script (taught hidden while its talent or window is up)"
            elif r["SpellId"] in catalog[cls] or r["SpellId"] in talent_owned[cls] or r["SpellId"] in replacement_targets:
                raise SystemExit("progression row %d of class %d is also owned by the talent system - decide first"
                                 % (r["SpellId"], cls))
            if not why and any(s["eff"][k] in ITEM_EFFECTS and s["item"][k] in vanity for k in range(3)):
                why = "creates an Ascension vanity item"
            if not why and (deprecated(s["name"]) or deprecated(s["rank"])):
                why = "deprecated (Player::learnSpell refuses it for a CoA class)"
            if not why and r["SpellId"] in spell_dbc_ids:
                raise SystemExit("spell %d is also a spell_dbc row: the table would win over Spell.dbc - decide first"
                                 % r["SpellId"])
            if why:
                excluded.append(dict(r, reason=why, name=s["name"], rank=s["rank"]))
                continue
            if r["Source"] not in ("CLASS", "RANK"):
                for a in by_spell.get(r["SpellId"], []):
                    if line_category.get(a["line"]) in (9, 11) and not a["cls"] & (1 << (cls - 1)):
                        raise SystemExit("trainer row %d of class %d sits on profession line %d without the class bit"
                                         % (r["SpellId"], cls, a["line"]))
            r["RaceMask"] = racial.mask(cls, r["SpellId"])
            r["Name"], r["Rank"] = s["name"], s["rank"]
            kept.append(r)

        # learning order: a row whose requirement is a row of the class comes after it; otherwise level, then data
        index = {r["SpellId"]: n for n, r in enumerate(kept)}
        order, placed, visiting = [], set(), set()

        def place(r):
            sid = r["SpellId"]
            if sid in placed:
                return
            if sid in visiting:
                raise SystemExit("requirement cycle at %d (class %d)" % (sid, cls))
            visiting.add(sid)
            req = r["RequiredSpellId"]
            if req in index:
                place(kept[index[req]])
            visiting.discard(sid)
            placed.add(sid)
            order.append(r)

        for r in sorted(kept, key=lambda x: (x["Level"], index[x["SpellId"]])):
            place(r)
        seen = set()
        for r in order:
            if r["RequiredSpellId"] in index and r["RequiredSpellId"] not in seen:
                raise SystemExit("order check failed at %d" % r["SpellId"])
            seen.add(r["SpellId"])
        rows_out.extend(order)
        per_class[cls] = collections.Counter(r["Source"] for r in order)

    unresolved_map = {}
    kept_ids = {(r["ClassId"], r["SpellId"]): r for r in rows_out}
    excl_ids = {(r["ClassId"], r["SpellId"]): r for r in excluded}
    for e in unresolved:
        k = (e["ClassId"], e["SpellId"])
        if k in kept_ids:
            unresolved_map[e["SpellId"]] = "row, level %d (%s)" % (kept_ids[k]["Level"], kept_ids[k]["Source"])
        elif k in excl_ids:
            unresolved_map[e["SpellId"]] = "excluded: " + excl_ids[k]["reason"]
        else:
            unresolved_map[e["SpellId"]] = "no CoA trainer sells it (not a Books of Ascension row)"

    write_header(args, coa, rows_out, per_class, excluded, catalog_entries, len(vanity))
    summary = dict(pin=coa.sha, rows=len(rows_out), excluded=len(excluded),
                   by_source=dict(collections.Counter(r["Source"] for r in rows_out)),
                   race_masked=sum(1 for r in rows_out if r["RaceMask"]),
                   with_requirement=sum(1 for r in rows_out if r["RequiredSpellId"]),
                   unresolved=collections.Counter(v.split(",")[0].split(":")[0] for v in unresolved_map.values()),
                   not_in_store=len(not_in_store))
    print(json.dumps(summary, indent=1))
    if args.evidence:
        racials = {"%d,%d" % (race, cls): racial.racials(race, cls) for race in PLAYABLE_RACES for cls in COA_CLASSES}
        # not_in_store: what a spell package round would still turn into rows (see the docstring)
        json.dump(dict(summary=summary, rows=rows_out, excluded=excluded, unresolved=unresolved_map,
                       per_class={c: dict(v) for c, v in per_class.items()}, replayed_rules=rule_fingerprints,
                       racial_rule=dict(skills=skills, variants=sorted(variant_pairs), rifts=rifts),
                       horde_rifts=horde_rifts, racials=racials, not_in_store=list(not_in_store.values())),
                  open(args.evidence, "w"), indent=1)


def write_header(args, coa, rows, per_class, excluded, catalog_entries, vanity_count):
    L = []
    w = L.append
    w("// Generated by tools/build_coa_class_spells.py - do not edit by hand; regenerate from a new CoA pin instead.")
    w("//")
    w("// The level-based spells of the 21 Chapters-of-Azeroth classes (ids 12-32): what CoA's own class trainer, the")
    w("// Books of Ascension (CoA's mod-spellbook, spellbook.cpp BuildRows), would sell a character of the class at")
    w("// each level. mod-learn-spells teaches every row on a level-up (LearnCoAClassSpells), exactly as it teaches the")
    w("// stock classes their spells, and mod-ascension-compat asks it to again after a talent or specialization")
    w("// change, at character creation and on an explicit repair.")
    w("//")
    w("// Source: Chapters of Azeroth %s" % coa.sha)
    w("//   src/server/coa/AscensionCustomClassData.h       ClassSpells                   -> Source CLASS")
    w("//   src/server/coa/AscensionCompat.cpp              FelswornHordeCapitalRifts     -> Source CLASS")
    w("//   src/server/coa/AscensionSpellProgressionData.h  Ranks (rank ladders)          -> Source RANK, RANK_ROOT")
    w("//   modules/mod-spellbook/src/SpellbookOfferData.h  services the trainer sold     -> Source OFFER")
    w("//   modules/mod-spellbook/src/SpellbookTrainerData.h NPCTrainer continuations     -> Source TRAINER")
    w("//   modules/mod-spellbook/src/SpellbookRankData.h   unresolved rank upgrades      -> Source BOOK_RANK")
    w("//   modules/mod-spellbook/src/SpellbookTreeSpellData.h talent-tree spells: never a trainer row")
    w("// Left out, as in the trainer window or because the Forgotten Land talent system owns them: a Character")
    w("// Advancement entry's spell (%d entries), a TalentReplacements rank or target, a TaughtAbilities spell, a"
      % catalog_entries)
    w("// spell a class script makes a replacement target (mod-ascension-compat's check_replacement_learns); also a")
    w("// spell that creates an Ascension vanity item (VanityCollection.dbc, %d items) or a deprecated one. The Book of"
      % vanity_count)
    w("// Artisans (trainer 200001) is never read: a spell only it teaches is a profession recipe.")
    w("// %d rows, %d left out." % (len(rows), len(excluded)))
    w("//")
    w("// RequiredSpellId: the rank beneath, which the character must hold (0 = none). RaceMask: the races")
    w("// mod-ascension-compat's CanGrantAscensionRacialSpell allows (0 = every race). Rows of a class are in")
    w("// learning order - a row's RequiredSpellId, when it is a row of the class, comes before it - so one pass")
    w("// learns a whole ladder.")
    w("#ifndef MOD_LEARN_SPELLS_COA_DATA_H")
    w("#define MOD_LEARN_SPELLS_COA_DATA_H")
    w("")
    w("#include \"LearnSpellsCoA.h\"")
    w("")
    w("#include <array>")
    w("")
    w("namespace LearnSpells::CoAData")
    w("{")
    w("inline constexpr std::array<CoAClassSpell, %d> ClassSpells =" % len(rows))
    w("{{")
    cls = None
    for r in rows:
        if r["ClassId"] != cls:
            cls = r["ClassId"]
            c = per_class[cls]
            w("    // class %d: %s" % (cls, ", ".join("%s %d" % (s, c[s]) for s in SOURCES if c.get(s))))
        name = (r["Name"] + (" (" + r["Rank"] + ")" if r["Rank"] else "")).replace("*/", "* /")
        w("    { %d, %d, %d, %d, %d, CoASource::%s }, // %s" % (r["ClassId"], r["Level"], r["SpellId"],
                                                            r["RequiredSpellId"], r["RaceMask"], r["Source"], name))
    w("}};")
    w("}")
    w("")
    w("#endif")
    open(args.out, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
