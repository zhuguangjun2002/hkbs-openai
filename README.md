# HKBS New Punctuation CUV Extractor

This repository contains a small extractor for the HKBS online Bible pages.

The New Punctuation Chinese Union Version has two paths:

```text
https://rcuv.hkbs.org.hk/CUNP1/GEN/1/
https://rcuv.hkbs.org.hk/CUNP1s/GEN/1/
```

`CUNP1` is traditional Chinese. `CUNP1s` is simplified Chinese.

The `RCUV1s` path in the example URL is the 2010 Revised Chinese Union Version
simplified text, not the New Punctuation CUV.

## Data Status

The `data/cunp` directory contains a complete per-chapter extraction for both
scripts:

- `traditional`: 1189 chapter JSON files
- `simplified`: 1189 chapter JSON files
- total: 2378 chapter JSON files

Verification on 2026-05-15 found no missing chapters, no invalid JSON files,
and no empty verse arrays.

## Usage

Fetch one chapter:

```bash
python3 scripts/extract_hkbs_cunp.py --book GEN --chapter 1
```

By default this fetches both traditional and simplified. To fetch only one:

```bash
python3 scripts/extract_hkbs_cunp.py --book GEN --chapter 1 --script traditional
python3 scripts/extract_hkbs_cunp.py --book GEN --chapter 1 --script simplified
```

Fetch one whole book into per-chapter JSON files:

```bash
python3 scripts/extract_hkbs_cunp.py --book GEN --output-dir data/cunp
```

Output is separated by script:

```text
data/cunp/traditional/GEN/001.json
data/cunp/simplified/GEN/001.json
```

Fetch all books:

```bash
python3 scripts/extract_hkbs_cunp.py --all --output-dir data/cunp --delay 1.5
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

## Copyright

Before bulk downloading, storing, or redistributing the text, check the HKBS
licensing and usage terms. This script is intended as an extraction tool for
authorized or personal research use; it does not include the Bible text itself.
