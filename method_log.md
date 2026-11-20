# OH\_SC Text Reuse: Method Log

Nov 20, 2026 · Dori Impson

## Purpose

The clearest case of text reuse so far runs inside South Carolina: the 1865 Black Code's migration section (Act No. 4731, Sec. XXII) reuses long stretches of the state's own 1820–1835 laws barring free Black people from entering the state. Ohio's Black Laws show no copied wording in either SC corpus, though the 1807 Ohio act and Sec. XXII share the same bond mechanism.

The project asks whether the language of race laws traveled: from Ohio's antebellum Black Laws to South Carolina's Jim Crow acts, and through South Carolina's own legal history (slave and free-Black laws, the 1865 Black Code, Jim Crow). This log records what was built and run on November 15–20, 2026, why each corpus and method change was added, and what each comparison found. It is a pilot meant to support a grant to run the method at scale.

All work lives in the `OH_SC_Text_Reuse` folder (a private GitHub repo): sources in `sources/`, corpora in `data/`, scripts in `scripts/`, results in `output/`.

## Method basis

The comparison is adapted from the 8510 Week 11 text reuse tutorial, so the core method matches what was taught and can be cited.

- **Starting script:** `02_reuse_all_pairs.py` (chop each passage into word n-grams, compare, score with Jaccard similarity).
- **Shared helpers:** `common.py` copied unchanged from the tutorial (`phrases`, `jaccard`, `snippet`).
- **Settings:** 5-word phrases, the tutorial's and Funk and Mullen's default ("The Spine of American Law," *AHR* 2018).
- **Character shingles:** added later from the tutorial's `01_reuse_jaccard_by_hand.py` (lowercase, drop punctuation, every run of K characters).
- **Alignment:** Python's `difflib`, as used in `04_reuse_trace_clause.py` to mark changes.
- **Software:** Python 3 standard library only; no API or outside service.

The unit of comparison is the section of a law, not the whole act. Copying happens at the scale of a clause, and the corpora differ greatly in size (about 4,150 Ohio words against 1.07 million SC Jim Crow words).

## Corpora

Four corpora were built, each from a public source, into the same layout: one file per law (`texts/`), one per section (`sections/`), and a `metadata.csv`. Two were added mid-project because the first comparison found only shared legal formulas.

| Corpus (folder) | Source | Dates | Size | Why it was added |
| --- | --- | --- | --- | --- |
| Ohio Black Laws (`ohio_black_laws`) | Arnett & Brown, *The Black Laws!* (1886), pp. 29–40; Library of Congress OCR | 1802–1878 | 9 laws, 35 sections, ~4,150 words | Original plan: compare Northern antebellum Black Laws with Southern Jim Crow |
| SC Jim Crow (`sc_jimcrow_1877-1920`) | On the Books in South Carolina, flagged-acts dataset (Boyd et al. 2025), filtered to 1877–1920 | 1877–1920 | 802 acts, 4,810 sections, ~1.07 million words | The Jim Crow side of the original comparison |
| SC 1865 Black Code (`sc_black_code_1865`) | *Statutes at Large of South Carolina*, vol. 13 (1875), pp. 245–285; Internet Archive OCR | Dec. 1865 | 4 acts (Nos. 4730–4733), 184 section files, ~22,000 words | Ohio vs. Jim Crow showed only formulas; the Black Code sits between the two in time |
| SC slave and free-Black acts (`sc_slave_acts_1690-1835`) | *Statutes at Large of South Carolina*, vol. 7 (1840), "Acts relating to Slaves," pp. 343–474; Internet Archive OCR | 1690–1835 | 41 acts, 385 section files, ~81,600 words | To test whether the Black Code drew on SC's own antebellum laws |

**Processing choices common to all four:**

