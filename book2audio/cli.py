"""CLI統合"""

from __future__ import annotations

import asyncio
import logging
import re
from pathlib import Path

import click

from book2audio.text_processor import clean_text
from book2audio.chapter_splitter import split_chapters_from_text
from book2audio.tts import synthesize_book
from book2audio.tts_backend import get_backend
from book2audio.audio_processor import AudioConfig


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


@click.command()
@click.argument("text_path", type=click.Path(exists=True))
@click.option("-o", "--output", "output_dir", default="./output", help="出力ディレクトリ")
@click.option("-v", "--voice", default="ja-JP-NanamiNeural", help="TTS音声名")
@click.option("--rate", default="+0%", help="読み上げ速度 (例: +10%, -20%)")
@click.option("--encoding", default="utf-8", help="入力ファイルのエンコーディング")
@click.option("--keep-text", is_flag=True, help="中間テキストファイルも出力する")
@click.option("--verbose", is_flag=True, help="詳細ログ出力")
@click.option("--backend", default="edge-tts", type=click.Choice(["edge-tts", "voicevox"]), help="TTSバックエンド")
@click.option("--voicevox-url", default="http://localhost:50021", help="VOICEVOXエンジンURL")
@click.option("--speaker-id", default=1, type=int, help="VOICEVOX話者ID")
@click.option("--pitch", default="+0Hz", help="ピッチ調整 (edge-tts用)")
@click.option("--normalize/--no-normalize", default=True, help="音量正規化")
@click.option("--paragraph-gap", default=600, type=int, help="段落間無音(ms)")
@click.option("--sentence-gap", default=200, type=int, help="文間の無音(ms)")
@click.option("--intonation-scale", default=1.2, type=float, help="抑揚の強さ (0.0-2.0, default: 1.2)")
@click.option("--pitch-scale", default=0.0, type=float, help="ピッチ調整 (-0.15〜0.15, default: 0.0)")
@click.option("--pre-phoneme-length", default=None, type=float, help="発話前の間 (default: VOICEVOX既定)")
@click.option("--post-phoneme-length", default=None, type=float, help="発話後の間 (default: VOICEVOX既定)")
@click.option("--max-chars", default=0, type=int, help="セグメント分割の最大文字数 (0=分割なし)")
@click.option("--strip-comments", is_flag=True, help="HTMLコメント (<!--...-->) を除去")
@click.option("--album", default=None, type=str, help="ID3タグのアルバム名")
@click.option("--no-chapter-split", is_flag=True, help="章分割をスキップし、ファイル全体を1章として扱う")
def main(
    text_path: str,
    output_dir: str,
    voice: str,
    rate: str,
    encoding: str,
    keep_text: bool,
    verbose: bool,
    backend: str,
    voicevox_url: str,
    speaker_id: int,
    pitch: str,
    normalize: bool,
    paragraph_gap: int,
    sentence_gap: int,
    intonation_scale: float,
    pitch_scale: float,
    pre_phoneme_length: float | None,
    post_phoneme_length: float | None,
    max_chars: int,
    strip_comments: bool,
    album: str | None,
    no_chapter_split: bool,
) -> None:
    """テキストファイルをオーディオブックに変換する。

    TEXT_PATH: 入力テキストファイルのパス (.txt)
    """
    _setup_logging(verbose)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    click.echo("=== book2audio: テキスト → オーディオブック変換 ===\n")

    # バックエンド設定
    tts_backend = get_backend(
        name=backend,
        voicevox_url=voicevox_url,
        speaker_id=speaker_id,
        pitch=pitch,
        intonation_scale=intonation_scale,
        pitch_scale=pitch_scale,
        pre_phoneme_length=pre_phoneme_length,
        post_phoneme_length=post_phoneme_length,
    )
    click.echo(f"  バックエンド: {tts_backend.name}")

    # VOICEVOX使用時はvoiceをspeaker_idに
    if backend == "voicevox":
        voice = str(speaker_id)

    # 音声後処理設定
    audio_config = AudioConfig(
        paragraph_gap_ms=paragraph_gap,
        sentence_gap_ms=sentence_gap,
        normalize=normalize,
    )

    # Phase 1: テキスト読み込み・整形・章分割
    click.echo("[Phase 1/2] テキスト整形・章分割")
    raw_text = Path(text_path).read_text(encoding=encoding)

    # HTMLコメント除去
    if strip_comments:
        raw_text = re.sub(r'<!--.*?-->', '', raw_text)

    cleaned = clean_text(raw_text)

    if no_chapter_split:
        # ファイル名からタイトルを取得
        title = Path(text_path).stem
        chapters = [{"title": title, "text": cleaned}]
    else:
        chapters = split_chapters_from_text(cleaned)
    click.echo(f"  {len(chapters)} 章を検出\n")

    # 中間テキスト保存
    if keep_text:
        text_dir = output_path / "text"
        text_dir.mkdir(exist_ok=True)

        # 全文テキスト
        full_text_path = text_dir / "full_text.txt"
        full_text_path.write_text(cleaned, encoding="utf-8")

        # 章ごとのテキスト
        for i, ch in enumerate(chapters):
            ch_path = text_dir / f"{i + 1:02d}_{ch['title']}.txt"
            ch_path.write_text(
                f"# {ch['title']}\n\n{ch['text']}", encoding="utf-8"
            )
        click.echo(f"  テキストファイル保存: {text_dir}\n")

    # Phase 2: 音声合成
    click.echo("[Phase 2/2] 音声合成")
    audio_dir = output_path / "audio"

    output_files = asyncio.run(
        synthesize_book(
            chapters, str(audio_dir), voice=voice, rate=rate,
            backend=tts_backend, audio_config=audio_config,
            max_chars=max_chars, album=album,
        )
    )

    # 完了
    click.echo(f"\n=== 変換完了 ===")
    click.echo(f"出力ディレクトリ: {output_path}")
    click.echo(f"音声ファイル数: {len(output_files)}")
    for f in output_files:
        click.echo(f"  - {Path(f).name}")


if __name__ == "__main__":
    main()
