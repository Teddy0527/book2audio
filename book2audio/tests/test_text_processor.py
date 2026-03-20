"""text_processor モジュールのテスト"""

from book2audio.text_processor import (
    normalize_width,
    remove_ruby_text,
    replace_symbols,
    fix_line_breaks,
    clean_text,
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
