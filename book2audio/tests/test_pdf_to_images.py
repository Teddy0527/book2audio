"""pdf_to_images モジュールのテスト"""

import pytest
from book2audio.pdf_to_images import parse_page_range


class TestParsePageRange:
    def test_none(self):
        assert parse_page_range(None) is None

    def test_single_page(self):
        assert parse_page_range("5") == (5, 5)

    def test_range(self):
        assert parse_page_range("1-10") == (1, 10)

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            parse_page_range("1-2-3")
