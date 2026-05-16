#!/usr/bin/env python3
"""Verify extracted HKBS per-chapter JSON data."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from extract_hkbs_cunp import BASE_URL, BOOKS, TRANSLATIONS


SCRIPTS = ("traditional", "simplified")


@dataclass
class Stats:
    expected: int = 0
    files: int = 0
    missing: int = 0
    invalid: int = 0
    unexpected: int = 0
    empty: int = 0
    bad_first: int = 0
    bad_metadata: int = 0
    bad_translation: int = 0
    bad_path: int = 0
    bad_verse: int = 0
    bad_verse_order: int = 0
    bad_verse_end: int = 0
    duplicate_verses: int = 0
    verse_end_files: int = 0
    verse_end_count: int = 0
    gaps_without_range: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def add_error(self, field_name: str, message: str) -> None:
        setattr(self, field_name, getattr(self, field_name) + 1)
        self.errors.append(message)


def expected_paths(root: Path) -> set[Path]:
    paths = set()
    for script in SCRIPTS:
        for code, _traditional, _simplified, chapters in BOOKS:
            for chapter in range(1, chapters + 1):
                paths.add(root / script / code / f"{chapter:03d}.json")
    return paths


def load_json(path: Path, stats: Stats) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        stats.add_error("invalid", f"{path}: invalid JSON: {exc}")
        return None
    if not isinstance(data, dict):
        stats.add_error("invalid", f"{path}: top-level JSON value is not an object")
        return None
    return data


def verify_dataset(root: Path) -> Stats:
    stats = Stats()
    translation = root.name
    if translation not in TRANSLATIONS:
        stats.add_error(
            "bad_translation",
            f"{root}: directory name is not a known translation: {translation}",
        )
        return stats

    expected = expected_paths(root)
    actual = set(root.glob("*/*/*.json"))
    stats.expected = len(expected)
    stats.files = len(actual)

    for path in sorted(expected - actual):
        stats.add_error("missing", f"{path}: missing chapter file")

    for path in sorted(actual - expected):
        stats.add_error("unexpected", f"{path}: unexpected chapter file")

    for path in sorted(actual & expected):
        data = load_json(path, stats)
        if data is None:
            continue
        verify_chapter(path, data, translation, stats)

    return stats


def verify_chapter(path: Path, data: dict[str, Any], translation: str, stats: Stats) -> None:
    script = path.parts[-3]
    book_code = path.parts[-2]
    chapter_text = path.stem
    chapter = int(chapter_text)
    traditional, simplified, _chapters = book_lookup(book_code)
    expected_book_name = traditional if script == "traditional" else simplified
    expected_version = TRANSLATIONS[translation][script]["code"]
    expected_version_name = TRANSLATIONS[translation][script]["name"]
    expected_url = BASE_URL.format(version=expected_version, book=book_code, chapter=chapter)

    expected_fields = {
        "translation": translation,
        "version": expected_version,
        "version_name": expected_version_name,
        "script": script,
        "book_code": book_code,
        "book_name": expected_book_name,
        "chapter": chapter,
        "source_url": expected_url,
    }
    for key, expected_value in expected_fields.items():
        if data.get(key) != expected_value:
            stats.add_error(
                "bad_metadata",
                f"{path}: {key} is {data.get(key)!r}, expected {expected_value!r}",
            )

    if data.get("translation") != translation:
        stats.add_error(
            "bad_translation",
            f"{path}: translation is {data.get('translation')!r}, expected {translation!r}",
        )
    if data.get("script") != script or data.get("book_code") != book_code or data.get("chapter") != chapter:
        stats.add_error("bad_path", f"{path}: metadata does not match path")

    verses = data.get("verses")
    if not isinstance(verses, list):
        stats.add_error("bad_verse", f"{path}: verses is not a list")
        return
    if not verses:
        stats.add_error("empty", f"{path}: verses is empty")
        return

    previous_start: int | None = None
    file_has_verse_end = False
    for index, verse in enumerate(verses):
        if not isinstance(verse, dict):
            stats.add_error("bad_verse", f"{path}: verse #{index + 1} is not an object")
            continue
        start = verse.get("verse")
        end = verse.get("verse_end")
        if not isinstance(start, int):
            stats.add_error("bad_verse", f"{path}: verse #{index + 1} has non-integer verse")
            continue
        if previous_start is not None and start < previous_start:
            stats.add_error(
                "bad_verse_order",
                f"{path}: verse number {start} does not increase after {previous_start}",
            )
        elif previous_start is not None and start == previous_start:
            stats.duplicate_verses += 1
        previous_start = start

        if "text" not in verse or not isinstance(verse.get("text"), str):
            stats.add_error("bad_verse", f"{path}: verse {start} has invalid text")
        if "notes" not in verse or not isinstance(verse.get("notes"), list):
            stats.add_error("bad_verse", f"{path}: verse {start} has invalid notes")
        if end is not None:
            file_has_verse_end = True
            stats.verse_end_count += 1
            if not isinstance(end, int) or end <= start:
                stats.add_error(
                    "bad_verse_end",
                    f"{path}: verse {start} has invalid verse_end {end!r}",
                )

    first = verses[0].get("verse") if isinstance(verses[0], dict) else None
    if first != 1:
        stats.add_error("bad_first", f"{path}: first parsed verse is {first!r}, expected 1")
    if file_has_verse_end:
        stats.verse_end_files += 1

    count_gaps_without_ranges(path, verses, stats)


def count_gaps_without_ranges(path: Path, verses: list[Any], stats: Stats) -> None:
    for current, following in zip(verses, verses[1:]):
        if not isinstance(current, dict) or not isinstance(following, dict):
            continue
        start = current.get("verse")
        end = current.get("verse_end")
        next_start = following.get("verse")
        if not isinstance(start, int) or not isinstance(next_start, int):
            continue
        if next_start > start + 1 and end != next_start - 1:
            stats.gaps_without_range += 1


def book_lookup(code: str) -> tuple[str, str, int]:
    for book_code, traditional, simplified, chapters in BOOKS:
        if book_code == code:
            return traditional, simplified, chapters
    raise KeyError(code)


def print_stats(root: Path, stats: Stats, max_errors: int) -> None:
    print(root)
    print(f"  expected: {stats.expected}")
    print(f"  files: {stats.files}")
    print(
        "  errors: "
        f"missing={stats.missing} invalid={stats.invalid} unexpected={stats.unexpected} "
        f"empty={stats.empty} metadata={stats.bad_metadata} path={stats.bad_path} "
        f"translation={stats.bad_translation} first={stats.bad_first} "
        f"verse={stats.bad_verse} order={stats.bad_verse_order} verse_end={stats.bad_verse_end}"
    )
    print(f"  verse_end: files={stats.verse_end_files} ranges={stats.verse_end_count}")
    print(f"  duplicate_verse_numbers: {stats.duplicate_verses}")
    print(f"  source_gaps_without_range: {stats.gaps_without_range}")
    print(f"  result: {'ok' if stats.ok else 'failed'}")
    for error in stats.errors[:max_errors]:
        print(f"  - {error}")
    if len(stats.errors) > max_errors:
        print(f"  ... {len(stats.errors) - max_errors} more errors")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("roots", nargs="+", type=Path, help="dataset roots such as data/cunp")
    parser.add_argument("--max-errors", type=int, default=20, help="errors to print per dataset")
    args = parser.parse_args()

    failed = False
    for index, root in enumerate(args.roots):
        if index:
            print()
        stats = verify_dataset(root)
        print_stats(root, stats, args.max_errors)
        failed = failed or not stats.ok
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
