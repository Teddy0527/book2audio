"""Phase 4: 音声合成（TTS → MP3）"""

from __future__ import annotations

import asyncio
import logging
import re
import tempfile
from pathlib import Path

from mutagen.id3 import ID3, TIT2, TRCK, TALB, ID3NoHeaderError
from pydub import AudioSegment

from book2audio.audio_processor import (
    AudioConfig,
    ChunkResult,
    BOUNDARY_PARAGRAPH,
    BOUNDARY_SENTENCE,
    insert_silence_between_chunks,
    post_process,
)
from book2audio.segment_splitter import split_text_by_chars
from book2audio.tts_backend import TTSBackend, EdgeTTSBackend, get_backend

logger = logging.getLogger(__name__)

DEFAULT_VOICE = "ja-JP-NanamiNeural"
DEFAULT_RATE = "+0%"
MAX_CHUNK_SIZE = 2000


def _split_text_into_chunks(
    text: str, max_size: int = MAX_CHUNK_SIZE
) -> list[tuple[str, str]]:
    """テキストを句点・段落区切りでチャンク分割する。

    Returns:
        [(text, boundary_type), ...] のリスト。
        boundary_type は "paragraph" または "sentence"。
    """
    if not text.strip():
        return []

    if len(text) <= max_size:
        return [(text, BOUNDARY_PARAGRAPH)]

    chunks: list[tuple[str, str]] = []
    current = ""

    # まず段落で分割
    paragraphs = text.split("\n\n")

    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue

        if len(current) + len(paragraph) + 2 <= max_size:
            current = current + "\n\n" + paragraph if current else paragraph
            continue

        # 現在のチャンクを保存
        if current:
            chunks.append((current, BOUNDARY_PARAGRAPH))
            current = ""

        # 段落自体が大きい場合、文単位で分割
        if len(paragraph) > max_size:
            sentences = re.split(r"(?<=。)", paragraph)
            for sentence in sentences:
                if not sentence.strip():
                    continue
                if len(current) + len(sentence) <= max_size:
                    current += sentence
                else:
                    if current:
                        chunks.append((current, BOUNDARY_SENTENCE))
                    current = sentence
        else:
            current = paragraph

    if current.strip():
        chunks.append((current, BOUNDARY_PARAGRAPH))

    return chunks


async def _synthesize_chunk(
    text: str, output_path: str, voice: str, rate: str,
    backend: TTSBackend | None = None,
) -> None:
    """1チャンクを音声合成してファイルに保存する。"""
    if backend is None:
        backend = EdgeTTSBackend()
    await backend.synthesize_chunk(text, output_path, voice, rate)


async def synthesize_chapter(
    text: str,
    output_path: str,
    voice: str = DEFAULT_VOICE,
    rate: str = DEFAULT_RATE,
    backend: TTSBackend | None = None,
    audio_config: AudioConfig | None = None,
) -> None:
    """テキストを音声合成してMP3ファイルとして保存する。

    Args:
        text: 合成するテキスト
        output_path: 出力MP3ファイルパス
        voice: TTS音声名
        rate: 読み上げ速度
        backend: TTSバックエンド（省略時はEdge TTS）
        audio_config: 音声後処理設定（省略時はデフォルト）
    """
    if backend is None:
        backend = EdgeTTSBackend()
    if audio_config is None:
        audio_config = AudioConfig()

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    max_size = backend.max_chunk_size
    chunks = _split_text_into_chunks(text, max_size=max_size)
    if not chunks:
        logger.warning("空のテキスト。スキップ: %s", output_path)
        return

    if len(chunks) == 1 and not audio_config.normalize:
        # チャンクが1つで後処理不要なら直接保存
        await backend.synthesize_chunk(chunks[0][0], str(output_path), voice, rate)
        logger.info("音声合成完了: %s", output_path)
        return

    # 複数チャンク or 後処理あり: 個別に合成してから結合
    chunk_results: list[ChunkResult] = []

    with tempfile.TemporaryDirectory() as tmpdir:
        for i, (chunk_text, boundary_type) in enumerate(chunks):
            tmp_path = Path(tmpdir) / f"chunk_{i:04d}.mp3"
            await backend.synthesize_chunk(chunk_text, str(tmp_path), voice, rate)
            segment = AudioSegment.from_mp3(str(tmp_path))
            chunk_results.append(ChunkResult(audio=segment, boundary_type=boundary_type))

    # チャンク間に無音を挿入して結合
    combined = insert_silence_between_chunks(chunk_results, audio_config)

    # 後処理（章無音 + 音量正規化）
    combined = post_process(combined, audio_config)

    combined.export(str(output_path), format="mp3")
    logger.info("音声合成完了 (%d チャンク結合): %s", len(chunks), output_path)


