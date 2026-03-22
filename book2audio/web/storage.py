"""音声ファイルストレージ — Cloudflare R2 またはローカルファイルシステム"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from mutagen.mp3 import MP3


# ── R2 (S3互換) クライアント ──────────────────────────

def _get_s3_client():
    """Cloudflare R2 の boto3 クライアントを返す。未設定なら None。"""
    account_id = os.environ.get("R2_ACCOUNT_ID")
    if not account_id:
        return None

    import boto3
    return boto3.client(
        "s3",
        endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
    )


def _get_bucket() -> str:
    return os.environ.get("R2_BUCKET", "book2audio")


def is_cloud_storage() -> bool:
    """R2 が設定されているか。"""
    return bool(os.environ.get("R2_ACCOUNT_ID"))


# ── ローカルストレージ用ヘルパー ──────────────────────

def _default_data_dir() -> Path:
    return Path(os.environ.get("BOOK2AUDIO_DATA_DIR", Path.home() / ".book2audio"))


def get_audio_base_dir(data_dir: Path | None = None) -> Path:
    base = (data_dir or _default_data_dir()) / "audio"
    base.mkdir(parents=True, exist_ok=True)
    return base


def get_book_audio_dir(book_id: str, data_dir: Path | None = None) -> Path:
    return get_audio_base_dir(data_dir) / book_id


def get_audio_path(book_id: str, filename: str, data_dir: Path | None = None) -> Path:
    return get_book_audio_dir(book_id, data_dir) / filename


# ── 共通関数 ──────────────────────────────────────────

def get_mp3_duration(filepath: Path) -> float:
    """MP3ファイルの再生時間（秒）を取得。"""
    audio = MP3(str(filepath))
    return audio.info.length


def move_audio_to_permanent(
    temp_dir: str, book_id: str, data_dir: Path | None = None
) -> list[dict]:
    """一時ディレクトリから永続ストレージ（R2 またはローカル）へ音声ファイルを保存。"""
    source = Path(temp_dir) / "audio"
    if not source.exists():
        return []

    mp3_files = sorted(source.glob("*.mp3"))
    if not mp3_files:
        return []

    s3 = _get_s3_client()
    bucket = _get_bucket()

    if not s3:
        # ローカルストレージ
        dest = get_book_audio_dir(book_id, data_dir)
        dest.mkdir(parents=True, exist_ok=True)

    results: list[dict] = []

    for mp3 in mp3_files:
        duration = get_mp3_duration(mp3)

        if s3:
            # R2 にアップロード
            key = f"{book_id}/{mp3.name}"
            s3.upload_file(
                str(mp3), bucket, key,
                ExtraArgs={"ContentType": "audio/mpeg"},
            )
        else:
            # ローカルにコピー
            shutil.copy2(str(mp3), str(dest / mp3.name))

        # タイトル推定: "01_第一章.mp3" → "第一章"
        stem = mp3.stem
        parts = stem.split("_", 1)
        title = parts[1] if len(parts) > 1 else stem

        results.append({
            "filename": mp3.name,
            "title": title,
            "duration_sec": duration,
        })

    return results


def upload_file_to_storage(local_path: Path, book_id: str, filename: str) -> None:
    """単一ファイルをストレージにアップロード。"""
    s3 = _get_s3_client()
    if s3:
        key = f"{book_id}/{filename}"
        s3.upload_file(
            str(local_path), _get_bucket(), key,
            ExtraArgs={"ContentType": "audio/mpeg"},
        )
    else:
        dest = get_book_audio_dir(book_id)
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(local_path), str(dest / filename))


def get_audio_url_or_path(book_id: str, filename: str, data_dir: Path | None = None):
    """R2ならプリサインURL(str)、ローカルならPath を返す。"""
    s3 = _get_s3_client()
    if s3:
        key = f"{book_id}/{filename}"
        return s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": _get_bucket(), "Key": key},
            ExpiresIn=3600,
        )
    return get_audio_path(book_id, filename, data_dir)


def delete_book_audio(book_id: str, data_dir: Path | None = None) -> bool:
    """書籍の音声をすべて削除。"""
    s3 = _get_s3_client()
    if s3:
        bucket = _get_bucket()
        # R2 からオブジェクト一覧取得 → バッチ削除
        response = s3.list_objects_v2(Bucket=bucket, Prefix=f"{book_id}/")
        objects = response.get("Contents", [])
        if not objects:
            return False
        s3.delete_objects(
            Bucket=bucket,
            Delete={"Objects": [{"Key": obj["Key"]} for obj in objects]},
        )
        return True

    # ローカル
    book_dir = get_book_audio_dir(book_id, data_dir)
    if book_dir.exists():
        shutil.rmtree(str(book_dir))
        return True
    return False
