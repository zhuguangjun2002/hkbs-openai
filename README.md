# HKBS Chinese Bible Extractor

This repository contains a small extractor for the HKBS online Bible pages and
the extracted per-chapter JSON data used by the static reader.

The New Punctuation Chinese Union Version has two paths:

```text
https://rcuv.hkbs.org.hk/CUNP1/GEN/1/
https://rcuv.hkbs.org.hk/CUNP1s/GEN/1/
```

`CUNP1` is traditional Chinese. `CUNP1s` is simplified Chinese.

The 2010 Revised Chinese Union Version, Shen edition, has two paths:

```text
https://rcuv.hkbs.org.hk/RCUV1/GEN/1/
https://rcuv.hkbs.org.hk/RCUV1s/GEN/1/
```

`RCUV1` is traditional Chinese. `RCUV1s` is simplified Chinese. These paths are
the 和合本2010（和修）（神版） text. The related `RCUV2` paths are the 上帝版
and are not included in this dataset.

## Data Status

Current deployed state as of 2026-05-17:

- CUNP data is available in the static web reader.
- RCUV Shen data is extracted and committed, but is not yet exposed as a
  selectable translation in the web reader.
- The extractor preserves source-level merged verse ranges with `verse_end`.
- The extractor preserves duplicate source verse numbers with `sequence`.
- Mid-verse headings from HKBS are not promoted into `section_headings`. For
  example, the source heading `爱` that appears after CUNP 1 Corinthians 12:31
  is not rendered before 12:31; the verse text remains complete.

The `data/cunp` directory contains a complete per-chapter extraction for both
scripts:

- `traditional`: 1189 chapter JSON files
- `simplified`: 1189 chapter JSON files
- total: 2378 chapter JSON files

Verification on 2026-05-17 found no missing chapters, no invalid JSON files,
no empty verse arrays, no mismatched metadata, and no chapters whose first
parsed verse starts after verse 1. The CUNP data has also been resynced from
the HKBS source pages with the current parser, correcting chapter headings and
restoring merged verse ranges that older extraction runs skipped.

The `data/rcuv-shen` directory contains a complete per-chapter extraction for
和合本2010（和修）（神版） in both scripts:

- `traditional`: 1189 chapter JSON files
- `simplified`: 1189 chapter JSON files
- total: 2378 chapter JSON files

Verification on 2026-05-17 found no missing chapters, no invalid JSON files,
no empty verse arrays, no mismatched metadata, and no chapters whose first
parsed verse starts after verse 1.

Run the verifier after changing extractor logic or files under `data/`:

```bash
python3 scripts/verify_bible_data.py data/cunp data/rcuv-shen
```

The verifier checks chapter coverage, JSON validity, path and metadata
consistency, non-empty verse arrays, verse ordering, merged verse ranges, and
source-level skipped or duplicate verse numbers.

## JSON Schema

Each chapter JSON file has this top-level shape:

```json
{
  "translation": "cunp",
  "version": "CUNP1s",
  "version_name": "新标点和合本",
  "script": "simplified",
  "book_code": "GEN",
  "book_name": "创世记",
  "chapter": 1,
  "heading": "神的创造",
  "source_url": "https://rcuv.hkbs.org.hk/CUNP1s/GEN/1/",
  "verses": []
}
```

Merged verse ranges from the HKBS source are represented by `verse_end` on the
first verse in the range:

```json
{
  "verse": 1,
  "verse_end": 2,
  "text": "...",
  "notes": []
}
```

Single verses omit `verse_end`. Gaps that remain without `verse_end` after
source resync are source-level omitted verse numbers, not inferred ranges.

If a source chapter contains duplicate verse numbers, each duplicate item keeps
the original `verse` number and receives a 1-based `sequence` value. This keeps
the source reference intact while allowing unique lookup by
`book_code/chapter/verse/sequence`:

```json
{
  "verse": 9,
  "sequence": 1,
  "section_headings": ["．有些古卷有下列结语．", "短结语："],
  "text": "...",
  "notes": []
}
```

`section_headings` preserves source headings that appear immediately before a
verse, such as the short and long endings in RCUV Shen Mark 16. Headings that
appear after verse text has already started are treated as following-section
markers and are not attached to the current verse.

## Usage

Fetch one CUNP chapter:

```bash
python3 scripts/extract_hkbs_cunp.py --book GEN --chapter 1
```

By default this fetches both traditional and simplified. To fetch only one:

```bash
python3 scripts/extract_hkbs_cunp.py --book GEN --chapter 1 --script traditional
python3 scripts/extract_hkbs_cunp.py --book GEN --chapter 1 --script simplified
```

Fetch one RCUV Shen chapter:

```bash
python3 scripts/extract_hkbs_cunp.py --translation rcuv-shen --book GEN --chapter 1
```

Fetch one whole CUNP book into per-chapter JSON files:

```bash
python3 scripts/extract_hkbs_cunp.py --book GEN --output-dir data/cunp
```

Fetch one whole RCUV Shen book:

```bash
python3 scripts/extract_hkbs_cunp.py --translation rcuv-shen --book GEN --output-dir data/rcuv-shen
```

Output is separated by script:

```text
data/cunp/traditional/GEN/001.json
data/cunp/simplified/GEN/001.json
data/rcuv-shen/traditional/GEN/001.json
data/rcuv-shen/simplified/GEN/001.json
```

Fetch all CUNP books:

```bash
python3 scripts/extract_hkbs_cunp.py --all --output-dir data/cunp --delay 1.5
```

Fetch all RCUV Shen books:

```bash
python3 scripts/extract_hkbs_cunp.py --translation rcuv-shen --all --output-dir data/rcuv-shen --workers 12 --delay 0.05
```

Use JSON Lines instead of nested chapter JSON:

```bash
python3 scripts/extract_hkbs_cunp.py --book PHP --chapter 1 --format jsonl
```

## Static Web Reader

This repo includes a static Bible reader and query tool in `web/`.

Live site:

```text
https://zhuguangjun2002.github.io/hkbs-openai/
```

Features:

- chapter reading by book and chapter
- simplified/traditional switching
- CUNP reading data bundled from `data/cunp`
- full-text client-side search across simplified and traditional text
- cross-script highlighting, such as searching `亞歷山大` while reading simplified text
- search scopes: whole Bible, Old Testament, New Testament, or current book
- reference jump support such as `约3:16`, `約3:16`, `约3:16-18`, or `JHN3:16`
- highlighted search terms after opening a search result
- light/dark theme

Rebuild the browser data bundle after changing files under `data/cunp`:

```bash
python3 scripts/build_web_data.py
```

Preview locally:

```bash
python3 -m http.server 8000
```

Then open:

```text
http://localhost:8000/web/
```

The site is deployed with GitHub Pages from `.github/workflows/pages.yml`.
The workflow publishes the `web/` directory directly, so no npm install or
build step is required.

Next recommended web task: add a translation selector and include
`data/rcuv-shen` in the browser data bundle so the live reader can switch
between CUNP and RCUV Shen.

## Copyright

Before bulk downloading, storing, or redistributing the text, check the HKBS
licensing and usage terms. This script is intended as an extraction tool for
authorized or personal research use; it does not include the Bible text itself.