def _sanitize_filename(name: str) -> str:
    """ファイル名に使用できない文字を除去する。"""
    # ファイル名に不適切な文字を除去
    name = re.sub(r'[\\/:*?"<>|]', "", name)
    name = name.strip()
    return name[:80] if name else "untitled"


def _set_id3_tags(
    filepath: str, title: str, track_number: int, album: str | None = None
) -> None:
    """MP3ファイルにID3タグを設定する。"""
    try:
        tags = ID3(filepath)
    except ID3NoHeaderError:
        tags = ID3()

    tags.add(TIT2(encoding=3, text=title))
    tags.add(TRCK(encoding=3, text=str(track_number)))
    if album:
        tags.add(TALB(encoding=3, text=album))
    tags.save(filepath)


async def synthesize_book(
    chapters: list[dict],
    output_dir: str,
    voice: str = DEFAULT_VOICE,
    rate: str = DEFAULT_RATE,
    backend: TTSBackend | None = None,
    audio_config: AudioConfig | None = None,
    max_chars: int = 0,
    album: str | None = None,
) -> list[str]:
    """全章を音声合成し、ファイルパスのリストを返す。

    Args:
        chapters: [{"title": "...", "text": "..."}, ...]
        output_dir: 出力ディレクトリ
        voice: TTS音声名
        rate: 読み上げ速度
        backend: TTSバックエンド（省略時はEdge TTS）
        audio_config: 音声後処理設定（省略時はデフォルト）
        max_chars: セグメント分割の最大文字数（0=分割なし）
        album: ID3タグのアルバム名

    Returns:
        生成したMP3ファイルパスのリスト
    """
    if backend is None:
        backend = EdgeTTSBackend()
    if audio_config is None:
        audio_config = AudioConfig()

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_paths: list[str] = []
    track_number = 0

    for i, chapter in enumerate(chapters):
        title = chapter["title"]
        text = chapter["text"]

        if not text.strip():
            logger.warning("空の章をスキップ: %s", title)
            continue

        safe_title = _sanitize_filename(title)

        # セグメント分割
        if max_chars > 0:
            segments = split_text_by_chars(text, max_chars=max_chars)
        else:
            segments = [text]

        for j, segment_text in enumerate(segments):
            track_number += 1

            if len(segments) > 1:
                filename = f"{i:02d}_{safe_title}_part{j + 1:02d}.mp3"
                segment_title = f"{title} (Part {j + 1})"
            else:
                filename = f"{i:02d}_{safe_title}.mp3"
                segment_title = title

            filepath = output_dir / filename

            logger.info(
                "章 %d/%d 音声合成中: %s (%d/%d セグメント, %d文字)",
                i + 1, len(chapters), title, j + 1, len(segments), len(segment_text),
            )
            await synthesize_chapter(
                segment_text, str(filepath), voice, rate,
                backend=backend, audio_config=audio_config,
            )

            # ID3タグ設定
            _set_id3_tags(str(filepath), segment_title, track_number, album=album)

            output_paths.append(str(filepath))

    logger.info("全章音声合成完了: %d ファイル", len(output_paths))
    return output_paths
