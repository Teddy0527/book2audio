"""Phase 3b: 章分割"""

from __future__ import annotations

import re
import logging

logger = logging.getLogger(__name__)

# 章タイトルパターン
CHAPTER_PATTERNS = [
    re.compile(r"^第[一二三四五六七八九十百\d]+章\s*.+", re.MULTILINE),
    re.compile(r"^第[一二三四五六七八九十百\d]+節\s*.+", re.MULTILINE),
    re.compile(r"^第[一二三四五六七八九十百\d]+部\s*.+", re.MULTILINE),
    re.compile(r"^[一二三四五六七八九十]+\s+.+", re.MULTILINE),
    re.compile(r"^\d+\.\s+.+", re.MULTILINE),
    re.compile(r"^Chapter\s+\d+", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^プロローグ", re.MULTILINE),
    re.compile(r"^エピローグ", re.MULTILINE),
    re.compile(r"^あとがき", re.MULTILINE),
    re.compile(r"^まえがき", re.MULTILINE),
    re.compile(r"^はじめに", re.MULTILINE),
    re.compile(r"^おわりに", re.MULTILINE),
    re.compile(r"^序章", re.MULTILINE),
    re.compile(r"^終章", re.MULTILINE),
]

# 目次検出キーワード
TOC_KEYWORDS = ["目次", "もくじ", "CONTENTS", "Contents", "contents"]


def _detect_toc_page(pages_text: list[str]) -> int | None:
    """目次ページのインデックスを返す。見つからなければNone。"""
    for i, text in enumerate(pages_text):
        for keyword in TOC_KEYWORDS:
            if keyword in text:
                logger.info("目次ページ検出: ページ %d", i + 1)
                return i
    return None


def _find_chapter_boundaries(full_text: str) -> list[tuple[int, str]]:
    """テキスト内の章タイトルの位置とタイトル文字列を返す。

    Returns:
        [(文字位置, タイトル文字列), ...] のリスト（出現順）
    """
    boundaries: list[tuple[int, str]] = []
    seen_positions: set[int] = set()

    for pattern in CHAPTER_PATTERNS:
        for match in pattern.finditer(full_text):
            pos = match.start()
            if pos not in seen_positions:
                seen_positions.add(pos)
                title = match.group(0).strip()
                boundaries.append((pos, title))

    # 位置でソート
    boundaries.sort(key=lambda x: x[0])
    return boundaries


def split_chapters(pages_text: list[str]) -> list[dict]:
    """ページテキストのリストから章分割する。

    Args:
        pages_text: 各ページのテキストのリスト

    Returns:
        [{"title": "第1章 ...", "text": "..."}, ...] のリスト
    """
    if not pages_text:
        return []

    # 目次ページを検出（目次自体は本文に含めない）
    toc_index = _detect_toc_page(pages_text)

    # 全ページのテキストを結合（目次ページ以降）
    start_index = (toc_index + 1) if toc_index is not None else 0
    content_pages = pages_text[start_index:]

    if not content_pages:
        content_pages = pages_text

    full_text = "\n\n".join(content_pages)

    # 章の境界を検出
    boundaries = _find_chapter_boundaries(full_text)

    if not boundaries:
        # 章区切りが見つからない場合は全体を1章として扱う
        logger.warning("章区切りが検出されませんでした。全体を1章として処理します。")
        return [{"title": "本文", "text": full_text}]

    # 章に分割
    chapters: list[dict] = []

    # 最初の章の前にテキストがある場合
    if boundaries[0][0] > 0:
        preamble = full_text[: boundaries[0][0]].strip()
        if preamble:
            chapters.append({"title": "前書き", "text": preamble})

    for i, (pos, title) in enumerate(boundaries):
        # 次の章の開始位置まで、または末尾まで
        if i + 1 < len(boundaries):
            end_pos = boundaries[i + 1][0]
        else:
            end_pos = len(full_text)

        text = full_text[pos:end_pos].strip()
        # タイトル行自体をテキストから除去（重複読み上げ防止）
        text = text[len(title) :].strip()

        chapters.append({"title": title, "text": text})

    logger.info("章分割完了: %d 章検出", len(chapters))
    return chapters
