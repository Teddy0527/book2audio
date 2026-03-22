"""テキストをセグメントに分割する（音声ファイルの長さ制限対応）"""

from __future__ import annotations

import math


def split_text_by_chars(
    text: str, max_chars: int = 7500, min_chars: int = 3000
) -> list[str]:
    """段落境界でテキストを均等に分割する。

    セグメント数を先に決め、各セグメントが均等な長さになるよう
    段落境界で分割する。短すぎる末尾セグメントを防ぐ。

    Args:
        text: 分割するテキスト
        max_chars: セグメントの最大文字数（デフォルト7500≒20分）
        min_chars: 未使用（互換性のため残す）

    Returns:
        分割されたテキストのリスト
    """
    if not text.strip():
        return []

    total = len(text)
    if total <= max_chars:
        return [text]

    # セグメント数を決定し、均等な目標サイズを計算
    num_segments = math.ceil(total / max_chars)
    target_size = total / num_segments

    paragraphs = text.split("\n\n")
    segments: list[str] = []
    current = ""

    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue

        candidate = current + "\n\n" + paragraph if current else paragraph

        # 目標サイズを超えたら現在のセグメントを保存
        if current and len(candidate) > target_size:
            segments.append(current)
            current = paragraph
        else:
            current = candidate

    if current:
        segments.append(current)

    # 末尾セグメントが短すぎれば前と結合（max_chars以内なら安全）
    while len(segments) >= 2 and len(segments[-1]) < min_chars:
        combined = segments[-2] + "\n\n" + segments[-1]
        if len(combined) <= max_chars:
            segments[-2] = combined
            segments.pop()
        else:
            break

    return segments
