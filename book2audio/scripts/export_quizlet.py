"""クイズデータをQuizletインポート用TSVで出力。

使い方:
  python3 scripts/export_quizlet.py

出力先: ~/Desktop/競争の戦略_quizlet.tsv
Quizletで「セット作成」→「インポート」→ TSVの中身を貼り付け
"""

from __future__ import annotations

import os
from pathlib import Path

from book2audio.web.database import Database


def main():
    db = Database()
    db.init_db()

    # 書籍を検索
    books = db._fetchall("SELECT * FROM books")
    book = next((b for b in books if "競争" in b["title"]), None)
    if not book:
        print("「競争の戦略」が見つかりません")
        return

    # 全クイズ問題を取得
    questions = db._fetchall(
        "SELECT qq.*, c.title AS chapter_title, c.track_order "
        "FROM quiz_questions qq "
        "JOIN chapters c ON c.id = qq.chapter_id "
        "WHERE qq.book_id = ? "
        "ORDER BY c.track_order, qq.difficulty, qq.id",
        (book["id"],),
    )

    if not questions:
        print("クイズ問題がありません")
        return

    # TSV出力
    output_path = Path.home() / "Desktop" / "競争の戦略_quizlet.tsv"
    lines = []
    seen = set()

    for q in questions:
        # 重複排除（同じ問題が複数パートに紐づいている場合）
        key = q["question"][:50]
        if key in seen:
            continue
        seen.add(key)

        # 答えの改行をセミコロンに変換（Quizletは1行）
        answer = q["answer"].replace("\n", "; ")
        question = q["question"].replace("\t", " ")
        answer = answer.replace("\t", " ")
        lines.append(f"{question}\t{answer}")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    db.close()

    print(f"出力完了: {output_path}")
    print(f"問題数: {len(lines)}")
    print(f"\nQuizletで「セット作成」→「インポート」→ このファイルの中身を貼り付けてください")


if __name__ == "__main__":
    main()
