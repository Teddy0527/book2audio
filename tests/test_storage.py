"""storage.py のユニットテスト"""

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from book2audio.web.storage import (
    get_audio_base_dir,
    get_book_audio_dir,
    get_audio_path,
    move_audio_to_permanent,
    delete_book_audio,
)


class TestGetAudioBaseDir:
    def test_creates_directory(self, tmp_path):
        base = get_audio_base_dir(tmp_path)
        assert base == tmp_path / "audio"
        assert base.exists()

    def test_idempotent(self, tmp_path):
        get_audio_base_dir(tmp_path)
        get_audio_base_dir(tmp_path)
        assert (tmp_path / "audio").exists()


class TestGetBookAudioDir:
    def test_returns_correct_path(self, tmp_path):
        path = get_book_audio_dir("abc123", tmp_path)
        assert path == tmp_path / "audio" / "abc123"


class TestGetAudioPath:
    def test_returns_correct_path(self, tmp_path):
        path = get_audio_path("abc123", "01_test.mp3", tmp_path)
        assert path == tmp_path / "audio" / "abc123" / "01_test.mp3"


class TestMoveAudioToPermanent:
    def test_empty_when_no_audio_dir(self, tmp_path):
        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()
        result = move_audio_to_permanent(str(temp_dir), "book1", tmp_path)
        assert result == []

    @patch("book2audio.web.storage.get_mp3_duration")
    def test_copies_files(self, mock_duration, tmp_path):
        mock_duration.return_value = 120.5

        # tempディレクトリにダミーMP3作成
        temp_dir = tmp_path / "temp"
        audio_dir = temp_dir / "audio"
        audio_dir.mkdir(parents=True)
        (audio_dir / "01_前書き.mp3").write_bytes(b"fake mp3 data")
        (audio_dir / "02_第一章.mp3").write_bytes(b"fake mp3 data")

        data_dir = tmp_path / "data"
        result = move_audio_to_permanent(str(temp_dir), "book1", data_dir)

        assert len(result) == 2
        assert result[0]["filename"] == "01_前書き.mp3"
        assert result[0]["title"] == "前書き"
        assert result[0]["duration_sec"] == 120.5
        assert result[1]["filename"] == "02_第一章.mp3"
        assert result[1]["title"] == "第一章"

        # ファイルがコピーされたか確認
        dest = data_dir / "audio" / "book1"
        assert (dest / "01_前書き.mp3").exists()
        assert (dest / "02_第一章.mp3").exists()

    @patch("book2audio.web.storage.get_mp3_duration")
    def test_title_extraction_no_prefix(self, mock_duration, tmp_path):
        mock_duration.return_value = 60.0

        temp_dir = tmp_path / "temp"
        audio_dir = temp_dir / "audio"
        audio_dir.mkdir(parents=True)
        (audio_dir / "standalone.mp3").write_bytes(b"fake")

        result = move_audio_to_permanent(str(temp_dir), "book1", tmp_path)
        assert result[0]["title"] == "standalone"


class TestDeleteBookAudio:
    def test_deletes_existing(self, tmp_path):
        book_dir = tmp_path / "audio" / "book1"
        book_dir.mkdir(parents=True)
        (book_dir / "test.mp3").write_bytes(b"data")

        assert delete_book_audio("book1", tmp_path) is True
        assert not book_dir.exists()

    def test_returns_false_for_missing(self, tmp_path):
        assert delete_book_audio("nonexistent", tmp_path) is False
