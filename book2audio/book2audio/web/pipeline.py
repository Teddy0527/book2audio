"""Web UI用パイプラインランナー + 進捗管理"""

from __future__ import annotations

import asyncio
import logging
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from book2audio.pdf_to_images import pdf_to_images, get_pdf_page_count
from book2audio.ocr import ocr_page, _get_vision_client
from book2audio.text_processor import clean_text
from book2audio.chapter_splitter import split_chapters
from book2audio.tts import synthesize_chapter, _sanitize_filename, _set_id3_tags

logger = logging.getLogger(__name__)


class Phase(str, Enum):
    pdf_to_images = "pdf_to_images"
    ocr = "ocr"
    text_processing = "text_processing"
    tts = "tts"
    done = "done"
    error = "error"


@dataclass
class ProgressEvent:
    phase: str
    current: int
    total: int
    message: str


@dataclass
class Job:
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    status: str = "running"
    output_dir: str = ""
    files: list[str] = field(default_factory=list)
    error: str | None = None


jobs: dict[str, Job] = {}


async def run_pipeline(
    job_id: str,
    pdf_path: str,
    output_dir: str,
    voice: str = "ja-JP-NanamiNeural",
    rate: str = "+0%",
    dpi: int = 300,
    pages: str | None = None,
    remove_ruby: bool = True,
) -> None:
    """パイプライン全体を実行し、進捗をキューに送信する。"""
    job = jobs[job_id]
    job.output_dir = output_dir
    tmp_img_dir = tempfile.mkdtemp()

    try:
        # 認証チェック（PDF変換前に失敗させる）
        _get_vision_client()

        # Phase 1: PDF → 画像変換（バッチ処理 + 進捗表示）
        total_pages = await asyncio.to_thread(get_pdf_page_count, pdf_path)
        loop = asyncio.get_running_loop()
        queue = job.queue

        def on_pdf_progress(completed: int, total: int) -> None:
            loop.call_soon_threadsafe(
                queue.put_nowait,
                ProgressEvent(
                    phase=Phase.pdf_to_images,
                    current=completed,
                    total=total,
                    message=f"PDF → 画像変換中... ({completed}/{total} ページ)",
                ),
            )

        await job.queue.put(ProgressEvent(
            phase=Phase.pdf_to_images, current=0, total=total_pages,
            message="PDF → 画像変換中...",
        ))
        image_paths = await asyncio.to_thread(
            pdf_to_images, pdf_path, tmp_img_dir,
            dpi=dpi, pages=pages, on_progress=on_pdf_progress,
        )
        await job.queue.put(ProgressEvent(
            phase=Phase.pdf_to_images, current=total_pages, total=total_pages,
            message=f"{len(image_paths)} ページの画像を生成",
        ))

        # Phase 2: OCR
        pages_text: list[str] = []
        total_pages = len(image_paths)
        for i, img_path in enumerate(image_paths):
            await job.queue.put(ProgressEvent(
                phase=Phase.ocr, current=i, total=total_pages,
                message=f"OCR処理中... ({i + 1}/{total_pages})",
            ))
            text = await asyncio.to_thread(ocr_page, img_path, remove_ruby)
            pages_text.append(text)
        await job.queue.put(ProgressEvent(
            phase=Phase.ocr, current=total_pages, total=total_pages,
            message=f"OCR完了: {total_pages} ページ",
        ))

        # Phase 3: テキスト整形・章分割
        await job.queue.put(ProgressEvent(
            phase=Phase.text_processing, current=0, total=1,
            message="テキスト整形・章分割中...",
        ))
        cleaned_pages = [clean_text(page) for page in pages_text]
        chapters = split_chapters(cleaned_pages)
        await job.queue.put(ProgressEvent(
            phase=Phase.text_processing, current=1, total=1,
            message=f"{len(chapters)} 章を検出",
        ))

        # Phase 4: 音声合成
        audio_dir = Path(output_dir) / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)
        total_chapters = len(chapters)
        output_files: list[str] = []

        for i, chapter in enumerate(chapters):
            title = chapter["title"]
            text = chapter["text"]
            await job.queue.put(ProgressEvent(
                phase=Phase.tts, current=i, total=total_chapters,
                message=f"音声合成中: {title} ({i + 1}/{total_chapters})",
            ))

            if not text.strip():
                continue

            safe_title = _sanitize_filename(title)
            filename = f"{i + 1:02d}_{safe_title}.mp3"
            filepath = audio_dir / filename

            await synthesize_chapter(text, str(filepath), voice, rate)
            _set_id3_tags(str(filepath), title, i + 1)
            output_files.append(filename)

        await job.queue.put(ProgressEvent(
            phase=Phase.tts, current=total_chapters, total=total_chapters,
            message=f"音声合成完了: {len(output_files)} ファイル",
        ))

        # 完了
        job.status = "done"
        job.files = output_files
        await job.queue.put(ProgressEvent(
            phase=Phase.done, current=0, total=0,
            message="変換完了",
        ))

    except Exception as e:
        logger.exception("パイプラインエラー: %s", e)
        job.status = "error"
        job.error = str(e)
        await job.queue.put(ProgressEvent(
            phase=Phase.error, current=0, total=0,
            message=str(e),
        ))

    finally:
        # temp画像ディレクトリを削除
        import shutil
        shutil.rmtree(tmp_img_dir, ignore_errors=True)
