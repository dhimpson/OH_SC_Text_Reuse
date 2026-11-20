# Ohio Black Laws and South Carolina Race Laws: A Text Reuse Project

A pilot project that tests whether the wording of race laws traveled: from Ohio's antebellum Black Laws to South Carolina's Jim Crow acts, and through South Carolina's own legal history (slave and free-Black acts, the 1865 Black Code, and Jim Crow).

The method compares laws section by section. It looks for shared 5-word phrases and for shared 10-character sequences ("shingles"), which hold up better against OCR errors. It is adapted from the 8510 text reuse tutorial and from Funk and Mullen, "The Spine of American Law" (*AHR*, 2018).

The main finding so far: the 1865 Black Code's migration section (Sec. XXII) reuses wording from South Carolina's 1820–1835 laws barring free Black people from entering the state. Ohio's laws show no copied wording in either South Carolina corpus.

See `method_log.md` for the full methods, results and limitations.

## Sources

| Corpus | Source | Dates |
| --- | --- | --- |
| Ohio Black Laws | B. W. Arnett and J. A. Brown, *The Black Laws!* (1886), Library of Congress | 1802–1878 |
| SC slave and free-Black acts | *Statutes at Large of South Carolina*, vol. 7 (1840), Internet Archive | 1690–1835 |
| SC 1865 Black Code | *Statutes at Large of South Carolina*, vol. 13 (1875), Internet Archive | 1865 |
| SC Jim Crow acts | *On the Books in South Carolina* dataset, University of South Carolina Libraries (2025), CC BY-NC-SA 4.0 | 1877–1920 |

## Folder layout

- `sources/`: the original OCR text files
- `data/`: the cleaned corpora, one folder per corpus (each has whole laws, separate sections, and a `metadata.csv`)
- `scripts/`: Python scripts that build the corpora, run comparisons and make viewer pages
- `output/`: results (CSV files) and side-by-side HTML viewer pages
- `method_log.md`: what was done, why, and what was found

## Requirements

- Python 3 (standard library only; no extra packages, API keys or outside services)
- A virtual environment (`venv/`) is optional
- VS Code with the Rainbow CSV extension is helpful for reading results, but not required

## Running a comparison

From the project folder:

```
python scripts/compare_oh_sc.py 5 slaveacts blackcode
```

- `5` sets the phrase length in words. Add `char` to compare 10-character shingles instead, and `norm` to merge racial terms into a single token.
- Corpus names: `ohio`, `slaveacts`, `blackcode`, `jimcrow`. Put the earlier corpus first. With no corpora named, the script compares Ohio with Jim Crow.

To view the results side by side in a browser:

```
python scripts/view_matches.py output/<results file>.csv
```
