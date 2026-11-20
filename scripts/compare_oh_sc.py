#!/usr/bin/env python3
"""
Compare Ohio Black Laws with South Carolina Jim Crow acts, section by section
=============================================================================

Adapted from 02_reuse_all_pairs.py (8510, Week 11: Text Reuse), using the same
helpers from common.py (phrases, jaccard, snippet). The three moves are the same:
chop each section into N-word phrases, compare, score.

Changes from 02, and why:

  1. Only Ohio-vs-SC pairs are compared (about 35 x 4,800 sections), not every
     pair in the combined corpus, which would be mostly SC-vs-SC.
  2. Boilerplate is dropped first, as in 03_reuse_minhash.py: any phrase found in
     more than MAX_SC_SECTIONS SC sections ("be it enacted by the senate and
     house ...") is ignored on both sides.
  3. Two scores per pair:
       jaccard   = shared phrases / all different phrases in both (as in 02)
       ohio_share = shared phrases / the Ohio section's phrases
     Ohio sections are much shorter than most SC sections, and Jaccard counts
     the long SC section's other phrases against the match. ohio_share asks the
     narrower question: how much of the Ohio clause turns up in the SC section?
  4. A lower threshold. 02's MATCH = 0.5 suits near-copies in one journal; laws
     decades apart score far lower. Funk and Mullen kept matches down to 0.1.
  5. Appropriation bills (flagged in the SC metadata) are left out by default.

  6. Optional: normalize racial terms (add "norm" to the command). Ohio's and
     South Carolina's different words for Black people ("black or mulatto
     person," "negro," "colored," "person of African descent," ...) all become
     one token, RACETERM, before phrases are made. Exact matching then counts
     "any black or mulatto person" and "any negro" as the same phrase, so the
     run tests for shared legal structure behind different vocabulary.
     "White" is left as it is: both states already use the same word.

Usage, from the OH_SC_Text_Reuse folder:
    python3 scripts/compare_oh_sc.py            # 5-word phrases
    python3 scripts/compare_oh_sc.py 4          # 4-word phrases
    python3 scripts/compare_oh_sc.py 5 norm     # 5-word phrases, racial terms normalized

Saves output/compare_n<N>[_norm].csv (every kept pair, best first) and
output/compare_n<N>[_norm]_boilerplate.csv (the phrases ignored as boilerplate).
"""

import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from common import jaccard, phrases, snippet

# --- Change these --------------------------------------------------------------

ARGS = sys.argv[1:]
N = next((int(a) for a in ARGS if a.isdigit()), 5)   # words per phrase
NORMALIZE = "norm" in ARGS                            # normalize racial terms?
MATCH = 0.10            # keep pairs with at least this Jaccard score...
OHIO_SHARE = 0.20       # ...or at least this share of the Ohio section's phrases
MAX_SC_SECTIONS = 50    # phrases in more SC sections than this are boilerplate
EXCLUDE_APPROPRIATIONS = True
SHOW = 15               # pairs to print

# -------------------------------------------------------------------------------

# Racial terms for Black people, and the mixed-race categories the laws list
# with them, become TOKEN. The nouns after them stay ("colored children" ->
# "raceterm children"; "black or mulatto person" -> "raceterm person"), so both
# states' phrasing lines up. The token is lowercase letters only, because
# common.py's phrases() keeps only lowercase letters.
TOKEN = "raceterm"
REPLACEMENTS = [
    # descriptive phrases -> "raceterm person(s)" / "raceterm blood"
    (r"\b(persons?) having a distinct and visible admixture of african blood\b", TOKEN + r" \1"),
    (r"\b(persons?) of (?:african descent|color)\b", TOKEN + r" \1"),
    (r"\bafrican blood\b", TOKEN + " blood"),
    # single words ("black" not in place names such as Black River)
    (r"\b(?:negroes|negro|mulattoes|mulattos|mulatto|mestizoes|mestizoe|mestizo|"
     r"half[ -]breeds?|colored|black(?! (?:river|creek|swamp|mingo|oak|water)\b))\b", TOKEN),
]
# "raceterm or raceterm", "raceterm, raceterm and raceterm" -> one token
COLLAPSE = re.compile(rf"\b{TOKEN}(?:(?:,? (?:or|and)|,) {TOKEN})+\b")


def normalize(text):
    for pattern, repl in REPLACEMENTS:
        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
    return COLLAPSE.sub(TOKEN, text)


PROJECT = Path(__file__).resolve().parent.parent
OHIO_DIR = PROJECT / "data" / "ohio_black_laws"
SC_DIR = PROJECT / "data" / "sc_jimcrow_1877-1920"
OUTPUT = PROJECT / "output"


def read_metadata(folder):
    with open(folder / "metadata.csv", newline="", encoding="utf-8") as f:
        return {row["doc_id"]: row for row in csv.DictReader(f)}


