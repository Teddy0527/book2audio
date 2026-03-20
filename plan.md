# book2audio: 縦書き日本語スキャンPDF → オーディオブック変換ツール

## 概要

縦書きの日本語書籍（スキャンPDF/画像PDF）を、OCRでテキスト抽出し、音声合成でMP3オーディオブックとして出力するCLIツール。

## 技術スタック

- **言語**: Python 3.11+
- **PDF→画像**: `pdf2image` (poppler依存)
- **OCR**: Google Cloud Vision API
- **テキスト処理**: 標準ライブラリ + `regex`
- **音声合成**: `edge-tts`
- **音声処理**: `pydub` (ffmpeg依存)
- **CLI**: `argparse` or `click`

## パイプライン

```
スキャンPDF → ページ画像化 → 縦書きOCR → テキスト整形 → 章分割 → Edge TTS → MP3出力（章別）
```

## ディレクトリ構成

```
book2audio/
├── book2audio/
│   ├── __init__.py
│   ├── cli.py            # CLIエントリーポイント
│   ├── pdf_to_images.py  # PDF→画像変換
│   ├── ocr.py            # Google Cloud Vision OCR
│   ├── text_processor.py # テキスト整形・クリーニング
│   ├── chapter_splitter.py # 章分割
│   └── tts.py            # Edge TTS → MP3生成
├── tests/
│   ├── test_ocr.py
│   ├── test_text_processor.py
│   └── test_tts.py
├── pyproject.toml
├── requirements.txt
└── README.md
```

## 開発フェーズ

### Phase 1: PDF → 画像変換 (`pdf_to_images.py`)

**目的**: スキャンPDFを1ページずつPNG画像に変換する。

**実装内容**:
- `pdf2image.convert_from_path()` でPDFをページ単位の画像リストに変換
- 解像度は **300dpi** をデフォルトとする（OCR精度とファイルサイズのバランス）
- 出力先ディレクトリに `page_001.png`, `page_002.png`, ... として保存
- ページ範囲の指定に対応（`--pages 1-10` のような形）

**依存関係**:
```bash
# macOS
brew install poppler
# Ubuntu
sudo apt-get install poppler-utils

pip install pdf2image Pillow
```

**インターフェース**:
```python
def pdf_to_images(pdf_path: str, output_dir: str, dpi: int = 300, pages: tuple | None = None) -> list[str]:
    """PDFを画像に変換し、保存したファイルパスのリストを返す"""
```

---

### Phase 2: 縦書きOCR (`ocr.py`) ← 最重要・最難関

**目的**: 縦書き日本語の画像からテキストを正しい読み順で抽出する。

**Google Cloud Vision API のセットアップ**:
1. GCPプロジェクトでCloud Vision APIを有効化
2. サービスアカウントキー（JSON）を作成
3. 環境変数 `GOOGLE_APPLICATION_CREDENTIALS` にパスを設定

**実装内容**:

1. **画像をVision APIに送信**
   - `document_text_detection()` を使う（`text_detection()` より構造化された結果が得られる）
   - `image_context` に `language_hints=["ja"]` を指定

2. **縦書きの読み順を再構成する** ← ここが核心
   - Vision APIは `full_text_annotation.pages[].blocks[].paragraphs[].words[]` の階層構造でテキストを返す
   - 各ブロックの `bounding_box` の座標を使って読み順をソート
   - **縦書きソートロジック**:
     - まずブロックをx座標の**降順**でソート（右の列 → 左の列）
     - 同一列内（x座標が近いブロック）はy座標の**昇順**でソート（上 → 下）
     - 列のグルーピングは、x座標の差がページ幅の一定割合以内かで判定

3. **ルビの処理**
   - ルビ（ふりがな）は本文テキストの右側に小さく表示される
   - ルビのブロックはbounding_boxの高さが極端に小さい → フィルタリング or 親テキストに統合
   - ルビを完全除去するか、括弧付きで残すかを設定可能にする

4. **ノイズ除去**
   - ヘッダー・フッター: ページ上下端の一定範囲内のテキストを除去
   - ページ番号: 数字のみの小さいブロックを除去
   - スキャンノイズ: 短すぎる or 信頼度が低いテキストを除去

**インターフェース**:
```python
def ocr_page(image_path: str, remove_ruby: bool = True) -> str:
    """1ページの画像からテキストを抽出し、正しい読み順の文字列を返す"""

def ocr_book(image_paths: list[str], remove_ruby: bool = True) -> list[str]:
    """全ページのテキストをリストで返す"""
```

**無料枠**: 月1,000ユニット（= 1,000ページ）まで無料。300ページの本なら月3冊程度。

**⚠️ リスクと対策**:
- 縦書きの読み順が崩れる可能性がある → サンプルページで必ず事前検証
- 段組み（2段以上）の場合にブロック分割が不正確になりうる
- **フォールバック**: OCR精度が不十分な場合、Claude Vision API（Anthropic API）に切り替える設計を考慮しておく。Claude Visionは縦書き・ルビ・読み順を文脈で理解できるため精度が高いが、コストは高い（300ページで$3-5程度）

---

### Phase 3: テキスト整形・章分割 (`text_processor.py`, `chapter_splitter.py`)

**テキスト整形** (`text_processor.py`):

