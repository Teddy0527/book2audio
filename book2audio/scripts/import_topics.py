#!/usr/bin/env python3
"""Import topics from 文字起こし text files into the database.

Parses section headers from transcript files and computes approximate
audio timestamps using character-ratio estimation.

Usage:
    python -m scripts.import_topics --text-dir /path/to/文字起こし --book-id <book_id>

The script is idempotent — re-running replaces existing topics.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from book2audio.web.database import Database


def parse_sections(text: str) -> list[dict]:
    """Extract section headers from transcript text.

    Section headers are non-indented lines that:
    - Are not page markers (<!--p.XX-->)
    - Are not blank
    - Don't start with full-width space (paragraph indent)
    - Are relatively short (< 60 chars, likely a heading)
    """
    sections: list[dict] = []
    total_chars = len(text)
    if total_chars == 0:
        return sections

    current_pos = 0
    for line in text.split("\n"):
        stripped = line.strip()
        # Skip blanks, page markers, indented paragraphs
        if (
            not stripped
            or stripped.startswith("<!--")
            or line.startswith("\u3000")  # full-width space indent
            or line.startswith(" ")
            or len(stripped) > 60
        ):
            current_pos += len(line) + 1
            continue

        # Likely a section header
        char_ratio = current_pos / total_chars
        sections.append({
            "name": stripped,
            "char_position": current_pos,
            "char_ratio": char_ratio,
        })
        current_pos += len(line) + 1

    return sections


def compute_timestamps(
    sections: list[dict], chapter_duration_sec: float
) -> list[dict]:
    """Convert character ratios to approximate audio timestamps."""
    topics: list[dict] = []
    for i, sec in enumerate(sections):
        start_sec = sec["char_ratio"] * chapter_duration_sec
        # End is the start of the next section, or chapter end
        if i + 1 < len(sections):
            end_sec = sections[i + 1]["char_ratio"] * chapter_duration_sec
        else:
            end_sec = chapter_duration_sec
        topics.append({
            "name": sec["name"],
            "start_sec": round(start_sec, 1),
            "end_sec": round(end_sec, 1),
        })
    return topics


def find_matching_chapter(
    chapters: list[dict], text_filename: str
) -> dict | None:
    """Match a text file to a chapter by extracting chapter number."""
    # Extract chapter number from filename like "第1章 業界の構造分析法.txt"
    m = re.search(r"第(\d+)章", text_filename)
    if not m:
        return None
    chapter_num = m.group(0)  # e.g., "第1章"

    for ch in chapters:
        if chapter_num in ch["title"]:
            return ch
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Import topics from transcript files")
    parser.add_argument("--text-dir", required=True, help="Path to 文字起こし directory")
    parser.add_argument("--book-id", required=True, help="Book ID in the database")
    args = parser.parse_args()

    text_dir = Path(args.text_dir)
    if not text_dir.exists():
        print(f"Error: {text_dir} does not exist")
        sys.exit(1)

    db = Database()
    db.init_db()

    # Get book and chapters
    book = db.get_book(args.book_id)
    if not book:
        print(f"Error: Book '{args.book_id}' not found in database")
        sys.exit(1)

    chapters = db.get_chapters(args.book_id)
    if not chapters:
        print(f"Error: No chapters found for book '{args.book_id}'")
        sys.exit(1)

    # Convert chapter rows to dicts for matching
    chapter_dicts = [
        {"id": ch.id, "title": ch.title, "duration_sec": ch.duration_sec}
        for ch in chapters
    ]

    total_imported = 0
    for txt_file in sorted(text_dir.glob("*.txt")):
        ch = find_matching_chapter(chapter_dicts, txt_file.name)
        if not ch:
            print(f"  Skip: {txt_file.name} (no matching chapter)")
            continue

        text = txt_file.read_text(encoding="utf-8")
        sections = parse_sections(text)
        if not sections:
            print(f"  Skip: {txt_file.name} (no sections found)")
            continue

        topics = compute_timestamps(sections, ch["duration_sec"])
        db.set_topics(ch["id"], args.book_id, topics)

        print(f"  {txt_file.name} -> {len(topics)} topics (chapter: {ch['title']})")
        total_imported += len(topics)

    print(f"\nDone: {total_imported} topics imported for book '{book.title}'")
    db.close()


if __name__ == "__main__":
    main()
