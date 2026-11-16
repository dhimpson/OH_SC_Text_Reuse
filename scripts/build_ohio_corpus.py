"""
Build a text-reuse-ready corpus of Ohio Black Laws from the LOC OCR of
B.W. Arnett & J.A. Brown, "The Black Laws!" (1886), pp. 29-40.

Usage: python3 build_ohio_corpus.py <arnett_txt> <output_dir>

Outputs:
  <output_dir>/texts/      one file per law (full text)
  <output_dir>/sections/   one file per section of each law
  <output_dir>/metadata.csv
  <output_dir>/corrections_log.csv  every OCR fix and line-break join applied
"""
import csv, re, sys
from pathlib import Path

src, out = Path(sys.argv[1]), Path(sys.argv[2])
raw = src.read_text(encoding="utf-8")

# ---- 1. Drop header, page markers, page numbers, scan noise --------------
lines = raw.splitlines()
lines = lines[lines.index(next(l for l in lines if l.startswith("=====SCAN"))):]
junk = re.compile(r"^(=====SCAN.*|\d{1,2}|i I'jwnri.*|I i)$")
lines = [l.strip() for l in lines if not junk.match(l.strip())]

# ---- 2. Rejoin words the OCR split across lines (hyphens were dropped) ----
# Explicit list, checked by hand against the scans, so genuine two-word
# phrases ("qui tam", "one half", "school house") are left alone.
SPLITS = ["certifi|cate", "obtain|ing", "Pro|vided", "pro|vided", "em|ploy",
          "mu|latto", "pre|vent", "per|son", "per|sons", "emi|grate",
          "town|ship", "town|ships", "de|livery", "resi|dent", "more|over",
          "insti|tuted", "con|trary", "con|tested", "attend|ing", "pow|ers",
          "dis|trict", "tax|payers", "num|ber", "com|mon", "privil|eges",
          "appli|cation", "per|mit", "sev|eral", "trus|tees", "rela|tion",
          "disabil|ities", "enumera|tion", "educa|tional", "edu|cation",
          "educa|tion", "afore|said", "herein|before", "dol|lars", "con-|ferreed", "Pro|vided"]
log = []
text = "\n".join(lines)
for s in dict.fromkeys(SPLITS):
    a, b = s.split("|")
    pat = re.compile(rf"\b{re.escape(a)}\n{re.escape(b)}\b")
    n = len(pat.findall(text))
    if n:
        text = pat.sub(a.rstrip("-") + b, text)
        log.append(("line-break join", f"{a} / {b}", a.rstrip("-") + b, n))

# ---- 3. Fix clear OCR errors (each checked against the page image) -------
FIXES = {"an}'": "any", "everv": "every", "sbe": "she", "resid,": "reside,",
         "court or record": "court of record", "elewhere": "elsewhere",
         "enjoved": "enjoyed", "tor the": "for the", "goverened": "governed",
         "countv": "county", "ihis": "this", "oft'": "off", "meet ngs": "meetings",
         "conferreed": "conferred", "anv ": "any ", "now' are": "now are",
         "the}'": "they", "9tii": "9th", "69S7": "6987", "Alrican": "African",
         "ot pure": "of pure", "be lined": "be fined", "knowing!}-": "knowingly",
         "required 10": "required to", "tor colored": "for colored",
         "ander the": "under the", "rais'ed": "raised", "■of": "of", "•not": "not",
         "q/ the": "of the", "Fol. 47": "Vol. 47"}
for bad, good in FIXES.items():
    n = text.count(bad)
    if n:
        text = text.replace(bad, good)
        log.append(("OCR fix", bad, good, n))

