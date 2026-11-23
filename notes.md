# OH_SC_Text_Reuse — Corpus compilation notes

Compiled November 15, 2026. This file documents how the two corpora in `data/` were built from the files in `sources/`, what was changed along the way, and the known limitations of each.

## Purpose

These corpora support a text reuse comparison between Ohio's antebellum Black Laws (early nineteenth century) and South Carolina laws of the late nineteenth and early twentieth centuries flagged as likely Jim Crow laws. Both corpora share one layout so they can be compared directly:

- `texts/`: one plain-text file per law or act
- `sections/`: one plain-text file per section of each law or act (the recommended unit of comparison, since the two corpora differ so greatly in size)
- `metadata.csv`: one row per law or act

## Folder layout

```
OH_SC_Text_Reuse/
├── notes.md                      this file
├── data/
│   ├── ohio_black_laws/          Ohio corpus (texts/, sections/, metadata.csv, corrections_log.csv)
│   └── sc_jimcrow_1877-1920/     SC corpus (texts/, sections/, duplicates/, metadata.csv)
├── scripts/
│   ├── build_ohio_corpus.py
│   └── build_sc_corpus.py
├── sources/                      unmodified source files the corpora were built from
└── archives/                     zip files used to transfer the corpora (safe to delete)
```

---

## 1. Ohio Black Laws corpus (`data/ohio_black_laws/`)

### Source

B. W. Arnett and J. A. Brown, *The Black Laws! Speech of Hon. B. W. Arnett of Greene County, and Hon. J. A. Brown of Cuyahoga County, in the Ohio House of Representatives, March 10, 1886* (Columbus: Ohio State Journal, 1886). Library of Congress, Rare Book and Special Collections Division, Daniel Murray Pamphlet Collection. https://www.loc.gov/item/91898104/

The pamphlet's appendix, "Black Laws of Ohio since 1802" (printed pp. 29–40), reprints the texts of Ohio's race laws. That appendix is the sole source for this corpus.

### Acquisition

The LOC scan has 46 images. Printed pp. 29–40 correspond to scan images 33–44. The text is LOC's own OCR (ABBYY FineReader 11, processed 2017-10-20), retrieved page by page from LOC's full-text service and saved without changes as `sources/arnett_1886_black_laws_pp29-40.txt`. Each page in that file is labeled with its scan image and printed page number. No retyping or manual transcription was done.

### Processing (`scripts/build_ohio_corpus.py`)

1. **Removed non-text lines:** page markers, printed page numbers, and scanner noise at the top of pp. 30 and 38.
2. **Rejoined words split across lines.** The OCR dropped end-of-line hyphens, leaving words broken in two (e.g., "certifi / cate," "emi / grate"). These were rejoined from an explicit, hand-checked list rather than an automatic rule, so genuine two-word phrases that fall across a line break ("qui tam," "one half," "school house") were left alone. 39 split patterns, 53 instances.
3. **Corrected clear OCR errors,** each checked against the page image. Examples: "69S7" → 6987, "Alrican" → African, "be lined" → be fined, "court or record" → court of record, "knowing!}-" → knowingly. 31 patterns, 33 instances.
4. **Extracted the laws only.** Each law was cut out of the appendix by its opening and closing words. Excluded: Arnett's framing text, N. S. Townshend's 1886 letter on the 1849 repeal, Governor William Bebb's 1847 message and the related House proceedings, the speakers' signatures and dates, Arnett's volume/page citations, the 1886 repeal bill, and the House vote.
5. **Split each law into sections** at "Section N." / "Sec. N." headings.

Every change from steps 2 and 3 is recorded in `corrections_log.csv` (type, text found, replacement, number of instances) so it can be checked against the scans.

### Contents

