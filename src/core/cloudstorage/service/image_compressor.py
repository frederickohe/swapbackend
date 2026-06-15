"""Lossy-but-high-quality image compression before object storage upload."""

from __future__ import annotations

import io
import logging
import os
from typing import BinaryIO, Optional, Tuple

from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

MIME_TO_FORMAT = {
    "image/jpeg": "JPEG",
    "image/jpg": "JPEG",
    "image/png": "PNG",
    "image/webp": "WEBP",
}

EXTENSION_TO_FORMAT = {
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".png": "PNG",
    ".webp": "WEBP",
}

SKIP_EXTENSIONS = {".gif", ".bmp", ".svg", ".ico", ".heic", ".heif"}


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def compression_enabled() -> bool:
    return _env_bool("STORAGE_IMAGE_COMPRESSION_ENABLED", True)


def jpeg_quality() -> int:
    return max(1, min(100, _env_int("STORAGE_IMAGE_JPEG_QUALITY", 88)))


def webp_quality() -> int:
    return max(1, min(100, _env_int("STORAGE_IMAGE_WEBP_QUALITY", 85)))


def max_dimension() -> int:
    return max(0, _env_int("STORAGE_IMAGE_MAX_DIMENSION", 2048))


def _resolve_format(content_type: str | None, file_name: str) -> str | None:
    if content_type:
        normalized = content_type.split(";", 1)[0].strip().lower()
        fmt = MIME_TO_FORMAT.get(normalized)
        if fmt:
            return fmt

    _, ext = os.path.splitext(file_name.lower())
    if ext in SKIP_EXTENSIONS:
        return None
    return EXTENSION_TO_FORMAT.get(ext)


def _resize_if_needed(image: Image.Image, limit: int) -> Image.Image:
    if limit <= 0:
        return image

    width, height = image.size
    longest = max(width, height)
    if longest <= limit:
        return image

    scale = limit / float(longest)
    new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
    return image.resize(new_size, Image.Resampling.LANCZOS)


def _prepare_for_format(image: Image.Image, fmt: str) -> Image.Image:
    image = ImageOps.exif_transpose(image)

    if fmt == "JPEG":
        if image.mode in {"RGBA", "LA"}:
            background = Image.new("RGB", image.size, (255, 255, 255))
            alpha = image.split()[-1]
            background.paste(image, mask=alpha)
            return background
        if image.mode != "RGB":
            return image.convert("RGB")
        return image

    if fmt == "PNG" and image.mode not in {"RGBA", "RGB", "L", "LA", "P"}:
        return image.convert("RGBA" if "A" in image.mode else "RGB")

    if fmt == "WEBP":
        if image.mode in {"P", "CMYK"}:
            return image.convert("RGBA" if "transparency" in image.info else "RGB")
        return image

    return image


def _save_image(image: Image.Image, fmt: str) -> bytes:
    buffer = io.BytesIO()
    save_kwargs: dict = {"format": fmt, "optimize": True}

    if fmt == "JPEG":
        save_kwargs["quality"] = jpeg_quality()
        save_kwargs["progressive"] = True
    elif fmt == "PNG":
        save_kwargs["compress_level"] = 9
    elif fmt == "WEBP":
        save_kwargs["quality"] = webp_quality()
        save_kwargs["method"] = 4

    image.save(buffer, **save_kwargs)
    return buffer.getvalue()


def compress_image_bytes(
    data: bytes,
    file_name: str,
    content_type: str | None = None,
) -> Optional[Tuple[io.BytesIO, str, str]]:
    """Compress image bytes in memory while preserving visual quality."""
    if not compression_enabled() or not data:
        return None

    fmt = _resolve_format(content_type, file_name)
    if fmt is None:
        return None

    try:
        with Image.open(io.BytesIO(data)) as image:
            image.load()
            prepared = _prepare_for_format(image, fmt)
            resized = _resize_if_needed(prepared, max_dimension())
            compressed = _save_image(resized, fmt)
    except Exception as exc:
        logger.debug("Skipping compression for %s: %s", file_name, exc)
        return None

    if len(compressed) >= len(data):
        logger.debug(
            "Keeping original upload for %s (%s bytes >= %s bytes)",
            file_name,
            len(data),
            len(compressed),
        )
        return None

    normalized_content_type = content_type or f"image/{fmt.lower()}"
    logger.info(
        "Compressed %s from %s to %s bytes (%.1f%% reduction)",
        file_name,
        len(data),
        len(compressed),
        100 * (1 - len(compressed) / len(data)),
    )

    buffer = io.BytesIO(compressed)
    buffer.seek(0)
    return buffer, file_name, normalized_content_type


def compress_image_for_upload(
    file_obj: BinaryIO,
    file_name: str,
    content_type: str | None = None,
) -> Optional[Tuple[io.BytesIO, str, str]]:
    """Compress an image in memory while preserving visual quality.

    Returns a tuple of (buffer, file_name, content_type) when compression is applied,
    or None when the original upload should be used unchanged.
    """
    try:
        file_obj.seek(0)
        data = file_obj.read()
    except Exception:
        logger.debug("Could not read upload for compression: %s", file_name)
        return None

    return compress_image_bytes(data, file_name, content_type)
