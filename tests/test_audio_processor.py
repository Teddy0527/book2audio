"""audio_processor モジュールのテスト"""

from pydub import AudioSegment
from pydub.generators import Sine

from book2audio.audio_processor import (
    AudioConfig,
    ChunkResult,
    BOUNDARY_PARAGRAPH,
    BOUNDARY_SENTENCE,
    insert_silence_between_chunks,
    normalize_loudness,
    add_chapter_silence,
    post_process,
)


def _make_tone(duration_ms: int = 1000, freq: int = 440) -> AudioSegment:
    """テスト用のサイン波を生成する。"""
    return Sine(freq).to_audio_segment(duration=duration_ms).apply_gain(-20)


class TestAudioConfig:
    def test_defaults(self):
        config = AudioConfig()
        assert config.paragraph_gap_ms == 600
        assert config.sentence_gap_ms == 200
        assert config.chapter_intro_ms == 1000
        assert config.chapter_outro_ms == 1500
        assert config.normalize is True
        assert config.target_dbfs == -20.0

    def test_custom(self):
        config = AudioConfig(paragraph_gap_ms=800, normalize=False)
        assert config.paragraph_gap_ms == 800
        assert config.normalize is False


class TestInsertSilenceBetweenChunks:
    def test_empty_list(self):
        result = insert_silence_between_chunks([])
        assert len(result) == 0

    def test_single_chunk(self):
        tone = _make_tone(500)
        chunks = [ChunkResult(audio=tone, boundary_type=BOUNDARY_PARAGRAPH)]
        result = insert_silence_between_chunks(chunks)
        assert len(result) == 500

    def test_paragraph_gap(self):
        config = AudioConfig(paragraph_gap_ms=600)
        tone1 = _make_tone(500)
        tone2 = _make_tone(500)
        chunks = [
            ChunkResult(audio=tone1, boundary_type=BOUNDARY_PARAGRAPH),
            ChunkResult(audio=tone2, boundary_type=BOUNDARY_PARAGRAPH),
        ]
        result = insert_silence_between_chunks(chunks, config)
        # 500 + 600 + 500 = 1600ms (with some tolerance)
        assert abs(len(result) - 1600) < 50

    def test_sentence_gap(self):
        config = AudioConfig(sentence_gap_ms=200)
        tone1 = _make_tone(500)
        tone2 = _make_tone(500)
        chunks = [
            ChunkResult(audio=tone1, boundary_type=BOUNDARY_PARAGRAPH),
            ChunkResult(audio=tone2, boundary_type=BOUNDARY_SENTENCE),
        ]
        result = insert_silence_between_chunks(chunks, config)
        # 500 + 200 + 500 = 1200ms
        assert abs(len(result) - 1200) < 50


class TestNormalizeLoudness:
    def test_basic_normalize(self):
        tone = _make_tone(1000)
        normalized = normalize_loudness(tone, target_dbfs=-15.0)
        assert abs(normalized.dBFS - (-15.0)) < 1.0

    def test_empty_audio(self):
        empty = AudioSegment.empty()
        result = normalize_loudness(empty)
        assert len(result) == 0

    def test_silent_audio(self):
        silent = AudioSegment.silent(duration=1000)
        result = normalize_loudness(silent)
        # Should not crash on -inf dBFS
        assert len(result) == 1000


class TestAddChapterSilence:
    def test_adds_silence(self):
        tone = _make_tone(1000)
        result = add_chapter_silence(tone, intro_ms=500, outro_ms=800)
        # 500 + 1000 + 800 = 2300ms
        assert abs(len(result) - 2300) < 50

    def test_default_values(self):
        tone = _make_tone(1000)
        result = add_chapter_silence(tone)
        # 1000 + 1000 + 1500 = 3500ms
        assert abs(len(result) - 3500) < 50


class TestPostProcess:
    def test_full_chain(self):
        tone = _make_tone(1000)
        config = AudioConfig(
            chapter_intro_ms=500,
            chapter_outro_ms=500,
            normalize=True,
            target_dbfs=-18.0,
        )
        result = post_process(tone, config)
        # 500 + 1000 + 500 = 2000ms
        assert abs(len(result) - 2000) < 50
        # 音量が目標付近になっている
        assert abs(result.dBFS - (-18.0)) < 1.0

    def test_no_normalize(self):
        tone = _make_tone(1000)
        original_dbfs = tone.dBFS
        config = AudioConfig(
            chapter_intro_ms=0,
            chapter_outro_ms=0,
            normalize=False,
        )
        result = post_process(tone, config)
        # 正規化なし → 無音部分以外は元の音量を維持
        # (intro/outroが0msなので、ほぼ同じ音量のはず)
        assert len(result) == len(tone)
