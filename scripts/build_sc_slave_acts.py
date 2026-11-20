"""
Build a text-reuse-ready corpus of South Carolina's laws on slaves and free
people of color, 1690-1835, from the Internet Archive OCR of The Statutes at
Large of South Carolina, vol. 7, ed. David J. McCord (1840), "Acts relating to
Slaves," pp. 343-474: the 41 acts and ordinances listed in the volume's table
of contents.

Usage, from the OH_SC_Text_Reuse folder:
    python3 scripts/build_sc_slave_acts.py sources/sc_statutes_v7_slave_acts_pp343-474.txt data/sc_slave_acts_1690-1835

Outputs (same layout as the other corpora):
  <output_dir>/texts/       one file per act
  <output_dir>/sections/    one file per section (s00 = preamble before Sec. I)
  <output_dir>/metadata.csv            one row per act
  <output_dir>/sections_metadata.csv   one row per section

The cleaning follows build_sc_black_code.py:
  1. Finds each act by the opening of its title. The OCR garbles many titles
     and act numbers ("No. 5T." for No. 57, "SlAVES"), so each act has its own
     search pattern below, matched in order through the file.
  2. Drops each act's title (it is in metadata.csv) up to the preamble or the
     enacting clause, and its closing signatures ("In the Council Chamber...",
     "In the Senate House...", "Assented to:").
  3. Drops running page headers ("OF SOUTH CAROLINA. 459", "STATUTES AT LARGE",
     "Acts relating to Slaves.") and "A. D. 1740." year markers.
  4. Removes margin notes where it can (a short piece set off by a wide gap, or
     a short line standing alone between blank lines). Notes the OCR ran into
     the text cannot be told apart and stay in.
  5. Drops OCR debris tokens, rejoins words hyphenated across lines.
  6. Splits each act at its Roman-numeral sections, accepting a numeral only
     if it is the next one expected (or one of the next two). Common OCR
     misreadings are mapped back (Y->V; l, i, t, r, 1 -> I). A section whose
     number cannot be read stays joined to the section before it. Acts with
     no numbered sections become a single section, s01.

The colonial acts keep their period spelling ("shew," "gaol," "colour"). That
lowers exact matches with later laws; spelling is not modernized here.
"""

import csv
import re
import sys
from pathlib import Path

src, out = Path(sys.argv[1]), Path(sys.argv[2])
raw = src.read_text(encoding="utf-8")
raw = raw.split("\n\n", 1)[1]          # drop the citation header written at download

SOURCE = ("The Statutes at Large of South Carolina, vol. 7, ed. David J. McCord (Columbia, "
          "S.C.: A. S. Johnston, 1840), pp. 343-474; Internet Archive statutesatlargeo07edit")

