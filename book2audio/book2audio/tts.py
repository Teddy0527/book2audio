"""Phase 4: 音声合成（Edge TTS → MP3）"""

from __future__ import annotations

import asyncio
import logging
import re
import tempfile
from pathlib import Path

import edge_tts
from mutagen.id3 import ID3, TIT2, TRCK, ID3NoHeaderError
from pydub import AudioSegment

logger = logging.getLogger(__name__)

DEFAULT_VOICE = "ja-JP-NanamiNeural"
DEFAULT_RATE = "+0%"
MAX_CHUNK_SIZE = 2000


def _split_text_into_chunks(text: str, max_size: int = MAX_CHUNK_SIZE) -> list[str]:
    """テキストを句点・段落区切りでチャンク分割する。

    文の途中で切れないよう、句点（。）や段落区切りで分割する。
    """
    if len(text) <= max_size:
        return [text] if text.strip() else []

    chunks: list[str] = []
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
            chunks.append(current)
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
                        chunks.append(current)
                    current = sentence
        else:
            current = paragraph

    if current.strip():
        chunks.append(current)

    return chunks


async def _synthesize_chunk(
    text: str, output_path: str, voice: str, rate: str
) -> None:
    """1チャンクを音声合成してファイルに保存する。"""
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(output_path)


async def synthesize_chapter(
    text: str,
    output_path: str,
    voice: str = DEFAULT_VOICE,
    rate: str = DEFAULT_RATE,
) -> None:
    """テキストを音声合成してMP3ファイルとして保存する。

    Args:
        text: 合成するテキスト
        output_path: 出力MP3ファイルパス
        voice: TTS音声名
        rate: 読み上げ速度
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    chunks = _split_text_into_chunks(text)
    if not chunks:
        logger.warning("空のテキスト。スキップ: %s", output_path)
        return

    if len(chunks) == 1:
        # チャンクが1つなら直接保存
        await _synthesize_chunk(chunks[0], str(output_path), voice, rate)
        logger.info("音声合成完了: %s", output_path)
        return

    # 複数チャンクの場合: 個別に合成してから結合
    combined = AudioSegment.empty()

    with tempfile.TemporaryDirectory() as tmpdir:
        for i, chunk in enumerate(chunks):
            tmp_path = Path(tmpdir) / f"chunk_{i:04d}.mp3"
            await _synthesize_chunk(chunk, str(tmp_path), voice, rate)
            segment = AudioSegment.from_mp3(str(tmp_path))
            combined += segment

    combined.export(str(output_path), format="mp3")
    logger.info("音声合成完了 (%d チャンク結合): %s", len(chunks), output_path)


def _sanitize_filename(name: str) -> str:
    """ファイル名に使用できない文字を除去する。"""
    # ファイル名に不適切な文字を除去
    name = re.sub(r'[\\/:*?"<>|]', "", name)
    name = name.strip()
    return name[:80] if name else "untitled"


def _set_id3_tags(filepath: str, title: str, track_number: int) -> None:
    """MP3ファイルにID3タグを設定する。"""
    try:
        tags = ID3(filepath)
    except ID3NoHeaderError:
        tags = ID3()

    tags.add(TIT2(encoding=3, text=title))
    tags.add(TRCK(encoding=3, text=str(track_number)))
    tags.save(filepath)


async def synthesize_book(
    chapters: list[dict],
    output_dir: str,
    voice: str = DEFAULT_VOICE,
    rate: str = DEFAULT_RATE,
) -> list[str]:
    """全章を音声合成し、ファイルパスのリストを返す。

    Args:
        chapters: [{"title": "...", "text": "..."}, ...]
        output_dir: 出力ディレクトリ
        voice: TTS音声名
        rate: 読み上げ速度

    Returns:
        生成したMP3ファイルパスのリスト
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_paths: list[str] = []

    for i, chapter in enumerate(chapters):
        title = chapter["title"]
        text = chapter["text"]

        if not text.strip():
            logger.warning("空の章をスキップ: %s", title)
            continue

        safe_title = _sanitize_filename(title)
        filename = f"{i + 1:02d}_{safe_title}.mp3"
        filepath = output_dir / filename

        logger.info("章 %d/%d 音声合成中: %s", i + 1, len(chapters), title)
        await synthesize_chapter(text, str(filepath), voice, rate)

        # ID3タグ設定
        _set_id3_tags(str(filepath), title, i + 1)

        output_paths.append(str(filepath))

    logger.info("全章音声合成完了: %d ファイル", len(output_paths))
    return output_paths
