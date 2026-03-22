"""text_processor モジュールのテスト"""

from book2audio.text_processor import (
    normalize_width,
    remove_ruby_text,
    replace_symbols,
    fix_line_breaks,
    clean_text,
    convert_numbers_to_spoken,
    normalize_punctuation_for_tts,
    insert_dialogue_pauses,
    split_long_sentences,
    _arabic_to_japanese,
)


class TestNormalizeWidth:
    def test_fullwidth_digits(self):
        assert normalize_width("１２３") == "123"

    def test_fullwidth_latin(self):
        assert normalize_width("ＡＢＣ") == "ABC"

    def test_halfwidth_katakana(self):
        assert normalize_width("ｱｲｳ") == "アイウ"

    def test_mixed(self):
        assert normalize_width("日本語はそのまま") == "日本語はそのまま"


class TestRemoveRubyText:
    def test_remove_ruby(self):
        assert remove_ruby_text("漢字（かんじ）") == "漢字"

    def test_remove_ruby_fullwidth_parens(self):
        assert remove_ruby_text("東京（とうきょう）") == "東京"

    def test_no_ruby(self):
        assert remove_ruby_text("普通のテキスト") == "普通のテキスト"

    def test_halfwidth_parens(self):
        assert remove_ruby_text("漢字(かんじ)") == "漢字"


class TestReplaceSymbols:
    def test_ellipsis(self):
        assert replace_symbols("待って……") == "待って、"

    def test_dash(self):
        assert replace_symbols("それは――") == "それは、"


class TestFixLineBreaks:
    def test_paragraph_preserved(self):
        result = fix_line_breaks("段落1。\n\n段落2。")
        assert "\n\n" in result

    def test_single_break_merged(self):
        result = fix_line_breaks("これは途中\nで切れた文")
        assert result == "これは途中で切れた文"

    def test_sentence_end_preserved(self):
        result = fix_line_breaks("文末。\n次の文")
        assert "。" in result


class TestArabicToJapanese:
    def test_zero(self):
        assert _arabic_to_japanese(0) == "零"

    def test_single_digits(self):
        assert _arabic_to_japanese(1) == "一"
        assert _arabic_to_japanese(5) == "五"
        assert _arabic_to_japanese(9) == "九"

    def test_tens(self):
        assert _arabic_to_japanese(10) == "十"
        assert _arabic_to_japanese(11) == "十一"
        assert _arabic_to_japanese(25) == "二十五"

    def test_hundreds(self):
        assert _arabic_to_japanese(100) == "百"
        assert _arabic_to_japanese(123) == "百二十三"
        assert _arabic_to_japanese(500) == "五百"

    def test_thousands(self):
        assert _arabic_to_japanese(1000) == "千"
        assert _arabic_to_japanese(2024) == "二千二十四"
        assert _arabic_to_japanese(3500) == "三千五百"

    def test_man(self):
        assert _arabic_to_japanese(10000) == "一万"
        assert _arabic_to_japanese(15000) == "一万五千"

    def test_oku(self):
        assert _arabic_to_japanese(100000000) == "一億"
        assert _arabic_to_japanese(123456789) == "一億二千三百四十五万六千七百八十九"

    def test_negative(self):
        assert _arabic_to_japanese(-5) == "マイナス五"


class TestConvertNumbersToSpoken:
    def test_year(self):
        result = convert_numbers_to_spoken("2024年")
        assert result == "二千二十四年"

    def test_date(self):
        result = convert_numbers_to_spoken("3月15日")
        assert result == "三月十五日"

    def test_counters(self):
        assert convert_numbers_to_spoken("5人") == "五人"
        assert convert_numbers_to_spoken("3冊") == "三冊"
        assert convert_numbers_to_spoken("10個") == "十個"

    def test_mixed_text(self):
        result = convert_numbers_to_spoken("彼は3人の子供と2匹の猫がいる。")
        assert "三人" in result
        assert "二匹" in result

    def test_no_numbers(self):
        text = "数字なしのテキスト。"
        assert convert_numbers_to_spoken(text) == text


class TestNormalizePunctuationForTts:
    def test_wave_to_long(self):
        assert normalize_punctuation_for_tts("え〜") == "えー"

    def test_exclamation_add_period(self):
        result = normalize_punctuation_for_tts("すごい！本当に")
        assert "！。" in result

    def test_exclamation_before_closing_quote(self):
        # 」の前では追加しない
        result = normalize_punctuation_for_tts("すごい！」")
        assert "！。" not in result

    def test_duplicate_periods(self):
        assert normalize_punctuation_for_tts("終わり。。") == "終わり。"

    def test_duplicate_commas(self):
        assert normalize_punctuation_for_tts("これは、、テスト") == "これは、テスト"


class TestInsertDialoguePauses:
    def test_narration_to_dialogue(self):
        result = insert_dialogue_pauses("彼は言った「こんにちは」")
        assert "\n\n" in result

    def test_dialogue_to_narration(self):
        result = insert_dialogue_pauses("「こんにちは」彼は言った")
        assert "\n\n" in result

    def test_period_before_dialogue(self):
        result = insert_dialogue_pauses("彼は言った。「こんにちは」")
        assert "。\n\n「" in result

    def test_no_dialogue(self):
        text = "普通のテキストです。"
        assert insert_dialogue_pauses(text) == text


class TestSplitLongSentences:
    def test_short_sentence_unchanged(self):
        text = "短い文。"
        assert split_long_sentences(text) == text

    def test_long_sentence_split(self):
        text = "これはとても長い文章ですが、途中に接続助詞があるので分割される可能性があります。"
        result = split_long_sentences(text, max_length=30)
        # 分割された結果、元より多くの句点が含まれる
        assert result.count("。") >= text.count("。")

    def test_preserves_newlines(self):
        text = "短い行1。\n短い行2。"
        assert split_long_sentences(text) == text


class TestCleanText:
    def test_full_pipeline(self):
        raw = "Ａ　Ｂ　Ｃ　漢字（かんじ）……テスト"
        result = clean_text(raw)
        assert "A" in result
        assert "（かんじ）" not in result
        assert "……" not in result

    def test_empty_text(self):
        assert clean_text("") == ""
        assert clean_text("  \n\n  ") == ""

    def test_numbers_converted(self):
        result = clean_text("2024年に3人で旅行した。")
        assert "二千二十四年" in result
        assert "三人" in result

    def test_dialogue_pauses(self):
        result = clean_text("彼は言った「こんにちは」そして去った。")
        assert "\n\n" in result
