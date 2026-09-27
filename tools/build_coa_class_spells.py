#!/usr/bin/env python3
r"""Generate src/LearnSpellsCoAData.h: the level-based spells of the 21 Chapters-of-Azeroth classes (ids 12-32).

What a CoA class learns on a level-up is what CoA's own class trainer - the Books of Ascension, module
mod-spellbook of Chapters of Azeroth - would sell it at that level (spellbook.cpp BuildRows, window view):

  1. the class progression spells, ClassSpells in src/server/coa/AscensionCustomClassData.h, at their level;
  2. the rank ladders, AscensionProgression::Ranks in AscensionSpellProgressionData.h: a ladder's first rank at its
     Spell.dbc BaseLevel when nothing else grants it, every higher rank at its level and requiring the rank beneath;
  3. SpellbookOfferData, SpellbookTrainerData and SpellbookRankData: the services CoA's captured original trainer
     window sold that the generated class data never resolved (the "trainer-taught" spells), at their level and
     requiring the rank beneath.

A spell the talent trees grant is not a trainer row (SpellbookTreeSpellData, as in the window), and neither is a spell
the Forgotten Land talent system owns: a Character Advancement entry's spell (CharacterAdvancement.dbc read as
mod-ascension-compat's LoadCoATalentData reads it), a TalentReplacements rank or target or a TaughtAbilities spell
(mod-ascension-compat's data headers), or a spell a class script makes a replacement target (resolved by
mod-ascension-compat's own gate, tools/check_replacement_learns.py --targets). A spell that creates an Ascension vanity item (VanityCollection.dbc) or whose
name marks it deprecated is left out too. Nothing of the Book of Artisans (trainer 200001) is read: a spell only it
teaches is a profession recipe.

RaceMask replays mod-ascension-compat's CanGrantAscensionRacialSpell for every playable race (0 = every race).

Every input is read, never executed: the CoA clone through `git show <pin>:<path>`, the DBC files directly.

usage:
  build_coa_class_spells.py --coa-clone DIR --pin SHA --compat DIR --dbc-dir DIR --vanity-dbc FILE
                            [--spell-dbc-ids FILE] --out HEADER [--evidence JSON]
"""
import argparse
import collections
import json
import os
import re
import struct
import subprocess
import sys

COA_CLASSES = range(12, 33)
PLAYABLE_RACES = (1, 2, 3, 4, 5, 6, 7, 8, 10, 11)
# AscensionRacialAbilities::Skills (mod-ascension-compat): race -> racial skill lines
RACIAL_SKILLS = ((1, 754), (2, 125), (2, 11125), (3, 101), (4, 126), (5, 220), (6, 124), (7, 753), (8, 733),
                 (10, 756), (11, 760), (11, 11760))
FELSWORN_CAPITAL_RIFTS = (535595, 535596, 535597, 535598, 535599, 535600)
CLASS_WITCH_HUNTER, CLASS_SUN_CLERIC = 15, 27
SKILL_RACIAL_BLOODELF, SKILL_DRAENEI_RACIAL_COA = 756, 11760
SPELL_ARCANE_TORRENT_ALL_RESOURCES, SPELL_GIFT_OF_THE_NAARU_HYBRID = 28730, 814282
SOURCES = ("CLASS", "RANK", "RANK_ROOT", "OFFER", "TRAINER", "BOOK_RANK")
ITEM_EFFECTS = (24, 157, 34, 66)


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
    """CanGrantAscensionRacialSpell / CanLearn / IsSupersededRacialCopy of mod-ascension-compat, offline."""

    def __init__(self, spells, by_spell, by_line):
        self.spells, self.by_spell, self.by_line = spells, by_spell, by_line
        self.race_of = {line: race for race, line in RACIAL_SKILLS}

    def can_learn(self, a, race, cls):
        if self.race_of.get(a["line"]) != race:
            return False
        torrent = cls == CLASS_WITCH_HUNTER and a["line"] == SKILL_RACIAL_BLOODELF and \
            a["spell"] == SPELL_ARCANE_TORRENT_ALL_RESOURCES
        gift = cls == CLASS_SUN_CLERIC and a["line"] == SKILL_DRAENEI_RACIAL_COA and a["spell"] == SPELL_GIFT_OF_THE_NAARU_HYBRID
        return a["acquire"] == 2 and a["minrank"] <= 1 and not a["superceded"] and \
            (not a["race"] or a["race"] & (1 << (race - 1))) and \
            (torrent or gift or not a["cls"] or a["cls"] & (1 << (cls - 1)))

    def superseded_copy(self, race, cls, sid):
        name = self.spells.get(sid, {}).get("name")
        if not name:
            return False
        for r, line in RACIAL_SKILLS:
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
        if sid in FELSWORN_CAPITAL_RIFTS:
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

    coa = Coa(args.coa_clone, args.pin)
    ccd = strip_comments(coa.show("src/server/coa/AscensionCustomClassData.h"))
    prog = strip_comments(coa.show("src/server/coa/AscensionSpellProgressionData.h"))
    book = "modules/mod-spellbook/src/"
    class_spells = table_rows(ccd, "ClassSpells", ["ClassId", "RequiredLevel", "SpellId"])
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
    for m in re.finditer(r"\{\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*\{\{(.*?)\}\}\s*\}",
                         repl_text[repl_text.find("TalentReplacements"):], re.S):
        replacements.append(dict(ClassId=int(m.group(1)), Parent=int(m.group(3)), Original=int(m.group(4)),
                                 Ranks=[int(a) for a, _ in re.findall(r"\{\s*(\d+)\s*,\s*(\d+)\s*\}", m.group(5))]))

    spells = spell_store(args.dbc_dir)
    by_spell, by_line, line_category = skill_line_abilities(args.dbc_dir)
    catalog, catalog_entries = catalog_spells(args.dbc_dir)
    racial = Racial(spells, by_spell, by_line)
    vd = Dbc(args.vanity_dbc)
    vanity = {struct.unpack_from("<I", vd.raw, 20 + i * vd.rsize + 4)[0] for i in range(vd.count)} - {0}
    spell_dbc_ids = set()
    if args.spell_dbc_ids:
        spell_dbc_ids = {int(x) for x in open(args.spell_dbc_ids).read().split()}

    talent_owned = collections.defaultdict(dict)
    for e in replacements:
        for s in e["Ranks"]:
            if s:
                talent_owned[e["ClassId"]][s] = "TalentReplacements rank of talent %d" % e["Parent"]
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
    for cls in COA_CLASSES:
        tree_spells = {r["SpellId"] for r in tree if r["ClassId"] == cls}
        rows = collections.OrderedDict()

        def add(sid, level, req, source):
            if not sid or sid not in spells or sid in tree_spells or sid in rows:
                return
            rows[sid] = dict(ClassId=cls, Level=level, SpellId=sid, RequiredSpellId=req, Source=source)

        for e in class_spells:
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
                   unresolved=collections.Counter(v.split(",")[0].split(":")[0] for v in unresolved_map.values()))
    print(json.dumps(summary, indent=1))
    if args.evidence:
        json.dump(dict(summary=summary, rows=rows_out, excluded=excluded, unresolved=unresolved_map,
                       per_class={c: dict(v) for c, v in per_class.items()}), open(args.evidence, "w"), indent=1)


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
