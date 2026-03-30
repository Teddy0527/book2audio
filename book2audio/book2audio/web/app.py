"""Web UI用FastAPIアプリケーション"""

from __future__ import annotations

import asyncio
import json
import tempfile
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Form, UploadFile
from fastapi.responses import (
    FileResponse, HTMLResponse, RedirectResponse, Response, StreamingResponse,
)
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from book2audio.web.database import Database
from book2audio.web.pipeline import Job, Phase, jobs, run_pipeline
from book2audio.web.storage import (
    delete_book_audio,
    get_audio_url_or_path,
    is_cloud_storage,
    move_audio_to_permanent,
)
from book2audio.tts_backend import get_backend
from book2audio.audio_processor import AudioConfig

# ── グローバル DB インスタンス ─────────────────────────
db: Database | None = None


@asynccontextmanager
async def lifespan(application: FastAPI):
    global db
    db = Database()
    db.init_db()
    yield
    db.close()


app = FastAPI(title="book2audio", lifespan=lifespan)

STATIC_DIR = Path(__file__).parent / "static"

# Static files mount (icons, manifest, etc.)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ── 既存エンドポイント ────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index():
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")


@app.get("/sw.js")
async def service_worker():
    """Service Worker はルート直下で配信（スコープの都合）。"""
    return FileResponse(
        path=str(STATIC_DIR / "sw.js"),
        media_type="application/javascript",
        headers={"Cache-Control": "no-cache"},
    )


@app.get("/favicon.ico")
async def favicon():
    return FileResponse(
        path=str(STATIC_DIR / "icons" / "icon-192x192.png"),
        media_type="image/png",
    )


@app.post("/api/convert")
async def convert(
    text: str = Form(""),
    file: UploadFile | None = None,
    voice: str = Form("ja-JP-NanamiNeural"),
    rate: str = Form("+0%"),
    backend: str = Form("edge-tts"),
    speaker_id: int = Form(1),
    voicevox_url: str = Form("http://localhost:50021"),
    normalize: bool = Form(True),
    paragraph_gap: int = Form(600),
):
    # file優先でテキストを取得
    input_text = ""
    if file and file.filename:
        content = await file.read()
        input_text = content.decode("utf-8")
    elif text:
        input_text = text

    if not input_text.strip():
        return {"error": "テキストまたは.txtファイルを入力してください"}

    # バックエンド設定
    tts_backend = get_backend(
        name=backend,
        voicevox_url=voicevox_url,
        speaker_id=speaker_id,
    )

    # VOICEVOX使用時はvoiceをspeaker_idに
    if backend == "voicevox":
        voice = str(speaker_id)

    # 音声後処理設定
    audio_config = AudioConfig(
        paragraph_gap_ms=paragraph_gap,
        normalize=normalize,
    )

    job_id = uuid.uuid4().hex[:12]
    output_dir = tempfile.mkdtemp(prefix=f"book2audio_{job_id}_")

    jobs[job_id] = Job(output_dir=output_dir)

    asyncio.create_task(run_pipeline(
        job_id=job_id,
        text=input_text,
        output_dir=output_dir,
        voice=voice,
        rate=rate,
        backend=tts_backend,
        audio_config=audio_config,
    ))

    return {"job_id": job_id}


@app.get("/api/progress/{job_id}")
async def progress(job_id: str):
    if job_id not in jobs:
        return StreamingResponse(
            iter([f"data: {json.dumps({'phase': 'error', 'message': 'Job not found'})}\n\n"]),
            media_type="text/event-stream",
        )

    job = jobs[job_id]

    async def event_stream():
        while True:
            event = await job.queue.get()
            data = {
                "phase": event.phase,
                "current": event.current,
                "total": event.total,
                "message": event.message,
            }
            if event.phase == Phase.done:
                data["files"] = job.files
            yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
            if event.phase in (Phase.done, Phase.error):
                break

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/api/download/{job_id}/{filename}")
async def download(job_id: str, filename: str):
    if job_id not in jobs:
        return {"error": "Job not found"}
    job = jobs[job_id]
    filepath = Path(job.output_dir) / "audio" / filename
    if not filepath.exists():
        return {"error": "File not found"}
    return FileResponse(filepath, filename=filename, media_type="audio/mpeg")


