"""tts_backend モジュールのテスト"""

from book2audio.tts_backend import (
    EdgeTTSBackend,
    VoicevoxBackend,
    get_backend,
    _parse_rate,
    VoiceInfo,
)


class TestParseRate:
    def test_positive_percent(self):
        assert _parse_rate("+10%") == 1.1

    def test_negative_percent(self):
        assert _parse_rate("-20%") == 0.8

    def test_zero(self):
        assert _parse_rate("+0%") == 1.0

    def test_no_sign(self):
        assert _parse_rate("50%") == 1.5

    def test_invalid(self):
        assert _parse_rate("abc") == 1.0


class TestEdgeTTSBackend:
    def test_default_voice(self):
        backend = EdgeTTSBackend()
        assert backend.default_voice() == "ja-JP-NanamiNeural"

    def test_max_chunk_size(self):
        backend = EdgeTTSBackend()
        assert backend.max_chunk_size == 2000

    def test_name(self):
        backend = EdgeTTSBackend()
        assert backend.name == "edge-tts"

    def test_pitch_volume(self):
        backend = EdgeTTSBackend(pitch="+5Hz", volume="+10%")
        assert backend.pitch == "+5Hz"
        assert backend.volume == "+10%"


class TestVoicevoxBackend:
    def test_default_voice(self):
        backend = VoicevoxBackend(speaker_id=3)
        assert backend.default_voice() == "3"

    def test_max_chunk_size(self):
        backend = VoicevoxBackend()
        assert backend.max_chunk_size == 200

    def test_name(self):
        backend = VoicevoxBackend()
        assert backend.name == "voicevox"

    def test_custom_url(self):
        backend = VoicevoxBackend(base_url="http://example.com:50021/")
        assert backend.base_url == "http://example.com:50021"


class TestGetBackend:
    def test_default_edge_tts(self):
        backend = get_backend()
        assert isinstance(backend, EdgeTTSBackend)

    def test_edge_tts(self):
        backend = get_backend("edge-tts")
        assert isinstance(backend, EdgeTTSBackend)

    def test_voicevox(self):
        backend = get_backend("voicevox")
        assert isinstance(backend, VoicevoxBackend)

    def test_voicevox_with_params(self):
        backend = get_backend(
            "voicevox",
            voicevox_url="http://custom:50021",
            speaker_id=5,
        )
        assert isinstance(backend, VoicevoxBackend)
        assert backend.base_url == "http://custom:50021"
        assert backend.speaker_id == 5

    def test_edge_with_pitch(self):
        backend = get_backend("edge-tts", pitch="+5Hz")
        assert isinstance(backend, EdgeTTSBackend)
        assert backend.pitch == "+5Hz"
