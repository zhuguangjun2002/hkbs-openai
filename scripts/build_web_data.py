#!/usr/bin/env python3
"""Build a browser-friendly data bundle for the static Bible reader."""

from __future__ import annotations

import json
from pathlib import Path

from extract_hkbs_cunp import BOOKS


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "web" / "data.js"

TRANSLATIONS = {
    "cunp": {
        "root": ROOT / "data" / "cunp",
        "short_name": "CUNP",
        "names": {
            "simplified": "新标点和合本",
            "traditional": "新標點和合本",
        },
    },
    "rcuv-shen": {
        "root": ROOT / "data" / "rcuv-shen",
        "short_name": "RCUV Shen",
        "names": {
            "simplified": "和合本2010（和修）（神版）",
            "traditional": "和合本2010（和修）（神版）",
        },
    },
}


def load_chapter(data_root: Path, script: str, code: str, chapter: int) -> dict:
    path = data_root / script / code / f"{chapter:03d}.json"
    with path.open(encoding="utf-8") as handle:
        record = json.load(handle)
    return {
        "heading": record.get("heading", ""),
        "verses": [web_verse(verse) for verse in record["verses"]],
    }


def web_verse(verse: dict) -> dict:
    item = {
        "n": verse["verse"],
        "t": verse["text"],
        "notes": verse.get("notes", []),
    }
    if "verse_end" in verse:
        item["end"] = verse["verse_end"]
    if "sequence" in verse:
        item["seq"] = verse["sequence"]
    if "section_headings" in verse:
        item["heads"] = verse["section_headings"]
    return item


def main() -> None:
    payload = {
        "version": "hkbs-web-2",
        "default_translation": "cunp",
        "translations": [
            {
                "id": translation_id,
                "short_name": config["short_name"],
                "names": config["names"],
            }
            for translation_id, config in TRANSLATIONS.items()
        ],
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
            translation_id: {
                script: {
                    code: {
                        str(chapter): load_chapter(config["root"], script, code, chapter)
                        for chapter in range(1, chapters + 1)
                    }
                    for code, _traditional, _simplified, chapters in BOOKS
                }
                for script in ("simplified", "traditional")
            }
            for translation_id, config in TRANSLATIONS.items()
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
