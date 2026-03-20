"""Phase 2: 縦書きOCR（Google Cloud Vision API）"""

from __future__ import annotations

import logging
from pathlib import Path

import google.auth.exceptions
from google.cloud import vision

logger = logging.getLogger(__name__)

# ページの上下端マージン（ノイズ除去用、割合）
HEADER_FOOTER_MARGIN = 0.05
# ルビ判定：ブロックの高さがページ高さに対してこの割合以下ならルビ扱い
RUBY_HEIGHT_RATIO = 0.015
# ページ番号判定：数字のみで短いテキスト
MIN_CONFIDENCE = 0.5
# 列グルーピング：x座標の差がページ幅のこの割合以内なら同じ列
COLUMN_THRESHOLD_RATIO = 0.05

_vision_client: vision.ImageAnnotatorClient | None = None


def _get_vision_client() -> vision.ImageAnnotatorClient:
    """Vision APIクライアントを取得（キャッシュ済み）。認証エラー時はわかりやすいメッセージを表示。"""
    global _vision_client
    if _vision_client is not None:
        return _vision_client
    try:
        _vision_client = vision.ImageAnnotatorClient()
        return _vision_client
    except google.auth.exceptions.DefaultCredentialsError:
        raise RuntimeError(
            "Google Cloud の認証情報が見つかりません。\n"
            "以下のいずれかの方法で設定してください:\n"
            '  1. 環境変数を設定: export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"\n'
            "  2. gcloud CLI でログイン: gcloud auth application-default login\n"
            "詳細: https://cloud.google.com/docs/authentication/external/set-up-adc"
        )


def _get_block_center(block: vision.Block) -> tuple[float, float]:
    """ブロックのバウンディングボックス中心座標を返す。"""
    vertices = block.bounding_box.vertices
    xs = [v.x for v in vertices]
    ys = [v.y for v in vertices]
    return (sum(xs) / len(xs), sum(ys) / len(ys))


def _get_block_height(block: vision.Block) -> float:
    """ブロックの高さを返す。"""
    vertices = block.bounding_box.vertices
    ys = [v.y for v in vertices]
    return max(ys) - min(ys)


def _get_block_text(block: vision.Block) -> str:
    """ブロック内の全テキストを結合して返す。"""
    text_parts = []
    for paragraph in block.paragraphs:
        for word in paragraph.words:
            word_text = "".join(symbol.text for symbol in word.symbols)
            text_parts.append(word_text)
    return "".join(text_parts)


def _is_page_number(text: str) -> bool:
    """テキストがページ番号かどうか判定する。"""
    stripped = text.strip()
    if not stripped:
        return False
    # 数字のみ、またはローマ数字のみ
    return stripped.isdigit() and len(stripped) <= 4


def _is_header_footer(block: vision.Block, page_height: float) -> bool:
    """ブロックがヘッダー/フッター領域にあるか判定する。"""
    vertices = block.bounding_box.vertices
    ys = [v.y for v in vertices]
    center_y = sum(ys) / len(ys)
    margin = page_height * HEADER_FOOTER_MARGIN
    return center_y < margin or center_y > (page_height - margin)


def _is_ruby(block: vision.Block, page_height: float) -> bool:
    """ブロックがルビ（ふりがな）かどうか判定する。"""
    height = _get_block_height(block)
    return height < page_height * RUBY_HEIGHT_RATIO


def _sort_blocks_vertical(
    blocks: list[vision.Block], page_width: float
) -> list[vision.Block]:
    """縦書き用にブロックをソートする。

    右の列→左の列（x降順）、同一列内は上→下（y昇順）。
    """
    if not blocks:
        return blocks

    column_threshold = page_width * COLUMN_THRESHOLD_RATIO

    # ブロックにx中心座標を付与してソート
    block_centers = [(block, _get_block_center(block)) for block in blocks]
    # まずx座標降順でソート
    block_centers.sort(key=lambda bc: -bc[1][0])

    # 列にグルーピング
    columns: list[list[tuple[vision.Block, tuple[float, float]]]] = []
    for bc in block_centers:
        placed = False
        for col in columns:
            col_x = sum(c[1][0] for c in col) / len(col)
            if abs(bc[1][0] - col_x) < column_threshold:
                col.append(bc)
                placed = True
                break
        if not placed:
            columns.append([bc])

    # 列をx座標降順でソート（右→左）
    columns.sort(key=lambda col: -sum(c[1][0] for c in col) / len(col))

    # 各列内をy座標昇順でソート（上→下）
    sorted_blocks = []
    for col in columns:
        col.sort(key=lambda bc: bc[1][1])
        sorted_blocks.extend(bc[0] for bc in col)

    return sorted_blocks


def ocr_page(image_path: str, remove_ruby: bool = True) -> str:
    """1ページの画像からテキストを抽出し、正しい読み順の文字列を返す。

    Args:
        image_path: 入力画像ファイルパス
        remove_ruby: ルビを除去するかどうか

    Returns:
        抽出されたテキスト
    """
    client = _get_vision_client()

    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(f"画像ファイルが見つかりません: {image_path}")

    with open(image_path, "rb") as f:
        content = f.read()

    image = vision.Image(content=content)
    image_context = vision.ImageContext(language_hints=["ja"])

    logger.info("OCR実行: %s", image_path)
    response = client.document_text_detection(
        image=image, image_context=image_context
    )

    if response.error.message:
        raise RuntimeError(f"Vision API エラー: {response.error.message}")

    if not response.full_text_annotation.pages:
        logger.warning("テキストが検出されませんでした: %s", image_path)
        return ""

    page = response.full_text_annotation.pages[0]
    page_width = page.width
    page_height = page.height

    # フィルタリング
    valid_blocks = []
    for block in page.blocks:
        text = _get_block_text(block)

        # ヘッダー/フッター除去
        if _is_header_footer(block, page_height):
            if _is_page_number(text):
                logger.debug("ページ番号除去: %s", text.strip())
                continue

        # ルビ除去
        if remove_ruby and _is_ruby(block, page_height):
            logger.debug("ルビ除去: %s", text.strip())
            continue

        # 信頼度チェック
        if block.confidence < MIN_CONFIDENCE:
            logger.debug("低信頼度ブロック除去 (%.2f): %s", block.confidence, text.strip())
            continue

        # 空テキスト除去
        if not text.strip():
            continue

        valid_blocks.append(block)

    # 縦書きソート
    sorted_blocks = _sort_blocks_vertical(valid_blocks, page_width)

    # テキスト結合
    texts = [_get_block_text(block) for block in sorted_blocks]
    return "\n".join(texts)


def ocr_book(image_paths: list[str], remove_ruby: bool = True) -> list[str]:
    """全ページのテキストをリストで返す。

    Args:
        image_paths: 画像ファイルパスのリスト
        remove_ruby: ルビを除去するかどうか

    Returns:
        各ページのテキストのリスト
    """
    results = []
    for i, path in enumerate(image_paths):
        logger.info("OCR処理中: %d/%d", i + 1, len(image_paths))
        text = ocr_page(path, remove_ruby=remove_ruby)
        results.append(text)
    return results
