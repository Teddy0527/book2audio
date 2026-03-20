"""Phase 1: PDF → ページ画像変換"""

from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image

# 高DPIで大きなPDFを変換するとPillowのピクセル数上限に達するため緩和
Image.MAX_IMAGE_PIXELS = None

from pdf2image import convert_from_path, pdfinfo_from_path
from typing import Callable

logger = logging.getLogger(__name__)


def parse_page_range(page_range: str | None) -> tuple[int, int] | None:
    """ページ範囲文字列 (例: '1-10') をタプルに変換する。"""
    if page_range is None:
        return None
    parts = page_range.split("-")
    if len(parts) == 1:
        p = int(parts[0])
        return (p, p)
    if len(parts) == 2:
        return (int(parts[0]), int(parts[1]))
    raise ValueError(f"無効なページ範囲: {page_range}")


def get_pdf_page_count(pdf_path: str) -> int:
    """PDFの総ページ数を返す。"""
    info = pdfinfo_from_path(str(pdf_path))
    return int(info["Pages"])


def pdf_to_images(
    pdf_path: str,
    output_dir: str,
    dpi: int = 300,
    pages: str | None = None,
    batch_size: int = 10,
    fmt: str = "jpeg",
    on_progress: Callable[[int, int], None] | None = None,
) -> list[str]:
    """PDFを画像に変換し、保存したファイルパスのリストを返す。

    バッチ処理により、大きなPDFでもメモリ使用量を抑えながら変換する。

    Args:
        pdf_path: 入力PDFファイルパス
        output_dir: 画像出力先ディレクトリ
        dpi: 変換解像度（デフォルト300）
        pages: ページ範囲文字列 (例: '1-10')
        batch_size: 一度に変換するページ数（デフォルト10）
        fmt: 出力画像フォーマット（デフォルト'jpeg'）
        on_progress: 進捗コールバック (completed, total) -> None

    Returns:
        保存した画像ファイルパスのリスト
    """
    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDFファイルが見つかりません: {pdf_path}")

    page_range = parse_page_range(pages)

    total_pdf_pages = get_pdf_page_count(str(pdf_path))
    start_page = page_range[0] if page_range else 1
    end_page = page_range[1] if page_range else total_pdf_pages
    total = end_page - start_page + 1

    ext = "jpg" if fmt == "jpeg" else fmt
    save_fmt = "JPEG" if fmt == "jpeg" else fmt.upper()
    save_kwargs: dict = {}
    if save_fmt == "JPEG":
        save_kwargs["quality"] = 95

    logger.info(
        "PDF→画像変換開始: %s (dpi=%d, pages=%d-%d, batch=%d, fmt=%s)",
        pdf_path, dpi, start_page, end_page, batch_size, fmt,
    )

    saved_paths: list[str] = []
    completed = 0

    for batch_start in range(start_page, end_page + 1, batch_size):
        batch_end = min(batch_start + batch_size - 1, end_page)
        batch_images = convert_from_path(
            str(pdf_path),
            dpi=dpi,
            fmt=fmt,
            first_page=batch_start,
            last_page=batch_end,
        )

        for i, image in enumerate(batch_images):
            page_num = batch_start + i
            filename = f"page_{page_num:03d}.{ext}"
            filepath = output_dir / filename
            image.save(str(filepath), save_fmt, **save_kwargs)
            saved_paths.append(str(filepath))
            logger.debug("保存: %s", filepath)

        del batch_images

        completed += batch_end - batch_start + 1
        if on_progress is not None:
            on_progress(completed, total)
        logger.info("バッチ変換: %d/%d ページ完了", completed, total)

    logger.info("変換完了: %d ページ", len(saved_paths))
    return saved_paths
