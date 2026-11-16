"""
Build a text-reuse-ready corpus of South Carolina acts (1877-1920) flagged as
likely Jim Crow laws by On the Books in South Carolina (Boyd et al. 2025,
https://scholarcommons.sc.edu/lib_facpub/64/, CC BY-NC-SA 4.0).

Usage: python3 build_sc_corpus.py <acts_txt> <output_dir> [acts_list_csv]

Outputs (same layout as the Ohio corpus):
  <output_dir>/texts/      one file per act (title + body)
  <output_dir>/sections/   one file per section (s00 = preamble/title material)
  <output_dir>/metadata.csv
"""
import csv, re, sys
from pathlib import Path

src, out = Path(sys.argv[1]), Path(sys.argv[2])
csv_path = Path(sys.argv[3]) if len(sys.argv) > 3 else None

raw = src.read_text(encoding="utf-8").replace("\r", "").replace(" ", " ")

def clean(s):
    s = re.sub(r"(\w)- (\w)", r"\1\2", s)           # "Trus- tees" -> "Trustees"
    s = re.sub(r"\s+([,.;:)])", r"\1", s)            # "Carolina , That" -> "Carolina, That"
    s = re.sub(r"\(\s+", "(", s)
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()

SEC_START = re.compile(r"^(SECTION|Section|SEC\.?|Sec\.?|§)\s*\d+\b")

records = re.split(r"(?m)^(?=Year:\d{4}\s+ACT NO\.:)", raw)[1:]
acts, seen = [], {}
for rec in records:
    lines = rec.split("\n")
    m = re.match(r"Year:(\d{4})\s+ACT NO\.:\s*(\S+)", lines[0])
    year, actno = m.group(1), m.group(2)
    key = (year, actno)
    seen[key] = seen.get(key, 0) + 1
    suffix = "" if seen[key] == 1 else "_" + "abcdefghij"[seen[key] - 1]
    doc_id = f"sc_{year}_act{actno}{suffix}"

    body = [clean(l) for l in lines[1:] if l.strip()]
    title = body[0] if body else ""
    sections, cur = [], []
    for l in body:
        if SEC_START.match(l) and cur:
            sections.append(" ".join(cur)); cur = []
        cur.append(l)
    if cur:
        sections.append(" ".join(cur))
    # if the first chunk is only title/preamble, keep it as s00
    if sections and not SEC_START.match(sections[0]):
        sections = [sections[0]] + sections[1:]
        start = 0
    else:
        start = 1
    full = "\n".join(body)
    n_items = sum(1 for l in body if re.match(r"^(Item\b|\$|Total\b)", l))
    acts.append(dict(doc_id=doc_id, year=year, act_no=actno, title=title,
                     n_sections=len(sections), n_words=len(full.split()),
                     appropriation_like=(n_items >= 10 or "APPROPRIAT" in title.upper()),
                     _full=full, _sections=sections, _start=start, _key=key,
                     _occ=seen[key]))

# ---- optional join with the project's act list (county, tags, date) --------
if csv_path:
    rows = list(csv.reader(csv_path.read_text(encoding="utf-8-sig").replace("\r", "").splitlines()))
    hdr_i = next(i for i, r in enumerate(rows) if r[:3] == ["title", "description", "volume"])
    hdr = rows[hdr_i]
    meta, occ = {}, {}
    for r in rows[hdr_i + 1:]:
        if not any(r):
            continue
        d = dict(zip(hdr, r))
        y = re.search(r"\d{4}", d.get("date", "") or d.get("title", ""))
        if not y:
            continue
        k = (y.group(0), d.get("act", "").strip())
        occ[k] = occ.get(k, 0) + 1
        meta[(k, occ[k])] = d
    for a in acts:
        d = meta.get((a["_key"], a["_occ"]), {})
        a["date"] = d.get("date", "")
        a["county"] = d.get("county", "")
        a["tags"] = d.get("tags", "")
        a["volume"] = d.get("volume", "")

for d in ("texts", "sections", "duplicates"):
    (out / d).mkdir(parents=True, exist_ok=True)
# The source file repeats some acts (a second OCR of the same act, mostly
# 1879 and 1906-07). Keep the first copy; set later copies aside.
for a in acts:
    a["duplicate_of"] = f"sc_{a['_key'][0]}_act{a['_key'][1]}" if a["_occ"] > 1 else ""
    if a["duplicate_of"]:
        (out / "duplicates" / f"{a['doc_id']}.txt").write_text(a["_full"] + "\n", encoding="utf-8")
        continue
    (out / "texts" / f"{a['doc_id']}.txt").write_text(a["_full"] + "\n", encoding="utf-8")
    for k, s in enumerate(a["_sections"], a["_start"]):
        (out / "sections" / f"{a['doc_id']}_s{k:02d}.txt").write_text(s + "\n", encoding="utf-8")

fields = [f for f in acts[0] if not f.startswith("_")]
with open(out / "metadata.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields + ["state", "source"], extrasaction="ignore")
    w.writeheader()
    for a in acts:
        w.writerow({**a, "state": "South Carolina",
                    "source": "On the Books in South Carolina Corpus (Boyd et al. 2025), https://scholarcommons.sc.edu/lib_facpub/64/"})

uniq = [a for a in acts if not a["duplicate_of"]]
n_sec = sum(len(a["_sections"]) for a in uniq)
n_app = sum(a["appropriation_like"] for a in uniq)
matched = sum(1 for a in uniq if a.get("tags") or a.get("county") or a.get("date"))
print(f"{len(uniq)} unique acts ({len(acts) - len(uniq)} dupes set aside), "
      f"{n_sec} section files, {n_app} appropriation-like acts")
if csv_path:
    print(f"{matched} acts matched to CSV metadata")