1. **OCR誤認識の補正**
   - 頻出パターン: `一` ↔ `ー` ↔ `—`, `口` ↔ `ロ` ↔ `□`, `二` ↔ `ニ`
   - 全角/半角の統一
   - 不要な改行の除去（文中の改行を連結、段落区切りは保持）

2. **読み上げ用の前処理**
   - 数字の読み方補正（「3月」→ そのまま、Edge TTSが処理する）
   - 記号の処理（「…」→ 間を空ける、「――」→ スキップ）
   - ルビが残っている場合の処理

**章分割** (`chapter_splitter.py`):

1. **目次ページの検出**
   - 「目次」「もくじ」「contents」等のキーワードを含むページを探す
   - 目次から章タイトルとページ番号を抽出

2. **本文中の章区切り検出**
   - 目次情報がない場合: 「第◯章」「第◯節」や、大きな空行 + 短い行（= 章タイトル）パターンで検出
   - 各チャプターのテキストをリストとして出力

**インターフェース**:
```python
def clean_text(raw_text: str) -> str:
    """OCR生テキストを整形する"""

def split_chapters(pages_text: list[str]) -> list[dict]:
    """ページテキストのリストから章分割し、[{"title": "第1章 ...", "text": "..."}] を返す"""
```

---

### Phase 4: 音声合成 (`tts.py`)

**Edge TTSの仕様**:
- 完全無料、API制限なし（Microsoft Edgeの読み上げ機能と同じバックエンド）
- 非同期（`async`）で動作
- 日本語音声:
  - `ja-JP-NanamiNeural` (女性、自然で聞きやすい) ← デフォルト推奨
  - `ja-JP-KeitaNeural` (男性)

**実装内容**:

1. **テキスト分割**
   - Edge TTSは一度に送れるテキスト量に制限がある
   - 句点（。）や段落区切りで **最大2000文字** ごとに分割
   - 文の途中で切れないようにする

2. **音声合成**
   - 各チャンクを `edge-tts` で音声化（MP3）
   - 章ごとにチャンクを結合して1つのMP3にする
   - `pydub` で結合・書き出し

3. **メタデータ**
   - ID3タグにタイトル、章番号を付与
   - 各章のMP3ファイル名: `01_第1章_タイトル.mp3`

**インターフェース**:
```python
async def synthesize_chapter(text: str, output_path: str, voice: str = "ja-JP-NanamiNeural", rate: str = "+0%") -> None:
    """テキストを音声合成してMP3ファイルとして保存"""

async def synthesize_book(chapters: list[dict], output_dir: str, voice: str = "ja-JP-NanamiNeural") -> list[str]:
    """全章を音声合成し、ファイルパスのリストを返す"""
```

**依存関係**:
```bash
pip install edge-tts pydub
# ffmpegも必要
brew install ffmpeg  # macOS
sudo apt-get install ffmpeg  # Ubuntu
```

---

### Phase 5: CLI統合 (`cli.py`)

**基本コマンド**:
```bash
# 最小構成: PDFを指定して実行
python -m book2audio input.pdf

# フルオプション
python -m book2audio input.pdf \
  --output ./audiobook/ \
  --voice ja-JP-NanamiNeural \
  --rate "+10%" \
  --dpi 300 \
  --pages 1-100 \
  --keep-text \
  --remove-ruby
```

**オプション一覧**:
| オプション | デフォルト | 説明 |
|---|---|---|
| `--output`, `-o` | `./output/` | 出力ディレクトリ |
| `--voice`, `-v` | `ja-JP-NanamiNeural` | TTS音声 |
| `--rate` | `+0%` | 読み上げ速度調整 |
| `--dpi` | `300` | PDF→画像変換の解像度 |
| `--pages` | 全ページ | 処理するページ範囲 |
| `--keep-text` | `false` | 中間テキストファイルも出力 |
| `--remove-ruby` | `true` | ルビを除去するか |

**進捗表示**:
- `tqdm` でプログレスバーを表示
- 各フェーズ（画像化 → OCR → 整形 → TTS）の進捗を個別表示

---

## セットアップ手順

### 1. 依存関係のインストール

```bash
# システム依存
brew install poppler ffmpeg  # macOS
# or
sudo apt-get install poppler-utils ffmpeg  # Ubuntu

# Python依存
pip install pdf2image Pillow google-cloud-vision edge-tts pydub tqdm click
```

### 2. Google Cloud Vision のセットアップ

```bash
# GCPプロジェクトを作成（または既存プロジェクトを使用）
# Cloud Vision APIを有効化
# サービスアカウントキーをダウンロード

export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

### 3. 動作確認

```bash
# Phase 2のOCR精度を先に確認する
python -m book2audio.ocr test_page.png --debug
```

---

## 実装の優先順位

1. **最初にやること**: Phase 2のOCR精度検証（サンプル5ページ程度で縦書き読み順が正しいか確認）
2. OCR精度OKなら → Phase 1 → Phase 3 → Phase 4 → Phase 5 の順に実装
3. OCR精度NGなら → Claude Vision APIへのフォールバック実装を先に検討

## コスト見積もり（300ページの本1冊）

| 項目 | コスト |
|---|---|
| Google Cloud Vision | 無料（月1,000ページまで） |
| Edge TTS | 無料 |
| 合計 | **¥0** |

※ 無料枠を超えた場合: Vision API = $1.50/1,000ページ
※ フォールバックでClaude Vision APIを使う場合: $3-5/冊