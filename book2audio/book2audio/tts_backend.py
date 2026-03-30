"""TTSバックエンド抽象化 + VOICEVOX対応"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

import edge_tts
from pydub import AudioSegment

logger = logging.getLogger(__name__)


@dataclass
class VoiceInfo:
    """音声情報"""
    id: str
    name: str
    language: str


class TTSBackend(ABC):
    """TTSバックエンドの抽象基底クラス"""

    name: str
    max_chunk_size: int

    @abstractmethod
    async def available_voices(self) -> list[VoiceInfo]:
        """利用可能な音声一覧を返す。"""

    @abstractmethod
    async def synthesize_chunk(
        self, text: str, output_path: str, voice: str, rate: str
    ) -> None:
        """1チャンクを音声合成してファイルに保存する。"""

    @abstractmethod
    def default_voice(self) -> str:
        """デフォルト音声IDを返す。"""


class EdgeTTSBackend(TTSBackend):
    """Microsoft Edge TTSバックエンド"""

    name = "edge-tts"
    max_chunk_size = 2000

    def __init__(self, pitch: str = "+0Hz", volume: str = "+0%"):
        self.pitch = pitch
        self.volume = volume

    async def available_voices(self) -> list[VoiceInfo]:
        voices = await edge_tts.list_voices()
        return [
            VoiceInfo(
                id=v["ShortName"],
                name=v.get("FriendlyName", v["ShortName"]),
                language=v.get("Locale", ""),
            )
            for v in voices
            if v.get("Locale", "").startswith("ja")
        ]

    async def synthesize_chunk(
        self, text: str, output_path: str, voice: str, rate: str
    ) -> None:
        communicate = edge_tts.Communicate(
            text, voice, rate=rate, pitch=self.pitch, volume=self.volume
        )
        await communicate.save(output_path)

    def default_voice(self) -> str:
        return "ja-JP-NanamiNeural"


class VoicevoxBackend(TTSBackend):
    """VOICEVOX TTSバックエンド（REST API経由）"""

    name = "voicevox"
    max_chunk_size = 200

    def __init__(
        self,
        base_url: str = "http://localhost:50021",
        speaker_id: int = 1,
        intonation_scale: float = 1.0,
        pitch_scale: float = 0.0,
        pre_phoneme_length: float | None = None,
        post_phoneme_length: float | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.speaker_id = speaker_id
        self.intonation_scale = intonation_scale
        self.pitch_scale = pitch_scale
        self.pre_phoneme_length = pre_phoneme_length
        self.post_phoneme_length = post_phoneme_length

    async def available_voices(self) -> list[VoiceInfo]:
        import httpx

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.base_url}/speakers")
                resp.raise_for_status()
                speakers = resp.json()

            voices = []
            for speaker in speakers:
                for style in speaker.get("styles", []):
                    voices.append(VoiceInfo(
                        id=str(style["id"]),
                        name=f"{speaker['name']}（{style['name']}）",
                        language="ja-JP",
                    ))
            return voices
        except Exception as e:
            logger.error("VOICEVOX接続エラー: %s。VOICEVOXエンジンが起動していることを確認してください。", e)
            raise ConnectionError(
                f"VOICEVOXエンジンに接続できません ({self.base_url})。"
                "VOICEVOXを起動してください。"
            ) from e

    async def synthesize_chunk(
        self, text: str, output_path: str, voice: str, rate: str
    ) -> None:
        import httpx

        speaker_id = int(voice) if voice.isdigit() else self.speaker_id

        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                # Step 1: 音声クエリ生成
                query_resp = await client.post(
                    f"{self.base_url}/audio_query",
                    params={"text": text, "speaker": speaker_id},
                )
                query_resp.raise_for_status()
                query = query_resp.json()

                # 速度調整
                rate_val = _parse_rate(rate)
                if rate_val != 1.0:
                    query["speedScale"] = rate_val

                # 抑揚・ピッチ・間の調整
                if self.intonation_scale != 1.0:
                    query["intonationScale"] = self.intonation_scale
                if self.pitch_scale != 0.0:
                    query["pitchScale"] = self.pitch_scale
                if self.pre_phoneme_length is not None:
                    query["prePhonemeLength"] = self.pre_phoneme_length
                if self.post_phoneme_length is not None:
                    query["postPhonemeLength"] = self.post_phoneme_length

                # Step 2: 音声合成
                synth_resp = await client.post(
                    f"{self.base_url}/synthesis",
                    params={"speaker": speaker_id},
                    json=query,
                    headers={"Content-Type": "application/json"},
                )
                synth_resp.raise_for_status()

            # WAV → MP3変換
            output_path_obj = Path(output_path)
            wav_path = output_path_obj.with_suffix(".wav")
            wav_path.write_bytes(synth_resp.content)

            audio = AudioSegment.from_wav(str(wav_path))
            audio.export(str(output_path), format="mp3")
            wav_path.unlink()

        except ConnectionError:
            raise
        except Exception as e:
            logger.error("VOICEVOX合成エラー: %s", e)
            raise RuntimeError(f"VOICEVOX音声合成に失敗しました: {e}") from e

    def default_voice(self) -> str:
        return str(self.speaker_id)


def _parse_rate(rate: str) -> float:
    """速度文字列（例: '+10%', '-20%'）を倍率に変換する。"""
    rate = rate.strip()
    if rate.endswith("%"):
        rate = rate[:-1]
    try:
        pct = float(rate)
        return 1.0 + pct / 100.0
    except ValueError:
        return 1.0


def get_backend(
    name: str = "edge-tts",
    voicevox_url: str = "http://localhost:50021",
    speaker_id: int = 1,
    pitch: str = "+0Hz",
    intonation_scale: float = 1.0,
    pitch_scale: float = 0.0,
    pre_phoneme_length: float | None = None,
    post_phoneme_length: float | None = None,
) -> TTSBackend:
    """名前からTTSバックエンドを取得するファクトリ関数。"""
    if name == "voicevox":
        return VoicevoxBackend(
            base_url=voicevox_url,
            speaker_id=speaker_id,
            intonation_scale=intonation_scale,
            pitch_scale=pitch_scale,
            pre_phoneme_length=pre_phoneme_length,
            post_phoneme_length=post_phoneme_length,
        )
    return EdgeTTSBackend(pitch=pitch)