| doc_id | Date | Sections | Words |
|---|---|---|---|
| ohio_1802_constitution_proposed | 1802 | 1 | 82 |
| ohio_1804_regulate_black_mulatto | 1804-01-05 | 7 | 814 |
| ohio_1807_amend_regulate | 1807-01-25 | 5 | 509 |
| ohio_1848_colored_schools | 1848-02-24 | 10 | 1,120 |
| ohio_1849_separate_districts_repeal | 1849-02-10 | 6 | 844 |
| ohio_1853_school_sec31 | 1853-03-14 | 1 | 231 |
| ohio_1861_intermarriage | 1861-01-31 | 2 | 124 |
| ohio_1864_school_sec31_amended | 1864-03-18 | 2 | 337 |
| ohio_1878_sec4008 | 1878 | 1 | 93 |

Total: 9 documents, 35 section files, about 4,150 words.

### Verification

After the build, every word occurring only once in the corpus was listed and reviewed to catch remaining OCR damage. This found one missed line-break split ("dol / lars" in the 1861 law), which was added to the script before the final run. No other broken words or misread characters were found.

### Caveats

- **1802 constitutional clause.** Arnett states that the 1802 convention passed this section. It should be checked against the constitution as adopted before it is treated as enacted law; it is kept in the corpus but flagged in `metadata.csv`.
- **1878 date.** The date for Rev. Stat. Sec. 4008 comes only from Arnett's heading.
- **Section numbering.** The 1861 and 1878 provisions carry Revised Statutes section numbers (6987–6988, 4008) as Arnett prints them, not session-law numbers.
- **The 1849 act** is largely a repeal measure; its Sec. 6 repeals the 1804 and 1807 acts but adds a new provision penalizing bringing likely paupers into the state.
- **Not comprehensive.** Arnett does not reprint every Ohio Black Law. Missing, for example, are the act of February 9, 1831, on juries and the amendment of February 27, 1834 (both named in the 1849 repeal), and the militia exclusion. These would have to come from the original *Acts of the State of Ohio* volumes.
- **Secondary print.** The texts are Arnett's 1886 reprints, not the original session-law volumes. For publication, quotations should be checked against the originals.

---

## 2. South Carolina corpus (`data/sc_jimcrow_1877-1920/`)

### Source

Kate F. Boyd, Kristin Harrell, Tyler Callahan, Robin Turnmire, Joseph Freeman, Vandana Srivastava, Colin Frear, Lance DuPre, and Nishant Gupta, *On the Books in South Carolina Corpus: Acts passed by the SC General Assembly, 1868–1968, Identified by Machine Learning as Likely to be Jim Crow Laws* [Datasets] (University of South Carolina Libraries, 2025). https://scholarcommons.sc.edu/lib_facpub/64/ . Licensed CC BY-NC-SA 4.0.

The dataset was produced by a machine learning model trained to classify SC session acts as Jim Crow or not, with review by historians. Methods are described in the project's white paper: Boyd et al., *On the Books in South Carolina: Mining for Jim Crow Laws* (2025), https://scholarcommons.sc.edu/lib_facpub/63/ . Project site: https://drsc.usccreate.org/otbsc/

### Acquisition

Two files were downloaded from Scholar Commons:

- **Full text** of all 2,726 flagged acts (1877–1968). This was filtered to acts dated 1877–1920 (863 records) and saved as `sources/otbsc_jimcrow_acts_1877-1920.txt`. The records themselves were not altered; a note on the first line records the filter and source.
- **Act list** (`sources/otbsc_jimcrow_acts_list.csv`), unmodified, with act number, date, title, county, and topic tags for every flagged act.

The 1877–1920 range was chosen to cover the late nineteenth and early twentieth centuries, including the period the project identifies as having the most Jim Crow language (1892–1897).

### Processing (`scripts/build_sc_corpus.py`)

