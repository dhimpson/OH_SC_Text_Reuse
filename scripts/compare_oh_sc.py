#!/usr/bin/env python3
"""
Compare two corpora of race laws, section by section
====================================================

Adapted from 02_reuse_all_pairs.py (8510, Week 11: Text Reuse), using the same
helpers from common.py (phrases, jaccard, snippet). The three moves are the same:
chop each section into N-word phrases, compare, score.

Corpora (folders in data/):
  ohio       Ohio Black Laws, 1802-1878 (Arnett 1886)
  blackcode  South Carolina's December 1865 Black Code (Statutes at Large, vol. 13)
  jimcrow    SC acts flagged as likely Jim Crow laws, 1877-1920 (On the Books)
  slaveacts  SC acts relating to slaves and free people of color, 1690-1835
             (Statutes at Large, vol. 7)

Every section of corpus A is compared with every section of corpus B.
A is the earlier, smaller corpus whose language you are looking for in B.

Changes from 02, and why:

  1. Only A-vs-B pairs are compared, not every pair in the combined corpus.
  2. Boilerplate is dropped first, as in 03_reuse_minhash.py: any phrase found in
     more than MAX_B_SECTIONS sections of B ("be it enacted by the senate and
     house ...") is ignored on both sides.
  3. Two scores per pair:
       jaccard  = shared phrases / all different phrases in both (as in 02)
       share_a  = shared phrases / the A section's phrases
     A sections are often much shorter than B sections, and Jaccard counts the
     long section's other phrases against the match. share_a asks the narrower
     question: how much of the A section turns up in the B section?
  4. A lower threshold. 02's MATCH = 0.5 suits near-copies in one journal; laws
     decades apart score far lower. Funk and Mullen kept matches down to 0.1.
  5. Appropriation bills (flagged in the Jim Crow metadata) are left out by default.
  6. Enacting clauses are removed before comparison, from a short fixed list:
     South Carolina's "Be it enacted by the Senate and House of Representatives,
     now met and sitting in General Assembly, and by the authority of the same,"
     Ohio's "Be it enacted by the general assembly of the state of Ohio," the
     colonial "Be it enacted, by his Excellency ... by the authority of the
     same," and "be it further enacted by the authority aforesaid." The
     boilerplate cutoff in step 2 catches these in a large corpus, but not in a
     small one (the enacting clause is in only 4 of the Black Code's sections).
  7. A third rule for keeping a pair: at least MIN_SHARED distinctive phrases
     in common. A passage copied into a long section shares many phrases but
     only a small share of the section, so the share and Jaccard thresholds
     miss it. Pairs are sorted by the number of shared phrases, then share_a.
  8. Optional: character shingles instead of word phrases (add "char" to the
     command). As in 01_reuse_jaccard_by_hand.py, each section is lowercased,
     stripped of punctuation and squeezed to single spaces, then cut into every
     run of K characters (spaces included). One misread or respelled letter
     ("he it" for "be it," "colour" for "color," "gaol") breaks every word phrase
     that contains the word, but only the few shingles that overlap it, so
     shingles tolerate OCR errors and spelling change. Short shingles match
     everywhere, so K defaults to 10. Shared shingles only find candidate
     pairs: a set of shingles does not record where each one came from, so it
     cannot tell borrowed passages from scattered fragments. Each candidate is
     therefore aligned with difflib (as in 04_reuse_trace_clause.py), which
     finds the text the two sections share in the same order. Blocks shorter
     than MIN_BLOCK characters (20, about 3-4 words) are ignored, so scattered
     fragments ("hundred dollars") do not add up. A pair is kept when its
     ordered shared text totals at least MIN_ALIGNED characters (100, about 17
     words), and pairs are sorted by that total. The shared_phrases column
     then holds the shared blocks in order, n_shared counts shingles,
     aligned_shared gives the ordered shared text in characters, and
     longest_shared the longest single block.
  9. Optional: normalize racial terms (add "norm" to the command). The laws'
     different words for Black people ("black or mulatto person," "negro,"
     "colored," "person of color," ...) all become one token, RACETERM, before
     phrases are made, so the run tests for shared legal structure behind
     different vocabulary. "White" is left as it is.

Usage, from the OH_SC_Text_Reuse folder. Name the corpora A then B; a number
sets the phrase length (default 5 words), or with "char" the shingle length
(default 10 characters); "norm" normalizes racial terms:
    python3 scripts/compare_oh_sc.py                        # ohio vs. jimcrow
    python3 scripts/compare_oh_sc.py 5 blackcode            # ohio vs. blackcode
    python3 scripts/compare_oh_sc.py 5 blackcode jimcrow    # blackcode vs. jimcrow
    python3 scripts/compare_oh_sc.py 5 blackcode jimcrow norm
    python3 scripts/compare_oh_sc.py 5 slaveacts blackcode  # slave acts vs. blackcode
    python3 scripts/compare_oh_sc.py char 10 slaveacts blackcode   # 10-character shingles

  With one corpus named, it is B and A is ohio. With none, A is ohio, B is jimcrow.

Saves output/compare_n<N>[_norm][_<A>_vs_<B>].csv (every kept pair, best first;
"c<K>" in place of "n<N>" for character shingles)
and the matching _boilerplate.csv. For ohio vs. jimcrow the file names have no
corpus suffix, and for ohio vs. blackcode the suffix is "_blackcode", as before.

Output columns: share_a, jaccard, n_shared, n_shared_racial, a_section, a_date,
a_part, b_section, b_date, b_title, b_county, b_tags, b_part, shared_phrases,
a_text, b_text. (a_part and b_part are the part headings recorded for the Black
Code, such as "Contracts For Service"; blank for the other corpora.)
"""