# act no., year, title (from the table of contents), page, pattern for the start of its title in the OCR
ACTS = [
    ("57", "1690", "An Act for the better ordering of Slaves", "343",
     r"AN\s+ACT\s+FOR\s+THE\s+BETTER\s+ORDERING\s+OF\s+S[lL]AVES"),
    ("237", "1704", "An Act for raising and enlisting such Slaves as shall be thought serviceable to this Province in time of alarms", "347",
     r"AN\s+ACT\s+FOR\s+RAISING\s+AND\s+ENLISTING"),
    ("278", "1708", "An Act for enlisting such trusty slaves as shall be thought serviceable to this Province in time of alarms", "349",
     r"AN\s+ACT\s+FOR\s+ENLISTING\s+SUCH\s+TRUSTY"),
    ("314", "1712", "An Act for the better ordering and governing of Negroes and Slaves", "352",
     r"No\.\s*314\.\s*AN\s+ACT"),
    ("344", "1714", "An additional Act to an Act entitled \"An Act for the better ordering and governing Negroes and all other Slaves\"", "365",
     r"AN\s+ADDITIONAL\s+ACT\s+TO\s+AN\s+AcT"),
    ("388", "1717", "A further additional Act to an Act entitled \"An Act for the better ordering and governing of negroes and all other slaves\"", "368",
     r"No\.\s*388\.\s*A\s+FURTHER"),
    ("476", "1722", "An Act for the better ordering and governing of Negroes and other Slaves", "371",
     r"AN\s+ACT\s+FOR\s+THE\s+BETTER\s+ORDERING\s+AND\s+GOVERNING\s+OF\s+NeGROES\s+No\.\s*476"),
    ("586", "1735", "An Act for the better ordering and governing Negroes and other Slaves", "385",
     r"AN\s+ACT\s+FOR\s+THE\s+BETTER\s+ORDERING\s+AND\s+GOVERNING\s+NeGROES\s+AND\s+No\.\s*586"),
    ("670", "1740", "An Act for the better ordering and governing Negroes and other Slaves in this Province", "397",
     r"AN\s+ACT\s+FOR\s+THE\s+BETTER\s+ORDERING\s+AND\s+GOVERNING\s+NeGROES\s+AND\s+No\.\s*670"),
    ("702", "1743", "An Act for the better security of this Province against the insurrections and other wicked attempts of Negroes and other Slaves; and for reviving and continuing an Act ... entitled \"An Act for the better ordering and governing Negroes and other Slaves in this Province\"", "417",
     r"an\s+act\s+for\s+the\s+better\s+security\s+of\s+this\s+province"),
    ("754", "1747", "An Act for giving freedom to a negro man named Arrah, late a slave belonging to Mr. Hugh Cartwright; and to confirm the freedom of all negroes ... that ... make their escape from his Majesty's enemies", "419",
     r"AN\s+ACT\s+FOR\s+GIVING\s+FREEDOM"),
    ("790", "1751", "An additional and explanatory Act to an Act ... entitled \"An Act for the better ordering and governing negroes and other slaves in this Province\"", "420",
     r"No\.\s*790"),
    ("822", "1754", "An Act to prevent the inveigling, stealing and carrying away negroes and other slaves in this Province", "426",
     r"No\.\s*822\.\s*AN\s+ACT"),
    ("1025", "1776", "An Ordinance to direct the manner of procuring negroes to be employed in the public service", "428",
     r"No\.\s*1025\."),
    ("1372", "1787", "An Ordinance to impose a penalty on any person who shall import into this State any Negroes, contrary to the Instalment Act", "430",
     r"No\.\s*1372\."),
    ("1389", "1788", "An Act authorizing persons having in their possession, or taking up, runaway slaves, to send them to the gaols of the districts where they may be apprehended", "430",
     r"No\.\s*1389\."),
    ("1544", "1792", "An Act to prohibit the importation of slaves from Africa, or other places beyond sea, into this State, for two years; and also to prohibit the importation or bringing in slaves, or negroes, mulattoes, Indians, Moors or mestizoes, bound for a term of years, from any of the United States", "431",
     r"AN\s+ACT\s+TO\s+PROHIBIT\s+THE\s+IMPORTATION\s+OF\s+S[lL]AVES\s+FROM"),
    ("1605", "1794", "An Act to revive and extend [the Act of 1792 prohibiting the importation of slaves]", "433",
     r"AN\s+ACT\s+TO\s+REVIVE\s+AND\s+EXTEND"),
    ("1645", "1796", "An Act to prohibit the importation of negroes, until the first day of January, one thousand seven hundred and ninety-nine", "434",
     r"No\.\s*1645\."),
    ("1658", "1796", "An Act more effectually to prevent shop-keepers, traders, and others, from dealing with slaves having no tickets from their masters", "434",
     r"No\.\s*1658\."),
    ("1696", "1798", "An Act to revive and extend [the Act of 1796 prohibiting the importation of negroes]", "435",
     r"AN\s+ACT\s+TO\s+REVIVE\s+AND\s+EXTEND"),
    ("1710", "1799", "An Act to protect slaves belonging to third persons, from being distrained for rent not due by them", "435",
     r"AN\s+ACT\s+TO\s+PROTECT\s+Slaves"),
    ("1740", "1800", "An Act further to revive and extend [the Act prohibiting the importation of negroes]", "436",
     r"No\.\s*1740\.\s*AN"),
    ("1744", "1800", "An Act to prevent negro slaves and other persons of colour, from being brought into or entering this State", "436",
     r"No\.\s*[I1]744"),
    ("1745", "1800", "An Act respecting slaves, free negroes, mulattoes and mestizoes; for enforcing the more punctual performance of patrol duty; and to impose certain restrictions on the emancipation of slaves", "440",
     r"No\.\s*1745\.\s*AN"),
    ("1756", "1801", "An Act supplementary to an Act entitled \"An Act to prevent negro slaves and persons of colour from being brought into or entering this State\"", "444",
     r"No\.\s*1756\."),
    ("1787", "1802", "An Act to alter and amend an Act entitled \"An Act to prevent negro slaves and persons of colour from being brought into or entering this State;\" and also, an Act supplementary to the Act aforesaid", "447",
     r"AN\s+ACT\s+TO\s+ALTER\s+AND\s+AMEND\s+AN\s+AcT\s+ENTITLED"),
    ("1811", "1803", "An Act to alter part of an Act entitled \"An Act respecting slaves, free negroes, mulattoes and mestizoes ...\"", "448",
     r"No\.\s*1811\."),
    ("1814", "1803", "An Act to alter and amend the several Acts respecting the importation or bringing into this State, from beyond seas, or elsewhere, negroes and other persons of colour", "449",
     r"AN\s+ACT\s+TO\s+ALTER\s+AND\s+AMEND\s+THE\s+SEVERAL"),
    ("2107", "1816", "An Act to prohibit the importation of slaves into this State from any of the United States", "451",
     r"AN\s+ACT\s+TO\s+PROHIBIT\s+THE\s+IMPORTATION\s+OF\s+S[lL]a?VES\s+INTO"),
    ("2135", "1817", "An Act to increase the penalties which are now by law inflicted on persons who deal or trade with negro slaves, without a license or ticket from their master or owner, or the person having charge of them", "454",
     r"No\.?\s*2135"),
    ("2141", "1817", "An Act to amend an Act entitled \"An Act to prohibit the importation of slaves into this State from any of the United States\"", "455",
     r"AN\s+ACT\s+TO\s+AMEND\s+AN\s+AcT\s+ENTITLED\s+\"\s*An\s+AcT\s+TO\s+PROHIBIT"),
    ("2195", "1818", "An Act to repeal the Act passed at December Session, 1816, and the amendatory Act thereto, ... prohibiting and restricting the bringing of Negroes into this State from the sister States", "458",
     r"No\.\s*2195\."),
    ("2236", "1820", "An Act to restrain the emancipation of slaves, and to prevent free persons of colour from entering into this State", "459",
     r"AN\s+ACT\s+TO\s+RESTRAIN"),
    ("2254", "1821", "An Act to provide more effectually against the offence of harbouring negro or other slaves", "460",
     r"No\.\s*2254\."),
    ("2277", "1822", "An Act for the better regulation and government of free negroes and persons of colour", "461",
     r"AN\s+ACT\s+FOR\s+THE\s+BETTER\s+REGULATION"),
    ("2319", "1823", "An Act the more effectually to prohibit free negroes and persons of colour from entering into this State", "463",
     r"AN\s+ACT\s+THE\s+MOR[EK]\s+EFFECTUALLY"),
    ("2361", "1825", "An Act to amend \"An Act the more effectually to prohibit free negroes and persons of colour from entering into this State\"", "466",
     r"No\.\s*236[1lL]"),
    ("2528", "1831", "An Act concerning free persons of colour and slaves", "467",
     r"AN\s+ACT\s+CONCERNING\s+Free"),
    ("2639", "1834", "An Act to amend the laws in relation to slaves and free persons of colour", "468",
     r"No\.\s*2639\."),
    ("2653", "1835", "An Act more effectually to prevent free negroes and other persons of color from entering into this State", "470",
     r"No\.\s*2653\."),
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
# A numeral followed by a period, or with no period when "Be it" follows
# ("L Be it therefore enacted" is the OCR's reading of "I. Be it therefore enacted").
CANDIDATE = re.compile(r"(?<![\w-])([IVXLCYH][IVXLCYlitrT1H]{0,7})"
                       r"(?:[.,](?=\s)|\s+(?=(?:And\s+)?B[Ee]\s*[Ii]t\b))")


def read_numeral(token, want):
    """The OCR also reads II as "H" and, at the start of an act, I as "L"."""
    if token == "L" and want == 1:
        return "I"
    return token.replace("H", "II").translate(OCR_FIX)

# ---- Line cleaning ------------------------------------------------------------
HEADER = re.compile(r"^\s*(OF\s+SOUTH\s+CAROLINA\.?\s+\d+|\d{3}\s+STATUTES\s+\w+\s+LARGE|"
                    r"STATUTES\s+AT\s+LARGE|\d{3}|VOL\.?\s*VII\W.*|Acts\s+rel\w+\s+to\s+Slaves\.?)\s*$",
                    re.IGNORECASE)
YEAR = r"A\s*[.,]\s*D\s*[.,]?\s*[0-9A-Za-z%().?\-]{2,8}\.?\^?"
YEAR_START = re.compile(rf"^\s*{YEAR}\s*")
YEAR_END = re.compile(rf"\s+{YEAR}.*$")
DEBRIS = re.compile(r"\S*[\^~■°«»•*{}\\|]\S*|(?<!\w)['\"]{2,}\S*")
CAPS_HEADING = re.compile(r"^[A-Z][A-Z ,'’—\-]+[A-Z][.,]?$")


def clean_lines(text):
    kept = []
    for line in text.split("\n"):
        if HEADER.match(line) or re.match(r"^\s*No\.?\s*\S{2,6}\.?\s*$", line):
            kept.append("")
            continue
        line = YEAR_START.sub("", line)
        line = YEAR_END.sub("", line)
        parts = [p for p in re.split(r" {3,}", line.strip()) if p.strip()]
        if len(parts) in (2, 3):
            if len(parts[0].split()) <= 4 and len(parts[1].split()) > 4:
                parts = parts[1:]               # margin note at the start (even pages)
            if len(parts) > 1 and len(parts[-1].split()) <= 4 and len(parts[-2].split()) > 4:
                parts = parts[:-1]              # margin note at the end (odd pages)
        line = DEBRIS.sub(" ", "  ".join(parts))
        kept.append(re.sub(r"\s+", " ", line).strip())
    final = []
    for k, line in enumerate(kept):
        prev_blank = k == 0 or not kept[k - 1]
        next_blank = k == len(kept) - 1 or not kept[k + 1]
        prev_text = next((x for x in reversed(kept[:k]) if x), "")
        if (line and len(line.split()) <= 3 and prev_blank and next_blank
                and not prev_text.endswith("-")):
            final.append("")                    # short line alone: a margin note
            continue
        if line and CAPS_HEADING.match(line) and not re.fullmatch(r"[IVXLC]+[.,]?", line):
            final.append("")                    # stray all-capitals line (title residue)
            continue
        final.append(line)
    return final


def join(lines):
    text = "\n".join(lines)
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)   # words hyphenated across lines
    return re.sub(r"\s+", " ", text).strip()


