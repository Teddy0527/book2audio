"""Phase 5: CLI統合"""

from __future__ import annotations

import asyncio
import logging
import sys
import tempfile
from pathlib import Path

import click
from tqdm import tqdm

from book2audio.pdf_to_images import pdf_to_images
from book2audio.ocr import ocr_page
from book2audio.text_processor import clean_text
from book2audio.chapter_splitter import split_chapters
from book2audio.tts import synthesize_book


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


@click.command()
@click.argument("pdf_path", type=click.Path(exists=True))
@click.option("-o", "--output", "output_dir", default="./output", help="出力ディレクトリ")
@click.option("-v", "--voice", default="ja-JP-NanamiNeural", help="TTS音声名")
@click.option("--rate", default="+0%", help="読み上げ速度 (例: +10%, -20%)")
@click.option("--dpi", default=300, type=int, help="PDF→画像変換の解像度")
@click.option("--pages", default=None, help="ページ範囲 (例: 1-10)")
@click.option("--keep-text", is_flag=True, help="中間テキストファイルも出力する")
@click.option("--remove-ruby/--keep-ruby", default=True, help="ルビを除去する")
@click.option("--verbose", is_flag=True, help="詳細ログ出力")
def main(
    pdf_path: str,
    output_dir: str,
    voice: str,
    rate: str,
    dpi: int,
    pages: str | None,
    keep_text: bool,
    remove_ruby: bool,
    verbose: bool,
) -> None:
    """縦書き日本語スキャンPDFをオーディオブックに変換する。

    PDF_PATH: 入力PDFファイルのパス
    """
    _setup_logging(verbose)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    click.echo("=== book2audio: PDF → オーディオブック変換 ===\n")

    # Phase 1: PDF → 画像変換
    click.echo("[Phase 1/4] PDF → 画像変換")
    with tempfile.TemporaryDirectory() as img_dir:
        image_paths = pdf_to_images(pdf_path, img_dir, dpi=dpi, pages=pages)
        click.echo(f"  {len(image_paths)} ページの画像を生成\n")

        # Phase 2: OCR
        click.echo("[Phase 2/4] 縦書きOCR")
        pages_text: list[str] = []
        for img_path in tqdm(image_paths, desc="  OCR処理", unit="ページ"):
            text = ocr_page(img_path, remove_ruby=remove_ruby)
            pages_text.append(text)
        click.echo()

        # Phase 3: テキスト整形・章分割
        click.echo("[Phase 3/4] テキスト整形・章分割")
        cleaned_pages = [clean_text(page) for page in pages_text]
        chapters = split_chapters(cleaned_pages)
        click.echo(f"  {len(chapters)} 章を検出\n")

        # 中間テキスト保存
        if keep_text:
            text_dir = output_path / "text"
            text_dir.mkdir(exist_ok=True)

            # 全文テキスト
            full_text_path = text_dir / "full_text.txt"
            full_text_path.write_text("\n\n".join(cleaned_pages), encoding="utf-8")

            # 章ごとのテキスト
            for i, ch in enumerate(chapters):
                ch_path = text_dir / f"{i + 1:02d}_{ch['title']}.txt"
                ch_path.write_text(
                    f"# {ch['title']}\n\n{ch['text']}", encoding="utf-8"
                )
            click.echo(f"  テキストファイル保存: {text_dir}\n")

        # Phase 4: 音声合成
        click.echo("[Phase 4/4] 音声合成")
        audio_dir = output_path / "audio"

        output_files = asyncio.run(
            synthesize_book(chapters, str(audio_dir), voice=voice, rate=rate)
        )

    # 完了
    click.echo(f"\n=== 変換完了 ===")
    click.echo(f"出力ディレクトリ: {output_path}")
    click.echo(f"音声ファイル数: {len(output_files)}")
    for f in output_files:
        click.echo(f"  - {Path(f).name}")


if __name__ == "__main__":
    main()