def read_sections(folder, skip=()):
    """Every section file as {"id", "doc_id", "text"}, in file-name order."""
    out = []
    for file in sorted((folder / "sections").glob("*.txt")):
        doc_id = file.stem.rsplit("_s", 1)[0]
        if doc_id in skip:
            continue
        text = file.read_text(encoding="utf-8")
        out.append({"id": file.stem, "doc_id": doc_id, "text": text,
                    "compare": normalize(text) if NORMALIZE else text})
    return out


def main():
    ohio_meta, sc_meta = read_metadata(OHIO_DIR), read_metadata(SC_DIR)
    skip = {d for d, r in sc_meta.items() if r.get("appropriation_like") == "True"} \
        if EXCLUDE_APPROPRIATIONS else set()

    ohio = read_sections(OHIO_DIR)
    sc = read_sections(SC_DIR, skip)
    print(f"{len(ohio)} Ohio sections, {len(sc):,} SC sections "
          f"({len(skip)} appropriation acts left out), {N}-word phrases"
          + (", racial terms normalized" if NORMALIZE else ""))

    # 1. Chop every section into phrases
    ohio_p = [phrases(s["compare"], N) for s in ohio]
    sc_p = [phrases(s["compare"], N) for s in sc]

    # 2. Boilerplate: phrases in more than MAX_SC_SECTIONS SC sections
    counts = Counter(p for ps in sc_p for p in ps)
    boilerplate = {p for p, c in counts.items() if c > MAX_SC_SECTIONS}
    ohio_p = [ps - boilerplate for ps in ohio_p]
    sc_p = [ps - boilerplate for ps in sc_p]
    hits = sorted(boilerplate & set().union(*[phrases(s["compare"], N) for s in ohio]),
                  key=lambda p: -counts[p])
    print(f"{len(boilerplate):,} boilerplate phrases ignored "
          f"({len(hits)} of them also occur in the Ohio laws)")

    # 3. Compare each Ohio section only with SC sections sharing a phrase
    index = defaultdict(set)
    for j, ps in enumerate(sc_p):
        for p in ps:
            index[p].add(j)

    pairs = []
    for i, o in enumerate(ohio_p):
        if not o:
            continue
        candidates = set().union(*(index[p] for p in o if p in index))
        for j in candidates:
            shared = o & sc_p[j]
            score, share = jaccard(o, sc_p[j]), len(shared) / len(o)
            if score >= MATCH or share >= OHIO_SHARE:
                pairs.append((share, score, i, j, shared))

    # 4. Best first: by share of the Ohio clause, then Jaccard
    pairs.sort(key=lambda x: (x[0], x[1]), reverse=True)
    print(f"{len(pairs):,} pairs kept (Jaccard >= {MATCH} or Ohio share >= {OHIO_SHARE})\n")

    def show(rows, heading):
        print(heading)
        for share, score, i, j, shared in rows[:SHOW]:
            m = sc_meta.get(sc[j]["doc_id"], {})
            print(f"ohio share {share:.2f}  jaccard {score:.2f}  {len(shared)} phrases "
                  f"({sum(TOKEN in p for p in shared)} with {TOKEN})")
            print(f"   {ohio[i]['id']}  ->  {sc[j]['id']}  [{m.get('tags', '')}]")
            print(f"   \"{snippet(ohio[i]['compare'], shared, N)} ...\"\n")

    show(pairs, "Best pairs overall:\n")
    if NORMALIZE:
        show([x for x in pairs if any(TOKEN in p for p in x[4])],
             f"Best pairs sharing at least one phrase with {TOKEN}:\n")

    OUTPUT.mkdir(exist_ok=True)
    tag = f"n{N}" + ("_norm" if NORMALIZE else "")
    path = OUTPUT / f"compare_{tag}.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ohio_share", "jaccard", "n_shared", "n_shared_racial", "ohio_section", "ohio_date",
                    "sc_section", "sc_year", "sc_title", "sc_county", "sc_tags",
                    "shared_phrases", "ohio_text", "sc_text"])
        for share, score, i, j, shared in pairs:
            m = sc_meta.get(sc[j]["doc_id"], {})
            w.writerow([round(share, 3), round(score, 3), len(shared),
                        sum(TOKEN in p for p in shared), ohio[i]["id"],
                        ohio_meta.get(ohio[i]["doc_id"], {}).get("date", ""),
                        sc[j]["id"], m.get("year", ""), m.get("title", ""),
                        m.get("county", ""), m.get("tags", ""),
                        " | ".join(sorted(shared)), ohio[i]["text"].strip(),
                        sc[j]["text"].strip()])
    bpath = OUTPUT / f"compare_{tag}_boilerplate.csv"
    with open(bpath, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["phrase", "sc_sections", "in_ohio"])
        for p in sorted(boilerplate, key=lambda p: -counts[p]):
            w.writerow([p, counts[p], p in set(hits)])
    print(f"Saved {path.relative_to(PROJECT)} and {bpath.relative_to(PROJECT)}")


if __name__ == "__main__":
    main()