@app.get("/api/voices")
async def voices(backend: str = "edge-tts"):
    """利用可能な音声一覧を返す。"""
    try:
        tts_backend = get_backend(name=backend)
        voice_list = await tts_backend.available_voices()
        return [{"id": v.id, "name": v.name, "language": v.language} for v in voice_list]
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/backends")
async def backends():
    """利用可能なバックエンド一覧を返す。"""
    return [
        {"id": "edge-tts", "name": "Edge TTS (Microsoft)", "available": True},
        {"id": "voicevox", "name": "VOICEVOX (ローカル)", "available": True},
    ]


# ── ユーザー API ──────────────────────────────────────

@app.get("/api/users")
async def list_users():
    """ユーザー一覧。"""
    return db.list_users()


# ── ライブラリ API ────────────────────────────────────

@app.get("/api/books")
async def list_books(user_id: str = "koh"):
    """全書籍一覧（ユーザー別進捗サマリー付き）。"""
    return db.list_books(user_id)


@app.get("/api/books/{book_id}")
async def get_book(book_id: str, user_id: str = "koh"):
    """書籍詳細 + 章一覧 + ユーザー別進捗。"""
    db.ensure_progress(user_id, book_id)
    book = db.get_book(book_id, user_id)
    if book is None:
        return Response(
            content=json.dumps({"error": "Book not found"}),
            status_code=404,
            media_type="application/json",
        )
    return book


@app.delete("/api/books/{book_id}")
async def delete_book(book_id: str):
    """書籍・音声ファイル・進捗をすべて削除。"""
    deleted = db.delete_book(book_id)
    if not deleted:
        return Response(
            content=json.dumps({"error": "Book not found"}),
            status_code=404,
            media_type="application/json",
        )
    delete_book_audio(book_id)
    return {"ok": True}


class SaveBookRequest(BaseModel):
    title: str = "無題"


@app.post("/api/books/from-job/{job_id}")
async def save_book_from_job(job_id: str, req: SaveBookRequest):
    """変換ジョブの結果をライブラリに保存。"""
    if job_id not in jobs:
        return Response(
            content=json.dumps({"error": "Job not found"}),
            status_code=404,
            media_type="application/json",
        )

    job = jobs[job_id]
    if job.status != "done":
        return Response(
            content=json.dumps({"error": "Job not completed"}),
            status_code=400,
            media_type="application/json",
        )

    book_id = uuid.uuid4().hex[:12]

    # 一時ディレクトリから永続ストレージへコピー
    chapter_data = move_audio_to_permanent(job.output_dir, book_id)
    if not chapter_data:
        return Response(
            content=json.dumps({"error": "No audio files found"}),
            status_code=400,
            media_type="application/json",
        )

    # DB に登録
    book = db.create_book(book_id, req.title, chapter_data)

    return {
        "book_id": book.id,
        "title": book.title,
        "chapter_count": book.chapter_count,
        "total_duration_sec": book.total_duration_sec,
    }


# ── 音声配信 API ──────────────────────────────────────

@app.get("/api/books/{book_id}/audio/{filename}")
async def serve_audio(book_id: str, filename: str):
    """音声配信。R2ならプリサインURLへリダイレクト、ローカルならFileResponse。"""
    result = get_audio_url_or_path(book_id, filename)

    if isinstance(result, str):
        # R2 プリサインURL → リダイレクト
        return RedirectResponse(url=result, status_code=302)

    # ローカルファイル
    if not result.exists():
        return Response(
            content=json.dumps({"error": "File not found"}),
            status_code=404,
            media_type="application/json",
        )
    return FileResponse(
        path=str(result),
        media_type="audio/mpeg",
        filename=filename,
    )


# ── 進捗 API ─────────────────────────────────────────

