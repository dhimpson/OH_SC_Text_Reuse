#!/usr/bin/env python3
"""
See the text reuse: side-by-side passages with the shared wording highlighted
=============================================================================

Turns a results file from compare_oh_sc.py into a web page. For each matched
pair, the two sections appear side by side, with every word that belongs to a
shared phrase highlighted. Long sections are cut down to the highlighted
passages plus some words of context on either side.

Usage, from the OH_SC_Text_Reuse folder:
    python3 scripts/view_matches.py output/compare_n5_slaveacts_vs_blackcode.csv
    python3 scripts/view_matches.py output/compare_n5_blackcode_vs_jimcrow.csv 40   # first 40 pairs

Works for word-phrase results (compare_n5_...) and character-shingle results
(compare_c10_...): with shingles, every word touched by a shared passage is
highlighted: the blocks of text the two sections share in the same order.
A block that occurs more than once in a section is marked each time.

Saves the page next to the CSV (same name, .html) and opens it in your browser.
"""

import csv
import html
import re
import sys
import webbrowser
from pathlib import Path

CSV_PATH = Path(sys.argv[1])
TOP = int(sys.argv[2]) if len(sys.argv) > 2 else 30     # pairs to show
CONTEXT = 30          # words of context around each highlighted passage
LONG = 250            # sections longer than this many words are shown as excerpts
OPEN_IN_BROWSER = True

WORD = re.compile(r"[a-z]+(?:['-][a-z]+)*")              # as in common.py
RACIAL = re.compile(r"^(?:negroes|negro|mulattoes|mulattos|mulatto|mestizoes|mestizoe|mestizo|"
                    r"colored|black)$")

name = CSV_PATH.stem
n_match = re.search(r"_n(\d+)", name)
N = int(n_match.group(1)) if n_match else 5
c_match = re.search(r"_c(\d+)", name)
K = int(c_match.group(1)) if c_match else None      # shingle length, for shingle results
NORM = "_norm" in name


def tokens(text):
    """(start, end, comparable word) for every word, as phrases() sees them."""
    out = []
    for m in WORD.finditer(text.lower()):
        w = m.group(0)
        if NORM and RACIAL.match(w):
            w = "raceterm"
        out.append((m.start(), m.end(), w))
    return out


def clean_map(text):
    """The text as compare_oh_sc.py's clean_chars() sees it (lowercase, no
    punctuation, single spaces), with each character's place in the original."""
    out, where, space = [], [], True
    for i, ch in enumerate(text.lower()):
        if ch.isalnum() or ch == "_":
            out.append(ch); where.append(i); space = False
        elif ch.isspace() and not space:
            out.append(" "); where.append(i); space = True
    return "".join(out), where


def marked(text, shared):
    """Indexes of the words that belong to a shared phrase (or, with shingles,
    that a shared passage touches)."""
    toks = tokens(text)
    if K:
        # the shared blocks compare_oh_sc.py found in order; each is marked
        # wherever it occurs in the section
        clean, where = clean_map(text)
        chars = set()
        for block in shared:
            start = clean.find(block)
            while block and start >= 0:
                chars.update(where[start:start + len(block)])
                start = clean.find(block, start + 1)
        hit = {k for k, (a, b, _) in enumerate(toks) if any(c in chars for c in range(a, b))}
        return toks, hit
    words = [t[2] for t in toks]
    hit = set()
    for i in range(len(words) - N + 1):
        if " ".join(words[i:i + N]) in shared:
            hit.update(range(i, i + N))
    return toks, hit


def render(text, shared):
    toks, hit = marked(text, shared)
    if not toks:
        return html.escape(text)
    show = set(range(len(toks)))
    if len(toks) > LONG and hit:
        show = set()
        for i in hit:
            show.update(range(max(0, i - CONTEXT), min(len(toks), i + CONTEXT + 1)))
    parts, pos, prev, in_mark = [], 0, -2, False
    for i, (a, b, _) in enumerate(toks):
        if i not in show:
            continue
        if i != prev + 1:                        # a gap: start a new excerpt
            if in_mark:
                parts.append("</mark>"); in_mark = False
            if prev >= 0:
                parts.append(' <span class="gap">[…]</span> ')
            elif i > 0:
                parts.append('<span class="gap">[…]</span> ')
            pos = a
        between = html.escape(text[pos:a])
        if i in hit and not in_mark:
            parts.append(between + "<mark>"); in_mark = True
        elif i not in hit and in_mark:
            parts.append("</mark>" + between); in_mark = False
        else:
            parts.append(between)
        parts.append(html.escape(text[a:b]))
        pos, prev = b, i
    if in_mark:
        parts.append("</mark>")
    tail = text[pos:]
    parts.append(html.escape(tail) if prev == len(toks) - 1 else ' <span class="gap">[…]</span>')
    return "".join(parts)


