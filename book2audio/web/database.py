"""データ層 — 書籍・章・リスニング進捗の永続管理（libsql / SQLite互換）"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True)
class BookRow:
    id: str
    title: str
    created_at: str
    total_duration_sec: float
    chapter_count: int


@dataclass(frozen=True)
class ChapterRow:
    id: int
    book_id: str
    title: str
    filename: str
    track_order: int
    duration_sec: float


@dataclass(frozen=True)
class ProgressRow:
    book_id: str
    current_chapter_id: int | None
    position_sec: float
    current_round: int
    updated_at: str


@dataclass(frozen=True)
class HistoryRow:
    id: int
    book_id: str
    round_number: int
    started_at: str
    completed_at: str | None


_SCHEMA_STATEMENTS = [
    """CREATE TABLE IF NOT EXISTS books (
        id                TEXT PRIMARY KEY,
        title             TEXT NOT NULL,
        created_at        TEXT NOT NULL,
        total_duration_sec REAL NOT NULL DEFAULT 0.0,
        chapter_count     INTEGER NOT NULL DEFAULT 0
    )""",
    """CREATE TABLE IF NOT EXISTS chapters (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id     TEXT NOT NULL REFERENCES books(id) ON DELETE CASCADE,
        title       TEXT NOT NULL,
        filename    TEXT NOT NULL,
        track_order INTEGER NOT NULL,
        duration_sec REAL NOT NULL DEFAULT 0.0,
        UNIQUE(book_id, track_order)
    )""",
    """CREATE TABLE IF NOT EXISTS listening_progress (
        book_id             TEXT PRIMARY KEY REFERENCES books(id) ON DELETE CASCADE,
        current_chapter_id  INTEGER REFERENCES chapters(id),
        position_sec        REAL NOT NULL DEFAULT 0.0,
        current_round       INTEGER NOT NULL DEFAULT 1,
        updated_at          TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS listening_history (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id      TEXT NOT NULL REFERENCES books(id) ON DELETE CASCADE,
        round_number INTEGER NOT NULL,
        started_at   TEXT NOT NULL,
        completed_at TEXT
    )""",
    "CREATE INDEX IF NOT EXISTS idx_chapters_book ON chapters(book_id, track_order)",
    "CREATE INDEX IF NOT EXISTS idx_history_book ON listening_history(book_id, round_number)",
]


def _connect():
    """Turso (libsql) またはローカル SQLite に接続。"""
    turso_url = os.environ.get("TURSO_DB_URL")
    if turso_url:
        import libsql_experimental as libsql
        return libsql.connect(
            database=turso_url,
            auth_token=os.environ.get("TURSO_AUTH_TOKEN", ""),
        )

    # ローカル開発用: sqlite3 互換モードで libsql を使用
    import libsql_experimental as libsql
    data_dir = Path(os.environ.get("BOOK2AUDIO_DATA_DIR", Path.home() / ".book2audio"))
    data_dir.mkdir(parents=True, exist_ok=True)
    return libsql.connect(database=str(data_dir / "book2audio.db"))


def _row_to_dict(cursor_description, row) -> dict:
    """タプル行を列名付き dict に変換。"""
    if row is None:
        return None
    return {desc[0]: val for desc, val in zip(cursor_description, row)}


class Database:
    """シングルユーザー向け DB ラッパー（libsql / Turso 対応）。"""

    def __init__(self, conn=None) -> None:
        self._conn = conn or _connect()

    def init_db(self) -> None:
        """テーブル作成（冪等）。"""
        for stmt in _SCHEMA_STATEMENTS:
            self._conn.execute(stmt)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    # ── helpers ────────────────────────────────────────

    def _fetchone(self, sql: str, params: tuple = ()) -> dict | None:
        cur = self._conn.execute(sql, params)
        row = cur.fetchone()
        if row is None:
            return None
        return _row_to_dict(cur.description, row)

    def _fetchall(self, sql: str, params: tuple = ()) -> list[dict]:
        cur = self._conn.execute(sql, params)
        desc = cur.description
        return [_row_to_dict(desc, r) for r in cur.fetchall()]

    # ── Books ──────────────────────────────────────────

    def create_book(
        self,
        book_id: str,
        title: str,
        chapters: list[dict],
    ) -> BookRow:
        """書籍 + 章を一括登録。"""
        now = _now_iso()
        total_dur = sum(ch["duration_sec"] for ch in chapters)

        self._conn.execute(
            "INSERT INTO books (id, title, created_at, total_duration_sec, chapter_count) "
            "VALUES (?, ?, ?, ?, ?)",
            (book_id, title, now, total_dur, len(chapters)),
        )
        first_chapter_id: int | None = None
        for i, ch in enumerate(chapters):
            cur = self._conn.execute(
                "INSERT INTO chapters (book_id, title, filename, track_order, duration_sec) "
                "VALUES (?, ?, ?, ?, ?)",
                (book_id, ch["title"], ch["filename"], i + 1, ch["duration_sec"]),
            )
            if i == 0:
                first_chapter_id = cur.lastrowid

        self._conn.execute(
            "INSERT INTO listening_progress "
            "(book_id, current_chapter_id, position_sec, current_round, updated_at) "
            "VALUES (?, ?, 0.0, 1, ?)",
            (book_id, first_chapter_id, now),
        )
        self._conn.execute(
            "INSERT INTO listening_history (book_id, round_number, started_at) "
            "VALUES (?, 1, ?)",
            (book_id, now),
        )
        self._conn.commit()

        return BookRow(
            id=book_id,
            title=title,
            created_at=now,
            total_duration_sec=total_dur,
            chapter_count=len(chapters),
        )

    def list_books(self) -> list[dict]:
        """全書籍一覧（進捗サマリー付き）。"""
        rows = self._fetchall(
            "SELECT b.id, b.title, b.created_at, b.total_duration_sec, b.chapter_count, "
            "lp.current_round, lp.updated_at AS last_listened "
            "FROM books b "
            "LEFT JOIN listening_progress lp ON b.id = lp.book_id "
            "ORDER BY b.created_at DESC"
        )
        for r in rows:
            r["current_round"] = r["current_round"] or 1
        return rows

    def get_book(self, book_id: str) -> dict | None:
        """書籍詳細 + 章一覧 + 進捗。"""
        row = self._fetchone("SELECT * FROM books WHERE id = ?", (book_id,))
        if row is None:
            return None

        chapters = self._fetchall(
            "SELECT * FROM chapters WHERE book_id = ? ORDER BY track_order",
            (book_id,),
        )

        progress = self._fetchone(
            "SELECT * FROM listening_progress WHERE book_id = ?", (book_id,)
        )

        return {
            "id": row["id"],
            "title": row["title"],
            "created_at": row["created_at"],
            "total_duration_sec": row["total_duration_sec"],
            "chapter_count": row["chapter_count"],
            "chapters": [
                {
                    "id": ch["id"],
                    "title": ch["title"],
                    "filename": ch["filename"],
                    "track_order": ch["track_order"],
                    "duration_sec": ch["duration_sec"],
                }
                for ch in chapters
            ],
            "progress": {
                "current_chapter_id": progress["current_chapter_id"] if progress else None,
                "position_sec": progress["position_sec"] if progress else 0.0,
                "current_round": progress["current_round"] if progress else 1,
                "updated_at": progress["updated_at"] if progress else None,
            },
        }

    def delete_book(self, book_id: str) -> bool:
        """書籍と関連データを削除。"""
        # libsql で CASCADE が効かない場合に備えて手動削除
        self._conn.execute("DELETE FROM listening_history WHERE book_id = ?", (book_id,))
        self._conn.execute("DELETE FROM listening_progress WHERE book_id = ?", (book_id,))
        self._conn.execute("DELETE FROM chapters WHERE book_id = ?", (book_id,))
        cur = self._conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
        self._conn.commit()
        return cur.rowcount > 0

    def update_book_title(self, book_id: str, title: str) -> bool:
        cur = self._conn.execute(
            "UPDATE books SET title = ? WHERE id = ?", (title, book_id)
        )
        self._conn.commit()
        return cur.rowcount > 0

    # ── Progress ──────────────────────────────────────

    def get_progress(self, book_id: str) -> ProgressRow | None:
        row = self._fetchone(
            "SELECT * FROM listening_progress WHERE book_id = ?", (book_id,)
        )
        if row is None:
            return None
        return ProgressRow(
            book_id=row["book_id"],
            current_chapter_id=row["current_chapter_id"],
            position_sec=row["position_sec"],
            current_round=row["current_round"],
            updated_at=row["updated_at"],
        )

    def save_progress(
        self, book_id: str, chapter_id: int, position_sec: float
    ) -> bool:
        now = _now_iso()
        cur = self._conn.execute(
            "UPDATE listening_progress "
            "SET current_chapter_id = ?, position_sec = ?, updated_at = ? "
            "WHERE book_id = ?",
            (chapter_id, position_sec, now, book_id),
        )
        self._conn.commit()
        return cur.rowcount > 0

    def advance_round(self, book_id: str) -> int | None:
        """現在の周目を完了し、次の周目を開始。"""
        now = _now_iso()

        progress = self.get_progress(book_id)
        if progress is None:
            return None

        current_round = progress.current_round
        new_round = current_round + 1

        first_ch = self._fetchone(
            "SELECT id FROM chapters WHERE book_id = ? ORDER BY track_order LIMIT 1",
            (book_id,),
        )
        first_chapter_id = first_ch["id"] if first_ch else None

        self._conn.execute(
            "UPDATE listening_history SET completed_at = ? "
            "WHERE book_id = ? AND round_number = ? AND completed_at IS NULL",
            (now, book_id, current_round),
        )
        self._conn.execute(
            "INSERT INTO listening_history (book_id, round_number, started_at) "
            "VALUES (?, ?, ?)",
            (book_id, new_round, now),
        )
        self._conn.execute(
            "UPDATE listening_progress "
            "SET current_chapter_id = ?, position_sec = 0.0, "
            "    current_round = ?, updated_at = ? "
            "WHERE book_id = ?",
            (first_chapter_id, new_round, now, book_id),
        )
        self._conn.commit()

        return new_round

    # ── History ───────────────────────────────────────

    def get_history(self, book_id: str) -> list[HistoryRow]:
        rows = self._fetchall(
            "SELECT * FROM listening_history WHERE book_id = ? ORDER BY round_number",
            (book_id,),
        )
        return [
            HistoryRow(
                id=r["id"],
                book_id=r["book_id"],
                round_number=r["round_number"],
                started_at=r["started_at"],
                completed_at=r["completed_at"],
            )
            for r in rows
        ]

    # ── Chapters ──────────────────────────────────────

    def get_chapters(self, book_id: str) -> list[ChapterRow]:
        rows = self._fetchall(
            "SELECT * FROM chapters WHERE book_id = ? ORDER BY track_order",
            (book_id,),
        )
        return [
            ChapterRow(
                id=r["id"],
                book_id=r["book_id"],
                title=r["title"],
                filename=r["filename"],
                track_order=r["track_order"],
                duration_sec=r["duration_sec"],
            )
            for r in rows
        ]
