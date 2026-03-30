"""database.py のユニットテスト（マルチユーザー対応）"""

import pytest
import libsql_experimental as libsql

from book2audio.web.database import Database


@pytest.fixture
def db():
    conn = libsql.connect(":memory:")
    database = Database(conn=conn)
    database.init_db()
    database.create_user("koh", "Koh")
    database.create_user("yumi", "Yumi")
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
        assert "users" in names
        assert "books" in names
        assert "chapters" in names
        assert "listening_progress" in names
        assert "listening_history" in names

    def test_idempotent(self, db):
        db.init_db()


class TestUsers:
    def test_create_user(self, db):
        users = db.list_users()
        assert len(users) == 2
        names = {u["name"] for u in users}
        assert "Koh" in names
        assert "Yumi" in names

    def test_create_user_idempotent(self, db):
        db.create_user("koh", "Koh")
        users = db.list_users()
        assert len(users) == 2


class TestCreateBook:
    def test_creates_book_and_chapters(self, db, sample_chapters):
        book = db.create_book("abc123", "テスト本", sample_chapters)
        assert book.id == "abc123"
        assert book.title == "テスト本"
        assert book.chapter_count == 3
        assert book.total_duration_sec == pytest.approx(670.8)

    def test_no_progress_created_on_book_creation(self, db, sample_chapters):
        db.create_book("abc123", "テスト本", sample_chapters)
        # 進捗はensure_progressで作成されるまで存在しない
        progress = db.get_progress("koh", "abc123")
        assert progress is None


class TestEnsureProgress:
    def test_creates_progress_for_user(self, db, sample_chapters):
        db.create_book("abc123", "テスト本", sample_chapters)
        db.ensure_progress("koh", "abc123")
        progress = db.get_progress("koh", "abc123")
        assert progress is not None
        assert progress.user_id == "koh"
        assert progress.current_round == 1
        assert progress.position_sec == 0.0

    def test_separate_progress_per_user(self, db, sample_chapters):
        db.create_book("abc123", "テスト本", sample_chapters)
        db.ensure_progress("koh", "abc123")
        db.ensure_progress("yumi", "abc123")

        koh_prog = db.get_progress("koh", "abc123")
        yumi_prog = db.get_progress("yumi", "abc123")
        assert koh_prog.user_id == "koh"
        assert yumi_prog.user_id == "yumi"

    def test_idempotent(self, db, sample_chapters):
        db.create_book("abc123", "テスト本", sample_chapters)
        db.ensure_progress("koh", "abc123")
        db.ensure_progress("koh", "abc123")  # no error
        progress = db.get_progress("koh", "abc123")
        assert progress is not None


class TestListBooks:
    def test_empty(self, db):
        assert db.list_books("koh") == []

    def test_returns_all_books(self, db, sample_chapters):
        db.create_book("book1", "本A", sample_chapters)
        db.create_book("book2", "本B", sample_chapters[:1])
        books = db.list_books("koh")
        assert len(books) == 2

    def test_user_specific_progress(self, db, sample_chapters):
        db.create_book("book1", "本A", sample_chapters)
        db.ensure_progress("koh", "book1")
        db.advance_round("koh", "book1")

        koh_books = db.list_books("koh")
        yumi_books = db.list_books("yumi")
        assert koh_books[0]["current_round"] == 2
        assert yumi_books[0]["current_round"] == 1  # default (no progress)


class TestGetBook:
    def test_returns_none_for_missing(self, db):
        assert db.get_book("nonexistent", "koh") is None

    def test_returns_full_details(self, db, sample_chapters):
        db.create_book("abc123", "テスト本", sample_chapters)
        db.ensure_progress("koh", "abc123")
        book = db.get_book("abc123", "koh")
        assert book is not None
        assert book["title"] == "テスト本"
        assert len(book["chapters"]) == 3
        assert book["progress"]["current_round"] == 1

    def test_user_specific_progress(self, db, sample_chapters):
        db.create_book("abc123", "テスト本", sample_chapters)
        db.ensure_progress("koh", "abc123")
        db.ensure_progress("yumi", "abc123")
        chapters = db.get_chapters("abc123")

        # Kohが進捗を保存
        db.save_progress("koh", "abc123", chapters[1].id, 45.0)

        koh_book = db.get_book("abc123", "koh")
        yumi_book = db.get_book("abc123", "yumi")
        assert koh_book["progress"]["position_sec"] == 45.0
        assert yumi_book["progress"]["position_sec"] == 0.0


class TestDeleteBook:
    def test_deletes_existing(self, db, sample_chapters):
        db.create_book("abc123", "テスト本", sample_chapters)
        assert db.delete_book("abc123") is True
        assert db.get_book("abc123", "koh") is None

    def test_returns_false_for_missing(self, db):
        assert db.delete_book("nonexistent") is False

    def test_cascades_all_user_progress(self, db, sample_chapters):
        db.create_book("abc123", "テスト本", sample_chapters)
        db.ensure_progress("koh", "abc123")
        db.ensure_progress("yumi", "abc123")
        db.delete_book("abc123")
        assert db.get_progress("koh", "abc123") is None
        assert db.get_progress("yumi", "abc123") is None


class TestSaveProgress:
    def test_saves_position(self, db, sample_chapters):
        db.create_book("abc123", "テスト本", sample_chapters)
        db.ensure_progress("koh", "abc123")
        chapters = db.get_chapters("abc123")

        assert db.save_progress("koh", "abc123", chapters[1].id, 45.2) is True
        progress = db.get_progress("koh", "abc123")
        assert progress.current_chapter_id == chapters[1].id
        assert progress.position_sec == pytest.approx(45.2)

    def test_independent_per_user(self, db, sample_chapters):
        db.create_book("abc123", "テスト本", sample_chapters)
        db.ensure_progress("koh", "abc123")
        db.ensure_progress("yumi", "abc123")
        chapters = db.get_chapters("abc123")

        db.save_progress("koh", "abc123", chapters[2].id, 100.0)
        db.save_progress("yumi", "abc123", chapters[0].id, 30.0)

        koh = db.get_progress("koh", "abc123")
        yumi = db.get_progress("yumi", "abc123")
        assert koh.current_chapter_id == chapters[2].id
        assert yumi.current_chapter_id == chapters[0].id

    def test_returns_false_for_missing(self, db):
        assert db.save_progress("koh", "nonexistent", 1, 0.0) is False


class TestAdvanceRound:
    def test_advances_to_round_2(self, db, sample_chapters):
        db.create_book("abc123", "テスト本", sample_chapters)
        db.ensure_progress("koh", "abc123")
        new_round = db.advance_round("koh", "abc123")
        assert new_round == 2

    def test_independent_per_user(self, db, sample_chapters):
        db.create_book("abc123", "テスト本", sample_chapters)
        db.ensure_progress("koh", "abc123")
        db.ensure_progress("yumi", "abc123")

        db.advance_round("koh", "abc123")
        db.advance_round("koh", "abc123")

        koh = db.get_progress("koh", "abc123")
        yumi = db.get_progress("yumi", "abc123")
        assert koh.current_round == 3
        assert yumi.current_round == 1

    def test_returns_none_for_missing(self, db):
        assert db.advance_round("koh", "nonexistent") is None


class TestGetChapters:
    def test_returns_ordered_chapters(self, db, sample_chapters):
        db.create_book("abc123", "テスト本", sample_chapters)
        chapters = db.get_chapters("abc123")
        assert len(chapters) == 3
        assert chapters[0].title == "前書き"

    def test_empty_for_missing_book(self, db):
        assert db.get_chapters("nonexistent") == []