def split_sections(text):
    """[(number, text)] and the numbers below the highest found that are missing."""
    found, want = [], 1
    for m in CANDIDATE.finditer(text):
        value = read_numeral(m.group(1), want)
        for step in range(3):
            if value == roman(want + step):
                found.append((want + step, m.start()))
                want += step + 1
                break
    numbers = [n for n, _ in found]
    if not found:
        return [(1, text)], []
    missing = [n for n in range(1, max(numbers) + 1) if n not in numbers]
    starts = [0] + [s for _, s in found] + [len(text)]
    labels = [0] + numbers
    sections = []
    for label, a, b in zip(labels, starts[:-1], starts[1:]):
        body = text[a:b].strip()
        if body:
            sections.append((label, body))
    return sections, missing


# ---- Find the acts in order and write the corpus ---------------------------------
starts, pos = [], 0
for no, year, title, page, pattern in ACTS:
    m = re.compile(pattern).search(raw, pos)
    if not m:
        raise SystemExit(f"Could not find the start of Act No. {no} ({year}).")
    starts.append(m.start())
    pos = m.end()
starts.append(len(raw))

for d in ("texts", "sections"):
    (out / d).mkdir(parents=True, exist_ok=True)

act_rows, sec_rows = [], []
for (no, year, title, page, _), a, b in zip(ACTS, starts[:-1], starts[1:]):
    chunk = raw[a:b]
    # drop the closing signatures
    chunk = re.split(r"In\s+the\s+(?:Council\s+Chamber|Senate\s+House|Cowndl\s+Chamber)|"
                     r"Assented\s+to\s*:|\n[A-Z][A-Za-z.\s]{3,40},\s+Speaker", chunk)[0]
    # drop the title, up to the preamble or the enacting/ordaining clause
    parts = re.split(r"(?=\bWHEREAS\b|\bWhereas\b|\bFORASMUCH\b|\bForasmuch\b|"
                     r"(?<![\w-])[IL1]\.?\s+(?:And\s+)?B[Ee]\s*[Ii]t\b|"
                     r"\bAnd\s+be\s+it\b|\bB[Ee]\s*[Ii]t\s+(?:therefore\s+|further\s+)?(?:enacted|ordained))",
                     chunk, maxsplit=1)
    chunk = parts[-1]
    text = join(clean_lines(chunk))
    sections, missing = split_sections(text)
    doc_id = f"sc_{year}_act{no}"
    plain = " ".join(s for _, s in sections)
    (out / "texts" / f"{doc_id}.txt").write_text(plain + "\n", encoding="utf-8")
    for label, body in sections:
        sid = f"{doc_id}_s{label:02d}"
        (out / "sections" / f"{sid}.txt").write_text(body + "\n", encoding="utf-8")
        sec_rows.append({"section_id": sid, "doc_id": doc_id, "section": label,
                         "roman": roman(label) if label else "preamble",
                         "part_heading": "", "n_words": len(body.split())})
    numbered = [s for s in sections if s[0]]
    act_rows.append({"doc_id": doc_id, "state": "South Carolina", "act_no": no, "year": year,
                     "date": year, "title": title, "page": page,
                     "sections_found": len(numbered),
                     "numbers_not_found": " ".join(roman(n) for n in missing),
                     "n_words": len(plain.split()), "source": SOURCE})
    print(f"{year} No. {no:>4}: {len(numbered):3} sections, {len(plain.split()):6,} words"
          + (f"; numbers not found: {' '.join(roman(n) for n in missing)}" if missing else ""))

with open(out / "metadata.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=act_rows[0].keys()); w.writeheader(); w.writerows(act_rows)
with open(out / "sections_metadata.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=sec_rows[0].keys()); w.writeheader(); w.writerows(sec_rows)
total = sum(r["n_words"] for r in act_rows)
print(f"{len(act_rows)} acts, {len(sec_rows)} section files, {total:,} words")