with open(CSV_PATH, newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
if not rows:
    raise SystemExit(f"{CSV_PATH.name} has no matched pairs.")

# Older results files used Ohio/SC column names; map them to the current ones.
ALIASES = {"share_a": "ohio_share", "a_section": "ohio_section", "a_date": "ohio_date",
           "b_section": "sc_section", "b_date": "sc_year", "b_title": "sc_title",
           "b_tags": "sc_tags", "a_text": "ohio_text", "b_text": "sc_text"}
get = lambda r, k: r.get(k) if k in r else r.get(ALIASES.get(k, ""), "")

labels = re.sub(r"^compare_[nc]\d+(_norm)?_?", "", name).replace("_vs_", " vs. ") or "ohio vs. jimcrow"
if labels == "blackcode":
    labels = "ohio vs. blackcode"
a_label, _, b_label = labels.partition(" vs. ")

summary, cards = [], []
for k, r in enumerate(rows[:TOP], 1):
    shared_list = [p.strip() for p in get(r, "shared_phrases").split("|") if p.strip()]
    shared = set(shared_list)
    a_id, b_id = get(r, "a_section"), get(r, "b_section")
    a_meta = " · ".join(x for x in [get(r, "a_date"), get(r, "a_part")] if x)
    b_meta = " · ".join(x for x in [get(r, "b_date"), get(r, "b_part"), get(r, "b_tags")] if x)
    title = get(r, "b_title")
    summary.append(f"<tr><td><a href='#p{k}'>{k}</a></td><td>{html.escape(a_id)}</td>"
                   f"<td>{html.escape(b_id)}</td><td class='num'>{get(r, 'aligned_shared') if K else len(shared)}</td>"
                   f"<td class='num'>{float(get(r, 'share_a') or 0):.2f}</td></tr>")
    cards.append(f"""
<section id="p{k}">
  <h2>{k}. {f"{get(r, 'aligned_shared')} characters shared in order" if K else f"{len(shared)} shared phrases"} <span class="scores">share of {html.escape(a_label)} section
  {float(get(r, 'share_a') or 0):.2f} · Jaccard {float(get(r, 'jaccard') or 0):.2f}</span></h2>
  <div class="pair">
    <div class="side"><h3>{html.escape(a_id)}</h3><p class="meta">{html.escape(a_meta)}</p>
      <p class="text">{render(get(r, 'a_text'), shared)}</p></div>
    <div class="side"><h3>{html.escape(b_id)}</h3><p class="meta">{html.escape(b_meta)}</p>
      {f'<p class="meta">{html.escape(title)}</p>' if title else ''}
      <p class="text">{render(get(r, 'b_text'), shared)}</p></div>
  </div>
  <details><summary>The shared {'blocks, in order' if K else 'phrases'}</summary><p class="phrases">{html.escape(' | '.join(shared_list if K else sorted(shared)))}</p></details>
</section>""")

page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>Text reuse: {html.escape(labels)}</title>
<style>
 :root {{ --ink:#1d2433; --muted:#5b6475; --line:#d9dde5; --mark:#ffe08a; --bg:#fbfaf7; }}
 body {{ font-family: Georgia, "Times New Roman", serif; color: var(--ink); background: var(--bg);
        max-width: 1200px; margin: 2em auto; padding: 0 1.2em; line-height: 1.55; }}
 h1, h2, h3, .meta, .scores, table, summary, .note {{ font-family: -apple-system, Helvetica, Arial, sans-serif; }}
 h1 {{ font-size: 1.5em; margin-bottom: .2em; }}
 .note {{ color: var(--muted); font-size: .92em; }}
 table {{ border-collapse: collapse; font-size: .88em; margin: 1em 0 2em; }}
 td, th {{ border-bottom: 1px solid var(--line); padding: .3em .8em; text-align: left; }}
 td.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
 section {{ border-top: 2px solid var(--line); padding-top: 1em; margin-top: 2em; }}
 h2 {{ font-size: 1.1em; }}
 .scores {{ font-weight: normal; color: var(--muted); font-size: .85em; margin-left: .6em; }}
 .pair {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.4em; }}
 .side {{ background: #fff; border: 1px solid var(--line); border-radius: 6px; padding: .8em 1em; }}
 h3 {{ font-size: .95em; margin: 0; }}
 .meta {{ color: var(--muted); font-size: .82em; margin: .2em 0 .6em; }}
 .text {{ font-size: .98em; }}
 mark {{ background: var(--mark); padding: 0 .1em; border-radius: 2px; }}
 .gap {{ color: var(--muted); font-family: Helvetica, Arial, sans-serif; font-size: .8em; }}
 details {{ margin-top: .6em; font-size: .85em; color: var(--muted); }}
 .phrases {{ font-family: Menlo, monospace; font-size: .85em; }}
 @media (max-width: 800px) {{ .pair {{ grid-template-columns: 1fr; }} }}
</style></head><body>
<h1>Text reuse: {html.escape(labels)}</h1>
<p class="note">{len(rows)} matched pairs in {html.escape(CSV_PATH.name)}; the first {min(TOP, len(rows))} are shown,
best first. <mark>Highlighted</mark> words belong to {f"blocks of text the two sections share in the same order (found with {K}-character shingles)" if K else f"{N}-word phrases the two sections share"}
(after enacting clauses and boilerplate were removed{', with racial terms normalized' if NORM else ''}).
Long sections are cut to the highlighted passages with {CONTEXT} words of context; [&hellip;] marks a cut.</p>
<table><tr><th>#</th><th>{html.escape(a_label)} section</th><th>{html.escape(b_label)} section</th>
<th>{'shared in order (characters)' if K else 'shared phrases'}</th><th>share</th></tr>{''.join(summary)}</table>
{''.join(cards)}
</body></html>"""

out = CSV_PATH.with_suffix(".html")
out.write_text(page, encoding="utf-8")
print(f"Saved {out}")
if OPEN_IN_BROWSER:
    webbrowser.open(out.resolve().as_uri())
