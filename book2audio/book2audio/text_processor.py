"""Phase 3a: テキスト整形・クリーニング"""

from __future__ import annotations

import re
import unicodedata


# OCR誤認識の補正マップ
OCR_CORRECTIONS: dict[str, str] = {
    "口ロ": "ロ",   # 漢字の口→カタカナのロ（文脈依存のため最低限）
}

# 読み上げ用の記号置換
SYMBOL_REPLACEMENTS: dict[str, str] = {
    "……": "、",
    "…": "、",
    "――": "、",
    "──": "、",
    "—―": "、",
    "──": "、",
    "※": "",
    "＊": "",
    "☆": "",
    "★": "",
    "■": "",
    "□": "",
    "●": "",
    "○": "",
    "◆": "",
    "◇": "",
    "▲": "",
    "△": "",
    "▼": "",
    "▽": "",
}

# ルビパターン: 漢字の後に括弧でふりがなが付く形式
RUBY_PATTERN = re.compile(r"([\u4e00-\u9fff]+)[（(]([\u3040-\u309f]+)[）)]")


def normalize_width(text: str) -> str:
    """全角英数字を半角に、半角カタカナを全角に統一する。"""
    # 全角英数字→半角
    result = []
    for char in text:
        name = unicodedata.name(char, "")
        if "FULLWIDTH LATIN" in name or "FULLWIDTH DIGIT" in name:
            result.append(unicodedata.normalize("NFKC", char))
        elif "HALFWIDTH KATAKANA" in name:
            result.append(unicodedata.normalize("NFKC", char))
        else:
            result.append(char)
    return "".join(result)


def remove_ruby_text(text: str) -> str:
    """括弧付きルビを除去する（漢字のみ残す）。"""
    return RUBY_PATTERN.sub(r"\1", text)


def fix_line_breaks(text: str) -> str:
    """不要な改行を除去し、段落区切りは保持する。

    - 2つ以上の連続改行 → 段落区切り（改行2つ）
    - 文中の単一改行 → 除去（前の行が句読点で終わらない場合）
    """
    # まず改行を正規化
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 3つ以上の連続改行を2つに
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 段落区切りを一時マーカーに置換
    text = text.replace("\n\n", "<<PARA>>")

    # 文中の単一改行を処理
    lines = text.split("\n")
    merged = []
    for i, line in enumerate(lines):
        if not line.strip():
            merged.append(line)
            continue
        # 前の行が句読点で終わっていない場合は結合
        if merged and merged[-1] and not merged[-1].rstrip().endswith(("。", "」", "』", "！", "？", "…")):
            merged[-1] = merged[-1].rstrip() + line.lstrip()
        else:
            merged.append(line)

    text = "\n".join(merged)

    # 段落区切りを復元
    text = text.replace("<<PARA>>", "\n\n")

    return text


def replace_symbols(text: str) -> str:
    """読み上げ用に記号を置換する。"""
    for symbol, replacement in SYMBOL_REPLACEMENTS.items():
        text = text.replace(symbol, replacement)
    return text


def clean_whitespace(text: str) -> str:
    """余分な空白を整理する。"""
    # 行頭・行末の空白を除去
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)
    # 連続する空白を1つに
    text = re.sub(r"[ \t]+", " ", text)
    # 空行の連続を最大2つに
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean_text(raw_text: str) -> str:
    """OCR生テキストを読み上げ用に整形する。

    Args:
        raw_text: OCRから得られた生テキスト

    Returns:
        整形済みテキスト
    """
    text = raw_text

    # 1. 全角半角統一
    text = normalize_width(text)

    # 2. ルビ除去
    text = remove_ruby_text(text)

    # 3. 記号置換
    text = replace_symbols(text)

    # 4. 改行処理
    text = fix_line_breaks(text)

    # 5. 空白整理
    text = clean_whitespace(text)

    return text