# ---- 4. Cut out each law by start/end anchors ------------------------------
# Excludes Arnett's commentary, Townshend's 1886 letter, Gov. Bebb's message,
# signatures/dates, the 1886 repeal bill, and the House vote.
LAWS = [
 ("ohio_1802_constitution_proposed", "1802", "Proposed constitutional section (1802 convention)",
  "No negro or mulatto shall ever", "not excepted by this constitution.",
  "Arnett says this section was passed; verify against the adopted 1802 constitution before treating it as law."),
 ("ohio_1804_regulate_black_mulatto", "1804-01-05", "An act to regulate black and mulatto persons",
  "Section 1. Be it enacted", "liable to the action of the\nparty injured.", ""),
 ("ohio_1807_amend_regulate", "1807-01-25", "Act amending 'An act to regulate black and mulatto persons'",
  "Sec. 1. Be it enacted by the general assembly of the state of\nOhio, That no negro",
  "day of April next.", "Includes Sec. 4 barring testimony against white persons."),
 ("ohio_1848_colored_schools", "1848-02-24", "Act establishing schools for black and colored persons",
  "Sec. 1. Be it enacted by the general assembly of the state of\nOhio, That all such property",
  "except as herein provided.", "Arnett cites Vol. 46, pp. 81-83; repealed Feb. 10, 1849."),
 ("ohio_1849_separate_districts_repeal", "1849-02-10", "Act creating separate school districts and repealing the 1804/1807 acts",
  "Sec. 1. Be it enacted by the general assembly of the state of\nOhio, That the trustees",
  "unless the court shall otherwise\ndirect.", "Arnett cites Vol. 47, pp. 17-18; repealed Mar. 14, 1853. Sec. 6 is mostly a repeal clause."),
 ("ohio_1853_school_sec31", "1853-03-14", "School law, Sec. 31 (separate schools)",
  "Sec. 31. The township boards of education in this State",
  "under the direction of the township board.", "One section of a larger school act."),
 ("ohio_1861_intermarriage", "1861-01-31", "Intermarriage prohibition (later Rev. Stat. secs. 6987-6988)",
  "Sec. 6987.", "three months, or both.\nJanuary", "Section numbers are Revised Statutes numbers as Arnett prints them."),
 ("ohio_1864_school_sec31_amended", "1864-03-18", "Amendment of school law Sec. 31 (separate schools)",
  "Sec. 4. That section thirty-one", "direction of the board.\nMarch 18", ""),
 ("ohio_1878_sec4008", "1878", "Rev. Stat. Sec. 4008 (separate schools)",
  "Sec. 4008. When, in the judgment", "the school house is situate.",
  "Date taken from Arnett's heading."),
]

def cut(start, end):
    i = text.index(start)
    j = text.index(end, i) + len(end)
    chunk = text[i:j]
    # trailing date line used only as an anchor
    chunk = re.sub(r"\n(January|March \d+)$", "", chunk)
    return re.sub(r"\s*\n\s*", " ", chunk).strip()

(out / "texts").mkdir(parents=True, exist_ok=True)
(out / "sections").mkdir(parents=True, exist_ok=True)
rows = []
for doc_id, date, title, start, end, note in LAWS:
    body = cut(start, end)
    (out / "texts" / f"{doc_id}.txt").write_text(body + "\n", encoding="utf-8")
    secs = [s.strip() for s in re.split(r"(?=\b(?:Section|Sec\.) \d+\.)", body) if s.strip()]
    for k, s in enumerate(secs, 1):
        (out / "sections" / f"{doc_id}_s{k:02d}.txt").write_text(s + "\n", encoding="utf-8")
    rows.append({"doc_id": doc_id, "state": "Ohio", "date": date, "title": title,
                 "n_sections": len(secs), "n_words": len(body.split()),
                 "source": "Arnett & Brown, The Black Laws! (1886), pp. 29-40; LOC https://www.loc.gov/item/91898104/",
                 "note": note})

with open(out / "metadata.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
with open(out / "corrections_log.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["type", "found", "replaced_with", "count"]); w.writerows(log)

for r in rows:
    print(f"{r['doc_id']:42} {r['n_sections']:3} sections {r['n_words']:5} words")
print(f"{len(log)} corrections logged")
