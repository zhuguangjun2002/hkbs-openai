#!/usr/bin/env python3
"""Extract HKBS Chinese Bible chapters.

This script fetches public chapter pages such as:
https://rcuv.hkbs.org.hk/CUNP1/GEN/1/
https://rcuv.hkbs.org.hk/RCUV1/GEN/1/

Check HKBS licensing/terms before bulk downloading or redistributing text.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BASE_URL = "https://rcuv.hkbs.org.hk/{version}/{book}/{chapter}/"
TRANSLATIONS = {
    "cunp": {
        "traditional": {
            "code": "CUNP1",
            "name": "新標點和合本(神)",
        },
        "simplified": {
            "code": "CUNP1s",
            "name": "新标点和合本",
        },
    },
    "rcuv-shen": {
        "traditional": {
            "code": "RCUV1",
            "name": "和合本2010 (和修) (神版)",
        },
        "simplified": {
            "code": "RCUV1s",
            "name": "和合本2010 (和修)（神版）",
        },
    },
}


BOOKS = [
    ("GEN", "創世記", "创世记", 50),
    ("EXO", "出埃及記", "出埃及记", 40),
    ("LEV", "利未記", "利未记", 27),
    ("NUM", "民數記", "民数记", 36),
    ("DEU", "申命記", "申命记", 34),
    ("JOS", "約書亞記", "约书亚记", 24),
    ("JDG", "士師記", "士师记", 21),
    ("RUT", "路得記", "路得记", 4),
    ("1SA", "撒母耳記上", "撒母耳记上", 31),
    ("2SA", "撒母耳記下", "撒母耳记下", 24),
    ("1KI", "列王紀上", "列王纪上", 22),
    ("2KI", "列王紀下", "列王纪下", 25),
    ("1CH", "歷代志上", "历代志上", 29),
    ("2CH", "歷代志下", "历代志下", 36),
    ("EZR", "以斯拉記", "以斯拉记", 10),
    ("NEH", "尼希米記", "尼希米记", 13),
    ("EST", "以斯帖記", "以斯帖记", 10),
    ("JOB", "約伯記", "约伯记", 42),
    ("PSA", "詩篇", "诗篇", 150),
    ("PRO", "箴言", "箴言", 31),
    ("ECC", "傳道書", "传道书", 12),
    ("SNG", "雅歌", "雅歌", 8),
    ("ISA", "以賽亞書", "以赛亚书", 66),
    ("JER", "耶利米書", "耶利米书", 52),
    ("LAM", "耶利米哀歌", "耶利米哀歌", 5),
    ("EZK", "以西結書", "以西结书", 48),
    ("DAN", "但以理書", "但以理书", 12),
    ("HOS", "何西阿書", "何西阿书", 14),
    ("JOL", "約珥書", "约珥书", 3),
    ("AMO", "阿摩司書", "阿摩司书", 9),
    ("OBA", "俄巴底亞書", "俄巴底亚书", 1),
    ("JON", "約拿書", "约拿书", 4),
    ("MIC", "彌迦書", "弥迦书", 7),
    ("NAM", "那鴻書", "那鸿书", 3),
    ("HAB", "哈巴谷書", "哈巴谷书", 3),
    ("ZEP", "西番雅書", "西番雅书", 3),
    ("HAG", "哈該書", "哈该书", 2),
    ("ZEC", "撒迦利亞書", "撒迦利亚书", 14),
    ("MAL", "瑪拉基書", "玛拉基书", 4),
    ("MAT", "馬太福音", "马太福音", 28),
    ("MRK", "馬可福音", "马可福音", 16),
    ("LUK", "路加福音", "路加福音", 24),
    ("JHN", "約翰福音", "约翰福音", 21),
    ("ACT", "使徒行傳", "使徒行传", 28),
    ("ROM", "羅馬書", "罗马书", 16),
    ("1CO", "哥林多前書", "哥林多前书", 16),
    ("2CO", "哥林多後書", "哥林多后书", 13),
    ("GAL", "加拉太書", "加拉太书", 6),
    ("EPH", "以弗所書", "以弗所书", 6),
    ("PHP", "腓立比書", "腓立比书", 4),
    ("COL", "歌羅西書", "歌罗西书", 4),
    ("1TH", "帖撒羅尼迦前書", "帖撒罗尼迦前书", 5),
    ("2TH", "帖撒羅尼迦後書", "帖撒罗尼迦后书", 3),
    ("1TI", "提摩太前書", "提摩太前书", 6),
    ("2TI", "提摩太後書", "提摩太后书", 4),
    ("TIT", "提多書", "提多书", 3),
    ("PHM", "腓利門書", "腓利门书", 1),
    ("HEB", "希伯來書", "希伯来书", 13),
    ("JAS", "雅各書", "雅各书", 5),
    ("1PE", "彼得前書", "彼得前书", 5),
    ("2PE", "彼得後書", "彼得后书", 3),
    ("1JN", "約翰一書", "约翰一书", 5),
    ("2JN", "約翰二書", "约翰二书", 1),
    ("3JN", "約翰三書", "约翰三书", 1),
    ("JUD", "猶大書", "犹大书", 1),
    ("REV", "啟示錄", "启示录", 22),
]

BOOK_BY_CODE = {code: (traditional, simplified, chapters) for code, traditional, simplified, chapters in BOOKS}


@dataclass
class Verse:
    number: int
    end: int | None
    text: str
    notes: list[str]


class ChapterParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_heading = False
        self.in_verse_num = False
        self.in_verse_text = False
        self.current_num: int | None = None
        self.current_end: int | None = None
        self.current_text: list[str] = []
        self.current_notes: list[str] = []
        self.heading_parts: list[str] = []
        self.headings: list[str] = []
        self.verses: list[Verse] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag == "h3":
            self.in_heading = True
        elif tag == "b":
            self._flush_verse()
            self.in_verse_num = True
        elif tag == "span" and self.current_num is not None:
            self.in_verse_text = True
        elif tag == "sup" and self.current_num is not None:
            title = attrs_dict.get("title")
            if title:
                self.current_notes.append(normalize_text(title))

    def handle_endtag(self, tag: str) -> None:
        if tag == "h3":
            heading = normalize_text("".join(self.heading_parts))
            if heading:
                self.headings.append(heading)
            self.heading_parts = []
            self.in_heading = False
        elif tag == "b":
            self.in_verse_num = False
        elif tag == "span":
            self.in_verse_text = False

    def handle_data(self, data: str) -> None:
        if self.in_heading:
            self.heading_parts.append(data)
        elif self.in_verse_num:
            number = data.strip()
            match = re.match(r"(\d+)(?:\s*[-–—]\s*(\d+))?", number)
            if match:
                self.current_num = int(match.group(1))
                if match.group(2):
                    self.current_end = int(match.group(2))
        elif self.in_verse_text:
            self.current_text.append(data)

    def close(self) -> None:
        self._flush_verse()
        super().close()

    def _flush_verse(self) -> None:
        if self.current_num is None:
            return
        text = normalize_text("".join(self.current_text))
        self.verses.append(Verse(self.current_num, self.current_end, text, self.current_notes))
        self.current_num = None
        self.current_end = None
        self.current_text = []
        self.current_notes = []


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def chapter_fragment(page_html: str, version_code: str) -> str:
    bible_marker = 'name="bible"'
    bible_start = page_html.find(bible_marker)
    if bible_start != -1:
        content_start = page_html.find(">", bible_start)
        end = page_html.find("</textarea>", content_start)
        if content_start != -1 and end != -1:
            return page_html[content_start + 1:end]

    end = page_html.rfind(f"{version_code}|")
    if end == -1:
        raise ValueError("could not find chapter metadata footer")

    start = page_html.rfind("<h3>", 0, end)
    if start == -1:
        raise ValueError("could not find chapter start")

    return page_html[start:end]


def fetch_html(url: str, timeout: int) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": "hkbs-cunp-extractor/0.1 (+personal research; respectful rate limit)",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def parse_chapter(page_html: str, version_code: str) -> tuple[str, list[Verse]]:
    parser = ChapterParser()
    parser.feed(chapter_fragment(page_html, version_code))
    parser.close()
    heading = parser.headings[0] if parser.headings else ""
    if not parser.verses:
        raise ValueError("no verses parsed from chapter")
    return heading, parser.verses


def iter_targets(book: str | None, chapter: int | None) -> Iterable[tuple[str, str, str, int]]:
    if book:
        code = book.upper()
        if code not in BOOK_BY_CODE:
            raise SystemExit(f"unknown book code: {book}")
        traditional, simplified, chapters = BOOK_BY_CODE[code]
        if chapter:
            if chapter < 1 or chapter > chapters:
                raise SystemExit(f"{code} chapter must be between 1 and {chapters}")
            yield code, traditional, simplified, chapter
        else:
            for chapter_num in range(1, chapters + 1):
                yield code, traditional, simplified, chapter_num
        return

    for code, traditional, simplified, chapters in BOOKS:
        for chapter_num in range(1, chapters + 1):
            yield code, traditional, simplified, chapter_num


def chapter_record(
    translation: str,
    script: str,
    code: str,
    book_name: str,
    chapter: int,
    timeout: int,
    retries: int,
    retry_delay: float,
) -> dict:
    version = TRANSLATIONS[translation][script]
    version_code = version["code"]
    url = BASE_URL.format(version=version_code, book=code, chapter=chapter)
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            heading, verses = parse_chapter(fetch_html(url, timeout), version_code)
            break
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            last_error = exc
            if attempt >= retries:
                raise
            time.sleep(max(retry_delay, 0))
    else:
        raise RuntimeError(f"failed to fetch {url}: {last_error}")

    return {
        "translation": translation,
        "version": version_code,
        "version_name": version["name"],
        "script": script,
        "book_code": code,
        "book_name": book_name,
        "chapter": chapter,
        "heading": heading,
        "source_url": url,
        "verses": [verse_record(verse) for verse in verses],
    }


def verse_record(verse: Verse) -> dict:
    record = {"verse": verse.number}
    if verse.end is not None and verse.end != verse.number:
        record["verse_end"] = verse.end
    record["text"] = verse.text
    record["notes"] = verse.notes
    return record


def write_record(record: dict, output: Path | None, fmt: str) -> None:
    if fmt == "json":
        text = json.dumps(record, ensure_ascii=False, indent=2)
    else:
        rows = []
        for verse in record["verses"]:
            rows.append(
                {
                    "version": record["version"],
                    "version_name": record["version_name"],
                    "script": record["script"],
                    "book_code": record["book_code"],
                    "book_name": record["book_name"],
                    "chapter": record["chapter"],
                    **verse,
                }
            )
        text = "\n".join(json.dumps(row, ensure_ascii=False) for row in rows)

    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


def job_output(output_dir: Path | None, script: str, code: str, chapter: int, fmt: str) -> Path | None:
    if not output_dir:
        return None
    suffix = "jsonl" if fmt == "jsonl" else "json"
    return output_dir / script / code / f"{chapter:03d}.{suffix}"


def run_job(
    index: int,
    total: int,
    script: str,
    code: str,
    name: str,
    chapter: int,
    args: argparse.Namespace,
) -> tuple[int, str]:
    label = f"[{index}/{total}] {script} {code} {chapter}"
    output = job_output(args.output_dir, script, code, chapter, args.format)
    if output and output.exists() and not args.force:
        return index, f"{label} skip existing {output}"

    print(f"{label} fetch", file=sys.stderr)
    try:
        record = chapter_record(
            args.translation,
            script,
            code,
            name,
            chapter,
            args.timeout,
            args.retries,
            args.retry_delay,
        )
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        raise RuntimeError(f"{label} failed: {exc}") from exc
    write_record(record, output, args.format)
    if output:
        return index, f"{label} wrote {output}"
    return index, f"{label} done"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--translation",
        choices=sorted(TRANSLATIONS),
        default="cunp",
        help="HKBS translation/version family; default: cunp",
    )
    parser.add_argument("--book", help="book code, for example GEN, PHP, REV")
    parser.add_argument("--chapter", type=int, help="chapter number")
    parser.add_argument("--all", action="store_true", help="fetch all 66 books")
    parser.add_argument(
        "--script",
        choices=["traditional", "simplified", "both"],
        default="both",
        help="which script to fetch; default: both",
    )
    parser.add_argument("--delay", type=float, default=1.0, help="seconds between requests")
    parser.add_argument("--workers", type=int, default=1, help="parallel download workers")
    parser.add_argument("--retries", type=int, default=3, help="retry failed chapter requests")
    parser.add_argument("--retry-delay", type=float, default=5.0, help="seconds between retries")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--format", choices=["json", "jsonl"], default="json")
    parser.add_argument("--output-dir", type=Path, help="write one file per chapter")
    parser.add_argument("--force", action="store_true", help="overwrite existing output files")
    args = parser.parse_args()

    if not args.all and not args.book:
        parser.error("use --book CODE [--chapter N] or --all")
    if args.all and (args.book or args.chapter):
        parser.error("--all cannot be combined with --book or --chapter")
    if args.chapter and not args.book:
        parser.error("--chapter requires --book")
    if args.all and not args.output_dir:
        parser.error("--all requires --output-dir")

    targets = list(iter_targets(None if args.all else args.book, args.chapter))
    scripts = ["traditional", "simplified"] if args.script == "both" else [args.script]
    jobs = [
        (script, code, traditional if script == "traditional" else simplified, chapter)
        for code, traditional, simplified, chapter in targets
        for script in scripts
    ]

    total = len(jobs)
    if args.workers <= 1:
        for index, (script, code, name, chapter) in enumerate(jobs, start=1):
            try:
                _, message = run_job(index, total, script, code, name, chapter, args)
            except RuntimeError as exc:
                print(f"[{index}/{total}] {script} {code} {chapter} failed: {exc}", file=sys.stderr)
                return 1
            print(message, file=sys.stderr)
            if index < total:
                time.sleep(max(args.delay, 0))
        return 0

    def submit_next(executor: ThreadPoolExecutor, job_iter: Iterable[tuple[int, tuple[str, str, str, int]]]):
        try:
            index, (script, code, name, chapter) = next(job_iter)
        except StopIteration:
            return None
        if index > 1 and args.delay > 0:
            time.sleep(args.delay)
        return executor.submit(run_job, index, total, script, code, name, chapter, args)

    with ThreadPoolExecutor(max_workers=max(args.workers, 1)) as executor:
        job_iter = iter(enumerate(jobs, start=1))
        pending = set()
        for _ in range(min(args.workers, total)):
            future = submit_next(executor, job_iter)
            if future:
                pending.add(future)

        while pending:
            done = next(as_completed(pending))
            pending.remove(done)
            try:
                _, message = done.result()
            except RuntimeError as exc:
                print(f"failed: {exc}", file=sys.stderr)
                return 1
            print(message, file=sys.stderr)

            future = submit_next(executor, job_iter)
            if future:
                pending.add(future)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
