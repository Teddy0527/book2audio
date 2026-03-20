"""chapter_splitter モジュールのテスト"""

from book2audio.chapter_splitter import split_chapters, _find_chapter_boundaries


class TestFindChapterBoundaries:
    def test_numbered_chapters(self):
        text = "前書き\n第一章 始まり\n本文\n第二章 展開\n本文2"
        boundaries = _find_chapter_boundaries(text)
        assert len(boundaries) == 2
        assert "第一章" in boundaries[0][1]
        assert "第二章" in boundaries[1][1]

    def test_prologue_epilogue(self):
        text = "プロローグ\n冒頭\nエピローグ\n結末"
        boundaries = _find_chapter_boundaries(text)
        assert len(boundaries) == 2

    def test_no_chapters(self):
        text = "普通のテキストだけです。章の区切りはありません。"
        boundaries = _find_chapter_boundaries(text)
        assert len(boundaries) == 0


class TestSplitChapters:
    def test_basic_split(self):
        pages = [
            "前書きテキスト",
            "第一章 始まりの章\n物語が始まる。",
            "第二章 展開の章\n物語が展開する。",
        ]
        chapters = split_chapters(pages)
        assert len(chapters) >= 2

    def test_no_chapters_found(self):
        pages = ["普通のテキスト。", "もっとテキスト。"]
        chapters = split_chapters(pages)
        assert len(chapters) == 1
        assert chapters[0]["title"] == "本文"

    def test_empty_input(self):
        assert split_chapters([]) == []

    def test_toc_detection(self):
        pages = [
            "目次\n第一章...3\n第二章...10",
            "第一章 はじめに\n内容",
            "第二章 つづき\n内容2",
        ]
        chapters = split_chapters(pages)
        # 目次ページ自体は除外される
        for ch in chapters:
            assert "目次" not in ch["title"]