import csv
import difflib
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from common import jaccard, phrases, snippet

# --- Change these --------------------------------------------------------------

CORPORA = {"ohio": "ohio_black_laws", "blackcode": "sc_black_code_1865",
           "jimcrow": "sc_jimcrow_1877-1920", "slaveacts": "sc_slave_acts_1690-1835"}
ARGS = sys.argv[1:]
CHAR = "char" in ARGS                                 # character shingles instead of words?
_NUMBER = next((int(a) for a in ARGS if a.isdigit()), None)
N = _NUMBER if _NUMBER and not CHAR else 5           # words per phrase
K = _NUMBER if _NUMBER and CHAR else 10              # characters per shingle
NORMALIZE = "norm" in ARGS                            # normalize racial terms?
NAMED = [a for a in ARGS if a in CORPORA]
if len(NAMED) >= 2:
    A, B = NAMED[0], NAMED[1]
elif len(NAMED) == 1:
    A, B = "ohio", NAMED[0]
else:
    A, B = "ohio", "jimcrow"
MATCH = 0.10            # keep pairs with at least this Jaccard score...
SHARE_A = 0.20          # ...or at least this share of the A section's phrases...
MIN_SHARED = 5          # ...or at least this many shared phrases (word phrases)
MIN_ALIGNED = 100       # ...with shingles: or this many characters of shared text in the same order
MIN_BLOCK = 20          # shared blocks shorter than this many characters (about 3-4 words) are ignored
CANDIDATE_SHINGLES = 30 # with shingles: pairs sharing fewer shingles than this are not aligned
MAX_B_SECTIONS = 50     # phrases in more B sections than this are boilerplate
EXCLUDE_APPROPRIATIONS = True
SHOW = 15               # pairs to print

# -------------------------------------------------------------------------------

# Racial terms for Black people, and the mixed-race categories the laws list
# with them, become TOKEN. The nouns after them stay ("colored children" ->
# "raceterm children"; "black or mulatto person" -> "raceterm person"), so the
# phrasing lines up. The token is lowercase letters only, because common.py's
# phrases() keeps only lowercase letters.
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