@app.get("/api/books/{book_id}/progress")
async def get_progress(book_id: str, user_id: str = "koh"):
    """現在の再生位置・周目を取得。"""
    prog = db.get_progress(user_id, book_id)
    if prog is None:
        return Response(
            content=json.dumps({"error": "Book not found"}),
            status_code=404,
            media_type="application/json",
        )
    return {
        "book_id": prog.book_id,
        "current_chapter_id": prog.current_chapter_id,
        "position_sec": prog.position_sec,
        "current_round": prog.current_round,
        "updated_at": prog.updated_at,
    }


class SaveProgressRequest(BaseModel):
    chapter_id: int
    position_sec: float


@app.put("/api/books/{book_id}/progress")
async def save_progress(book_id: str, req: SaveProgressRequest, user_id: str = "koh"):
    """再生位置を保存。"""
    saved = db.save_progress(user_id, book_id, req.chapter_id, req.position_sec)
    if not saved:
        return Response(
            content=json.dumps({"error": "Book not found"}),
            status_code=404,
            media_type="application/json",
        )
    return {"ok": True}


@app.post("/api/books/{book_id}/complete-round")
async def complete_round(book_id: str, user_id: str = "koh"):
    """現在の周目を完了し、次の周目を開始。"""
    new_round = db.advance_round(user_id, book_id)
    if new_round is None:
        return Response(
            content=json.dumps({"error": "Book not found"}),
            status_code=404,
            media_type="application/json",
        )
    return {"new_round": new_round}


@app.get("/api/books/{book_id}/history")
async def get_history(book_id: str, user_id: str = "koh"):
    """リスニング履歴（全周目）。"""
    rows = db.get_history(user_id, book_id)
    return [
        {
            "round_number": r.round_number,
            "started_at": r.started_at,
            "completed_at": r.completed_at,
        }
        for r in rows
    ]


# ── トピック API ──────────────────────────────────────

@app.get("/api/books/{book_id}/topics")
async def get_book_topics(book_id: str):
    """書籍の全トピック（章ごとにグループ化）を取得。"""
    return db.get_book_topics(book_id)


# ── クイズ API ────────────────────────────────────────

@app.get("/api/books/{book_id}/chapters/{chapter_id}/quiz")
async def get_quiz(book_id: str, chapter_id: int):
    """章のクイズ問題を取得。"""
    questions = db.get_quiz_questions(chapter_id)
    return questions


class QuizAttemptRequest(BaseModel):
    question_id: int
    is_correct: bool


@app.post("/api/books/{book_id}/chapters/{chapter_id}/quiz/attempt")
async def submit_quiz_attempt(
    book_id: str, chapter_id: int, req: QuizAttemptRequest, user_id: str = "koh"
):
    """クイズ回答を記録。"""
    db.save_quiz_attempt(user_id, req.question_id, req.is_correct)
    return {"ok": True}


class QuizBatchRequest(BaseModel):
    results: list[QuizAttemptRequest]


@app.post("/api/books/{book_id}/chapters/{chapter_id}/quiz/batch")
async def submit_quiz_batch(
    book_id: str, chapter_id: int, req: QuizBatchRequest, user_id: str = "koh"
):
    """クイズ結果を一括記録 + 復習スケジュール更新。"""
    correct = 0
    for r in req.results:
        db.save_quiz_attempt(user_id, r.question_id, r.is_correct)
        if r.is_correct:
            correct += 1

    total = len(req.results)
    pct = round(correct / total * 100) if total else 0

    db.update_review_schedule(user_id, chapter_id, pct)

    return {"correct": correct, "total": total, "pct": pct}


@app.get("/api/books/{book_id}/quiz-stats")
async def get_quiz_stats(book_id: str, user_id: str = "koh"):
    """全章のクイズ正答率サマリー。"""
    return db.get_quiz_stats(user_id, book_id)


@app.get("/api/books/{book_id}/reviews")
async def get_reviews(book_id: str, user_id: str = "koh"):
    """今日復習すべき章のリスト。"""
    return db.get_due_reviews(user_id, book_id)


# ── サーバー起動 ──────────────────────────────────────

def start():
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(
        "book2audio.web.app:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
    )


if __name__ == "__main__":
    start()
