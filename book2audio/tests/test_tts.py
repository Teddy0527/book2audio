"""tts モジュールのテスト"""

from book2audio.tts import _split_text_into_chunks, _sanitize_filename


class TestSplitTextIntoChunks:
    def test_short_text(self):
        chunks = _split_text_into_chunks("短いテキスト。")
        assert len(chunks) == 1
        assert chunks[0] == "短いテキスト。"

    def test_empty_text(self):
        chunks = _split_text_into_chunks("")
        assert len(chunks) == 0

    def test_whitespace_only(self):
        chunks = _split_text_into_chunks("   \n\n  ")
        assert len(chunks) == 0

    def test_long_text_split(self):
        # 2000文字を超えるテキスト
        text = "テスト文。" * 500  # 2500文字
        chunks = _split_text_into_chunks(text, max_size=100)
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) <= 200  # 余裕を持って確認

    def test_paragraph_split(self):
        text = "段落1。" * 50 + "\n\n" + "段落2。" * 50
        chunks = _split_text_into_chunks(text, max_size=200)
        assert len(chunks) >= 2


class TestSanitizeFilename:
    def test_basic(self):
        assert _sanitize_filename("第一章 始まり") == "第一章 始まり"

    def test_special_chars(self):
        result = _sanitize_filename('テスト/ファイル:名*前')
        assert "/" not in result
        assert ":" not in result
        assert "*" not in result

    def test_empty(self):
        assert _sanitize_filename("") == "untitled"

    def test_long_name(self):
        name = "あ" * 100
        result = _sanitize_filename(name)
        assert len(result) <= 80