- Page headers, year markers, signature blocks and OCR debris removed; words hyphenated across lines rejoined.
- Margin notes removed where they could be detected (a short piece set off by a wide gap, or a short line alone). Notes the OCR ran into a sentence remain as noise.
- Sections split at their numbers. A number the OCR destroyed leaves that section joined to the one before; each corpus's `metadata.csv` lists these.

**Corpus-specific choices:**

- **Ohio:** line-break joins came from a hand-checked list, not a rule, so real two-word phrases ("qui tam," "one half") stayed apart. All 86 joins and OCR fixes are logged in `corrections_log.csv`. Arnett's commentary, Townshend's letter, the 1886 repeal bill and the House vote were excluded.
- **SC Jim Crow:** the source repeats 61 acts (a second OCR of the same act, 1879–1907); second copies were set aside in `duplicates/` so they would not create false matches. The 44 appropriation bills are flagged and left out of comparisons.
- **Black Code:** Roman numerals were accepted only in sequence, with common misreadings mapped back ("YI" to VI, "Vill" to VIII). 181 of 185 sections were recovered; II, XL, IV and VII could not be read.
- **Slave acts:** acts were located from the volume's table of contents because the OCR garbled many titles ("No. 5T" for No. 57). The Statutes at Large were chosen over O'Neall's *Negro Law of South Carolina* (1848), which is a digest in O'Neall's words, not the statute text. Period spelling ("colour," "gaol") was not modernized. About 30 section numbers could not be read.

## Comparison method and its changes

Every section of an earlier corpus (A) is compared with every section of a later one (B) by `compare_oh_sc.py`. Each change below was added because a run exposed a specific problem.

| Change | Why it was needed | When |
| --- | --- | --- |
| Compare A sections only with B sections, not all pairs | Running the tutorial's 02 on both corpora would compare ~11.7 million pairs, mostly SC vs. SC | First version |
| Ignore phrases found in more than 50 B sections (boilerplate) | Enacting and procedural formulas match everywhere; adapted from tutorial script 03 | First version |
| Second score: share of the A section found in B (beside Jaccard) | A short Ohio clause copied into a long SC section still scores near 0 on Jaccard | First version |
| Keep pairs at Jaccard ≥ 0.10 or share ≥ 0.20 | The tutorial's 0.5 suits near-copies in one journal; Funk and Mullen kept matches down to 0.1 | First version |
| Leave out appropriation bills | Tabular budget lines add noise, not language | First version |
| Optional racial-term normalization (`norm`): "black or mulatto," "negro," "colored," "person of color" become one token | To test shared legal structure behind changing vocabulary | Nov. 18 |
| Any two corpora can be compared, either order | The project moved from one comparison to a chain of four corpora | Nov. 20 |
| Remove enacting clauses before comparing (fixed list: SC, Ohio, colonial, "by the authority aforesaid") | Slave acts vs. Black Code returned 21 pairs, all the SC enacting clause; the 50-section cutoff cannot catch it in a 184-section corpus | Nov. 20 |
| Also keep pairs with 5+ shared phrases; sort by that count | A passage borrowed into a long section is a small share of it: the 1823 entry ban shares 10 phrases with Sec. XXII but only 3% of its own phrases | Nov. 20 |
| Character-shingle mode (`char`, 10 characters) | Tolerates OCR errors and spelling change ("he it" for "be it," "colour") that break word phrases | Nov. 20 |
| In shingle mode, align candidates with `difflib`; keep pairs with ≥ 100 characters of shared text in the same order, in blocks of ≥ 20 characters | A set of shingles does not record order, so the first version stitched fragments from different places into false "passages" | Nov. 20 |
| `view_matches.py`: side-by-side HTML with shared wording highlighted | CSV rows made the reuse hard to see | Nov. 20 |

Word-phrase results are saved as `output/compare_n5_<A>_vs_<B>.csv`, shingle results as `compare_c10_…`. Each run also writes a `_boilerplate.csv` listing what was ignored.

## Log of steps and decisions

