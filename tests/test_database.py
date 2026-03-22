"""database.py のユニットテスト（libsql対応）"""

import pytest
import libsql_experimental as libsql

from book2audio.web.database import Database


@pytest.fixture
def db():
    conn = libsql.connect(":memory:")
    database = Database(conn=conn)
    database.init_db()
    yield database
    database.close()


@pytest.fixture
def sample_chapters():
    return [
        {"title": "前書き", "filename": "01_前書き.mp3", "duration_sec": 120.5},
        {"title": "第一章", "filename": "02_第一章.mp3", "duration_sec": 300.0},
        {"title": "第二章", "filename": "03_第二章.mp3", "duration_sec": 250.3},
    ]


class TestInitDb:
    def test_creates_tables(self, db):
        cur = db._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        names = {r[0] for r in cur.fetchall()}
        assert "books" in names
        assert "chapters" in names
        assert "listening_progress" in names
        assert "listening_history" in names

    def test_idempotent(self, db):
        db.init_db()


class TestCreateBook:
    def test_creates_book_and_chapters(self, db, sample_chapters):
        book = db.create_book("abc123", "テスト本", sample_chapters)
        assert book.id == "abc123"
        assert book.title == "テスト本"
        assert book.chapter_count == 3
        assert book.total_duration_sec == pytest.approx(670.8)

    def test_creates_initial_progress(self, db, sample_chapters):
        db.create_book("abc123", "テスト本", sample_chapters)
        progress = db.get_progress("abc123")
        assert progress is not None
        assert progress.current_round == 1
        assert progress.position_sec == 0.0
        assert progress.current_chapter_id is not None

    def test_creates_initial_history(self, db, sample_chapters):
        db.create_book("abc123", "テスト本", sample_chapters)
        history = db.get_history("abc123")
        assert len(history) == 1
        assert history[0].round_number == 1
        assert history[0].completed_at is None


class TestListBooks:
    def test_empty(self, db):
        assert db.list_books() == []

    def test_returns_all_books(self, db, sample_chapters):
        db.create_book("book1", "本A", sample_chapters)
        db.create_book("book2", "本B", sample_chapters[:1])
        books = db.list_books()
        assert len(books) == 2

    def test_includes_round_info(self, db, sample_chapters):
        db.create_book("book1", "本A", sample_chapters)
        books = db.list_books()
        assert books[0]["current_round"] == 1


class TestGetBook:
    def test_returns_none_for_missing(self, db):
        assert db.get_book("nonexistent") is None

    def test_returns_full_details(self, db, sample_chapters):
        db.create_book("abc123", "テスト本", sample_chapters)
        book = db.get_book("abc123")
        assert book is not None
        assert book["title"] == "テスト本"
        assert len(book["chapters"]) == 3
        assert book["chapters"][0]["track_order"] == 1
        assert book["chapters"][2]["track_order"] == 3
        assert book["progress"]["current_round"] == 1

    def test_chapters_ordered(self, db, sample_chapters):
        db.create_book("abc123", "テスト本", sample_chapters)
        book = db.get_book("abc123")
        orders = [ch["track_order"] for ch in book["chapters"]]
        assert orders == [1, 2, 3]


class TestDeleteBook:
    def test_deletes_existing(self, db, sample_chapters):
        db.create_book("abc123", "テスト本", sample_chapters)
        assert db.delete_book("abc123") is True
        assert db.get_book("abc123") is None

    def test_returns_false_for_missing(self, db):
        assert db.delete_book("nonexistent") is False

    def test_cascades_chapters_and_progress(self, db, sample_chapters):
        db.create_book("abc123", "テスト本", sample_chapters)
        db.delete_book("abc123")
        assert db.get_progress("abc123") is None
        assert db.get_chapters("abc123") == []
        assert db.get_history("abc123") == []


class TestUpdateBookTitle:
    def test_updates_title(self, db, sample_chapters):
        db.create_book("abc123", "旧タイトル", sample_chapters)
        assert db.update_book_title("abc123", "新タイトル") is True
        book = db.get_book("abc123")
        assert book["title"] == "新タイトル"

    def test_returns_false_for_missing(self, db):
        assert db.update_book_title("nonexistent", "タイトル") is False


class TestSaveProgress:
    def test_saves_position(self, db, sample_chapters):
        db.create_book("abc123", "テスト本", sample_chapters)
        chapters = db.get_chapters("abc123")
        second_ch = chapters[1]

        assert db.save_progress("abc123", second_ch.id, 45.2) is True

        progress = db.get_progress("abc123")
        assert progress.current_chapter_id == second_ch.id
        assert progress.position_sec == pytest.approx(45.2)

    def test_returns_false_for_missing(self, db):
        assert db.save_progress("nonexistent", 1, 0.0) is False


class TestAdvanceRound:
    def test_advances_to_round_2(self, db, sample_chapters):
        db.create_book("abc123", "テスト本", sample_chapters)
        new_round = db.advance_round("abc123")
        assert new_round == 2

        progress = db.get_progress("abc123")
        assert progress.current_round == 2
        assert progress.position_sec == 0.0

    def test_completes_previous_history(self, db, sample_chapters):
        db.create_book("abc123", "テスト本", sample_chapters)
        db.advance_round("abc123")
        history = db.get_history("abc123")
        assert len(history) == 2
        assert history[0].completed_at is not None
        assert history[1].completed_at is None

    def test_returns_none_for_missing(self, db):
        assert db.advance_round("nonexistent") is None

    def test_multiple_advances(self, db, sample_chapters):
        db.create_book("abc123", "テスト本", sample_chapters)
        db.advance_round("abc123")
        db.advance_round("abc123")
        new_round = db.advance_round("abc123")
        assert new_round == 4


class TestGetChapters:
    def test_returns_ordered_chapters(self, db, sample_chapters):
        db.create_book("abc123", "テスト本", sample_chapters)
        chapters = db.get_chapters("abc123")
        assert len(chapters) == 3
        assert chapters[0].title == "前書き"
        assert chapters[1].title == "第一章"
        assert chapters[2].title == "第二章"

    def test_empty_for_missing_book(self, db):
        assert db.get_chapters("nonexistent") == []
