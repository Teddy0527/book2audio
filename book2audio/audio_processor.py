"""音声後処理パイプライン"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from pydub import AudioSegment

logger = logging.getLogger(__name__)


@dataclass
class AudioConfig:
    """音声後処理の設定"""
    paragraph_gap_ms: int = 600     # 段落間の無音
    sentence_gap_ms: int = 200      # 文間の無音
    chapter_intro_ms: int = 1000    # 章頭の無音
    chapter_outro_ms: int = 1500    # 章末の無音
    normalize: bool = True          # 音量正規化
    target_dbfs: float = -20.0      # 目標音量 (dBFS)


# チャンクの境界タイプ
BOUNDARY_PARAGRAPH = "paragraph"
BOUNDARY_SENTENCE = "sentence"


@dataclass
class ChunkResult:
    """チャンクの合成結果 + メタデータ"""
    audio: AudioSegment
    boundary_type: str = BOUNDARY_PARAGRAPH  # paragraph or sentence


def insert_silence_between_chunks(
    chunks: list[ChunkResult],
    config: AudioConfig | None = None,
) -> AudioSegment:
    """チャンク間に適切な無音を挿入して結合する。

    段落境界=paragraph_gap_ms、文境界=sentence_gap_msの無音を挿入。
    """
    if config is None:
        config = AudioConfig()

    if not chunks:
        return AudioSegment.empty()

    combined = chunks[0].audio

    for chunk in chunks[1:]:
        if chunk.boundary_type == BOUNDARY_PARAGRAPH:
            gap_ms = config.paragraph_gap_ms
        else:
            gap_ms = config.sentence_gap_ms

        silence = AudioSegment.silent(duration=gap_ms)
        combined = combined + silence + chunk.audio

    return combined


def normalize_loudness(audio: AudioSegment, target_dbfs: float = -20.0) -> AudioSegment:
    """音量を目標dBFSに正規化する。"""
    if len(audio) == 0:
        return audio

    current_dbfs = audio.dBFS
    if current_dbfs == float("-inf"):
        return audio

    gain = target_dbfs - current_dbfs
    return audio.apply_gain(gain)


def add_chapter_silence(
    audio: AudioSegment,
    intro_ms: int = 1000,
    outro_ms: int = 1500,
) -> AudioSegment:
    """章の前後に無音を追加する。"""
    intro = AudioSegment.silent(duration=intro_ms)
    outro = AudioSegment.silent(duration=outro_ms)
    return intro + audio + outro


def post_process(audio: AudioSegment, config: AudioConfig | None = None) -> AudioSegment:
    """音声後処理チェーン: 章無音追加 → 音量正規化。"""
    if config is None:
        config = AudioConfig()

    # 章の前後に無音追加
    audio = add_chapter_silence(audio, config.chapter_intro_ms, config.chapter_outro_ms)

    # 音量正規化
    if config.normalize:
        audio = normalize_loudness(audio, config.target_dbfs)

    return audio
