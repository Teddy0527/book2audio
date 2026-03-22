"""ローカルデータをクラウド（Turso + Cloudflare R2）に移行するスクリプト。

使用前に以下の環境変数を設定:
  TURSO_DB_URL       - Turso データベースURL
  TURSO_AUTH_TOKEN    - Turso 認証トークン
  R2_ACCOUNT_ID      - Cloudflare アカウントID
  R2_ACCESS_KEY_ID   - R2 APIアクセスキー
  R2_SECRET_ACCESS_KEY - R2 APIシークレットキー
  R2_BUCKET          - R2 バケット名 (デフォルト: book2audio)

実行:
  python3 scripts/migrate_to_cloud.py
"""

from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

import boto3


def main():
    # ── 環境変数チェック ──
    required = ["TURSO_DB_URL", "TURSO_AUTH_TOKEN", "R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        print(f"エラー: 環境変数が未設定: {', '.join(missing)}")
        sys.exit(1)

    local_data = Path(os.environ.get("BOOK2AUDIO_DATA_DIR", Path.home() / ".book2audio"))
    local_db_path = local_data / "book2audio.db"
    local_audio_dir = local_data / "audio"

    if not local_db_path.exists():
        print(f"エラー: ローカルDB が見つかりません: {local_db_path}")
        sys.exit(1)

    # ── Turso 接続 ──
    import libsql_experimental as libsql
    cloud_conn = libsql.connect(
        database=os.environ["TURSO_DB_URL"],
        auth_token=os.environ["TURSO_AUTH_TOKEN"],
    )

    # ── スキーマ作成 ──
    from book2audio.web.database import Database
    cloud_db = Database(conn=cloud_conn)
    cloud_db.init_db()
    print("Turso: スキーマ作成完了")

    # ── ローカルDB読み込み ──
    local_conn = sqlite3.connect(str(local_db_path))
    local_conn.row_factory = sqlite3.Row

    # books
    books = local_conn.execute("SELECT * FROM books").fetchall()
    for b in books:
        try:
            cloud_conn.execute(
                "INSERT INTO books (id, title, created_at, total_duration_sec, chapter_count) "
                "VALUES (?, ?, ?, ?, ?)",
                (b["id"], b["title"], b["created_at"], b["total_duration_sec"], b["chapter_count"]),
            )
            print(f"  book: {b['title']}")
        except Exception as e:
            print(f"  book skip (exists?): {b['title']} - {e}")

    # chapters
    chapters = local_conn.execute("SELECT * FROM chapters ORDER BY book_id, track_order").fetchall()
    for ch in chapters:
        try:
            cloud_conn.execute(
                "INSERT INTO chapters (id, book_id, title, filename, track_order, duration_sec) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (ch["id"], ch["book_id"], ch["title"], ch["filename"], ch["track_order"], ch["duration_sec"]),
            )
        except Exception as e:
            print(f"  chapter skip: {ch['title']} - {e}")

    # listening_progress
    progress_rows = local_conn.execute("SELECT * FROM listening_progress").fetchall()
    for p in progress_rows:
        try:
            cloud_conn.execute(
                "INSERT INTO listening_progress (book_id, current_chapter_id, position_sec, current_round, updated_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (p["book_id"], p["current_chapter_id"], p["position_sec"], p["current_round"], p["updated_at"]),
            )
        except Exception as e:
            print(f"  progress skip: {e}")

    # listening_history
    history_rows = local_conn.execute("SELECT * FROM listening_history").fetchall()
    for h in history_rows:
        try:
            cloud_conn.execute(
                "INSERT INTO listening_history (id, book_id, round_number, started_at, completed_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (h["id"], h["book_id"], h["round_number"], h["started_at"], h["completed_at"]),
            )
        except Exception as e:
            print(f"  history skip: {e}")

    cloud_conn.commit()
    local_conn.close()
    print(f"Turso: {len(books)}冊, {len(chapters)}章, {len(progress_rows)}進捗, {len(history_rows)}履歴 を移行完了")

    # ── R2 に音声アップロード ──
    if not local_audio_dir.exists():
        print("音声ディレクトリが見つかりません。スキップ。")
        return

    s3 = boto3.client(
        "s3",
        endpoint_url=f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
    )
    bucket = os.environ.get("R2_BUCKET", "book2audio")

    uploaded = 0
    for book_dir in sorted(local_audio_dir.iterdir()):
        if not book_dir.is_dir():
            continue
        book_id = book_dir.name
        for mp3 in sorted(book_dir.glob("*.mp3")):
            key = f"{book_id}/{mp3.name}"
            print(f"  R2 upload: {key} ({mp3.stat().st_size / 1024 / 1024:.1f}MB)")
            s3.upload_file(
                str(mp3), bucket, key,
                ExtraArgs={"ContentType": "audio/mpeg"},
            )
            uploaded += 1

    print(f"R2: {uploaded}ファイルをアップロード完了")
    print("\n移行完了!")


if __name__ == "__main__":
    main()
