"""
Build a text-reuse-ready corpus of South Carolina's December 1865 "Black Code"
from the Internet Archive OCR of The Statutes at Large of South Carolina, vol. 13
(1875), pp. 245-285: Acts No. 4730-4733.

Usage, from the OH_SC_Text_Reuse folder:
    python3 scripts/build_sc_black_code.py sources/sc_statutes_v13_1865_black_code_pp245-285.txt data/sc_black_code_1865

Outputs (same layout as the other corpora):
  <output_dir>/texts/       one file per act
  <output_dir>/sections/    one file per section (s00 = preamble before Sec. I)
  <output_dir>/metadata.csv            one row per act
  <output_dir>/sections_metadata.csv   one row per section (number, part heading, words)

What the script does to the OCR, in order:
  1. Cuts the file into the four acts and drops each act's closing signature block.
  2. Drops running page headers ("OF SOUTH CAROLINA. 245", "270 STATUTES AT LARGE",
     "Vol. 13-17") and the "A. D. 1865." year markers.
  3. Removes margin notes where it can. The notes sit at the start of lines on
     even pages and the end of lines on odd pages, set off by a wide gap (3+
     spaces; the OCR puts 2 spaces between ordinary words). A short piece
     (4 words or fewer) on the far side of a wide gap is dropped, as is a short
     line standing alone between blank lines. Notes the OCR ran into the text
     with a normal gap cannot be told apart and stay in.
  4. Drops tokens that are OCR debris (containing ^ ~ ° and similar marks).
  5. Records the all-capitals part headings ("HUSBAND AND WIFE", "VAGRANCY AND
     IDLENESS") as section metadata, and takes them out of the text.
  6. Rejoins words hyphenated across lines and squeezes the spacing.
  7. Splits each act at its Roman-numeral section numbers. The OCR misreads
     some numerals ("YI." for VI, "Vill." for VIII, "XCTI." for XCII), so
     common misreadings are mapped back (Y->V; l, i, t, r, 1 -> I), and a
     numeral is accepted only if it is the next one expected (or one of the
     next two, when a numeral is too damaged to read). A section whose number
     is unreadable stays joined to the section before it; metadata.csv lists
     these for each act.
"""

import csv
import re
import sys
from pathlib import Path

src, out = Path(sys.argv[1]), Path(sys.argv[2])
raw = src.read_text(encoding="utf-8")
raw = raw.split("\n\n", 1)[1]          # drop the citation header written at download

SOURCE = ("The Statutes at Large of South Carolina, vol. 13 (Columbia, S.C.: Republican "
          "Printing Co., 1875), pp. 245-285; Internet Archive statutesatlargeo13repu")

ACTS = [  # act no., date ratified, title, page, expected sections, opening words in the OCR
    ("4730", "1865-12-19", "An Act preliminary to the legislation induced by the emancipation of slaves",
     "245", 5, r"AN\s+ACT\s+Preliminary"),
    ("4731", "1865-12-19", "An Act to amend the criminal law", "246", 32,
     r"AN\s+ACT\s+TO\s+Amend\s+the\s+Criminal"),
    ("4732", "1865-12-19", "An Act to establish District Courts", "254", 49,
     r"No\.\s+4732\.\s+AN\s+ACT\s+to\s+Establish\s+District"),
    ("4733", "1865-12-21", "An Act to establish and regulate the domestic relations of persons "
     "of color, and to amend the law in relation to paupers and vagrancy", "269", 99,
     r"AN\s+ACT\s+TO\s+Establish\s+and\s+Regulate"),
]

# ---- Roman numerals ---------------------------------------------------------
def roman(n):
    vals = [(100, "C"), (90, "XC"), (50, "L"), (40, "XL"), (10, "X"), (9, "IX"),
            (5, "V"), (4, "IV"), (1, "I")]
    s = ""
    for v, r in vals:
        while n >= v:
            s, n = s + r, n - v
    return s

OCR_FIX = str.maketrans({"Y": "V", "l": "I", "i": "I", "t": "I", "r": "I", "1": "I", "T": "I"})
CANDIDATE = re.compile(r"(?<![\w-])([IVXLCY][IVXLCYlitrT1]{0,7})[.,](?=\s)")

# ---- Line cleaning ------------------------------------------------------------
HEADER = re.compile(r"^\s*(OF\s+SOUTH\s+CAROLINA\.?\s+\d+|\d{3}\s+STATUTES\s+\w+\s+LARGE|"
                    r"STATUTES\s+AT\s+LARGE|\d{3}|Vol\.\s*13\W+\d+)\s*$")
YEAR = r"A\s*[.,]\s*D\s*[.,]?\s*[0-9A-Za-z%().?\-]{2,8}\.?\^?"
YEAR_START = re.compile(rf"^\s*{YEAR}\s*")
YEAR_END = re.compile(rf"\s+{YEAR}.*$")
DEBRIS = re.compile(r"\S*[\^~■°«»•*{}\\|]\S*|(?<!\w)['\"]{2,}\S*")
CAPS_HEADING = re.compile(r"^[A-Z][A-Z ,'’—\-]+[A-Z][.,]?$")


