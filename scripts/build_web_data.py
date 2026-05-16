#!/usr/bin/env python3
"""Build a browser-friendly data bundle for the static Bible reader."""

from __future__ import annotations

import json
from pathlib import Path

from extract_hkbs_cunp import BOOKS


ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data" / "cunp"
OUTPUT = ROOT / "web" / "data.js"


def load_chapter(script: str, code: str, chapter: int) -> dict:
    path = DATA_ROOT / script / code / f"{chapter:03d}.json"
    with path.open(encoding="utf-8") as handle:
        record = json.load(handle)
    return {
        "heading": record.get("heading", ""),
        "verses": [
            {
                "n": verse["verse"],
                "t": verse["text"],
                "notes": verse.get("notes", []),
            }
            for verse in record["verses"]
        ],
    }


def main() -> None:
    payload = {
        "version": "cunp-web-1",
        "books": [
            {
                "code": code,
                "traditional": traditional,
                "simplified": simplified,
                "chapters": chapters,
                "testament": "old" if index < 39 else "new",
            }
            for index, (code, traditional, simplified, chapters) in enumerate(BOOKS)
        ],
        "chapters": {
            script: {
                code: {
                    str(chapter): load_chapter(script, code, chapter)
                    for chapter in range(1, chapters + 1)
                }
                for code, _traditional, _simplified, chapters in BOOKS
            }
            for script in ("simplified", "traditional")
        },
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    json_text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    OUTPUT.write_text(
        "window.BIBLE_DATA = " + json_text + ";\n",
        encoding="utf-8",
    )
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