# Enacting clauses, removed before comparison. "[bh]e" because the OCR often
# reads "be it" as "he it"; "\\s*" because it also reads "Beit".
_ = r"[\s,]+"
ENACTING = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in [
    # South Carolina, state period
    rf"(?:and{_})?[bh]e\s*it{_}(?:therefore{_}|further{_}|also{_})?enacted{_}(?:by{_})?(?:the{_}honou?rable{_})?"
    rf"(?:by{_})?the{_}senate{_}and{_}house{_}of{_}representatives(?:{_}of{_}the{_}state{_}of{_}south{_}carolina)?"
    rf"{_}now{_}met{_}and{_}sitting{_}in{_}general{_}assembly(?:{_}and{_}by{_}the{_}authority{_}of{_}the{_}same)?"
    rf"(?:{_}as{_}follows\s*:)?",
    # Ohio
    rf"(?:and{_})?[bh]e\s*it{_}(?:further{_})?enacted{_}by{_}the{_}general{_}assembly{_}of{_}the{_}state{_}of{_}ohio",
    # colonial: "Be it enacted, by his Excellency [or: the honorable William Bull] ... by the authority of the same"
    rf"(?:and{_})?[bh]e\s*it{_}(?:therefore{_}|accordingly{_}|further{_})?enacted{_}by{_}(?:his{_}excellency|the{_}honou?rable).{{0,400}}?"
    rf"by{_}the{_}authority{_}of{_}the{_}same",
    # "be it further enacted by the authority aforesaid"
    rf"(?:and{_})?[bh]e\s*it{_}(?:therefore{_}|further{_}|also{_})?enacted{_}by{_}the{_}authority{_}aforesaid",
    # what is left of a garbled South Carolina clause ("repi'csentatives now met p j and sitting")
    rf"(?:by{_})?the{_}senate{_}and{_}house{_}of{_}rep\S*(?:{_}of{_}the{_}state{_}of{_}south{_}carolina)?"
    rf"(?:{_}now{_}met(?:{_}\S{{1,3}}){{0,3}}{_}and{_}sitting{_}in{_}general{_}assembly)?"
    rf"(?:{_}and{_}(?:it{_}is{_}hereby{_}enacted{_})?by{_}the{_}authority{_}of{_}the{_}same)?",
    # the clause's second half, when a margin note or OCR noise splits it from the first
    rf"met{_}and{_}sitting{_}in{_}general{_}assembly(?:{_}and{_}by{_}the{_}authority{_}of{_}the{_}same)?(?:{_}as{_}follows\s*:?)?",
    # a bare opening left over: "be it (therefore) enacted (by the honorable)"
    rf"(?:and{_})?[bh]e\s*it{_}(?:therefore{_}|further{_}|also{_}|accordingly{_})?enacted(?:{_}by(?:{_}the{_}honou?rable)?)?",
]]


def strip_enacting(text):
    for pattern in ENACTING:
        text = pattern.sub(" ", text)
    return text


def clean_chars(text):
    """As clean() in 01_reuse_jaccard_by_hand.py: lowercase, drop punctuation,
    squeeze runs of spaces to one."""
    text = re.sub(r"[^\w\s]", "", text.lower())
    return " ".join(text.split())


def pieces(text):
    """The units compared: N-word phrases, or K-character shingles. Shingles are
    stored as Python hash numbers to save memory on the large Jim Crow corpus."""
    if not CHAR:
        return phrases(text, N)
    c = clean_chars(text)
    return {hash(c[i:i + K]) for i in range(len(c) - K + 1)}


def shingle_sequence(clean):
    """A cleaned section's shingles in order (as hash numbers)."""
    return [hash(clean[k:k + K]) for k in range(len(clean) - K + 1)]


def aligned_blocks(clean_a, seq_a, seq_b):
    """With shingles: the text two sections share in the same order, as blocks
    of at least MIN_BLOCK characters (difflib, as in 04_reuse_trace_clause.py).
    difflib compares the sequences of shingles rather than of letters: a run of
    m shingles that match in order is a shared passage m + K - 1 characters long,
    and this is far faster than comparing letters, which repeat endlessly."""
    matcher = difflib.SequenceMatcher(None, seq_a, seq_b, autojunk=False)
    return [clean_a[m.a:m.a + m.size + K - 1].strip() for m in matcher.get_matching_blocks()
            if m.size and m.size + K - 1 >= MIN_BLOCK]


PROJECT = Path(__file__).resolve().parent.parent
A_DIR = PROJECT / "data" / CORPORA[A]
B_DIR = PROJECT / "data" / CORPORA[B]
OUTPUT = PROJECT / "output"