The project moved in four stages, newest first: building the antebellum SC corpus and refining the method (Nov. 20), adding the Black Code (Nov. 18–20), the first Ohio vs. Jim Crow comparison (Nov. 16–18), and building the first two corpora (Nov. 15).

| Date | Step | Decision or result |
| --- | --- | --- |
| Nov. 20 | Ohio vs. SC Jim Crow with shingles (`char 10`) | 17 pairs, all legal and school-administration formulas; confirms the word-phrase result |
| Nov. 20 | Shingle mode corrected with ordered alignment | Slave acts vs. Black Code: 4 pairs, all migration provisions → Sec. XXII; Ohio vs. Black Code: 0 |
| Nov. 20 | Ohio vs. Black Code rerun with shingles | Exposed that the first shingle version overstated matches (see Corrections) |
| Nov. 20 | Character-shingle mode and `view_matches.py` added | Viewer pages made for each results file |
| Nov. 20 | Enacting-clause removal and 5-phrase rule added; all comparisons rerun | Slave acts vs. Black Code: 9 pairs, led by the 1823, 1835 and 1820 entry bans |
| Nov. 20 | Slave acts vs. Black Code, first run | 21 pairs, all the SC enacting clause; reuse in Sec. XXII found underneath |
| Nov. 20 | SC slave acts corpus built from Statutes at Large vol. 7 | 41 acts, 385 sections; build fixed for "L"/"H" numeral misreadings and dropped first sections |
| Nov. 20 | Black Code vs. Jim Crow | Only filing and penal formulas; Black Code's master-servant and "persons of color" language absent from flagged Jim Crow acts |
| Nov. 20 | Ohio vs. Black Code | 0 pairs; migration-bond sections share structure but not wording |
| Nov. 20 | Black Code corpus built (Acts 4730–4733) | 181 of 185 sections recovered |
| Nov. 18 | Pivot to the 1865 Black Code | Ohio vs. Jim Crow shared only legal language; Black Code text gathered from Statutes at Large vol. 13 |
| Nov. 18 | Racial-term normalization run | Still only legal formulas in common |
| Nov. 18 | First Ohio vs. Jim Crow run (5 words); diagnostics at 3–5 words, no thresholds | 2 pairs, both formulas; method validated on Ohio 1853 vs. 1864 school law (Jaccard 0.31) |
| Nov. 16 | Private GitHub repo created; tutorial read; `compare_oh_sc.py` written | Method adapted from tutorial 02 |
| Nov. 15 | Project folder `OH_SC_Text_Reuse` and `notes.md` created | Separate from the 8510 class folder |
| Nov. 15 | SC Jim Crow corpus built from On the Books (1877–1920) | 802 unique acts after setting aside 61 duplicates |
| Nov. 15 | Ohio corpus built from Arnett (1886) | 9 laws, 35 sections; every OCR fix logged |

## Results

Only one comparison shows copied wording beyond legal formulas: SC's 1820–1835 free-Black entry bans into the Black Code's migration section. Figures are from the final method (enacting clauses removed) unless noted.