1. **Split the file into acts** at each "Year: ... ACT NO.: ..." header.
2. **Cleaned OCR formatting:** rejoined words hyphenated across lines (e.g., "Trus- tees" → "Trustees"), removed spaces before punctuation (e.g., "Carolina , That" → "Carolina, That"), and replaced non-breaking spaces with ordinary ones. No word-level OCR corrections were made, given the corpus size.
3. **Split each act into sections** at lines beginning "SECTION," "Section," "SEC.," "Sec.," or "§" followed by a number. Any title, preamble, or "Whereas" text before the first section is saved as section `s00`.
4. **Gave each act a unique ID** (`sc_YEAR_actNUMBER`).
5. **Set aside duplicates.** The source file contains 61 acts twice, in 1879, 1880, 1906, and 1907. Each pair is the same act OCR'd from two different scans (titles and lengths match). The first copy is kept; the second is saved in `duplicates/` with an `_b` suffix and linked to its original in the `duplicate_of` column, and is excluded from `texts/` and `sections/`. Keeping both would have counted those acts twice and produced false perfect matches within SC.
6. **Flagged appropriation bills.** Acts with "appropriat" in the title, or ten or more line-item/dollar/total lines, are marked `appropriation_like = True` (44 acts). They are kept, but can be filtered out, since their tabular content adds little to a language comparison.
7. **Joined the project's metadata** (date, county, topic tags, source volume) from the act list by year and act number.

### Contents

- 802 unique acts (863 in the source, minus 61 duplicate copies), 4,810 section files, about 1.07 million words
- By decade: 1870s 20 · 1880s 83 · 1890s 176 · 1900s 210 · 1910s 256 · 1920 57
- 799 of 802 acts matched to the project's act list. Not in the list: 1889 Act 299, 1904 Act 211, 1914 Act 468.
- Most frequent topic tags: education, voting, taxation (the tags are inconsistently capitalized in the source)

### Caveats

- **Model output, not a definitive list.** The project notes that the laws' indirect wording made Jim Crow and non–Jim Crow laws hard for the model to distinguish, and that substantial human review was needed. Expect false positives (the first record, an 1877 act on fences in Fairfield County, gives no sign of racial content in its title) and missed laws. The topic tags help separate clear cases from marginal ones.
- **Flagged acts only.** This corpus contains only acts the project flagged, not all SC acts for the period. A baseline of non-flagged acts (to tell racial language apart from ordinary legal boilerplate) would need the project's full corpus.
- **Margin notes.** In the 1900s volumes, the printed margin notes are mixed into the body text by the OCR (e.g., "Notice of elec-" appears mid-sentence). They cannot be removed reliably. Occasionally the hyphen fix in step 2 merges a margin note into a word: "Trus- / Notice of elec- / tees" became "TrusNotice of electees." This adds noise but is unlikely to produce false matches with the Ohio texts.
- **OCR quality varies by volume** and was not corrected word by word.

---

## Rebuilding the corpora

From inside `OH_SC_Text_Reuse/`:

```
python3 scripts/build_ohio_corpus.py sources/arnett_1886_black_laws_pp29-40.txt data/ohio_black_laws
python3 scripts/build_sc_corpus.py sources/otbsc_jimcrow_acts_1877-1920.txt data/sc_jimcrow_1877-1920 sources/otbsc_jimcrow_acts_list.csv
```

Both scripts use only the Python standard library. Running them writes into the output folder given, overwriting files with the same names.

## Notes for the comparison

- The corpora differ in size by a factor of roughly 250 (about 4,150 Ohio words vs. 1.07 million SC words). Compare each Ohio section against the SC sections rather than whole documents.
- Racial vocabulary shifts across the period ("black or mulatto person" → "negro," "colored," "person of African descent"). Exact n-gram matching will miss conceptual reuse that uses different terms; consider normalizing racial terms to a single token as an alternate run, and report both.
- Strip or discount common enacting and legal boilerplate ("be it enacted," "be it further enacted," "any person or persons") so matches reflect substantive language.

# Notes on Runs:
## First run on compare_oh_sc.py