def read_metadata(folder):
    with open(folder / "metadata.csv", newline="", encoding="utf-8") as f:
        return {row["doc_id"]: row for row in csv.DictReader(f)}


def read_parts(folder):
    """Part headings by section id, where the corpus records them (the Black Code)."""
    path = folder / "sections_metadata.csv"
    if not path.exists():
        return {}
    with open(path, newline="", encoding="utf-8") as f:
        return {row["section_id"]: row.get("part_heading", "") for row in csv.DictReader(f)}


def read_sections(folder, skip=()):
    """Every section file as {"id", "doc_id", "text", "compare"}, in file-name order."""
    out = []
    for file in sorted((folder / "sections").glob("*.txt")):
        doc_id = file.stem.rsplit("_s", 1)[0]
        if doc_id in skip:
            continue
        text = file.read_text(encoding="utf-8")
        compare = strip_enacting(text)
        out.append({"id": file.stem, "doc_id": doc_id, "text": text,
                    "compare": normalize(compare) if NORMALIZE else compare})
    return out


def appropriations(meta):
    if not EXCLUDE_APPROPRIATIONS:
        return set()
    return {d for d, r in meta.items() if r.get("appropriation_like") == "True"}


def date(meta, doc_id):
    m = meta.get(doc_id, {})
    return m.get("year") or m.get("date", "")


