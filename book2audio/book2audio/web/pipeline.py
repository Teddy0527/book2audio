"""Web UI用パイプラインランナー + 進捗管理"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from book2audio.text_processor import clean_text
from book2audio.chapter_splitter import split_chapters_from_text
from book2audio.tts import synthesize_chapter, _sanitize_filename, _set_id3_tags
from book2audio.tts_backend import TTSBackend, EdgeTTSBackend
from book2audio.audio_processor import AudioConfig

logger = logging.getLogger(__name__)


class Phase(str, Enum):
    text_processing = "text_processing"
    tts = "tts"
    post_processing = "post_processing"
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
    text: str,
    output_dir: str,
    voice: str = "ja-JP-NanamiNeural",
    rate: str = "+0%",
    backend: TTSBackend | None = None,
    audio_config: AudioConfig | None = None,
) -> None:
    """パイプライン全体を実行し、進捗をキューに送信する。"""
    if backend is None:
        backend = EdgeTTSBackend()
    if audio_config is None:
        audio_config = AudioConfig()

    job = jobs[job_id]
    job.output_dir = output_dir

    try:
        # Phase 1: テキスト整形・章分割
        await job.queue.put(ProgressEvent(
            phase=Phase.text_processing, current=0, total=1,
            message="テキスト整形・章分割中...",
        ))
        cleaned = clean_text(text)
        chapters = split_chapters_from_text(cleaned)
        await job.queue.put(ProgressEvent(
            phase=Phase.text_processing, current=1, total=1,
            message=f"{len(chapters)} 章を検出",
        ))

        # Phase 2: 音声合成
        audio_dir = Path(output_dir) / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)
        total_chapters = len(chapters)
        output_files: list[str] = []

        for i, chapter in enumerate(chapters):
            title = chapter["title"]
            ch_text = chapter["text"]
            await job.queue.put(ProgressEvent(
                phase=Phase.tts, current=i, total=total_chapters,
                message=f"音声合成中: {title} ({i + 1}/{total_chapters})",
            ))

            if not ch_text.strip():
                continue

            safe_title = _sanitize_filename(title)
            filename = f"{i + 1:02d}_{safe_title}.mp3"
            filepath = audio_dir / filename

            await synthesize_chapter(
                ch_text, str(filepath), voice, rate,
                backend=backend, audio_config=audio_config,
            )
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