# 35 Ohio sections, 4,079 SC sections (48 appropriation acts left out), 5-word phrases
249 boilerplate phrases ignored (37 of them also occur in the Ohio laws)
2 pairs kept (Jaccard >= 0.1 or Ohio share >= 0.2)

ohio share 0.36  jaccard 0.00  4 phrases
   ohio_1864_school_sec31_amended_s01  ->  sc_1900_act188_s01  [Amendments, Judicial]
   "be so amended as to read as follows ..."

ohio share 0.14  jaccard 0.13  7 phrases
   ohio_1807_amend_regulate_s05  ->  sc_1879_act110_s02  [Fence Laws]
   "act shall take effect and be in force from and after the first day of april next ..."
# this run did not prove text reuse. I decided to have Claude assist with normalizing the racial terms within the data sets from both states and then rerun. This will remove vocbulary differences between the two states (regarding racial terms only), replace such instances with a single token word, raceterm, and then allow for a cleaner comparison in how the states built laws. 

#results of the first rerun with racenormalizing (compare_oh_sc.py 5 norm)

35 Ohio sections, 4,079 SC sections (48 appropriation acts left out), 5-word phrases, racial terms normalized
249 boilerplate phrases ignored (37 of them also occur in the Ohio laws)
3 pairs kept (Jaccard >= 0.1 or Ohio share >= 0.2)

Best pairs overall:

ohio share 0.36  jaccard 0.00  4 phrases (0 with raceterm)
   ohio_1864_school_sec31_amended_s01  ->  sc_1900_act188_s01  [Amendments, Judicial]
   "be so amended as to read as follows ..."

   ohio share 0.15  jaccard 0.14  7 phrases (0 with raceterm)
   ohio_1807_amend_regulate_s05  ->  sc_1879_act110_s02  [Fence Laws]
   "act shall take effect and be in force from and after the first day of april next ..."

ohio share 0.12  jaccard 0.10  6 phrases (0 with raceterm)
   ohio_1807_amend_regulate_s05  ->  sc_1892_act216_s03  [Fence Laws, Stock Laws]
   "act shall take effect and be in force from and after the first day of april next ..."

Best pairs sharing at least one phrase with raceterm:

Saved output/compare_n5_norm.csv and output/compare_n5_norm_boilerplate.csv
35 Ohio sections, 4,079 SC sections (48 appropriation acts left out), 4-word phrases, racial terms normalized
478 boilerplate phrases ignored (80 of them also occur in the Ohio laws)
4 pairs kept (Jaccard >= 0.1 or Ohio share >= 0.2)

Best pairs overall:

ohio share 0.36  jaccard 0.00  4 phrases (0 with raceterm)
   ohio_1864_school_sec31_amended_s01  ->  sc_1900_act188_s01  [Amendments, Judicial]
   "be so amended as to read as follows ..."

ohio share 0.18  jaccard 0.12  2 phrases (0 with raceterm)
   ohio_1864_school_sec31_amended_s01  ->  sc_1890_act614_s04  [education]
   "of said act be so amended as to read as follows ..."

ohio share 0.18  jaccard 0.12  2 phrases (0 with raceterm)
   ohio_1864_school_sec31_amended_s01  ->  sc_1894_act598_s03  [education]
   "of said act be so amended as to read as follows ..."

ohio share 0.16  jaccard 0.15  7 phrases (0 with raceterm)
   ohio_1807_amend_regulate_s05  ->  sc_1879_act110_s02  [Fence Laws]
   "shall take effect and be in force from and after the first day of april next ..."

Best pairs sharing at least one phrase with raceterm:
# It looks like the only sharing is legal languge. 

# A lack of viable text reuse results led me to try something else: Compare the 1804/1807 OH Black Code Corpus to a corpus of SC Black Codes from 1865. Did southern Black Codes borrow from Northern post-slavery Black Codes? 

## please follow methods log for more changes.