def clean_lines(text):
    lines = text.split("\n")
    kept = []
    for k, line in enumerate(lines):
        if HEADER.match(line) or re.match(r"^\s*No\.\s+47\d\d\.?\s*$", line):
            kept.append("")
            continue
        line = re.sub(r"No\.\s+47\d\d\.?", " ", line)
        line = YEAR_START.sub("", line)
        line = YEAR_END.sub("", line)
        parts = [p for p in re.split(r" {3,}", line.strip()) if p.strip()]
        # Only lines with one or two wide gaps are treated as text + margin note.
        # A line with more wide gaps is loosely set body text (p. 248), left whole.
        if len(parts) in (2, 3):
            if len(parts[0].split()) <= 4 and len(parts[1].split()) > 4:
                parts = parts[1:]               # margin note at the start (even pages)
            if len(parts) > 1 and len(parts[-1].split()) <= 4 and len(parts[-2].split()) > 4:
                parts = parts[:-1]              # margin note at the end (odd pages)
        line = DEBRIS.sub(" ", "  ".join(parts))
        line = re.sub(r"\s+", " ", line).strip()
        kept.append(line)
    # short lines standing alone between blank lines are margin notes
    final = []
    for k, line in enumerate(kept):
        prev_blank = k == 0 or not kept[k - 1]
        next_blank = k == len(kept) - 1 or not kept[k + 1]
        prev_text = next((x for x in reversed(kept[:k]) if x), "")
        if (line and len(line.split()) <= 3 and prev_blank and next_blank
                and not prev_text.endswith("-") and not CAPS_HEADING.match(line)):
            final.append("")
            continue
        if line and CAPS_HEADING.match(line) and not re.fullmatch(r"[IVXLC]+[.,]?", line):
            final.append(f"@@{line.rstrip('.,')}@@")
            continue
        final.append(line)
    return final


def join(lines):
    text = "\n".join(lines)
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)   # words hyphenated across lines
    return re.sub(r"\s+", " ", text).strip()


def split_sections(text, expected):
    """[(number, heading, text)], plus the numbers that could not be found."""
    found, pos, want = [], 0, 1
    for m in CANDIDATE.finditer(text):
        if want > expected:
            break
        value = m.group(1).translate(OCR_FIX)
        for step in range(3):                    # the next numeral, or one of the two after
            if value == roman(want + step):
                found.append((want + step, m.start()))
                want += step + 1
                break
    sections, missing = [], []
    numbers = [n for n, _ in found]
    missing = [n for n in range(1, expected + 1) if n not in numbers]
    starts = [0] + [s for _, s in found] + [len(text)]
    labels = [0] + numbers
    heading = ""
    for label, a, b in zip(labels, starts[:-1], starts[1:]):
        chunk = text[a:b]
        heads = re.findall(r"@@(.+?)@@", chunk)
        if heads and chunk.strip().startswith("@@"):
            heading = heads[0]
        body = re.sub(r"@@.+?@@", " ", chunk)
        body = re.sub(r"\s+", " ", body).strip()
        if body:
            sections.append((label, heading, body))
        if heads:
            heading = heads[-1]
    return sections, missing


# ---- Cut the acts and write the corpus ------------------------------------------
starts = [re.search(pattern, raw).start() for *_, pattern in ACTS] + [len(raw)]
for d in ("texts", "sections"):
    (out / d).mkdir(parents=True, exist_ok=True)

act_rows, sec_rows = [], []
for (no, date, title, page, expected, _), a, b in zip(ACTS, starts[:-1], starts[1:]):
    chunk = raw[a:b]
    chunk = re.split(r"In\s+the\s+Senate\s+House", chunk)[0]    # drop the signature block
    # drop the act's own title (it is in metadata) up to the enacting clause or preamble
    chunk = re.split(r"(?=Whereas|Be\s+it\s+enacted|I\.\s+Be\s+it\s+enacted)", chunk, maxsplit=1)[-1]
    text = join(clean_lines(chunk))
    sections, missing = split_sections(text, expected)
    doc_id = f"sc_1865_act{no}"
    plain = " ".join(s for _, _, s in sections)
    (out / "texts" / f"{doc_id}.txt").write_text(plain + "\n", encoding="utf-8")
    for label, heading, body in sections:
        sid = f"{doc_id}_s{label:02d}"
        (out / "sections" / f"{sid}.txt").write_text(body + "\n", encoding="utf-8")
        sec_rows.append({"section_id": sid, "doc_id": doc_id, "section": label,
                         "roman": roman(label) if label else "preamble",
                         "part_heading": heading.title() if heading else "",
                         "n_words": len(body.split())})
    act_rows.append({"doc_id": doc_id, "state": "South Carolina", "act_no": no, "date": date,
                     "title": title, "page": page, "sections_expected": expected,
                     "sections_found": len([s for s in sections if s[0]]),
                     "numbers_not_found": " ".join(roman(n) for n in missing),
                     "n_words": len(plain.split()), "source": SOURCE})
    print(f"Act {no}: {len([s for s in sections if s[0]])}/{expected} sections, "
          f"{len(plain.split()):,} words; numbers not found: "
          f"{' '.join(roman(n) for n in missing) or 'none'}")

with open(out / "metadata.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=act_rows[0].keys()); w.writeheader(); w.writerows(act_rows)
with open(out / "sections_metadata.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=sec_rows[0].keys()); w.writeheader(); w.writerows(sec_rows)
print(f"{len(sec_rows)} section files written to {out / 'sections'}")
