"""テキスト整形・クリーニング"""

from __future__ import annotations

import re
import unicodedata


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
    "●": "、",
    "○": "",
    "◆": "",
    "◇": "",
    "▲": "",
    "△": "",
    "▼": "",
    "▽": "",
}

# 数字→日本語変換用の単位
_DIGIT_KANJI = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九"]
_LARGE_UNITS = [(100_000_000, "億"), (10_000, "万"), (1_000, "千"), (100, "百"), (10, "十")]

# 助数詞パターン（数字の後に続く助数詞）
_COUNTER_PATTERN = re.compile(
    r"(\d+)(年|月|日|時|分|秒|人|個|本|冊|枚|台|匹|頭|羽|杯|回|番|階|歳|才|円|万|億|兆|件|軒|着|足|通|点|曲|話|巻|章|節|部|号|割|倍|度|%|ページ|キロ|メートル|センチ|ミリ|グラム|リットル|つ)"
)

# 独立した数字（助数詞なし）
_STANDALONE_NUMBER = re.compile(r"(?<![.\d])(\d+)(?![.\d\w])")


def _arabic_to_japanese(n: int) -> str:
    """アラビア数字を日本語読みに変換する（億まで対応）。"""
    if n == 0:
        return "零"
    if n < 0:
        return "マイナス" + _arabic_to_japanese(-n)

    result = ""
    for unit_val, unit_char in _LARGE_UNITS:
        if n >= unit_val:
            digit = n // unit_val
            if unit_val >= 10_000:
                result += _arabic_to_japanese(digit) + unit_char
            elif digit > 1:
                result += _DIGIT_KANJI[digit] + unit_char
            else:
                result += unit_char
            n %= unit_val

    if n > 0:
        result += _DIGIT_KANJI[n]

    return result

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


def convert_numbers_to_spoken(text: str) -> str:
    """数字を日本語読みに変換する。

    例: 2024年→二千二十四年、5人→五人、3冊→三冊
    """
    # 助数詞付きの数字を変換
    def _replace_counter(m: re.Match) -> str:
        num = int(m.group(1))
        counter = m.group(2)
        return _arabic_to_japanese(num) + counter

    text = _COUNTER_PATTERN.sub(_replace_counter, text)

    # 独立した数字も変換（小数点や英数字の一部でない場合）
    def _replace_standalone(m: re.Match) -> str:
        num = int(m.group(1))
        if num > 999_999_999:  # 億超えは元のまま
            return m.group(0)
        return _arabic_to_japanese(num)

    text = _STANDALONE_NUMBER.sub(_replace_standalone, text)

    return text


def normalize_punctuation_for_tts(text: str) -> str:
    """TTS向けに句読点を正規化する。

    - ！？の後に。がなければ追加
    - 〜→ー（長音記号統一）
    - 重複句読点の整理
    """
    # 〜 → ー（長音記号統一）
    text = text.replace("〜", "ー")

    # ！？の後に句点がなく、文が続く場合に。を追加
    text = re.sub(r"([！？])(?=[^\n！？。」』\s])", r"\1。", text)

    # 重複句読点の整理
    text = re.sub(r"。{2,}", "。", text)
    text = re.sub(r"、{2,}", "、", text)

    return text


def insert_dialogue_pauses(text: str) -> str:
    """会話文の前後に段落区切りを挿入して自然な間を作る。

    地の文→セリフ、セリフ→地の文の切り替わりに\n\nを挿入。
    """
    # 地の文の直後に「が来る場合（句点がない場合は追加）
    text = re.sub(r"([^。\n\s「」『』])(「)", r"\1。\n\n\2", text)
    # 句点の後に「が来る場合
    text = re.sub(r"(。)(「)", r"\1\n\n\2", text)

    # 」の後に地の文が続く場合
    text = re.sub(r"(」)([^\n」『』「\s])", r"\1\n\n\2", text)

    # 『』も同様に処理
    text = re.sub(r"([^。\n\s「」『』])(『)", r"\1。\n\n\2", text)
    text = re.sub(r"(。)(『)", r"\1\n\n\2", text)
    text = re.sub(r"(』)([^\n」『』「\s])", r"\1\n\n\2", text)

    return text


def split_long_sentences(text: str, max_length: int = 80) -> str:
    """長い文を自然な接続助詞の位置で分割する。

    日本語TTSは短い文の方が自然な抑揚を生成する。
    """
    # 接続助詞パターン（分割ポイント）
    split_points = re.compile(r"(が、|けど、|けれど、|ので、|から、|ため、|して、|ており、|ですが、|ますが、)")

    lines = text.split("\n")
    result = []
    for line in lines:
        if len(line) <= max_length:
            result.append(line)
            continue

        # 文ごとに処理
        sentences = re.split(r"(?<=。)", line)
        new_sentences = []
        for sentence in sentences:
            if len(sentence) <= max_length:
                new_sentences.append(sentence)
                continue

            # 接続助詞で分割
            parts = split_points.split(sentence)
            current = ""
            for part in parts:
                if not part:
                    continue
                if split_points.match(part):
                    current += part
                    if len(current) > max_length // 2:
                        new_sentences.append(current.rstrip("、") + "。")
                        current = ""
                else:
                    if current and len(current) + len(part) > max_length:
                        new_sentences.append(current.rstrip("、") + "。")
                        current = part
                    else:
                        current += part

            if current:
                new_sentences.append(current)

        result.append("".join(new_sentences))

    return "\n".join(result)


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
    """テキストを読み上げ用に整形する。

    Args:
        raw_text: 入力テキスト

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

    # 4. 数字→日本語変換
    text = convert_numbers_to_spoken(text)

    # 5. 句読点正規化
    text = normalize_punctuation_for_tts(text)

    # 6. 会話文の間挿入
    text = insert_dialogue_pauses(text)

    # 7. 改行処理
    text = fix_line_breaks(text)

    # 8. 長文分割
    text = split_long_sentences(text)

    # 9. 空白整理
    text = clean_whitespace(text)

    return text