def main():
    if A == B:
        raise SystemExit("Name two different corpora.")
    a_meta, b_meta = read_metadata(A_DIR), read_metadata(B_DIR)
    a_parts, b_parts = read_parts(A_DIR), read_parts(B_DIR)
    a_skip, b_skip = appropriations(a_meta), appropriations(b_meta)

    a = read_sections(A_DIR, a_skip)
    b = read_sections(B_DIR, b_skip)
    UNIT = f"{K}-character shingles" if CHAR else f"{N}-word phrases"
    print(f"{A} ({CORPORA[A]}) vs. {B} ({CORPORA[B]})")
    print(f"{len(a):,} {A} sections, {len(b):,} {B} sections "
          f"({len(a_skip) + len(b_skip)} appropriation acts left out), {UNIT}"
          + (", racial terms normalized" if NORMALIZE else ""))

    # 1. Chop every section into phrases
    a_p = [pieces(s["compare"]) for s in a]
    b_p = [pieces(s["compare"]) for s in b]

    if CHAR:                   # cleaned texts, for aligning candidate pairs
        a_clean = [clean_chars(s["compare"]) for s in a]
        a_seq = [shingle_sequence(c) for c in a_clean]
        b_seq = [shingle_sequence(clean_chars(s["compare"])) for s in b]

    # 2. Boilerplate: phrases in more than MAX_B_SECTIONS sections of B
    counts = Counter(p for ps in b_p for p in ps)
    boilerplate = {p for p, c in counts.items() if c > MAX_B_SECTIONS}
    in_a = set().union(*a_p) if a_p else set()
    hits = boilerplate & in_a
    a_p = [ps - boilerplate for ps in a_p]
    b_p = [ps - boilerplate for ps in b_p]
    print(f"{len(boilerplate):,} boilerplate phrases ignored "
          f"({len(hits)} of them also occur in {A})")

    # 3. Compare each A section only with B sections sharing a phrase
    index = defaultdict(set)
    for j, ps in enumerate(b_p):
        for p in ps:
            index[p].add(j)

    pairs = []
    for i, o in enumerate(a_p):
        if not o:
            continue
        candidates = set().union(*(index[p] for p in o if p in index))
        for j in candidates:
            shared = o & b_p[j]
            score, share = jaccard(o, b_p[j]), len(shared) / len(o)
            if CHAR:
                if len(shared) < CANDIDATE_SHINGLES:
                    continue
                blocks = aligned_blocks(a_clean[i], a_seq[i], b_seq[j])
                aligned = sum(len(x) for x in blocks)
                keep = score >= MATCH or share >= SHARE_A or aligned >= MIN_ALIGNED
            else:
                blocks, aligned = sorted(shared), 0
                keep = score >= MATCH or share >= SHARE_A or len(shared) >= MIN_SHARED
            if keep:
                pairs.append((share, score, i, j, shared, aligned, blocks))

    # 4. Best first: by number of shared phrases (or, with shingles, the longest
    #    shared passage), then share of the A section
    if CHAR:
        pairs.sort(key=lambda x: (x[5], len(x[4])), reverse=True)
        rule = f"or {MIN_ALIGNED}+ characters of shared text in order"
    else:
        pairs.sort(key=lambda x: (len(x[4]), x[0]), reverse=True)
        rule = f"or {MIN_SHARED}+ shared phrases"
    print(f"{len(pairs):,} pairs kept (Jaccard >= {MATCH}, share of {A} section >= {SHARE_A}, {rule})\n")

    def show(rows, heading):
        print(heading)
        for share, score, i, j, shared, aligned, passages in rows[:SHOW]:
            tags = b_meta.get(b[j]["doc_id"], {}).get("tags", "") or b_parts.get(b[j]["id"], "")
            longest = f"{aligned} characters shared in order, " if CHAR else ""
            print(f"share of {A} {share:.2f}  jaccard {score:.2f}  {longest}{len(shared)} "
                  f"{'shingles' if CHAR else 'phrases'} ({sum(TOKEN in p for p in passages)} with {TOKEN})")
            print(f"   {a[i]['id']}  ->  {b[j]['id']}  [{tags}]")
            if CHAR:
                print(f"   \"{' ... '.join(passages)[:200]} ...\"\n")
            else:
                print(f"   \"{snippet(a[i]['compare'], shared, N)} ...\"\n")

    show(pairs, "Best pairs overall:\n")
    if NORMALIZE:
        show([x for x in pairs if any(TOKEN in p for p in x[6])],
             f"Best pairs sharing at least one phrase with {TOKEN}:\n")

    OUTPUT.mkdir(exist_ok=True)
    if (A, B) == ("ohio", "jimcrow"):
        suffix = ""
    elif A == "ohio":
        suffix = f"_{B}"
    else:
        suffix = f"_{A}_vs_{B}"
    tag = (f"c{K}" if CHAR else f"n{N}") + ("_norm" if NORMALIZE else "") + suffix
    path = OUTPUT / f"compare_{tag}.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["share_a", "jaccard", "n_shared", "n_shared_racial", "aligned_shared", "longest_shared",
                    "a_section", "a_date", "a_part",
                    "b_section", "b_date", "b_title", "b_county", "b_tags", "b_part",
                    "shared_phrases", "a_text", "b_text"])
        for share, score, i, j, shared, aligned, passages in pairs:
            m = b_meta.get(b[j]["doc_id"], {})
            w.writerow([round(share, 3), round(score, 3), len(shared),
                        sum(TOKEN in p for p in passages), aligned if CHAR else "",
                        max((len(x) for x in passages), default=0) if CHAR else "",
                        a[i]["id"], date(a_meta, a[i]["doc_id"]), a_parts.get(a[i]["id"], ""),
                        b[j]["id"], date(b_meta, b[j]["doc_id"]), m.get("title", ""),
                        m.get("county", ""), m.get("tags", ""), b_parts.get(b[j]["id"], ""),
                        " | ".join(passages), a[i]["text"].strip(), b[j]["text"].strip()])
    bpath = OUTPUT / f"compare_{tag}_boilerplate.csv"
    names = {}
    if CHAR:                     # look up the text of each boilerplate shingle
        for s in b:
            c = clean_chars(s["compare"])
            for k in range(len(c) - K + 1):
                h = hash(c[k:k + K])
                if h in boilerplate and h not in names:
                    names[h] = c[k:k + K]
    with open(bpath, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["shingle" if CHAR else "phrase", "b_sections", "in_a"])
        for p in sorted(boilerplate, key=lambda p: -counts[p]):
            w.writerow([names.get(p, p), counts[p], p in hits])
    print(f"Saved {path.relative_to(PROJECT)} and {bpath.relative_to(PROJECT)}")


if __name__ == "__main__":
    main()