*(The online version of this log has a diagram here showing the four corpora and four comparisons. The one strong link runs within South Carolina; Ohio's tie to the Black Code is a shared mechanism without shared wording.)*

| Comparison | Word 5-grams | 10-character shingles | What the matches are |
| --- | --- | --- | --- |
| Ohio → SC Jim Crow | 22 pairs | 17 pairs | Legal and school-administration formulas ("clerk of the court of common pleas," "board of education"), no racial wording; at most 137 characters in order (shingles). Word run had 2 pairs before the method fixes |
| Ohio → Black Code | 0 pairs | 0 pairs | Ohio 1807 Sec. 1 and Black Code Sec. XXII share ~14% of shingles, in pieces under 20 characters |
| SC slave acts → Black Code | 9 pairs | 4 pairs | Top: 1823, 1835, 1820 entry bans → Sec. XXII; then penalty and filing formulas |
| Black Code → SC Jim Crow | 57 pairs | 31 pairs | Penal, court-fund and magistrate formulas; nothing racial |

**The Black Code borrowed its expulsion procedure from SC's own entry bans.** Sec. XXII and the 1823 act (No. 2319) share 239 characters of text in the same order; the 1835 act shares 256, the 1820 act 140. The shared sequence:

> 1823: "…every free negro or person of color, **so ordered to leave the State**, and thereafter remaining longer than **fifteen days** within the same, **or having left the State** and thereafter **return**ing **to the same**… shall be subjected to be sentenced **to such corporal punishment as the** said magistrate and freeholders shall, in their discretion, **think fit to order**."

> 1865: "…any such person, **so ordered to leave the State**… shall… be liable **to such corporal punishment as the** Court, in its discretion, shall **think fit to order**. And if any such person… shall still remain within the State more than **fifteen days**… **or having left the State**, shall **return to the same**…"

The changes are telling: "free negro or person of color" becomes "person of color," extending the antebellum free-Black category to all freedpeople, and "magistrate and three freeholders" becomes the new District Court.

**Ohio's resemblance is structural, not textual.** Ohio 1807 and Sec. XXII share a bond mechanism (twenty days, a bond with two freehold sureties, conditioned on good behavior and support), in the same order, in short pieces: "within twenty days," "bond with two," "good behavior," "unable to support." The first half of Sec. XXII (the bond) is absent from the 1823 act, so Sec. XXII looks like an Ohio-type bond attached to SC's own expulsion procedure. Whether SC took the bond from Ohio or a common source is an archival question.

**Racial vocabulary barely carries from Ohio to SC Jim Crow.** Of 495 Ohio 5-word phrases containing a racial term, one appears in SC Jim Crow ("for the education of white"). At 3 words, 17 match, all in school laws. The Black Code's "persons of color" and master-servant framework is likewise absent from the flagged Jim Crow acts, where "white and colored" separation language appears instead (14 sections, 1893–1920).

**Shingles confirm the Ohio–Jim Crow result.** With 10-character shingles, Ohio vs. SC Jim Crow keeps 17 pairs, none with racial wording. The Ohio school laws (1848, 1853, 1864) match SC school and tax acts on "are hereby authorized and required to" and "board of education"; Ohio 1807 matches SC magistrate acts on "the clerk of the court of common pleas." Two methods give the same answer, so the absence of borrowing does not depend on the method.

**The method detects reuse where it exists.** Ohio's 1853 school section and its 1864 amendment score Jaccard 0.31, with 57% of the 1853 phrases carried over, so empty results are meaningful.

## Corrections and limitations

**Corrections to earlier statements:**

- **Shingle "longest passage" figures withdrawn.** The first shingle version reported a 94-character unbroken passage shared by the 1823 act and Sec. XXII, and 69 characters for Ohio 1807. Both were wrong: the measure stitched fragments from different places in the second text. The ordered-alignment figures in Results replace them.
- **Enacting clauses inflated early results.** Before Nov. 20, small-corpus comparisons were dominated by the SC enacting clause. `compare_n5_norm.csv` and `compare_n4_norm.csv` in `output/` predate the fix and should be rerun or deleted.

**Limitations to state in any write-up:**

- **Racial normalization misses British spelling.** `norm` turns "person of color" into the token but not "person of colour" or "coloured," which the antebellum acts use. Not yet fixed; `norm` runs on the slave acts would undercount.
- **The Jim Crow corpus is model-flagged acts only.** It omits laws written in race-neutral terms, such as labor-contract, enticement and vagrancy acts, where Black Code provisions may have continued. The model also flags some non-racial acts (an 1877 Fairfield County fence law is the first record).
- **OCR noise.** Margin notes run into sentences in the Black Code, slave acts and 1900s Jim Crow acts (once producing "TrusNotice of electees"). The antebellum OCR often reads "be it" as "he it." No word-level correction was done outside the Ohio corpus.
- **Merged sections.** Unreadable numbers leave sections joined: 4 in the Black Code, about 30 in the slave acts (listed in each `metadata.csv`).
- **Ohio texts are a secondary print.** Arnett's 1886 reprints, not the session-law volumes; quotations need checking against the originals. Arnett omits the 1831 juries act, the 1834 amendment and the militia exclusion.
- **1802 Ohio clause unverified.** Arnett says the convention passed it; it may not be in the adopted constitution.
- **Exact methods miss paraphrase.** Word n-grams and shingles detect shared wording; the Ohio–SC bond parallel is visible only by reading or by a meaning-based method.
- **Thresholds are judgment calls.** 50-section boilerplate cutoff, 0.10 / 0.20 / 5-phrase rules, 20-character blocks and 100-character totals were set by inspecting results; a write-up should report them and, ideally, show results at a second setting.

## Next steps

- [ ] Fix racial normalization for "colour" / "coloured," then run `norm` comparisons on the slave acts
- [x] Run the remaining shingle comparison: Ohio vs. SC Jim Crow (`char 10`)
- [ ] Rerun or delete the outdated `compare_n5_norm.csv` and `compare_n4_norm.csv`
- [ ] Read the top pairs of each comparison in the viewer and record judgments (borrowing, common source, or formula)
- [ ] Check the 1807 / Sec. XXII and 1823 / Sec. XXII quotations against the printed volumes
- [ ] Verify the 1802 Ohio clause against the adopted constitution
- [ ] Update `notes.md` in the project to cover the Black Code and slave-acts corpora and the method changes

Corpora that would extend the pilot, in rough order of payoff:

1. **Indiana and Illinois Black Laws:** reported to have borrowed from Ohio, so a test of whether the method catches borrowing between states.
2. **SC post-1877 labor, enticement and vagrancy acts, flagged or not:** tests whether Black Code provisions continued in race-neutral wording.
3. **Missing Ohio acts** (1831 juries, 1834 amendment, militia exclusion) from the original session-law volumes.
4. **A meaning-based comparison** (sentence embeddings) to measure paraphrase such as the Ohio–SC bond provision, building on the word2vec work on *The Crisis* and *Opportunity*.

## Sources

- B. W. Arnett and J. A. Brown, *The Black Laws!* (Columbus: Ohio State Journal, 1886), Library of Congress, Daniel Murray Pamphlet Collection: [loc.gov/item/91898104](https://www.loc.gov/item/91898104/)
- K. Boyd et al., *On the Books in South Carolina Corpus* [Datasets] (University of South Carolina Libraries, 2025), CC BY-NC-SA 4.0: [scholarcommons.sc.edu/lib\_facpub/64](https://scholarcommons.sc.edu/lib_facpub/64/)
- K. Boyd et al., *On the Books in South Carolina: Mining for Jim Crow Laws* [White Paper] (2025): [scholarcommons.sc.edu/lib\_facpub/63](https://scholarcommons.sc.edu/lib_facpub/63)
- *The Statutes at Large of South Carolina*, vol. 13 (Columbia: Republican Printing Co., 1875), Internet Archive: [statutesatlargeo13repu](https://archive.org/details/statutesatlargeo13repu)
- *The Statutes at Large of South Carolina*, vol. 7, ed. David J. McCord (Columbia: A. S. Johnston, 1840), Internet Archive: [statutesatlargeo07edit](https://archive.org/details/statutesatlargeo07edit)
- Kellen Funk and Lincoln Mullen, "The Spine of American Law: Digital Text Analysis and U.S. Legal Practice," *American Historical Review* 123, no. 1 (2018): 132–164: [doi:10.1093/ahr/123.1.132](https://doi.org/10.1093/ahr/123.1.132)
- 8510 Week 11 text reuse tutorial (`11-Text-Reuse`, scripts 01–04 and `common.py`), course repository

Author list for the On the Books dataset is given as in the Scholar Commons citation; check full names before formal citation.
