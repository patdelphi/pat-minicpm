"""
程序说明：
为本地 API 提供媒体输入辅助能力：
1. 解析本地路径、file URL、data URL。
2. 使用 ffmpeg / ffprobe 从视频中抽取代表性帧。
3. 将抽出的帧加载为 PIL.Image，供 MiniCPM-V 4.6 作为多图输入使用。
"""

from __future__ import annotations

import base64
import mimetypes
import shutil
import subprocess
import tempfile
from io import BytesIO
from pathlib import Path
from typing import List, Tuple
from urllib.parse import unquote, urlparse

from PIL import Image

VIDEO_FRAME_LIMIT = 8


def _decode_data_url(data_url: str) -> Tuple[str, bytes]:
    if not data_url.startswith("data:"):
        raise ValueError("Only data URLs are supported in this helper.")
    if ";base64," not in data_url:
        raise ValueError("The data URL is missing the ';base64,' segment.")
    header, b64 = data_url.split(";base64,", 1)
    mime_type = header[5:] or "application/octet-stream"
    return mime_type, base64.b64decode(b64)


def _file_url_to_path(file_url: str) -> Path:
    parsed = urlparse(file_url)
    path = unquote(parsed.path or "")
    if path.startswith("/") and len(path) >= 3 and path[2] == ":":
        path = path[1:]
    return Path(path)


def resolve_media_path(source: str, *, default_suffix: str) -> Tuple[Path, Path | None]:
    """
    将 data URL / file URL / 本地路径 统一解析为本地文件路径。
    如果中间创建了临时目录，则一并返回，调用方负责清理。
    """
    source = (source or "").strip()
    if not source:
        raise ValueError("The media URL or path is empty.")

    if source.startswith("data:"):
        mime_type, raw = _decode_data_url(source)
        suffix = mimetypes.guess_extension(mime_type) or default_suffix
        temp_dir = Path(tempfile.mkdtemp(prefix="minicpm_media_"))
        file_path = temp_dir / f"input{suffix}"
        file_path.write_bytes(raw)
        return file_path, temp_dir

    if source.startswith("file://"):
        file_path = _file_url_to_path(source)
    else:
        file_path = Path(source)

    if not file_path.exists():
        raise ValueError(f"Media file not found: {file_path}")
    return file_path, None


def load_image_input(source: str) -> Image.Image:
    """
    加载图片输入，支持 data URL、file URL 与本地路径。
    """
    image_path, temp_dir = resolve_media_path(source, default_suffix=".png")
    try:
        return Image.open(image_path).convert("RGB")
    finally:
        if temp_dir is not None:
            shutil.rmtree(temp_dir, ignore_errors=True)


def _require_binary(binary_name: str) -> str:
    binary_path = shutil.which(binary_name)
    if not binary_path:
        raise ValueError(f"{binary_name} is required but was not found in PATH.")
    return binary_path


def _probe_duration_seconds(video_path: Path) -> float | None:
    """
    使用 ffprobe 获取视频时长；失败时返回 None，后续回退到保守抽帧策略。
    """
    ffprobe = _require_binary("ffprobe")
    try:
        result = subprocess.run(
            [
                ffprobe,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(video_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        value = (result.stdout or "").strip()
        return float(value) if value else None
    except (subprocess.SubprocessError, ValueError):
        return None


def extract_video_frames(source: str, *, max_frames: int = VIDEO_FRAME_LIMIT) -> List[Image.Image]:
    """
    使用 ffmpeg 从视频中抽取最多 `max_frames` 张代表帧，并加载为 RGB 图片。
    这样可以在不依赖额外视频解码库的前提下，将视频问题降级为多图理解。
    """
    video_path, source_temp_dir = resolve_media_path(source, default_suffix=".mp4")
    frames_temp_dir = Path(tempfile.mkdtemp(prefix="minicpm_video_frames_"))
    ffmpeg = _require_binary("ffmpeg")

    try:
        duration = _probe_duration_seconds(video_path)
        if duration and duration > 0:
            fps_value = min(max_frames / duration, 2.0)
            fps_filter = f"fps={fps_value:.6f}"
        else:
            fps_filter = "fps=1"

        output_pattern = frames_temp_dir / "frame_%03d.jpg"
        result = subprocess.run(
            [
                ffmpeg,
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(video_path),
                "-vf",
                fps_filter,
                "-frames:v",
                str(max_frames),
                str(output_pattern),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            stderr = (result.stderr or "").strip()
            raise ValueError(f"ffmpeg failed to extract video frames: {stderr or 'unknown error'}")

        frames: List[Image.Image] = []
        for frame_path in sorted(frames_temp_dir.glob("frame_*.jpg")):
            frames.append(Image.open(frame_path).convert("RGB"))

        if not frames:
            raise ValueError("No frames could be extracted from the provided video.")
        return frames
    finally:
        shutil.rmtree(frames_temp_dir, ignore_errors=True)
        if source_temp_dir is not None:
            shutil.rmtree(source_temp_dir, ignore_errors=True)
